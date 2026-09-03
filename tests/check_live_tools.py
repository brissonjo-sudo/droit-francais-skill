#!/usr/bin/env python3
"""Valide les six outils contre le service déployé, avec un vrai jeton.

Cette sonde couvre la part automatisable de la validation de bout en bout :
découverte puis appel des six outils, lectures avec texte et provenance
officielle, datation explicite, absence non inventée et contrôle anti-secret.
Elle ne remplace pas le parcours ChatGPT — seul celui-ci prouve qu'un
utilisateur peut se connecter — mais elle en retire tout ce qui n'a pas besoin
d'un navigateur.

Le jeton est lu dans la variable d'environnement ``MCP_ACCESS_TOKEN`` et n'est
jamais affiché, ni journalisé, ni écrit. Il n'est pas accepté en argument de
ligne de commande, qui serait visible dans l'historique du shell et dans la
liste des processus.

    export MCP_ACCESS_TOKEN="…"
    python tests/check_live_tools.py https://droit-francais-skill.onrender.com/mcp

Attention : cette sonde consomme le quota PISTE du titulaire des clés, comme
n'importe quel appel réel.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_server.catalog import EXPECTED_TOOLS  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

#: Noms de variables dont la valeur ne doit jamais apparaître dans une réponse.
VARIABLES_FOURNISSEUR = (
    "LEGIFRANCE_CLIENT_ID",
    "LEGIFRANCE_CLIENT_SECRET",
    "JUDILIBRE_KEY_ID",
    "PISTE_KEY_ID",
)
VARIABLES_SENSIBLES = (*VARIABLES_FOURNISSEUR, "MCP_ACCESS_TOKEN")

#: Article stable, choisi pour ne pas dépendre d'une réforme récente.
ARTICLE_TEMOIN = "L2212-2"
CODE_TEMOIN = "Code général des collectivités territoriales"


class SondeError(RuntimeError):
    """Défaut constaté, formulé sans recopier de valeur sensible."""


def _attribut(objet, *noms):
    """Lit le premier attribut présent : le SDK v1 et le v2 les nomment différemment."""
    for nom in noms:
        valeur = getattr(objet, nom, None)
        if valeur is not None:
            return valeur
    return None


def _texte(resultat) -> str:
    """Rendu textuel d'un résultat d'outil, structuré et non structuré confondus."""
    morceaux = [str(_attribut(resultat, "structured_content", "structuredContent"))]
    for element in getattr(resultat, "content", None) or []:
        morceaux.append(str(getattr(element, "text", element)))
    return "\n".join(morceaux)


def _exiger_succes(resultat, quoi: str):
    if _attribut(resultat, "is_error", "isError"):
        # Ne jamais recopier une erreur distante : une régression pourrait y
        # réexposer une clé fournisseur ou le bearer utilisé par la sonde.
        raise SondeError(f"{quoi} a échoué ; détail distant volontairement masqué")
    charge = _attribut(resultat, "structured_content", "structuredContent")
    if charge is None:
        raise SondeError(f"{quoi} n'a renvoyé aucun contenu structuré")
    return charge


def _exiger_provenance(charge: dict, source: str, quoi: str) -> None:
    provenance = charge.get("provenance") or {}
    if provenance.get("source") != source or provenance.get("verified") is not True:
        raise SondeError(f"{quoi} ne porte pas une provenance officielle vérifiée")


def _exiger_lecture_officielle(
    charge: dict,
    identifiant: str,
    source: str,
    hote: str,
    quoi: str,
) -> dict:
    """Valide le contrat minimal d'une lecture, sans prétendre à l'exhaustivité."""
    if charge.get("id") != identifiant or not str(charge.get("text") or "").strip():
        raise SondeError(f"{quoi} n'a pas rendu l'identifiant et un texte non vide")
    url = urlparse(str(charge.get("url") or ""))
    if url.scheme != "https" or url.hostname != hote:
        raise SondeError(f"{quoi} ne porte pas l'URL officielle attendue")
    metadonnees = charge.get("metadata") or {}
    if metadonnees.get("source") != source or metadonnees.get("verified") is not True:
        raise SondeError(f"{quoi} ne porte pas une provenance officielle vérifiée")
    return metadonnees


def _exiger_absence_reussie(resultat, quoi: str) -> dict:
    """Une absence n'est prouvée que par un succès structuré sans résultat."""
    charge = _exiger_succes(resultat, quoi)
    resultats = charge.get("results")
    if not isinstance(resultats, list):
        raise SondeError(f"{quoi} n'a pas rendu la liste de résultats attendue")
    if resultats:
        raise SondeError(f"{quoi} a produit un résultat inattendu")
    return charge


