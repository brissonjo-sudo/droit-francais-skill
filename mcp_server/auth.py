#!/usr/bin/env python3
"""Vérification des jetons OAuth 2.1 présentés au serveur MCP public.

Le serveur MCP est un *Resource Server* : il ne délivre aucun jeton et
n'héberge aucun mot de passe. Un serveur d'autorisation externe (Auth0,
Stytch, Clerk, WorkOS, Descope…) authentifie l'utilisateur, puis émet un
jeton signé que ce module valide localement à partir du JWKS public de
l'émetteur.

Conséquence pratique : les clés PISTE restent sur le serveur, mais chaque
appel d'outil devient imputable à un sujet identifié, ce qui permet un
quota par utilisateur et non plus seulement un quota global d'instance.

Contrôles appliqués à chaque jeton :

* signature asymétrique vérifiée contre le JWKS de l'émetteur ;
* ``iss`` strictement égal à l'émetteur canonique configuré ;
* ``aud`` contenant l'audience configurée (indicateur de ressource,
  RFC 8707) — un jeton émis pour une autre API est refusé ;
* ``exp`` et ``nbf`` vérifiés par la bibliothèque ;
* portées requises vérifiées en amont par le SDK MCP.

Aucun jeton, aucune charge utile et aucun secret n'est journalisé.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Iterable

import anyio
import jwt
from jwt import PyJWKClient
from mcp.server.auth.provider import AccessToken

LOGGER = logging.getLogger("droit_francais.mcp.auth")

#: Algorithme exact configuré dans le tenant Auth0 de production. Une liste
#: générique d'algorithmes asymétriques élargirait inutilement la politique de
#: validation des jetons.
ALLOWED_ALGORITHMS: tuple[str, ...] = ("RS256",)

#: Durée de vie du cache « tier 1 » (jeu de clés complet) de ``PyJWKClient``.
#: Une clé révoquée chez l'émetteur reste donc acceptée au plus ce délai après
#: la rotation — jamais jusqu'au redémarrage du processus (SEC-03).
JWKS_CACHE_LIFESPAN_SECONDS = 300

#: Plafond dur de la constante ci-dessus, vérifié par
#: ``test_jwks_client_is_configured_defensively`` indépendamment de sa
#: valeur : une relecture a mesuré qu'élever ``JWKS_CACHE_LIFESPAN_SECONDS``
#: à 86400 (24 h — un simple zéro de trop) laissait la suite de tests
#: entièrement verte tout en acceptant une clé révoquée 24 h durant, mot pour
#: mot SEC-03 rouvert. Fixé à l'ancienne valeur de
#: ``JWKS_CACHE_LIFESPAN_SECONDS`` d'avant le présent correctif (voir
#: ``JWKS_FORCED_REFRESH_INTERVAL_SECONDS`` plus bas pour le contexte de ce
#: resserrement) : quelle que soit la raison d'abaisser encore la valeur
#: ci-dessus, elle ne doit jamais pouvoir remonter au-delà de ce qui était
#: déjà le pire cas accepté avant cette revue.
JWKS_CACHE_LIFESPAN_SECONDS_MAX = 3600

#: Le cache « tier 2 » de ``PyJWKClient`` (``cache_keys=True``) est un
#: ``lru_cache`` SANS expiration temporelle : avec les deux clés du JWKS de
#: production, la LRU n'évince jamais rien et une clé révoquée resterait
#: acceptée jusqu'au redémarrage du processus. Il reste désactivé ; seul le
#: cache à expiration ci-dessus fait foi (SEC-03).
JWKS_CACHE_KEYS = False

#: ``PyJWKClient`` attend 30 s par défaut. ``_decode`` tourne dans un thread du
#: pool anyio (voir ``verify_token``) : sans borne, un émetteur qui ralentit
#: laisserait un attaquant non authentifié immobiliser tout le pool 30 s par
#: requête, jusqu'à épuiser les threads disponibles pour les requêtes
#: légitimes (SEC-01).
JWKS_HTTP_TIMEOUT_SECONDS = 5

#: Intervalle minimal entre deux rafraîchissements forcés du JWKS provoqués
#: par un ``kid`` absent du cache. Le vérificateur de jeton EST le point
#: d'authentification : avant tout contrôle, le ``kid`` est un texte
#: entièrement choisi par l'appelant. Sans ce bridage, un ``kid`` inconnu (au
#: hasard ou non) déclenche un aller-retour réseau vers l'émetteur à CHAQUE
#: requête anonyme (mesuré en production : +0,054 s par requête, facteur 1,8)
#: et peut épuiser le quota du locataire Auth0 (SEC-01). Contrepartie
#: acceptée : un attaquant qui inonde de ``kid`` aléatoires consomme ce budget
#: et peut retarder l'adoption d'une clé légitimement tournée d'au plus un
#: intervalle. C'est délibéré et borné.
JWKS_FORCED_REFRESH_INTERVAL_SECONDS = 60


class LegalAccessToken(AccessToken):
    """Jeton validé, enrichi du sujet servant de clé de quota."""

    subject: str


def _normalise_scopes(payload: dict[str, Any]) -> list[str]:
    """Extrait les portées, quel que soit le dialecte de l'émetteur."""
    raw: Any = payload.get("scope")
    if isinstance(raw, str):
        return [item for item in raw.split(" ") if item]
    for key in ("scp", "permissions", "scopes"):
        value = payload.get(key)
        if isinstance(value, str):
            return [item for item in value.split(" ") if item]
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value if str(item)]
    return []


