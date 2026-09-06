#!/usr/bin/env python3
"""flux.py — lecture du flux `stream-json` d'un agent headless.

(Le module ne s'appelle pas `trace.py` : ce nom masque le module `trace` de
la bibliothèque standard selon le chemin d'import retenu.)

Transforme la sortie de `claude -p --output-format stream-json --verbose`
en une :class:`Trace` exploitable par les verdicts et le juge.

Le format des événements a été relevé sur un run réel de la CLI 2.1.133
(voir `tests/fixtures/bench/`), pas déduit d'une documentation :

    {"type":"system","subtype":"init","tools":[...],"mcp_servers":[...],
     "model":"claude-sonnet-4-6",...}
    {"type":"assistant","message":{"content":[
        {"type":"tool_use","id":"toolu_…","name":"mcp__droit-francais__search_articles",
         "input":{…}}]}}
    {"type":"user","message":{"content":[
        {"type":"tool_result","tool_use_id":"toolu_…","is_error":false,
         "content":[{"type":"text","text":"…"}]}]}}
    {"type":"result","subtype":"success","is_error":false,"result":"…",
     "num_turns":3,"duration_ms":18234,"duration_api_ms":15210,
     "total_cost_usd":0.041,"usage":{…},"permission_denials":[]}

Principe de lecture : **tolérant en entrée, strict en sortie**. Une ligne
illisible est comptée (`lignes_illisibles`) et non fatale — un flux tronqué
par un timeout doit rester analysable jusqu'à son point de coupure — mais
tout ce que la trace expose est typé et vérifié.

Stdlib uniquement (convention du dépôt : voir `tests/README.md`).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

# Préfixe des outils MCP tel que la CLI les nomme : mcp__<serveur>__<outil>.
PREFIXE_MCP = "mcp__droit-francais__"

# Identifiants officiels français. Chaque motif est ancré sur une forme
# publiée ; un motif trop lâche produirait de faux positifs de provenance.
MOTIFS_IDENTIFIANTS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bLEGIARTI\d{12}\b"),
    re.compile(r"\bLEGITEXT\d{12}\b"),
    re.compile(r"\bJORFTEXT\d{12}\b"),
    re.compile(r"\bCETATEXT\d{12}\b"),
    re.compile(r"\bCONSTEXT\d{12}\b"),
    # Pourvoi Cour de cassation : 23-81.234
    re.compile(r"\b\d{2}-\d{2}\.\d{3}\b"),
    # ECLI européen / français
    re.compile(r"\bECLI:[A-Z]{2}:[A-Z0-9]+:\d{4}:[A-Z0-9.]+\b"),
    # NOR d'un texte publié au JORF
    re.compile(r"\b[A-Z]{4}\d{7}[A-Z]\b"),
)


def identifiants(texte: str) -> set[str]:
    """Extrait tous les identifiants officiels présents dans un texte."""
    trouves: set[str] = set()
    for motif in MOTIFS_IDENTIFIANTS:
        trouves.update(motif.findall(texte or ""))
    return trouves


@dataclass(frozen=True)
class Appel:
    """Un appel d'outil et son résultat, dans l'ordre du flux."""

    ordre: int
    nom_complet: str
    arguments: dict[str, Any]
    resultat_texte: str = ""
    is_error: bool = False

    @property
    def nom(self) -> str:
        """Nom court de l'outil, sans le préfixe MCP."""
        if self.nom_complet.startswith(PREFIXE_MCP):
            return self.nom_complet[len(PREFIXE_MCP) :]
        return self.nom_complet

    @property
    def identifiants_renvoyes(self) -> set[str]:
        """Identifiants officiels contenus dans le résultat de cet appel.

        Un appel en erreur n'en renvoie aucun : un résultat d'échec ne peut
        pas servir de preuve de provenance.
        """
        if self.is_error:
            return set()
        return identifiants(self.resultat_texte)


@dataclass
class Trace:
    """Ce qu'un run d'agent a réellement fait, indépendamment du verdict."""

    appels: list[Appel] = field(default_factory=list)
    texte_final: str = ""
    modele: str = ""
    mcp_connecte: bool = False
    permission_denials: list[Any] = field(default_factory=list)
    outils_disponibles: list[str] = field(default_factory=list)
    num_turns: int = 0
    duration_ms: int = 0
    duration_api_ms: int = 0
    total_cost_usd: float = 0.0
    usage: dict[str, Any] = field(default_factory=dict)
    is_error: bool = False
    api_error_status: int | None = None
    lignes_illisibles: int = 0

    @property
    def noms_outils_appeles(self) -> list[str]:
        """Noms courts des outils appelés, dans l'ordre, doublons compris."""
        return [a.nom for a in self.appels]

    def identifiants_traces(self, avant_ordre: int | None = None) -> set[str]:
        """Identifiants rendus par les outils, hors appels en erreur.

        ``avant_ordre`` restreint aux appels antérieurs : un identifiant ne
        prouve sa provenance que s'il a été récupéré **avant** d'être cité.
        """
        vus: set[str] = set()
        for appel in self.appels:
            if avant_ordre is not None and appel.ordre >= avant_ordre:
                break
            vus.update(appel.identifiants_renvoyes)
        return vus


