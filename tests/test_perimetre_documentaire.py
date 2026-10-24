"""Le poste peut avoir des clients locaux sans devenir la documentation du plugin."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import check_affirmations
import check_commands
import check_links
from bench import campaign, corriges


class PerimetreDocumentaireTests(unittest.TestCase):
    def test_artefacts_exclus_et_documents_du_corpus_conserves(self):
        with tempfile.TemporaryDirectory() as dossier:
            root = Path(dossier)
            gardes = ("docs/guide.md", "tests/campaign/fixtures/procedure.md")
            exclus = ("tests/bench/runs/reponse.md", "outils/node_modules/tiers/README.md")
            for nom in gardes + exclus:
                p = root / nom
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("plugin v0.1.0 [lien](absent.md)", encoding="utf-8")
            for module, fn in ((check_affirmations, check_affirmations.documents),
                               (check_commands, check_commands.iter_markdown),
                               (check_links, check_links.iter_markdown)):
                with self.subTest(module=module.__name__), mock.patch.object(module, "ROOT", root):
                    self.assertEqual(set(gardes), {p.relative_to(root).as_posix() for p in fn()})
            # La restriction ne masque pas les erreurs d'un document de premier rang.
            with mock.patch.object(check_links, "ROOT", root):
                self.assertTrue(check_links.check_file(root / gardes[0]))

    def test_exporter_ne_modifie_ni_corpus_ni_validation(self):
        avant = campaign.CORPUS.read_bytes()
        with tempfile.TemporaryDirectory() as dossier:
            sortie = Path(dossier) / "corriges.md"
            self.assertEqual(36, corriges.exporter(sortie))
            texte = sortie.read_text(encoding="utf-8")
            self.assertIn("0/36", texte)
            self.assertIn("M18-b", texte)
            self.assertIn("brouillons", texte)
        self.assertEqual(avant, campaign.CORPUS.read_bytes())
        self.assertFalse(any(campaign.gold_pret(c) for c in campaign.corpus()))

    def test_exporter_refuse_de_remplacer_le_corpus(self):
        with self.assertRaisesRegex(ValueError, "remplacer le corpus"):
            corriges.exporter(campaign.CORPUS)


if __name__ == "__main__":
    unittest.main()
