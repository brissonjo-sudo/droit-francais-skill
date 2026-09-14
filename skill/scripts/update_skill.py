#!/usr/bin/env python3
"""Mise à jour optionnelle et prudente du skill via le CLI ``skills``.

Ce script n'est jamais actif par défaut. Il est appelé au premier usage de la
journée seulement si ``.recherche-juridique-update.json`` contient
``{"automatic": true}``. Les fichiers personnels sont sauvegardés puis
restaurés, même si la mise à jour échoue.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory


SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG = SKILL_ROOT / ".recherche-juridique-update.json"
PERSONAL_FILES = (
    SKILL_ROOT / "profil.md",
    SKILL_ROOT / "scripts" / ".env",
)
INTERVAL = timedelta(hours=24)


def read_version() -> str:
    """Retourne la version déclarée, sans dépendre d'un parseur YAML."""
    try:
        for line in (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines():
            if line.startswith("  version:"):
                return line.partition(":")[2].strip()
    except OSError:
        pass
    return "inconnue"


def load_config() -> dict[str, object] | None:
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        print("UPDATE_SKIPPED configuration de mise à jour illisible")
        return None
    if not isinstance(config, dict) or config.get("automatic") is not True:
        return None
    return config


def due(config: dict[str, object], now: datetime) -> bool:
    raw = config.get("last_attempt_at")
    if not isinstance(raw, str):
        return True
    try:
        previous = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return True
    if previous.tzinfo is None:
        return True
    return now - previous.astimezone(UTC) >= INTERVAL


def scope_argument() -> str | None:
    """Déduit le périmètre sans jamais deviner lorsqu'il est ambigu."""
    home = Path.home().resolve()
    try:
        relative = SKILL_ROOT.resolve().relative_to(home)
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) >= 3 and parts[0] in {".codex", ".claude", ".cursor", ".copilot"} and parts[1] == "skills":
        return "-g"
    return None


def backup_personal_files(directory: Path) -> list[tuple[Path, Path]]:
    backups: list[tuple[Path, Path]] = []
    for source in PERSONAL_FILES:
        if source.is_file():
            destination = directory / str(len(backups))
            shutil.copy2(source, destination)
            backups.append((source, destination))
    return backups


def restore_personal_files(backups: list[tuple[Path, Path]]) -> None:
    for destination, source in backups:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def save_config(config: dict[str, object]) -> None:
    CONFIG.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    config = load_config()
    if config is None:
        return 0
    now = datetime.now(UTC)
    if not due(config, now):
        return 0
    scope = scope_argument()
    if scope is None:
        print("UPDATE_SKIPPED installation non globale ou emplacement non reconnu")
        return 0
    if shutil.which("npx") is None:
        print("UPDATE_SKIPPED npx indisponible")
        return 0

    before = read_version()
    command = ["npx", "skills", "update", "recherche-juridique", "-y", scope]
    with TemporaryDirectory(prefix="recherche-juridique-update-") as tmp:
        backups = backup_personal_files(Path(tmp))
        try:
            result = subprocess.run(command, check=False, text=True, capture_output=True)
        except OSError as exc:
            print(f"UPDATE_FAILED lancement impossible : {exc}")
            return 0
        finally:
            restore_personal_files(backups)

    config["last_attempt_at"] = now.isoformat().replace("+00:00", "Z")
    save_config(config)
    if result.returncode != 0:
        print("UPDATE_FAILED le CLI skills a refusé la mise à jour")
        return 0
    after = read_version()
    if after != before:
        print(f"UPDATE_APPLIED recherche-juridique {before} → {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
