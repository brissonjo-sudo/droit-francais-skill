#!/usr/bin/env python3
"""Tests unitaires hors réseau des fondations de l'outillage API."""

from __future__ import annotations

import argparse
import io
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import legifrance as cli  # noqa: E402
from droit_francais.config import (  # noqa: E402
    judilibre_base,
    legifrance_environment,
    load_dotenv,
)
from droit_francais.errors import LegifranceError  # noqa: E402
from droit_francais.transport import http_get_json, http_post_json  # noqa: E402


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self.body


class ConfigTests(unittest.TestCase):
    def test_default_and_sandbox_environments(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIn("api.piste.gouv.fr", legifrance_environment()["api"])
            os.environ["LEGIFRANCE_ENV"] = "sandbox"
            self.assertIn("sandbox-api.piste.gouv.fr", legifrance_environment()["api"])
            self.assertIn("sandbox-api.piste.gouv.fr", judilibre_base())

    def test_judilibre_can_override_legifrance_environment(self):
        with mock.patch.dict(
            os.environ,
            {"LEGIFRANCE_ENV": "prod", "JUDILIBRE_ENV": "sandbox"},
            clear=True,
        ):
            self.assertIn("sandbox-api.piste.gouv.fr", judilibre_base())

    def test_invalid_environment_keeps_historical_exit_code(self):
        with mock.patch.dict(os.environ, {"LEGIFRANCE_ENV": "local"}, clear=True):
            with self.assertRaises(LegifranceError) as caught:
                legifrance_environment()
        self.assertEqual(2, caught.exception.exit_code)

    def test_dotenv_order_and_exported_value_precedence(self):
        explicit = ROOT / "tests" / "fixtures" / "sample.env"
        env = {
            "LEGIFRANCE_DOTENV": str(explicit),
            "DROIT_TEST_EXPORTED": "environment",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            load_dotenv(script_dir=ROOT / "tests" / "fixtures")
            self.assertEqual("explicit", os.environ["DROIT_TEST_VALUE"])
            self.assertEqual("environment", os.environ["DROIT_TEST_EXPORTED"])


class TransportTests(unittest.TestCase):
    @mock.patch("droit_francais.transport.urllib.request.urlopen")
    def test_post_decodes_json_and_forwards_timeout(self, urlopen):
        urlopen.return_value = FakeResponse(b'{"access_token": "token"}')
        result = http_post_json(
            "https://example.test/token",
            b"grant_type=client_credentials",
            {"Content-Type": "application/x-www-form-urlencoded"},
            timeout=7,
        )
        self.assertEqual("token", result["access_token"])
        request = urlopen.call_args.args[0]
        self.assertEqual("POST", request.get_method())
        self.assertEqual(7, urlopen.call_args.kwargs["timeout"])

    @mock.patch("droit_francais.transport.urllib.request.urlopen")
    def test_get_maps_404_to_not_found(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.test/decision",
            404,
            "Not Found",
            {},
            io.BytesIO(b"missing"),
        )
        with self.assertRaises(LegifranceError) as caught:
            http_get_json("https://example.test/decision", {})
        self.assertEqual(5, caught.exception.exit_code)
        self.assertEqual(404, caught.exception.http_status)

    @mock.patch("droit_francais.transport.urllib.request.urlopen")
    def test_post_keeps_http_failures_as_api_errors(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.test/search",
            404,
            "Not Found",
            {},
            io.BytesIO(b"missing"),
        )
        with self.assertRaises(LegifranceError) as caught:
            http_post_json("https://example.test/search", b"{}", {})
        self.assertEqual(4, caught.exception.exit_code)

    @mock.patch("droit_francais.transport.urllib.request.urlopen")
    def test_invalid_json_is_an_api_error(self, urlopen):
        urlopen.return_value = FakeResponse(b"not-json")
        with self.assertRaises(LegifranceError) as caught:
            http_get_json("https://example.test/data", {})
        self.assertEqual(4, caught.exception.exit_code)


class CompatibilityTests(unittest.TestCase):
    def test_cli_reuses_shared_error_type(self):
        self.assertIs(LegifranceError, cli.LegifranceError)

    def test_all_historical_commands_remain_exposed(self):
        commands = set()
        for action in cli.build_parser()._actions:
            if isinstance(action, argparse._SubParsersAction):
                commands.update(action.choices)
        self.assertEqual(
            {"ping", "article", "search", "ceta", "constit", "juri", "decision", "taxonomy"},
            commands,
        )


if __name__ == "__main__":
    unittest.main()
