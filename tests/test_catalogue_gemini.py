"""Sonde catalogue : secret confiné, appel unique et absence de génération."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import contextlib
import unittest
import urllib.error
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import catalogue_gemini


class CatalogueGeminiTests(unittest.TestCase):
    def test_appel_unique_cle_en_entete_et_sortie_assainie(self):
        data = {"models": [{"name": "models/gemini-3.5-flash", "inputTokenLimit": 100,
                            "outputTokenLimit": 50, "description": "secret-test",
                            "supportedGenerationMethods": ["generateContent"]},
                           {"name": "models/autre-123", "description": "secret-test"}]}
        opener = mock.Mock()
        opener.open.return_value = io.BytesIO(json.dumps(data).encode())
        with mock.patch.object(catalogue_gemini.urllib.request, "build_opener", return_value=opener):
            result = catalogue_gemini.lire("secret-test", mock.MagicMock())
        opener.open.assert_called_once()
        req = opener.open.call_args.args[0]
        self.assertEqual("GET", req.method)
        self.assertEqual(catalogue_gemini.ENDPOINT, req.full_url)
        self.assertNotIn("secret-test", req.full_url)
        self.assertEqual("secret-test", req.get_header("X-goog-api-key"))
        self.assertNotIn("secret-test", json.dumps(result))
        self.assertEqual(0, result["generations"])
        self.assertFalse(result["quotas_actifs_et_projet_attestes"])
        self.assertFalse(result["collecte_autorisee"])
        self.assertEqual(1, len(result["modeles"]))

    def test_pagination_ne_declenche_aucun_second_appel(self):
        opener = mock.Mock()
        opener.open.return_value = io.BytesIO(b'{"models": [], "nextPageToken": "suite"}')
        with mock.patch.object(catalogue_gemini.urllib.request, "build_opener", return_value=opener):
            result = catalogue_gemini.lire("secret-test", mock.MagicMock())
        opener.open.assert_called_once()
        self.assertFalse(result["catalogue_complet"])

    def test_cle_absente_ne_fait_aucun_appel(self):
        with mock.patch.object(catalogue_gemini.urllib.request, "build_opener") as build:
            with self.assertRaises(ValueError):
                catalogue_gemini.lire("", mock.MagicMock())
            build.assert_not_called()

    def test_redirection_ne_transmet_pas_le_secret(self):
        req = catalogue_gemini.urllib.request.Request(catalogue_gemini.ENDPOINT)
        with self.assertRaises(urllib.error.HTTPError):
            catalogue_gemini.SansRedirection().redirect_request(req, None, 302, "", {}, "https://ailleurs.invalid")

    def test_erreur_http_sans_retry_ni_message_sensible(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(catalogue_gemini.ENDPOINT, 403,
                                                        "secret-test", {}, None)
        with mock.patch.object(catalogue_gemini.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(urllib.error.HTTPError):
                catalogue_gemini.lire("secret-test", mock.MagicMock())
        opener.open.assert_called_once()

    def test_cli_erreur_ne_journalise_pas_la_cle(self):
        with tempfile.TemporaryDirectory() as dossier:
            erreur = urllib.error.HTTPError(catalogue_gemini.ENDPOINT, 403, "secret-test", {}, None)
            messages = io.StringIO()
            with (mock.patch.object(catalogue_gemini, "LOCAL", Path(dossier)),
                  mock.patch.object(catalogue_gemini, "lire", side_effect=erreur),
                  mock.patch("bench.gemini_rest.preparer_client"),
                  contextlib.redirect_stderr(messages)):
                code = catalogue_gemini.main(["--sortie", str(Path(dossier) / "catalogue.json"), "--registre", "registre.json",
                                                "--profil", "profil-01", "--budget-state", dossier])
            self.assertEqual(2, code)
            self.assertIn("403", messages.getvalue())
            self.assertNotIn("secret-test", messages.getvalue())
            self.assertFalse((Path(dossier) / "catalogue.json").exists())


if __name__ == "__main__":
    unittest.main()
