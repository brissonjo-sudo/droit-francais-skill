#!/usr/bin/env python3
"""Contrôles locaux du socle plugin, sans dépendance externe.

Le validateur officiel reste la référence pour le paquet final. Ces contrôles
reproduisent les invariants du dépôt qui doivent aussi rester vérifiables dans
la CI publique : manifeste minimal, découverte native du skill et maintien du
point d'entrée historique.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PLUGIN_FIELDS = ("name", "version", "description", "author", "skills", "interface")
INTERFACE_FIELDS = (
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "defaultPrompt",
)


def fail(message: str, problems: list[str]) -> None:
    problems.append(message)


def main() -> int:
    problems: list[str] = []

    if not MANIFEST.is_file():
        print("❌ Manifeste absent : .codex-plugin/plugin.json")
        return 1

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"❌ Manifeste illisible : {exc}")
        return 1

    for field in PLUGIN_FIELDS:
        if field not in manifest:
            fail(f"champ obligatoire absent : {field}", problems)

    if manifest.get("name") != ROOT.name:
        fail(
            f"name doit correspondre au dossier racine ({ROOT.name!r})",
            problems,
        )

    version = manifest.get("version")
    if not isinstance(version, str) or SEMVER.fullmatch(version) is None:
        fail("version doit respecter SemVer strict (x.y.z)", problems)

    if manifest.get("skills") != "./skills/":
        fail("skills doit pointer vers ./skills/", problems)

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        fail("interface doit être un objet JSON", problems)
    else:
        for field in INTERFACE_FIELDS:
            if field not in interface:
                fail(f"champ interface absent : {field}", problems)
        capabilities = interface.get("capabilities")
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) and item.strip() for item in capabilities
        ):
            fail("interface.capabilities doit être une liste de chaînes", problems)

    if "[TODO:" in json.dumps(manifest, ensure_ascii=False):
        fail("le manifeste contient encore un marqueur TODO", problems)

    adapter = ROOT / "skills" / "recherche-juridique" / "SKILL.md"
    legacy = ROOT / "skill" / "SKILL.md"
    if not adapter.is_file():
        fail("adaptateur plugin absent : skills/recherche-juridique/SKILL.md", problems)
    else:
        adapter_text = adapter.read_text(encoding="utf-8")
        if "name: recherche-juridique" not in adapter_text:
            fail("le nom de l'adaptateur ne correspond pas à son dossier", problems)
        if "../../skill/SKILL.md" not in adapter_text:
            fail("l'adaptateur ne charge pas le skill historique", problems)
        adapter_target = (adapter.parent / "../../skill/SKILL.md").resolve()
        if adapter_target != legacy.resolve():
            fail("le chemin de l'adaptateur ne résout pas vers skill/SKILL.md", problems)

    if not legacy.is_file():
        fail("point d'entrée historique supprimé : skill/SKILL.md", problems)

    companions = (("apps", ".app.json"), ("mcpServers", ".mcp.json"))
    for field, filename in companions:
        if field in manifest and not (ROOT / filename).is_file():
            fail(f"{field} est déclaré sans fichier compagnon {filename}", problems)

    mcp_manifest = ROOT / ".mcp.json"
    if manifest.get("mcpServers") == "./.mcp.json" and mcp_manifest.is_file():
        try:
            mcp_payload = json.loads(mcp_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f".mcp.json est illisible : {exc}", problems)
        else:
            servers = mcp_payload.get("mcpServers")
            if not isinstance(servers, dict) or not servers:
                fail(".mcp.json.mcpServers doit être un objet non vide", problems)
            else:
                legal_server = servers.get("droit-francais")
                if not isinstance(legal_server, dict):
                    fail("serveur MCP droit-francais absent", problems)
                else:
                    command = legal_server.get("command")
                    args = legal_server.get("args")
                    if not isinstance(command, str) or not command.strip():
                        fail("commande du serveur MCP absente", problems)
                    if not isinstance(args, list) or not all(
                        isinstance(item, str) and item.strip() for item in args
                    ):
                        fail("arguments du serveur MCP invalides", problems)
                    elif "./mcp_server/server.py" not in args:
                        fail("le serveur MCP ne lance pas mcp_server/server.py", problems)
                    elif not (ROOT / "mcp_server" / "server.py").is_file():
                        fail("point d'entrée mcp_server/server.py absent", problems)

            serialized_mcp = json.dumps(mcp_payload, ensure_ascii=False)
            for secret_name in (
                "LEGIFRANCE_CLIENT_ID",
                "LEGIFRANCE_CLIENT_SECRET",
                "JUDILIBRE_KEY_ID",
                "PISTE_KEY_ID",
            ):
                if secret_name in serialized_mcp:
                    fail(
                        f"secret ou variable sensible interdit dans .mcp.json : {secret_name}",
                        problems,
                    )

    if problems:
        print(f"❌ {len(problems)} problème(s) dans le socle plugin :")
        for problem in problems:
            print(f"   - {problem}")
        return 1

    print("✅ Socle plugin cohérent ; skill historique préservé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
