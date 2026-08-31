#!/usr/bin/env python3
"""Parcours OAuth complet du serveur MCP, joué en processus et hors réseau.

Les tests de ``test_auth.py`` vérifient le vérificateur de jetons isolément.
Ceux-ci exercent la chaîne réelle : application ASGI construite par le SDK,
middleware d'authentification, transport Streamable HTTP, dispatch d'outil.
Seuls deux points sont simulés — le JWKS de l'émetteur, remplacé par une clé
RSA engendrée à la volée, et les appels aux API juridiques, qui ne doivent
jamais partir vers PISTE depuis un test.

Aucun secret n'est lu et aucun jeton réel n'est nécessaire : l'émetteur est
factice et les jetons sont signés localement.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
import time
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

import httpx2  # noqa: E402  — dépendance de transport du SDK MCP
import jwt  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402
from mcp import ClientSession  # noqa: E402
from mcp.client.streamable_http import streamable_http_client  # noqa: E402
from mcp.server.transport_security import TransportSecuritySettings  # noqa: E402

from mcp_server import server as mcp_app  # noqa: E402

ISSUER = "https://exemple-idp.eu.auth0.com/"
PUBLIC_URL = "https://exemple.test"
RESOURCE = "https://exemple.test/mcp"
AUTRE_EMETTEUR = "https://idp-pirate.example/"

#: Origine utilisee pour joindre l'application en processus. Elle est distincte
#: de l'URL publique, qui reste celle de la ressource et de l'audience.
TRANSPORT_HOST = "127.0.0.1:8000"
TRANSPORT_URL = f"http://{TRANSPORT_HOST}"

#: Le SDK protege le transport contre le rebinding DNS en validant l'en-tete
#: Host. En production, l'hote est celui sur lequel uvicorn ecoute ; ici,
#: l'application est jointe en processus, sans socket. La protection reste
#: ACTIVE — on se contente de declarer l'hote de test comme legitime, pour ne
#: pas eprouver un serveur configure plus permissivement que le vrai.
TRANSPORT_SECURITY = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[TRANSPORT_HOST],
    allowed_origins=[TRANSPORT_URL],
)

#: Quota volontairement bas : le dépassement doit être atteint en trois appels.
QUOTA_PAR_UTILISATEUR = 2

OAUTH_ENV = {
    "MCP_ENV": "test",
    "MCP_AUTH_MODE": "oauth",
    "MCP_PUBLIC_URL": PUBLIC_URL,
    "MCP_OAUTH_ISSUER": ISSUER,
    "MCP_USER_CALLS_PER_MINUTE": str(QUOTA_PAR_UTILISATEUR),
}


class OAuthServerCase(unittest.TestCase):
    """Socle : recharge le serveur en mode OAuth avec un émetteur factice.

    Le module ``mcp_server.server`` lit sa configuration à l'import. Le
    rechargement est donc le seul moyen d'exercer le mode OAuth sans démarrer
    un processus séparé — et il impose de restaurer l'état d'origine, sous
    peine de contaminer les autres modules de test de la même session.
    """

    extra_env: dict[str, str] = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        cls._env = mock.patch.dict(
            os.environ, dict(OAUTH_ENV, **cls.extra_env), clear=False
        )
        cls._env.start()

        cls._jwks = mock.patch("mcp_server.auth.PyJWKClient")
        jwks_client = cls._jwks.start()
        signing_key = mock.Mock()
        signing_key.key = cls.key.public_key()
        jwks_client.return_value.get_signing_key_from_jwt.return_value = signing_key

        importlib.reload(mcp_app)
        assert mcp_app.SETTINGS.auth_enabled, "le rechargement n'a pas activé OAuth"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._jwks.stop()
        cls._env.stop()
        # Rétablit un serveur non authentifié pour les autres modules de test.
        importlib.reload(mcp_app)

    # ------------------------------------------------------------------
    # Lecture d'un resultat d'outil
    #
    # Le SDK v1 nomme ces champs en camelCase, le v2 en snake_case. Les deux
    # formes sont lues, comme le fait deja tests/check_mcp_http.py : le test
    # reste lisible quelle que soit la version installee et n'echoue que sur
    # le fond.

    @staticmethod
    def en_erreur(resultat) -> bool:
        valeur = getattr(resultat, "is_error", None)
        if valeur is None:
            valeur = getattr(resultat, "isError", None)
        return bool(valeur)

    @staticmethod
    def contenu_structure(resultat):
        valeur = getattr(resultat, "structured_content", None)
        if valeur is None:
            valeur = getattr(resultat, "structuredContent", None)
        return valeur

    # ------------------------------------------------------------------
    # Fabrication de jetons

    def token(self, **overrides) -> str:
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
        return jwt.encode(payload, self.key, algorithm="RS256")

    # ------------------------------------------------------------------
    # Accès HTTP en processus

    @asynccontextmanager
    async def _running(self, token: str | None):
        """Application neuve, cycle de vie démarré, client HTTP en processus.

        L'application est reconstruite à chaque appel : le gestionnaire de
        sessions Streamable HTTP n'accepte qu'un seul cycle de vie par
        instance. Sans ce cycle de vie, il ne démarre jamais et tout appel
        d'outil échoue.
        """
        app = mcp_app.server.streamable_http_app(
            transport_security=TRANSPORT_SECURITY
        )
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with app.router.lifespan_context(app):
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url=TRANSPORT_URL,
                headers=headers,
                timeout=30,
            ) as client:
                yield client

    def post_mcp(self, token: str | None, body: dict | None = None):
        """POST brut sur /mcp, sans session MCP : sert aux cas de refus."""

        async def run():
            async with self._running(token) as client:
                return await client.post(
                    "/mcp",
                    json=body or {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    headers={"Accept": "application/json, text/event-stream"},
                )

        return asyncio.run(run())

    def call_tool(self, token: str, name: str, arguments: dict):
        """Session MCP complète, jeton porté par le client de transport."""

        async def run():
            async with self._running(token) as client:
                async with streamable_http_client(
                    f"{TRANSPORT_URL}/mcp", http_client=client
                ) as (reader, writer, *_):
                    async with ClientSession(reader, writer) as session:
                        await session.initialize()
                        return await session.call_tool(name, arguments)

        return asyncio.run(run())


class RefusTests(OAuthServerCase):
    """Tout jeton non conforme doit être refusé, sans détail exploitable."""

    def test_requete_anonyme_est_refusee_avec_le_bon_challenge(self):
        response = self.post_mcp(None)
        self.assertEqual(401, response.status_code)
        challenge = response.headers.get("www-authenticate", "")
        self.assertIn("Bearer", challenge)
        self.assertIn(
            f'resource_metadata="{PUBLIC_URL}/.well-known/oauth-protected-resource/mcp"',
            challenge,
        )

    def test_jeton_pour_une_autre_api_est_refuse(self):
        token = self.token(aud="https://une-autre-api.example")
        self.assertEqual(401, self.post_mcp(token).status_code)

    def test_jeton_d_un_autre_emetteur_est_refuse(self):
        self.assertEqual(401, self.post_mcp(self.token(iss=AUTRE_EMETTEUR)).status_code)

    def test_jeton_expire_est_refuse(self):
        now = int(time.time())
        token = self.token(iat=now - 7200, exp=now - 3600)
        self.assertEqual(401, self.post_mcp(token).status_code)

    def test_jeton_signe_par_une_cle_inconnue_est_refuse(self):
        autre = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        now = int(time.time())
        token = jwt.encode(
            {
                "iss": ISSUER,
                "aud": RESOURCE,
                "sub": "auth0|intrus",
                "iat": now,
                "exp": now + 300,
            },
            autre,
            algorithm="RS256",
        )
        self.assertEqual(401, self.post_mcp(token).status_code)

    def test_jeton_sans_sujet_est_refuse(self):
        # Sans « sub », aucun quota individuel n'est imputable : le jeton ne
        # doit pas ouvrir l'accès, même si sa signature est valide.
        now = int(time.time())
        token = jwt.encode(
            {"iss": ISSUER, "aud": RESOURCE, "iat": now, "exp": now + 300},
            self.key,
            algorithm="RS256",
        )
        self.assertEqual(401, self.post_mcp(token).status_code)

    def test_le_refus_ne_divulgue_aucun_detail(self):
        response = self.post_mcp(self.token(aud="https://une-autre-api.example"))
        corps = response.text.lower()
        for indice in ("audience", "signature", "jwks", "exemple-idp"):
            self.assertNotIn(indice, corps)


class AccesAutoriseTests(OAuthServerCase):
    """Un jeton conforme ouvre l'accès et rend le sujet imputable."""

    def test_jeton_valide_permet_un_appel_d_outil(self):
        attendu = {
            "results": [
                {
                    "id": "LEGIARTI000042193463",
                    "title": "Article L2212-2",
                    "url": "https://www.legifrance.gouv.fr/x",
                }
            ]
        }
        with mock.patch.object(
            mcp_app.legal_tools, "search", return_value=attendu
        ) as recherche:
            resultat = self.call_tool(self.token(), "search", {"query": "police"})

        self.assertFalse(self.en_erreur(resultat), resultat.content)
        self.assertEqual(attendu, self.contenu_structure(resultat))
        recherche.assert_called_once_with("police")

    def test_l_appel_est_impute_au_sujet_du_jeton(self):
        vus: list[str] = []
        original = mcp_app._current_principal

        def espion() -> str:
            principal = original()
            vus.append(principal)
            return principal

        with mock.patch.object(mcp_app, "_current_principal", espion):
            with mock.patch.object(mcp_app.legal_tools, "search", return_value={}):
                self.call_tool(
                    self.token(sub="auth0|utilisateur-observe"),
                    "search",
                    {"query": "x"},
                )

        self.assertEqual(["auth0|utilisateur-observe"], vus)

    def test_les_portees_du_jeton_sont_journalisees(self):
        """La portée portée par le jeton doit être lisible dans le journal.

        C'est elle qui permettra de trancher la réactivation du contrôle de
        portée sur une mesure plutôt que sur une hypothèse. Le journal ne doit
        pour autant révéler ni le jeton ni le sujet en clair.
        """
        with mock.patch.object(mcp_app.legal_tools, "search", return_value={}):
            with self.assertLogs("droit_francais.mcp", level="INFO") as journal:
                self.call_tool(
                    self.token(sub="auth0|alice", scope="legal:read openid"),
                    "search",
                    {"query": "x"},
                )

        lignes = [ligne for ligne in journal.output if "tool_call" in ligne]
        self.assertTrue(lignes, journal.output)
        ligne = lignes[0]
        self.assertIn("scopes=legal:read,openid", ligne)
        self.assertNotIn("auth0|alice", ligne)

    def test_l_erreur_metier_ne_reexpose_aucun_secret(self):
        from droit_francais.errors import LegifranceError

        def echouer(*_args, **_kwargs):
            raise LegifranceError("cle valeur-tres-secrete refusee", exit_code=3)

        with mock.patch.dict(
            os.environ, {"LEGIFRANCE_CLIENT_SECRET": "valeur-tres-secrete"}
        ):
            with mock.patch.object(mcp_app.legal_tools, "search", echouer):
                resultat = self.call_tool(self.token(), "search", {"query": "x"})

        self.assertTrue(self.en_erreur(resultat))
        rendu = str(resultat.content)
        self.assertNotIn("valeur-tres-secrete", rendu)
        self.assertIn("secret masqué", rendu)


