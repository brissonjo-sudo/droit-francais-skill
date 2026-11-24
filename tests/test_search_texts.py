#!/usr/bin/env python3
"""search_texts hors réseau : réponse /search LODA_DATE réelle, réduite."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))

from droit_francais import tools as legal_tools  # noqa: E402
from droit_francais.errors import LegifranceError  # noqa: E402

TITRE = (
    "Décret n°88-547 du 6 mai 1988 portant statut particulier du cadre d'emplois "
    "des agents de maîtrise territoriaux"
)


def resultat(identifiant, titre, cid, nor, nature="DECRET"):
    """Forme observée : ``num`` vide, version datée dans le suffixe de ``titles[0].id``."""
    return {
        "nature": nature, "num": None, "nor": nor, "etat": "VIGUEUR", "origin": "LEGI",
        "datePublication": "1988-05-07T00:00:00.000+0000",
        "titles": [{"id": identifiant, "cid": cid, "title": titre, "legalStatus": None}],
    }


def decret(version):
    return resultat(f"LEGITEXT000006066665_{version}", TITRE, "JORFTEXT000000866458", "MCLB8800149D")


@mock.patch("droit_francais.text_search.get_token", return_value="token")
@mock.patch("droit_francais.text_search.api_call")
class SearchTextsTests(unittest.TestCase):
    def test_dedoublonne_par_legitext_et_retire_le_suffixe(self, api_call, _token):
        # Trois versions du même texte, dont une programmée dans le futur.
        api_call.return_value = {
            "totalResultNumber": 3,
            "results": [decret("01-11-2005"), decret("01-01-2022"), decret("01-01-2999")],
        }
        found = legal_tools.search_texts(number="n° 88-547")
        self.assertEqual(1, len(found["results"]))
        text = found["results"][0]
        self.assertEqual("LEGITEXT000006066665", text["legitext_id"])
        self.assertEqual("JORFTEXT000000866458", text["jorftext_id"])
        self.assertEqual("88-547", text["number"])
        self.assertEqual("MCLB8800149D", text["nor"])
        self.assertEqual(TITRE, text["title"])
        self.assertEqual("2022-01-01", text["version_date"])
        self.assertEqual("1988-05-07", text["publication_date"])
        self.assertEqual("https://www.legifrance.gouv.fr/loda/id/LEGITEXT000006066665/", text["url"])
        self.assertNotIn("_", text["legitext_id"])
        self.assertFalse(found["truncated"])
        body = api_call.call_args.args[1]
        self.assertEqual("LODA_DATE", body["fond"])
        champs = body["recherche"]["champs"]
        self.assertEqual([("NUM", "88-547")],
                         [(c["typeChamp"], c["criteres"][0]["valeur"]) for c in champs])
        self.assertEqual([], body["recherche"]["filtres"])

    def test_filtre_serveur_ecarte_ce_qui_ne_correspond_pas_exactement(self, api_call, _token):
        modificateur = resultat(
            "LEGITEXT000033245422_01-01-2017",
            "Décret n° 2016-1382 du 12 octobre 2016 modifiant le décret n° 88-547 du 6 mai 1988",
            "JORFTEXT000033243020", "ARCB1618936D",
        )
        autre = resultat("LEGITEXT000000000001_01-01-2020", "Décret n° 88-5470 du 1 mai 2020",
                         "JORFTEXT000000000001", "AAAA0000000D")
        api_call.return_value = {"totalResultNumber": 3,
                                 "results": [modificateur, autre, decret("01-01-2022")]}
        found = legal_tools.search_texts(number="88-547")
        self.assertEqual(["LEGITEXT000006066665"], [t["legitext_id"] for t in found["results"]])
        self.assertEqual(2, found["rejected_results"])

    def test_nor_exact_et_date_de_version(self, api_call, _token):
        arrete = resultat("LEGITEXT000005631789_01-10-2026",
                          "Arrêté du 14 novembre 2001 fixant les tarifs maxima",
                          "JORFTEXT000000587932", "INTD0100681A", nature="ARRETE")
        api_call.return_value = {"totalResultNumber": 1, "results": [arrete, decret("01-01-2022")]}
        found = legal_tools.search_texts(nor="intd0100681a", date="2026-11-24")
        self.assertEqual(["LEGITEXT000005631789"], [t["legitext_id"] for t in found["results"]])
        self.assertNotIn("number", found["results"][0])
        body = api_call.call_args.args[1]["recherche"]
        self.assertEqual("NOR", body["champs"][0]["typeChamp"])
        self.assertEqual("DATE_VERSION", body["filtres"][0]["facette"])
        self.assertEqual("2026-11-24", found["dating"]["as_of_date"])

    def test_resultat_vide_et_troncature_signalee(self, api_call, _token):
        api_call.return_value = {"totalResultNumber": 0, "results": []}
        self.assertEqual([], legal_tools.search_texts(number="99-999999")["results"])
        api_call.return_value = {"totalResultNumber": 250, "results": [decret("01-01-2022")]}
        self.assertTrue(legal_tools.search_texts(number="88-547")["truncated"])

    def test_refuse_un_appel_sans_critere_ou_malforme(self, api_call, _token):
        for kwargs in ({}, {"number": "  "}, {"number": "88 547"}, {"nor": "court"},
                       {"number": "88-547", "date": "hier"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(LegifranceError) as caught:
                legal_tools.search_texts(**kwargs)
            self.assertEqual(2, caught.exception.exit_code)
        api_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
