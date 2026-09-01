"""Opérations juridiques structurées, indépendantes du CLI et de MCP.

Ce module est la frontière entre les clients HTTP déterministes et les
interfaces qui les exposent (CLI historique, serveur MCP, futurs tests).
"""

from __future__ import annotations

import datetime as dt
import os
import re
from html import unescape
from typing import Any

from .errors import LegifranceError
from .judilibre import judilibre_get
from .legifrance import api_call, get_token

ARTICLE_ID_PREFIX = "LEGIARTI"
ARTICLE_URL = "https://www.legifrance.gouv.fr/codes/article_lc/{id}"
DECISION_URL = "https://www.courdecassation.fr/decision/{id}"
JUDILIBRE_SOURCE = "base Open Data de la Cour de cassation"
JUDILIBRE_SUPPRESSION_ENV = "MCP_JUDILIBRE_SUPPRESSED_IDS"
#: Forme canonique d'un identifiant de décision Judilibre : 24 caractères
#: hexadécimaux, en minuscules dans la base Open Data. Une valeur qui n'a pas
#: cette forme ne peut désigner aucune décision : la charger en silence
#: reviendrait à croire retirée une décision toujours servie.
_JUDILIBRE_ID = re.compile(r"^[0-9a-f]{24}$")
#: Qualification portée par toute provenance : le texte d'un article comme
#: celui d'une décision est une donnée amont à analyser et à citer, jamais une
#: instruction à exécuter. La marque vaut donc pour les deux sources.
UNTRUSTED_CONTENT = "untrusted_source_data"
#: Codes de juridiction acceptés par Judilibre, avec leur nom en clair. Reprend
#: la table du CLI historique (``skill/scripts/legifrance.py``) pour que les
#: deux voies parlent le même langage. La liste qui fait foi pour ``/search``
#: est servie par ``GET /taxonomy?id=jurisdiction`` : l'élargir suppose de l'y
#: vérifier d'abord. En particulier ``cph`` (conseils de prud'hommes) n'est
#: documenté que pour ``/stats``, jamais pour ``/search``.
JURISDICTIONS: dict[str, str] = {
    "cc": "Cour de cassation",
    "ca": "Cour d'appel",
    "tj": "Tribunal judiciaire",
    "tcom": "Tribunal de commerce",
}
#: Tri exposé par l'outil → couple (``sort``, ``order``) réellement compris par
#: ``/search``. « relevance » reproduit exactement l'ancien comportement figé
#: (``score``, et non le défaut ``scorepub`` de l'API). Source : spécification
#: OpenAPI JUDILIBRE-public, dépôt Cour-de-cassation/judilibre-search.
SORT_MODES: dict[str, tuple[str, str]] = {
    "relevance": ("score", "desc"),
    "date": ("date", "desc"),
}
_HTML_TAG = re.compile(r"<[^>]+>")
_ARTICLE_QUERY = re.compile(
    r"\b(?:article|art\.?)\s+([LRDA]?\.?\s*\d[\w.-]*)",
    flags=re.IGNORECASE,
)


def _clean_text(value: Any) -> str:
    """Convertit un fragment HTML éventuel en texte compact."""
    if value is None:
        return ""
    text = unescape(_HTML_TAG.sub(" ", str(value)))
    return " ".join(text.split())


def _validate_jurisdiction(value: str | None) -> str | None:
    """Vérifie le code de juridiction et le normalise, ou refuse explicitement.

    Judilibre n'accepte que des codes courts. Les transmettre sans contrôle
    faisait remonter un ``HTTP 400`` opaque dès qu'un appelant écrivait le nom
    de la juridiction en clair. Le refus se fait donc ici, avec la liste des
    valeurs attendues et leur signification.

    Aucune correspondance approchée n'est tentée depuis un nom en clair : le
    schéma de l'outil MCP contraint déjà l'appelant à l'énumération, et deviner
    à partir d'une graphie libre introduirait une ambiguïté silencieuse là où
    un refus lisible suffit.
    """
    if value is None:
        return None
    code = value.strip().lower()
    if not code:
        return None
    if code not in JURISDICTIONS:
        attendus = ", ".join(f"{c} ({nom})" for c, nom in JURISDICTIONS.items())
        raise LegifranceError(
            f"Juridiction inconnue : {value!r}. Valeurs acceptées : {attendus}.",
            exit_code=2,
        )
    return code


