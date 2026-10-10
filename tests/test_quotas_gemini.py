"""Les relevés privés ne sont ni une authentification ni une autorisation."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from bench import campaign, quotas_gemini

NOW = dt.datetime(2026, 10, 10, 12, tzinfo=dt.timezone.utc)


class QuotasGeminiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.local = Path(self.tmp.name) / "runs"
        self.local.mkdir()
        self.patch = mock.patch.object(quotas_gemini, "LOCAL", self.local)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.path = self.local / "releve.json"
        self.piece = self.local / "capture.txt"
        self.piece.write_text("PIECE SYNTHETIQUE DE TEST, AUCUN QUOTA REEL", encoding="utf-8")
        self.data = json.loads(quotas_gemini.EXEMPLE.read_text(encoding="utf-8"))
        self.data.update(projet_ref="projet-synthetique", cle_projet_confirmee=True,
                         modele="gemini-3.5-flash", observe_le=NOW.isoformat(),
                         autres_limites_verifiees=True,
                         preuve={"fichier": "capture.txt", "sha256": hashlib.sha256(self.piece.read_bytes()).hexdigest()},
                         limites={"rpm": 4, "tpm_entree": 500, "rpd": 12})

    def verifier(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        return quotas_gemini.verifier(self.path, maintenant=NOW)

    def test_initialisation_incomplete_et_sans_ecrasement(self):
        quotas_gemini.initialiser(self.path)
        avant = self.path.read_bytes()
        result = quotas_gemini.verifier(self.path, maintenant=NOW)
        self.assertTrue(result["problemes_releve"])
        self.assertFalse(result["collecte_autorisee"])
        with self.assertRaisesRegex(ValueError, "exist"):
            quotas_gemini.initialiser(self.path)
        self.assertEqual(avant, self.path.read_bytes())

    def test_releve_coherent_ne_promet_pas_auth_ou_collecte(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "cle-test-privee"}, clear=True):
            result = self.verifier()
        self.assertEqual([], result["problemes_releve"])
        self.assertTrue(result["cle_chargee_environnement"])
        self.assertFalse(result["collecte_autorisee"])
        sortie = json.dumps(result)
        for private in ("projet-synthetique", "cle-test-privee", "capture.txt"):
            self.assertNotIn(private, sortie)

    def test_quotas_absents_nuls_booleens_et_decimaux_bloquent(self):
        for dimension in ("rpm", "tpm_entree", "rpd"):
            for invalide in (None, 0, -1, True, 1.5, "250"):
                with self.subTest(dimension=dimension, value=invalide):
                    self.data["limites"] = {"rpm": 4, "tpm_entree": 500, "rpd": 12}
                    self.data["limites"][dimension] = invalide
                    self.assertTrue(self.verifier()["problemes_releve"])

    def test_date_future_ancienne_ou_sans_fuseau_bloque(self):
        for when in (NOW + dt.timedelta(seconds=1), NOW - dt.timedelta(hours=25), NOW.replace(tzinfo=None)):
            with self.subTest(when=when):
                self.data["observe_le"] = when.isoformat()
                self.assertTrue(self.verifier()["problemes_releve"])

    def test_preuve_modifiee_ou_hors_etat_local_bloque(self):
        self.piece.write_text("MODIFIEE", encoding="utf-8")
        self.assertTrue(self.verifier()["problemes_releve"])
        outside = self.local.parent / "hors-etat.txt"
        outside.write_text("TEST", encoding="utf-8")
        self.data["preuve"] = {"fichier": "../hors-etat.txt", "sha256": hashlib.sha256(outside.read_bytes()).hexdigest()}
        self.assertTrue(self.verifier()["problemes_releve"])

    def test_releve_prive_hors_runs_refuse(self):
        with self.assertRaisesRegex(ValueError, "hors du dépôt public"):
            quotas_gemini.initialiser(self.local.parent / "public.json")
        with self.assertRaises(ValueError):
            quotas_gemini.verifier(self.local.parent / "public.json")

    def test_mauvais_niveau_alias_ou_quota_supplementaire_bloque(self):
        for champ, valeur in (("niveau", "paid"), ("cle_projet_confirmee", False),
                              ("modele", "auto"), ("modele", "gemini-3.5-flash-latest"),
                              ("modele", "gemini-3.1-pro"), ("autres_limites", [{"tpd": 1000}])):
            with self.subTest(champ=champ, valeur=valeur):
                ancien = self.data[champ]
                self.data[champ] = valeur
                self.assertTrue(self.verifier()["problemes_releve"])
                self.data[champ] = ancien

    def test_json_et_champs_supplementaires_ne_divulguent_pas_secret(self):
        self.path.write_text('{"GEMINI_API_KEY":"secret-test"', encoding="utf-8")
        with self.assertRaises(ValueError) as error:
            quotas_gemini.verifier(self.path, maintenant=NOW)
        self.assertNotIn("secret-test", str(error.exception))
        self.data["GEMINI_API_KEY"] = "secret-test"
        with self.assertRaises(ValueError) as error:
            self.verifier()
        self.assertNotIn("secret-test", str(error.exception))

    def test_gel_gratuit_arrete_avant_cli_ou_catalogue(self):
        config = campaign.read_json(ROOT / "tests/campaign/config.example.json")
        config["familles"][2]["auth"] = "cle_api_gratuite"
        path = self.local / "config.json"
        campaign.write_json(path, config)
        with mock.patch.object(campaign, "version_cli") as version:
            with self.assertRaisesRegex(ValueError, "par requête non qualifiés"):
                campaign.figer(path, self.local / "gel.json")
            version.assert_not_called()
        self.assertFalse((self.local / "gel.json").exists())


if __name__ == "__main__":
    unittest.main()
