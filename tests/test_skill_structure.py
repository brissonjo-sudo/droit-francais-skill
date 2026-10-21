"""Conservation de la méthode, taille du noyau et identité du paquet."""
from __future__ import annotations

import csv
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from check_skill_structure import CORRESPONDANCE, ROOT, check_rows, instruction_manifest


class SkillStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CORRESPONDANCE.open(encoding="utf-8", newline="") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_le_noyau_respecte_les_deux_plafonds(self):
        text = (ROOT / "skill/SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 400)
        self.assertLessEqual(len(text), 20_000)

    def test_les_337_unites_sont_a_leur_emplacement_realise(self):
        self.assertEqual(check_rows(self.rows), [])

    def test_un_checkout_crlf_conserve_la_preuve_normalisee(self):
        rows = deepcopy(self.rows)
        for row in rows:
            row["texte_source"] = row["texte_source"].replace("\n", "\r\n")
            row["texte_realise"] = row["texte_realise"].replace("\n", "\r\n")
        self.assertEqual(check_rows(rows), [])

    def test_une_unite_omise_est_detectee(self):
        self.assertTrue(check_rows(self.rows[:-1]))

    def test_une_regle_modifiee_ne_peut_pas_etre_revalidee_par_le_csv(self):
        rows = deepcopy(self.rows)
        rows[20]["texte_source"] = "Une règle différente"
        rows[20]["texte_realise"] = "Une règle différente"
        self.assertTrue(check_rows(rows))

    def test_un_emplacement_decale_est_detecte(self):
        rows = deepcopy(self.rows)
        rows[20]["debut_realise"] = str(int(rows[20]["debut_realise"]) + 1)
        self.assertTrue(check_rows(rows))

    def test_un_fichier_manquant_est_detecte(self):
        rows = deepcopy(self.rows)
        rows[20]["fichier_realise"] = "skill/references/absente.md"
        self.assertTrue(check_rows(rows))

    def test_les_ancres_contractuelles_restent_uniques(self):
        text = (ROOT / "skill/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## Déclenchement\n"), 1)
        self.assertEqual(text.count("## 7. Déclencheurs d'abstention (ou sortie dégradée balisée)\n"), 1)

    def test_vibe_declare_la_lecture_et_ses_references_sont_installees(self):
        text = (ROOT / "vibe_skill/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("  - read_file\n", text)
        for name in ("SKILL.md", "references/sources-autorisees.md", "references/modules.md"):
            self.assertIn(f"../skill/{name}", text)
            self.assertTrue((ROOT / "skill" / name).is_file())

    def test_le_manifeste_change_si_une_reference_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            references = root / "skill/references"
            references.mkdir(parents=True)
            (root / "skill/SKILL.md").write_text("noyau\n", encoding="utf-8")
            reference = references / "regle.md"
            reference.write_text("règle A\n", encoding="utf-8")
            before = instruction_manifest(root)
            reference.write_text("règle B\n", encoding="utf-8")
            self.assertNotEqual(before["sha256"], instruction_manifest(root)["sha256"])
