#!/usr/bin/env python3
"""Tests hors réseau de la sonde de surveillance et du résumé de série.

Ce que ces tests protègent : la distinction entre un **réveil d'instance** et
une **panne**. Les 1er et 2 septembre 2026, cinq réveils de 32,4 à 32,7 s ont
été consignés comme « service indisponible en pratique » alors que le service
répondait en 0,2 s à la requête suivante. Les deux appellent des décisions
opposées — changer d'hébergement, ou ouvrir un incident — et les confondre
rendait la période d'observation illisible.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ICI = Path(__file__).resolve().parent
if str(ICI) not in sys.path:
    sys.path.insert(0, str(ICI))

import check_service_health as sonde  # noqa: E402
import summarize_surveillance as resume  # noqa: E402

BASE = "https://exemple.test"
SANTE = {"version": "0.7.0", "auth": "oauth"}


def _mesures(*couples):
    """Programme les retours successifs de ``_mesurer`` : (code, durée)."""
    return [(code, duree, dict(SANTE), None) for code, duree in couples]


class SondeTests(unittest.TestCase):
    def setUp(self):
        # Les métadonnées OAuth ont leur propre sonde, déjà couverte ailleurs.
        patch = mock.patch.object(sonde, "verify", return_value=None)
        patch.start()
        self.addCleanup(patch.stop)

    def _sonder(self, *couples) -> dict:
        with mock.patch.object(sonde, "_mesurer", side_effect=_mesures(*couples)):
            return sonde.sonder(BASE)

    def test_premier_appel_lent_puis_rapide_est_un_reveil_pas_un_defaut(self):
        rapport = self._sonder((200, 32.4), (200, 0.20))
        self.assertTrue(rapport["reveil"])
        self.assertEqual(32.4, rapport["reveil_s"])
        self.assertEqual([], rapport["defauts"])
        self.assertEqual(1, len(rapport["avertissements"]))
        message = rapport["avertissements"][0]
        self.assertIn("réveil d'instance mesuré à 32.4 s", message)
        # La gravité reste dite : c'est elle qui bloque la publication.
        self.assertIn("au-delà du seuil d'alerte", message)
        self.assertIn("0.20 s à chaud", message)

    def test_un_reveil_sous_le_seuil_d_alerte_ne_crie_pas_a_la_gravite(self):
        rapport = self._sonder((200, 5.0), (200, 0.3))
        self.assertTrue(rapport["reveil"])
        self.assertNotIn("seuil d'alerte", rapport["avertissements"][0])
        self.assertEqual([], rapport["defauts"])

    def test_latence_a_chaud_hors_norme_reste_un_defaut(self):
        rapport = self._sonder((200, 45.0), (200, 42.0))
        self.assertFalse(rapport["reveil"])
        self.assertIsNone(rapport["reveil_s"])
        self.assertEqual(1, len(rapport["defauts"]))
        self.assertIn("latence à chaud de 42.0 s", rapport["defauts"][0])

    def test_service_sain_ne_produit_ni_defaut_ni_avertissement(self):
        rapport = self._sonder((200, 0.18), (200, 0.12))
        self.assertFalse(rapport["reveil"])
        self.assertEqual([], rapport["defauts"])
        self.assertEqual([], rapport["avertissements"])
        self.assertEqual("0.7.0", rapport["version"])

    def test_un_hote_injoignable_est_un_defaut_et_non_un_plantage(self):
        """Une panne de connexion doit produire une mesure, pas une trace de pile.

        Elle faisait planter la sonde : sortie standard vide, donc aucune
        ligne au journal, donc l'indisponibilité disparaissait de la série au
        lieu d'y être la mesure la plus visible.
        """
        with mock.patch.object(
            sonde.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("nom de domaine introuvable"),
        ):
            rapport = sonde.sonder(BASE)
        self.assertEqual(sonde.CODE_INJOIGNABLE, rapport["health_code"])
        self.assertEqual(sonde.CODE_INJOIGNABLE, rapport["health_code_chaud"])
        self.assertFalse(rapport["reveil"])
        self.assertEqual(2, len(rapport["defauts"]))
        self.assertIn("/health injoignable : ", rapport["defauts"][0])
        self.assertIn("nom de domaine introuvable", rapport["defauts"][0])
        self.assertIn("au second appel", rapport["defauts"][1])
        # La mesure doit rester sérialisable en une ligne de journal.
        ligne = json.dumps(rapport, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("\n", ligne)

    def test_un_delai_depasse_est_capture_comme_une_panne(self):
        with mock.patch.object(
            sonde.urllib.request, "urlopen", side_effect=TimeoutError("timed out")
        ):
            rapport = sonde.sonder(BASE)
        self.assertEqual(sonde.CODE_INJOIGNABLE, rapport["health_code"])
        self.assertTrue(rapport["defauts"])

    def test_un_second_appel_qui_echoue_vite_n_est_jamais_un_reveil(self):
        """Un refus de connexion revient en quelques millisecondes.

        Sans garde sur le code du second appel, le service le plus franchement
        mort passerait pour une instance qui vient de se réveiller.
        """
        with mock.patch.object(
            sonde,
            "_mesurer",
            side_effect=[
                (200, 32.4, dict(SANTE), None),
                (sonde.CODE_INJOIGNABLE, 0.02, None, "connexion refusée"),
            ],
        ):
            rapport = sonde.sonder(BASE)
        self.assertFalse(rapport["reveil"])
        self.assertIsNone(rapport["reveil_s"])
        self.assertTrue(any("injoignable" in d for d in rapport["defauts"]))

    def test_un_echec_au_second_appel_est_signale_a_part(self):
        # Le premier appel réussit, le second non : sans lui, une instance qui
        # meurt juste après son réveil passerait pour un simple réveil.
        with mock.patch.object(
            sonde,
            "_mesurer",
            side_effect=[(200, 32.4, dict(SANTE), None), (503, 0.10, None, None)],
        ):
            rapport = sonde.sonder(BASE)
        self.assertIn("/health répond 503 au second appel", rapport["defauts"])

    def test_la_charge_du_second_appel_est_celle_qui_fait_foi(self):
        premier = (200, 32.4, {"version": "0.7.0", "auth": "oauth"}, None)
        second = (200, 0.20, {"version": "0.7.0", "auth": "disabled"}, None)
        with mock.patch.object(sonde, "_mesurer", side_effect=[premier, second]):
            rapport = sonde.sonder(BASE)
        self.assertEqual("disabled", rapport["auth"])
        self.assertTrue(
            any("au second appel" in d and "disabled" in d for d in rapport["defauts"])
        )

    def test_une_premiere_charge_transitoire_ne_cree_pas_de_faux_defaut(self):
        premier = (200, 32.4, None, None)
        second = (200, 0.20, dict(SANTE), None)
        with mock.patch.object(sonde, "_mesurer", side_effect=[premier, second]):
            rapport = sonde.sonder(BASE)
        self.assertEqual([], rapport["defauts"])
        self.assertEqual("oauth", rapport["auth"])

    def test_une_charge_chaude_incomplete_est_un_defaut(self):
        premier = (200, 0.2, dict(SANTE), None)
        second = (200, 0.2, None, None)
        with mock.patch.object(sonde, "_mesurer", side_effect=[premier, second]):
            rapport = sonde.sonder(BASE)
        self.assertTrue(any("version absente" in d for d in rapport["defauts"]))
        self.assertTrue(
            any("authentification au second appel" in d for d in rapport["defauts"])
        )


class ResumeTests(unittest.TestCase):
    def _serie(self):
        return [
            # Format d'avant le 2 septembre : pas de champ « reveil ».
            {
                "horodatage": "2026-09-02T01:05:26Z",
                "health_latence_s": 32.464,
                "defauts": ["latence de 32.5 s : service indisponible en pratique"],
            },
            # Format courant : réveil qualifié, service sain à chaud.
            {
                "horodatage": "2026-09-02T18:00:00Z",
                "health_latence_s": 32.381,
                "health_latence_chaud_s": 0.21,
                "reveil": True,
                "reveil_s": 32.381,
                "defauts": [],
            },
            {
                "horodatage": "2026-09-02T18:10:00Z",
                "health_latence_s": 0.19,
                "health_latence_chaud_s": 0.12,
                "reveil": False,
                "reveil_s": None,
                "defauts": [],
            },
        ]

    def test_la_latence_retenue_est_celle_a_chaud(self):
        texte, _ = resume.resumer(self._serie(), None)
        # Sans cette correction, la médiane serait tirée par les réveils et
        # décrirait le sommeil de l'instance, pas la santé du service.
        self.assertIn("Latence `/health` à chaud (2 mesures)", texte)
        self.assertIn("max 0.21 s", texte)
        self.assertIn("Indisponibilités à chaud (> 30 s) : 0", texte)

    def test_une_mesure_ancienne_et_lente_n_est_pas_comptee_deux_fois(self):
        """Un réveil d'avant le 2 septembre n'a pas de latence à chaud connue.

        La compter comme telle la ferait figurer à la fois en réveil et en
        indisponibilité, et gonflerait le p95 du sommeil de l'instance.
        """
        ancienne = self._serie()[0]
        texte, bloquantes = resume.resumer([ancienne], None)
        self.assertIn("Réveils d'instance : 1", texte)
        self.assertNotIn("Latence `/health` à chaud", texte)
        self.assertIn("| — | 1 | 32.5 |", texte)
        # L'ancien faux défaut de latence est requalifié, sans double comptage.
        self.assertNotIn("service indisponible en pratique", texte)
        self.assertEqual(1, bloquantes)

    def test_les_reveils_sont_comptes_et_leur_gravite_dite(self):
        texte, _ = resume.resumer(self._serie(), None)
        self.assertIn("Réveils d'instance : 2", texte)
        self.assertIn("2 au-delà de 30 s", texte)

    def test_un_reveil_grave_bloque_le_verdict_meme_sans_defaut(self):
        # Critère de publication : aucun défaut *et* aucun réveil au-delà du
        # seuil. Un réveil de trente secondes suffit à faire conclure à un
        # relecteur que le service ne fonctionne pas.
        propre_sauf_reveil = [self._serie()[1], self._serie()[2]]
        _, bloquantes = resume.resumer(propre_sauf_reveil, None)
        self.assertEqual(1, bloquantes)

    def test_une_mesure_sans_reponse_ne_compte_pas_comme_latence(self):
        """Un appel qui n'aboutit pas mesure la vitesse d'un refus.

        L'inclure ferait baisser la médiane pendant une panne, c'est-à-dire
        exactement quand elle doit monter.
        """
        panne = {
            "horodatage": "2026-09-02T19:00:00Z",
            "health_code": 0,
            "health_latence_s": 0.02,
            "health_code_chaud": 0,
            "health_latence_chaud_s": 0.02,
            "reveil": False,
            "defauts": ["/health injoignable : connexion refusée"],
        }
        self.assertIsNone(resume._latence_chaud(panne))
        texte, bloquantes = resume.resumer([panne, self._serie()[2]], None)
        self.assertIn("Latence `/health` à chaud (1 mesures)", texte)
        self.assertIn("médiane 0.12 s", texte)
        self.assertEqual(1, bloquantes)

    def test_une_serie_saine_ne_bloque_rien(self):
        texte, bloquantes = resume.resumer([self._serie()[2]], None)
        self.assertEqual(0, bloquantes)
        self.assertIn("Réveils d'instance : aucun", texte)

    def test_une_derive_du_p95_a_chaud_bloque_le_verdict(self):
        serie = [
            {
                "horodatage": "2026-09-02T18:00:00Z",
                "health_latence_s": 0.2,
                "health_latence_chaud_s": 10.0,
                "reveil": False,
                "defauts": [],
            }
        ]
        texte, bloquantes = resume.resumer(serie, None)
        self.assertEqual(1, bloquantes)
        self.assertIn("Dérive bloquante", texte)

    def test_requalification_ancienne_conserve_les_autres_defauts(self):
        ancienne = self._serie()[0]
        ancienne["defauts"].append("métadonnées OAuth invalides")
        texte, bloquantes = resume.resumer([ancienne], None)
        self.assertIn("métadonnées OAuth invalides", texte)
        self.assertNotIn("service indisponible en pratique", texte)
        self.assertEqual(2, bloquantes)

    def test_une_fenetre_vide_ne_peut_pas_valider_sept_jours(self):
        texte, bloquantes = resume.resumer([], 7)
        self.assertEqual(1, bloquantes)
        self.assertIn("Couverture insuffisante", texte)

    def test_une_mesure_unique_ne_peut_pas_valider_sept_jours(self):
        maintenant = dt.datetime.now(dt.timezone.utc)
        mesure = {
            "horodatage": maintenant.isoformat(),
            "health_latence_s": 0.2,
            "health_latence_chaud_s": 0.1,
            "reveil": False,
            "defauts": [],
        }
        texte, bloquantes = resume.resumer([mesure], 7)
        self.assertEqual(1, bloquantes)
        self.assertIn("début de fenêtre trop récent", texte)

    def test_une_fenetre_complete_et_sans_trou_peut_passer(self):
        maintenant = dt.datetime.now(dt.timezone.utc)
        mesures = []
        for heures in range(7 * 24 - 1, -1, -1):
            mesures.append(
                {
                    "horodatage": (maintenant - dt.timedelta(hours=heures)).isoformat(),
                    "health_latence_s": 0.2,
                    "health_latence_chaud_s": 0.1,
                    "reveil": False,
                    "defauts": [],
                }
            )
        texte, bloquantes = resume.resumer(mesures, 7)
        self.assertEqual(0, bloquantes)
        self.assertIn("Couverture : complète", texte)

    def test_le_tableau_par_jour_porte_le_pire_reveil(self):
        texte, _ = resume.resumer(self._serie(), None)
        self.assertIn("| Jour | Mesures | Défauts | p95 à chaud (s) | Réveils | Réveil max (s) |", texte)
        self.assertIn("| 2026-09-02 | 3 | 0 | 0.21 | 2 | 32.5 |", texte)


if __name__ == "__main__":
    unittest.main()
