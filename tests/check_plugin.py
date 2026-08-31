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
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Catalogue sans dépendance externe : importable ici sans le SDK MCP.
from mcp_server.catalog import EXPECTED_TOOLS  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
SUBMISSION = ROOT / "chatgpt-app-submission.json"
SERVER = ROOT / "mcp_server" / "server.py"

# Limites publiees par OpenAI pour la soumission au repertoire d'applications.
# Elles sont recopiees ici plutot que deduites : un depassement fait echouer la
# soumission sans que rien, dans le depot, ne l'ait signale auparavant.
# Source : https://developers.openai.com/plugins/deploy/submission-errors
LIMITES_TEXTE = {
    "displayName": 30,
    "shortDescription": 30,
    "longDescription": 4000,
    "developerName": 80,
}
CATEGORIES = frozenset(
    {
        "Productivity", "Creativity", "Developer Tools", "Business & Operations",
        "Data & Analytics", "Communication", "Education & Research", "Security",
        "Finance", "Healthcare", "Travel", "Entertainment", "Other",
    }
)
MAX_PROMPTS = 3
MAX_LONGUEUR_PROMPT = 128
MAX_CAPABILITIES = 20
MAX_LONGUEUR_CAPABILITY = 120
MAX_LONGUEUR_URL = 1024

