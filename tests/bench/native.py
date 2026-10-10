"""Adaptateurs natifs Codex/Gemini. Aucun repli API ni modèle implicite.

Leurs contrats de flux sont testés hors réseau ; cela ne vaut pas préflight
sur une CLI installée. Un modèle absent du flux reste inconnu.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from bench.flux import Appel, PREFIXE_MCP, Trace

API_ENV = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "GEMINI_API_KEY", "GOOGLE_API_KEY",
    "GOOGLE_GENAI_USE_VERTEXAI", "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
)


def environnement_abonnement() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in API_ENV}


def analyser_natif(flux: str, famille: str) -> Trace:
    trace = Trace()
    termine = False
    pending: dict[str, int] = {}
    for ligne in flux.splitlines():
        try:
            ev = json.loads(ligne)
            if not isinstance(ev, dict):
                raise ValueError("événement non objet")
            kind = ev.get("type")
            if kind in ("init", "session.started") and isinstance(ev.get("model"), str):
                trace.modele = ev["model"]
            if famille == "codex":
                if kind == "item.completed":
                    item = ev.get("item", {})
                    if item.get("type") == "agent_message":
                        trace.texte_final += item.get("text", "")
                    elif item.get("type") == "mcp_tool_call":
                        nom = item.get("tool", "")
                        server = item.get("server", "")
                        full = PREFIXE_MCP + nom if server == "droit-francais" else f"mcp__{server}__{nom}"
                        result = item.get("result")
                        trace.appels.append(Appel(len(trace.appels), full, item.get("arguments", {}),
                                                  json.dumps(result, ensure_ascii=False),
                                                  bool(item.get("error")) or item.get("status") == "failed"))
                    elif item.get("type") in ("command_execution", "web_search", "file_change"):
                        trace.appels.append(Appel(len(trace.appels), item["type"], {}))
                elif kind == "turn.completed":
                    termine = True
                    trace.usage = ev.get("usage", {})
                elif kind in ("turn.failed", "error"):
                    trace.is_error = True
            else:
                if kind == "message" and ev.get("role") == "assistant":
                    trace.texte_final += ev.get("content", "")
                elif kind == "tool_use":
                    nom = ev.get("tool_name", "")
                    prefix = "mcp_droit-francais_"
                    full = PREFIXE_MCP + nom[len(prefix):] if nom.startswith(prefix) else nom
                    pending[ev.get("tool_id", "")] = len(trace.appels)
                    trace.appels.append(Appel(len(trace.appels), full, ev.get("parameters", {})))
                elif kind == "tool_result":
                    index = pending.pop(ev.get("tool_id", ""), None)
                    if index is None:
                        trace.lignes_illisibles += 1
                    else:
                        trace.appels[index] = replace(trace.appels[index],
                            resultat_texte=str(ev.get("output", "")), is_error=ev.get("status") != "success")
                elif kind == "result":
                    termine = True
                    trace.is_error |= ev.get("status") != "success"
                    trace.usage = ev.get("stats", {})
                    models = trace.usage.get("models", {})
                    # Le modèle d'init peut être un alias. Les stats attestent
                    # le modèle utilisé ; plusieurs modèles rendent le run impropre.
                    if len(models) == 1:
                        trace.modele = next(iter(models))
                    elif len(models) > 1:
                        trace.modele = ""
                        trace.is_error = True
                elif kind == "error":
                    trace.is_error = True
        except (ValueError, TypeError, AttributeError):
            trace.lignes_illisibles += 1
    trace.is_error |= not termine or bool(pending)
    return trace


def methode(references: bool = False) -> str:
    from bench.agents import SKILL
    texte = SKILL.read_text(encoding="utf-8")
    if references:
        for path in sorted((SKILL.parent / "references").glob("*.md")):
            texte += f"\n--- RÉFÉRENCE {path.name} ---\n" + path.read_text(encoding="utf-8")
    return texte


def instructions(bras: str, references: bool = False, variante: str | None = None) -> str:
    from bench.agents import PROMPTS, SKILL
    if bras in ("A", "D"):
        return (PROMPTS / f"bras-{bras}.md").read_text(encoding="utf-8")
    suffixe = (PROMPTS / f"preambule-{bras}.md").read_text(encoding="utf-8")
    # La découverte différée est propre à Claude, pas aux deux autres CLI.
    debut = suffixe.find("**Ces outils ne sont pas préchargés.")
    fin = suffixe.find("Aucun autre outil", debut)
    if debut >= 0 and fin >= 0:
        suffixe = suffixe[:debut] + suffixe[fin:]
    base = Path(variante).read_text(encoding="utf-8") if variante else methode(references)
    return base + "\n" + suffixe


def commande_codex(executable: str, modele: str, systeme: Path, bras: str, options) -> list[str]:
    from bench.agents import RACINE
    settings = {
        "model_instructions_file": str(systeme), "project_doc_max_bytes": 0,
        "features.shell_tool": False, "web_search": "disabled",
        "memories.use_memories": False, "memories.generate_memories": False,
    }
    if options.effort != "defaut_cli":
        settings["model_reasoning_effort"] = options.effort
    if bras in ("C", "D"):
        settings.update({
            "mcp_servers.droit-francais.command": options.interpreteur_python or "python",
            "mcp_servers.droit-francais.args": [str(RACINE / "mcp_server/server.py")],
            "mcp_servers.droit-francais.cwd": str(RACINE),
        })
    cmd = [executable, "--no-daemon", "exec", "--json", "--ephemeral", "--ignore-user-config",
           "--skip-git-repo-check", "--sandbox", "read-only", "--model", modele]
    for k, v in settings.items():
        cmd.extend(["-c", f"{k}={json.dumps(v, ensure_ascii=False)}"])
    cmd.append("-")
    return cmd


def executer(famille: str, *, prompt: str, bras: str, plafond: int, options):
    from bench.agents import Execution, RACINE
    if bras not in ("A", "B", "C", "D"):
        raise ValueError("bras inconnu")
    if famille == "gemini" and options.effort != "defaut_cli":
        raise ValueError("Gemini : seul le réglage natif attesté au préflight est supporté")
    if bras in ("C", "D") and not options.mcp_local:
        raise ValueError("les adaptateurs natifs exigent le candidat MCP local")
    exe = options.executable or shutil.which(famille)
    if not exe:
        return Execution(Trace(), "", -1, statut="infra_error", motif_infra=f"CLI {famille} absente")
    env = environnement_abonnement()
    with tempfile.TemporaryDirectory(prefix=f"bench-{famille}-") as dossier:
        root = Path(dossier)
        systeme = root / "system.md"
        systeme.write_text(instructions(bras, options.fournir_references, options.methode_experimentale),
                          encoding="utf-8", newline="\n")
        if famille == "codex":
            cmd = commande_codex(exe, options.modele, systeme, bras, options)
        else:
            # Ne copier que les caches d'authentification, jamais les réglages,
            # extensions, skills ou mémoire du compte. Ils ne quittent pas le poste.
            source = Path(os.environ.get("GEMINI_CLI_HOME", str(Path.home()))) / ".gemini"
            isolated = root / ".gemini"
            isolated.mkdir()
            for nom in ("oauth_creds.json", "google_accounts.json"):
                if (source / nom).is_file():
                    shutil.copyfile(source / nom, isolated / nom)
            settings = {
                "tools": {"core": []}, "skills": {"enabled": False},
                "hooksConfig": {"enabled": False}, "useWriteTodos": False,
                "context": {"fileName": [], "includeDirectoryTree": False},
                "security": {"auth": {"selectedType": "oauth-personal"}},
                "mcp": {"allowed": ["droit-francais"] if bras in ("C", "D") else []},
                "mcpServers": {},
            }
            if bras in ("C", "D"):
                settings["mcpServers"]["droit-francais"] = {
                    "command": options.interpreteur_python or "python",
                    "args": [str(RACINE / "mcp_server/server.py")], "cwd": str(RACINE), "trust": True,
                }
            config = isolated / "settings.json"
            config.write_text(json.dumps(settings), encoding="utf-8")
            env.update(GEMINI_CLI_HOME=dossier, GEMINI_SYSTEM_MD=str(systeme),
                       GEMINI_CLI_SYSTEM_SETTINGS_PATH=str(config), GEMINI_CLI_SYSTEM_DEFAULTS_PATH=str(config))
            cmd = [exe, "--model", options.modele, "--output-format", "stream-json"]
        try:
            started = time.perf_counter()
            result = subprocess.run(cmd, input=prompt,
                capture_output=True, encoding="utf-8", errors="replace", timeout=options.timeout_s,
                cwd=dossier, env=env, shell=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            partiel = getattr(exc, "stdout", "") or ""
            if isinstance(partiel, bytes):
                partiel = partiel.decode("utf-8", errors="replace")
            return Execution(analyser_natif(partiel, famille), partiel if options.garder_flux else "", -1,
                             statut="infra_error", motif_infra=type(exc).__name__)
    trace = analyser_natif(result.stdout, famille)
    trace.duration_ms = int((time.perf_counter() - started) * 1000)
    motif = ""
    if result.returncode or trace.is_error or trace.lignes_illisibles or not trace.texte_final:
        motif = "flux incomplet, erreur CLI ou réponse absente"
    elif not trace.modele:
        motif = "modèle effectif absent du flux natif : qualification manquante"
    execution = Execution(trace, result.stdout if options.garder_flux else "", result.returncode,
                          "", "infra_error" if motif else "ok", motif)
    if not motif:
        from bench.agents import _classer
        _classer(execution, bras)
    return execution
