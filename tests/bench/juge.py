#!/usr/bin/env python3
"""juge.py — verdict d'un second modèle sur (réponse + trace).

Le juge complète les verdicts déterministes ; il ne les remplace pas. Un cas
passe si **et** les contrôles de trace **et** le juge concluent au succès :
un juge indulgent ne peut pas à lui seul faire réussir une sonde.

Différence avec `run_eval.judge` : le juge reçoit ici un **résumé structuré de
la trace** en plus de la réponse. Sans lui, il ne peut pas distinguer une
source récupérée d'une source récitée — la question centrale du skill.

Le résumé ne reprend jamais le texte intégral des résultats d'outils : seuls
les noms, les arguments et les identifiants renvoyés. C'est plus lisible pour
le juge, et cela évite qu'un secret présent dans une réponse d'outil ne
transite vers un second appel de modèle.

Stdlib uniquement.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from bench.flux import Trace

PROMPTS = Path(__file__).resolve().parent / "prompts"

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "raison": {"type": "string"},
        "axe_defaillant": {
            "type": "string",
            "enum": ["source", "temporalite", "interpretation", "faits", "forme", "aucun"],
        },
        "extrait": {"type": "string"},
    },
    "required": ["verdict", "raison", "axe_defaillant"],
    "additionalProperties": False,
}

LIBELLE_BRAS = {
    "A": "A — aucun skill, aucun outil",
    "B": "B — méthodologie appliquée, aucun outil",
    "C": "C — méthodologie appliquée, outils de recherche juridique disponibles",
}


@dataclass
class Avis:
    verdict: str
    raison: str
    axe_defaillant: str = "aucun"
    extrait: str = ""
    modele: str = ""
    erreur: str = ""

    @property
    def passe(self) -> bool:
        return self.verdict == "PASS"


def resumer_trace(trace: Trace) -> str:
    """Rend la trace lisible par un modèle, sans recopier les sources."""
    if not trace.appels:
        return "Aucun appel d'outil."
    lignes = []
    for appel in trace.appels:
        arguments = ", ".join(
            f"{cle}={valeur!r}" for cle, valeur in sorted(appel.arguments.items()) if valeur is not None
        )
        etat = "erreur" if appel.is_error else "ok"
        renvoyes = sorted(appel.identifiants_renvoyes)
        suffixe = f" → identifiants : {', '.join(renvoyes)}" if renvoyes else ""
        lignes.append(f"{appel.ordre + 1}. {appel.nom}({arguments}) [{etat}]{suffixe}")
    return "\n".join(lignes)


def construire_entree(*, bras: str, comportement_attendu: str, trace: Trace, reponse: str) -> str:
    return (
        f"BRAS : {LIBELLE_BRAS.get(bras, bras)}\n\n"
        f"COMPORTEMENT ATTENDU :\n{comportement_attendu}\n\n"
        f"RÉSUMÉ DE LA TRACE :\n{resumer_trace(trace)}\n\n"
        f"RÉPONSE :\n{reponse}"
    )


def construire_commande(modele: str, executable: str | None = None) -> list[str]:
    """Ligne de commande du juge — fonction pure, testable."""
    binaire = executable or shutil.which("claude")
    if not binaire:
        raise RuntimeError("CLI `claude` introuvable pour le juge")
    return [
        binaire,
        "-p",
        "--output-format",
        "json",
        "--model",
        modele,
        "--no-session-persistence",
        "--setting-sources",
        "",
        "--tools",
        "",
        "--strict-mcp-config",
        "--system-prompt-file",
        str(PROMPTS / "juge.md"),
        "--json-schema",
        json.dumps(SCHEMA, ensure_ascii=False),
    ]


def extraire_avis(sortie: str) -> Avis:
    """Lit le verdict, que la CLI le rende structuré ou noyé dans du texte."""
    charge: dict | None = None
    try:
        enveloppe = json.loads(sortie)
    except (ValueError, TypeError):
        enveloppe = None

    if isinstance(enveloppe, dict):
        structure = enveloppe.get("structured_output")
        if isinstance(structure, dict):
            charge = structure
        else:
            resultat = enveloppe.get("result")
            if isinstance(resultat, dict):
                charge = resultat
            elif isinstance(resultat, str):
                charge = _json_noye(resultat)
            elif "verdict" in enveloppe:
                charge = enveloppe

    if charge is None:
        charge = _json_noye(sortie)

    if not isinstance(charge, dict) or "verdict" not in charge:
        return Avis("FAIL", "verdict du juge illisible", erreur="sortie non conforme au schéma")

    verdict = str(charge.get("verdict", "")).upper()
    if verdict not in ("PASS", "FAIL"):
        return Avis("FAIL", f"verdict inattendu : {verdict}", erreur="valeur hors énumération")

    return Avis(
        verdict=verdict,
        raison=str(charge.get("raison", "")),
        axe_defaillant=str(charge.get("axe_defaillant", "aucun")),
        extrait=str(charge.get("extrait", "")),
    )


def _json_noye(texte: str) -> dict | None:
    """Repli : premier objet JSON trouvé dans du texte libre."""
    trouve = re.search(r"\{.*\}", texte or "", re.DOTALL)
    if not trouve:
        return None
    try:
        charge = json.loads(trouve.group(0))
    except (ValueError, TypeError):
        return None
    return charge if isinstance(charge, dict) else None


def juger(
    *,
    bras: str,
    comportement_attendu: str,
    trace: Trace,
    reponse: str,
    modele: str,
    executable: str | None = None,
    timeout_s: int = 180,
) -> Avis:
    """Soumet (réponse + trace) au juge et rend son avis."""
    entree = construire_entree(
        bras=bras, comportement_attendu=comportement_attendu, trace=trace, reponse=reponse
    )
    try:
        acheve = subprocess.run(  # noqa: S603 — commande construite, shell=False
            construire_commande(modele, executable),
            input=entree,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return Avis("FAIL", "le juge n'a pas répondu dans le délai", erreur="timeout")
    except OSError as exc:
        return Avis("FAIL", "le juge n'a pas pu être lancé", erreur=type(exc).__name__)

    avis = extraire_avis(acheve.stdout or "")
    avis.modele = modele
    return avis
