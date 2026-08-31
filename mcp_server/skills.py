#!/usr/bin/env python3
"""Catalogue de compétences au format de l'extension Skills (SEP-2640).

Ce module calcule, sans rien exposer, la charge utile que réclameraient les
méthodes ``skills/list`` et ``skills/get`` : identifiants ``skill://``,
frontmatter du skill, liste des ressources et empreinte SHA-256 de chacune.

**Pourquoi la partie transport est absente.** Le SDK MCP valide chaque requête
entrante contre une union fermée de types. Ni la version 1.27 ni la 2.1.1 ne
connaissent ``skills/list`` : une telle requête est rejetée avant d'atteindre
un gestionnaire. Brancher l'extension aujourd'hui supposerait de rustiner
cette union, sur une proposition qui n'appartient pas encore à la
spécification stable. Le jour où le SDK la portera, il ne restera qu'à
déclarer la capacité et à router les trois méthodes vers les fonctions
ci-dessous.

Le module ne dépend que de la bibliothèque standard : les tests l'importent
sans installer le SDK.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent

#: Espace de noms du serveur dans les identifiants ``skill://<serveur>/…``.
SERVER_NAMESPACE = "droit-francais"

#: Capacité à déclarer à l'initialisation, le jour où le SDK la supporte.
EXTENSION_CAPABILITY: dict[str, dict[str, Any]] = {
    "io.modelcontextprotocol/skills": {}
}

#: Dossiers de `skill/` publiés comme ressources d'accompagnement. Les scripts
#: en sont exclus : ce sont des programmes, pas des instructions, et le serveur
#: expose déjà leurs capacités sous forme d'outils.
COMPANION_DIRECTORIES: tuple[str, ...] = ("references", "profils")


def _digest(content: str) -> str:
    """Empreinte d'une ressource textuelle : SHA-256 des octets UTF-8."""
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_frontmatter(text: str) -> dict[str, str]:
    """Lit `name` et `description` d'un frontmatter YAML, sans dépendance.

    Seules les clés de premier niveau à valeur scalaire sont retenues, les
    continuations indentées étant recollées. Les blocs imbriqués (`metadata`)
    sont ignorés : l'extension n'attend que `name` et `description`.
    """
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}

    valeurs: dict[str, str] = {}
    cle: str | None = None
    dans_bloc_imbrique = False
    for ligne in lines[1:end]:
        if not ligne.strip():
            continue
        indente = ligne[:1].isspace()
        if not indente:
            nom, _, reste = ligne.partition(":")
            nom = nom.strip()
            reste = reste.strip()
            if not reste:  # ouverture d'un bloc imbriqué
                cle, dans_bloc_imbrique = None, True
                continue
            dans_bloc_imbrique = False
            cle = nom
            valeurs[cle] = reste
        elif cle and not dans_bloc_imbrique:
            valeurs[cle] = f"{valeurs[cle]} {ligne.strip()}".strip()
    return {c: v for c, v in valeurs.items() if c in {"name", "description"}}


def _companion_files(skill_dir: Path) -> Iterable[Path]:
    """Fichiers d'accompagnement, dans un ordre stable entre deux exécutions."""
    for nom_dossier in COMPANION_DIRECTORIES:
        dossier = skill_dir / nom_dossier
        if dossier.is_dir():
            yield from sorted(dossier.glob("*.md"))


def build_skill(
    skill_dir: Path | None = None, server: str = SERVER_NAMESPACE
) -> dict[str, Any]:
    """Construit l'entrée de catalogue d'un skill à partir de ses fichiers.

    L'espace de noms des identifiants suit le `name` du frontmatter, comme
    l'exige l'extension, indépendamment du nom du dossier sur le disque.
    """
    skill_dir = skill_dir or (ROOT / "skill")
    fichier_noyau = skill_dir / "SKILL.md"
    if not fichier_noyau.is_file():
        raise FileNotFoundError(f"SKILL.md introuvable dans {skill_dir}.")

    texte_noyau = fichier_noyau.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(texte_noyau)
    nom = frontmatter.get("name")
    if not nom:
        raise ValueError("Le frontmatter de SKILL.md ne déclare pas de `name`.")

    base = f"skill://{server}/{nom}"
    uri_noyau = f"{base}/SKILL.md"
    ressources = [{"uri": uri_noyau, "digest": _digest(texte_noyau)}]
    for chemin in _companion_files(skill_dir):
        relatif = chemin.relative_to(skill_dir).as_posix()
        ressources.append(
            {
                "uri": f"{base}/{relatif}",
                "digest": _digest(chemin.read_text(encoding="utf-8")),
            }
        )
    return {"uri": uri_noyau, "frontmatter": frontmatter, "resources": ressources}


def build_catalogue(
    skill_dir: Path | None = None, server: str = SERVER_NAMESPACE
) -> dict[str, Any]:
    """Charge utile exacte de ``skills/list`` — un seul skill, sans pagination."""
    return {"skills": [build_skill(skill_dir, server)]}


def resource_index(
    skill_dir: Path | None = None, server: str = SERVER_NAMESPACE
) -> dict[str, Path]:
    """Table identifiant ``skill://`` → fichier, pour servir ``resources/read``."""
    skill_dir = skill_dir or (ROOT / "skill")
    skill = build_skill(skill_dir, server)
    prefixe = skill["uri"].rsplit("/SKILL.md", 1)[0] + "/"
    index: dict[str, Path] = {}
    for ressource in skill["resources"]:
        relatif = ressource["uri"][len(prefixe) :]
        index[ressource["uri"]] = skill_dir / relatif
    return index


def read_resource(
    uri: str, skill_dir: Path | None = None, server: str = SERVER_NAMESPACE
) -> str:
    """Contenu textuel d'une ressource du catalogue, ou `KeyError` si inconnue."""
    index = resource_index(skill_dir, server)
    if uri not in index:
        raise KeyError(f"Ressource hors catalogue : {uri}")
    return index[uri].read_text(encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover - inspection manuelle
    import json

    print(json.dumps(build_catalogue(), ensure_ascii=False, indent=2))
