#!/usr/bin/env python3
"""Expose les sources officielles du skill via le protocole MCP."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
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

load_dotenv(script_dir=SCRIPTS)

HTTP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
try:
    HTTP_PORT = int(os.environ.get("PORT") or os.environ.get("MCP_PORT", "8000"))
except ValueError as exc:
    raise RuntimeError("PORT/MCP_PORT doit être un entier.") from exc

server_options: dict[str, Any] = {
    "instructions": (
        "Recherche juridique française en lecture seule. Utiliser search puis "
        "fetch pour lire une source avant de la citer. Une erreur d'accès ne "
        "doit jamais être présentée comme une vérification réussie."
    )
}
if MCP_V2:
    server_options["version"] = "0.4.0"
else:
    server_options.update(host=HTTP_HOST, port=HTTP_PORT)
server = MCPServer("Droit français", **server_options)

READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)


def _safe_call(operation: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Transforme une erreur métier en erreur MCP sans exposer de secret."""
    try:
        return operation(*args, **kwargs)
    except LegifranceError as exc:
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
        "Le code, s'il est fourni, doit être son libellé officiel complet."
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
        "d'article à partir de son identifiant LEGIARTI."
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
    args = parser.parse_args()
    if args.transport == "streamable-http" and MCP_V2:
        server.run(transport=args.transport, host=HTTP_HOST, port=HTTP_PORT)
    else:
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()