def _verifier_absence_de_secrets(rendu: str, quoi: str) -> None:
    """Aucune valeur de clé fournisseur ne doit transiter vers le client.

    Le contrôle porte sur la *valeur* des variables, pas sur leur nom : c'est la
    fuite qui compte. Les variables absentes de l'environnement local sont
    ignorées — la sonde ne peut alors rien affirmer et le dit.
    """
    non_verifiables = []
    for nom in VARIABLES_SENSIBLES:
        valeur = os.environ.get(nom, "").strip()
        if not valeur:
            if nom in VARIABLES_FOURNISSEUR:
                non_verifiables.append(nom)
            continue
        if valeur in rendu:
            raise SondeError(f"{quoi} : la valeur de {nom} apparaît dans la réponse")
    if non_verifiables:
        print(
            f"   ⚠️  {len(non_verifiables)}/{len(VARIABLES_FOURNISSEUR)} valeur(s) "
            "de clé fournisseur absente(s) localement : comparaison partielle"
        )


async def _verifier_le_jeton(client: httpx2.AsyncClient, url: str) -> None:
    """Refus d'authentification annonce avant l'ouverture de session.

    Sans ce controle, un jeton refuse remonte sous la forme d'un
    ``ExceptionGroup`` du groupe de taches du client, qui ne dit rien de la
    cause reelle.
    """
    reponse = await client.post(
        url,
        json={"jsonrpc": "2.0", "id": 0, "method": "tools/list"},
        headers={"Accept": "application/json, text/event-stream"},
    )
    if reponse.status_code == 401:
        raise SondeError(
            "jeton refuse (401). Verifier qu'il est signe par l'emetteur "
            "configure, non expire, et emis pour l'audience du serveur MCP."
        )
    if reponse.status_code == 403:
        raise SondeError(
            "jeton valide mais portee insuffisante (403). Verifier "
            "MCP_OAUTH_REQUIRED_SCOPES et les portees portees par le jeton."
        )


