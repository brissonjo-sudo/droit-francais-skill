#!/usr/bin/env python3
"""jeton.py — obtention du jeton d'accès au serveur MCP de production.

Transposition locale de l'échange `client_credentials` de
`.github/workflows/sonde-fonctionnelle.yml` : mêmes garanties, même hygiène.

Règles tenues ici :

- Le secret ne passe **jamais** en argument de ligne de commande — il serait
  visible dans la liste des processus. Il est lu dans l'environnement et
  envoyé dans le corps de la requête.
- Aucun jeton n'est écrit sur disque ni journalisé.
- Les messages d'erreur se limitent aux champs `error` et `error_description`
  du fournisseur : le corps complet d'une réponse d'échec peut contenir des
  éléments de configuration.

Stdlib uniquement (urllib), comme le reste des sondes du dépôt.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

EMETTEUR_DEFAUT = "https://dev-7soa32jfmxpejzhs.eu.auth0.com"
AUDIENCE_DEFAUT = "https://droit-francais-skill.onrender.com/mcp"

# Marge sous l'expiration : au-delà, on renouvelle plutôt que risquer un 401
# au milieu d'un cas déjà lancé.
MARGE_S = 600


class JetonIndisponible(RuntimeError):
    """Aucun jeton ne peut être obtenu avec la configuration présente."""


@dataclass
class Jeton:
    valeur: str
    expire_a: float

    @property
    def bientot_expire(self) -> bool:
        return time.time() >= self.expire_a - MARGE_S


def _emetteur() -> str:
    return (os.environ.get("AUTH0_ISSUER") or EMETTEUR_DEFAUT).rstrip("/")


def _refuser_jeton_etranger(valeur: str) -> None:
    """Refuse un jeton qui n'est manifestement pas celui du serveur MCP.

    ``MCP_ACCESS_TOKEN`` court-circuite l'échange Auth0. Un jeton d'abonnement
    Claude (préfixe ``sk-ant-``) rangé là part vers le serveur MCP en en-tête
    ``Authorization`` et revient en 401 — alors que les identifiants Auth0 du
    même fichier fonctionnaient. Erreur constatée en vrai : les deux jetons se
    ressemblent à l'œil, et le nom de la variable ne dit pas lequel est
    attendu.

    Le diagnostic porte sur le **préfixe** seul ; aucune valeur n'est
    journalisée ni renvoyée dans le message.
    """
    if valeur.startswith("sk-ant-"):
        raise JetonIndisponible(
            "MCP_ACCESS_TOKEN contient un jeton d'abonnement Claude (préfixe "
            "« sk-ant- »), pas un jeton du serveur MCP. Le vider : le harnais "
            "obtiendra le bon jeton par échange Auth0. Pour authentifier la "
            "CLI, la variable attendue est CLAUDE_CODE_OAUTH_TOKEN."
        )


def obtenir(*, timeout_s: int = 30) -> Jeton:
    """Rend un jeton d'accès, depuis l'environnement ou par échange Auth0.

    Un ``MCP_ACCESS_TOKEN`` déjà exporté est utilisé tel quel — c'est le mode
    d'emploi de `check_live_tools.py`, et il évite un échange inutile quand
    l'utilisateur dispose déjà d'un jeton valide.
    """
    direct = os.environ.get("MCP_ACCESS_TOKEN")
    if direct:
        _refuser_jeton_etranger(direct)
        # Durée inconnue : on la suppose courte pour forcer un renouvellement
        # par échange si l'exécution se prolonge.
        return Jeton(direct, time.time() + 3600)

    identifiant = os.environ.get("AUTH0_CLIENT_ID")
    secret = os.environ.get("AUTH0_CLIENT_SECRET")
    if not identifiant or not secret:
        raise JetonIndisponible(
            "ni MCP_ACCESS_TOKEN, ni AUTH0_CLIENT_ID/AUTH0_CLIENT_SECRET dans "
            "l'environnement — le bras C ne peut pas atteindre le serveur MCP"
        )

    corps = json.dumps(
        {
            "grant_type": "client_credentials",
            "client_id": identifiant,
            "client_secret": secret,
            "audience": os.environ.get("AUTH0_AUDIENCE") or AUDIENCE_DEFAUT,
        }
    ).encode("utf-8")

    requete = urllib.request.Request(  # noqa: S310 — schéma https fixé par l'émetteur
        f"{_emetteur()}/oauth/token",
        data=corps,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(requete, timeout=timeout_s) as reponse:  # noqa: S310
            charge = json.loads(reponse.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise JetonIndisponible(f"échange refusé ({exc.code}) : {_motif(exc)}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise JetonIndisponible(f"émetteur injoignable : {type(exc).__name__}") from None
    except (ValueError, TypeError):
        raise JetonIndisponible("réponse de l'émetteur illisible") from None

    valeur = charge.get("access_token")
    if not isinstance(valeur, str) or not valeur:
        raise JetonIndisponible("réponse sans access_token")

    duree = charge.get("expires_in")
    duree = duree if isinstance(duree, (int, float)) and duree > 0 else 3600
    return Jeton(valeur, time.time() + float(duree))


def _motif(exc: urllib.error.HTTPError) -> str:
    """Motif public d'un échec, sans recopier le corps complet de la réponse."""
    try:
        charge = json.loads(exc.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — un échec de lecture ne doit rien révéler
        return "détail non exploitable"
    if not isinstance(charge, dict):
        return "détail non exploitable"
    morceaux = [str(charge[cle]) for cle in ("error", "error_description") if cle in charge]
    return " — ".join(morceaux) if morceaux else "détail non exploitable"


def secrets_surveilles() -> list[str]:
    """Valeurs qui ne doivent jamais apparaître dans une trace persistée."""
    noms = ("MCP_ACCESS_TOKEN", "AUTH0_CLIENT_SECRET", "AUTH0_CLIENT_ID")
    return [valeur for nom in noms if (valeur := os.environ.get(nom))]
