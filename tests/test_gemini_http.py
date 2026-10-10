"""Contrat REST et mesure tokenizer ; aucun réseau réel dans ces tests."""
from __future__ import annotations

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import gemini_http, mesure_tokens_gemini


class GeminiHttpTests(unittest.TestCase):
    def test_count_requete_complete_un_post_sans_secret_dans_url(self):
        opener = mock.Mock()
        opener.open.return_value = io.BytesIO(b'{"totalTokens": 123}')
        request = {"systemInstruction": {"parts": [{"text": "méthode"}]},
                   "contents": [{"role": "user", "parts": [{"text": "question"}]}]}
        with mock.patch.object(gemini_http.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(123, gemini_http.compter("secret-test", "gemini-3.8-flash", request))
        opener.open.assert_called_once()
        http = opener.open.call_args.args[0]
        self.assertTrue(http.full_url.endswith("gemini-3.8-flash:countTokens"))
        self.assertNotIn("secret-test", http.full_url)
        self.assertEqual("secret-test", http.get_header("X-goog-api-key"))
        body = json.loads(http.data)
        self.assertNotIn("contents", body)
        self.assertEqual("models/gemini-3.8-flash", body["generateContentRequest"]["model"])
        self.assertEqual(request["systemInstruction"], body["generateContentRequest"]["systemInstruction"])

    def test_modeles_alias_et_methodes_inconnues_sans_reseau(self):
        with mock.patch.object(gemini_http.urllib.request, "build_opener") as build:
            for model in ("auto", "gemini-flash-latest", "gemini-3.8-flash/../../evil", "gemini-3.1-pro"):
                with self.assertRaises(ValueError):
                    gemini_http.appeler("secret-test", model, "countTokens", {})
            with self.assertRaises(ValueError):
                gemini_http.appeler("secret-test", "gemini-3.8-flash", "autre", {})
            build.assert_not_called()

    def test_429_arret_immediat_sans_corps_ni_retry(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError("https://exemple.invalid", 429,
                                                         "secret-test", {}, io.BytesIO(b'secret-test'))
        with mock.patch.object(gemini_http.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(gemini_http.ErreurGemini) as error:
                gemini_http.compter("secret-test", "gemini-3.8-flash", {})
        self.assertEqual(429, error.exception.statut)
        self.assertNotIn("secret-test", str(error.exception))
        opener.open.assert_called_once()

    def test_secret_dans_charge_ou_reponse_refuse(self):
        with mock.patch.object(gemini_http.urllib.request, "build_opener") as build:
            with self.assertRaises(ValueError):
                gemini_http.appeler("secret-test", "gemini-3.8-flash", "countTokens", {"text": "secret-test"})
            build.assert_not_called()
        opener = mock.Mock()
        opener.open.return_value = io.BytesIO(b'{"text": "secret-test"}')
        with mock.patch.object(gemini_http.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(gemini_http.ErreurGemini):
                gemini_http.appeler("secret-test", "gemini-3.8-flash", "countTokens", {})

    def test_compteur_invalide_refuse(self):
        for value in (None, True, 0, "10", -1):
            with mock.patch.object(gemini_http, "appeler", return_value={"totalTokens": value}):
                with self.assertRaises(gemini_http.ErreurGemini):
                    gemini_http.compter("secret-test", "gemini-3.8-flash", {})

    def test_mesure_publique_deterministe_aucun_corrige_envoye(self):
        before = mesure_tokens_gemini.preparer()
        self.assertEqual(before, mesure_tokens_gemini.preparer())
        with mock.patch.object(gemini_http, "compter", return_value=321) as count:
            result = mesure_tokens_gemini.mesurer("secret-test")
        count.assert_called_once()
        self.assertEqual(321, result["tokens_entree"])
        self.assertEqual(0, result["generations"])
        self.assertFalse(result["collecte_autorisee"])
        self.assertFalse(result["outils_inclus"])
        self.assertNotIn("gold", before[0])
        for forbidden in ("secret-test", "valide_par", "conclusion_attendue"):
            self.assertNotIn(forbidden, json.dumps(before[0]))


if __name__ == "__main__":
    unittest.main()
