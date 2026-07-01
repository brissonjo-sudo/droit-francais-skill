#!/usr/bin/env python3
"""check_links.py — vérifie les liens relatifs des fichiers Markdown.

Parcourt les `.md` du dépôt (hors `vault/`, qui utilise des wikilinks Obsidian
`[[…]]` non résolus en chemins) et vérifie que chaque lien relatif de la forme
`[texte](chemin)` pointe vers un fichier existant. Les URL http(s), ancres
(`#…`) et `mailto:` sont ignorées.

Sans dépendance externe. Code de sortie 1 si au moins un lien est cassé.

Usage :
    python tests/check_links.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Dossiers exclus du contrôle (wikilinks Obsidian, artefacts).
EXCLUDE_DIRS = {".git", "vault", "__pycache__", ".github"}
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def iter_markdown() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def check_file(md: Path) -> list[str]:
    problems = []
    text = md.read_text(encoding="utf-8")
    for m in LINK_RE.finditer(text):
        target = m.group(1).strip()
        # Retirer un éventuel titre : [x](path "titre")
        target = target.split(" ", 1)[0].strip()
        if not target:
            continue
        low = target.lower()
        if low.startswith(("http://", "https://", "mailto:", "#", "tel:")):
            continue
        # Retirer l'ancre éventuelle
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (md.parent / path_part).resolve()
        if not resolved.exists():
            rel = md.relative_to(ROOT)
            problems.append(f"{rel}: lien cassé → {target}")
    return problems


def main() -> int:
    files = iter_markdown()
    all_problems = []
    for md in files:
        all_problems.extend(check_file(md))
    if all_problems:
        print(f"❌ {len(all_problems)} lien(s) cassé(s) sur {len(files)} fichier(s) :")
        for p in all_problems:
            print(f"   {p}")
        return 1
    print(f"✅ Liens Markdown OK ({len(files)} fichiers vérifiés, hors vault/).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
