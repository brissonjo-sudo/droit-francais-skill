#!/usr/bin/env python3
"""Mode pont : chaque appelant transmet ses identifiants PISTE, le serveur n'en détient aucun.

Deux niveaux :

- le client PISTE, hors serveur : cache de jetons isolé par appelant, aucun
  repli sur les clés de l'exploitant ;
- la chaîne HTTP réelle du SDK MCP 2.x, jouée en processus : en-têtes lus par
  le middleware, identifiants visibles dans l'outil, refus sans en-têtes.

Aucun appel réseau : le serveur de jetons PISTE est simulé.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

import droit_francais.judilibre as judilibre_client  # noqa: E402
import droit_francais.legifrance as legifrance_client  # noqa: E402
from mcp_server.runtime import RuntimeConfigurationError, RuntimeSettings  # noqa: E402

OPERATEUR = {
    "LEGIFRANCE_CLIENT_ID": "operateur-id",
    "LEGIFRANCE_CLIENT_SECRET": "operateur-secret",
    "JUDILIBRE_KEY_ID": "operateur-keyid",
}


def _jeton_par_identifiant(_url, payload, _headers):
    """Serveur de jetons simulé : un jeton distinct par identifiant client."""
    form = urllib.parse.parse_qs(payload.decode("utf-8"))
    return {"access_token": f"jeton-{form['client_id'][0]}", "expires_in": 3600}


class ClientPisteAppelantTests(unittest.TestCase):
    def setUp(self):
        legifrance_client.clear_token_cache()

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_les_cles_de_l_appelant_priment_sur_celles_de_l_exploitant(self, post):
        with mock.patch.dict(os.environ, OPERATEUR, clear=True):
            with legifrance_client.caller_credentials("appelant-a", "secret-a"):
                self.assertEqual("jeton-appelant-a", legifrance_client.get_token())
        form = urllib.parse.parse_qs(post.call_args.args[1].decode("utf-8"))
        self.assertEqual(["appelant-a"], form["client_id"])
        self.assertEqual(["secret-a"], form["client_secret"])

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_le_cache_est_isole_par_appelant(self, post):
        with legifrance_client.caller_credentials("appelant-a", "secret-a"):
            legifrance_client.get_token()
            legifrance_client.get_token()
        with legifrance_client.caller_credentials("appelant-b", "secret-b"):
            self.assertEqual("jeton-appelant-b", legifrance_client.get_token())
        self.assertEqual(2, post.call_count)
        # Le cache de l'exploitant n'est pas touché par les appelants.
        self.assertEqual({}, legifrance_client._TOKEN_CACHE)

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_un_autre_secret_ne_reprend_pas_le_jeton_en_cache(self, post):
        with legifrance_client.caller_credentials("appelant-a", "secret-a"):
            legifrance_client.get_token()
        with legifrance_client.caller_credentials("appelant-a", "autre-secret"):
            legifrance_client.get_token()
        self.assertEqual(2, post.call_count)

    def test_hors_contexte_l_environnement_reste_la_source(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(legifrance_client.LegifranceError) as caught:
                legifrance_client.get_token()
        self.assertEqual(2, caught.exception.exit_code)
        self.assertFalse(legifrance_client.caller_credentials_active())

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_le_cache_des_appelants_est_borne(self, _post):
        with mock.patch.object(legifrance_client, "CALLER_TOKENS_MAX", 3):
            for index in range(5):
                with legifrance_client.caller_credentials(f"appelant-{index}", "secret"):
                    legifrance_client.get_token()
            self.assertEqual(3, len(legifrance_client._CALLER_TOKENS))
        for key in legifrance_client._CALLER_TOKENS:
            self.assertNotIn("appelant", key)

    def test_judilibre_n_utilise_jamais_la_keyid_de_l_exploitant(self):
        with mock.patch.dict(os.environ, OPERATEUR, clear=True):
            self.assertEqual("KeyId", judilibre_client.auth_modes()[0][0])
            with legifrance_client.caller_credentials("appelant-a", "secret-a"):
                self.assertEqual([("OAuth", None)], judilibre_client.auth_modes())


class ConfigurationPontTests(unittest.TestCase):
    BASE = {"MCP_ENV": "production", "MCP_PISTE_CREDENTIALS": "caller"}

    def test_mode_inconnu_refuse(self):
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env({"MCP_PISTE_CREDENTIALS": "les-deux"})

    def test_pont_en_production_sans_cle_ni_oauth_est_accepte(self):
        RuntimeSettings.from_env(self.BASE).validate_public(self.BASE)

    def test_pont_refuse_toute_cle_d_exploitant(self):
        env = dict(self.BASE, JUDILIBRE_KEY_ID="operateur-keyid")
        with self.assertRaises(RuntimeConfigurationError) as caught:
            RuntimeSettings.from_env(env).validate_public(env)
        self.assertIn("JUDILIBRE_KEY_ID", str(caught.exception))
        self.assertNotIn("operateur-keyid", str(caught.exception))

    def test_pont_refuse_le_sandbox_en_production(self):
        env = dict(self.BASE, LEGIFRANCE_ENV="sandbox")
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env(env).validate_public(env)

    def test_mode_serveur_inchange(self):
        env = {"MCP_ENV": "production"}
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env(env).validate_public(env)


try:
    import httpx2  # noqa: F401
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from mcp.server.transport_security import TransportSecuritySettings
    from mcp.server import MCPServer  # noqa: F401  — SDK 2.x seulement
except ImportError:  # SDK 1.x ou transport absent : le mode pont exige le 2.x
    httpx2 = None

TRANSPORT_HOST = "127.0.0.1:8000"
TRANSPORT_URL = f"http://{TRANSPORT_HOST}"


@unittest.skipIf(httpx2 is None, "SDK MCP 2.x et httpx2 requis")
class PontHttpTests(unittest.TestCase):
    """Chaîne réelle : ASGI du SDK, middleware, transport, dispatch d'outil."""

    @classmethod
    def setUpClass(cls):
        from mcp_server import server as mcp_app

        cls.app_module = mcp_app
        cls._env = mock.patch.dict(
            os.environ,
            {"MCP_ENV": "test", "MCP_AUTH_MODE": "disabled", "MCP_PISTE_CREDENTIALS": "caller",
             "MCP_USER_CALLS_PER_MINUTE": "2"},
        )
        cls._env.start()
        for name in OPERATEUR:
            os.environ.pop(name, None)
        importlib.reload(mcp_app)
        assert mcp_app.SETTINGS.caller_credentials

    @classmethod
    def tearDownClass(cls):
        cls._env.stop()
        importlib.reload(cls.app_module)

    def setUp(self):
        legifrance_client.clear_token_cache()

    def call(self, headers: dict, name: str = "search_articles"):
        app_module = self.app_module
        security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[TRANSPORT_HOST],
            allowed_origins=[TRANSPORT_URL],
        )

        async def run():
            app = app_module.server.streamable_http_app(transport_security=security)
            async with app.router.lifespan_context(app):
                async with httpx2.AsyncClient(
                    transport=httpx2.ASGITransport(app=app),
                    base_url=TRANSPORT_URL,
                    headers=headers,
                    timeout=30,
                ) as client:
                    async with streamable_http_client(
                        f"{TRANSPORT_URL}/mcp", http_client=client
                    ) as (reader, writer, *_):
                        async with ClientSession(reader, writer) as session:
                            await session.initialize()
                            return await session.call_tool(name, {"number": "L2212-2"})

        return asyncio.run(run())

    @staticmethod
    def texte(resultat) -> str:
        return " ".join(getattr(part, "text", "") for part in resultat.content)

    @staticmethod
    def en_erreur(resultat) -> bool:
        return bool(getattr(resultat, "is_error", None) or getattr(resultat, "isError", None))

    def _outil_qui_lit_le_jeton(self):
        def search_articles(*_args, **_kwargs):
            return {"jeton": legifrance_client.get_token()}

        return mock.patch.object(self.app_module.legal_tools, "search_articles", search_articles)

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_l_outil_utilise_les_identifiants_de_la_requete(self, _post):
        headers = {"X-Piste-Client-Id": "appelant-http-a", "X-Piste-Client-Secret": "secret-http-a"}
        with self._outil_qui_lit_le_jeton():
            resultat = self.call(headers)
        self.assertFalse(self.en_erreur(resultat), self.texte(resultat))
        self.assertIn("jeton-appelant-http-a", self.texte(resultat))

    def test_sans_en_tetes_l_appel_est_refuse(self):
        with self._outil_qui_lit_le_jeton():
            resultat = self.call({})
        self.assertTrue(self.en_erreur(resultat))
        self.assertIn("Identifiants PISTE absents", self.texte(resultat))

    def test_en_tete_mal_forme_refuse_sans_le_recopier(self):
        headers = {"X-Piste-Client-Id": "appelant-http-b", "X-Piste-Client-Secret": "court"}
        with self._outil_qui_lit_le_jeton():
            resultat = self.call(headers)
        self.assertTrue(self.en_erreur(resultat))
        self.assertNotIn("court", self.texte(resultat).replace("mal formés", ""))

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_le_quota_individuel_suit_l_application_piste(self, _post):
        a = {"X-Piste-Client-Id": "appelant-quota-a", "X-Piste-Client-Secret": "secret-quota-a"}
        b = {"X-Piste-Client-Id": "appelant-quota-b", "X-Piste-Client-Secret": "secret-quota-b"}
        with self._outil_qui_lit_le_jeton():
            self.assertFalse(self.en_erreur(self.call(a)))
            self.assertFalse(self.en_erreur(self.call(a)))
            self.assertTrue(self.en_erreur(self.call(a)))
            self.assertFalse(self.en_erreur(self.call(b)))
            # L'identifiant de A avec un autre secret n'hérite pas du quota épuisé de A.
            usurpe = dict(a, **{"X-Piste-Client-Secret": "faux-secret-quota"})
            self.assertFalse(self.en_erreur(self.call(usurpe)))


if __name__ == "__main__":
    unittest.main()
