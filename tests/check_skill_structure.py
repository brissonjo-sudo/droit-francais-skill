#!/usr/bin/env python3
"""Vérifie la conservation A4 et décrit le paquet d'instructions, hors réseau."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
CORRESPONDANCE = ROOT / "tests/fixtures/rj-correspondance.csv"
SOURCE_DIGEST = "ac774ea9df1fb9b28abb77b5076dde8e3b05f6085eecfdd342cdf04ac17ea57d"
OLD_P1 = "`scripts/legifrance.py` **en premier**, à défaut\n`web_fetch`/`web_search` sur un domaine officiel — ordre normé à\nl'**étape 2**, *échelle de récupération*"
NEW_P1 = "selon l'ordre normé de l'**étape 2**, *échelle de récupération* :\nconnecteur MCP officiel disponible, sinon `scripts/legifrance.py`,\nà défaut `web_fetch`/`web_search` sur un domaine officiel"


def normalize(text: str) -> str:
    """Normalise seulement Unicode et espaces ; conserve mots et ponctuation."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def expected_text(row: dict[str, str]) -> str:
    """Applique exclusivement les arbitrages A4b et le rebasing des liens."""
    text = row["texte_source"].replace("\r\n", "\n")
    text = text.replace(OLD_P1, NEW_P1)
    text = text.replace("module PÉNAL §6", "module PÉNAL §5")
    text = text.replace("(voir §6).", "(voir §5).")
    if row["identifiant"] == "RJ-L0001":
        text = text.replace("  version: 3.5.0\n", "  version: 3.6.0\n")
    if row["identifiant"] == "RJ-L0019":
        text = text.replace("(v3.5.0)", "(v3.6.0)")
    if row["fichier_realise"].startswith("skill/references/"):
        for old, new in (("](references/", "]("), ("](profils/", "](../profils/"), ("](scripts/", "](../scripts/"), ("](CHANGELOG.md)", "](../CHANGELOG.md)")):
            text = text.replace(old, new)
    return text


def source_digest(rows: list[dict[str, str]]) -> str:
    """Empreinte de toutes les unités originales A4, avant transformations."""
    payload = [
        (r["identifiant"], unicodedata.normalize("NFC", r["texte_source"].replace("\r\n", "\n")))
        for r in rows
    ]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def check_rows(rows: list[dict[str, str]], root: Path = ROOT) -> list[str]:
    """Vérifie l'origine figée et chaque intervalle réalisé du paquet."""
    errors = []
    if len(rows) != 337 or len({r["identifiant"] for r in rows}) != 337:
        errors.append("337 unités distinctes obligatoires")
    if source_digest(rows) != SOURCE_DIGEST:
        errors.append("unités source différentes de la correspondance A4 figée")
    for row in rows:
        name = row["identifiant"]
        relative = PurePosixPath(row["fichier_realise"])
        if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("skill",) or "\\" in str(relative) or ":" in str(relative):
            errors.append(f"{name} : chemin réalisé hors skill")
            continue
        path = root.joinpath(*relative.parts)
        if not path.resolve().is_relative_to((root / "skill").resolve()) or not path.is_file():
            errors.append(f"{name} : fichier réalisé absent ou hors skill")
            continue
        try:
            first, last = int(row["debut_realise"]), int(row["fin_realisee"])
            lines = path.read_text(encoding="utf-8").splitlines()
            if not 1 <= first <= last <= len(lines):
                raise ValueError("intervalle hors fichier")
            actual = normalize("\n".join(lines[first - 1:last]))
        except (ValueError, OSError) as exc:
            errors.append(f"{name} : {exc}")
            continue
        expected = normalize(expected_text(row))
        if normalize(row["texte_realise"]) != expected or actual != expected:
            errors.append(f"{name} : texte différent à l'emplacement réalisé")
    return errors


def instruction_manifest(root: Path = ROOT) -> dict:
    """Inventorie les instructions distribuées ; ne prétend pas tracer leur lecture."""
    paths = [root / "skill/SKILL.md", *sorted((root / "skill/references").glob("*.md"))]
    files = []
    for path in paths:
        data = path.read_text(encoding="utf-8").encode("utf-8")
        files.append({"path": path.relative_to(root).as_posix(), "sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)})
    payload = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"scope": "instruction-package-not-runtime-reads", "files": files, "sha256": hashlib.sha256(payload).hexdigest()}


def main() -> int:
    """Contrôle local ou manifeste JSON, sans importer de client modèle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    if args.manifest:
        print(json.dumps(instruction_manifest(), ensure_ascii=False, indent=2))
        return 0
    with CORRESPONDANCE.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    errors = check_rows(rows)
    for error in errors:
        print(error)
    if not errors:
        print("Correspondance A4b : 337/337 unites verifiees.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
