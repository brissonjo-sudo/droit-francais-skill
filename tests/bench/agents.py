#!/usr/bin/env python3
"""agents.py — exécution d'un cas par un agent réel, en headless.

Le harnais pilote la **vraie CLI**, pas une boucle d'API reconstituée : ce qui
est mesuré est la méthodologie telle qu'elle s'applique dans la chaîne
d'outils distribuée, pas une approximation.

Trois bras :

===== ===================================== ==========================
Bras  Prompt système                        Outils
===== ===================================== ==========================
A     neutre (`prompts/bras-A.md`)          aucun
B     `skill/SKILL.md` + préambule B        aucun
C     `skill/SKILL.md` + préambule C        MCP `droit-francais` seul
===== ===================================== ==========================

Options relevées sur la CLI 2.1.133 de ce poste (`claude --help` et runs
réels) :

- ``--system-prompt-file`` / ``--append-system-prompt-file`` — **obligatoires**
  ici : `skill/SKILL.md` pèse ~47 ko, très au-delà de la limite d'une ligne de
  commande Windows (32 767 caractères).
- ``--tools ""`` — vérifié : l'événement `init` passe de 24 outils à `[]`.
  C'est ce qui rend les bras A et B honnêtes ; sans lui, la CLI conserve
  WebFetch et WebSearch et le « sans outils » n'en est pas un.
- ``--setting-sources ""`` — vérifié : retire les skills et réglages du poste.
  Sans cela, le skill `recherche-juridique` installé chez l'utilisateur et son
  `CLAUDE.md` global contamineraient le bras A, censé mesurer un modèle nu.
- ``--no-session-persistence``, ``--strict-mcp-config``, ``--allowedTools``,
  ``--disallowedTools``, ``--mcp-config`` — acceptées.
- ``--fallback-model`` : **jamais employée**. Un basculement silencieux de
  modèle rendrait deux baselines incomparables sans que rien ne le signale.

Le jeton d'accès ne transite **que** par l'environnement du sous-processus :
jamais en argument de ligne de commande (visible dans la liste des processus),
jamais dans un fichier commité.

Stdlib uniquement.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from bench.flux import Trace, analyser

RACINE = Path(__file__).resolve().parent.parent.parent
PROMPTS = Path(__file__).resolve().parent / "prompts"
SKILL = RACINE / "skill" / "SKILL.md"

BRAS_SANS_OUTIL = ("A", "B")

# Outils intégrés explicitement refusés sur le bras C. `--tools ""` les
# désactive déjà ; la liste est une seconde barrière, au cas où une version
# ultérieure de la CLI changerait la sémantique de `--tools`.
OUTILS_REFUSES = (
    "WebFetch",
    "WebSearch",
    "Bash",
    "Edit",
    "Write",
    "Read",
    "Glob",
    "Grep",
    "Task",
    "Skill",
)


@dataclass
class Options:
    """Réglages d'exécution partagés par tous les cas d'un run."""

    modele: str = "sonnet"
    url_mcp: str = "https://droit-francais-skill.onrender.com/mcp"
    timeout_s: int = 300
    executable: str | None = None
    interpreteur_python: str | None = None
    mcp_local: bool = False
    marge_tours: int = 2
    garder_flux: bool = False


@dataclass
class Execution:
    """Résultat brut d'un run, avant tout verdict."""

    trace: Trace
    flux_brut: str
    code_retour: int
    erreur: str = ""
    statut: str = "ok"  # "ok" | "infra_error"
    motif_infra: str = ""


class Agent(Protocol):
    """Contrat d'un backend d'exécution."""

    nom: str

    def executer(self, *, prompt: str, bras: str, plafond: int, options: Options) -> Execution:
        ...


def chemin_executable(options: Options) -> str:
    """Résout la CLI, en préférant un chemin explicite au PATH."""
    if options.executable:
        return options.executable
    trouve = shutil.which("claude")
    if not trouve:
        raise RuntimeError(
            "CLI `claude` introuvable dans le PATH — préciser --executable"
        )
    return trouve


def config_mcp(options: Options) -> dict:
    """Configuration MCP du bras C.

    Deux cibles possibles. En production (défaut), le serveur HTTP porte les
    clés PISTE ; le jeton est lu depuis l'environnement du sous-processus par
    substitution ``${MCP_ACCESS_TOKEN}``. En local (``--mcp-local``), le
    serveur est lancé en stdio — utile hors ligne, mais il lui faut ses
    propres clés PISTE.

    Le chemin de l'interpréteur est explicite : sur ce poste, le `python` du
    PATH POSIX et celui que voit un processus Windows ne sont pas le même
    binaire, et un serveur MCP qui ne démarre pas se manifeste par une liste
    d'outils vide, sans message d'erreur.
    """
    if options.mcp_local:
        interpreteur = options.interpreteur_python or "python"
        return {
            "mcpServers": {
                "droit-francais": {
                    "type": "stdio",
                    "command": interpreteur,
                    "args": [str(RACINE / "mcp_server" / "server.py")],
                    "cwd": str(RACINE),
                }
            }
        }
    return {
        "mcpServers": {
            "droit-francais": {
                "type": "http",
                "url": options.url_mcp,
                "headers": {"Authorization": "Bearer ${MCP_ACCESS_TOKEN}"},
            }
        }
    }


