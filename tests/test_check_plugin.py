#!/usr/bin/env python3
"""Le contrôle du socle Claude Code doit échouer sur chaque défaut qu'il annonce.

Un vérificateur qui passe toujours ne vérifie rien. Chaque invariant de
`check_plugin.controler_socle_claude` est donc éprouvé sur un couple
manifeste/marketplace qui le viole, et sur un couple qui le respecte.

Le contrôle vise une classe d'erreur constatée le 14 septembre 2026 : le
manifeste `.claude-plugin/plugin.json` n'était lu par aucun vérificateur, alors
que `.github/auto-review.md` affirmait le contraire. Sa version pouvait diverger
de `SERVER_VERSION` sans que rien ne le signale.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import check_plugin  # noqa: E402

VERSION = "1.2.3"


def manifeste(**surcharges) -> dict:
    base = {"name": "droit-francais-skill", "version": VERSION}
    base.update(surcharges)
    return base


def marketplace(**surcharges) -> dict:
    entree = {
        "name": "droit-francais-skill",
        "source": "./",
        "version": VERSION,
    }
    entree.update(surcharges.pop("entree", {}))
    base = {"owner": {"name": "brissonjo-sudo"}, "plugins": [entree]}
    base.update(surcharges)
    return base


class SocleClaudeTests(unittest.TestCase):
    def controler(self, manifeste_claude, marketplace_claude, server="1.2.3"):
        problemes: list[str] = []
        check_plugin.controler_socle_claude(
            manifeste_claude, marketplace_claude, server, problemes
        )
        return problemes

    def test_socle_conforme_ne_signale_rien(self):
        self.assertEqual(self.controler(manifeste(), marketplace()), [])

    def test_version_divergente_de_server_version(self):
        problemes = self.controler(manifeste(version="9.9.9"), marketplace())
        self.assertTrue(any("SERVER_VERSION" in p for p in problemes), problemes)

    def test_version_hors_semver(self):
        problemes = self.controler(manifeste(version="0.8"), marketplace())
        self.assertTrue(any("SemVer" in p for p in problemes), problemes)

    def test_nom_hors_kebab_case(self):
        problemes = self.controler(manifeste(name="Droit_Francais"), marketplace())
        self.assertTrue(any("kebab-case" in p for p in problemes), problemes)

    def test_proprietaire_du_marketplace_absent(self):
        problemes = self.controler(manifeste(), marketplace(owner={}))
        self.assertTrue(any("owner" in p for p in problemes), problemes)

    def test_marketplace_sans_plugin(self):
        problemes = self.controler(manifeste(), marketplace(plugins=[]))
        self.assertTrue(any("liste non vide" in p for p in problemes), problemes)

    def test_marketplace_ne_reference_pas_le_plugin(self):
        problemes = self.controler(
            manifeste(), marketplace(entree={"name": "autre-chose"})
        )
        self.assertTrue(any("ne reference pas" in p for p in problemes), problemes)

    def test_source_autre_que_la_racine(self):
        problemes = self.controler(
            manifeste(), marketplace(entree={"source": "./plugins/x"})
        )
        self.assertTrue(any("source './'" in p for p in problemes), problemes)

    def test_version_marketplace_desynchronisee(self):
        problemes = self.controler(manifeste(), marketplace(entree={"version": "0.0.1"}))
        self.assertTrue(any("entree marketplace" in p for p in problemes), problemes)


class DepotReelTests(unittest.TestCase):
    """Le dépôt lui-même doit satisfaire le contrôle."""

    def test_socle_du_depot_est_coherent(self):
        problemes: list[str] = []
        manifeste_claude = check_plugin.charger_json(
            check_plugin.MANIFEST_CLAUDE, problemes
        )
        marketplace_claude = check_plugin.charger_json(
            check_plugin.MARKETPLACE_CLAUDE, problemes
        )
        self.assertEqual(problemes, [])
        self.assertIsNotNone(manifeste_claude)
        self.assertIsNotNone(marketplace_claude)
        check_plugin.controler_socle_claude(
            manifeste_claude,
            marketplace_claude,
            manifeste_claude["version"],
            problemes,
        )
        self.assertEqual(problemes, [])

    def test_manifeste_claude_ne_duplique_pas_le_mcp(self):
        """`.mcp.json` racine est repris automatiquement : le dupliquer dérive."""
        problemes: list[str] = []
        manifeste_claude = check_plugin.charger_json(
            check_plugin.MANIFEST_CLAUDE, problemes
        )
        self.assertEqual(problemes, [])
        self.assertNotIn("mcpServers", manifeste_claude)


if __name__ == "__main__":
    unittest.main()
