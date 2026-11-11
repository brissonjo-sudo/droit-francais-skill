"""La CLI montre les pourvois joints : sans eux, un numéro réel paraît introuvable."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "skill" / "scripts" / "legifrance.py"

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("legifrance_cli_joints", SCRIPT)
cli = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cli
_spec.loader.exec_module(cli)

JONCTION = {
    "id": "abc123",
    "jurisdiction": "cc",
    "decision_date": "2010-07-13",
    "number": "09-42.839",
    "numbers": ["09-42.839", "09-42.873"],
}


def _sortie(commande: list[str], reponse: dict) -> str:
    args = cli.build_parser().parse_args(commande)
    tampon = io.StringIO()
    with mock.patch.object(cli, "judilibre_get", return_value=reponse), contextlib.redirect_stdout(tampon):
        getattr(cli, f"cmd_{commande[0]}")(args)
    return tampon.getvalue()


class PourvoisJointsTests(unittest.TestCase):
    def test_la_recherche_affiche_les_pourvois_joints(self):
        sortie = _sortie(["juri", "09-42.873"], {"total": 1, "results": [JONCTION]})
        self.assertIn("Pourvois joints: 09-42.873", sortie)

    def test_la_decision_affiche_les_pourvois_joints(self):
        sortie = _sortie(["decision", "abc123"], JONCTION)
        self.assertIn("Pourvois joints    : 09-42.873", sortie)

    def test_un_pourvoi_unique_n_ajoute_aucune_ligne(self):
        seul = {**JONCTION, "numbers": ["09-42.839"]}
        self.assertNotIn("Pourvois joints", _sortie(["juri", "x"], {"total": 1, "results": [seul]}))
        sans = {k: v for k, v in JONCTION.items() if k != "numbers"}
        self.assertNotIn("Pourvois joints", _sortie(["decision", "abc123"], sans))


if __name__ == "__main__":
    unittest.main()
