#!/usr/bin/env python3
"""Vérifie les métadonnées OAuth d'un serveur MCP déjà démarré.

Contrôle le point exact dont dépend l'acceptation du connecteur ChatGPT :
l'émetteur annoncé par les deux routes RFC 9728 doit être identique, caractère
pour caractère, à celui que publie le serveur d'autorisation. OpenAI compare
ces chaînes textuellement, sans normaliser la barre oblique finale.

S'utilise aussi bien contre un serveur local, avec un émetteur factice, que
contre la production :

    python tests/check_oauth_metadata.py http://127.0.0.1:8000 \\
        --issuer https://exemple.eu.auth0.com/

    python tests/check_oauth_metadata.py https://droit-francais-skill.onrender.com \\
        --discover

Aucun jeton n'est présenté et aucun secret n'est lu : seules des routes
publiques sont interrogées.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TIMEOUT = 15
ROOT_PATH = "/.well-known/oauth-protected-resource"


class MetadataError(RuntimeError):
    """Défaut de métadonnée, formulé sans recopier de valeur sensible."""


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        return json.load(response)


def _metadata_of(url: str) -> tuple[str, str]:
    """Retourne (émetteur annoncé, ressource déclarée) pour une route RFC 9728."""
    payload = _get_json(url)
    servers = payload.get("authorization_servers")
    if not isinstance(servers, list) or not servers:
        raise MetadataError(f"authorization_servers absent ou vide : {url}")
    resource = payload.get("resource")
    if not isinstance(resource, str) or not resource:
        raise MetadataError(f"resource absent ou vide : {url}")
    return str(servers[0]), resource


def _expected_metadata_url(resource: str) -> str:
    """URL de métadonnée déduite de la ressource, au sens de la RFC 9728 §3.1.

    Le chemin de la ressource est inséré *après* le suffixe well-known — même
    construction que ``build_resource_metadata_url`` côté SDK.
    """
    parts = urlsplit(resource)
    return urlunsplit((parts.scheme, parts.netloc, f"{ROOT_PATH}{parts.path}", "", ""))


def _anonymous_challenge(base_url: str) -> str:
    """Retourne l'en-tête WWW-Authenticate du refus anonyme attendu."""
    request = urllib.request.Request(
        f"{base_url}/mcp",
        method="POST",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raise MetadataError(
                f"une requête anonyme a été acceptée (code {response.status}) : "
                "le transport n'exige pas de jeton"
            )
    except urllib.error.HTTPError as error:
        if error.code != 401:
            raise MetadataError(
                f"refus anonyme attendu en 401, obtenu {error.code}"
            ) from error
        challenge = error.headers.get("WWW-Authenticate", "")
    if not challenge:
        raise MetadataError("le 401 ne porte aucun en-tête WWW-Authenticate")
    return challenge


def verify(base_url: str, expected_issuer: str | None, discover: bool) -> None:
    base_url = base_url.rstrip("/")
    racine, ressource_racine = _metadata_of(f"{base_url}{ROOT_PATH}")
    suffixee, ressource_suffixee = _metadata_of(f"{base_url}{ROOT_PATH}/mcp")

    if ressource_racine != ressource_suffixee:
        raise MetadataError(
            "les deux routes de métadonnées déclarent des ressources différentes :"
            f"\n    racine : {ressource_racine!r}"
            f"\n    /mcp   : {ressource_suffixee!r}"
        )

    if racine != suffixee:
        raise MetadataError(
            "les deux routes de métadonnées annoncent des émetteurs différents :"
            f"\n    racine : {racine!r}"
            f"\n    /mcp   : {suffixee!r}"
        )

    if discover:
        # Le document de découverte fait autorité. Il se lit sur la base
        # tronquée : la barre finale y produirait une double barre.
        published = _get_json(
            f"{racine.rstrip('/')}/.well-known/openid-configuration"
        ).get("issuer")
        expected_issuer = str(published)

    if expected_issuer is not None and racine != expected_issuer:
        raise MetadataError(
            "l'émetteur publié diffère de celui attendu — OpenAI compare ces "
            "chaînes sans les normaliser :"
            f"\n    publié  : {racine!r}"
            f"\n    attendu : {expected_issuer!r}"
        )

    challenge = _anonymous_challenge(base_url)
    # Le challenge est bâti sur l'URL publique déclarée, pas sur celle par
    # laquelle on sonde : c'est celle-là que le client ira réellement lire.
    attendu = f'resource_metadata="{_expected_metadata_url(ressource_racine)}"'
    if attendu not in challenge:
        raise MetadataError(
            "le challenge du 401 ne renvoie pas vers la route de métadonnées attendue :"
            f"\n    attendu : {attendu}"
            f"\n    reçu    : {challenge}"
        )

    print(f"✅ Émetteur publié à l'identique par les deux routes : {racine}")
    print(f"✅ Ressource déclarée de façon cohérente : {ressource_racine}")
    print("✅ Requête anonyme refusée en 401, challenge conforme.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Contrôle les métadonnées OAuth d'un serveur MCP"
    )
    parser.add_argument(
        "base_url",
        nargs="?",
        default="http://127.0.0.1:8000",
        help="Origine du serveur MCP, sans /mcp.",
    )
    parser.add_argument(
        "--issuer",
        help="Émetteur attendu, comparé caractère pour caractère.",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help=(
            "Lit l'émetteur attendu dans le document de découverte plutôt que "
            "de le recevoir en argument. Exige un émetteur joignable."
        ),
    )
    args = parser.parse_args()
    if args.issuer and args.discover:
        parser.error("--issuer et --discover s'excluent.")
    try:
        verify(args.base_url, args.issuer, args.discover)
    except MetadataError as exc:
        print(f"❌ {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
