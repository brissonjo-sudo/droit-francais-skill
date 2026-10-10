"""Régressions de revue propres au prototype REST, sans génération externe."""
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import agents, campaign, gemini_http, gemini_rest, quotas_gemini
from bench.budget_gemini import Budget

class RelectureGeminiTests(unittest.TestCase):
    def test_sonde_actions_sans_secret_et_limitee_a_main_environnement(self):
        yaml = (campaign.ROOT / ".github/workflows/sonde-fonctionnelle.yml").read_text(encoding="utf-8")
        section = yaml.split("  gemini-preparation:", 1)[1]
        self.assertIn("github.ref == 'refs/heads/main'", section)
        self.assertIn("environment: gemini-free", section)
        self.assertNotIn("secrets.", section)


    def test_deadline_http_expiree_ne_fait_aucun_envoi(self):
        with mock.patch.object(gemini_http.urllib.request, "build_opener") as build:
            with self.assertRaises(gemini_http.ErreurGemini):
                gemini_http.appeler("secret-test", "gemini-3.8-flash", "countTokens", {}, echeance=0)
        build.assert_not_called()


    def test_rest_respecte_100_tentatives_etude_avant_http(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for i in range(100):
                campaign.reserver_budget(root / "etude", str(i))
            with mock.patch.object(quotas_gemini, "LOCAL", root):
                budget = Budget(root / "quota", "projet-test", "gemini-3.8-flash",
                                {"rpm": 100, "rpd": 100, "tpm_entree": 100000})
            client = gemini_rest.Client("secret-test", "gemini-3.8-flash", budget, etat_etude=root / "etude")
            with mock.patch.object(gemini_http, "compter") as compter:
                with self.assertRaisesRegex(ValueError, "journalière"):
                    client.generer({})
            compter.assert_not_called()


class DelaiTests(unittest.IsolatedAsyncioTestCase):
    async def test_delai_inclut_initialisation_mcp(self):
        async def blocked(*args, **kwargs):
            await asyncio.sleep(10)
        with mock.patch.object(gemini_rest, "_executer_mcp", side_effect=blocked):
            result = await gemini_rest.executer_mcp(mock.Mock(), prompt="test", bras="C", plafond=1,
                                                   options=agents.Options(timeout_s=0.01))
        self.assertEqual("infra_error", result.statut)