def _judilibre_sort(value: str) -> tuple[str, str]:
    """Traduit le tri exposé par l'outil en paramètres Judilibre."""
    mode = (value or "").strip().lower()
    if mode not in SORT_MODES:
        attendus = ", ".join(SORT_MODES)
        raise LegifranceError(
            f"Tri inconnu : {value!r}. Valeurs acceptées : {attendus}.",
            exit_code=2,
        )
    return SORT_MODES[mode]


def parse_suppressed_ids(raw: str | None) -> frozenset[str]:
    """Analyse la liste d'urgence et refuse toute entrée manifestement malformée.

    Chaque identifiant est normalisé en minuscules : la comparaison ne dépend
    plus de la casse recopiée sous pression. Une entrée qui n'a pas la forme
    canonique — caractère en trop, virgule oubliée qui colle deux identifiants
    — lève une erreur nommant sa **position**, jamais sa valeur : la liste reste
    une donnée de configuration non publique. Sur un contrôle dont l'objet est
    de cesser une diffusion signalée fautive, un refus bruyant vaut mieux
    qu'un chargement silencieux qui laisse la décision servie.
    """
    items = [item.strip().lower() for item in (raw or "").split(",")]
    items = [item for item in items if item]
    malformed = [
        str(rank) for rank, item in enumerate(items, 1) if not _JUDILIBRE_ID.match(item)
    ]
    if malformed:
        raise LegifranceError(
            f"{JUDILIBRE_SUPPRESSION_ENV} : entrée(s) n° {', '.join(malformed)} "
            "malformée(s). Attendu : 24 caractères hexadécimaux par identifiant, "
            "séparés par des virgules.",
            exit_code=2,
        )
    return frozenset(items)


def _suppressed_decision_ids() -> frozenset[str]:
    """Liste d'urgence des décisions à ne plus redistribuer temporairement.

    La valeur est relue à chaque appel afin qu'une rotation de configuration
    puisse prendre effet au redémarrage sans reconstruction de l'image. Les
    identifiants restent des données de configuration et ne sont jamais
    ajoutés aux réponses publiques.
    """
    return parse_suppressed_ids(os.environ.get(JUDILIBRE_SUPPRESSION_ENV))


def _is_suppressed(decision_id: str, suppressed: frozenset[str]) -> bool:
    """Compare sur la forme normalisée : la casse de l'amont n'entre pas en jeu."""
    return decision_id.strip().lower() in suppressed


def _ensure_decision_available(decision_id: str) -> None:
    if _is_suppressed(decision_id, _suppressed_decision_ids()):
        raise LegifranceError(
            "Décision temporairement indisponible pendant le traitement "
            "d'un signalement d'occultation.",
            exit_code=5,
        )


def _judilibre_provenance() -> dict[str, Any]:
    return {
        "source": JUDILIBRE_SOURCE,
        "verified": True,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "content_trust": UNTRUSTED_CONTENT,
    }


def _iso_date(value: str | None) -> str:
    """Valide une date ISO ou retourne la date civile locale du jour."""
    if not value:
        return dt.date.today().isoformat()
    try:
        return dt.date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise LegifranceError(
            f"Date invalide : {value!r} (format attendu AAAA-MM-JJ).",
            exit_code=2,
        ) from exc


