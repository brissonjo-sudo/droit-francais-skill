"""Parité structurelle des README FR/EN, hors traduction de la prose.

Ce contrôle statique ne vérifie ni la qualité de la traduction ni les sources
externes. Sans dépendance ni réseau : python tests/check_readme_parity.py.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
NAVIGATION = "[🇫🇷 Français](README.md) | [🇬🇧 English](README.en.md)"
VERSION = re.compile(r"\b(?:v)?(\d+\.\d+\.\d+(?:-[\w.]+)?)\b")
LINK = re.compile(r"\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)")


def structure(text: str) -> dict:
    """Extraire l'ordre des titres, dimensions des tableaux et blocs clôturés."""
    headings, tables, blocks, prose = [], [], [], []
    table, body = [], []
    fence = language = ""
    anchors, pending, slugs = {}, [], Counter()
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(\w*)\s*$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                blocks.append((language, body))
                fence, body = "", []
            else:
                body.append(line)
            continue
        if marker:
            fence, language = marker[1], marker[2].lower()
            continue
        prose.append(line)
        pending.extend(re.findall(r'<a\s+id="([^"]+)"\s*></a>', line))
        title = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if title:
            headings.append(len(title[1]))
            slug = re.sub(r"[^\w -]", "", title[2].lower()).replace(" ", "-")
            number = slugs[slug]
            slugs[slug] += 1
            anchors[slug + (f"-{number}" if number else "")] = len(headings)
            for anchor in pending:
                anchors[anchor] = len(headings)
            pending = []
        if line.strip().startswith("|") and line.strip().endswith("|"):
            table.append(len(re.split(r"(?<!\\)\|", line.strip())) - 2)
        elif table:
            tables.append(tuple(table))
            table = []
    if table:
        tables.append(tuple(table))
    if fence:
        raise ValueError("bloc de code non clôturé")
    commands = []
    for lang, lines in blocks:
        if lang in ("bash", "sh", "powershell", "json"):
            # Les commentaires explicatifs sont traduisibles ; les commandes
            # et valeurs JSON doivent conserver leur contenu et leur ordre.
            commands.append((lang, tuple(s for line in lines
                if (s := re.sub(r"\s+#.*$", "", line.strip())) and not s.startswith("#"))))
    outside = "\n".join(prose)
    def target(link: str) -> str:
        if link.startswith("#"):
            return f"#titre-{anchors[link[1:]]}" if link[1:] in anchors else link
        # Une page traduite peut pointer vers son équivalent de langue ;
        # les URL externes gardent leur cible exacte.
        if not re.match(r"\w+://", link):
            return re.sub(r"\.(?:en|fr)\.md(?=#|$)", ".md", link)
        return link
    return {"titres": headings, "tableaux": tables,
            "blocs": [lang for lang, _ in blocks], "commandes": commands,
            "liens": Counter(target(link) for link in LINK.findall(outside)),
            "versions": Counter(VERSION.findall(text))}


def check_pair(french: str, english: str) -> list[str]:
    problems = []
    for name, text in (("README.md", french), ("README.en.md", english)):
        if not text.splitlines() or text.splitlines()[0] != NAVIGATION:
            problems.append(f"{name}: navigation bilingue absente ou modifiée en première ligne")
    try:
        fr, en = structure(french), structure(english)
    except ValueError as error:
        return problems + [str(error)]
    for field in fr:
        if fr[field] != en[field]:
            problems.append(f"README FR/EN : parité différente pour {field}")
    return problems


def main() -> int:
    problems = check_pair((ROOT / "README.md").read_text(encoding="utf-8"),
                          (ROOT / "README.en.md").read_text(encoding="utf-8"))
    for problem in problems:
        print(problem)
    if not problems:
        print("Parité README FR/EN OK (structure, commandes, liens, versions et navigation).")
    return int(bool(problems))


if __name__ == "__main__":
    raise SystemExit(main())
