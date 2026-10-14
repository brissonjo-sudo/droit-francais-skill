"""Débits partagés, persistance des erreurs et reset Pacifique été/hiver."""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import budget_gemini, quotas_gemini


class BudgetGeminiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        patch = mock.patch.object(quotas_gemini, "LOCAL", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.now = dt.datetime(2026, 10, 10, 12, tzinfo=dt.timezone.utc)
        self.limits = {"rpm": 5, "tpm_entree": 1000, "rpd": 5}

    def budget(self, projet="123456789", modele="gemini-3.8-flash"):
        return budget_gemini.Budget(projet, modele, self.limits, horloge=lambda: self.now, _state=self.root)

    def test_deux_cles_du_meme_projet_partagent_rpm(self):
        a, b = self.budget(), self.budget()
        for _ in range(4):
            with a.tentative(0, "countTokens"):
                pass
        self.limits["rpd"] = 100
        b = self.budget()
        with self.assertRaisesRegex(budget_gemini.ArretBudget, "RPM"):
            with b.tentative(0, "countTokens"):
                self.fail("aucun envoi ne doit être possible")
        self.assertEqual(a.journal, b.journal)
        self.assertNotEqual(a.journal, self.budget("987654321").journal)

    def test_tpm_bloque_avant_envoi_et_fenetre_glissante_expire(self):
        budget = self.budget()
        with budget.tentative(700, "generateContent"):
            pass
        with self.assertRaisesRegex(budget_gemini.ArretBudget, "TPM"):
            with budget.tentative(101, "generateContent"):
                self.fail()
        self.now += dt.timedelta(seconds=60)
        with budget.tentative(700, "generateContent"):
            pass

    def test_exception_ne_rembourse_pas_reservation(self):
        budget = self.budget()
        with self.assertRaises(RuntimeError):
            with budget.tentative(200, "generateContent"):
                raise RuntimeError("erreur transport synthétique")
        self.assertEqual(1, len(budget._lire(self.now)))
        self.assertEqual(200, budget._lire(self.now)[0]["tokens"])

    def test_429_persiste_apres_redemarrage_du_client(self):
        budget = self.budget()
        with budget.tentative(0, "countTokens"):
            budget.bloquer(429)
        self.now += dt.timedelta(days=1)
        with self.assertRaisesRegex(budget_gemini.ArretBudget, "reprise explicite"):
            with self.budget().tentative(0, "countTokens"):
                self.fail()

    def test_rpd_ete_et_hiver_reset_au_minuit_pacifique(self):
        for previous, following in (("2026-07-10T06:59:00+00:00", "2026-07-10T07:00:00+00:00"),
                                    ("2026-01-10T07:59:00+00:00", "2026-01-10T08:00:00+00:00")):
            with self.subTest(previous=previous):
                self.now = dt.datetime.fromisoformat(previous)
                budget = self.budget("123457" if "07-10" in previous else "123458")
                for _ in range(4):
                    with budget.tentative(0, "countTokens"):
                        pass
                self.now += dt.timedelta(seconds=59)
                with self.assertRaisesRegex(budget_gemini.ArretBudget, "RPD"):
                    with budget.tentative(0, "countTokens"):
                        self.fail()
                self.now = dt.datetime.fromisoformat(following)
                with budget.tentative(0, "countTokens"):
                    pass

    def test_fold_automne_ne_cree_pas_de_second_jour(self):
        before = dt.datetime(2026, 11, 1, 8, 30, tzinfo=dt.timezone.utc)
        after = before + dt.timedelta(hours=1)
        self.assertEqual(0, before.astimezone(budget_gemini.pacifique()).fold)
        self.assertEqual(1, after.astimezone(budget_gemini.pacifique()).fold)
        self.assertEqual(budget_gemini.jour_pacifique(before), budget_gemini.jour_pacifique(after))

    def test_corruption_horloge_reculee_et_verrou_bloquent(self):
        budget = self.budget()
        with budget.tentative(0, "countTokens"):
            with self.assertRaisesRegex(budget_gemini.ArretBudget, "concurrente"):
                with self.budget().tentative(0, "countTokens"):
                    self.fail()
        self.now -= dt.timedelta(seconds=1)
        with self.assertRaises(budget_gemini.ArretBudget):
            with budget.tentative(0, "countTokens"):
                self.fail()
        budget.journal.write_text('{"interrompu":', encoding="utf-8")
        with self.assertRaises(budget_gemini.ArretBudget):
            with budget.tentative(0, "countTokens"):
                self.fail()

    def test_surplus_arrete_et_conserve_la_consommation(self):
        budget = self.budget()
        with budget.tentative(200, "generateContent") as at:
            with self.assertRaises(budget_gemini.ArretBudget):
                budget.usage(at, 200, 250)
        rows = budget._lire(self.now)
        self.assertEqual(250, sum(r["tokens"] for r in rows))
        self.assertEqual(1, sum(r["requetes"] for r in rows))
        self.assertTrue(budget.arret.exists())


if __name__ == "__main__":
    unittest.main()
