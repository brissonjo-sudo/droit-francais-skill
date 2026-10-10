"""Préparer des profils privés Gemini ; aucune rotation ni collecte réseau."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

from bench import quotas_gemini

EXEMPLE = Path(__file__).resolve().parents[2] / "tests/campaign/profils-gemini.example.json"


def initialiser(sortie: Path) -> None:
    """Créer un registre privé vide de preuves, sans écraser l'existant."""
    target = quotas_gemini.chemin_local(sortie)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(EXEMPLE.read_text(encoding="utf-8"))
    except FileExistsError as exc:
        raise ValueError("registre existant : aucune écriture") from exc
    except OSError as exc:
        raise ValueError("création du registre impossible ; aucun chemin privé affiché") from exc


def verifier(registre: Path, profil: str | None = None, *,
             maintenant: dt.datetime | None = None) -> dict:
    """Contrôler les déclarations de profils sans restituer projets ni secrets."""
    path = quotas_gemini.chemin_local(registre)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError, OSError) as exc:
        raise ValueError("registre privé illisible ; aucun contenu affiché") from exc
    if (not isinstance(data, dict) or set(data) != {"schema", "profils"}
            or type(data["schema"]) is not int or data["schema"] != 1
            or not isinstance(data["profils"], list) or not 1 <= len(data["profils"]) <= 20):
        raise ValueError("structure du registre invalide ; ne pas inclure de clé")
    ids, envs, rows = set(), set(), []
    for row in data["profils"]:
        if (not isinstance(row, dict) or set(row) != {"profil", "cle_env", "releve"}
                or not isinstance(row["profil"], str)
                or not re.fullmatch(r"profil-[0-9]{2}", row["profil"])
                or not isinstance(row["cle_env"], str)
                or not re.fullmatch(r"GEMINI_API_KEY(?:_[A-Z0-9_]{1,60})?", row["cle_env"])
                or not isinstance(row["releve"], str) or not row["releve"]
                or row["profil"] in ids or row["cle_env"] in envs):
            raise ValueError("profil invalide ou doublon ; aucun contenu affiché")
        ids.add(row["profil"])
        envs.add(row["cle_env"])
        try:
            evidence = quotas_gemini.chemin_local(path.parent / row["releve"])
        except ValueError as exc:
            raise ValueError("relevé hors de l'état privé") from exc
        if evidence == path:
            raise ValueError("un relevé ne peut pas désigner son registre")
        rows.append((row, evidence))
    if profil is not None and profil not in ids:
        raise ValueError("profil demandé absent du registre")
    groups, declarations, observations, problems = {}, {}, [], []
    models = set()
    for row, evidence in rows:
        try:
            checked = quotas_gemini.verifier(evidence, maintenant=maintenant)
            issues = checked["problemes_releve"]
        except (ValueError, OSError):
            issues = ["relevé absent ou invalide ; aucun contenu affiché"]
        group = None
        if not issues:
            # Toutes ces données restent privées. La sortie ne contient que
            # des numéros de groupes attribués selon l'ordre du registre.
            try:
                declared = json.loads(evidence.read_text(encoding="utf-8"))
            except (ValueError, UnicodeError, OSError) as exc:
                raise ValueError("relevé devenu illisible ; aucun contenu affiché") from exc
            project = declared["projet_ref"]
            group = groups.setdefault(project, f"groupe-{len(groups) + 1:02}")
            models.add(declared["modele"])
            key = (project, declared["modele"])
            limits = declared["limites"]
            if key in declarations and declarations[key] != limits:
                problems.append("relevés contradictoires pour un même projet et modèle")
            declarations[key] = limits
        observations.append({"profil": row["profil"], "groupe_quota_declare": group,
                             "releve_coherent": not issues,
                             "cle_disponible": bool(os.environ.get(row["cle_env"])),
                             "problemes_releve": issues})
    if len(models) > 1:
        problems.append("modèles différents : séries distinctes à préparer")
    selected = next((r for r in observations if r["profil"] == profil), None)
    return {"statut": "profils_declares_coherents" if not problems and all(
                r["releve_coherent"] for r in observations) else "profils_incomplets_ou_invalides",
            "controle_hors_reseau": True, "collecte_autorisee": False,
            "profil_selectionne": profil, "selection_explicitement_coherente": bool(
                selected and selected["releve_coherent"] and not problems),
            "groupes_quota_declares": len(groups), "rotation_automatique": False,
            "limite_globale_reponses_jour_UTC": 100,
            "profils": observations, "problemes_registre": sorted(set(problems)),
            "reste_a_qualifier": ["usage multiprojet compatible avec les limites Google",
                                  "authentification, quotas actifs et compteurs par requête",
                                  "corrigés humains, préflights et pilote"]}