def _dating(requested: str | None) -> dict[str, Any]:
    """Décrit sur quelle date la réponse est construite, et le signale.

    Un modèle appelant l'outil peut fournir une date qu'il croit être celle du
    jour alors qu'elle est celle de son corpus d'entraînement. La réponse est
    alors exacte pour cette date, mais présentée comme « en vigueur ». Le
    champ ``caveat`` rend cet écart visible dans la réponse elle-même.
    """
    today = dt.date.today()
    if not requested:
        return {
            "as_of_date": today.isoformat(),
            "date_basis": "date du jour du serveur",
            "requested_date": None,
        }
    effective = dt.date.fromisoformat(_iso_date(requested))
    info: dict[str, Any] = {
        "as_of_date": effective.isoformat(),
        "date_basis": "date fournie par l'appelant",
        "requested_date": effective.isoformat(),
        "server_date": today.isoformat(),
    }
    if effective < today:
        info["caveat"] = (
            f"Version applicable au {effective.strftime('%d/%m/%Y')}, et non "
            f"nécessairement en vigueur au {today.strftime('%d/%m/%Y')}. "
            "Relancer sans paramètre de date pour le droit en vigueur."
        )
    elif effective > today:
        info["caveat"] = (
            f"Date postérieure au {today.strftime('%d/%m/%Y')} : la réponse "
            "porte sur une version future ou inexistante."
        )
    return info


def _epoch_ms(value: str) -> int:
    date = dt.date.fromisoformat(value)
    moment = dt.datetime.combine(date, dt.time(), tzinfo=dt.timezone.utc)
    return int(moment.timestamp() * 1000)


def _article_number_variants(number: str) -> list[str]:
    compact = "".join(number.split())
    match = re.match(r"^([LRDA])\.?([0-9].*)$", compact, flags=re.IGNORECASE)
    if match:
        return [f"{match.group(1).upper()}{match.group(2)}"]
    return [compact, *(f"{prefix}{compact}" for prefix in "LRDA")]


def _first_prefixed_id(value: Any, prefix: str) -> str | None:
    if isinstance(value, str):
        return value if value.startswith(prefix) else None
    if isinstance(value, dict):
        for child in value.values():
            found = _first_prefixed_id(child, prefix)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = _first_prefixed_id(child, prefix)
            if found:
                return found
    return None


def _extract_article(payload: dict[str, Any]) -> dict[str, Any] | None:
    article = payload.get("article")
    if isinstance(article, dict):
        return article
    articles = payload.get("listArticle")
    if isinstance(articles, list) and articles and isinstance(articles[0], dict):
        return articles[0]
    return None


