"""Client Légifrance : authentification OAuth2 et appels API JSON."""

from __future__ import annotations

import json
import os
import urllib.parse

from .config import legifrance_environment
from .errors import LegifranceError
from .transport import http_post_json


def get_token() -> str:
    """Récupère un jeton OAuth2 ``client_credentials`` PISTE."""
    client_id = os.environ.get("LEGIFRANCE_CLIENT_ID")
    client_secret = os.environ.get("LEGIFRANCE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise LegifranceError(
            "Identifiants PISTE absents : voie outillée indisponible.\n"
            "→ Bascule attendue : voie de repli web (gabarits web_search / "
            "web_fetch sur domaine officiel — references/gabarits-requetes.md, "
            "échelle de récupération à l'étape 2 du SKILL.md).\n"
            "La clé PISTE est OPTIONNELLE : le skill reste pleinement "
            "opérationnel sans elle, et la règle de provenance s'applique à "
            "l'identique sur la voie web. Ne pas demander de clé à "
            "l'utilisateur : basculer.\n"
            "Ce que la clé apporte, et qui se relève sinon à la main sur la "
            "fiche officielle : identifiant, date de version en vigueur et "
            "statut (en vigueur / modifié / abrogé) lus dans une réponse API "
            "déterministe.\n"
            "L'activer (gratuit, 2 minutes) :\n"
            "  1. Compte + application abonnée à l'API « Légifrance » sur "
            "https://piste.gouv.fr\n"
            "  2. Copier .env.example en .env et y coller les deux identifiants\n"
            "       cp skill/scripts/.env.example skill/scripts/.env\n"
            "     (ou : export LEGIFRANCE_CLIENT_ID=… LEGIFRANCE_CLIENT_SECRET=…)\n"
            "  3. Relancer la commande.\n"
            "Détail pas-à-pas : skill/scripts/README.md",
            exit_code=2,
        )
    payload = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid",
        }
    ).encode("utf-8")
    try:
        data = http_post_json(
            legifrance_environment()["token"],
            payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
    except LegifranceError as exc:
        raise LegifranceError(
            f"Authentification PISTE échouée : {exc}",
            exit_code=3,
        ) from exc
    token = data.get("access_token")
    if not token:
        raise LegifranceError(
            f"Réponse OAuth sans access_token : {data}",
            exit_code=3,
        )
    return token


def api_call(path: str, body: dict, token: str) -> dict:
    """Exécute un appel authentifié sur l'API Légifrance."""
    url = legifrance_environment()["api"] + path
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return http_post_json(url, json.dumps(body).encode("utf-8"), headers)
