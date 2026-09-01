"""Transport HTTP JSON partagé par les clients des API officielles.

Deux règles, issues de l'audit du 1er septembre 2026 :

* **Reprise bornée.** Les appels sont strictement en lecture et idempotents :
  un ``429`` ou un ``5xx`` ponctuel de PISTE est rejoué, au plus deux fois,
  avec un recul exponentiel et un peu d'aléa, en respectant ``Retry-After``
  quand l'en-tête est présent. Aucun ``4xx`` autre que ``429`` n'est rejoué.
  Le tout tient dans un budget de temps qui reste sous le délai réseau d'une
  seule requête : la reprise absorbe un incident bref, elle ne contourne pas
  les plafonds fixés côté serveur.
* **Message public stable, détail réservé au journal.** L'appelant reçoit un
  code, une phrase actionnable et l'hôte amont — jamais l'URL complète avec
  ses paramètres ni un fragment de corps de réponse. Ceux-ci vont dans
  ``LegifranceError.detail``, que le serveur MCP journalise et que le CLI
  affiche sur la sortie d'erreur, pour le seul titulaire des clés.
"""

from __future__ import annotations

import json
import logging
import random
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

from .errors import LegifranceError

DEFAULT_TIMEOUT = 30
#: Tentatives au plus, première comprise : deux reprises, jamais davantage.
MAX_ATTEMPTS = 3
#: Budget total des reprises, attentes comprises. Inférieur au délai d'une
#: seule requête : la reprise ne doit pas allonger un appel au-delà de ce que
#: le serveur tolère déjà pour une requête lente.
RETRY_BUDGET_SECONDS = 8.0
#: Recul de base, doublé à chaque tentative, majoré d'un aléa de 0 à 50 %.
BACKOFF_BASE_SECONDS = 0.5
#: Seuls statuts rejoués : saturation et défauts serveur passagers.
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})

LOGGER = logging.getLogger("droit_francais.transport")

#: Indirection pour les tests : la suite ne doit jamais dormir réellement.
_sleep = time.sleep


def http_post_json(
    url: str,
    data: bytes,
    headers: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Exécute un POST et décode une réponse JSON."""
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    return _perform(request, timeout, not_found_exit_code=4)


def http_get_json(
    url: str,
    headers: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Exécute un GET et décode une réponse JSON."""
    request = urllib.request.Request(url, headers=headers, method="GET")
    return _perform(request, timeout, not_found_exit_code=5)


def _host(url: str) -> str:
    """Hôte amont seul : information publique, sans chemin ni paramètres."""
    return urllib.parse.urlsplit(url).hostname or "source amont"


def _public_message(code: int, host: str) -> str:
    """Phrase stable et actionnable, sans charge de débogage."""
    if code == 429:
        return f"Source amont saturée ({host}, HTTP 429) : réessayer dans quelques instants."
    if code >= 500:
        return f"Source amont indisponible ({host}, HTTP {code}) : réessayer plus tard."
    if code == 404:
        return f"Ressource introuvable sur {host} (HTTP 404)."
    if code in (401, 403):
        return (
            f"Accès refusé par {host} (HTTP {code}) : configuration ou abonnement "
            "du service à vérifier."
        )
    return f"Requête refusée par {host} (HTTP {code})."


def _retry_after_seconds(headers) -> float | None:
    """Lit ``Retry-After`` en secondes ; une date HTTP est ignorée."""
    raw = headers.get("Retry-After") if headers is not None else None
    if raw is None:
        return None
    try:
        seconds = float(str(raw).strip())
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def _retry_delay(
    status: int | None, headers, attempt: int, started: float
) -> float | None:
    """Délai avant la prochaine tentative, ou ``None`` pour abandonner.

    Un ``Retry-After`` supérieur au budget restant vaut abandon immédiat :
    attendre plus longtemps que ce que l'on s'autorise ne servirait qu'à
    retarder la même erreur.
    """
    if attempt >= MAX_ATTEMPTS:
        return None
    if status is not None and status not in RETRYABLE_STATUSES:
        return None
    remaining = RETRY_BUDGET_SECONDS - (time.monotonic() - started)
    if remaining <= 0:
        return None
    delay = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)) * (1 + random.random() * 0.5)
    retry_after = _retry_after_seconds(headers)
    if retry_after is not None:
        delay = retry_after
    return delay if delay <= remaining else None


def _is_timeout(exc: urllib.error.URLError) -> bool:
    return isinstance(exc.reason, (socket.timeout, TimeoutError))


def _perform(request: urllib.request.Request, timeout: int, *, not_found_exit_code: int) -> dict:
    url = request.full_url
    host = _host(url)
    started = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
            return _decode_json(raw, url, host)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:500]
            detail = f"HTTP {exc.code} sur {url}\n{body}"
            delay = _retry_delay(exc.code, exc.headers, attempt, started)
            if delay is None:
                raise LegifranceError(
                    _public_message(exc.code, host),
                    exit_code=not_found_exit_code if exc.code == 404 else 4,
                    http_status=exc.code,
                    detail=detail,
                ) from exc
            cause = f"HTTP {exc.code}"
        except urllib.error.URLError as exc:
            detail = f"Échec réseau vers {url} : {exc.reason}"
            # Un délai dépassé a déjà consommé tout le temps qu'on lui accorde :
            # le rejouer doublerait l'attente pour le même résultat probable.
            delay = None if _is_timeout(exc) else _retry_delay(None, None, attempt, started)
            if delay is None:
                raise LegifranceError(
                    f"Échec réseau vers {host} : réessayer plus tard.",
                    exit_code=4,
                    detail=detail,
                ) from exc
            cause = "réseau"
        except TimeoutError as exc:
            raise LegifranceError(
                f"Délai dépassé vers {host} : réessayer plus tard.",
                exit_code=4,
                detail=f"Délai de {timeout} s dépassé vers {url}",
            ) from exc
        LOGGER.info(
            "retry host=%s cause=%s attempt=%d delay_s=%.2f", host, cause, attempt, delay
        )
        _sleep(delay)


def _decode_json(raw: str, url: str, host: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LegifranceError(
            f"Réponse illisible de {host} : source non vérifiée.",
            exit_code=4,
            detail=f"Réponse non-JSON de {url} : {raw[:300]}",
        ) from exc