#: URL de schema attendue dans le fichier de soumission. Le chemin historique
#: « apps-sdk » redirige, mais le schema exige desormais la forme « plugins » :
#: un fichier declarant l'ancienne valeur echoue a la validation officielle.
SCHEMA_SOUMISSION = (
    "https://developers.openai.com/plugins/schemas/chatgpt-app-submission.v1.json"
)
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
#: Les quatre URL exigees a la soumission. « supportURL » manquait au
#: manifeste : son absence ne se serait vue qu'au depot du dossier.
PUBLIC_URL_FIELDS = (
    "websiteURL",
    "supportURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
)
LOCAL_ASSET_FIELDS = (
    "composerIcon",
    "logo",
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
        for field in PUBLIC_URL_FIELDS:
            value = interface.get(field)
            parsed = urlparse(value) if isinstance(value, str) else None
            if not parsed or parsed.scheme != "https" or not parsed.netloc:
                fail(f"interface.{field} doit être une URL HTTPS publique", problems)
        for field in LOCAL_ASSET_FIELDS:
            value = interface.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"interface.{field} doit être un chemin relatif", problems)
                continue
            if not value.startswith("./") or not value[2:].strip():
                fail(
                    f"interface.{field} doit être un chemin relatif au dépôt "
                    f"de la forme ./chemin/fichier.png",
                    problems,
                )
                continue
            asset = (ROOT / value[2:]).resolve()
            if ROOT not in asset.parents:
                fail(f"interface.{field} sort du dépôt : {value}", problems)
            elif not asset.is_file():
                fail(f"interface.{field} pointe vers un fichier absent : {value}", problems)
            elif asset.suffix.lower() != ".png":
                fail(f"interface.{field} doit être une image PNG : {value}", problems)

        for champ, limite in LIMITES_TEXTE.items():
            valeur = interface.get(champ)
            if isinstance(valeur, str) and len(valeur) > limite:
                fail(
                    f"interface.{champ} fait {len(valeur)} caracteres, "
                    f"la soumission OpenAI en accepte {limite} au plus",
                    problems,
                )
        if interface.get("category") not in CATEGORIES:
            fail(
                "interface.category doit figurer dans la liste OpenAI : "
                f"{sorted(CATEGORIES)}",
                problems,
            )
        for champ in PUBLIC_URL_FIELDS:
            valeur = interface.get(champ)
            if isinstance(valeur, str) and len(valeur) > MAX_LONGUEUR_URL:
                fail(
                    f"interface.{champ} depasse {MAX_LONGUEUR_URL} caracteres",
                    problems,
                )
        if isinstance(capabilities, list):
            if len(capabilities) > MAX_CAPABILITIES:
                fail(
                    f"interface.capabilities compte {len(capabilities)} entrees, "
                    f"la soumission en accepte {MAX_CAPABILITIES} au plus",
                    problems,
                )
            for item in capabilities:
                if isinstance(item, str) and len(item) > MAX_LONGUEUR_CAPABILITY:
                    fail(
                        f"une capability depasse {MAX_LONGUEUR_CAPABILITY} caracteres",
                        problems,
                    )
        prompts = interface.get("defaultPrompt")
        if not isinstance(prompts, list) or not prompts:
            fail("interface.defaultPrompt doit etre une liste non vide", problems)
        else:
            if len(prompts) > MAX_PROMPTS:
                fail(
                    f"interface.defaultPrompt compte {len(prompts)} entrees, "
                    f"la soumission en accepte {MAX_PROMPTS} au plus",
                    problems,
                )
            if len(set(prompts)) != len(prompts):
                fail("les prompts de demarrage doivent etre distincts", problems)
            for item in prompts:
                if not isinstance(item, str) or not item.strip():
                    fail("un prompt de demarrage est vide", problems)
                elif len(item) > MAX_LONGUEUR_PROMPT:
                    fail(
                        f"un prompt de demarrage depasse {MAX_LONGUEUR_PROMPT} caracteres",
                        problems,
                    )

    # Le manifeste du plugin suit la version du serveur MCP : ce sont les deux
    # faces d'un meme deploiement. Le skill, lui, garde sa propre ligne
    # editoriale et n'est pas contraint ici.
    if SERVER.is_file():
        trouve = re.search(
            r'^SERVER_VERSION = "([^"]+)"', SERVER.read_text(encoding="utf-8"), re.M
        )
        if trouve and version != trouve.group(1):
            fail(
                f"version du manifeste ({version}) differente de SERVER_VERSION "
                f"({trouve.group(1)}) : le plugin suit le serveur MCP",
                problems,
            )

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

    for policy in ("docs/privacy-policy.md", "docs/terms-of-use.md"):
        if not (ROOT / policy).is_file():
            fail(f"document public absent : {policy}", problems)

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

    if not SUBMISSION.is_file():
        fail("fichier de soumission absent : chatgpt-app-submission.json", problems)
    else:
        try:
            submission = json.loads(SUBMISSION.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"chatgpt-app-submission.json est illisible : {exc}", problems)
        else:
            if submission.get("schema_version") != 1:
                fail("schema_version de la soumission doit valoir 1", problems)
            if submission.get("$schema") != SCHEMA_SOUMISSION:
                fail(
                    f"$schema doit valoir {SCHEMA_SOUMISSION} : l'ancienne forme "
                    "apps-sdk echoue a la validation officielle",
                    problems,
                )
            if not str(submission.get("release_notes", "")).strip():
                fail("release_notes est obligatoire a la soumission", problems)
            tools = submission.get("tools")
            if not isinstance(tools, dict) or set(tools) != set(EXPECTED_TOOLS):
                fail("la soumission doit couvrir exactement les six outils MCP", problems)
            else:
                for name, descriptor in tools.items():
                    justifications = descriptor.get("justifications", {})
                    for cle in (
                        "read_only_justification",
                        "open_world_justification",
                        "destructive_justification",
                    ):
                        if not str(justifications.get(cle, "")).strip():
                            fail(
                                f"justification {cle} absente pour {name} : "
                                "OpenAI en exige une par annotation",
                                problems,
                            )
                    annotations = descriptor.get("annotations", {})
                    expected = {
                        "readOnlyHint": True,
                        "openWorldHint": False,
                        "destructiveHint": False,
                    }
                    if annotations != expected:
                        fail(f"annotations de soumission invalides pour {name}", problems)
            positives = submission.get("test_cases", [])
            negatives = submission.get("negative_test_cases", [])
            if len(positives) != 5:
                fail("la soumission doit contenir cinq cas de test positifs", problems)
            if len(negatives) != 3:
                fail("la soumission doit contenir trois cas de test négatifs", problems)

            for index, case in enumerate(positives, start=1):
                triggered = case.get("tools_triggered")
                if not isinstance(triggered, str) or not triggered.strip():
                    fail(
                        f"cas de test positif {index} : tools_triggered est obligatoire",
                        problems,
                    )
                    continue
                named = [item.strip() for item in triggered.split(",")]
                unknown = sorted(set(named) - set(EXPECTED_TOOLS))
                if unknown:
                    fail(
                        f"cas de test positif {index} : outil inconnu {unknown}",
                        problems,
                    )
            for index, case in enumerate(negatives, start=1):
                if case.get("tools_triggered") is not None:
                    fail(
                        f"cas de test négatif {index} : tools_triggered doit être null",
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
