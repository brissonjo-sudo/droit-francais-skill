"""Sondes avec vrai journal de quotas et transport simulé, aucune génération."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import catalogue_gemini, gemini_http, gemini_rest, mesure_tokens_gemini
from bench.budget_gemini import Budget


class CatalogueGeminiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.budget = Budget("123456789", "gemini-3.5-flash", {"rpm": 100, "rpd": 100, "tpm_entree": 100000}, _state=self.root)
        self.requests = []

    def client(self, payload, status=200):
        def handler(req):
            self.requests.append(req)
            return httpx.Response(status, json=payload)
        transport = gemini_http.Transport(client=httpx.AsyncClient(transport=httpx.MockTransport(handler), trust_env=False))
        return gemini_rest.Client("secret-test", "gemini-3.5-flash", self.budget, transport=transport)

    async def test_catalogue_unique_filtre_metadata_et_vrai_journal(self):
        result = await catalogue_gemini.lire(self.client({"models": [{"name": "models/gemini-3.5-flash",
            "inputTokenLimit": 100, "outputTokenLimit": 50, "description": "description ignorée",
            "supportedGenerationMethods": ["generateContent"]}, {"name": "models/gemini-3.8-flash-latest"}]}))
        self.assertEqual(1, len(self.requests))
        self.assertEqual("GET", self.requests[0].method)
        self.assertNotIn("secret-test", str(self.requests[0].url))
        self.assertEqual("secret-test", self.requests[0].headers["x-goog-api-key"])
        self.assertNotIn("description ignorée", json.dumps(result))
        self.assertEqual(1, len(result["modeles"]))
        self.assertEqual(0, result["generations"])
        self.assertFalse(result["collecte_autorisee"])
        self.assertEqual(["models.list"], [r["type"] for r in self.budget._lire(self.budget.horloge())])

    async def test_pagination_ne_provoque_pas_un_autre_appel(self):
        result = await catalogue_gemini.lire(self.client({"models": [], "nextPageToken": "suite"}))
        self.assertFalse(result["catalogue_complet"])
        self.assertEqual(1, len(self.requests))

    async def test_429_persistant_arrete_sonde_suivante(self):
        with self.assertRaises(gemini_http.ErreurGemini):
            await catalogue_gemini.lire(self.client({}, 429))
        with self.assertRaises(ValueError):
            await mesure_tokens_gemini.mesurer(self.client({"totalTokens": 100}))
        self.assertEqual(1, len(self.requests))
        self.assertEqual(1, len(self.budget._lire(self.budget.horloge())))

    async def test_tokens_utilise_modele_profil_sans_corrige(self):
        result = await mesure_tokens_gemini.mesurer(self.client({"totalTokens": 321}))
        self.assertEqual("gemini-3.5-flash", result["modele"])
        self.assertTrue(str(self.requests[0].url).endswith("gemini-3.5-flash:countTokens"))
        body = self.requests[0].content.decode()
        for forbidden in ("gold", "valide_par", "conclusion_attendue", "secret-test"):
            self.assertNotIn(forbidden, body)
        self.assertEqual(321, result["tokens_entree"])
        self.assertEqual(["countTokens"], [r["type"] for r in self.budget._lire(self.budget.horloge())])
