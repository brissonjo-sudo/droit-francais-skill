#!/usr/bin/env python3
"""Garde-fous de contrat et de confidentialité de la sonde de production."""

from __future__ import annotations

import ast
import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server.catalog import EXPECTED_TOOLS  # noqa: E402

TESTS = ROOT / "tests"
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

import check_live_tools as sonde  # noqa: E402

SONDE = ROOT / "tests" / "check_live_tools.py"


def resultat(*, charge=None, erreur=False, texte=""):
    """Construit le strict minimum d'un résultat MCP v2 pour les tests."""
    return SimpleNamespace(
        isError=erreur,
        structuredContent=charge,
        content=[SimpleNamespace(text=texte)] if texte else [],
    )


class CouvertureSondeProductionTests(unittest.TestCase):
    def test_chaque_outil_est_reellement_appele(self) -> None:
        arbre = ast.parse(SONDE.read_text(encoding="utf-8"))
        appeles = {
            appel.args[0].value
            for appel in ast.walk(arbre)
            if isinstance(appel, ast.Call)
            and isinstance(appel.func, ast.Name)
            and appel.func.id == "appeler"
            and appel.args
            and isinstance(appel.args[0], ast.Constant)
            and isinstance(appel.args[0].value, str)
        }
        self.assertEqual(set(EXPECTED_TOOLS), appeles)

    def test_applicabilite_est_controlee_par_presence_et_non_par_verite(self) -> None:
        """``False`` est la valeur normale d'une version historique.

        Contrôler ce champ par sa valeur de vérité rejetterait deux réponses
        correctes : ``False`` (version non applicable à la date évaluée) et
        ``None`` (date de début manquante, applicabilité indéterminée).
        """
        arbre = ast.parse(SONDE.read_text(encoding="utf-8"))
        champ = "applicable_at_as_of_date"

        boucles_de_verite = {
            element.value
            for noeud in ast.walk(arbre)
            if isinstance(noeud, ast.For) and isinstance(noeud.iter, ast.Tuple)
            for element in noeud.iter.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        }
        self.assertNotIn(champ, boucles_de_verite)

        controles_de_presence = {
            noeud.left.value
            for noeud in ast.walk(arbre)
            if isinstance(noeud, ast.Compare)
            and isinstance(noeud.left, ast.Constant)
            and isinstance(noeud.left.value, str)
            and any(isinstance(operateur, ast.NotIn) for operateur in noeud.ops)
        }
        self.assertIn(champ, controles_de_presence)

    def test_erreur_distante_est_masquee(self) -> None:
        secret = "jeton-tres-secret"
        with self.assertRaises(sonde.SondeError) as caught:
            sonde._exiger_succes(
                resultat(erreur=True, texte=f"Authorization: Bearer {secret}"),
                "appel",
            )
        self.assertNotIn(secret, str(caught.exception))
        self.assertIn("masqué", str(caught.exception))

    def test_bearer_est_inclus_dans_le_controle_anti_secret(self) -> None:
        secret = "bearer-sentinelle-non-jwt"
        sortie = io.StringIO()
        with mock.patch.dict(os.environ, {"MCP_ACCESS_TOKEN": secret}, clear=True):
            with contextlib.redirect_stdout(sortie):
                with self.assertRaises(sonde.SondeError) as caught:
                    sonde._verifier_absence_de_secrets(
                        f"réponse contaminée {secret}", "appel"
                    )
        rendu = sortie.getvalue() + str(caught.exception)
        self.assertNotIn(secret, rendu)
        self.assertIn("MCP_ACCESS_TOKEN", rendu)

    def test_absence_refuse_une_erreur_distante(self) -> None:
        with self.assertRaises(sonde.SondeError):
            sonde._exiger_absence_reussie(
                resultat(charge={"results": []}, erreur=True, texte="HTTP 429"),
                "article inexistant",
            )

    def test_absence_exige_une_liste_vide(self) -> None:
        with self.assertRaises(sonde.SondeError):
            sonde._exiger_absence_reussie(
                resultat(charge={}), "article inexistant"
            )
        with self.assertRaises(sonde.SondeError):
            sonde._exiger_absence_reussie(
                resultat(charge={"results": [{"id": "x"}]}),
                "article inexistant",
            )
        charge = {"results": []}
        self.assertIs(
            charge,
            sonde._exiger_absence_reussie(
                resultat(charge=charge), "article inexistant"
            ),
        )

    def test_lecture_officielle_valide_le_contrat_complet(self) -> None:
        charge = {
            "id": "LEGIARTI1",
            "text": "Texte officiel",
            "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI1",
            "metadata": {"source": "Légifrance API", "verified": True},
        }
        metadata = sonde._exiger_lecture_officielle(
            charge,
            "LEGIARTI1",
            "Légifrance API",
            "www.legifrance.gouv.fr",
            "get_article",
        )
        self.assertTrue(metadata["verified"])

    def test_lecture_officielle_refuse_hote_texte_ou_preuve_invalides(self) -> None:
        base = {
            "id": "LEGIARTI1",
            "text": "Texte officiel",
            "url": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI1",
            "metadata": {"source": "Légifrance API", "verified": True},
        }
        variations = (
            {**base, "text": ""},
            {**base, "url": "https://example.org/LEGIARTI1"},
            {**base, "metadata": {"source": "Légifrance API", "verified": False}},
        )
        for charge in variations:
            with self.subTest(charge=charge):
                with self.assertRaises(sonde.SondeError):
                    sonde._exiger_lecture_officielle(
                        charge,
                        "LEGIARTI1",
                        "Légifrance API",
                        "www.legifrance.gouv.fr",
                        "get_article",
                    )


if __name__ == "__main__":
    unittest.main()
