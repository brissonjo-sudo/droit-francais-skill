"""Garde-fous du planificateur de surveillance de production."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "surveillance.yml"


class SurveillanceWorkflowTests(unittest.TestCase):
    def test_cron_est_horaire_et_decale_du_debut_d_heure(self) -> None:
        """Le registre d'observation se contente d'une mesure par heure.

        Le pas de cinq minutes servait à maintenir l'instance hors veille ; ce
        rôle est passé à un ping externe le 2 septembre 2026, le planificateur
        GitHub n'ayant rendu qu'un run sur quarante. Le décalage à la troisième
        minute évite le début d'heure, que GitHub signale comme chargé.
        """
        texte = WORKFLOW.read_text(encoding="utf-8")
        crons = re.findall(r'^\s*- cron: ["\']([^"\']+)["\']\s*$', texte, re.M)
        self.assertEqual(["3 * * * *"], crons)

    def test_un_defaut_de_sonde_fait_toujours_echouer_le_job(self) -> None:
        texte = WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(texte, r"steps\.sonde\.outputs\.code != '0'")
        self.assertRegex(texte, r"Signaler le défaut[\s\S]+?exit 1")

    def test_une_mesure_vide_fait_echouer_le_job_sans_le_faire_derailler(self) -> None:
        """Une sortie de sonde vide doit être signalée, pas silencieusement subie.

        Elle survenait quand une panne de connexion faisait planter la sonde :
        `git commit` sortait alors en 1 faute d'avoir quelque chose à indexer,
        et le job mourait à l'étape de journalisation — avant le résumé de
        série et avant l'étape prévue pour porter le message d'échec.
        """
        texte = WORKFLOW.read_text(encoding="utf-8")
        # L'échec est porté par l'étape dédiée, qui couvre les deux causes.
        self.assertRegex(
            texte, r"steps\.sonde\.outputs\.vide == 'true'[\s\S]+?exit 1"
        )
        # La journalisation ne peut plus être ce qui arrête le job.
        self.assertRegex(texte, r"git diff --cached --quiet")
        # Le résumé de série reste publié même quand la sonde a relevé un défaut.
        self.assertRegex(texte, r"Résumer la série\n\s+if: always\(\)")


if __name__ == "__main__":
    unittest.main()
