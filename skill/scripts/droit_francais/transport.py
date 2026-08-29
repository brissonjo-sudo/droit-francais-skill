"""Transport HTTP JSON partagé par les clients des API officielles."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .errors import LegifranceError

DEFAULT_TIMEOUT = 30


def http_post_json(
    url: str,
    data: bytes,
    headers: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Exécute un POST et décode une réponse JSON."""
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        raise LegifranceError(
            f"HTTP {exc.code} sur {url}\n{body}",
            exit_code=4,
            http_status=exc.code,
        ) from exc
    except urllib.error.URLError as exc:
        raise LegifranceError(
            f"Échec réseau vers {url} : {exc.reason}",
            exit_code=4,
        ) from exc
    return _decode_json(raw, url)


def http_get_json(
    url: str,
    headers: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Exécute un GET et décode une réponse JSON."""
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:500]
        exit_code = 5 if exc.code == 404 else 4
        raise LegifranceError(
            f"HTTP {exc.code} sur {url}\n{body}",
            exit_code=exit_code,
            http_status=exc.code,
        ) from exc
    except urllib.error.URLError as exc:
        raise LegifranceError(
            f"Échec réseau vers {url} : {exc.reason}",
            exit_code=4,
        ) from exc
    return _decode_json(raw, url)


def _decode_json(raw: str, url: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LegifranceError(
            f"Réponse non-JSON de {url} : {raw[:300]}",
            exit_code=4,
        ) from exc
