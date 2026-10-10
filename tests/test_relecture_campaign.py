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

    def test_temoin_gold_jamais_envoye_et_contamination_arretee(self):
        data = campaign.read_json(campaign.CORPUS)
        for c in campaign.corpus():
            self.assertNotIn(data["temoin_corriges"], campaign.prompt_cas(c))
        trace = Trace(texte_final=data["temoin_corriges"])
        self.assertFalse(campaign.controles(trace, "A")["isolation_appels"])






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
                        with self.assertRaisesRegex(ValueError, "périmètre"):
                            campaign.figer(p, Path(d) / "gel.json")
                    version.assert_not_called()


if __name__ == "__main__":
    unittest.main()
