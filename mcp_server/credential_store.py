"""Clés PISTE des utilisateurs, chiffrées et rangées dans leur compte Auth0.

Mode ``MCP_PISTE_CREDENTIALS=account`` : l'utilisateur s'authentifie par OAuth
(sujet ``sub``) et le serveur retrouve SES identifiants PISTE, saisis une fois
sur ``/compte``. Ils sont chiffrés en AES-GCM par le serveur avant d'être
écrits dans ``app_metadata`` (non modifiable par l'utilisateur) : Auth0 ne
voit qu'un blob. Render détient la clé ET l'accès Management : quiconque
contrôle le service peut donc lire toutes les clés stockées.

Le sujet sert de donnée associée : un blob copié d'un compte à un autre ne se
déchiffre pas. Aucun identifiant, secret ni blob n'est journalisé.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Mapping

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LOGGER = logging.getLogger("droit_francais.mcp.comptes")

#: Champ de ``app_metadata`` qui porte le blob chiffré.
METADATA_FIELD = "piste"
BLOB_PREFIX = "v1."
CACHE_TTL_SECONDS = 300
CACHE_MAX = 1024
LINK_TTL_SECONDS = 600
HTTP_TIMEOUT_SECONDS = 10

Http = Callable[[str, str, dict[str, str], bytes | None], dict[str, Any]]


class CredentialStoreError(RuntimeError):
    """Service de comptes indisponible ou blob illisible, sans détail sensible."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def decode_master_key(raw: str | None) -> bytes:
    """Clé maîtresse : 32 octets en base64 (standard ou URL)."""
    try:
        key = base64.b64decode((raw or "").strip() + "==", altchars=b"-_")
    except ValueError as exc:
        raise ValueError("MCP_CREDENTIALS_KEY n'est pas du base64.") from exc
    if len(key) != 32:
        raise ValueError("MCP_CREDENTIALS_KEY doit coder exactement 32 octets.")
    return key


