"""Préconditions locales de la campagne ; jamais de jeton en sortie."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path

from bench.native import environnement_abonnement


def abonnement(famille: str, executable: str) -> bool:
    env = environnement_abonnement()
    if famille == "claude":
        cmd = [executable, "auth", "status", "--json"]
    elif famille == "codex":
        cmd = [executable, "login", "status"]
    else:
        source = Path(os.environ.get("GEMINI_CLI_HOME", str(Path.home()))) / ".gemini"
        # Nécessaire, pas suffisant : le préflight vérifie aussi l'appel réel.
        return (source / "oauth_creds.json").is_file()
    try:
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", timeout=15,
                                shell=False, env=env)
        if result.returncode:
            return False
        if famille == "claude":
            data = json.loads(result.stdout)
            return data.get("loggedIn") is True and data.get("authMethod") == "claude.ai"
        return "logged in using chatgpt" in (result.stdout + result.stderr).lower()
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


async def _catalogue(root: Path, python: str):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    env = {**environnement_abonnement(), "MCP_ENV": "test", "MCP_AUTH_MODE": "disabled"}
    params = StdioServerParameters(command=python, args=[str(root / "mcp_server/server.py")],
                                  cwd=str(root), env=env)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            listed = await session.list_tools()
            return sorted([{"name": t.name, "inputSchema": t.input_schema} for t in listed.tools],
                          key=lambda t: t["name"])


def catalogue(root: Path, python: str) -> list[dict]:
    async def bounded():
        return await asyncio.wait_for(_catalogue(root, python), timeout=30)
    return asyncio.run(bounded())
