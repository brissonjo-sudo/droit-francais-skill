"""Tests du contrôle des affirmations — le chemin d'échec, surtout.

Un vérificateur qui ne se déclenche jamais ne protège de rien. La CI n'exerce
que le cas où le dépôt concorde ; ces tests montent un dépôt factice, y
injectent chacune des régressions réellement constatées le 1er septembre 2026,
et vérifient que le contrôle les refuse.

La dernière compte autant que les autres : elle fait dériver le **serveur** en
laissant la documentation juste. Un contrôle qui présumerait la documentation
coupable la laisserait passer.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import check_affirmations  # noqa: E402

SERVEUR_FACTICE = '''\
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    openWorldHint=False,
)
'''

OUTILS_FACTICES = {
    "tools": {
        "search": {
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "openWorldHint": False,
            }
        }
    }
}


class DepotFactice:
    """Arborescence minimale portant les quatre sources que le contrôle lit."""

    def __init__(self, racine: Path) -> None:
        self.racine = racine
        (racine / ".codex-plugin").mkdir(parents=True)
        (racine / "mcp_server").mkdir()
        (racine / "skill" / "scripts").mkdir(parents=True)
        (racine / "tests").mkdir()
        (racine / "docs").mkdir()
        self.ecrire_manifeste("0.7.0")
        self.ecrire_serveur(SERVEUR_FACTICE)
        self.ecrire_soumission(OUTILS_FACTICES)
        (racine / "skill" / "scripts" / ".env.example").write_text(
            "MCP_AUTH_MODE=oauth\n", encoding="utf-8"
        )
        self.ecrire_doc("Le plugin v0.7.0 expose `openWorldHint: false`.\n")

    def ecrire_manifeste(self, version: str) -> None:
        (self.racine / ".codex-plugin" / "plugin.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )

    def ecrire_serveur(self, contenu: str) -> None:
        (self.racine / "mcp_server" / "server.py").write_text(contenu, encoding="utf-8")

    def ecrire_soumission(self, contenu: dict) -> None:
        (self.racine / "chatgpt-app-submission.json").write_text(
            json.dumps(contenu), encoding="utf-8"
        )

    def ecrire_doc(self, texte: str) -> None:
        (self.racine / "docs" / "guide.md").write_text(texte, encoding="utf-8")

    def ecrire_changelog(self, texte: str) -> None:
        (self.racine / "skill" / "CHANGELOG.md").write_text(texte, encoding="utf-8")

    def problemes(self) -> list[str]:
        """Exécute les trois contrôles contre ce dépôt factice."""
        racine = self.racine
        with mock.patch.multiple(
            check_affirmations,
            ROOT=racine,
            SERVER=racine / "mcp_server" / "server.py",
            MANIFEST=racine / ".codex-plugin" / "plugin.json",
            SUBMISSION=racine / "chatgpt-app-submission.json",
            ENV_EXAMPLE=racine / "skill" / "scripts" / ".env.example",
        ):
            releves: list[str] = []
            check_affirmations.controler_versions(releves)
            check_affirmations.controler_annotations(releves)
            check_affirmations.controler_variables(releves)
            return releves


class ControleAffirmationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.depot = DepotFactice(Path(self._tmp.name))

    def test_un_depot_coherent_ne_leve_rien(self) -> None:
        self.assertEqual([], self.depot.problemes())

    def test_version_de_plugin_perimee_dans_la_prose(self) -> None:
        # Le défaut du README : la prose fige une version que le manifeste a dépassée.
        self.depot.ecrire_doc("Distribution du plugin v0.5.0.\n")
        problemes = self.depot.problemes()
        self.assertEqual(1, len(problemes))
        self.assertIn("v0.5.0", problemes[0])
        self.assertIn("0.7.0", problemes[0])

    def test_le_changelog_peut_porter_les_versions_passees(self) -> None:
        """Un « Keep a Changelog » n'existe que pour citer les versions passées.

        Leur exiger la version courante rendait toute montée de version
        impossible : le constat a été fait en montant le plugin en 0.8.0, sa
        première montée. Le CHANGELOG rejoint donc les journaux datés.
        """
        self.depot.ecrire_changelog(
            "### [plugin-v0.7.0] — 2026-09-01\n\nPremière release.\n"
        )
        self.assertEqual([], self.depot.problemes())

    def test_une_version_perimee_hors_journal_reste_refusee(self) -> None:
        # Le garde-fou ne doit pas se relâcher ailleurs : c'est la prose
        # courante, pas l'historique, que le contrôle vise.
        self.depot.ecrire_changelog("### [plugin-v0.7.0] — 2026-09-01\n")
        self.depot.ecrire_doc("Le plugin est en v0.5.0.\n")
        problemes = self.depot.problemes()
        self.assertEqual(1, len(problemes))
        self.assertIn("guide.md", problemes[0])

    def test_annotation_contredite_par_le_serveur(self) -> None:
        # Le défaut de deployment.md : la doc promet une valeur que le code a changée.
        self.depot.ecrire_doc("Les outils annoncent `openWorldHint: true`.\n")
        problemes = self.depot.problemes()
        self.assertEqual(1, len(problemes))
        self.assertIn("openWorldHint", problemes[0])

    def test_variable_d_environnement_inexistante(self) -> None:
        self.depot.ecrire_doc("Poser MCP_AUTH_MODE_V2 sur l'hébergeur.\n")
        problemes = self.depot.problemes()
        self.assertEqual(1, len(problemes))
        self.assertIn("MCP_AUTH_MODE_V2", problemes[0])

    def test_le_dossier_de_soumission_qui_diverge_du_serveur(self) -> None:
        divergent = json.loads(json.dumps(OUTILS_FACTICES))
        divergent["tools"]["search"]["annotations"]["openWorldHint"] = True
        self.depot.ecrire_soumission(divergent)
        problemes = self.depot.problemes()
        self.assertEqual(1, len(problemes))
        self.assertIn("search.openWorldHint", problemes[0])

    def test_la_derive_se_detecte_aussi_cote_serveur(self) -> None:
        # Sens inverse : la documentation reste juste, c'est le serveur qui bouge.
        # Un contrôle qui présumerait la doc coupable ne verrait rien ici.
        self.depot.ecrire_serveur(
            SERVEUR_FACTICE.replace("openWorldHint=False", "openWorldHint=True")
        )
        problemes = self.depot.problemes()
        self.assertEqual(2, len(problemes))
        self.assertTrue(any("guide.md" in p for p in problemes))
        self.assertTrue(any("chatgpt-app-submission.json" in p for p in problemes))

    def test_le_depot_reel_est_coherent(self) -> None:
        # Garde-fou de bout en bout, sur les vraies sources cette fois.
        self.assertEqual(0, check_affirmations.main())


if __name__ == "__main__":
    unittest.main()
