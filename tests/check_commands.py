#!/usr/bin/env python3
"""check_commands.py — cohérence entre les sous-commandes de `legifrance.py`
et celles citées dans la documentation Markdown.

Deux contrôles symétriques, qui couvrent les deux fautes possibles :

1. **Commande citée mais inexistante** — la doc prescrit au modèle une
   commande que le CLI n'expose pas (cas de la v3.1.0 : `ceta` / `constit`
   supprimées par une PR qui n'a touché aucun `.md`).
2. **Commande exposée mais non documentée** — le CLI gagne une commande que
   la doc ignore, donc que le skill n'utilisera jamais.

La liste **autoritaire** des sous-commandes est extraite du parser réel
(`build_parser()`), par import du module et lecture des sous-parsers argparse
— jamais par expression régulière sur le source, qui divergerait à son tour.

Le balayage ne regarde que le **contexte de code** (blocs clôturés et spans
`` `…` ``) : la prose française mentionne `legifrance.py` suivi d'un verbe,
qui n'est pas une commande. Le préfixe de citation `>` est retiré avant la
détection de bloc, sans quoi les exemples de `gabarits-requetes.md` — placés
dans un blockquote — ne seraient jamais lus.

Exclusions : `vault/` (notes Obsidian historiques) et `skill/CHANGELOG.md`
(journal immuable, qui cite légitimement des commandes retirées depuis).

Sans dépendance externe. Code de sortie 1 si au moins une incohérence.

Usage :
    python tests/check_commands.py
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skill" / "scripts" / "legifrance.py"

# Dossiers exclus du contrôle (wikilinks Obsidian, artefacts).
# `.claude` : worktrees d'agents, qui contiennent une copie complète du dépôt.
# Sans cette exclusion, le contrôle compare le parser de CETTE copie aux `.md`
# d'une autre — divergence normale entre copies, signalée comme une faute.
EXCLUDE_DIRS = {".git", ".claude", ".venv", "vault", "__pycache__", ".github"}
# Journal historique : cite légitimement des commandes retirées depuis.
EXCLUDE_FILES = {"skill/CHANGELOG.md"}

BLOCKQUOTE_RE = re.compile(r"^\s{0,3}(?:>\s?)+")
FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
# Une invocation : « legifrance.py » puis des espaces horizontaux (jamais
# `\s`, qui traverserait le saut de ligne et aspirerait le premier mot de la
# ligne suivante) puis un mot commençant par une lettre. Écarte de fait les
# drapeaux (`--json`), les paramètres fictifs (`<LEGIARTI>`), les chemins nus
# suivis d'une ponctuation et les schémas d'arborescence (`← …`).
INVOCATION_RE = re.compile(r"legifrance\.py[ \t]+([A-Za-z][A-Za-z0-9_-]*)")


def load_commands() -> set[str]:
    """Sous-commandes réellement exposées par `build_parser()`.

    L'import se fait sous un nom différent de `__main__` : le module ne
    déclare que des constantes et des fonctions au niveau supérieur, donc
    aucun effet de bord (ni lecture de `.env`, ni appel réseau).
    """
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("legifrance_cli", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Module illisible : {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    commands: set[str] = set()
    for action in module.build_parser()._actions:
        if isinstance(action, argparse._SubParsersAction):
            commands.update(action.choices)
    if not commands:
        # Échouer bruyamment : un contrôle qui ne connaît aucune commande
        # serait silencieusement inutile.
        raise RuntimeError(
            "Aucune sous-commande extraite de build_parser() — introspection "
            "argparse à revoir avant de se fier à ce contrôle."
        )
    return commands


def iter_markdown() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        # as_posix() : sur Windows, str(rel) sépare par « \ » et l'exclusion
        # serait inopérante en local tout en restant verte sur GitHub.
        if rel.as_posix() in EXCLUDE_FILES:
            continue
        files.append(path)
    return sorted(files)


def iter_code_fragments(text: str):
    """Rend les (n° de ligne, fragment) situés en contexte de code."""
    in_fence = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = BLOCKQUOTE_RE.sub("", raw)
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            yield lineno, line
        else:
            for m in INLINE_CODE_RE.finditer(line):
                yield lineno, m.group(1)


def check_file(md: Path, commands: set[str]) -> tuple[list[str], set[str], int]:
    """Renvoie (problèmes, commandes valides citées, nb d'invocations vues)."""
    problems: list[str] = []
    seen: set[str] = set()
    total = 0
    rel = md.relative_to(ROOT).as_posix()
    for lineno, fragment in iter_code_fragments(md.read_text(encoding="utf-8")):
        for m in INVOCATION_RE.finditer(fragment):
            token = m.group(1)
            total += 1
            if token in commands:
                seen.add(token)
            else:
                problems.append(
                    f"{rel}:{lineno}: commande inconnue « {token} » "
                    f"(exposées : {', '.join(sorted(commands))})"
                )
    return problems, seen, total


def main() -> int:
    commands = load_commands()
    files = iter_markdown()

    problems: list[str] = []
    documented: set[str] = set()
    invocations = 0
    for md in files:
        file_problems, seen, total = check_file(md, commands)
        problems.extend(file_problems)
        documented |= seen
        invocations += total

    undocumented = sorted(commands - documented)
    if undocumented:
        problems.append(
            "documentation absente : "
            + ", ".join(f"« {c} »" for c in undocumented)
            + " — commande(s) exposée(s) par legifrance.py mais citée(s) dans "
            "aucun fichier Markdown, donc jamais mobilisable(s) par le skill."
        )

    if problems:
        print(f"❌ {len(problems)} incohérence(s) doc ↔ CLI sur {len(files)} fichier(s) :")
        for p in problems:
            print(f"   {p}")
        return 1
    print(
        f"✅ Commandes documentées OK ({invocations} invocation(s) sur "
        f"{len(files)} fichiers ; {len(commands)} sous-commandes exposées, "
        "toutes documentées)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
