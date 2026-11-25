#!/usr/bin/env python3
"""Mode ``account`` : clés PISTE de chaque utilisateur, chiffrées dans Auth0.

Auth0 (API Management) et PISTE sont simulés ; aucun appel réseau.
"""

from __future__ import annotations

import base64
import json
import re
import sys
import time
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import droit_francais.legifrance as legifrance_client  # noqa: E402
from droit_francais.errors import LegifranceError  # noqa: E402
from mcp_server.credential_store import (  # noqa: E402
    CredentialStore,
    CredentialStoreError,
    decode_master_key,
)
from mcp_server.runtime import RuntimeConfigurationError, RuntimeSettings  # noqa: E402
from test_oauth_end_to_end import OAUTH_ENV, OAuthServerCase  # noqa: E402

CLE = base64.b64encode(bytes(range(32))).decode()
AUTRE_CLE = base64.b64encode(bytes(range(1, 33))).decode()


class FauxAuth0:
    """API Management minimale : jeton M2M, lecture et PATCH d'app_metadata."""

    def __init__(self) -> None:
        self.metadata: dict[str, dict] = {}
        self.calls: list[str] = []

    def __call__(self, method, url, headers, body):
        self.calls.append(method)
        if url.endswith("/oauth/token"):
            return {"access_token": "jeton-gestion", "expires_in": 86400}
        assert headers["Authorization"] == "Bearer jeton-gestion"
        subject = urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[1])
        meta = self.metadata.setdefault(subject, {})
        if method == "PATCH":
            for key, value in json.loads(body)["app_metadata"].items():
                if value is None:
                    meta.pop(key, None)
                else:
                    meta[key] = value
            return {}
        return {"app_metadata": dict(meta)}


def _store(http=None, cle=CLE, clock=time.monotonic) -> CredentialStore:
    return CredentialStore("tenant.eu.auth0.com", "m2m-id", "m2m-secret",
                           decode_master_key(cle), http=http or FauxAuth0(), clock=clock)


def _jeton_par_identifiant(_url, payload, _headers):
    form = urllib.parse.parse_qs(payload.decode("utf-8"))
    return {"access_token": f"jeton-{form['client_id'][0]}", "expires_in": 3600}


class ChiffrementTests(unittest.TestCase):
    def test_aller_retour(self):
        store = _store()
        blob = store.encrypt("auth0|a", "identifiant-a", "secret-a-123")
        self.assertNotIn("secret-a-123", blob)
        self.assertEqual(("identifiant-a", "secret-a-123"), store.decrypt("auth0|a", blob))

    def test_blob_d_un_autre_sujet_mauvaise_cle_ou_altere_refuses(self):
        store = _store()
        blob = store.encrypt("auth0|a", "identifiant-a", "secret-a-123")
        altere = blob[:-2] + ("A" if blob[-2] != "A" else "B") + blob[-1]
        for sujet, valeur, coffre in (("auth0|b", blob, store),
                                      ("auth0|a", altere, store),
                                      ("auth0|a", blob, _store(cle=AUTRE_CLE))):
            with self.assertRaises(CredentialStoreError):
                coffre.decrypt(sujet, valeur)

    def test_cle_maitresse_standard_ou_url_meme_valeur_sans_avertissement(self):
        import warnings

        brut = bytes([0xFB, 0xFF] * 16)  # base64 riche en « + » et « / »
        standard = base64.b64encode(brut).decode()
        self.assertTrue("+" in standard and "/" in standard)
        url = base64.urlsafe_b64encode(brut).decode()
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # un FutureWarning ferait échouer le test
            for variante in (standard, url, url.rstrip("="), f'"{standard}"', standard + "\n"):
                self.assertEqual(brut, decode_master_key(variante), variante)

    def test_cle_maitresse_invalide(self):
        for brute in ("", "court", base64.b64encode(b"x" * 31).decode(),
                      base64.b64encode(bytes(32)).decode()[:-2] + "!="):
            with self.assertRaises(ValueError):
                decode_master_key(brute)
        self.assertEqual(32, len(decode_master_key(CLE)))


