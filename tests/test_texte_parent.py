#!/usr/bin/env python3
"""Texte parent et section dans get_article : hors réseau, réponses réelles réduites."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))

from droit_francais import tools as legal_tools  # noqa: E402

DECRET_TITRE = (
    "Décret n°88-547 du 6 mai 1988 portant statut particulier du cadre d'emplois "
    "des agents de maîtrise territoriaux"
)
#: /consult/getArticle LEGIARTI000033247542 (décret 88-547), champs réduits.
ARTICLE_DECRET = {
    "id": "LEGIARTI000033247542",
    "num": "9-2",
    "etat": "VIGUEUR",
    "dateDebut": 1467331200000,
    "dateFin": 32472144000000,
    "texte": "Texte de l'article.",
    "sectionParentId": "LEGISCTA000018943319",
    "sectionParentTitre": "CHAPITRE III : Nomination, titularisation et formation obligatoire.",
    "textTitles": [
        {"id": "JORFTEXT000000866458", "cid": "JORFTEXT000000866458",
         "titre": "Décret n° 88-547 du 6 mai 1988", "etat": "", "nature": "DECRET",
         "nor": "MCLB8800149D", "num": "88-547", "datePubli": 578966400000,
         "dateDebut": 32472144000000, "titreLong": DECRET_TITRE.replace("n°88", "n° 88")},
        {"id": "LEGITEXT000006066665", "cid": "JORFTEXT000000866458",
         "titre": "Décret n°88-547 du 6 mai 1988", "etat": "VIGUEUR", "nature": "DECRET",
         "nor": "MCLB8800149D", "num": "88-547", "datePubli": 578966400000,
         "dateDebut": 578966400000, "titreLong": DECRET_TITRE},
    ],
}
#: Article de code : une seule entrée LEGITEXT, date de publication sentinelle.
ARTICLE_CODE = {
    "id": "LEGIARTI000037312533", "num": "L80 A", "etat": "VIGUEUR", "texte": "…",
    "sectionParentId": "LEGISCTA000006163093",
    "sectionParentTitre": "Section VI : Conséquences et limites des procédures de rectification",
    "textTitles": [{"id": "LEGITEXT000006069583", "cid": "LEGITEXT000006069583",
                    "titre": "Livre des procédures fiscales", "etat": "VIGUEUR",
                    "nature": "CODE", "nor": "", "num": "", "datePubli": 32472144000000}],
}


@mock.patch("droit_francais.tools.get_token", return_value="token")
@mock.patch("droit_francais.tools.api_call")
class TexteParentTests(unittest.TestCase):
    def _lire(self, api_call, article):
        api_call.return_value = {"article": article}
        return legal_tools.get_article("LEGIARTI000033247542")

    def test_decret_non_codifie_expose_legitext_jorftext_et_titre_complet(self, api_call, _token):
        result = self._lire(api_call, ARTICLE_DECRET)
        self.assertEqual(
            {
                "id": "LEGITEXT000006066665",
                "jorftext_id": "JORFTEXT000000866458",
                "nature": "DECRET",
                "number": "88-547",
                "nor": "MCLB8800149D",
                "title": DECRET_TITRE,
                "legal_status": "VIGUEUR",
                "publication_date": "1988-05-07",
            },
            result["parent_text"],
        )
        self.assertEqual(
            {"id": "LEGISCTA000018943319",
             "title": "CHAPITRE III : Nomination, titularisation et formation obligatoire."},
            result["section"],
        )
        # Ajout seul : les clés historiques restent en place.
        self.assertEqual("Article 9-2", result["title"])
        self.assertEqual("Texte de l'article.", result["text"])

    def test_article_de_code_ignore_la_date_sentinelle(self, api_call, _token):
        parent = self._lire(api_call, ARTICLE_CODE)["parent_text"]
        self.assertEqual("LEGITEXT000006069583", parent["id"])
        self.assertEqual("CODE", parent["nature"])
        self.assertNotIn("publication_date", parent)
        self.assertNotIn("jorftext_id", parent)

    def test_sans_text_titles_repli_sans_erreur(self, api_call, _token):
        article = {k: v for k, v in ARTICLE_DECRET.items()
                   if k not in ("textTitles", "sectionParentId", "sectionParentTitre")}
        result = self._lire(api_call, article)
        self.assertNotIn("parent_text", result)
        self.assertNotIn("section", result)
        self.assertEqual("Article 9-2", result["title"])
        result = self._lire(api_call, {**article, "textTitles": [None, "x"]})
        self.assertNotIn("parent_text", result)


if __name__ == "__main__":
    unittest.main()
