#!/usr/bin/env python3
"""Tests d'intégrité de la déclinaison chatgpt_gpt/ (GPT personnalisé ChatGPT).

Le builder de GPT impose des contraintes de forme que rien d'autre ne
vérifie : un champ Instructions plafonné à 8 000 caractères (au-delà, le
GPT ne s'enregistre plus) et des fichiers de connaissances téléversés un à
un. Ces tests figent ce qui peut l'être :
- longueur des instructions sous le plafond, avec une marge de révision ;
- présence des sept principes invariants P1 à P7 ;
- présence des six modules activables dans modules.md ;
- échelle de récupération en trois voies (app, web officiel, abstention) ;
- chaque fichier de connaissances annoncé dans les instructions existe ;
- aucune mention d'outillage inexistant dans un GPT (scripts PISTE, MCP local).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GPT_DIR = ROOT / "chatgpt_gpt"
INSTRUCTIONS = GPT_DIR / "instructions.md"
README = GPT_DIR / "README.md"
REFERENCES = GPT_DIR / "references"

PLAFOND_BUILDER = 8000
MARGE_REVISION = 500


class ChatgptGptIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instructions = INSTRUCTIONS.read_text(encoding="utf-8")

    def test_fichiers_fondamentaux_presents(self):
        for path in (INSTRUCTIONS, README, REFERENCES / "modules.md",
                     REFERENCES / "sources-autorisees.md"):
            with self.subTest(fichier=path.name):
                self.assertTrue(path.is_file(), f"{path.name} manquant")

    def test_instructions_sous_le_plafond_du_builder(self):
        longueur = len(self.instructions)
        self.assertLessEqual(
            longueur,
            PLAFOND_BUILDER - MARGE_REVISION,
            f"{longueur} caractères : le builder refuse au-delà de "
            f"{PLAFOND_BUILDER}, garder {MARGE_REVISION} de marge",
        )

    def test_presence_sept_principes_invariants(self):
        for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
            with self.subTest(principe=p):
                self.assertRegex(self.instructions, rf"\b{p}\b")

    def test_echelle_de_recuperation_en_trois_voies(self):
        self.assertIn("App « Droit français »", self.instructions)
        self.assertIn("legifrance.gouv.fr", self.instructions)
        self.assertIn("abstention (P7)", self.instructions)

    def test_outils_de_l_app_nommes_exactement(self):
        for outil in ("search", "fetch", "search_articles", "get_article",
                      "search_case_law", "get_decision"):
            with self.subTest(outil=outil):
                self.assertRegex(self.instructions, rf"\b{outil}\b")

    def test_fichiers_de_connaissances_annonces_existent(self):
        section = self.instructions.split("FICHIERS DE CONNAISSANCES", 1)[1]
        section = section.split("\n\n", 1)[0]
        annonces = re.findall(r"([a-z-]+\.md)", section)
        self.assertGreaterEqual(len(annonces), 2)
        for nom in annonces:
            with self.subTest(fichier=nom):
                self.assertTrue((REFERENCES / nom).is_file(), f"{nom} annoncé mais absent")

    def test_presence_six_modules_activables(self):
        texte = (REFERENCES / "modules.md").read_text(encoding="utf-8")
        for mod in ("PÉNAL", "ACTE-ADMIN", "PA-PJ", "FOND", "CONTENTIEUX", "DOC-AUDIT"):
            with self.subTest(module=mod):
                self.assertIn(f"## Module {mod}", texte)

    def test_aucun_outillage_inexistant_dans_un_gpt(self):
        interdits = ("scripts/legifrance.py", "web_fetch", "SKILL.md", "${CLAUDE_PLUGIN_ROOT}")
        for path in [INSTRUCTIONS, *sorted(REFERENCES.glob("*.md"))]:
            texte = path.read_text(encoding="utf-8")
            for motif in interdits:
                with self.subTest(fichier=path.name, motif=motif):
                    self.assertNotIn(motif, texte)


if __name__ == "__main__":
    unittest.main()