class LienTests(unittest.TestCase):
    def test_usage_unique(self):
        store = _store()
        jeton = store.issue_link_token("auth0|a")
        self.assertEqual("auth0|a", store.read_link_token(jeton, consume=False))
        self.assertEqual("auth0|a", store.read_link_token(jeton, consume=True))
        self.assertIsNone(store.read_link_token(jeton, consume=False))

    def test_falsifie_ou_signe_par_une_autre_cle(self):
        jeton = _store().issue_link_token("auth0|a")
        corps, _, signature = jeton.partition(".")
        faux_corps = base64.urlsafe_b64encode(
            json.dumps({"sub": "auth0|b", "exp": 9_999_999_999, "n": "x"}).encode()
        ).decode().rstrip("=")
        store = _store()
        self.assertIsNone(store.read_link_token(f"{faux_corps}.{signature}", consume=False))
        self.assertIsNone(_store(cle=AUTRE_CLE).read_link_token(jeton, consume=False))
        self.assertIsNone(store.read_link_token("", consume=False))
        self.assertIsNone(store.read_link_token(corps, consume=False))

    def test_expire(self):
        store = _store()
        jeton = store.issue_link_token("auth0|a")
        with mock.patch("mcp_server.credential_store.time.time", return_value=time.time() + 601):
            self.assertIsNone(store.read_link_token(jeton, consume=False))


class CoffreTests(unittest.TestCase):
    def test_enregistrer_relire_supprimer(self):
        auth0 = FauxAuth0()
        store = _store(auth0)
        self.assertIsNone(store.load("auth0|a"))
        store.save("auth0|a", "identifiant-a", "secret-a-123")
        self.assertTrue(auth0.metadata["auth0|a"]["piste"].startswith("v1."))
        self.assertNotIn("secret-a-123", json.dumps(auth0.metadata))
        self.assertEqual(("identifiant-a", "secret-a-123"), _store(auth0).load("auth0|a"))
        store.delete("auth0|a")
        self.assertNotIn("piste", auth0.metadata["auth0|a"])
        self.assertIsNone(store.load("auth0|a"))

    def test_cache_evite_un_second_appel(self):
        auth0 = FauxAuth0()
        store = _store(auth0)
        store.load("auth0|a")
        store.load("auth0|a")
        self.assertEqual(["POST", "GET"], auth0.calls)


class ConfigurationTests(unittest.TestCase):
    BASE = dict(OAUTH_ENV, MCP_ENV="production", MCP_PISTE_CREDENTIALS="account",
                AUTH0_MGMT_CLIENT_ID="m2m", AUTH0_MGMT_CLIENT_SECRET="m2m-secret",
                MCP_CREDENTIALS_KEY=CLE)

    def test_account_exige_oauth(self):
        with self.assertRaises(RuntimeConfigurationError):
            RuntimeSettings.from_env(dict(self.BASE, MCP_AUTH_MODE="disabled"))

    def test_production_valide(self):
        settings = RuntimeSettings.from_env(self.BASE)
        self.assertTrue(settings.caller_credentials and settings.account_credentials)
        settings.validate_public(self.BASE)

    def test_production_refusee(self):
        for env in (dict(self.BASE, AUTH0_MGMT_CLIENT_SECRET=""),
                    dict(self.BASE, MCP_CREDENTIALS_KEY="court"),
                    dict(self.BASE, LEGIFRANCE_CLIENT_ID="operateur")):
            with self.assertRaises(RuntimeConfigurationError):
                RuntimeSettings.from_env(env).validate_public(env)


