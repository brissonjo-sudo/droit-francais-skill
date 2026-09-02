"""Garde-fous du planificateur de surveillance de production."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "surveillance.yml"


class SurveillanceWorkflowTests(unittest.TestCase):
    def test_cron_est_decale_et_au_pas_minimal_de_cinq_minutes(self) -> None:
        texte = WORKFLOW.read_text(encoding="utf-8")
        crons = re.findall(r'^\s*- cron: ["\']([^"\']+)["\']\s*$', texte, re.M)
        self.assertEqual(["3/5 * * * *"], crons)

    def test_un_defaut_de_sonde_fait_toujours_echouer_le_job(self) -> None:
        texte = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("if: steps.sonde.outputs.code != '0'", texte)
        self.assertRegex(texte, r"Signaler le défaut[\s\S]+?exit 1")


if __name__ == "__main__":
    unittest.main()
