#!/usr/bin/env python3
"""Tests unitaires hors réseau des fondations de l'outillage API."""

from __future__ import annotations

import argparse
import io
import os
import sys
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import legifrance as cli  # noqa: E402
import droit_francais.judilibre as judilibre_client  # noqa: E402
import droit_francais.legifrance as legifrance_client  # noqa: E402
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


PISTE_ENV = {
    "LEGIFRANCE_CLIENT_ID": "client-id",
    "LEGIFRANCE_CLIENT_SECRET": "client-secret",
}


class LegifranceClientTests(unittest.TestCase):
    def setUp(self):
        legifrance_client.clear_token_cache()

    def test_missing_credentials_trigger_web_fallback_code(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(LegifranceError) as caught:
                legifrance_client.get_token()
        self.assertEqual(2, caught.exception.exit_code)

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_oauth_token_uses_configured_credentials(self, http_post_json):
        http_post_json.return_value = {"access_token": "oauth-token"}
        env = {
            "LEGIFRANCE_CLIENT_ID": "client-id",
            "LEGIFRANCE_CLIENT_SECRET": "client-secret",
            "LEGIFRANCE_ENV": "sandbox",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            token = legifrance_client.get_token()

        self.assertEqual("oauth-token", token)
        url, payload, headers = http_post_json.call_args.args
        self.assertIn("sandbox-oauth.piste.gouv.fr", url)
        parsed = urllib.parse.parse_qs(payload.decode("utf-8"))
        self.assertEqual(["client-id"], parsed["client_id"])
        self.assertEqual(["client-secret"], parsed["client_secret"])
        self.assertEqual("application/x-www-form-urlencoded", headers["Content-Type"])

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_oauth_transport_failure_is_authentication_error(self, http_post_json):
        http_post_json.side_effect = LegifranceError("denied", exit_code=4)
        env = {
            "LEGIFRANCE_CLIENT_ID": "client-id",
            "LEGIFRANCE_CLIENT_SECRET": "client-secret",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(LegifranceError) as caught:
                legifrance_client.get_token()
        self.assertEqual(3, caught.exception.exit_code)

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_api_call_builds_bearer_json_request(self, http_post_json):
        http_post_json.return_value = {"ok": True}
        with mock.patch.dict(os.environ, {"LEGIFRANCE_ENV": "prod"}, clear=True):
            result = legifrance_client.api_call("/search", {"fond": "CODE_DATE"}, "token")
        self.assertTrue(result["ok"])
        url, payload, headers = http_post_json.call_args.args
        self.assertTrue(url.endswith("/search"))
        self.assertEqual(b'{"fond": "CODE_DATE"}', payload)
        self.assertEqual("Bearer token", headers["Authorization"])

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_token_is_reused_until_it_nears_expiry(self, http_post_json):
        # Un jeton par opération ajoutait une requête d'authentification à
        # chaque appel, et une panne passagère du serveur PISTE cassait une
        # session dont le jeton était encore valide.
        http_post_json.return_value = {"access_token": "t1", "expires_in": 3600}
        with mock.patch.dict(os.environ, PISTE_ENV, clear=True):
            self.assertEqual("t1", legifrance_client.get_token())
            self.assertEqual("t1", legifrance_client.get_token())
        http_post_json.assert_called_once()

    @mock.patch("droit_francais.legifrance.time.monotonic")
    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_token_is_requested_again_after_expiry(self, http_post_json, monotonic):
        http_post_json.side_effect = [
            {"access_token": "t1", "expires_in": 120},
            {"access_token": "t2", "expires_in": 120},
        ]
        margin = legifrance_client.TOKEN_SAFETY_MARGIN_SECONDS
        with mock.patch.dict(os.environ, PISTE_ENV, clear=True):
            monotonic.return_value = 1000.0
            self.assertEqual("t1", legifrance_client.get_token())
            # Juste avant la marge de sécurité : toujours servi depuis le cache.
            monotonic.return_value = 1000.0 + 120 - margin - 1
            self.assertEqual("t1", legifrance_client.get_token())
            # La marge atteinte : renouvelé avant le terme réel du jeton.
            monotonic.return_value = 1000.0 + 120 - margin
            self.assertEqual("t2", legifrance_client.get_token())
        self.assertEqual(2, http_post_json.call_count)

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_short_or_missing_lifetime_is_handled_conservatively(self, http_post_json):
        # Une durée inférieure à la marge n'est pas mise en cache du tout ;
        # une durée absente reçoit une valeur par défaut, courte.
        http_post_json.side_effect = [
            {"access_token": "court", "expires_in": 30},
            {"access_token": "court-bis", "expires_in": 30},
            {"access_token": "sans-duree"},
        ]
        with mock.patch.dict(os.environ, PISTE_ENV, clear=True):
            self.assertEqual("court", legifrance_client.get_token())
            self.assertEqual("court-bis", legifrance_client.get_token())
            self.assertEqual("sans-duree", legifrance_client.get_token())
            self.assertEqual("sans-duree", legifrance_client.get_token())
        self.assertEqual(3, http_post_json.call_count)

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_api_call_renews_the_token_exactly_once_on_401(self, http_post_json):
        http_post_json.side_effect = [
            LegifranceError("expired", exit_code=4, http_status=401),
            {"access_token": "frais", "expires_in": 3600},
            {"ok": True},
        ]
        with mock.patch.dict(os.environ, {**PISTE_ENV, "LEGIFRANCE_ENV": "prod"}, clear=True):
            result = legifrance_client.api_call("/search", {}, "perime")
        self.assertTrue(result["ok"])
        self.assertEqual(3, http_post_json.call_count)
        # 1. appel API avec le jeton périmé ; 2. renouvellement ; 3. rejeu.
        self.assertEqual(
            "Bearer perime", http_post_json.call_args_list[0].args[2]["Authorization"]
        )
        self.assertIn("oauth.piste.gouv.fr", http_post_json.call_args_list[1].args[0])
        self.assertEqual(
            "Bearer frais", http_post_json.call_args_list[2].args[2]["Authorization"]
        )
        # Le jeton renouvelé remplace l'ancien dans le cache.
        self.assertEqual("frais", legifrance_client.get_token())
        self.assertEqual(3, http_post_json.call_count)

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_a_fresh_token_refused_is_not_retried_again(self, http_post_json):
        http_post_json.side_effect = [
            LegifranceError("expired", exit_code=4, http_status=401),
            {"access_token": "frais", "expires_in": 3600},
            LegifranceError("still refused", exit_code=4, http_status=401),
        ]
        with mock.patch.dict(os.environ, {**PISTE_ENV, "LEGIFRANCE_ENV": "prod"}, clear=True):
            with self.assertRaises(LegifranceError) as caught:
                legifrance_client.api_call("/search", {}, "perime")
        self.assertEqual(401, caught.exception.http_status)
        self.assertEqual(3, http_post_json.call_count)

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_other_http_errors_do_not_touch_the_token(self, http_post_json):
        http_post_json.side_effect = LegifranceError("nope", exit_code=4, http_status=403)
        with mock.patch.dict(os.environ, {**PISTE_ENV, "LEGIFRANCE_ENV": "prod"}, clear=True):
            with self.assertRaises(LegifranceError):
                legifrance_client.api_call("/search", {}, "token")
        http_post_json.assert_called_once()


class JudilibreClientTests(unittest.TestCase):
    def setUp(self):
        judilibre_client.clear_token_cache()

    @mock.patch("droit_francais.legifrance.http_post_json")
    def test_judilibre_shares_the_legifrance_token_cache(self, http_post_json):
        # Un seul émetteur, un seul jeton : le cache est commun aux deux
        # clients, et le nom historique reste utilisable.
        http_post_json.return_value = {"access_token": "partage", "expires_in": 3600}
        with mock.patch.dict(os.environ, PISTE_ENV, clear=True):
            self.assertEqual("partage", legifrance_client.get_token())
            self.assertEqual("partage", judilibre_client.get_token_cached())
        http_post_json.assert_called_once()
        self.assertIs(legifrance_client._TOKEN_CACHE, judilibre_client._TOKEN_CACHE)

    @mock.patch("droit_francais.judilibre.get_token")
    @mock.patch("droit_francais.judilibre.http_get_json")
    def test_oauth_401_renews_the_token_once_then_gives_up(self, http_get_json, get_token):
        # Sans renouvellement, la voie OAuth restait cassée jusqu'au
        # redémarrage du processus une fois le jeton périmé.
        get_token.side_effect = ["perime", "frais"]
        http_get_json.side_effect = [
            LegifranceError("expired", exit_code=4, http_status=401),
            LegifranceError("still", exit_code=4, http_status=401),
        ]
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(LegifranceError) as caught:
                judilibre_client.judilibre_get("/search", {"query": "x"})
        self.assertEqual(3, caught.exception.exit_code)
        self.assertEqual(
            [mock.call(), mock.call(force_refresh=True)], get_token.call_args_list
        )
        self.assertEqual(2, http_get_json.call_count)
        self.assertEqual(
            "Bearer frais", http_get_json.call_args_list[1].args[1]["Authorization"]
        )

    @mock.patch("droit_francais.judilibre.get_token")
    @mock.patch("droit_francais.judilibre.http_get_json")
    def test_oauth_401_then_success_after_renewal(self, http_get_json, get_token):
        get_token.side_effect = ["perime", "frais"]
        http_get_json.side_effect = [
            LegifranceError("expired", exit_code=4, http_status=401),
            {"results": ["ok"]},
        ]
        with mock.patch.dict(os.environ, {}, clear=True):
            result = judilibre_client.judilibre_get("/search", {"query": "x"})
        self.assertEqual(["ok"], result["results"])
        self.assertEqual(2, get_token.call_count)

    @mock.patch("droit_francais.judilibre.get_token")
    @mock.patch("droit_francais.judilibre.http_get_json")
    def test_keyid_falls_back_to_oauth_and_repeats_list_params(
        self,
        http_get_json,
        get_token,
    ):
        http_get_json.side_effect = [
            LegifranceError("forbidden", exit_code=4, http_status=403),
            {"results": ["decision"]},
        ]
        get_token.return_value = "oauth-token"
        env = {"JUDILIBRE_KEY_ID": "key-id", "JUDILIBRE_ENV": "sandbox"}
        with mock.patch.dict(os.environ, env, clear=True):
            result = judilibre_client.judilibre_get(
                "/search",
                {"jurisdiction": ["cc", "ca"], "page_size": 10, "empty": None},
            )

        self.assertEqual(["decision"], result["results"])
        first_url, first_headers = http_get_json.call_args_list[0].args
        second_url, second_headers = http_get_json.call_args_list[1].args
        self.assertEqual(first_url, second_url)
        self.assertIn("sandbox-api.piste.gouv.fr", first_url)
        self.assertIn("jurisdiction=cc&jurisdiction=ca", first_url)
        self.assertNotIn("empty=", first_url)
        self.assertEqual("key-id", first_headers["KeyId"])
        self.assertEqual("Bearer oauth-token", second_headers["Authorization"])

    @mock.patch("droit_francais.judilibre.http_get_json")
    def test_non_authentication_error_does_not_retry(self, http_get_json):
        http_get_json.side_effect = LegifranceError(
            "server error",
            exit_code=4,
            http_status=500,
        )
        with mock.patch.dict(os.environ, {"JUDILIBRE_KEY_ID": "key-id"}, clear=True):
            with self.assertRaises(LegifranceError) as caught:
                judilibre_client.judilibre_get("/search", {})
        self.assertEqual(4, caught.exception.exit_code)
        http_get_json.assert_called_once()


class CompatibilityTests(unittest.TestCase):
    def test_cli_reuses_shared_error_type(self):
        self.assertIs(LegifranceError, cli.LegifranceError)

    def test_cli_reexports_extracted_clients(self):
        self.assertIs(legifrance_client.get_token, cli.get_token)
        self.assertIs(legifrance_client.api_call, cli.api_call)
        self.assertIs(judilibre_client.judilibre_get, cli.judilibre_get)
        self.assertIs(judilibre_client._TOKEN_CACHE, cli._TOKEN_CACHE)

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
