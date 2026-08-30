#!/usr/bin/env python3
"""Vérification des jetons OAuth 2.1 présentés au serveur MCP public.

Le serveur MCP est un *Resource Server* : il ne délivre aucun jeton et
n'héberge aucun mot de passe. Un serveur d'autorisation externe (Auth0,
Stytch, Clerk, WorkOS, Descope…) authentifie l'utilisateur, puis émet un
jeton signé que ce module valide localement à partir du JWKS public de
l'émetteur.

Conséquence pratique : les clés PISTE restent sur le serveur, mais chaque
appel d'outil devient imputable à un sujet identifié, ce qui permet un
quota par utilisateur et non plus seulement un quota global d'instance.

Contrôles appliqués à chaque jeton :

* signature asymétrique vérifiée contre le JWKS de l'émetteur ;
* ``iss`` égal à l'émetteur configuré, à la barre oblique finale près ;
* ``aud`` contenant l'audience configurée (indicateur de ressource,
  RFC 8707) — un jeton émis pour une autre API est refusé ;
* ``exp`` et ``nbf`` vérifiés par la bibliothèque ;
* portées requises vérifiées en amont par le SDK MCP.

Aucun jeton, aucune charge utile et aucun secret n'est journalisé.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Sequence

import anyio
import jwt
from jwt import PyJWKClient
from mcp.server.auth.provider import AccessToken

LOGGER = logging.getLogger("droit_francais.mcp.auth")

#: Algorithmes asymétriques acceptés. Les algorithmes symétriques (HS*) et
#: « none » sont exclus : le serveur ne partage aucun secret avec l'émetteur.
ALLOWED_ALGORITHMS: tuple[str, ...] = ("RS256", "RS384", "RS512", "ES256", "ES384")


class LegalAccessToken(AccessToken):
    """Jeton validé, enrichi du sujet servant de clé de quota."""

    subject: str


def _normalise_scopes(payload: dict[str, Any]) -> list[str]:
    """Extrait les portées, quel que soit le dialecte de l'émetteur."""
    raw: Any = payload.get("scope")
    if isinstance(raw, str):
        return [item for item in raw.split(" ") if item]
    for key in ("scp", "permissions", "scopes"):
        value = payload.get(key)
        if isinstance(value, str):
            return [item for item in value.split(" ") if item]
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value if str(item)]
    return []


def _client_identifier(payload: dict[str, Any]) -> str:
    """Identifie l'application appelante sans jamais renvoyer le jeton."""
    for key in ("azp", "client_id", "cid", "aud"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, (list, tuple)) and value:
            return str(value[0])
    return "client-inconnu"


class JwksTokenVerifier:
    """Implémente le protocole ``TokenVerifier`` du SDK MCP.

    Le client JWKS met les clés publiques en cache et ne rappelle l'émetteur
    qu'en cas de rotation, ce qui évite un appel réseau par requête.
    """

    def __init__(
        self,
        issuer: str,
        jwks_url: str,
        audience: str,
        *,
        leeway_seconds: int = 30,
        algorithms: Sequence[str] = ALLOWED_ALGORITHMS,
    ) -> None:
        self._issuer = issuer
        # Certains émetteurs (Auth0) écrivent « iss » avec une barre oblique
        # finale que les métadonnées de configuration n'affichent pas. Les deux
        # écritures désignent le même émetteur : accepter l'une et l'autre évite
        # un refus systématique pour une différence purement typographique.
        base = issuer.rstrip("/")
        self._accepted_issuers = frozenset({base, base + "/"})
        self._audience = audience
        self._leeway_seconds = leeway_seconds
        self._algorithms = tuple(algorithms)
        self._jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)

    def _decode(self, token: str) -> dict[str, Any]:
        """Décodage bloquant, exécuté hors de la boucle d'événements."""
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=list(self._algorithms),
            audience=self._audience,
            issuer=self._accepted_issuers,
            leeway=self._leeway_seconds,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        """Retourne le jeton validé, ou ``None`` si un contrôle échoue."""
        try:
            payload = await anyio.to_thread.run_sync(self._decode, token)
        except jwt.PyJWTError as exc:
            # Le motif est journalisé, jamais le jeton ni sa charge utile.
            LOGGER.info("auth_rejected reason=%s", type(exc).__name__)
            return None
        except Exception as exc:  # réseau JWKS indisponible, etc.
            LOGGER.warning("auth_unavailable reason=%s", type(exc).__name__)
            return None

        subject = str(payload.get("sub", ""))
        if not subject:
            LOGGER.info("auth_rejected reason=MissingSubject")
            return None

        expires_at = payload.get("exp")
        return LegalAccessToken(
            token=token,
            client_id=_client_identifier(payload),
            scopes=_normalise_scopes(payload),
            expires_at=int(expires_at) if isinstance(expires_at, (int, float)) else None,
            resource=self._audience,
            subject=subject,
        )


def principal_of(access_token: AccessToken | None) -> str:
    """Clé de quota : le sujet authentifié, sinon l'application appelante."""
    if access_token is None:
        return "anonyme"
    subject = getattr(access_token, "subject", "")
    if isinstance(subject, str) and subject:
        return subject
    return access_token.client_id or "anonyme"


def scopes_from_env_value(raw: str | None, default: Iterable[str]) -> list[str]:
    """Découpe une liste de portées écrite avec des virgules ou des espaces."""
    if raw is None or not raw.strip():
        return list(default)
    separators = "," if "," in raw else " "
    return [item.strip() for item in raw.split(separators) if item.strip()]
