#!/usr/bin/env python3
"""Vérifie un serveur MCP HTTP déjà démarré, sans appeler les API juridiques."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server.catalog import EXPECTED_TOOLS  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def probe(url: str) -> None:
    async with streamable_http_client(url) as (reader, writer, *_):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = {tool.name for tool in listed.tools}
            if names != set(EXPECTED_TOOLS):
                raise RuntimeError(
                    f"Outils MCP inattendus : {sorted(names)}"
                )
            for tool in listed.tools:
                annotations = tool.annotations
                read_only = getattr(
                    annotations,
                    "readOnlyHint",
                    getattr(annotations, "read_only_hint", None),
                )
                open_world = getattr(
                    annotations,
                    "openWorldHint",
                    getattr(annotations, "open_world_hint", None),
                )
                destructive = getattr(
                    annotations,
                    "destructiveHint",
                    getattr(annotations, "destructive_hint", None),
                )
                if (read_only, open_world, destructive) != (True, True, False):
                    raise RuntimeError(
                        f"Annotations de sécurité invalides pour {tool.name}"
                    )
                output_schema = getattr(
                    tool,
                    "outputSchema",
                    getattr(tool, "output_schema", None),
                )
                if not output_schema:
                    raise RuntimeError(
                        f"Schéma de sortie absent pour {tool.name}"
                    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sonde un endpoint MCP HTTP")
    parser.add_argument("url", nargs="?", default="http://127.0.0.1:8000/mcp")
    args = parser.parse_args()
    asyncio.run(probe(args.url))
    print("Endpoint MCP HTTP valide ; 6 outils et métadonnées contrôlés.")


if __name__ == "__main__":
    main()
