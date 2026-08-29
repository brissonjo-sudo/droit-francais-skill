"""Configuration d'environnement commune à Légifrance et Judilibre."""

from __future__ import annotations

import os
from pathlib import Path

from .errors import LegifranceError

ENVIRONMENTS = {
    "prod": {
        "token": "https://oauth.piste.gouv.fr/api/oauth/token",
        "api": "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app",
        "judilibre": "https://api.piste.gouv.fr/cassation/judilibre/v1.0",
    },
    "sandbox": {
        "token": "https://sandbox-oauth.piste.gouv.fr/api/oauth/token",
        "api": "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app",
        "judilibre": "https://sandbox-api.piste.gouv.fr/cassation/judilibre/v1.0",
    },
}

SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(script_dir: Path | None = None) -> None:
    """Charge un fichier ``.env`` sans écraser l'environnement explicite.

    Ordre de recherche : ``LEGIFRANCE_DOTENV``, ``./.env``, puis le fichier
    voisin du CLI. Le paramètre ``script_dir`` sert aux tests et aux futurs
    points d'entrée sans changer le comportement historique.
    """
    candidates = []
    explicit = os.environ.get("LEGIFRANCE_DOTENV")
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(Path.cwd() / ".env")
    candidates.append((script_dir or SCRIPTS_DIR) / ".env")

    seen = set()
    for path in candidates:
        try:
            if not path.is_file():
                continue
            real = path.resolve()
        except OSError:
            continue
        if real in seen:
            continue
        seen.add(real)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def legifrance_environment() -> dict:
    """Retourne les endpoints Légifrance de l'environnement actif."""
    name = os.environ.get("LEGIFRANCE_ENV", "prod").lower()
    if name not in ENVIRONMENTS:
        raise LegifranceError(
            f"LEGIFRANCE_ENV invalide : {name!r} (attendu 'prod' ou 'sandbox')",
            exit_code=2,
        )
    return ENVIRONMENTS[name]


def judilibre_base() -> str:
    """Retourne l'URL Judilibre, avec repli sur ``LEGIFRANCE_ENV``."""
    name = (os.environ.get("JUDILIBRE_ENV") or "").strip().lower()
    if not name:
        return legifrance_environment()["judilibre"]
    if name not in ENVIRONMENTS:
        raise LegifranceError(
            f"JUDILIBRE_ENV invalide : {name!r} (attendu 'prod' ou 'sandbox')",
            exit_code=2,
        )
    return ENVIRONMENTS[name]["judilibre"]
