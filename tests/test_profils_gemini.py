"""Isolation des profils, quotas partagés et confidentialité du registre."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import profils_gemini, quotas_gemini

NOW = dt.datetime(2026, 10, 10, 12, tzinfo=dt.timezone.utc)


class ProfilsGeminiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        patch = mock.patch.object(quotas_gemini, "LOCAL", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.path = self.root / "profils.json"
        self.registry = json.loads(profils_gemini.EXEMPLE.read_text(encoding="utf-8"))
        self.records = []
        for i, row in enumerate(self.registry["profils"]):
            record_path = self.root / row["releve"]
            record_path.parent.mkdir()
            piece = record_path.parent / "preuve.txt"
            piece.write_text("QUOTAS SYNTHETIQUES HORS RESEAU", encoding="utf-8")
            record = json.loads(quotas_gemini.EXEMPLE.read_text(encoding="utf-8"))
            record.update(projet_ref=f"projet-prive-{i}", cle_projet_confirmee=True,
                          modele="gemini-3.8-flash", observe_le=NOW.isoformat(),
                          autres_limites_verifiees=True, limites={"rpm": 3, "tpm_entree": 500, "rpd": 10},
                          preuve={"fichier": "preuve.txt", "sha256": hashlib.sha256(piece.read_bytes()).hexdigest()})
            self.records.append(record)
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")
        for row, record in zip(self.registry["profils"], self.records):
            (self.root / row["releve"]).write_text(json.dumps(record), encoding="utf-8")

    def check(self, profil=None):
        return profils_gemini.verifier(self.path, profil, maintenant=NOW)

    def test_selection_explicite_sans_rotation_ni_divulgation(self):
        with mock.patch.dict("os.environ", {"GEMINI_API_KEY": "secret-un",
                                             "GEMINI_API_KEY_COMPTE_2": "secret-deux"}, clear=True):
            result = self.check("profil-02")
        self.assertEqual("profils_declares_coherents", result["statut"])
        self.assertTrue(result["selection_explicitement_coherente"])
        self.assertFalse(result["collecte_autorisee"])
        self.assertFalse(result["rotation_automatique"])
        self.assertEqual(100, result["limite_globale_reponses_jour_UTC"])
        self.assertEqual(2, result["groupes_quota_declares"])
        self.assertTrue(all(r["cle_disponible"] for r in result["profils"]))
        for private in ("secret-un", "secret-deux", "projet-prive", str(self.root), "GEMINI_API_KEY"):
            self.assertNotIn(private, json.dumps(result))

    def test_meme_projet_ne_cree_pas_un_quota_par_cle(self):
        self.records[1]["projet_ref"] = self.records[0]["projet_ref"]
        self.save()
        result = self.check()
        self.assertEqual(1, result["groupes_quota_declares"])
        self.assertEqual(result["profils"][0]["groupe_quota_declare"],
                         result["profils"][1]["groupe_quota_declare"])
        self.assertIsNone(result["profil_selectionne"])
        self.assertFalse(result["selection_explicitement_coherente"])

    def test_quotas_contradictoires_du_meme_projet_bloquent(self):
        self.records[1]["projet_ref"] = self.records[0]["projet_ref"]
        self.records[1]["limites"]["rpm"] = 9
        self.save()
        result = self.check("profil-01")
        self.assertTrue(result["problemes_registre"])
        self.assertFalse(result["selection_explicitement_coherente"])

    def test_modele_different_exige_des_series_distinctes(self):
        self.records[1]["modele"] = "gemini-3.5-flash"
        self.save()
        self.assertTrue(self.check()["problemes_registre"])

    def test_doublons_profil_et_variable_refuses(self):
        for field in ("profil", "cle_env"):
            with self.subTest(field=field):
                original = self.registry["profils"][1][field]
                self.registry["profils"][1][field] = self.registry["profils"][0][field]
                self.path.write_text(json.dumps(self.registry), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.check()
                self.registry["profils"][1][field] = original

    def test_secret_en_clair_refuse_sans_echo(self):
        self.registry["profils"][0]["cle"] = "secret-interdit"
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")
        with self.assertRaises(ValueError) as error:
            self.check()
        self.assertNotIn("secret-interdit", str(error.exception))

    def test_profil_absent_et_releve_hors_etat_refuses(self):
        with self.assertRaises(ValueError):
            self.check("profil-99")
        self.registry["profils"][0]["releve"] = "../hors-etat.json"
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.check()

    def test_releve_manquant_ne_selectionne_pas_un_autre_profil(self):
        (self.root / self.registry["profils"][0]["releve"]).unlink()
        result = self.check("profil-01")
        self.assertEqual("profil-01", result["profil_selectionne"])
        self.assertFalse(result["selection_explicitement_coherente"])
        self.assertTrue(result["profils"][1]["releve_coherent"])

    def test_initialisation_necrase_pas_un_registre(self):
        target = self.root / "nouveau.json"
        profils_gemini.initialiser(target)
        before = target.read_bytes()
        with self.assertRaises(ValueError) as error:
            profils_gemini.initialiser(target)
        self.assertNotIn(str(target), str(error.exception))
        self.assertEqual(before, target.read_bytes())


if __name__ == "__main__":
    unittest.main()