def _client_identifier(payload: dict[str, Any]) -> str:
    """Identifie l'application appelante sans jamais renvoyer le jeton."""
    for key in ("azp", "client_id", "cid", "aud"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, (list, tuple)) and value:
            return str(value[0])
    return "client-inconnu"


class JwksTokenVerifier:
    """Implémente le protocole ``TokenVerifier`` du SDK MCP.

    Le jeu de clés JWKS est mis en cache avec expiration
    (``JWKS_CACHE_LIFESPAN_SECONDS``) : une rotation ou une révocation chez
    l'émetteur est reconnue au plus tard à l'expiration de ce délai, jamais
    seulement au redémarrage du processus.

    Un ``kid`` absent du jeu de clés en cache déclencherait normalement, côté
    ``PyJWKClient``, un rafraîchissement forcé immédiat auprès de l'émetteur.
    Comme ce jeton n'est pas encore authentifié à ce stade, le ``kid`` est une
    valeur que l'appelant contrôle entièrement : sans bridage, il pourrait
    provoquer un aller-retour réseau vers l'émetteur à chaque requête, avant
    toute authentification. Ce rafraîchissement forcé est donc limité à un
    appel au plus par ``JWKS_FORCED_REFRESH_INTERVAL_SECONDS``, quel que soit
    le nombre de ``kid`` distincts présentés — voir ``_forced_refresh_allowed``
    et ``_resolve_signing_key``.

    Amplification résiduelle, distincte de la précédente : le cache « tier 1 »
    de ``PyJWKClient`` (``JWKSetCache``) n'a lui-même aucun verrou. À
    l'instant précis où son ``lifespan`` expire, chaque requête concurrente
    qui atteint ``_resolve_signing_key`` constate un cache vide et déclenche
    SA PROPRE requête réseau — mesuré sur un vrai serveur JWKS : 8 threads →
    8 requêtes, 40 → 30, 80 → 76, atteignable sans le moindre jeton valide
    puisque cette lecture précède toute vérification de signature.
    ``_get_signing_keys`` sérialise donc tout appel à
    ``PyJWKClient.get_signing_keys`` (avec ou sans rafraîchissement forcé)
    sous ``_jwks_fetch_lock``, un verrou dédié et distinct de
    ``_refresh_lock`` : voir son commentaire dans ``__init__``.
    """

    def __init__(
        self,
        issuer: str,
        jwks_url: str,
        audience: str,
        *,
        leeway_seconds: int = 30,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._leeway_seconds = leeway_seconds
        self._algorithms = ALLOWED_ALGORITHMS
        self._jwks_client = PyJWKClient(
            jwks_url,
            cache_keys=JWKS_CACHE_KEYS,
            lifespan=JWKS_CACHE_LIFESPAN_SECONDS,
            timeout=JWKS_HTTP_TIMEOUT_SECONDS,
        )
        #: Horloge injectable (monotone, insensible aux ajustements de
        #: l'horloge système) : les tests figent ou avancent le temps sans
        #: jamais avoir à dormir pour observer le bridage ci-dessous.
        self._clock = clock
        #: Protège ``_last_forced_refresh`` : ``_decode`` s'exécute dans un
        #: thread du pool anyio, et des requêtes concurrentes portant un
        #: ``kid`` inconnu ne doivent consommer qu'un seul rafraîchissement.
        self._refresh_lock = threading.Lock()
        #: Horodatage du dernier rafraîchissement forcé, ou ``None`` avant le
        #: premier. Un unique horodatage suffit à plafonner les appels
        #: sortants : accumuler les ``kid`` déjà vus dans un dictionnaire
        #: donnerait à un attaquant un moyen de faire croître la mémoire du
        #: processus sans limite, au gré des ``kid`` aléatoires envoyés.
        self._last_forced_refresh: float | None = None
        #: Sérialise tout appel à ``PyJWKClient.get_signing_keys`` — avec ou
        #: sans rafraîchissement forcé. ``JWKSetCache`` (le cache « tier 1 »
        #: de PyJWKClient) n'a lui-même aucun verrou : à l'instant précis où
        #: son ``lifespan`` expire, chaque requête concurrente constate un
        #: cache vide et déclenche SA PROPRE requête réseau vers l'émetteur —
        #: mesuré sur un vrai serveur JWKS : 8 threads → 8 requêtes, 40 → 30,
        #: 80 → 76, sans le moindre jeton valide requis puisque cette lecture
        #: précède toute vérification de signature. Ce verrou transforme la
        #: ruée en single-flight : un seul thread contacte l'émetteur, les
        #: autres attendent puis retrouvent le cache déjà rechargé par le
        #: premier. Distinct de ``_refresh_lock`` ci-dessus, qui protège un
        #: budget d'une tout autre nature — le nombre de rafraîchissements
        #: forcés par intervalle, pas l'accès au cache lui-même — et n'est
        #: donc jamais tenu en même temps que celui-ci (voir
        #: ``_get_signing_keys`` et ``_resolve_signing_key`` : les deux
        #: verrous s'acquièrent et se relâchent l'un après l'autre, jamais
        #: imbriqués, ce qui exclut tout interblocage par ordre croisé).
        #: Coût : le chemin nominal (cache déjà frais) tourne autour de 45 µs
        #: sans le verrou ; le sérialiser ajoute au pire quelques
        #: millisecondes sur quarante threads simultanés — sans commune
        #: mesure avec quarante appels réseau concurrents vers Auth0.
        self._jwks_fetch_lock = threading.Lock()

    def _resolve_signing_key(self, token: str) -> jwt.PyJWK:
        """Trouve la clé de signature sans jamais amplifier un ``kid`` inconnu.

        1. Le ``kid`` est lu dans l'en-tête *non vérifié* du jeton : un simple
           décodage base64, jamais une preuve d'authenticité. Il ne sert qu'à
           indexer la recherche de clé ci-dessous, jamais à autoriser quoi que
           ce soit.
        2. La recherche part du jeu de clés en cache (``_get_signing_keys``,
           sans appel réseau si le cache est encore frais — voir
           ``_jwks_fetch_lock``). Si le ``kid`` y figure, la clé
           correspondante est retournée immédiatement.
        3. Sinon, un rafraîchissement forcé (``_get_signing_keys(refresh=True)``,
           qui contacte l'émetteur) n'est tenté que si ``_forced_refresh_allowed``
           l'autorise. À défaut, échec immédiat, sans aucun appel réseau.

        Chacun des deux appels à ``_get_signing_keys`` acquiert puis relâche
        entièrement ``_jwks_fetch_lock`` avant que ``_forced_refresh_allowed``
        n'acquière (séparément) ``_refresh_lock`` : les deux verrous ne sont
        donc jamais imbriqués, quel que soit le chemin emprunté.
        """
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise jwt.PyJWKClientError("Jeton sans identifiant de clé exploitable.")

        keys = self._get_signing_keys(refresh=False)
        key = self._jwks_client.match_kid(keys, kid)
        if key is not None:
            return key

        if not self._forced_refresh_allowed():
            raise jwt.PyJWKClientError(
                "Clé introuvable dans le cache ; rafraîchissement forcé bridé."
            )

        keys = self._get_signing_keys(refresh=True)
        key = self._jwks_client.match_kid(keys, kid)
        if key is None:
            raise jwt.PyJWKClientError("Aucune clé ne correspond au jeton présenté.")
        return key

    def _get_signing_keys(self, *, refresh: bool) -> list[jwt.PyJWK]:
        """Point d'appel unique vers ``PyJWKClient.get_signing_keys``.

        Sérialisé sous ``_jwks_fetch_lock`` (single-flight) : voir le
        commentaire de ce verrou dans ``__init__`` pour la mesure qui motive
        cette sérialisation et l'analyse d'absence d'interblocage avec
        ``_refresh_lock``.
        """
        with self._jwks_fetch_lock:
            return self._jwks_client.get_signing_keys(refresh=refresh)

    def _forced_refresh_allowed(self) -> bool:
        """Autorise au plus un rafraîchissement forcé par intervalle.

        Verrouillé parce que ``_decode`` tourne dans un thread du pool anyio :
        plusieurs requêtes concurrentes portant un ``kid`` inconnu ne doivent
        déclencher qu'un seul aller-retour réseau, quelle que soit la forme de
        l'attaque (un seul ``kid`` répété ou une rafale de ``kid`` distincts).
        L'appel réseau lui-même a lieu hors du verrou, dans
        ``_resolve_signing_key`` : le tenir pendant l'attente réseau
        sérialiserait aussi les requêtes qui n'ont, elles, pas besoin
        d'attendre — il suffit qu'elles constatent le budget déjà consommé.
        """
        now = self._clock()
        with self._refresh_lock:
            allowed = (
                self._last_forced_refresh is None
                or now - self._last_forced_refresh
                >= JWKS_FORCED_REFRESH_INTERVAL_SECONDS
            )
            if allowed:
                self._last_forced_refresh = now
            return allowed

    def _decode(self, token: str) -> dict[str, Any]:
        """Décodage bloquant, exécuté hors de la boucle d'événements."""
        signing_key = self._resolve_signing_key(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=list(self._algorithms),
            audience=self._audience,
            issuer=self._issuer,
            leeway=self._leeway_seconds,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        """Retourne le jeton validé, ou ``None`` si un contrôle échoue."""
        try:
            payload = await anyio.to_thread.run_sync(self._decode, token)
        except jwt.PyJWKClientConnectionError as exc:
            # PyJWKClientConnectionError hérite de PyJWTError (voir
            # jwt.exceptions) : sans cette clause AVANT la suivante, la
            # clause générique ``except jwt.PyJWTError`` l'intercepterait en
            # premier. Une panne réelle de l'émetteur — DNS mort, port
            # fermé, délai dépassé, les trois mesurés en production — serait
            # alors journalisée comme un refus de jeton ordinaire
            # (auth_rejected, INFO), noyant le signal « l'émetteur est
            # tombé » dans le bruit des jetons invalides plutôt que de
            # remonter comme une indisponibilité (WARNING). Le comportement
            # observable ne change pas : verify_token rend toujours None.
            LOGGER.warning("auth_unavailable reason=%s", type(exc).__name__)
            return None
        except jwt.PyJWTError as exc:
            # Le motif est journalisé, jamais le jeton ni sa charge utile.
            LOGGER.info("auth_rejected reason=%s", type(exc).__name__)
            return None
        except Exception as exc:  # panne inattendue (bug, etc.) : prudence
            LOGGER.warning("auth_unavailable reason=%s", type(exc).__name__)
            return None

        subject = str(payload.get("sub", ""))
        if not subject:
            LOGGER.info("auth_rejected reason=MissingSubject")
            return None

        expires_at = payload.get("exp")
        return LegalAccessToken(
            token=token,
            client_id=_client_identifier(payload),
            scopes=_normalise_scopes(payload),
            expires_at=int(expires_at) if isinstance(expires_at, (int, float)) else None,
            resource=self._audience,
            subject=subject,
        )


def principal_of(access_token: AccessToken | None) -> str:
    """Clé de quota : le sujet authentifié, sinon l'application appelante."""
    if access_token is None:
        return "anonyme"
    subject = getattr(access_token, "subject", "")
    if isinstance(subject, str) and subject:
        return subject
    return access_token.client_id or "anonyme"


def scopes_from_env_value(raw: str | None, default: Iterable[str]) -> list[str]:
    """Découpe une liste de portées écrite avec des virgules ou des espaces."""
    if raw is None or not raw.strip():
        return list(default)
    separators = "," if "," in raw else " "
    return [item.strip() for item in raw.split(separators) if item.strip()]