def _urllib_http(method: str, url: str, headers: dict[str, str], body: bytes | None) -> dict[str, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310 - URL https fixée par la configuration
            payload = response.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        # Ni corps ni URL : le chemin porte le sujet de l'utilisateur.
        raise CredentialStoreError(f"Auth0 injoignable ({type(exc).__name__}).") from None
    try:
        return json.loads(payload) if payload else {}
    except ValueError:
        raise CredentialStoreError("Réponse Auth0 illisible.") from None


class CredentialStore:
    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        master_key: bytes,
        *,
        http: Http = _urllib_http,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._base = f"https://{domain}"
        self._client_id = client_id
        self._client_secret = client_secret
        self._aead = AESGCM(master_key)
        self._link_key = hashlib.sha256(b"lien-compte\0" + master_key).digest()
        self._http = http
        self._clock = clock
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[tuple[str, str] | None, float]] = {}
        self._mgmt_token: tuple[str, float] | None = None
        self._used_links: dict[str, float] = {}

    @classmethod
    def from_env(cls, env: Mapping[str, str], issuer: str) -> "CredentialStore":
        domain = env.get("AUTH0_MGMT_DOMAIN", "").strip() or urllib.parse.urlsplit(issuer).hostname
        return cls(
            domain or "",
            env.get("AUTH0_MGMT_CLIENT_ID", "").strip(),
            env.get("AUTH0_MGMT_CLIENT_SECRET", "").strip(),
            decode_master_key(env.get("MCP_CREDENTIALS_KEY")),
        )

    # -- chiffrement ------------------------------------------------------
    def encrypt(self, subject: str, client_id: str, client_secret: str) -> str:
        nonce = os.urandom(12)
        plain = json.dumps({"id": client_id, "secret": client_secret}).encode("utf-8")
        return BLOB_PREFIX + _b64(nonce + self._aead.encrypt(nonce, plain, subject.encode("utf-8")))

    def decrypt(self, subject: str, blob: str) -> tuple[str, str]:
        if not blob.startswith(BLOB_PREFIX):
            raise CredentialStoreError("Format de clés stockées inconnu.")
        try:
            raw = _unb64(blob[len(BLOB_PREFIX):])
            plain = self._aead.decrypt(raw[:12], raw[12:], subject.encode("utf-8"))
            data = json.loads(plain)
            return str(data["id"]), str(data["secret"])
        except (InvalidTag, ValueError, KeyError, TypeError):
            raise CredentialStoreError("Clés stockées illisibles : à ressaisir.") from None

    # -- lien de saisie à usage unique ------------------------------------
    def issue_link_token(self, subject: str) -> str:
        body = _b64(json.dumps({
            "sub": subject,
            "exp": int(time.time()) + LINK_TTL_SECONDS,
            "n": secrets.token_urlsafe(12),
        }).encode("utf-8"))
        return f"{body}.{_b64(hmac.new(self._link_key, body.encode(), hashlib.sha256).digest())}"

    def read_link_token(self, token: str, *, consume: bool) -> str | None:
        """Sujet du lien s'il est authentique, non expiré et jamais consommé."""
        body, _, signature = (token or "").partition(".")
        expected = _b64(hmac.new(self._link_key, body.encode(), hashlib.sha256).digest())
        if not body or not hmac.compare_digest(signature, expected):
            return None
        try:
            data = json.loads(_unb64(body))
            subject, expires, nonce = str(data["sub"]), int(data["exp"]), str(data["n"])
        except (ValueError, KeyError, TypeError):
            return None
        now = time.time()
        with self._lock:
            for stale in [n for n, exp in self._used_links.items() if exp <= now]:
                del self._used_links[stale]
            if expires <= now or nonce in self._used_links:
                return None
            if consume:
                self._used_links[nonce] = expires
        return subject

    # -- API Management Auth0 ---------------------------------------------
    def _token(self) -> str:
        now = self._clock()
        if self._mgmt_token and now < self._mgmt_token[1]:
            return self._mgmt_token[0]
        payload = self._http("POST", f"{self._base}/oauth/token", {"Content-Type": "application/json"},
                             json.dumps({
                                 "grant_type": "client_credentials",
                                 "client_id": self._client_id,
                                 "client_secret": self._client_secret,
                                 "audience": f"{self._base}/api/v2/",
                             }).encode("utf-8"))
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise CredentialStoreError("Auth0 n'a pas délivré de jeton de gestion.")
        self._mgmt_token = (token, now + max(60, int(payload.get("expires_in", 600)) - 60))
        return token

    def _user_url(self, subject: str) -> str:
        return f"{self._base}/api/v2/users/{urllib.parse.quote(subject, safe='')}"

    def _remember(self, subject: str, pair: tuple[str, str] | None) -> None:
        with self._lock:
            if len(self._cache) >= CACHE_MAX:
                self._cache.pop(next(iter(self._cache)))
            self._cache[subject] = (pair, self._clock() + CACHE_TTL_SECONDS)

    def load(self, subject: str) -> tuple[str, str] | None:
        with self._lock:
            entry = self._cache.get(subject)
        if entry and self._clock() < entry[1]:
            return entry[0]
        url = self._user_url(subject) + "?fields=app_metadata&include_fields=true"
        user = self._http("GET", url, {"Authorization": f"Bearer {self._token()}"}, None)
        blob = (user.get("app_metadata") or {}).get(METADATA_FIELD)
        pair = self.decrypt(subject, blob) if isinstance(blob, str) and blob else None
        self._remember(subject, pair)
        return pair

    def _patch(self, subject: str, value: str | None) -> None:
        # Auth0 fusionne app_metadata : une valeur null retire le champ.
        self._http("PATCH", self._user_url(subject), {
            "Authorization": f"Bearer {self._token()}",
            "Content-Type": "application/json",
        }, json.dumps({"app_metadata": {METADATA_FIELD: value}}).encode("utf-8"))

    def save(self, subject: str, client_id: str, client_secret: str) -> None:
        self._patch(subject, self.encrypt(subject, client_id, client_secret))
        self._remember(subject, (client_id, client_secret))
        LOGGER.info("piste_credentials_saved")

    def delete(self, subject: str) -> None:
        self._patch(subject, None)
        self._remember(subject, None)
        LOGGER.info("piste_credentials_deleted")
