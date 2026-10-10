"""Contrats REST synthétiques : outils exclusifs, signatures et modèle effectif."""
from __future__ import annotations

import copy
import sys
import tempfile
import time
import asyncio
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import agents, gemini_http, gemini_rest, native, quotas_gemini
from bench.budget_gemini import Budget
from mcp_server.catalog import EXPECTED_TOOLS
from _gemini_test_helpers import reserver
from _gemini_test_helpers import ecrire_profil
from bench import budget_gemini, etude_v2


def response(parts, model="gemini-3.8-flash", finish="STOP"):
    return {"modelVersion": model, "usageMetadata": {"promptTokenCount": 100},
            "candidates": [{"finishReason": finish, "content": {"role": "model", "parts": parts}}]}


class BoucleGeminiTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, responses, bras="A", outils=None, callback=None):
        client = mock.Mock(modele="gemini-3.8-flash", requetes=0)
        client.generer = mock.AsyncMock(side_effect=[(copy.deepcopy(r), 100) for r in responses])
        result = await gemini_rest.boucle(client, prompt="contrôle synthétique", bras=bras, plafond=12,
                                         instructions="instruction synthétique", outils=outils or [],
                                         appeler_outil=callback, echeance=time.monotonic()+300)
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
            self.assertTrue(result.flux_brut)
            self.assertNotIn("secret-source-test", result.flux_brut)
            self.assertFalse(result.trace.appels)
            client.generer.assert_called_once()

    async def test_erreur_initialisation_mcp_assainie(self):
        with mock.patch.object(gemini_rest, "_executer_mcp", side_effect=RuntimeError("secret-source-test")):
            result = await gemini_rest.executer_mcp(mock.Mock(), prompt="test", bras="C", plafond=1,
                                                   options=agents.Options())
        self.assertEqual("infra_error", result.statut)
        self.assertNotIn("secret-source-test", result.motif_infra + result.flux_brut)



class ClientGeminiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        patch = mock.patch.object(quotas_gemini, "LOCAL", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.budget = Budget("123456789", "gemini-3.8-flash",
                             {"rpm": 100, "tpm_entree": 100000, "rpd": 100}, _state=self.root)

    async def test_tokenizer_et_generation_reserves_et_compte_avant_envoi(self):
        transport = mock.Mock(compter=mock.AsyncMock(return_value=100), appeler=mock.AsyncMock(return_value=response([{ "text": "ok"}])))
        client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget, transport=transport)
        client.contexte = reserver(self.root)
        with (mock.patch.object(transport, "compter", new_callable=mock.AsyncMock, return_value=100),
              mock.patch.object(transport, "appeler", new_callable=mock.AsyncMock, return_value=response([{"text": "ok"}]))):
            await client.generer({"contents": []}, echeance=client.contexte.echeance_monotone)
        rows = self.budget._lire(self.budget.horloge())
        self.assertEqual(2, len(rows))
        self.assertEqual(["countTokens", "generateContent"], [r["type"] for r in rows])
        self.assertEqual(2, client.requetes)

    async def test_429_tokenizer_nactive_pas_generation_ni_autre_cle(self):
        transport = mock.Mock(compter=mock.AsyncMock(return_value=100), appeler=mock.AsyncMock(return_value=response([{ "text": "ok"}])))
        client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget, transport=transport)
        client.contexte = reserver(self.root)
        with (mock.patch.object(transport, "compter", new_callable=mock.AsyncMock, side_effect=gemini_http.ErreurGemini(429)),
              mock.patch.object(transport, "appeler", new_callable=mock.AsyncMock) as generate):
            with self.assertRaises(gemini_http.ErreurGemini):
                await client.generer({}, echeance=client.contexte.echeance_monotone)
        generate.assert_not_called()
        self.assertTrue(self.budget.arret.exists())
        self.assertEqual(1, client.requetes)

    async def test_secret_source_bloque_avant_tokenizer(self):
        transport = mock.Mock(compter=mock.AsyncMock(return_value=100), appeler=mock.AsyncMock(return_value=response([{ "text": "ok"}])))
        client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget, transport=transport)
        client.contexte = reserver(self.root)
        with (mock.patch.dict("os.environ", {"PISTE_KEY_ID": "secret-source-test"}),
              mock.patch.object(transport, "compter", new_callable=mock.AsyncMock) as compter):
            with self.assertRaises(ValueError):
                await client.generer({"contents": ["secret-source-test"]}, echeance=client.contexte.echeance_monotone)
        compter.assert_not_called()
        self.assertFalse(self.budget.journal.exists())

    def test_prototype_non_selectionne_implicitement_et_profils_incomplets_refuses(self):
        with mock.patch.object(native, "executer", return_value="natif") as run:
            self.assertEqual("natif", agents.GeminiHeadless().executer(options=agents.Options()))
            run.assert_called_once()
        with mock.patch.object(gemini_rest.profils_gemini, "verifier", return_value={"statut": "incomplet"}):
            with self.assertRaises(ValueError):
                gemini_rest.preparer_client(self.root / "profil.json", "profil-01")

    def test_cles_multiprofils_exclues_des_processus_abonnement_et_mcp(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY_COMPTE_2": "secret-test", "LEGIFRANCE_CLIENT_ID": "source-test"}, clear=True):
            env = native.environnement_abonnement()
        self.assertNotIn("GEMINI_API_KEY_COMPTE_2", env)
        self.assertIn("LEGIFRANCE_CLIENT_ID", env)


class BackendRESTContratTests(unittest.TestCase):
    def test_backend_transmet_arguments_nommes_a_coroutine_keyword_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = ecrire_profil(root)
            ctx = reserver(root)
            expected = agents.Execution(agents.Trace(texte_final="SYNTHESE SYNTHETIQUE"), "FLUX SYNTHETIQUE", 0)
            observed = []
            async def keyword_only(client, *, prompt, bras, plafond, options):
                try:
                    etude_v2.verifier_contexte(options.contexte)
                    client.garde()
                    observed.append((prompt, bras, plafond, options.contexte.attempt_id, client.modele))
                    return expected
                finally:
                    await client.transport.fermer()
            options = agents.Options(modele=ctx.modele, effort="high", contexte=ctx,
                gemini_registre=str(registry), gemini_profil="profil-01")
            with (mock.patch.object(quotas_gemini, "LOCAL", root),
                  mock.patch.object(budget_gemini, "etat_canonique", return_value=root),
                  mock.patch.dict("os.environ", {"GEMINI_API_KEY": "secret-test"}, clear=True),
                  mock.patch.object(gemini_rest, "executer_mcp", new=keyword_only)):
                result = agents.GeminiREST().executer(prompt="CONTROLE SYNTHETIQUE", bras="A", plafond=12, options=options)
            self.assertIs(expected, result)
            self.assertEqual([("CONTROLE SYNTHETIQUE", "A", 12, ctx.attempt_id, ctx.modele)], observed)
            self.assertEqual(1, len(etude_v2.reservations(root)))
            self.assertFalse(any(root.rglob("requetes.jsonl")))


if __name__ == "__main__":
    unittest.main()