async def sonder(url: str, token: str) -> None:
    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {token}"}, timeout=90
    ) as client:
        await _verifier_le_jeton(client, url)
        async with streamable_http_client(url, http_client=client) as (
            reader,
            writer,
            *_,
        ):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                appeles: set[str] = set()

                async def appeler(nom: str, arguments: dict) -> tuple[object, float]:
                    """Appelle, chronomètre et consigne un outil sans exposer le jeton."""
                    debut = time.perf_counter()
                    resultat = await session.call_tool(nom, arguments)
                    appeles.add(nom)
                    return resultat, time.perf_counter() - debut

                # ---- 1. Découverte des outils -----------------------------
                listes = await session.list_tools()
                noms = {outil.name for outil in listes.tools}
                if noms != set(EXPECTED_TOOLS):
                    raise SondeError(
                        f"outils inattendus : {sorted(noms)} "
                        f"(attendus : {sorted(EXPECTED_TOOLS)})"
                    )
                for outil in listes.tools:
                    annotations = outil.annotations
                    lecture = _attribut(annotations, "readOnlyHint", "read_only_hint")
                    ouvert = _attribut(annotations, "openWorldHint", "open_world_hint")
                    destructif = _attribut(
                        annotations, "destructiveHint", "destructive_hint"
                    )
                    if (lecture, ouvert, destructif) != (True, False, False):
                        raise SondeError(
                            f"annotations de sécurité invalides pour {outil.name}"
                        )
                print("✅ Six outils découverts, tous annotés en lecture seule.")

                # ---- 2. Appel Légifrance réel -----------------------------
                resultat, latence_legifrance = await appeler(
                    "search_articles",
                    {"number": ARTICLE_TEMOIN, "code": CODE_TEMOIN, "limit": 5},
                )
                charge = _exiger_succes(resultat, "search_articles")
                _verifier_absence_de_secrets(_texte(resultat), "search_articles")
                resultats = charge.get("results") or []
                if not resultats:
                    raise SondeError(
                        f"aucun résultat pour l'article {ARTICLE_TEMOIN} : "
                        "source officielle non vérifiée"
                    )
                article = resultats[0]
                identifiant = str(article.get("id", ""))
                if not identifiant.startswith("LEGIARTI"):
                    raise SondeError(f"identifiant Légifrance inattendu : {identifiant}")
                _exiger_provenance(charge, "Légifrance API", "search_articles")
                print(
                    f"✅ Légifrance : {identifiant} — statut "
                    f"{article.get('legal_status', 'inconnu')} — premier appel "
                    f"{latence_legifrance:.3f} s"
                )

                # ---- 3. Lecture datée de l'article ------------------------
                resultat, _ = await appeler("get_article", {"id": identifiant})
                charge = _exiger_succes(resultat, "get_article")
                _verifier_absence_de_secrets(_texte(resultat), "get_article")
                metadonnees = _exiger_lecture_officielle(
                    charge,
                    identifiant,
                    "Légifrance API",
                    "www.legifrance.gouv.fr",
                    "get_article",
                )
                for champ in ("as_of_date", "date_basis"):
                    if not metadonnees.get(champ):
                        raise SondeError(
                            f"la réponse n'est pas datée explicitement : {champ} absent"
                        )
                print(
                    f"✅ Datation explicite : {metadonnees['as_of_date']} "
                    f"({metadonnees['date_basis']})"
                )

                # ---- 4. Appel Judilibre réel ------------------------------
                resultat, latence_judilibre = await appeler(
                    "search_case_law",
                    {"query": "responsabilité du fait des choses", "limit": 5},
                )
                charge = _exiger_succes(resultat, "search_case_law")
                _verifier_absence_de_secrets(_texte(resultat), "search_case_law")
                decisions = charge.get("results") or []
                if not decisions:
                    raise SondeError(
                        "aucune décision Judilibre : source officielle non vérifiée"
                    )
                decision = decisions[0]
                _exiger_provenance(
                    charge,
                    "base Open Data de la Cour de cassation",
                    "search_case_law",
                )
                print(
                    f"✅ Judilibre : {decision.get('id')} — "
                    f"{decision.get('jurisdiction')} {decision.get('decision_date')} — "
                    f"premier appel {latence_judilibre:.3f} s"
                )

                # ---- 5. Lecture de la décision ----------------------------
                decision_id = str(decision.get("id", ""))
                resultat, _ = await appeler("get_decision", {"id": decision_id})
                charge = _exiger_succes(resultat, "get_decision")
                _verifier_absence_de_secrets(_texte(resultat), "get_decision")
                metadonnees_decision = _exiger_lecture_officielle(
                    charge,
                    decision_id,
                    "base Open Data de la Cour de cassation",
                    "www.courdecassation.fr",
                    "get_decision",
                )
                if not metadonnees_decision.get("decision_date"):
                    raise SondeError("get_decision ne porte pas la date de décision")
                print("✅ get_decision : texte et provenance officielle présents.")

                # ---- 6. Parcours standard search → fetch ------------------
                resultat, _ = await appeler(
                    "search", {"query": f"article {ARTICLE_TEMOIN}"}
                )
                charge = _exiger_succes(resultat, "search")
                _verifier_absence_de_secrets(_texte(resultat), "search")
                resultats_standards = charge.get("results") or []
                if not resultats_standards:
                    raise SondeError("search n'a renvoyé aucun identifiant à transmettre à fetch")
                identifiant_standard = str(resultats_standards[0].get("id", ""))
                if not identifiant_standard.startswith("LEGIARTI"):
                    raise SondeError("search n'a pas rendu un identifiant Légifrance")
                resultat, _ = await appeler("fetch", {"id": identifiant_standard})
                charge = _exiger_succes(resultat, "fetch")
                _verifier_absence_de_secrets(_texte(resultat), "fetch")
                _exiger_lecture_officielle(
                    charge,
                    identifiant_standard,
                    "Légifrance API",
                    "www.legifrance.gouv.fr",
                    "fetch",
                )
                print("✅ search → fetch : parcours standard complet et traçable.")

                # ---- 7. Comportement en cas d'absence ---------------------
                resultat, _ = await appeler(
                    "search_articles",
                    {"number": "L9999-1", "code": CODE_TEMOIN, "limit": 5},
                )
                rendu = _texte(resultat)
                _verifier_absence_de_secrets(rendu, "article inexistant")
                _exiger_absence_reussie(resultat, "article inexistant")
                print("✅ Article inexistant : absence signalée, rien d'inventé.")

                if appeles != set(EXPECTED_TOOLS):
                    raise SondeError(
                        f"outils non réellement appelés : {sorted(set(EXPECTED_TOOLS) - appeles)}"
                    )
                print("✅ Les six outils ont chacun été réellement appelés.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valide les six outils contre le service déployé"
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://droit-francais-skill.onrender.com/mcp",
        help="URL complète du endpoint MCP.",
    )
    args = parser.parse_args()

    token = os.environ.get("MCP_ACCESS_TOKEN", "").strip()
    if not token:
        print(
            "❌ MCP_ACCESS_TOKEN est vide.\n"
            "   Exporter un jeton d'accès valide pour l'audience du serveur :\n"
            '   export MCP_ACCESS_TOKEN="…"\n'
            "   Le jeton n'est jamais affiché ni écrit par cette sonde."
        )
        return 2

    try:
        asyncio.run(sonder(args.url, token))
    except SondeError as exc:
        print(f"❌ {exc}")
        return 1
    except Exception as exc:  # transport, réseau, refus d'authentification
        # Le texte d'une exception de transport peut inclure des en-têtes.
        print(f"❌ {type(exc).__name__} ; détail technique volontairement masqué")
        return 1

    print("\n✅ Sonde complète des six outils validée contre la production.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
