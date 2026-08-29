#!/usr/bin/env python3
"""Vérifie un serveur MCP HTTP déjà démarré, sans appeler les API juridiques."""

from __future__ import annotations

import argparse
import asyncio
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPECTED_TOOLS = {
    "search",
    "fetch",
    "search_articles",
    "get_article",
    "search_case_law",
    "get_decision",
}


async def probe(url: str) -> None:
    async with streamable_http_client(url) as (reader, writer, *_):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            if names != EXPECTED_TOOLS:
                raise RuntimeError(
                    f"Outils MCP inattendus : {sorted(names)}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonde un endpoint MCP HTTP")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8000/mcp")
    args = parser.parse_args()
    asyncio.run(probe(args.url))
    print("Endpoint MCP HTTP valide ; 6 outils découverts.")


if __name__ == "__main__":
    main()
