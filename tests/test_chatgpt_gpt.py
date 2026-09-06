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
- correspondance exacte entre fichiers annoncés et fichiers présents ;
- toute référence du noyau reprise, sauf exclusion documentée ;
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
REFERENCES_NOYAU = ROOT / "skill" / "references"

PLAFOND_BUILDER = 8000
MARGE_REVISION = 500

#: Références du noyau volontairement non reprises dans les connaissances du
#: GPT. ``maintenance.md`` décrit la revue annuelle du dépôt — archivage,
#: CHANGELOG, veille — et non la méthode juridique : la téléverser ferait
#: croire au GPT qu'il doit conduire cette revue.
REFERENCES_ECARTEES = {"maintenance.md"}


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

    def _fichiers_annonces(self) -> set[str]:
        section = self.instructions.split("FICHIERS DE CONNAISSANCES", 1)[1]
        section = section.split("\n\n", 1)[0]
        return set(re.findall(r"([a-z-]+\.md)", section))

    def test_fichiers_de_connaissances_annonces_et_presents_concordent(self):
        """Correspondance exacte, dans les deux sens.

        Un fichier annoncé mais absent fait promettre au GPT une connaissance
        qu'il n'a pas. Un fichier présent mais non annoncé sera téléversé sans
        que rien n'y renvoie, donc rarement retrouvé par la recherche
        sémantique. Les deux écarts sont des défauts.
        """
        annonces = self._fichiers_annonces()
        presents = {p.name for p in REFERENCES.glob("*.md")}
        self.assertGreaterEqual(len(annonces), 2)
        self.assertEqual(
            annonces,
            presents,
            f"annoncés sans fichier : {sorted(annonces - presents)} ; "
            f"présents sans mention : {sorted(presents - annonces)}",
        )

    def test_references_du_noyau_reprises_ou_ecartees_sciemment(self):
        """Toute référence du noyau est reprise, sauf exclusion documentée.

        Une référence ajoutée au noyau fera échouer ce test tant qu'elle n'aura
        pas été soit portée dans les connaissances du GPT, soit inscrite dans
        REFERENCES_ECARTEES. C'est le but : l'arbitrage doit rester explicite.
        """
        noyau = {p.name for p in REFERENCES_NOYAU.glob("*.md")}
        presents = {p.name for p in REFERENCES.glob("*.md")}
        self.assertEqual(
            noyau - REFERENCES_ECARTEES - presents,
            set(),
            "références du noyau ni reprises ni écartées sciemment",
        )
        self.assertEqual(
            presents & REFERENCES_ECARTEES,
            set(),
            "référence déclarée écartée, pourtant présente",
        )

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