def construire_commande(
    *,
    bras: str,
    plafond: int,
    options: Options,
    chemin_config_mcp: Path | None,
) -> list[str]:
    """Assemble la ligne de commande d'un bras.

    Fonction **pure** : testable sans réseau ni CLI, et vérifiable quant à
    l'absence de tout secret dans les arguments.
    """
    if bras not in ("A", "B", "C"):
        raise ValueError(f"bras inconnu : {bras}")

    commande = [
        chemin_executable(options),
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--model",
        options.modele,
        "--setting-sources",
        "",
        "--tools",
        "",
        "--strict-mcp-config",
        "--max-turns",
        str(max(1, plafond + options.marge_tours)),
    ]

    if bras == "A":
        commande += ["--system-prompt-file", str(PROMPTS / "bras-A.md")]
    else:
        preambule = "preambule-B.md" if bras == "B" else "preambule-C.md"
        commande += [
            "--system-prompt-file",
            str(SKILL),
            "--append-system-prompt-file",
            str(PROMPTS / preambule),
        ]

    if bras == "C":
        if chemin_config_mcp is None:
            raise ValueError("le bras C exige une configuration MCP")
        commande += [
            "--mcp-config",
            str(chemin_config_mcp),
            "--allowedTools",
            "mcp__droit-francais__*",
            "--disallowedTools",
            *OUTILS_REFUSES,
        ]

    return commande


class ClaudeHeadless:
    """Backend `claude -p`."""

    nom = "claude"

    def executer(self, *, prompt: str, bras: str, plafond: int, options: Options) -> Execution:
        environnement = dict(os.environ)
        fichier_config: Path | None = None
        temporaire: str | None = None

        try:
            if bras == "C":
                temporaire = tempfile.mkdtemp(prefix="bench-mcp-")
                fichier_config = Path(temporaire) / "mcp.json"
                fichier_config.write_text(
                    json.dumps(config_mcp(options), ensure_ascii=False), encoding="utf-8"
                )

            commande = construire_commande(
                bras=bras, plafond=plafond, options=options, chemin_config_mcp=fichier_config
            )

            acheve = subprocess.run(  # noqa: S603 — commande construite, shell=False
                commande,
                input=prompt,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=environnement,
                timeout=options.timeout_s,
                shell=False,
                cwd=str(RACINE),
            )
        except subprocess.TimeoutExpired:
            return Execution(
                trace=Trace(),
                flux_brut="",
                code_retour=-1,
                statut="infra_error",
                motif_infra=f"délai dépassé ({options.timeout_s} s)",
            )
        except OSError as exc:
            return Execution(
                trace=Trace(),
                flux_brut="",
                code_retour=-1,
                statut="infra_error",
                motif_infra=f"lancement impossible : {type(exc).__name__}",
            )
        finally:
            if temporaire:
                shutil.rmtree(temporaire, ignore_errors=True)

        trace = analyser(acheve.stdout or "")
        execution = Execution(
            trace=trace,
            flux_brut=acheve.stdout if options.garder_flux else "",
            code_retour=acheve.returncode,
            erreur=(acheve.stderr or "")[:500],
        )
        _classer(execution, bras)
        return execution


def _classer(execution: Execution, bras: str) -> None:
    """Distingue une panne d'infrastructure d'un échec méthodologique.

    Une instance endormie, un jeton expiré ou un quota atteint ne sont pas des
    régressions du skill : les compter comme des échecs ferait baisser un
    score pour des raisons étrangères à ce qu'on mesure.
    """
    trace = execution.trace

    if trace.api_error_status:
        execution.statut = "infra_error"
        execution.motif_infra = f"erreur API {trace.api_error_status}"
        return

    if bras == "C" and not trace.mcp_connecte:
        execution.statut = "infra_error"
        execution.motif_infra = "serveur MCP non connecté"
        return

    if trace.permission_denials:
        execution.statut = "infra_error"
        execution.motif_infra = f"{len(trace.permission_denials)} refus de permission"
        return

    for appel in trace.appels:
        texte = appel.resultat_texte.lower()
        if appel.is_error and any(m in texte for m in ("429", "rate", "quota", "timeout")):
            execution.statut = "infra_error"
            execution.motif_infra = "quota ou indisponibilité côté outil"
            return

    if not trace.texte_final:
        execution.statut = "infra_error"
        execution.motif_infra = "aucune réponse finale dans le flux"


class CodexHeadless:
    """Backend `codex exec` — second point de vue, non branché.

    Prévu pour croiser les résultats avec l'écosystème OpenAI, où le dépôt
    publie déjà un manifeste (`.codex-plugin/plugin.json`). Laissé explicite
    plutôt qu'absent : la forme de la commande cible est consignée ici pour
    que le branchement n'ait pas à la redécouvrir.

    Commande visée : ``codex exec --json --skip-git-repo-check <prompt>``
    avec la configuration MCP du dépôt.
    """

    nom = "codex"

    def executer(self, *, prompt: str, bras: str, plafond: int, options: Options) -> Execution:
        raise NotImplementedError(
            "backend codex non branché — la CLI `codex` n'est pas installée sur ce poste"
        )


BACKENDS: dict[str, type] = {"claude": ClaudeHeadless, "codex": CodexHeadless}


def backend(nom: str) -> Agent:
    if nom not in BACKENDS:
        raise ValueError(f"backend inconnu : {nom} (connus : {', '.join(BACKENDS)})")
    return BACKENDS[nom]()  # type: ignore[return-value]
