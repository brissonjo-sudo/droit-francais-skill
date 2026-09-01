#!/usr/bin/env python3
"""check_affirmations.py — confronte la prose du dépôt au code qu'elle décrit.

Ce contrôle vise une classe d'erreur précise, constatée trois fois lors de
l'audit du 1er septembre 2026 : *un document affirme une propriété que le code
ou la configuration contredit*. Chaque affirmation était plausible isolément —
personne ne recoupait. Le README annonçait `v0.5.0` quand le manifeste portait
`0.7.0` ; `deployment.md` promettait `openWorldHint: true` après que le serveur
fut repassé à `false`.

Ce que le contrôle vérifie, en prenant le code comme source de vérité :

1. toute version `v0.x.y` citée en prose vaut la version déclarée du plugin —
   les versions du skill sont en `2.x`/`3.x`, les deux espaces ne se recoupent
   pas, si bien qu'un `v0.…` désigne toujours le plugin ;
2. toute annotation d'outil citée en prose (`openWorldHint`, `readOnlyHint`,
   `destructiveHint`) vaut ce que déclare `READ_ONLY` dans le serveur, et le
   dossier de soumission dit la même chose que le serveur ;
3. toute variable d'environnement `MCP_*` citée en prose existe réellement
   dans le code ou dans `.env.example`.

Complément de `check_plugin.py`, qui compare les sources entre elles (manifeste
contre `SERVER_VERSION`) : ici on compare la **documentation** aux sources.

Sans dépendance externe. Code de sortie 1 si au moins une affirmation est
démentie.

Usage :
    python tests/check_affirmations.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "mcp_server" / "server.py"
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
SUBMISSION = ROOT / "chatgpt-app-submission.json"
ENV_EXAMPLE = ROOT / "skill" / "scripts" / ".env.example"

#: Journaux datés : ils consignent un état d'époque et doivent pouvoir citer une
#: valeur périmée. Les y corriger effacerait l'historique au lieu de le tenir.
#: Toute entrée devenue fausse y porte une mention de péremption, à la main.
JOURNAUX = {"docs/roadmap-chatgpt-plugin.md"}

#: Répertoires sans prose opposable : wikilinks Obsidian, copies de travail.
EXCLUDE_DIRS = {".git", ".claude", ".venv", "vault", "__pycache__"}

ANNOTATIONS = ("readOnlyHint", "destructiveHint", "openWorldHint")

VERSION_PLUGIN_RE = re.compile(r"\bv(0\.\d+\.\d+)\b")
ANNOTATION_RE = re.compile(
    r"\b(" + "|".join(ANNOTATIONS) + r")\b\s*[:=]\s*`?(true|false)\b"
)
ENV_RE = re.compile(r"\bMCP_[A-Z0-9_]+\b")


def _fail(message: str, problems: list[str]) -> None:
    problems.append(message)


def documents() -> list[Path]:
    """Fichiers Markdown porteurs d'affirmations opposables."""
    fichiers = []
    for chemin in ROOT.rglob("*.md"):
        parts = chemin.relative_to(ROOT).parts
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        if chemin.relative_to(ROOT).as_posix() in JOURNAUX:
            continue
        fichiers.append(chemin)
    return sorted(fichiers)


def version_declaree() -> str:
    """Version du plugin, lue au seul endroit qui fait foi."""
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]


def annotations_du_serveur() -> dict[str, bool]:
    """Valeurs réelles de ``READ_ONLY`` dans le serveur MCP."""
    texte = SERVER.read_text(encoding="utf-8")
    bloc = re.search(r"READ_ONLY = ToolAnnotations\((.*?)\n\)", texte, re.S)
    if not bloc:
        raise SystemExit("❌ READ_ONLY introuvable dans mcp_server/server.py")
    valeurs: dict[str, bool] = {}
    for nom in ANNOTATIONS:
        trouve = re.search(rf"\b{nom}\s*=\s*(True|False)\b", bloc.group(1))
        if trouve:
            valeurs[nom] = trouve.group(1) == "True"
    return valeurs


def noms_env_connus() -> set[str]:
    """Variables ``MCP_*`` réellement lues par le code ou proposées en exemple."""
    connus: set[str] = set()
    sources = [ROOT / "mcp_server", ROOT / "skill" / "scripts", ROOT / "tests"]
    fichiers = [f for base in sources for f in base.rglob("*.py")]
    fichiers += [ENV_EXAMPLE, ROOT / "Dockerfile"]
    for chemin in fichiers:
        if chemin.exists():
            connus.update(ENV_RE.findall(chemin.read_text(encoding="utf-8")))
    return connus


def controler_versions(problems: list[str]) -> None:
    courante = version_declaree()
    for doc in documents():
        rel = doc.relative_to(ROOT).as_posix()
        for numero, ligne in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for citee in VERSION_PLUGIN_RE.findall(ligne):
                if citee != courante:
                    _fail(
                        f"{rel}:{numero} annonce le plugin en v{citee} ; "
                        f"le manifeste déclare {courante}",
                        problems,
                    )


def controler_annotations(problems: list[str]) -> None:
    reelles = annotations_du_serveur()
    for doc in documents():
        rel = doc.relative_to(ROOT).as_posix()
        for numero, ligne in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for nom, valeur in ANNOTATION_RE.findall(ligne):
                if nom not in reelles:
                    continue
                if (valeur == "true") != reelles[nom]:
                    _fail(
                        f"{rel}:{numero} annonce {nom}={valeur} ; "
                        f"le serveur déclare {str(reelles[nom]).lower()}",
                        problems,
                    )
    if not SUBMISSION.exists():
        return
    outils = json.loads(SUBMISSION.read_text(encoding="utf-8")).get("tools", {})
    for outil, descripteur in outils.items():
        declarees = descripteur.get("annotations", {})
        for nom, attendue in reelles.items():
            if nom in declarees and declarees[nom] != attendue:
                _fail(
                    f"chatgpt-app-submission.json : {outil}.{nom} vaut "
                    f"{str(declarees[nom]).lower()}, le serveur déclare "
                    f"{str(attendue).lower()}",
                    problems,
                )


def controler_variables(problems: list[str]) -> None:
    connus = noms_env_connus()
    for doc in documents():
        rel = doc.relative_to(ROOT).as_posix()
        for numero, ligne in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for nom in ENV_RE.findall(ligne):
                if nom not in connus:
                    _fail(
                        f"{rel}:{numero} cite {nom}, que ni le code ni "
                        ".env.example ne connaissent",
                        problems,
                    )


def main() -> int:
    problems: list[str] = []
    controler_versions(problems)
    controler_annotations(problems)
    controler_variables(problems)
    if problems:
        print(f"❌ {len(problems)} affirmation(s) démentie(s) par le code :")
        for probleme in sorted(set(problems)):
            print(f"   - {probleme}")
        print(
            "\nCorriger la documentation, ou le code si c'est lui qui a tort. "
            "Un journal daté se corrige par une mention de péremption."
        )
        return 1
    nombre = len(documents())
    print(
        f"✅ Affirmations vérifiées ({nombre} documents) : versions, "
        "annotations d'outils et variables d'environnement concordent."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
