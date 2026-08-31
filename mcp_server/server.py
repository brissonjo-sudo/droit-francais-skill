#!/usr/bin/env python3
"""Expose les sources officielles du skill via le protocole MCP."""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:  # SDK MCP v2
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    MCP_V2 = True
except ImportError:  # SDK MCP v1.27, encore largement installé
    from mcp.server.fastmcp import FastMCP as MCPServer
    from mcp.server.fastmcp.exceptions import ToolError
    MCP_V2 = False
from mcp.types import ToolAnnotations

from droit_francais.config import load_dotenv
from droit_francais.errors import LegifranceError
from droit_francais import tools as legal_tools
from mcp_server.runtime import (
    PrincipalRateLimiter,
    RequestGovernor,
    RuntimeCapacityError,
    RuntimeConfigurationError,
    RuntimeSettings,
)

load_dotenv(script_dir=SCRIPTS)
SETTINGS = RuntimeSettings.from_env()
logging.basicConfig(
    level=getattr(logging, SETTINGS.log_level),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger("droit_francais.mcp")
# L'image de production tourne en WARNING pour faire taire le SDK MCP et le
# serveur HTTP. Le journal métier, lui, est la seule trace d'imputabilité des
# appels d'outils : il doit survivre à ce réglage. Le niveau du logger
# d'origine décide seul de l'émission, indépendamment du logger racine.
if LOGGER.level in (logging.NOTSET,) or LOGGER.getEffectiveLevel() > logging.INFO:
    LOGGER.setLevel(logging.INFO)
logging.getLogger("droit_francais.mcp.auth").setLevel(logging.INFO)
GOVERNOR = RequestGovernor(
    SETTINGS.max_concurrent_requests,
    SETTINGS.tool_calls_per_minute,
    SETTINGS.queue_timeout_seconds,
)
USER_LIMITER = PrincipalRateLimiter(SETTINGS.user_calls_per_minute)

SERVER_VERSION = "0.6.0"


def _build_auth_options() -> dict[str, Any]:
    """Configure le serveur en Resource Server OAuth 2.1, si demandé.

    L'import du vérificateur reste local : le transport stdio, utilisé pour
    un usage personnel, n'a alors besoin ni de PyJWT ni d'un émetteur.
    """
    if not SETTINGS.auth_enabled:
        return {}

    from mcp.server.auth.settings import AuthSettings

    from mcp_server.auth import JwksTokenVerifier

    verifier = JwksTokenVerifier(
        issuer=SETTINGS.oauth_issuer,
        jwks_url=SETTINGS.oauth_jwks_url,
        audience=SETTINGS.oauth_audience,
    )
    return {
        "token_verifier": verifier,
        "auth": AuthSettings(
            issuer_url=SETTINGS.oauth_issuer,
            resource_server_url=SETTINGS.resource_url,
            required_scopes=list(SETTINGS.oauth_required_scopes),
        ),
    }

server_options: dict[str, Any] = {
    "log_level": SETTINGS.log_level,
    "instructions": (
        "Recherche juridique française en lecture seule. Utiliser search puis "
        "fetch pour lire une source avant de la citer. Une erreur d'accès ne "
        "doit jamais être présentée comme une vérification réussie."
    )
}
if MCP_V2:
    server_options["version"] = SERVER_VERSION
else:
    server_options.update(host=SETTINGS.host, port=SETTINGS.port)
server_options.update(_build_auth_options())
server = MCPServer("Droit français", **server_options)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _canonical_issuer() -> str:
    """Même écriture que la route RFC 9728 du SDK : chemin vide noté « / »."""
    parts = urlsplit(SETTINGS.oauth_issuer)
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def _pseudonym(principal: str) -> str:
    """Empreinte courte et stable : les journaux ne portent aucun identifiant brut."""
    if principal == "anonyme":
        return principal
    return hashlib.sha256(principal.encode("utf-8")).hexdigest()[:12]


def _current_principal() -> str:
    """Sujet authentifié de la requête courante, sans jamais lire le jeton."""
    if not SETTINGS.auth_enabled:
        return "anonyme"
    from mcp.server.auth.middleware.auth_context import get_access_token

    from mcp_server.auth import principal_of

    return principal_of(get_access_token())


def _safe_call(operation: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Transforme une erreur métier en erreur MCP sans exposer de secret."""
    started = time.monotonic()
    operation_name = getattr(operation, "__name__", "legal_operation")
    principal = _current_principal()
    try:
        USER_LIMITER.check(principal)
        with GOVERNOR.slot():
            result = operation(*args, **kwargs)
        LOGGER.info(
            "tool_call tool=%s principal=%s outcome=success duration_ms=%d",
            operation_name,
            _pseudonym(principal),
            int((time.monotonic() - started) * 1000),
        )
        return result
    except RuntimeCapacityError as exc:
        LOGGER.warning("tool_call tool=%s outcome=throttled", operation_name)
        raise ToolError(str(exc)) from exc
    except LegifranceError as exc:
        LOGGER.warning(
            "tool_call tool=%s outcome=upstream_error duration_ms=%d",
            operation_name,
            int((time.monotonic() - started) * 1000),
        )
        message = str(exc)
        for key in (
            "LEGIFRANCE_CLIENT_ID",
            "LEGIFRANCE_CLIENT_SECRET",
            "JUDILIBRE_KEY_ID",
            "PISTE_KEY_ID",
        ):
            secret = os.environ.get(key)
            if secret:
                message = message.replace(secret, "[secret masqué]")
        raise ToolError(
            f"Source officielle non vérifiée (code {exc.exit_code}) : {message}"
        ) from exc


if hasattr(server, "custom_route"):
    from starlette.requests import Request
    from starlette.responses import JSONResponse, PlainTextResponse, Response

    @server.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health(_request: Request) -> Response:
        """Sonde publique sans donnée interne ni vérification consommatrice d'API."""
        return JSONResponse(
            {"status": "ok", "version": SERVER_VERSION, "auth": SETTINGS.auth_mode}
        )

    @server.custom_route(
        "/.well-known/oauth-protected-resource",
        methods=["GET", "OPTIONS"],
        include_in_schema=False,
    )
    async def protected_resource_root(_request: Request) -> Response:
        """Alias racine : certains clients ignorent le suffixe de chemin RFC 9728."""
        if not SETTINGS.auth_enabled:
            return PlainTextResponse("Not configured", status_code=404)
        return JSONResponse(
            {
                "resource": SETTINGS.resource_url,
                "authorization_servers": [_canonical_issuer()],
                "scopes_supported": list(SETTINGS.oauth_required_scopes),
                "bearer_methods_supported": ["header"],
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

    @server.custom_route(
        "/.well-known/openai-apps-challenge",
        methods=["GET"],
        include_in_schema=False,
    )
    async def openai_apps_challenge(_request: Request) -> Response:
        """Répond exactement au jeton temporaire fourni lors de la soumission."""
        token = os.environ.get("OPENAI_APPS_CHALLENGE", "")
        if not token:
            return PlainTextResponse("Not configured", status_code=404)
        return PlainTextResponse(token)


@server.tool(
    name="search",
    title="Rechercher dans les sources juridiques",
    description=(
        "Recherche standard en lecture seule. Une requête contenant « article » "
        "interroge Légifrance ; les autres requêtes interrogent Judilibre. "
        "Retourne des identifiants à transmettre à fetch."
    ),
    annotations=READ_ONLY,
)
def search(query: str) -> dict[str, Any]:
    """Search French official legal sources with one plain-text query."""
    return _safe_call(legal_tools.search, query)


@server.tool(
    name="fetch",
    title="Lire une source juridique",
    description=(
        "Récupère le texte et les métadonnées officiels d'un identifiant renvoyé "
        "par search. Les identifiants LEGIARTI utilisent Légifrance ; les autres "
        "utilisent Judilibre."
    ),
    annotations=READ_ONLY,
)
def fetch(id: str) -> dict[str, Any]:
    """Fetch one source by the exact identifier returned by search."""
    return _safe_call(legal_tools.fetch, id)


@server.tool(
    name="search_articles",
    title="Rechercher un article de code",
    description=(
        "Recherche dans Légifrance un numéro d'article applicable à une date. "
        "Le code, s'il est fourni, doit être son libellé officiel complet. "
        "Ne renseigner date QUE si l'utilisateur demande une date précise, "
        "passée ou future. Laisser ce paramètre vide pour le droit en vigueur "
        "aujourd'hui : le serveur utilise sa propre horloge, plus fiable que "
        "la date supposée par le modèle."
    ),
    annotations=READ_ONLY,
)
def search_articles(
    number: str,
    code: str | None = None,
    date: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search legislation by article number, optional code title and ISO date."""
    return _safe_call(legal_tools.search_articles, number, code, date, limit)


@server.tool(
    name="get_article",
    title="Lire un article Légifrance",
    description=(
        "Récupère le texte, le statut juridique et les dates d'une version "
        "d'article à partir de son identifiant LEGIARTI. Ne renseigner date "
        "QUE si l'utilisateur demande une date précise. Laisser ce paramètre "
        "vide pour la version en vigueur aujourd'hui : le serveur utilise sa "
        "propre horloge, plus fiable que la date supposée par le modèle."
    ),
    annotations=READ_ONLY,
)
def get_article(id: str, date: str | None = None) -> dict[str, Any]:
    """Fetch one Légifrance article and its legal-status metadata."""
    return _safe_call(legal_tools.get_article, id, date)


@server.tool(
    name="search_case_law",
    title="Rechercher une décision judiciaire",
    description=(
        "Recherche la jurisprudence judiciaire officielle dans Judilibre, avec "
        "filtres facultatifs de juridiction et de dates ISO."
    ),
    annotations=READ_ONLY,
)
def search_case_law(
    query: str,
    jurisdiction: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search Judilibre decisions with optional filters."""
    return _safe_call(
        legal_tools.search_case_law,
        query,
        jurisdiction,
        date_start,
        date_end,
        limit,
    )


@server.tool(
    name="get_decision",
    title="Lire une décision Judilibre",
    description=(
        "Récupère le texte intégral et les métadonnées officielles d'une décision "
        "à partir de son identifiant Judilibre."
    ),
    annotations=READ_ONLY,
)
def get_decision(id: str) -> dict[str, Any]:
    """Fetch one full Judilibre decision by identifier."""
    return _safe_call(legal_tools.get_decision, id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP Droit français")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="stdio pour le plugin local ; streamable-http pour /mcp.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Valide la configuration de production puis quitte.",
    )
    args = parser.parse_args()
    try:
        SETTINGS.validate_public()
    except RuntimeConfigurationError as exc:
        parser.error(str(exc))
    if args.check_config:
        print("Configuration MCP valide.")
        return
    if args.transport == "streamable-http" and MCP_V2:
        server.run(
            transport=args.transport,
            host=SETTINGS.host,
            port=SETTINGS.port,
            max_request_body_size=SETTINGS.max_request_body_bytes,
        )
    else:
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()
