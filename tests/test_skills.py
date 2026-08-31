#!/usr/bin/env python3
"""Tests du catalogue de compétences (extension Skills, SEP-2640).

Le transport n'existe pas encore côté SDK : ces tests portent sur la charge
utile, seule partie qui peut être figée aujourd'hui.
"""

from __future__ import annotations

import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp_server.skills import (  # noqa: E402
    EXTENSION_CAPABILITY,
    SERVER_NAMESPACE,
    build_catalogue,
    build_skill,
    parse_frontmatter,
    read_resource,
    resource_index,
)

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class FrontmatterTests(unittest.TestCase):
    def test_recolle_une_description_sur_plusieurs_lignes(self):
        texte = "---\nname: exemple\ndescription: début\n  suite\n  fin\n---\ncorps\n"
        self.assertEqual(
            parse_frontmatter(texte),
            {"name": "exemple", "description": "début suite fin"},
        )

    def test_ignore_les_blocs_imbriques(self):
        texte = "---\nname: exemple\nmetadata:\n  version: 1.0.0\n---\n"
        self.assertEqual(parse_frontmatter(texte), {"name": "exemple"})

    def test_texte_sans_frontmatter(self):
        self.assertEqual(parse_frontmatter("# Titre\n"), {})


class CatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = build_catalogue()
        cls.skill = cls.catalogue["skills"][0]

    def test_un_seul_skill_publie(self):
        self.assertEqual(len(self.catalogue["skills"]), 1)

    def test_identifiant_construit_sur_le_nom_du_frontmatter(self):
        nom = self.skill["frontmatter"]["name"]
        self.assertEqual(
            self.skill["uri"], f"skill://{SERVER_NAMESPACE}/{nom}/SKILL.md"
        )

    def test_frontmatter_porte_nom_et_description(self):
        self.assertIn("name", self.skill["frontmatter"])
        self.assertTrue(self.skill["frontmatter"]["description"])

    def test_le_noyau_est_la_premiere_ressource(self):
        self.assertEqual(self.skill["resources"][0]["uri"], self.skill["uri"])

    def test_les_references_accompagnent_le_noyau(self):
        uris = [r["uri"] for r in self.skill["resources"]]
        self.assertGreater(len(uris), 1)
        self.assertTrue(any("/references/" in u for u in uris))

    def test_aucun_script_publie(self):
        # Les scripts sont des programmes : le serveur les expose en outils.
        uris = [r["uri"] for r in self.skill["resources"]]
        self.assertFalse([u for u in uris if "/scripts/" in u])

    def test_chaque_empreinte_est_un_sha256_minuscule(self):
        for ressource in self.skill["resources"]:
            self.assertRegex(ressource["digest"], DIGEST)

    def test_chaque_empreinte_correspond_au_contenu_reel(self):
        for ressource in self.skill["resources"]:
            contenu = read_resource(ressource["uri"])
            attendu = "sha256:" + hashlib.sha256(contenu.encode("utf-8")).hexdigest()
            self.assertEqual(ressource["digest"], attendu, ressource["uri"])

    def test_chaque_identifiant_est_resolvable(self):
        index = resource_index()
        for ressource in self.skill["resources"]:
            self.assertIn(ressource["uri"], index)
            self.assertTrue(index[ressource["uri"]].is_file())

    def test_identifiants_uniques(self):
        uris = [r["uri"] for r in self.skill["resources"]]
        self.assertEqual(len(uris), len(set(uris)))

    def test_ressource_hors_catalogue_refusee(self):
        with self.assertRaises(KeyError):
            read_resource("skill://droit-francais/recherche-juridique/inconnu.md")

    def test_catalogue_stable_entre_deux_appels(self):
        self.assertEqual(build_catalogue(), build_catalogue())


class DigestSensibiliteTests(unittest.TestCase):
    """Une empreinte qui ne bouge pas avec le contenu ne sert à rien."""

    def test_une_modification_change_l_empreinte(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "skill"
            dossier.mkdir()
            noyau = dossier / "SKILL.md"
            noyau.write_text("---\nname: essai\ndescription: d\n---\nA\n", encoding="utf-8")
            avant = build_skill(dossier)["resources"][0]["digest"]
            noyau.write_text("---\nname: essai\ndescription: d\n---\nB\n", encoding="utf-8")
            apres = build_skill(dossier)["resources"][0]["digest"]
            self.assertNotEqual(avant, apres)

    def test_skill_sans_nom_refuse(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            dossier = Path(tmp) / "skill"
            dossier.mkdir()
            (dossier / "SKILL.md").write_text("---\ndescription: d\n---\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_skill(dossier)


class CapabiliteTests(unittest.TestCase):
    def test_identifiant_d_extension_exact(self):
        self.assertEqual(
            list(EXTENSION_CAPABILITY), ["io.modelcontextprotocol/skills"]
        )


if __name__ == "__main__":
    unittest.main()
