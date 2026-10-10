"""Contrats REST synthétiques : outils exclusifs, signatures et modèle effectif."""
from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import agents, gemini_http, gemini_rest, native, quotas_gemini
from bench.budget_gemini import Budget
from mcp_server.catalog import EXPECTED_TOOLS


def response(parts, model="gemini-3.8-flash", finish="STOP"):
    return {"modelVersion": model, "usageMetadata": {"promptTokenCount": 100},
            "candidates": [{"finishReason": finish, "content": {"role": "model", "parts": parts}}]}


class BoucleGeminiTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, responses, bras="A", outils=None, callback=None):
        client = mock.Mock(modele="gemini-3.8-flash", requetes=0)
        client.generer.side_effect = [(copy.deepcopy(r), 100) for r in responses]
        result = await gemini_rest.boucle(client, prompt="contrôle synthétique", bras=bras, plafond=12,
                                         instructions="instruction synthétique", outils=outils or [],
                                         appeler_outil=callback)
        return result, client

    async def test_reponse_neutre_sans_outils(self):
        result, client = await self.run_case([response([{"text": "contrôle technique"}])])
        self.assertEqual("ok", result.statut)
        self.assertNotIn("tools", client.generer.call_args.args[0])
        self.assertEqual("gemini-3.8-flash", result.trace.modele)

    async def test_outil_neutre_interdit_avant_execution(self):
        result, client = await self.run_case([response([{"functionCall": {"name": "search", "args": {}}}])])
        self.assertEqual("infra_error", result.statut)
        client.generer.assert_called_once()
        self.assertFalse(result.trace.appels)

    async def test_signature_preservee_et_resultat_mcp_au_tour_suivant(self):
        first = response([{"functionCall": {"name": "search", "args": {"query": "article"}, "id": "id-1"},
                           "thoughtSignature": "signature-synthetique"}])
        tools = [{"name": n, "parametersJsonSchema": {"type": "object"}} for n in EXPECTED_TOOLS]
        callback = mock.AsyncMock(return_value=("résultat synthétique", False))
        result, client = await self.run_case([first, response([{"text": "fin"}])], "C", tools, callback)
        self.assertEqual("ok", result.statut)
        next_request = client.generer.call_args_list[1].args[0]
        self.assertEqual(first["candidates"][0]["content"], next_request["contents"][1])
        self.assertEqual("id-1", next_request["contents"][2]["parts"][0]["functionResponse"]["id"])
        self.assertEqual("mcp__droit-francais__search", result.trace.appels[0].nom_complet)

    async def test_modele_absent_different_troncature_et_usage_arrete_conservent_texte(self):
        for kind in ("absent", "different", "tronque", "budget"):
            with self.subTest(kind=kind):
                row = response([{"text": "réponse partielle"}])
                if kind == "absent":
                    row.pop("modelVersion")
                elif kind == "different":
                    row["modelVersion"] = "gemini-3.5-flash"
                elif kind == "tronque":
                    row["candidates"][0]["finishReason"] = "MAX_TOKENS"
                else:
                    row["budget_arret"] = True
                result, client = await self.run_case([row])
                self.assertEqual("infra_error", result.statut)
                self.assertEqual("réponse partielle", result.trace.texte_final)
                client.generer.assert_called_once()

    async def test_ensemble_appels_inconnus_refuse_avant_tout_outil(self):
        tools = [{"name": n} for n in EXPECTED_TOOLS]
        callback = mock.AsyncMock()
        row = response([{"functionCall": {"name": "search", "args": {}}},
                        {"functionCall": {"name": "shell", "args": {}}}])
        result, _ = await self.run_case([row], "C", tools, callback)
        self.assertEqual("infra_error", result.statut)
        callback.assert_not_called()

    async def test_secret_et_exception_mcp_arretent_sans_transmettre_ni_journaliser(self):
        tools = [{"name": n} for n in EXPECTED_TOOLS]
        row = response([{"functionCall": {"name": "search", "args": {}}}])
        for callback in (mock.AsyncMock(return_value=("secret-source-test", False)),
                         mock.AsyncMock(side_effect=RuntimeError("secret-source-test"))):
            with mock.patch.dict("os.environ", {"PISTE_KEY_ID": "secret-source-test"}):
                result, client = await self.run_case([row], "C", tools, callback)
            self.assertEqual("infra_error", result.statut)
            self.assertNotIn("secret-source-test", result.flux_brut)
            self.assertFalse(result.trace.appels)
            client.generer.assert_called_once()

    async def test_erreur_initialisation_mcp_assainie(self):
        with mock.patch.object(gemini_rest, "_executer_mcp", side_effect=RuntimeError("secret-source-test")):
            result = await gemini_rest.executer_mcp(mock.Mock(), prompt="test", bras="C", plafond=1,
                                                   options=agents.Options())
        self.assertEqual("infra_error", result.statut)
        self.assertNotIn("secret-source-test", result.motif_infra + result.flux_brut)

    async def test_catalogue_stdio_reel_converti_sans_generation_google(self):
        client = mock.Mock(modele="gemini-3.8-flash", requetes=0)
        client.generer.return_value = (response([{"text": "contrôle synthétique"}]), 100)
        options = agents.Options(mcp_local=True, interpreteur_python=sys.executable, effort="high")
        result = await gemini_rest.executer_mcp(client, prompt="contrôle synthétique", bras="C",
                                               plafond=1, options=options)
        self.assertEqual("ok", result.statut, result.motif_infra)
        declarations = client.generer.call_args.args[0]["tools"][0]["functionDeclarations"]
        self.assertEqual(EXPECTED_TOOLS, {t["name"] for t in declarations})
        self.assertTrue(all(isinstance(t["parametersJsonSchema"], dict) for t in declarations))


class ClientGeminiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        patch = mock.patch.object(quotas_gemini, "LOCAL", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.budget = Budget(self.root, "projet-test", "gemini-3.8-flash",
                             {"rpm": 100, "tpm_entree": 100000, "rpd": 100})

    def test_tokenizer_et_generation_reserves_et_compte_avant_envoi(self):
        client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget)
        with (mock.patch.object(gemini_http, "compter", return_value=100),
              mock.patch.object(gemini_http, "appeler", return_value=response([{"text": "ok"}]))):
            client.generer({"contents": []})
        rows = self.budget._lire(self.budget.horloge())
        self.assertEqual(2, len(rows))
        self.assertEqual(["countTokens", "generateContent"], [r["type"] for r in rows])
        self.assertEqual(2, client.requetes)

    def test_429_tokenizer_nactive_pas_generation_ni_autre_cle(self):
        client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget)
        with (mock.patch.object(gemini_http, "compter", side_effect=gemini_http.ErreurGemini(429)),
              mock.patch.object(gemini_http, "appeler") as generate):
            with self.assertRaises(gemini_http.ErreurGemini):
                client.generer({})
        generate.assert_not_called()
        self.assertTrue(self.budget.arret.exists())
        self.assertEqual(1, client.requetes)

    def test_secret_source_bloque_avant_tokenizer(self):
        client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget)
        with (mock.patch.dict("os.environ", {"PISTE_KEY_ID": "secret-source-test"}),
              mock.patch.object(gemini_http, "compter") as compter):
            with self.assertRaises(ValueError):
                client.generer({"contents": ["secret-source-test"]})
        compter.assert_not_called()
        self.assertFalse(self.budget.journal.exists())

    def test_prototype_non_selectionne_implicitement_et_profils_incomplets_refuses(self):
        with mock.patch.object(native, "executer", return_value="natif") as run:
            self.assertEqual("natif", agents.GeminiHeadless().executer(options=agents.Options()))
            run.assert_called_once()
        with mock.patch.object(gemini_rest.profils_gemini, "verifier", return_value={"statut": "incomplet"}):
            with self.assertRaises(ValueError):
                gemini_rest.preparer_client(self.root / "profil.json", "profil-01", self.root)

    def test_cles_multiprofils_exclues_des_processus_abonnement_et_mcp(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY_COMPTE_2": "secret-test", "LEGIFRANCE_CLIENT_ID": "source-test"}, clear=True):
            env = native.environnement_abonnement()
        self.assertNotIn("GEMINI_API_KEY_COMPTE_2", env)
        self.assertIn("LEGIFRANCE_CLIENT_ID", env)


if __name__ == "__main__":
    unittest.main()
