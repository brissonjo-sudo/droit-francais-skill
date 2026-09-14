#!/usr/bin/env python3
"""Tests hors réseau de l'authentification OAuth du serveur MCP public."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from typing import Callable
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

import jwt  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from mcp_server.auth import (  # noqa: E402
    JWKS_CACHE_LIFESPAN_SECONDS,
    JWKS_CACHE_LIFESPAN_SECONDS_MAX,
    JWKS_FORCED_REFRESH_INTERVAL_SECONDS,
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


#: Identifiant de clé par défaut : celui que le jeu de clés simulé (voir
#: ``JwksTokenVerifierTests._verifier``) sait déjà résoudre sans réseau.
KID = "clef-actuelle"

#: Second identifiant de clé, dédié aux tests de confusion de clé de
#: ``JwksTwoKeyConfusionTests`` (R2) : un JWKS réel de production porte
#: plusieurs clés, jamais une seule.
KID_B = "clef-suivante"


def _sign(payload: dict[str, object], key, *, kid: str | None = KID) -> str:
    headers = {"kid": kid} if kid else None
    return jwt.encode(payload, key, algorithm="RS256", headers=headers)


class _FrozenClock:
    """Horloge monotone injectable, avancée sur demande — ne dort jamais.

    ``test_window_expiry_frees_the_quota_and_purges_the_bucket`` ci-dessus
    dort 60 ms pour observer une expiration : fragilité connue, à ne pas
    reproduire (voir la revue qui a introduit ce commentaire). Les tests du
    bridage JWKS avancent cette horloge au lieu de dormir.
    """

    def __init__(self, start: float = 1_000_000.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def _key_stub(kid: str, private_key) -> mock.Mock:
    """Imite un ``jwt.PyJWK`` : seuls ``key_id`` et ``key`` sont lus, par le
    vrai ``PyJWKClient.match_kid`` et par ``JwksTokenVerifier._decode``."""
    return mock.Mock(key_id=kid, key=private_key.public_key())


class _FakeRotatingJwksClient:
    """Simule le cache « tier 1 » réel de ``PyJWKClient`` (``JWKSetCache``) :
    un jeu de clés « publié » par un émetteur simulé, plus un instantané mis
    en cache pendant ``lifespan`` secondes.

    Remplacer ``JwksTokenVerifier._jwks_client`` entier par ce double — au
    lieu de se contenter de patcher ``get_signing_keys`` comme le fait
    ``JwksTokenVerifierTests._verifier`` — est nécessaire dès qu'un test doit
    observer le comportement du CACHE lui-même (une révocation honorée après
    expiration, ou une ruée de threads à l'instant de cette expiration) :
    un simple ``mock.Mock(return_value=...)`` n'a ni notion de fraîcheur ni
    de compteur d'appels réseau réels, deux choses que ce double fournit :

    * ``network_calls`` ne s'incrémente que lors d'un véritable rafraîchi-
      ssement (cache absent, expiré, ou ``refresh=True``) — jamais sur un
      retour de cache encore frais ;
    * ``get_signing_keys`` n'est protégé par AUCUN verrou, à l'image du vrai
      ``JWKSetCache`` de PyJWT (voir sa source, ``jwt/jwk_set_cache.py`` :
      aucun ``threading.Lock``) — c'est précisément cette absence que le
      verrou ajouté à ``JwksTokenVerifier`` (R3) doit compenser en amont.

    Utilisé par ``test_revoked_key_is_rejected_once_the_cache_lifespan_elapses``
    (horloge figée, avancée sur demande) et par
    ``test_concurrent_cache_expiry_produces_a_single_network_call`` (horloge
    réelle, pour un vrai chevauchement de threads).
    """

    #: Déléguée à la véritable ``staticmethod`` de PyJWT : voir le
    #: commentaire de ``JwksTokenVerifierTests._verifier`` sur le choix de ne
    #: jamais simuler ``match_kid``.
    match_kid = staticmethod(jwt.PyJWKClient.match_kid)

    def __init__(
        self,
        *,
        lifespan: float,
        published: list,
        clock: Callable[[], float] = time.monotonic,
        fetch_delay_seconds: float = 0.0,
    ) -> None:
        self._lifespan = lifespan
        self._published = list(published)
        self._clock = clock
        self._fetch_delay_seconds = fetch_delay_seconds
        self._cached: list | None = None
        self._cached_at: float | None = None
        self.network_calls = 0
        #: Protège seulement l'exactitude du compteur ci-dessus — pas une
        #: substitution au verrou sous test. Sans lui, l'incrémentation
        #: elle-même (lecture-modification-écriture) pourrait perdre des
        #: mises à jour sous concurrence réelle et fausserait la mesure que
        #: le test rapporte, indépendamment de ce que fait (ou pas)
        #: ``JwksTokenVerifier``.
        self._counter_lock = threading.Lock()

    def set_published_keys(self, keys: list) -> None:
        """Simule une rotation/révocation côté émetteur : n'affecte le
        résultat de ``get_signing_keys`` qu'après expiration du cache."""
        self._published = list(keys)

    def get_signing_keys(self, refresh: bool = False) -> list:
        fresh = (
            not refresh
            and self._cached is not None
            and self._cached_at is not None
            and (self._clock() - self._cached_at) < self._lifespan
        )
        if fresh:
            return self._cached

        # Fenêtre délibérément non atomique, comme le vrai JWKSetCache : rien
        # ici n'empêche deux threads d'entrer tous les deux dans cette
        # branche avant que l'un d'eux n'ait mis le cache à jour. C'est
        # exactement l'absence de verrou que R3 démontre et compense.
        with self._counter_lock:
            self.network_calls += 1
        if self._fetch_delay_seconds:
            time.sleep(self._fetch_delay_seconds)
        self._cached = list(self._published)
        self._cached_at = self._clock()
        return self._cached


class JwksTokenVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def _verifier(self, *, clock=None) -> JwksTokenVerifier:
        """Vérificateur construit avec un vrai ``PyJWKClient``.

        Construire ``PyJWKClient`` ne fait aucun appel réseau (voir sa
        source) : seul ``get_signing_keys`` — la frontière réseau — est
        remplacé ci-dessous. ``match_kid`` reste la véritable
        ``staticmethod`` de PyJWT, non simulée : les tests exercent la même
        logique de correspondance qu'en production, pas une réimplémentation
        de complaisance dans le test.
        """
        kwargs = {"clock": clock} if clock is not None else {}
        verifier = JwksTokenVerifier(
            issuer=ISSUER, jwks_url=f"{ISSUER}/jwks", audience=RESOURCE, **kwargs
        )
        # Jeu de clés par défaut : seule KID y figure. Les tests qui veulent
        # un kid inconnu, une panne réseau ou une rotation remplacent
        # get_signing_keys explicitement après construction.
        verifier._jwks_client.get_signing_keys = mock.Mock(
            return_value=[_key_stub(KID, self.key)]
        )
        return verifier

    def _verify(self, token: str):
        return asyncio.run(self._verifier().verify_token(token))

    def _verify_with(self, verifier: JwksTokenVerifier, token: str):
        return asyncio.run(verifier.verify_token(token))

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

    def test_non_canonical_trailing_slash_in_issuer_is_refused(self):
        token = _sign(self._payload(iss=f"{ISSUER}/"), self.key)
        self.assertIsNone(self._verify(token))

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
        # kid=KID explicite : sans lui, le jeton serait déjà refusé faute de
        # kid avant même d'atteindre le contrôle d'algorithme visé ici.
        token = jwt.encode(
            self._payload(), "secret-partage", algorithm="HS256", headers={"kid": KID}
        )
        self.assertIsNone(self._verify(token))

    def test_unconfigured_asymmetric_algorithm_is_refused(self):
        token = jwt.encode(
            self._payload(), self.key, algorithm="RS384", headers={"kid": KID}
        )
        self.assertIsNone(self._verify(token))

    def test_missing_token_gives_the_anonymous_principal(self):
        self.assertEqual(principal_of(None), "anonyme")

    # ------------------------------------------------------------------
    # Bridage du rafraîchissement forcé JWKS (SEC-01 / SEC-03).
    #
    # PyJWKClient.get_signing_key(kid), quand le kid ne figure pas dans le
    # jeu de clés en cache, rappelle l'émetteur avec refresh=True — sans
    # aucune authentification préalable, puisque ce vérificateur EST le point
    # d'authentification. Les tests ci-dessous prouvent que
    # JwksTokenVerifier borne ce rappel au lieu de se contenter de le
    # documenter.

    def test_unknown_kid_is_refused(self):
        """T1 — comble TEST-02 : un kid absent du JWKS n'authentifie jamais,
        même après le rafraîchissement forcé (lui aussi sans le kid).

        Le jeu de clés simulé (celui par défaut de ``_verifier`` : une seule
        clé, KID) reste non vide : le vrai ``PyJWKClient.get_signing_keys``
        ne rend jamais une liste vide (il lève ``PyJWKClientError`` dans ce
        cas, voir sa source) — un jeu non vide mais dépourvu du kid visé est
        le cas réel face à un kid inconnu ou falsifié.
        """
        verifier = self._verifier()
        token = _sign(self._payload(), self.key, kid="kid-inconnu")
        self.assertIsNone(self._verify_with(verifier, token))

    def test_unreachable_jwks_is_reported_as_unavailable(self):
        """T2 — une panne de l'émetteur doit emprunter la branche
        ``auth_unavailable``, pas ``auth_rejected`` (qui, elle, suppose un
        émetteur joignable mais un jeton non conforme).

        ``PyJWKClientConnectionError`` est le vrai type levé par
        ``PyJWKClient.fetch_data`` en production (DNS mort, port fermé,
        délai dépassé — les trois mesurés) ; il hérite de ``PyJWTError``,
        d'où la nécessité de l'intercepter séparément et en premier dans
        ``verify_token``. Un ``OSError`` nu, lui, n'atteint jamais ce code :
        ``PyJWKClient`` l'intercepte déjà et le relève sous cette forme.
        """
        verifier = self._verifier()
        verifier._jwks_client.get_signing_keys = mock.Mock(
            side_effect=jwt.PyJWKClientConnectionError("résolution DNS impossible")
        )
        token = _sign(self._payload(), self.key, kid=KID)
        with self.assertLogs("droit_francais.mcp.auth", level="WARNING") as journal:
            access = self._verify_with(verifier, token)
        self.assertIsNone(access)
        self.assertTrue(
            any("auth_unavailable" in ligne for ligne in journal.output),
            journal.output,
        )

    def test_unknown_kid_flood_triggers_a_single_forced_refresh(self):
        """T3 — LE TEST CENTRAL : garantie anti-amplification de SEC-01.

        Sans bridage, 20 requêtes à kid inconnu déclenchent 20
        rafraîchissements forcés (un aller-retour réseau non authentifié
        chacun) ; avec, un seul. C'est mesuré ici en comptant les appels
        réels de ``get_signing_keys(refresh=True)``, pas supposé. Le jeu de
        clés simulé (par défaut de ``_verifier``) reste non vide et dépourvu
        du kid visé — voir T1 pour la raison de fidélité.
        """
        clock = _FrozenClock()
        verifier = self._verifier(clock=clock)
        token = _sign(self._payload(), self.key, kid="kid-inconnu")

        for _ in range(20):
            self.assertIsNone(self._verify_with(verifier, token))

        appels = verifier._jwks_client.get_signing_keys.call_args_list
        appels_forces = [c for c in appels if c.kwargs.get("refresh") is True]
        self.assertEqual(
            1,
            len(appels_forces),
            "le bridage doit plafonner les rafraîchissements forcés à un "
            f"seul pour 20 requêtes à kid inconnu ; observé : {len(appels_forces)}",
        )

    def test_legitimate_rotation_is_still_honoured_after_the_interval(self):
        """T4 — non-régression : passé l'intervalle de bridage, un kid
        nouvellement publié par l'émetteur est résolu et le jeton accepté.
        Le bridage retarde une rotation légitime d'au plus un intervalle ;
        il ne doit jamais l'empêcher.
        """
        clock = _FrozenClock()
        verifier = self._verifier(clock=clock)
        nouvelle_cle = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nouveau_kid = "kid-apres-rotation"
        # Le rafraîchissement forcé ne « voit » la clé tournée qu'une fois le
        # délai suivant écoulé — ce qui isole ce que le test vérifie
        # réellement : que c'est l'horloge injectée, pas l'horloge système,
        # qui gouverne le bridage.
        seuil = clock() + JWKS_FORCED_REFRESH_INTERVAL_SECONDS + 1

        def lookup(refresh: bool = False):
            if refresh and clock() >= seuil:
                return [_key_stub(nouveau_kid, nouvelle_cle)]
            # Avant la rotation, l'émetteur simulé sert toujours son jeu de
            # clés courant (KID) — jamais une liste vide : le vrai
            # PyJWKClient.get_signing_keys ne rend jamais [] (voir T1).
            return [_key_stub(KID, self.key)]

        verifier._jwks_client.get_signing_keys = mock.Mock(side_effect=lookup)
        token = _sign(self._payload(), nouvelle_cle, kid=nouveau_kid)

        # Consomme le budget de rafraîchissement forcé de cet intervalle ;
        # l'émetteur simulé ne sert pas encore la nouvelle clé.
        self.assertIsNone(self._verify_with(verifier, token))

        # Toujours dans le même intervalle : bridé sans même retourner au
        # réseau, quand bien même la clé serait déjà disponible côté
        # émetteur.
        self.assertIsNone(self._verify_with(verifier, token))

        clock.advance(JWKS_FORCED_REFRESH_INTERVAL_SECONDS + 1)
        access = self._verify_with(verifier, token)
        self.assertIsInstance(
            access, LegalAccessToken, "la rotation légitime doit finir par aboutir"
        )

    def test_known_kid_never_triggers_a_forced_refresh(self):
        """T5 — un kid déjà présent dans le cache n'appelle jamais
        ``refresh=True`` : le bridage ne doit pas coûter au cas nominal."""
        verifier = self._verifier()  # jeu par défaut : contient déjà KID
        token = _sign(self._payload(), self.key, kid=KID)

        access = self._verify_with(verifier, token)

        self.assertIsInstance(access, LegalAccessToken)
        appels = verifier._jwks_client.get_signing_keys.call_args_list
        self.assertFalse(
            any(c.kwargs.get("refresh") for c in appels),
            f"aucun appel ne doit passer refresh=True ; observé : {appels}",
        )

    def test_token_without_kid_is_refused_without_any_network_call(self):
        """T6 — un en-tête sans kid est un cas dégénéré : rejet immédiat,
        sans consommer le budget de rafraîchissement forcé ni faire de
        distinction réseau."""
        verifier = self._verifier()
        lookup = mock.Mock(return_value=[_key_stub(KID, self.key)])
        verifier._jwks_client.get_signing_keys = lookup
        token = _sign(self._payload(), self.key, kid=None)

        self.assertIsNone(self._verify_with(verifier, token))
        lookup.assert_not_called()

    def test_jwks_client_is_configured_defensively(self):
        """T7 — garde-fou de configuration du client JWKS.

        ``cache_keys`` gouverne le ``lru_cache`` interne de
        ``PyJWKClient.get_signing_key`` — au SINGULIER, une méthode que ce
        module n'appelle jamais : la résolution passe par
        ``get_signing_keys`` (au pluriel) et ``match_kid``, voir
        ``JwksTokenVerifier._resolve_signing_key``. Ce levier est donc
        INERTE sur le chemin réel — vérifié : remettre ``cache_keys=True``
        sur le code corrigé ne fait plus jamais réaccepter une clé révoquée.
        La vérifier ici reste une hygiène de configuration défensive (si un
        appel à ``get_signing_key`` singulier apparaissait un jour, on ne
        voudrait pas hériter d'un ``lru_cache`` sans expiration sans s'en
        apercevoir), mais ce n'est PAS elle qui protège SEC-03.

        Les deux garanties qui protègent réellement SEC-03 sont :

        * ``lifespan`` ne doit jamais dépasser ``JWKS_CACHE_LIFESPAN_SECONDS_MAX``
          — sans ce plafond, relever ``JWKS_CACHE_LIFESPAN_SECONDS`` à 86400
          (24 h) laisserait toute la suite verte tout en acceptant une clé
          révoquée 24 h durant ; c'est mesuré, pas supposé (voir le rapport
          de la revue qui a introduit ce plafond) ;
        * le test de comportement
          ``test_revoked_key_is_rejected_once_the_cache_lifespan_elapses``
          ci-dessous, qui exerce la révocation pour de vrai plutôt que de
          se fier à la seule configuration.
        """
        with mock.patch("mcp_server.auth.PyJWKClient") as jwks_cls:
            JwksTokenVerifier(
                issuer=ISSUER, jwks_url=f"{ISSUER}/jwks", audience=RESOURCE
            )

        self.assertEqual(1, jwks_cls.call_count)
        _, kwargs = jwks_cls.call_args
        self.assertIs(
            kwargs.get("cache_keys"),
            False,
            "cache_keys=True installerait un lru_cache sans expiration sur "
            "get_signing_key (singulier) — inerte sur le chemin réel, mais "
            "une régression de configuration à détecter tout de même",
        )
        self.assertIsNotNone(kwargs.get("timeout"))
        self.assertLessEqual(
            kwargs["timeout"],
            5,
            "un timeout non borné expose le pool de threads anyio à un "
            "émetteur lent (SEC-01)",
        )
        self.assertGreater(kwargs.get("lifespan", 0), 0)
        self.assertLessEqual(
            kwargs.get("lifespan", 0),
            JWKS_CACHE_LIFESPAN_SECONDS_MAX,
            "une clé révoquée resterait acceptée jusqu'à cette durée après "
            "sa rotation chez l'émetteur (SEC-03) ; lifespan configuré : "
            f"{kwargs.get('lifespan')}",
        )

    def test_revoked_key_is_rejected_once_the_cache_lifespan_elapses(self):
        """R1.b — LA garantie comportementale de SEC-03, celle que T7 ne
        peut qu'approcher par la configuration : une clé retirée du jeu
        publié par l'émetteur cesse d'être acceptée une fois
        ``JWKS_CACHE_LIFESPAN_SECONDS`` écoulé, sans attendre un redémarrage
        du processus. Utilise un faux ``PyJWKClient`` (``_FakeRotatingJwksClient``)
        dont le jeu de clés publié change entre deux appels, avec l'horloge
        injectable pour avancer le temps sans dormir.
        """
        clock = _FrozenClock()
        verifier = self._verifier(clock=clock)
        fake_client = _FakeRotatingJwksClient(
            lifespan=JWKS_CACHE_LIFESPAN_SECONDS,
            published=[_key_stub(KID, self.key)],
            clock=clock,
        )
        verifier._jwks_client = fake_client
        token = _sign(self._payload(), self.key, kid=KID)

        # Avant révocation : jeton nominal accepté, un seul appel réseau
        # (mise en cache initiale).
        access = self._verify_with(verifier, token)
        self.assertIsInstance(access, LegalAccessToken)
        self.assertEqual(1, fake_client.network_calls)

        # L'émetteur révoque la clé, mais le cache tier 1 est encore frais :
        # le jeton reste accepté SANS nouvel appel réseau. C'est le délai
        # annoncé par JWKS_CACHE_LIFESPAN_SECONDS, pas un bug.
        fake_client.set_published_keys([])
        access = self._verify_with(verifier, token)
        self.assertIsInstance(access, LegalAccessToken)
        self.assertEqual(
            1,
            fake_client.network_calls,
            "le cache encore frais ne doit produire aucun appel réseau",
        )

        # Le cache expire : la révocation est enfin honorée, sans
        # redémarrage du processus.
        clock.advance(JWKS_CACHE_LIFESPAN_SECONDS + 1)
        self.assertIsNone(self._verify_with(verifier, token))

    # ------------------------------------------------------------------
    # R3 — amplification résiduelle : lecture non verrouillée du cache
    # tier 1 de PyJWKClient (JWKSetCache, qui n'a lui-même aucun verrou).

    def test_concurrent_cache_expiry_produces_a_single_network_call(self):
        """R3.b — LE TEST CENTRAL de l'amplification résiduelle.

        N=20 threads qui franchissent ENSEMBLE une expiration du cache tier
        1 ne doivent produire qu'un seul appel réseau réel à
        ``get_signing_keys`` : c'est le single-flight de
        ``JwksTokenVerifier._jwks_fetch_lock``. Mesuré sur un vrai serveur
        JWKS, sans ce verrou, une telle rafale produit un appel par thread
        environ (8 → 8, 40 → 30, 80 → 76) — atteignable sans le moindre
        jeton valide, puisque cette lecture précède toute vérification de
        signature.

        ``_FakeRotatingJwksClient`` reproduit fidèlement l'absence de verrou
        interne du vrai ``JWKSetCache`` de PyJWT (voir sa source) : c'est
        donc bien le verrou de ``JwksTokenVerifier``, et lui seul, qui est
        sous test ici — pas un artefact du double.
        """
        N = 20
        verifier = JwksTokenVerifier(
            issuer=ISSUER, jwks_url=f"{ISSUER}/jwks", audience=RESOURCE
        )
        fake_client = _FakeRotatingJwksClient(
            lifespan=JWKS_CACHE_LIFESPAN_SECONDS,
            published=[_key_stub(KID, self.key)],
            # Délai artificiel : élargit la fenêtre de course pour que des
            # threads non sérialisés se chevauchent de façon fiable — sans
            # quoi l'absence de verrou ne se remarquerait qu'une fraction du
            # temps, et la contre-épreuve (verrou retiré) pourrait passer
            # par chance.
            fetch_delay_seconds=0.02,
        )
        verifier._jwks_client = fake_client
        token = _sign(self._payload(), self.key, kid=KID)

        barrier = threading.Barrier(N)
        erreurs: list[BaseException] = []

        def worker() -> None:
            barrier.wait()  # tous les threads démarrent au même instant
            try:
                verifier._resolve_signing_key(token)
            except BaseException as exc:  # pragma: no cover - diagnostic
                erreurs.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual([], erreurs, f"résolution en échec : {erreurs}")
        self.assertEqual(
            1,
            fake_client.network_calls,
            f"{N} threads franchissant ensemble l'expiration du cache tier 1 "
            "ne doivent produire qu'un seul appel réseau réel à "
            f"get_signing_keys ; observé : {fake_client.network_calls}",
        )


class JwksTwoKeyConfusionTests(unittest.TestCase):
    """R2 — sur un JWKS à deux clés (la forme réelle de production), un
    jeton signé par une clé mais annonçant le ``kid`` d'une autre doit être
    refusé.

    Tous les jeux de clés simulés ailleurs dans ce fichier n'ont qu'un seul
    élément (ou zéro) : ``match_kid`` y trouve alors toujours la bonne clé,
    ou aucune — jamais la mauvaise. Une mutation qui remplacerait
    ``match_kid(keys, kid)`` par ``keys[0]`` survivrait donc à toute la
    suite sans les tests ci-dessous.

    La clé B est délibérément placée en tête de liste (``keys[0]``) : un tel
    mutant renverrait alors toujours la clé B, quel que soit le ``kid``
    demandé. Les deux assertions de chaque test le détectent
    indépendamment l'une de l'autre :

    * jeton signé par B, en-tête ``kid`` de A → doit être REFUSÉ (la
      vérification cryptographique échoue, la clé A ne correspond pas à la
      signature de B) ; le mutant l'ACCEPTERAIT à tort (``keys[0]`` = clé B,
      qui elle correspond) — exactement la confusion de clé mesurée ;
    * jeton signé par A, en-tête ``kid`` de A (le cas nominal) → doit être
      ACCEPTÉ ; le mutant le REFUSERAIT à tort (``keys[0]`` = clé B, qui ne
      correspond pas à la signature de A).
    """

    @classmethod
    def setUpClass(cls):
        cls.key_a = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.key_b = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    @staticmethod
    def _payload() -> dict[str, object]:
        now = int(time.time())
        return {
            "iss": ISSUER,
            "aud": RESOURCE,
            "sub": "auth0|utilisateur-1",
            "iat": now,
            "exp": now + 300,
        }

    def _two_key_jwks(self) -> list:
        # Clé B en position 0 : voir le docstring de la classe.
        return [_key_stub(KID_B, self.key_b), _key_stub(KID, self.key_a)]

    def _new_verifier(self) -> JwksTokenVerifier:
        return JwksTokenVerifier(
            issuer=ISSUER, jwks_url=f"{ISSUER}/jwks", audience=RESOURCE
        )

    # -- Chemin résolu depuis le cache : les deux kids y figurent déjà -----

    def test_cached_path_distinguishes_the_two_keys(self):
        verifier = self._new_verifier()
        verifier._jwks_client.get_signing_keys = mock.Mock(
            return_value=self._two_key_jwks()
        )

        confusion = _sign(self._payload(), self.key_b, kid=KID)  # signé B, kid=A
        self.assertIsNone(
            asyncio.run(verifier.verify_token(confusion)),
            "un jeton signé par B mais annonçant le kid de A doit être refusé",
        )

        nominal = _sign(self._payload(), self.key_a, kid=KID)  # signé A, kid=A
        access = asyncio.run(verifier.verify_token(nominal))
        self.assertIsInstance(
            access, LegalAccessToken, "le jeton nominal signé par A doit être accepté"
        )

        appels = verifier._jwks_client.get_signing_keys.call_args_list
        self.assertFalse(
            any(c.kwargs.get("refresh") for c in appels),
            "ce test doit rester sur le chemin en cache, sans rafraîchissement forcé",
        )

    # -- Chemin par rafraîchissement forcé : absent du cache initial -------

    def _verifier_forcing_refresh(self) -> JwksTokenVerifier:
        """Le premier appel (sans rafraîchissement) ne porte ni KID ni
        KID_B : un rafraîchissement forcé est donc déclenché à chaque fois,
        et c'est lui qui sert le JWKS à deux clés où la confusion est
        exercée."""
        verifier = self._new_verifier()
        cle_hors_sujet = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        def lookup(refresh: bool = False):
            if refresh:
                return self._two_key_jwks()
            return [_key_stub("clef-sans-rapport", cle_hors_sujet)]

        verifier._jwks_client.get_signing_keys = mock.Mock(side_effect=lookup)
        return verifier

    def test_forced_refresh_path_distinguishes_the_two_keys(self):
        # Une instance par jeton : _forced_refresh_allowed ne laisse passer
        # qu'un seul rafraîchissement forcé par intervalle et par instance
        # (voir JwksTokenVerifier._refresh_lock) — réutiliser le même
        # vérificateur pour les deux jetons bloquerait le second par ce
        # bridage, indépendamment de toute confusion de clé.
        verifier_confusion = self._verifier_forcing_refresh()
        confusion = _sign(self._payload(), self.key_b, kid=KID)
        self.assertIsNone(
            asyncio.run(verifier_confusion.verify_token(confusion)),
            "un jeton signé par B mais annonçant le kid de A doit être refusé",
        )

        verifier_nominal = self._verifier_forcing_refresh()
        nominal = _sign(self._payload(), self.key_a, kid=KID)
        access = asyncio.run(verifier_nominal.verify_token(nominal))
        self.assertIsInstance(
            access, LegalAccessToken, "le jeton nominal signé par A doit être accepté"
        )

        for verifier in (verifier_confusion, verifier_nominal):
            appels = verifier._jwks_client.get_signing_keys.call_args_list
            self.assertTrue(
                any(c.kwargs.get("refresh") for c in appels),
                "ce test doit exercer le chemin par rafraîchissement forcé",
            )


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
