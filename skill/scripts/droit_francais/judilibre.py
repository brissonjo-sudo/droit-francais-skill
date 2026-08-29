"""Client Judilibre avec authentification KeyId puis OAuth2 en repli."""

from __future__ import annotations

import os
import urllib.parse

from .config import judilibre_base
from .errors import LegifranceError
from .legifrance import get_token
from .transport import http_get_json

_TOKEN_CACHE: dict = {}


def clear_token_cache() -> None:
    """Vide le cache OAuth de l'exécution courante."""
    _TOKEN_CACHE.clear()


def get_token_cached() -> str:
    """Évite de redemander un jeton à chaque appel d'une même exécution."""
    if "token" not in _TOKEN_CACHE:
        _TOKEN_CACHE["token"] = get_token()
    return _TOKEN_CACHE["token"]


def auth_modes() -> list:
    """Construit les modes d'authentification à essayer, dans l'ordre."""
    modes = []
    key_id = os.environ.get("JUDILIBRE_KEY_ID") or os.environ.get("PISTE_KEY_ID")
    if key_id:
        modes.append(("KeyId", {"KeyId": key_id, "Accept": "application/json"}))
    modes.append(("OAuth", None))
    return modes


def judilibre_get(path: str, params: dict) -> dict:
    """Appelle un endpoint Judilibre et renvoie son document JSON.

    Les listes sont encodées en paramètres répétés conformément à la
    spécification Judilibre.
    """
    query = urllib.parse.urlencode(
        {key: value for key, value in params.items() if value not in (None, "", [], ())},
        doseq=True,
    )
    base = judilibre_base()
    url = f"{base}{path}" + (f"?{query}" if query else "")

    last: LegifranceError | None = None
    for label, headers in auth_modes():
        if headers is None:
            headers = {
                "Authorization": f"Bearer {get_token_cached()}",
                "Accept": "application/json",
            }
        try:
            return http_get_json(url, headers)
        except LegifranceError as exc:
            if exc.http_status in (401, 403):
                last = LegifranceError(
                    f"Authentification Judilibre refusée en mode {label} : {exc}",
                    exit_code=3,
                    http_status=exc.http_status,
                )
                continue
            raise
    raise last or LegifranceError(
        "Aucun mode d'authentification Judilibre accepté. Vérifier que "
        "l'application PISTE est bien abonnée à l'API « Judilibre », ou "
        "renseigner JUDILIBRE_KEY_ID.",
        exit_code=3,
    )