def _texte_des_blocs(contenu: Any) -> str:
    """Concatène le texte d'un `content` MCP/Anthropic, quelle que soit sa forme."""
    if isinstance(contenu, str):
        return contenu
    if not isinstance(contenu, list):
        return ""
    morceaux: list[str] = []
    for bloc in contenu:
        if isinstance(bloc, str):
            morceaux.append(bloc)
        elif isinstance(bloc, dict):
            texte = bloc.get("text")
            if isinstance(texte, str):
                morceaux.append(texte)
            else:
                # Un tool_result peut porter du JSON structuré plutôt que du
                # texte : on le sérialise pour que la recherche d'identifiants
                # le couvre quand même.
                morceaux.append(json.dumps(bloc, ensure_ascii=False))
    return "\n".join(morceaux)


def lire_evenements(lignes: Iterable[str]) -> tuple[list[dict[str, Any]], int]:
    """Découpe un flux JSONL en événements, en comptant les lignes illisibles."""
    evenements: list[dict[str, Any]] = []
    illisibles = 0
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            charge = json.loads(ligne)
        except (ValueError, TypeError):
            illisibles += 1
            continue
        if isinstance(charge, dict):
            evenements.append(charge)
        else:
            illisibles += 1
    return evenements, illisibles


def analyser(flux: str) -> Trace:
    """Construit la :class:`Trace` d'un flux `stream-json` complet."""
    evenements, illisibles = lire_evenements(flux.splitlines())
    trace = Trace(lignes_illisibles=illisibles)

    # tool_use_id -> index dans trace.appels, pour raccrocher chaque résultat
    # à son appel : le flux les sépare de plusieurs événements.
    par_id: dict[str, int] = {}
    ordre = 0
    textes_assistant: list[str] = []

    for evenement in evenements:
        type_ev = evenement.get("type")

        if type_ev == "system" and evenement.get("subtype") == "init":
            trace.modele = evenement.get("model") or ""
            outils = evenement.get("tools")
            trace.outils_disponibles = [str(o) for o in outils] if isinstance(outils, list) else []
            serveurs = evenement.get("mcp_servers")
            if isinstance(serveurs, list):
                trace.mcp_connecte = any(
                    isinstance(s, dict) and s.get("status") == "connected" for s in serveurs
                )
            continue

        if type_ev == "assistant":
            for bloc in _blocs(evenement):
                if bloc.get("type") == "tool_use":
                    trace.appels.append(
                        Appel(
                            ordre=ordre,
                            nom_complet=str(bloc.get("name") or ""),
                            arguments=bloc.get("input") if isinstance(bloc.get("input"), dict) else {},
                        )
                    )
                    identifiant = bloc.get("id")
                    if isinstance(identifiant, str):
                        par_id[identifiant] = len(trace.appels) - 1
                    ordre += 1
                elif bloc.get("type") == "text":
                    texte = bloc.get("text")
                    if isinstance(texte, str) and texte.strip():
                        textes_assistant.append(texte)
            continue

        if type_ev == "user":
            for bloc in _blocs(evenement):
                if bloc.get("type") != "tool_result":
                    continue
                index = par_id.get(bloc.get("tool_use_id"))
                if index is None:
                    continue
                ancien = trace.appels[index]
                trace.appels[index] = Appel(
                    ordre=ancien.ordre,
                    nom_complet=ancien.nom_complet,
                    arguments=ancien.arguments,
                    resultat_texte=_texte_des_blocs(bloc.get("content")),
                    is_error=bool(bloc.get("is_error")),
                )
            continue

        if type_ev == "result":
            trace.is_error = bool(evenement.get("is_error"))
            statut = evenement.get("api_error_status")
            trace.api_error_status = statut if isinstance(statut, int) else None
            trace.num_turns = _entier(evenement.get("num_turns"))
            trace.duration_ms = _entier(evenement.get("duration_ms"))
            trace.duration_api_ms = _entier(evenement.get("duration_api_ms"))
            cout = evenement.get("total_cost_usd")
            trace.total_cost_usd = float(cout) if isinstance(cout, (int, float)) else 0.0
            usage = evenement.get("usage")
            trace.usage = usage if isinstance(usage, dict) else {}
            refus = evenement.get("permission_denials")
            trace.permission_denials = refus if isinstance(refus, list) else []
            resultat = evenement.get("result")
            if isinstance(resultat, str) and resultat.strip():
                trace.texte_final = resultat
            continue

    # `result.result` porte la réponse finale ; en son absence (flux tronqué),
    # on retombe sur le dernier bloc de texte de l'assistant.
    if not trace.texte_final and textes_assistant:
        trace.texte_final = textes_assistant[-1]

    return trace


def _blocs(evenement: dict[str, Any]) -> list[dict[str, Any]]:
    """Blocs de contenu d'un événement assistant ou user."""
    message = evenement.get("message")
    if not isinstance(message, dict):
        return []
    contenu = message.get("content")
    if not isinstance(contenu, list):
        return []
    return [b for b in contenu if isinstance(b, dict)]


def _entier(valeur: Any) -> int:
    return valeur if isinstance(valeur, int) and not isinstance(valeur, bool) else 0
