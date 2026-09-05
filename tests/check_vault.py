#!/usr/bin/env python3
"""Contrôle le maillage du vault Obsidian lu par la vue graphe (Graphify).

``check_links.py`` exclut ``vault/`` : il vérifie des liens Markdown, pas des
wikiliens, et le vault vit hors du paquet. Rien ne surveillait donc ce
maillage, et il a dérivé — au 5 septembre 2026, deux notes sur treize portaient
une section de liens, trois agrégats n'avaient aucun lien sortant et deux notes
de version aucun lien entrant. Une note isolée est invisible dans la vue
graphe : elle existe, mais aucun chemin de lecture n'y mène.

Quatre invariants, chacun rendant une note réellement atteignable :

1. **Section de liens** — chaque note porte ``## Liens (maillage Graphify)``.
2. **Aucune note orpheline** — chaque note reçoit au moins un lien entrant.
3. **Aucun cul-de-sac** — chaque note émet au moins un lien sortant.
4. **Liens résolus** — sauf les références conceptuelles que l'index déclare
   explicitement comme n'existant pas en fichier séparé.

Le quatrième point ne duplique aucune liste : la tolérance est **dérivée de
l'index lui-même**, section « Fichiers supprimés (remplacés par agrégats) ».
Déclarer une nouvelle notion agrégée dans l'index suffit donc à la faire
accepter ici ; l'oublier fait échouer ce contrôle, ce qui est le but.

    python tests/check_vault.py
    python tests/check_vault.py --vault chemin/vers/vault

Sortie 0 si le maillage tient, 1 sinon.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
INDEX = "index-recherche-juridique"
TITRE_SECTION = "## Liens (maillage Graphify)"
SECTION_DECLARATION = "## Fichiers supprimés (remplacés par agrégats)"

#: Un wikilien : ``[[cible]]``, ``[[cible|alias]]`` ou ``[[cible#titre]]``.
_WIKILIEN = re.compile(r"\[\[([^\]\n]+)\]\]")
#: Blocs et fragments de code. Obsidian n'y interprète aucun wikilien : les
#: retirer avant l'analyse évite de compter comme lien ce qui n'en est pas un,
#: et permet à une note de citer la syntaxe sans créer de nœud fantôme.
_BLOC_CODE = re.compile(r"```.*?```", re.S)
_CODE_EN_LIGNE = re.compile(r"`[^`\n]*`")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _hors_code(texte: str) -> str:
    return _CODE_EN_LIGNE.sub(" ", _BLOC_CODE.sub(" ", texte))


def _cible(brut: str) -> str:
    """Réduit un wikilien à son nom de note : alias, ancre et ``.md`` retirés."""
    cible = brut.split("|", 1)[0].split("#", 1)[0].strip()
    return cible[:-3] if cible.endswith(".md") else cible


def _liens(texte: str) -> list[str]:
    return [_cible(m.group(1)) for m in _WIKILIEN.finditer(_hors_code(texte))]


def _notions_declarees(texte_index: str) -> set[str]:
    """Relève les notions que l'index déclare absentes du vault.

    Elles sont écrites en ``code`` dans la section de déclaration — c'est
    justement pour ne pas créer les nœuds fantômes que cette section annonce
    comme inexistants. Le préfixe est conservé sans sa partie variable, pour
    qu'une déclaration de ``mode 1``–``mode 14`` couvre ``mode 10`` sans que
    l'index ait à énumérer les quatorze.
    """
    debut = texte_index.find(SECTION_DECLARATION)
    if debut == -1:
        return set()
    fin = texte_index.find("\n## ", debut + len(SECTION_DECLARATION))
    section = texte_index[debut : fin if fin != -1 else len(texte_index)]
    notions = set()
    for fragment in _CODE_EN_LIGNE.findall(section):
        valeur = fragment.strip("`").strip()
        if valeur:
            notions.add(_prefixe(valeur))
    return notions


def _prefixe(valeur: str) -> str:
    """Retire la partie variable d'une notion : numéro ou nom de module."""
    sans_numero = re.sub(r"\s*\d+\s*$", "", valeur).strip()
    if sans_numero != valeur:
        return sans_numero or valeur
    if valeur.startswith("module "):
        return "module"
    return valeur


def controler(vault: Path) -> list[str]:
    notes = {p.stem: p for p in sorted(vault.glob("*.md"))}
    if not notes:
        return [f"aucune note trouvée dans {vault}"]
    if INDEX not in notes:
        return [f"note d'index absente : {INDEX}.md"]

    tolerees = _notions_declarees(notes[INDEX].read_text(encoding="utf-8"))
    defauts: list[str] = []
    sortants: dict[str, list[str]] = {}
    entrants: dict[str, int] = dict.fromkeys(notes, 0)

    for nom, chemin in notes.items():
        texte = chemin.read_text(encoding="utf-8")
        if TITRE_SECTION not in texte:
            defauts.append(f"{nom} : section « {TITRE_SECTION.strip('# ')} » absente")
        sortants[nom] = _liens(texte)

    # Une même notion citée dix fois dans une note est un seul défaut à
    # corriger : la signaler dix fois noierait les autres.
    signales: set[tuple[str, str]] = set()
    for source, cibles in sortants.items():
        if not cibles:
            defauts.append(f"{source} : cul-de-sac, aucun lien sortant")
        for cible in cibles:
            if cible in entrants:
                # Un auto-lien ne rend pas une note atteignable depuis ailleurs.
                if cible != source:
                    entrants[cible] += 1
            elif _prefixe(cible) not in tolerees and (source, cible) not in signales:
                signales.add((source, cible))
                defauts.append(
                    f"{source} : lien non résolu [[{cible}]] — créer la note, "
                    f"ou déclarer la notion dans « {SECTION_DECLARATION.strip('# ')} » "
                    "de l'index si elle vit dans un agrégat"
                )

    for nom, compte in entrants.items():
        if compte == 0:
            defauts.append(f"{nom} : orpheline, aucun lien entrant")

    return defauts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vérifie le maillage du vault Obsidian (vue graphe)."
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=RACINE / "vault",
        help="Dossier du vault (défaut : vault/ à la racine du dépôt).",
    )
    arguments = parser.parse_args()

    defauts = controler(arguments.vault)
    if defauts:
        print(f"❌ Maillage du vault : {len(defauts)} défaut(s).")
        for defaut in defauts:
            print(f"   - {defaut}")
        return 1

    total = len(list(arguments.vault.glob("*.md")))
    print(
        f"✅ Maillage du vault OK ({total} notes) : section de liens partout, "
        "aucune orpheline, aucun cul-de-sac, aucun lien non résolu non déclaré."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
