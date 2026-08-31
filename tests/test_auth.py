#!/usr/bin/env python3
"""Tests hors réseau de l'authentification OAuth du serveur MCP public."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

import jwt  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from mcp_server.auth import (  # noqa: E402
    JwksTokenVerifier,
    LegalAccessToken,
    _normalise_scopes,
    principal_of,
)
from mcp_server.runtime import (  # noqa: E402
    PrincipalRateLimiter,
    RuntimeCapacityError,
    RuntimeConfigurationError,
    RuntimeSettings,
)

ISSUER = "https://exemple-idp.eu.auth0.com"
RESOURCE = "https://droit-francais-skill.onrender.com/mcp"

BASE_ENV = {
    "MCP_ENV": "production",
    "MCP_AUTH_MODE": "oauth",
    "MCP_PUBLIC_URL": "https://droit-francais-skill.onrender.com",
    "MCP_OAUTH_ISSUER": ISSUER,
}

PISTE_ENV = {
    "LEGIFRANCE_CLIENT_ID": "identifiant",
    "LEGIFRANCE_CLIENT_SECRET": "secret",
    "JUDILIBRE_KEY_ID": "cle",
}


class AuthSettingsTests(unittest.TestCase):
    def test_oauth_mode_derives_resource_jwks_and_audience(self):
        settings = RuntimeSettings.from_env(BASE_ENV)
        self.assertTrue(settings.auth_enabled)
        self.assertEqual(settings.resource_url, RESOURCE)
        self.assertEqual(settings.oauth_audience, RESOURCE)
        self.assertEqual(settings.oauth_jwks_url, f"{ISSUER}/.well-known/jwks.json")
        self.assertEqual(settings.oauth_required_scopes, ("legal:read",))

    def test_trailing_slash_never_produces_a_double_separator(self):
        env = dict(BASE_ENV, MCP_PUBLIC_URL="https://droit-francais-skill.onrender.com/")
        self.assertEqual(RuntimeSettings.from_env(env).resource_url, RESOURCE)

    def test_scopes_accept_commas_and_spaces(self):
        for raw in ("legal:read, legal:search", "legal:read legal:search"):
            env = dict(BASE_ENV, MCP_OAUTH_REQUIRED_SCOPES=raw)
            self.assertEqual(
                RuntimeSettings.from_env(env).oauth_required_scopes,
                ("legal:read", "legal:search"),
            )

    def test_scope_gate_can_be_disabled_explicitly(self):
        for raw in ("-", "none", "AUCUNE"):
            env = dict(BASE_ENV, MCP_OAUTH_REQUIRED_SCOPES=raw)
            settings = RuntimeSettings.from_env(env)
            self.assertEqual(settings.oauth_required_scopes, ())
            # L'authentification reste exigée : seul le contrôle de portée tombe.
            self.assertTrue(settings.auth_enabled)

    def test_absent_scope_variable_keeps_the_default(self):
        self.assertEqual(
            RuntimeSettings.from_env(BASE_ENV).oauth_required_scopes, ("legal:read",)
        )

    def test_plaintext_issuer_is_refused(self):
        env = dict(BASE_ENV, MCP_OAUTH_ISSUER="http://exemple-idp.local")
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env(env)

    def test_oauth_mode_requires_a_public_url(self):
        env = {key: value for key, value in BASE_ENV.items() if key != "MCP_PUBLIC_URL"}
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env(env)

    def test_production_refuses_an_anonymous_public_gateway(self):
        env = dict(BASE_ENV, MCP_AUTH_MODE="disabled")
        settings = RuntimeSettings.from_env(env)
        with self.assertRaises(RuntimeConfigurationError) as raised:
            settings.validate_public(dict(env, **PISTE_ENV))
        self.assertIn("MCP_AUTH_MODE", str(raised.exception))

    def test_production_accepts_a_complete_oauth_configuration(self):
        settings = RuntimeSettings.from_env(BASE_ENV)
        settings.validate_public(dict(BASE_ENV, **PISTE_ENV))

    def test_local_stdio_usage_stays_unauthenticated(self):
        settings = RuntimeSettings.from_env({"MCP_ENV": "development"})
        self.assertFalse(settings.auth_enabled)
        self.assertEqual(settings.resource_url, "")


class IssuerCanonicalisationTests(unittest.TestCase):
    """L'émetteur publié doit être celui du document de découverte, à la lettre.

    OpenAI rapproche textuellement l'``issuer`` annoncé par le serveur
    d'autorisation et celui que publient les métadonnées RFC 9728 du serveur
    MCP. Aucune normalisation n'est appliquée de leur côté : une barre oblique
    finale ajoutée ou retirée suffit à faire échouer le connecteur.
    """

    AVEC_BARRE = "https://exemple-idp.eu.auth0.com/"
    SANS_BARRE = "https://exemple-idp.eu.auth0.com"

    def test_trailing_slash_is_preserved(self):
        env = dict(BASE_ENV, MCP_OAUTH_ISSUER=self.AVEC_BARRE)
        self.assertEqual(RuntimeSettings.from_env(env).oauth_issuer, self.AVEC_BARRE)

    def test_absent_trailing_slash_is_never_invented(self):
        # L'exploitant recopie ce que publie son émetteur : Auth0 écrit la
        # barre, Google ne l'écrit pas. Normaliser dans un sens ou dans l'autre
        # casserait l'un des deux.
        env = dict(BASE_ENV, MCP_OAUTH_ISSUER=self.SANS_BARRE)
        self.assertEqual(RuntimeSettings.from_env(env).oauth_issuer, self.SANS_BARRE)

    def test_base_form_never_carries_a_trailing_slash(self):
        for raw in (self.AVEC_BARRE, self.SANS_BARRE):
            env = dict(BASE_ENV, MCP_OAUTH_ISSUER=raw)
            self.assertEqual(
                RuntimeSettings.from_env(env).oauth_issuer_base, self.SANS_BARRE
            )

    def test_derived_jwks_url_never_doubles_the_separator(self):
        for raw in (self.AVEC_BARRE, self.SANS_BARRE):
            env = dict(BASE_ENV, MCP_OAUTH_ISSUER=raw)
            jwks = RuntimeSettings.from_env(env).oauth_jwks_url
            self.assertEqual(jwks, f"{self.SANS_BARRE}/.well-known/jwks.json")
            self.assertNotIn("//.well-known", jwks)

    def test_explicit_jwks_url_still_wins(self):
        env = dict(
            BASE_ENV,
            MCP_OAUTH_ISSUER=self.AVEC_BARRE,
            MCP_OAUTH_JWKS_URL="https://exemple-idp.eu.auth0.com/cles.json",
        )
        self.assertEqual(
            RuntimeSettings.from_env(env).oauth_jwks_url,
            "https://exemple-idp.eu.auth0.com/cles.json",
        )

    def test_whitespace_only_issuer_is_still_refused(self):
        env = dict(BASE_ENV, MCP_OAUTH_ISSUER="   ")
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env(env)

    def test_public_url_keeps_its_trailing_slash_stripped(self):
        # La troncature reste indispensable là où l'URL sert de préfixe.
        env = dict(
            BASE_ENV,
            MCP_PUBLIC_URL="https://droit-francais-skill.onrender.com/",
            MCP_OAUTH_ISSUER=self.AVEC_BARRE,
        )
        self.assertEqual(RuntimeSettings.from_env(env).resource_url, RESOURCE)

    @staticmethod
    def _root_route_issuer(settings) -> str:
        """Émetteur réellement servi par la route racine de ``server.py``."""
        from mcp_server import server as mcp_app

        with mock.patch.object(mcp_app, "SETTINGS", settings):
            response = asyncio.run(mcp_app.protected_resource_root(mock.Mock()))
        return json.loads(response.body)["authorization_servers"][0]

    @staticmethod
    def _sdk_route_issuer(settings) -> str:
        """Émetteur réellement servi par la route « /mcp » du SDK.

        Reproduit la construction de ``create_protected_resource_routes`` : le
        SDK instancie ``ProtectedResourceMetadata`` à partir de
        ``AuthSettings.issuer_url``, puis sérialise le modèle tel quel.
        """
        from mcp.server.auth.settings import AuthSettings
        from mcp.shared.auth import ProtectedResourceMetadata

        auth = AuthSettings(
            issuer_url=settings.oauth_issuer,
            resource_server_url=settings.resource_url,
            required_scopes=list(settings.oauth_required_scopes),
        )
        metadata = ProtectedResourceMetadata(
            resource=auth.resource_server_url,
            authorization_servers=[auth.issuer_url],
            scopes_supported=auth.required_scopes,
        )
        payload = metadata.model_dump(by_alias=True, mode="json", exclude_none=True)
        return payload["authorization_servers"][0]

    def test_root_route_publishes_the_issuer_verbatim(self):
        for raw in (self.AVEC_BARRE, self.SANS_BARRE):
            with self.subTest(issuer=raw):
                settings = RuntimeSettings.from_env(dict(BASE_ENV, MCP_OAUTH_ISSUER=raw))
                self.assertEqual(self._root_route_issuer(settings), raw)

    def test_sdk_route_publishes_the_issuer_verbatim(self):
        # Garde-fou de version : le SDK MCP 2.x préserve la chaîne configurée
        # (« url_preserve_empty_path »), là où le 1.x laissait pydantic ajouter
        # une barre finale. Un échec ici signale un SDK non conforme à
        # requirements-mcp.txt, donc une métadonnée que ChatGPT refusera.
        for raw in (self.AVEC_BARRE, self.SANS_BARRE):
            with self.subTest(issuer=raw):
                settings = RuntimeSettings.from_env(dict(BASE_ENV, MCP_OAUTH_ISSUER=raw))
                self.assertEqual(
                    self._sdk_route_issuer(settings),
                    raw,
                    "le SDK MCP installé ne préserve pas l'émetteur configuré ; "
                    "vérifier la version épinglée dans requirements-mcp.txt",
                )

    def test_both_metadata_routes_publish_the_same_string(self):
        """C'est l'égalité des deux routes qui débloque le connecteur ChatGPT."""
        for raw in (self.AVEC_BARRE, self.SANS_BARRE):
            with self.subTest(issuer=raw):
                settings = RuntimeSettings.from_env(dict(BASE_ENV, MCP_OAUTH_ISSUER=raw))
                self.assertEqual(
                    self._root_route_issuer(settings), self._sdk_route_issuer(settings)
                )


class PrincipalRateLimiterTests(unittest.TestCase):
    def test_quota_is_counted_per_principal(self):
        limiter = PrincipalRateLimiter(calls_per_minute=2)
        limiter.check("utilisateur-a")
        limiter.check("utilisateur-a")
        with self.assertRaises(RuntimeCapacityError):
            limiter.check("utilisateur-a")
        # Un second utilisateur dispose de son propre quota.
        limiter.check("utilisateur-b")

    def test_window_expiry_frees_the_quota_and_purges_the_bucket(self):
        limiter = PrincipalRateLimiter(calls_per_minute=1, window_seconds=0.05)
        limiter.check("utilisateur-a")
        time.sleep(0.06)
        limiter.check("utilisateur-a")
        self.assertEqual(limiter.tracked_principals, 1)


def _sign(payload: dict[str, object], key) -> str:
    return jwt.encode(payload, key, algorithm="RS256")


class JwksTokenVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def _verifier(self) -> JwksTokenVerifier:
        with mock.patch("mcp_server.auth.PyJWKClient"):
            verifier = JwksTokenVerifier(
                issuer=ISSUER, jwks_url=f"{ISSUER}/jwks", audience=RESOURCE
            )
        signing_key = mock.Mock()
        signing_key.key = self.key.public_key()
        verifier._jwks_client.get_signing_key_from_jwt.return_value = signing_key
        return verifier

    def _verify(self, token: str):
        return asyncio.run(self._verifier().verify_token(token))

    def _payload(self, **overrides) -> dict[str, object]:
        now = int(time.time())
        payload = {
            "iss": ISSUER,
            "aud": RESOURCE,
            "sub": "auth0|utilisateur-1",
            "azp": "application-chatgpt",
            "scope": "legal:read",
            "iat": now,
            "exp": now + 300,
        }
        payload.update(overrides)
        return payload

    def test_valid_token_yields_subject_scopes_and_resource(self):
        access = self._verify(_sign(self._payload(), self.key))
        self.assertIsInstance(access, LegalAccessToken)
        self.assertEqual(access.subject, "auth0|utilisateur-1")
        self.assertEqual(access.client_id, "application-chatgpt")
        self.assertEqual(access.scopes, ["legal:read"])
        self.assertEqual(access.resource, RESOURCE)
        self.assertEqual(principal_of(access), "auth0|utilisateur-1")

    def test_token_issued_for_another_api_is_refused(self):
        token = _sign(self._payload(aud="https://une-autre-api.example"), self.key)
        self.assertIsNone(self._verify(token))

    def test_trailing_slash_in_issuer_is_accepted(self):
        # Auth0 écrit « iss » avec une barre oblique finale absente des réglages.
        token = _sign(self._payload(iss=f"{ISSUER}/"), self.key)
        access = self._verify(token)
        self.assertIsNotNone(access)
        self.assertEqual(access.subject, "auth0|utilisateur-1")

    def test_token_from_another_issuer_is_refused(self):
        token = _sign(self._payload(iss="https://idp-pirate.example"), self.key)
        self.assertIsNone(self._verify(token))

    def test_expired_token_is_refused(self):
        now = int(time.time())
        token = _sign(self._payload(iat=now - 7200, exp=now - 3600), self.key)
        self.assertIsNone(self._verify(token))

    def test_token_without_subject_is_refused(self):
        payload = self._payload()
        del payload["sub"]
        self.assertIsNone(self._verify(_sign(payload, self.key)))

    def test_token_signed_by_an_unknown_key_is_refused(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.assertIsNone(self._verify(_sign(self._payload(), other)))

    def test_symmetric_algorithm_is_never_accepted(self):
        token = jwt.encode(self._payload(), "secret-partage", algorithm="HS256")
        self.assertIsNone(self._verify(token))

    def test_missing_token_gives_the_anonymous_principal(self):
        self.assertEqual(principal_of(None), "anonyme")


class DatingTests(unittest.TestCase):
    """La date qui sert de référence doit être explicite dans la réponse."""

    def setUp(self):
        from droit_francais.tools import _dating

        self._dating = _dating

    def test_no_date_uses_the_server_clock(self):
        info = self._dating(None)
        self.assertEqual(info["as_of_date"], dt.date.today().isoformat())
        self.assertEqual(info["date_basis"], "date du jour du serveur")
        self.assertIsNone(info["requested_date"])
        self.assertNotIn("caveat", info)

    def test_past_date_supplied_by_the_caller_is_flagged(self):
        passee = (dt.date.today() - dt.timedelta(days=120)).isoformat()
        info = self._dating(passee)
        self.assertEqual(info["as_of_date"], passee)
        self.assertEqual(info["date_basis"], "date fournie par l'appelant")
        self.assertIn("Version applicable au", info["caveat"])
        self.assertIn("sans paramètre de date", info["caveat"])

    def test_future_date_is_flagged_too(self):
        future = (dt.date.today() + dt.timedelta(days=30)).isoformat()
        self.assertIn("postérieure", self._dating(future)["caveat"])

    def test_today_supplied_explicitly_carries_no_caveat(self):
        info = self._dating(dt.date.today().isoformat())
        self.assertNotIn("caveat", info)


class ScopeNormalisationTests(unittest.TestCase):
    def test_every_common_dialect_is_understood(self):
        self.assertEqual(_normalise_scopes({"scope": "a b"}), ["a", "b"])
        self.assertEqual(_normalise_scopes({"scp": ["a", "b"]}), ["a", "b"])
        self.assertEqual(_normalise_scopes({"permissions": ["a"]}), ["a"])
        self.assertEqual(_normalise_scopes({}), [])


if __name__ == "__main__":
    unittest.main()