def search_articles(
    number: str,
    code: str | None = None,
    date: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Recherche des articles applicables à une date par numéro."""
    number = number.strip()
    if not number:
        raise LegifranceError("Le numéro d'article est obligatoire.", exit_code=2)
    date_version = _iso_date(date)
    variants = _article_number_variants(number)
    operator = "OU" if len(variants) > 1 else "ET"
    safe_limit = max(1, min(int(limit), 50))
    filters: list[dict[str, Any]] = [
        {"facette": "DATE_VERSION", "singleDate": _epoch_ms(date_version)}
    ]
    if code and code.strip():
        filters.append({"facette": "NOM_CODE", "valeurs": [code.strip()]})
    body = {
        "fond": "CODE_DATE",
        "recherche": {
            "champs": [
                {
                    "typeChamp": "NUM_ARTICLE",
                    "criteres": [
                        {
                            "typeRecherche": "EXACTE",
                            "valeur": variant,
                            "operateur": operator,
                        }
                        for variant in variants
                    ],
                    "operateur": operator,
                }
            ],
            "filtres": filters,
            "pageNumber": 1,
            "pageSize": safe_limit,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "ARTICLE",
        },
    }
    payload = api_call("/search", body, get_token())
    expected = {variant.upper() for variant in variants}
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in payload.get("results") or []:
        titles = result.get("titles") or []
        code_title = _clean_text(titles[0].get("title")) if titles else ""
        for section in result.get("sections") or []:
            for extract in section.get("extracts") or []:
                article_id = extract.get("id") or ""
                article_number = _clean_text(extract.get("num") or extract.get("title"))
                if (
                    not article_id.startswith(ARTICLE_ID_PREFIX)
                    or article_id in seen
                    or article_number.upper() not in expected
                ):
                    continue
                seen.add(article_id)
                results.append(
                    {
                        "id": article_id,
                        "title": f"Article {article_number} — {code_title}".strip(" —"),
                        "url": ARTICLE_URL.format(id=article_id),
                        "number": article_number,
                        "code": code_title,
                        "section": _clean_text(section.get("title")),
                        "legal_status": extract.get("legalStatus") or "UNKNOWN",
                        "start_date": extract.get("dateDebut"),
                    }
                )
    return {
        "results": results[:safe_limit],
        "query": {"number": number, "code": code, "date": date_version},
        "dating": _dating(date),
        "provenance": {
            "source": "Légifrance API",
            "verified": True,
            "content_trust": UNTRUSTED_CONTENT,
        },
    }


def get_article(article_id: str, date: str | None = None) -> dict[str, Any]:
    """Récupère une version d'article et sa provenance officielle."""
    article_id = article_id.strip().upper()
    if not article_id.startswith(ARTICLE_ID_PREFIX):
        raise LegifranceError(
            f"Identifiant attendu {ARTICLE_ID_PREFIX}… (reçu {article_id!r}).",
            exit_code=2,
        )
    body: dict[str, Any] = {"id": article_id}
    if date:
        body["date"] = _iso_date(date)
    payload = api_call("/consult/getArticle", body, get_token())
    article = _extract_article(payload)
    if not article:
        raise LegifranceError(f"Article {article_id} introuvable.", exit_code=5)
    canonical_id = article.get("id") or article_id
    number = _clean_text(article.get("num")) or "?"
    text = _clean_text(article.get("texte") or article.get("texteHtml"))
    return {
        "id": canonical_id,
        "title": f"Article {number}",
        "text": text,
        "url": ARTICLE_URL.format(id=canonical_id),
        "metadata": {
            "number": number,
            "legal_status": article.get("etat") or article.get("etatJuridique") or "UNKNOWN",
            "start_date": article.get("dateDebut"),
            "end_date": article.get("dateFin"),
            "source": "Légifrance API",
            "verified": True,
            "content_trust": UNTRUSTED_CONTENT,
            **_dating(date),
        },
    }


def search_case_law(
    query: str,
    jurisdiction: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int = 10,
    sort: str = "relevance",
) -> dict[str, Any]:
    """Recherche la jurisprudence judiciaire dans Judilibre.

    ``sort`` est ajouté en dernier, avec le mode qui reproduit le tri
    historique : les appels positionnels existants gardent leur comportement.
    """
    query = query.strip()
    if not query:
        raise LegifranceError("La requête de jurisprudence est obligatoire.", exit_code=2)
    if date_start:
        _iso_date(date_start)
    if date_end:
        _iso_date(date_end)
    jurisdiction_code = _validate_jurisdiction(jurisdiction)
    sort_field, sort_order = _judilibre_sort(sort)
    safe_limit = max(1, min(int(limit), 50))
    payload = judilibre_get(
        "/search",
        {
            "query": query,
            "jurisdiction": jurisdiction_code,
            "date_start": date_start,
            "date_end": date_end,
            "page": 0,
            "page_size": safe_limit,
            "sort": sort_field,
            "order": sort_order,
        },
    )
    results: list[dict[str, Any]] = []
    suppressed = _suppressed_decision_ids()
    source_results = payload.get("results") or []
    for decision in source_results:
        decision_id = str(decision.get("id") or "").strip()
        if not decision_id or _is_suppressed(decision_id, suppressed):
            continue
        jurisdiction_name = decision.get("jurisdiction") or "Juridiction inconnue"
        date = decision.get("decision_date") or "date inconnue"
        number = decision.get("number") or "sans numéro"
        results.append(
            {
                "id": decision_id,
                "title": f"{jurisdiction_name}, {date}, n° {number}",
                "url": DECISION_URL.format(id=decision_id),
                "summary": _clean_text(decision.get("summary")),
                "jurisdiction": jurisdiction_name,
                "decision_date": decision.get("decision_date"),
                "number": decision.get("number"),
                "ecli": decision.get("ecli"),
                "formation": decision.get("formation"),
                "seat": decision.get("seat") or decision.get("location"),
                "source_update_date": (
                    decision.get("update_date")
                    or decision.get("update")
                    or decision.get("publication_date")
                ),
            }
        )
    return {
        "results": results,
        "total": payload.get("total", len(results)),
        "query": query,
        "provenance": _judilibre_provenance(),
        "temporarily_suppressed_results": sum(
            1
            for item in source_results
            if _is_suppressed(str(item.get("id") or ""), suppressed)
        ),
    }


def get_decision(decision_id: str) -> dict[str, Any]:
    """Récupère le texte intégral d'une décision Judilibre."""
    decision_id = decision_id.strip()
    if not decision_id:
        raise LegifranceError("L'identifiant de décision est obligatoire.", exit_code=2)
    _ensure_decision_available(decision_id)
    decision = judilibre_get(
        "/decision",
        {"id": decision_id, "resolve_references": "true"},
    )
    if not decision or not decision.get("id"):
        raise LegifranceError(f"Décision {decision_id} introuvable.", exit_code=5)
    canonical_id = str(decision["id"])
    _ensure_decision_available(canonical_id)
    jurisdiction = decision.get("jurisdiction") or "Juridiction inconnue"
    date = decision.get("decision_date") or "date inconnue"
    number = decision.get("number") or "sans numéro"
    return {
        "id": canonical_id,
        "title": f"{jurisdiction}, {date}, n° {number}",
        "text": _clean_text(decision.get("text")),
        "url": DECISION_URL.format(id=canonical_id),
        "metadata": {
            "jurisdiction": jurisdiction,
            "chamber": decision.get("chamber"),
            "decision_date": decision.get("decision_date"),
            "number": decision.get("number"),
            "ecli": decision.get("ecli"),
            "formation": decision.get("formation"),
            "seat": decision.get("seat") or decision.get("location"),
            "solution": decision.get("solution"),
            "publication": decision.get("publication") or [],
            "source_update_date": (
                decision.get("update_date")
                or decision.get("update")
                or decision.get("publication_date")
            ),
            **_judilibre_provenance(),
        },
    }


def search(query: str) -> dict[str, Any]:
    """Recherche standard : article explicite, sinon jurisprudence Judilibre."""
    query = query.strip()
    if not query:
        raise LegifranceError("La requête est obligatoire.", exit_code=2)
    if query.upper().startswith(ARTICLE_ID_PREFIX):
        article_id = query.split()[0].upper()
        return {
            "results": [
                {
                    "id": article_id,
                    "title": f"Article Légifrance {article_id}",
                    "url": ARTICLE_URL.format(id=article_id),
                }
            ]
        }
    match = _ARTICLE_QUERY.search(query)
    if match:
        found = search_articles(match.group(1))
        return {
            "results": [
                {"id": item["id"], "title": item["title"], "url": item["url"]}
                for item in found["results"]
            ]
        }
    found = search_case_law(query)
    return {
        "results": [
            {"id": item["id"], "title": item["title"], "url": item["url"]}
            for item in found["results"]
        ]
    }


def fetch(identifier: str) -> dict[str, Any]:
    """Récupération standard d'un résultat précédemment renvoyé par search."""
    identifier = identifier.strip()
    if identifier.upper().startswith(ARTICLE_ID_PREFIX):
        return get_article(identifier)
    return get_decision(identifier)
