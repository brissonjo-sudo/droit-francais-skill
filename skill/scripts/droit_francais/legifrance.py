"""Client Légifrance : authentification OAuth2 et appels API JSON."""

from __future__ import annotations

import json
import os
import time
import urllib.parse

from .config import legifrance_environment
from .errors import LegifranceError
from .transport import http_post_json

#: Cache du jeton PISTE, commun à Légifrance et au mode OAuth de Judilibre :
#: un seul émetteur, un seul jeton. Reste un dictionnaire nommé parce que le
#: CLI historique l'importe sous ce nom.
_TOKEN_CACHE: dict = {}
#: Marge retirée à ``expires_in`` : un jeton est renouvelé avant son terme,
#: jamais présenté à la limite, où l'horloge de l'émetteur peut différer.
TOKEN_SAFETY_MARGIN_SECONDS = 60
#: Durée retenue quand l'émetteur omet ``expires_in`` — volontairement courte.
DEFAULT_TOKEN_LIFETIME_SECONDS = 600


def clear_token_cache() -> None:
    """Vide le cache de jeton de l'exécution courante."""
    _TOKEN_CACHE.clear()


def _cached_token() -> str | None:
    token = _TOKEN_CACHE.get("token")
    expires_at = _TOKEN_CACHE.get("expires_at")
    if not token or expires_at is None or time.monotonic() >= expires_at:
        return None
    return token


def _remember_token(token: str, lifetime: object) -> None:
    try:
        seconds = int(lifetime)
    except (TypeError, ValueError):
        seconds = DEFAULT_TOKEN_LIFETIME_SECONDS
    ttl = seconds - TOKEN_SAFETY_MARGIN_SECONDS
    _TOKEN_CACHE.clear()
    if ttl > 0:
        _TOKEN_CACHE.update(token=token, expires_at=time.monotonic() + ttl)


def get_token(*, force_refresh: bool = False) -> str:
    """Récupère un jeton OAuth2 ``client_credentials`` PISTE.

    Le jeton est mis en cache jusqu'à ``expires_in`` moins une marge de
    sécurité : une opération n'en redemande pas un à chaque appel, et une
    indisponibilité passagère du serveur d'authentification ne casse plus une
    session dont le jeton est encore valide. ``force_refresh`` sert au seul
    renouvellement tenté après un ``401`` amont.
    """
    if not force_refresh:
        cached = _cached_token()
        if cached:
            return cached
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
    _remember_token(token, data.get("expires_in"))
    return token


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def api_call(path: str, body: dict, token: str) -> dict:
    """Exécute un appel authentifié sur l'API Légifrance.

    Un ``401`` déclenche **un seul** renouvellement du jeton, puis une seconde
    tentative ; l'erreur suivante est propagée telle quelle. Pas de boucle :
    un jeton frais refusé n'est pas un jeton périmé, mais une configuration
    ou un abonnement à corriger.
    """
    url = legifrance_environment()["api"] + path
    payload = json.dumps(body).encode("utf-8")
    try:
        return http_post_json(url, payload, _headers(token))
    except LegifranceError as exc:
        if exc.http_status != 401:
            raise
    return http_post_json(url, payload, _headers(get_token(force_refresh=True)))
