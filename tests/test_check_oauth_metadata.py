#!/usr/bin/env python3
"""Tests hors réseau des quatre branches d'échec de ``check_oauth_metadata.py``.

``check_oauth_metadata.py`` protège le point de rupture historique du
connecteur ChatGPT : l'émetteur annoncé par les deux routes RFC 9728 doit être
identique, caractère pour caractère, à celui que publie le serveur
d'autorisation (voir son propre docstring). Aucun test ne l'exerçait jusqu'ici
— y compris, et surtout, son chemin d'échec : un script de contrôle qui ne se
déclenche jamais ne protège de rien.

Ces tests forcent chacune des quatre branches ``raise MetadataError`` de
``verify()`` en simulant les réponses HTTP via ``_get_json`` et
``_anonymous_challenge``. Aucune requête réseau n'est faite.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import check_oauth_metadata as verifie  # noqa: E402

BASE_URL = "https://exemple.test"
EMETTEUR = "https://idp.exemple.test"
RESSOURCE = "https://exemple.test/mcp"


def _metadonnees(*, emetteur: str = EMETTEUR, ressource: str = RESSOURCE) -> dict:
    """Corps JSON minimal d'une route ``oauth-protected-resource`` valide."""
    return {"authorization_servers": [emetteur], "resource": ressource}


class VerifyFailureBranchesTests(unittest.TestCase):
    """Un test par branche : chacun échouerait si sa branche cessait d'être
    atteinte, ou cessait de lever ``MetadataError``."""

    def _verifier(
        self,
        *,
        get_json_returns: list[dict],
        challenge: str = "",
        expected_issuer: str | None = None,
        discover: bool = False,
    ):
        """Appelle ``verify`` avec ``_get_json``/``_anonymous_challenge`` simulés.

        Retourne le message de l'exception levée et les deux mocks, pour que
        chaque test puisse en plus vérifier qu'aucun appel superflu n'a eu
        lieu après la première anomalie détectée.
        """
        with mock.patch.object(
            verifie, "_get_json", side_effect=get_json_returns
        ) as json_mock:
            with mock.patch.object(
                verifie, "_anonymous_challenge", return_value=challenge
            ) as challenge_mock:
                with self.assertRaises(verifie.MetadataError) as cm:
                    verifie.verify(BASE_URL, expected_issuer, discover)
        return str(cm.exception), json_mock, challenge_mock

    def test_diverging_resources_between_the_two_routes_is_rejected(self):
        """Branche 1 : la route racine et la route ``/mcp`` déclarent des
        ressources différentes — RFC 9728 exige qu'elles concordent."""
        message, _json_mock, challenge_mock = self._verifier(
            get_json_returns=[
                _metadonnees(ressource=RESSOURCE),
                _metadonnees(ressource=f"{RESSOURCE}/autre"),
            ]
        )
        self.assertIn("ressources différentes", message)
        # L'anomalie est fatale : sonder le refus anonyme serait un appel
        # réseau superflu une fois les métadonnées déjà incohérentes.
        challenge_mock.assert_not_called()

    def test_diverging_issuers_between_the_two_routes_is_rejected(self):
        """Branche 2 : même ressource, mais un émetteur différent selon la
        route interrogée — exactement la panne qu'OpenAI ne pardonne pas."""
        message, _json_mock, challenge_mock = self._verifier(
            get_json_returns=[
                _metadonnees(emetteur="https://idp-a.exemple.test"),
                _metadonnees(emetteur="https://idp-b.exemple.test"),
            ]
        )
        self.assertIn("émetteurs différents", message)
        challenge_mock.assert_not_called()

    def test_issuer_different_from_the_expected_one_is_rejected(self):
        """Branche 3 : les deux routes concordent entre elles, mais pas avec
        l'émetteur attendu (``--issuer`` explicite ou ``--discover``)."""
        message, _json_mock, challenge_mock = self._verifier(
            get_json_returns=[_metadonnees(), _metadonnees()],
            expected_issuer="https://idp-attendu.exemple.test",
        )
        self.assertIn("diffère de celui attendu", message)
        challenge_mock.assert_not_called()

    def test_401_challenge_without_resource_metadata_is_rejected(self):
        """Branche 4 : les métadonnées concordent, mais le défi 401 anonyme
        ne pointe pas vers la route de métadonnées attendue."""
        message, _json_mock, challenge_mock = self._verifier(
            get_json_returns=[_metadonnees(), _metadonnees()],
            challenge='Bearer realm="mcp"',
        )
        self.assertIn(
            "ne renvoie pas vers la route de métadonnées attendue", message
        )
        challenge_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