class CompteHttpTests(OAuthServerCase):
    """Chaîne réelle : OAuth, outil, page /compte, coffre simulé."""

    extra_env = {"MCP_PISTE_CREDENTIALS": "account", "MCP_CREDENTIALS_KEY": CLE,
                 "AUTH0_MGMT_CLIENT_ID": "m2m", "AUTH0_MGMT_CLIENT_SECRET": "m2m-secret"}

    def setUp(self):
        from mcp_server import server as mcp_app

        self.app = mcp_app
        self.auth0 = FauxAuth0()
        store = mcp_app.CREDENTIAL_STORE
        store._http = self.auth0
        store._cache.clear()
        store._used_links.clear()
        legifrance_client.clear_token_cache()
        self.addCleanup(legifrance_client.clear_token_cache)

    def texte(self, resultat) -> str:
        return " ".join(getattr(c, "text", "") for c in resultat.content)

    def _outil_qui_lit_le_jeton(self):
        def search_articles(*_args, **_kwargs):
            return {"jeton": legifrance_client.get_token()}

        return mock.patch.object(self.app.legal_tools, "search_articles", search_articles)

    def http(self, method, path, **kwargs):
        import asyncio

        async def run():
            async with self._running(None) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(run())

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_chaque_sujet_utilise_ses_propres_cles(self, _post):
        self.app.CREDENTIAL_STORE.save("auth0|a", "identifiant-a", "secret-a-123")
        with self._outil_qui_lit_le_jeton():
            ok = self.call_tool(self.token(sub="auth0|a"), "search_articles", {"number": "L1"})
            sans = self.call_tool(self.token(sub="auth0|b"), "search_articles", {"number": "L1"})
        self.assertFalse(self.en_erreur(ok), self.texte(ok))
        self.assertIn("jeton-identifiant-a", self.texte(ok))
        self.assertTrue(self.en_erreur(sans))
        self.assertIn("configurer_cles_piste", self.texte(sans))
        self.assertNotIn("identifiant-a", self.texte(sans))

    def _lien(self, sub="auth0|c") -> str:
        resultat = self.call_tool(self.token(sub=sub), "configurer_cles_piste", {})
        self.assertFalse(self.en_erreur(resultat), self.texte(resultat))
        lien = re.search(r"https://exemple\.test/compte\?t=([A-Za-z0-9_.\-]+)", self.texte(resultat))
        self.assertIsNotNone(lien, self.texte(resultat))
        return lien.group(1)

    @mock.patch("droit_francais.legifrance.http_post_json", side_effect=_jeton_par_identifiant)
    def test_parcours_de_saisie_puis_rejeu_refuse(self, _post):
        jeton = self._lien()
        page = self.http("GET", f"/compte?t={jeton}")
        self.assertEqual(200, page.status_code)
        self.assertEqual("no-store", page.headers["cache-control"])
        self.assertIn("auth0|…c", page.text)
        form = {"t": jeton, "client_id": "identifiant-c", "client_secret": "secret-c-123"}
        envoi = self.http("POST", "/compte", data=form)
        self.assertEqual(200, envoi.status_code, envoi.text)
        self.assertNotIn("secret-c-123", envoi.text)
        self.assertEqual(("identifiant-c", "secret-c-123"), _store(self.auth0).load("auth0|c"))
        self.assertEqual(400, self.http("POST", "/compte", data=form).status_code)
        self.assertEqual(400, self.http("GET", f"/compte?t={jeton}").status_code)

    def test_cles_refusees_par_piste_non_enregistrees_lien_reutilisable(self):
        jeton = self._lien()
        refus = LegifranceError("Authentification PISTE échouée", 3, 400)
        form = {"t": jeton, "client_id": "identifiant-c", "client_secret": "faux-secret-1"}
        with mock.patch("droit_francais.legifrance.http_post_json", side_effect=refus):
            envoi = self.http("POST", "/compte", data=form)
        self.assertEqual(400, envoi.status_code)
        self.assertNotIn("piste", self.auth0.metadata.get("auth0|c", {}))
        self.assertEqual(200, self.http("GET", f"/compte?t={jeton}").status_code)

    def test_oublier_supprime_les_cles(self):
        self.app.CREDENTIAL_STORE.save("auth0|a", "identifiant-a", "secret-a-123")
        resultat = self.call_tool(self.token(sub="auth0|a"), "oublier_cles_piste", {})
        self.assertFalse(self.en_erreur(resultat), self.texte(resultat))
        self.assertNotIn("piste", self.auth0.metadata["auth0|a"])


if __name__ == "__main__":
    unittest.main()