class QuotaParUtilisateurTests(OAuthServerCase):
    """Le quota protège les clés PISTE du titulaire, sujet par sujet."""

    def setUp(self) -> None:
        # Chaque test repart d'un compteur vide : le quota est glissant sur une
        # minute, donc un test précédent le remplirait pour le suivant.
        mcp_app.USER_LIMITER._buckets.clear()

    def test_le_quota_est_isole_par_sujet(self):
        with mock.patch.object(mcp_app.legal_tools, "search", return_value={}):
            for _ in range(QUOTA_PAR_UTILISATEUR):
                resultat = self.call_tool(
                    self.token(sub="auth0|alice"), "search", {"query": "x"}
                )
                self.assertFalse(self.en_erreur(resultat), resultat.content)

            depassement = self.call_tool(
                self.token(sub="auth0|alice"), "search", {"query": "x"}
            )
            self.assertTrue(self.en_erreur(depassement))
            self.assertIn("Quota individuel", str(depassement.content))

            # Un second sujet dispose de son propre quota : le dépassement de
            # l'un ne ferme pas le service à l'autre.
            autre = self.call_tool(
                self.token(sub="auth0|bob"), "search", {"query": "x"}
            )
            self.assertFalse(self.en_erreur(autre), autre.content)


class PorteeDesactiveeTests(OAuthServerCase):
    """``MCP_OAUTH_REQUIRED_SCOPES=-`` ne désactive jamais l'authentification.

    C'est une configuration de compatibilité : certains clients n'annoncent pas
    la portée personnalisée dans leur requête d'autorisation alors que
    l'authentification, elle, aboutit. L'imputabilité repose alors sur le sujet
    du jeton, pas sur la portée — mais un jeton reste exigé.
    """

    extra_env = {"MCP_OAUTH_REQUIRED_SCOPES": "-"}

    def test_le_controle_de_portee_est_bien_desactive(self):
        self.assertEqual((), mcp_app.SETTINGS.oauth_required_scopes)
        self.assertTrue(mcp_app.SETTINGS.auth_enabled)

    def test_l_authentification_reste_exigee(self):
        self.assertEqual(401, self.post_mcp(None).status_code)

    def test_un_jeton_sans_la_portee_est_accepte(self):
        with mock.patch.object(mcp_app.legal_tools, "search", return_value={}):
            resultat = self.call_tool(
                self.token(scope="openid profile"), "search", {"query": "x"}
            )
        self.assertFalse(self.en_erreur(resultat), resultat.content)

    def test_un_jeton_sans_aucune_portee_est_journalise_comme_tel(self):
        """« aucune » doit être lisible tel quel : c'est ce constat, dans les
        journaux de production, qui dira si le contrôle de portée peut être
        réactivé sans casser le connecteur."""
        with mock.patch.object(mcp_app.legal_tools, "search", return_value={}):
            with self.assertLogs("droit_francais.mcp", level="INFO") as journal:
                self.call_tool(self.token(scope=""), "search", {"query": "x"})

        lignes = [ligne for ligne in journal.output if "tool_call" in ligne]
        self.assertTrue(lignes, journal.output)
        self.assertIn("scopes=aucune", lignes[0])


class PorteeExigeeTests(OAuthServerCase):
    """À l'inverse, la portée redevient contraignante dès qu'elle est exigée."""

    extra_env = {"MCP_OAUTH_REQUIRED_SCOPES": "legal:read"}

    def test_un_jeton_sans_la_portee_exigee_est_refuse(self):
        reponse = self.post_mcp(self.token(scope="openid profile"))
        self.assertEqual(403, reponse.status_code)

    def test_un_jeton_portant_la_portee_est_accepte(self):
        # Le cas accepte se verifie sur une session complete, pas sur un POST
        # brut : hors session, le transport repond 400 quel que soit le jeton,
        # ce qui ne dirait rien de l'autorisation. Un « pas 401 » serait tout
        # aussi trompeur, puisqu'il laisserait passer un 403 de portee.
        with mock.patch.object(mcp_app.legal_tools, "search", return_value={}):
            resultat = self.call_tool(self.token(), "search", {"query": "x"})
        self.assertFalse(self.en_erreur(resultat), resultat.content)


if __name__ == "__main__":
    unittest.main()
