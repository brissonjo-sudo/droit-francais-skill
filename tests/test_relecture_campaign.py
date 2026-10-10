"""Régressions des constats de revue : reprise, gel, sorties et secrets."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import agents, campaign, confidentialite
from bench.flux import Trace
import run_campaign


class RelectureTests(unittest.TestCase):
    def contexte_collecte(self, root, backend):
        f = {"nom": "claude", "modele_demande": "claude-exact", "version_cli": "1",
             "executable": "claude", "raisonnement": "high"}
        gel = {"series_sha256": "s", "config": {"familles": [f], "bras": ["A", "B", "C", "D"],
                                                "pilote_modes": [1, 3, 5, 18]}}
        campaign.write_json(root / "s/preflight-claude.json", {})
        stack = contextlib.ExitStack()
        for target, value in (("bench.campaign.verifier_gel", None),
                              ("bench.campaign.version_cli", "1"),
                              ("bench.campaign.gold_pret", True),
                              ("bench.campaign.preflight_pret", True),
                              ("bench.preconditions.abonnement", True),
                              ("bench.agents.backend", backend)):
            stack.enter_context(mock.patch(target, return_value=value))
        return gel, stack

    def execution(self, statut="ok"):
        return agents.Execution(Trace(modele="claude-exact", texte_final="réponse"),
                                '{"type":"result","is_error":false}', 0, statut=statut)

    def test_panne_reprise_une_fois_sans_effacer_la_tentative(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            backend = mock.Mock()
            backend.executer.side_effect = [self.execution("infra_error")] + [self.execution() for _ in range(4)]
            gel, stack = self.contexte_collecte(root, backend)
            with stack:
                with self.assertRaises(campaign.ArretCollecte):
                    campaign.collecter(gel, "claude", "pilote", state=root)
                self.assertEqual(4, campaign.collecter(gel, "claude", "pilote", state=root))
            rows = campaign.lire_strict(root / "s/pilote-claude.jsonl")
            self.assertEqual(5, len(rows))
            self.assertEqual(rows[0]["identite"], rows[1]["identite"])
            self.assertEqual([1, 2], [r["tentative"] for r in rows[:2]])
            self.assertEqual(4, len(campaign.dernieres_tentatives(rows)))
            self.assertEqual(5, len(campaign.lire_strict(root / "budget.jsonl")))

    def test_deux_pannes_bloquent_un_troisieme_tirage(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            backend = mock.Mock()
            backend.executer.side_effect = [self.execution("infra_error"), self.execution("infra_error")]
            gel, stack = self.contexte_collecte(root, backend)
            with stack:
                for _ in range(3):
                    with self.assertRaises(campaign.ArretCollecte):
                        campaign.collecter(gel, "claude", "pilote", state=root)
            self.assertEqual(2, backend.executer.call_count)

    def test_gel_et_version_verifies_avant_et_apres_chaque_reponse(self):
        f = {"nom": "codex", "executable": "codex", "version_cli": "1"}
        backend = mock.Mock()
        backend.executer.return_value = self.execution()
        with (mock.patch.object(campaign, "verifier_gel") as check,
              mock.patch.object(campaign, "version_cli", side_effect=["1", "2"]),
              mock.patch.object(agents, "backend", return_value=backend)):
            result = campaign.executer_fige({}, f, prompt="x")
        self.assertEqual(2, check.call_count)
        self.assertEqual("infra_error", result.statut)

    def test_gel_modifie_avant_appel_nexecute_pas_le_modele(self):
        with (mock.patch.object(campaign, "verifier_gel", side_effect=ValueError("modifié")),
              mock.patch.object(agents, "backend") as backend):
            with self.assertRaises(ValueError):
                campaign.executer_fige({}, {}, prompt="x")
        backend.assert_not_called()

    def test_fable_toutes_casses_et_familles_refuse_avant_cli(self):
        cfg = campaign.read_json(campaign.ROOT / "tests/campaign/config.example.json")
        with tempfile.TemporaryDirectory() as d:
            for family in range(3):
                for modele in ("FABLE", "Claude-Fable-5-1", "provider/FaBlE-version"):
                    value = copy.deepcopy(cfg)
                    value["familles"][family]["modele_demande"] = modele
                    p = Path(d) / "cfg.json"
                    campaign.write_json(p, value)
                    with mock.patch.object(campaign, "version_cli") as version:
                        with self.assertRaisesRegex(ValueError, "crédits"):
                            campaign.figer(p, Path(d) / "gel.json")
                    version.assert_not_called()

    def test_cli_retourne_2_apres_infra_error(self):
        with (mock.patch.object(campaign, "read_json", return_value={}),
              mock.patch.object(campaign, "collecter", side_effect=campaign.ArretCollecte("panne conservée")),
              contextlib.redirect_stderr(io.StringIO())):
            self.assertEqual(2, run_campaign.main(["collecter", "--gel", "x", "--famille", "claude", "--phase", "pilote"]))

    def test_secret_source_et_valeur_echappee_expurges_par_la_meme_politique(self):
        value = 'source-avec-"guillemets'
        with mock.patch.dict("os.environ", {"PISTE_KEY_ID": value}, clear=True):
            with self.assertRaises(ValueError):
                confidentialite.verifier({"text": value})
            cleaned = campaign.nettoyer({"flux": json.dumps({"text": value})})
        self.assertNotIn("source-avec", json.dumps(cleaned))

    def test_collecte_entrelacee_alterne_quatre_reponses_par_famille(self):
        cfg = {"series_sha256": "s", "config": {"familles": [{"nom": f} for f in campaign.FAMILLES]}}
        with tempfile.TemporaryDirectory() as d:
            state = Path(d)
            for f in campaign.FAMILLES:
                campaign.write_json(state / f"s/preflight-{f}.json", {})
            with (mock.patch.object(campaign, "preflight_pret", return_value=True),
                  mock.patch.object(campaign, "collecter", side_effect=[4, 4, 4, 0, 0, 0]) as run):
                self.assertEqual(12, campaign.collecter_entrelace(cfg, "pilote", state=state))
            self.assertEqual(list(campaign.FAMILLES) * 2, [c.args[1] for c in run.call_args_list])
            self.assertTrue(all(c.kwargs["max_reponses"] == 4 for c in run.call_args_list))

    def test_temoin_gold_jamais_envoye_et_contamination_arretee(self):
        data = campaign.read_json(campaign.CORPUS)
        for c in campaign.corpus():
            self.assertNotIn(data["temoin_corriges"], campaign.prompt_cas(c))
        trace = Trace(texte_final=data["temoin_corriges"])
        self.assertFalse(campaign.controles(trace, "A")["isolation_appels"])







if __name__ == "__main__":
    unittest.main()
