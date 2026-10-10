"""Recettes SDK MCP explicites, transport modèle simulé, zéro appel Google."""
import asyncio
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import agents, gemini_http, gemini_rest
from bench.budget_gemini import Budget
from mcp_server.catalog import EXPECTED_TOOLS
from _gemini_test_helpers import reserver


@unittest.skipUnless(os.environ.get("BENCH_TEST_MCP_INTEGRATION") == "1", "Recette SDK explicite requise")
class IntegrationGeminiTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalogue_stdio_reel_converti_et_ferme_sans_generation_google(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            requests = []
            def handler(req):
                requests.append(req)
                if str(req.url).endswith("countTokens"):
                    return httpx.Response(200, json={"totalTokens": 100})
                return httpx.Response(200, json={"modelVersion": "gemini-3.8-flash", "usageMetadata": {"promptTokenCount": 100},
                    "candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [{"text": "contrôle synthétique"}]}}]})
            transport = gemini_http.Transport(client=httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False))
            budget = Budget("123456789", "gemini-3.8-flash", {"rpm": 100, "rpd": 100, "tpm_entree": 100000}, _state=root)
            client = gemini_rest.Client("secret-test", "gemini-3.8-flash", budget, transport=transport)
            ctx = reserver(root, bras="C")
            options = agents.Options(mcp_local=True, interpreteur_python=sys.executable, effort="high", contexte=ctx)
            result = await gemini_rest.executer_mcp(client, prompt="contrôle synthétique", bras="C", plafond=1, options=options)
            self.assertEqual("ok", result.statut, result.motif_infra)
            import json
            payload = json.loads(requests[-1].content)
            tools = payload["tools"][0]["functionDeclarations"]
            self.assertEqual(EXPECTED_TOOLS, {t["name"] for t in tools})
            self.assertTrue(all(isinstance(t["parametersJsonSchema"], dict) for t in tools))
            self.assertTrue(transport.client.is_closed)

    async def test_dotenv_factice_cwd_et_scripts_ne_reintroduit_pas_secret(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            scripts = root / "scripts"
            scripts.mkdir()
            for p in (root / ".env", scripts / ".env"):
                p.write_text("GITHUB_TOKEN=sentinelle-github\nAUTH0_CLIENT_SECRET=sentinelle-auth0\nGEMINI_API_KEY=sentinelle-gemini\n", encoding="utf-8")
            source = str(Path(__file__).resolve().parents[1] / "skill/scripts")
            code = ("import sys,os; sys.path.insert(0,sys.argv[1]);"
                    "from droit_francais.config import load_dotenv;load_dotenv(script_dir=__import__('pathlib').Path(sys.argv[2]));"
                    "assert not any(os.environ.get(n) for n in ('GITHUB_TOKEN','AUTH0_CLIENT_SECRET','GEMINI_API_KEY'));print('isolation vérifiée')")
            env = gemini_rest.environnement_mcp()
            result = await asyncio.to_thread(subprocess.run, [sys.executable, "-c", code, source, str(scripts)],
                env=env, cwd=root, capture_output=True, encoding="utf-8", timeout=10)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn("sentinelle", result.stdout+result.stderr)
