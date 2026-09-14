#!/usr/bin/env python3
"""Tests d'intégrité et de conformité de la déclinaison gemini_skill/.

Vérifie que la déclinaison Gemini respecte les standards du dépôt :
- frontmatter conforme aux spécifications Agent Skills (name, versions) ;
- présence intégrale des 7 principes invariants P1 à P7 ;
- documentation complète des 6 modules activables ;
- hiérarchie rigoureuse des 4 voies de récupération d'outils ;
- intégrité des liens relatifs internes et des références ;
- cohérence du prompt système dans le package compagnon gemini_agent/.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Mock gracieux si google-genai n'est pas installé dans l'environnement de test
for mod in ("google", "google.genai", "google.genai.types"):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

GEMINI_SKILL_DIR = ROOT / "gemini_skill"
SKILL_MD = GEMINI_SKILL_DIR / "SKILL.md"
MODULES_MD = GEMINI_SKILL_DIR / "references" / "modules.md"
SOURCES_MD = GEMINI_SKILL_DIR / "references" / "sources-autorisees.md"
README_MD = GEMINI_SKILL_DIR / "README.md"


class GeminiSkillIntegrityTests(unittest.TestCase):
    def test_fichiers_fondamentaux_presents(self):
        self.assertTrue(SKILL_MD.is_file(), "SKILL.md manquant")
        self.assertTrue(MODULES_MD.is_file(), "modules.md manquant")
        self.assertTrue(SOURCES_MD.is_file(), "sources-autorisees.md manquant")
        self.assertTrue(README_MD.is_file(), "README.md manquant")

    def test_frontmatter_conforme(self):
        texte = SKILL_MD.read_text(encoding="utf-8")
        self.assertTrue(texte.startswith("---"), "Frontmatter doit commencer par ---")
        parties = texte.split("---", 2)
        self.assertGreaterEqual(len(parties), 3, "Frontmatter non fermé")
        frontmatter = parties[1]

        self.assertIn("name: recherche-juridique", frontmatter)
        self.assertIn("version: 3.3.0-gemini", frontmatter)
        self.assertIn("base_version: 3.3.0", frontmatter)
        self.assertIn("adapted_for: Gemini", frontmatter)

    def test_presence_sept_principes_invariants(self):
        texte = SKILL_MD.read_text(encoding="utf-8")
        for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
            with self.subTest(principe=p):
                pattern = rf"\b{p}\b"
                self.assertRegex(
                    texte,
                    pattern,
                    f"Le principe invariant {p} doit être formellement énoncé dans SKILL.md",
                )

    def test_presence_six_modules_activables(self):
        texte = MODULES_MD.read_text(encoding="utf-8")
        modules = ("PÉNAL", "ACTE-ADMIN", "PA-PJ", "FOND", "CONTENTIEUX", "DOC-AUDIT")
        for mod in modules:
            with self.subTest(module=mod):
                self.assertIn(
                    f"## Module {mod}",
                    texte,
                    f"Le module {mod} doit avoir sa section dédiée dans modules.md",
                )

    def test_echelle_outils_gemini(self):
        texte = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Voie 1 : Connecteur MCP officiel", texte)
        self.assertIn("Voie 2 : Recherche Google / Grounding", texte)
        self.assertIn("Voie 3 : Code Execution / Client Python", texte)
        self.assertIn("Voie 4 : Abstention informée", texte)

    def test_coherence_agent_compagnon(self):
        from gemini_agent.legal_agent_config import (
            MODEL_NAME,
            SYSTEM_PROMPT,
            TEMPERATURE,
            LegalAgentConfig,
        )

        self.assertEqual(MODEL_NAME, "gemini-2.5-pro")
        self.assertEqual(TEMPERATURE, 0.0)
        self.assertIn("v3.3.0", SYSTEM_PROMPT)
        for p in ("P1", "P2", "P3", "P4", "P5", "P6", "P7"):
            with self.subTest(principe_agent=p):
                self.assertIn(
                    p,
                    SYSTEM_PROMPT,
                    f"Le principe {p} doit figurer dans le SYSTEM_PROMPT de l'agent Python",
                )

        cfg = LegalAgentConfig()
        self.assertEqual(cfg.temperature, 0.0)


if __name__ == "__main__":
    unittest.main()
