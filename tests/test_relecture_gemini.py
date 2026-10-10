"""Régressions #117 : budgets/contextes durables, deadline et profils fixes."""
import asyncio
import dataclasses
import datetime as dt
import json
import os
import sys
import tempfile
import socket
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import agents, budget_gemini, etude_v2, gemini_http, gemini_rest, liaisons_gemini
from _gemini_test_helpers import reserver
from _gemini_test_helpers import ecrire_profil
from bench import quotas_gemini
from bench import verrous_gemini


class RelectureGeminiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.budget = budget_gemini.Budget("123456789", "gemini-3.8-flash",
            {"rpm": 100, "rpd": 100, "tpm_entree": 100000}, _state=self.root)
        self.transport = mock.Mock(compter=mock.AsyncMock(return_value=100),
            appeler=mock.AsyncMock(return_value={"usageMetadata": {"promptTokenCount": 100}}),
            fermer=mock.AsyncMock())
        self.client = gemini_rest.Client("secret-test", "gemini-3.8-flash", self.budget, transport=self.transport)

    def contexte(self, *, secondes=300):
        ctx = reserver(self.root, secondes=secondes)
        self.client.contexte = ctx
        return ctx

    async def test_pas_double_reservation_et_contexte_forge_refuse(self):
        ctx = self.contexte()
        await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.assertEqual(1, len(etude_v2.reservations(self.root)))
        self.assertEqual(2, len(self.budget._lire(self.budget.horloge())))
        self.client.contexte = dataclasses.replace(ctx, attempt_id="forge")
        with self.assertRaises(ValueError):
            await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.assertEqual(1, self.transport.compter.await_count)
        etude_v2.clore(self.root, ctx.reservation, statut="ok")
        self.client.contexte = ctx
        with self.assertRaises(ValueError):
            await self.client.generer({}, echeance=ctx.echeance_monotone)

    async def test_429_generation_usage_absent_et_garde_modifiee(self):
        ctx = self.contexte()
        self.transport.appeler.side_effect = gemini_http.ErreurGemini(429)
        with self.assertRaises(gemini_http.ErreurGemini):
            await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.assertTrue(self.budget.arret.exists())
        with self.assertRaises(budget_gemini.ArretBudget) as error:
            self.client.avant(ctx.echeance_monotone)
        self.assertEqual("quota_429", error.exception.categorie)
        self.assertEqual(2, len(self.budget._lire(self.budget.horloge())))

    async def test_usage_absent_bloque_et_contexte_deja_reserve_reste_unique(self):
        ctx = self.contexte()
        self.transport.appeler.return_value = {}
        response, _ = await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.assertTrue(response["budget_arret"])
        self.assertTrue(self.budget.arret.exists())
        self.assertEqual(1, len(etude_v2.reservations(self.root)))

    async def test_usage_surplus_garde_attempt_id_et_pas_remboursement(self):
        ctx = self.contexte()
        self.transport.appeler.return_value = {"usageMetadata": {"promptTokenCount": 200}}
        response, _ = await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.assertTrue(response["budget_arret"])
        rows = self.budget._lire(self.budget.horloge())
        self.assertEqual(2, sum(r["requetes"] for r in rows))
        self.assertEqual(200, sum(r["tokens"] for r in rows))
        self.assertTrue(all(r["attempt_id"] == ctx.attempt_id for r in rows))
        self.assertEqual(ctx.attempt_id, json.loads(self.budget.arret.read_bytes())["attempt_id"])

    async def test_variable_token_sans_rapport_ne_cree_pas_faux_secret(self):
        ctx = self.contexte()
        with mock.patch.dict(os.environ, {"TASK_TOKEN_DESCRIPTION": "article 1240"}, clear=True):
            await self.client.generer({"contents": ["article 1240"]}, echeance=ctx.echeance_monotone)
        self.transport.compter.assert_awaited_once()
        self.transport.appeler.assert_awaited_once()

    async def test_count_finit_apres_deadline_aucune_generation(self):
        ctx = self.contexte(secondes=.01)
        async def lent(*args, **kwargs):
            await asyncio.sleep(.02)
            return 100
        self.transport.compter.side_effect = lent
        with self.assertRaises(gemini_http.ErreurGemini) as error:
            await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.assertEqual("delai", error.exception.categorie)
        self.transport.appeler.assert_not_called()
        self.assertEqual(1, len(self.budget._lire(self.budget.horloge())))

    async def test_delai_debute_avant_mcp_et_transport_ferme(self):
        ctx = self.contexte(secondes=.02)
        async def blocked(*args, **kwargs):
            await asyncio.sleep(1)
        with mock.patch.object(gemini_rest, "_executer_mcp", side_effect=blocked):
            result = await gemini_rest.executer_mcp(self.client, prompt="test", bras="C", plafond=1,
                options=agents.Options(effort="high", contexte=ctx))
        self.assertEqual("infra_error", result.statut)
        self.assertEqual("delai", result.categorie_infra)
        self.transport.fermer.assert_awaited_once()

    async def test_arret_429_precedent_ne_demarre_pas_mcp(self):
        self.budget.dossier.mkdir(parents=True)
        self.budget.bloquer(429)
        ctx = self.contexte()
        with mock.patch.object(gemini_rest, "_executer_mcp") as run:
            result = await gemini_rest.executer_mcp(self.client, prompt="test", bras="C", plafond=1,
                options=agents.Options(effort="high", contexte=ctx))
        self.assertEqual("quota_429", result.categorie_infra)
        run.assert_not_called()

    async def test_contexte_forge_ou_cloture_refuse_avant_mcp(self):
        ctx = self.contexte()
        for invalid in (dataclasses.replace(ctx, attempt_id="forge"), ctx):
            if invalid is ctx:
                etude_v2.clore(self.root, ctx.reservation, statut="ok")
            with mock.patch.object(gemini_rest, "_executer_mcp") as run:
                result = await gemini_rest.executer_mcp(self.client, prompt="test", bras="C", plafond=1,
                    options=agents.Options(effort="high", contexte=invalid))
            self.assertEqual("profil", result.categorie_infra)
            run.assert_not_called()

    async def test_profil_modifie_entre_count_et_generation_bloque(self):
        ctx = self.contexte()
        self.client.garde = mock.Mock(side_effect=[None, budget_gemini.ArretBudget("profil modifié", "profil")])
        with self.assertRaises(budget_gemini.ArretBudget):
            await self.client.generer({}, echeance=ctx.echeance_monotone)
        self.transport.appeler.assert_not_called()

    def test_etat_commun_numero_normalise_et_liaison_cle(self):
        with mock.patch.object(budget_gemini, "etat_canonique", return_value=self.root):
            a = budget_gemini.Budget("000123456789", "gemini-3.8-flash", {"rpm": 5, "rpd": 5, "tpm_entree": 1000})
            b = budget_gemini.Budget("123456789", "gemini-3.8-flash", {"rpm": 5, "rpd": 5, "tpm_entree": 1000})
        self.assertEqual(a.journal, b.journal)
        limits = {"rpm": 5, "rpd": 5, "tpm_entree": 1000}
        liaisons_gemini.lier("secret-test", "123456789", "gemini-3.8-flash", limits, self.root)
        with self.assertRaises(ValueError):
            liaisons_gemini.lier("secret-test", "987654321", "gemini-3.8-flash", limits, self.root)
        self.assertNotIn("secret-test", (self.root / "liaisons-gemini.json").read_text())
        self.assertNotIn(__import__("hashlib").sha256(b"secret-test").hexdigest(), (self.root / "liaisons-gemini.json").read_text())
        self.assertEqual(32, len((self.root / "liaisons-gemini.hmac").read_bytes()))
        if os.name != "nt":
            self.assertEqual(0, (self.root / "liaisons-gemini.hmac").stat().st_mode & 0o077)

    def test_liaison_ancienne_non_migree_refuse_sans_reset(self):
        path = self.root / "liaisons-gemini.json"
        path.write_text(json.dumps({"schema": 2, "cles": {}, "limites": {"ancien": {"rpd": 5}}}))
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            liaisons_gemini.lier("secret-test", "123456789", "gemini-3.8-flash",
                {"rpm": 100, "rpd": 100, "tpm_entree": 100000}, self.root)
        self.assertEqual(before, path.read_bytes())
        self.assertFalse((self.root / "liaisons-gemini.hmac").exists())

    def test_verrou_orphelin_et_tzdata_differente_bloquent(self):
        self.budget.dossier.mkdir(parents=True)
        lock = self.budget.dossier / "requete.lock"
        lock.write_text('{"pid":999999,"hote":"test","cree_le":"test"}')
        with self.assertRaises(ValueError):
            with self.budget.tentative(0, "countTokens"):
                self.fail()
        self.assertTrue(lock.exists())
        budget_gemini.pacifique.cache_clear()
        try:
            with mock.patch.object(budget_gemini.metadata, "version", return_value="ancienne"):
                with self.assertRaises(ValueError):
                    budget_gemini.pacifique()
        finally:
            budget_gemini.pacifique.cache_clear()

    def test_recuperation_verrou_exclut_acquisition_et_second_recuperateur(self):
        self.budget.dossier.mkdir(parents=True)
        path = self.budget.dossier / "requete.lock"
        info = {"schema": 2, "pid": 999999, "hote": socket.gethostname(), "nonce": "ancien",
                "cree_le": "2026-10-10T00:00:00+00:00", "attempt_id": "interrompu"}
        path.write_text(json.dumps(info))
        def pendant_journal(row):
            with self.assertRaises(ValueError):
                with self.budget.tentative(0, "countTokens"):
                    self.fail("acquisition pendant récupération")
            with self.assertRaises(ValueError):
                verrous_gemini.retirer(self.root, path, "TEST", "second récupérateur")
            self.assertEqual(info, json.loads(path.read_bytes()))
        with (mock.patch.object(etude_v2, "processus_actif", return_value=False),
              mock.patch.object(verrous_gemini.Journal, "ajouter", side_effect=pendant_journal)):
            verrous_gemini.retirer(self.root, path, "TEST", "processus synthétique mort")
        self.assertFalse(path.exists())
        with self.budget.tentative(0, "countTokens"):
            active = path.read_bytes()
            with self.assertRaises(ValueError):
                verrous_gemini.retirer(self.root, path, "TEST", "reprise tardive")
            self.assertEqual(active, path.read_bytes())
        self.assertEqual(1, len(self.budget._lire(self.budget.horloge())))

    def test_recuperation_preserve_arret_429_et_refuse_pid_actif(self):
        self.budget.dossier.mkdir(parents=True)
        self.budget.bloquer(429)
        path = self.root / "profils.lock"
        with verrous_gemini.verrou(self.root, path):
            with self.assertRaises(ValueError):
                verrous_gemini.retirer(self.root, path, "TEST", "pid actuel")
            self.assertTrue(path.exists())
        self.assertTrue(self.budget.arret.exists())
        with self.assertRaises(budget_gemini.ArretBudget):
            self.budget.verifier_arret()

    def test_environnement_mcp_liste_blanche_et_workflow(self):
        with mock.patch.dict(os.environ, {"AUTH0_CLIENT_SECRET": "secret-test", "MCP_ACCESS_TOKEN": "secret-test",
                "CLAUDE_CODE_OAUTH_TOKEN": "secret-test", "GITHUB_TOKEN": "secret-test", "GEMINI_API_KEY": "secret-test",
                "LEGIFRANCE_CLIENT_ID": "source-test", "LEGIFRANCE_DOTENV": "malveillant"}, clear=True):
            env = gemini_rest.environnement_mcp()
        self.assertEqual("source-test", env["LEGIFRANCE_CLIENT_ID"])
        self.assertEqual("1", env["LEGIFRANCE_NO_DOTENV"])
        for name in ("AUTH0_CLIENT_SECRET", "MCP_ACCESS_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "GITHUB_TOKEN", "GEMINI_API_KEY", "LEGIFRANCE_DOTENV"):
            self.assertNotIn(name, env)
        yaml = (Path(__file__).resolve().parents[1] / ".github/workflows/sonde-fonctionnelle.yml").read_text()
        section = yaml.split("  gemini-preparation:", 1)[1]
        self.assertIn("github.ref == 'refs/heads/main'", section)
        self.assertIn("environment: gemini-free", section)
        self.assertNotIn("secrets.", section)
        self.assertNotIn('run: python tests/check_live_tools.py "${{ inputs.url }}"', yaml)

    async def test_instantane_capture_valide_puis_modification_releve_bloque(self):
        registry = ecrire_profil(self.root)
        with (mock.patch.object(quotas_gemini, "LOCAL", self.root),
              mock.patch.object(budget_gemini, "etat_canonique", return_value=self.root),
              mock.patch.dict(os.environ, {"GEMINI_API_KEY": "secret-test"}, clear=True)):
            client = gemini_rest.preparer_client(registry, "profil-01")
            try:
                client.garde()
                record = self.root / "releve.json"
                record.write_bytes(record.read_bytes()+b" ")
                with self.assertRaises(budget_gemini.ArretBudget) as error:
                    client.garde()
                self.assertEqual("profil", error.exception.categorie)
            finally:
                await client.transport.fermer()
