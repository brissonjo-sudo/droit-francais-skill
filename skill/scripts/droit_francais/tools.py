"""Opérations juridiques structurées, indépendantes du CLI et de MCP.

Ce module est la frontière entre les clients HTTP déterministes et les
interfaces qui les exposent (CLI historique, serveur MCP, futurs tests).
"""

from __future__ import annotations

import datetime as dt
import re
from html import unescape
from typing import Any

from .errors import LegifranceError
from .judilibre import judilibre_get
from .legifrance import api_call, get_token

ARTICLE_ID_PREFIX = "LEGIARTI"
ARTICLE_URL = "https://www.legifrance.gouv.fr/codes/article_lc/{id}"
DECISION_URL = "https://www.courdecassation.fr/decision/{id}"
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
        "provenance": {"source": "Légifrance API", "verified": True},
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
            "requested_date": date,
            "source": "Légifrance API",
            "verified": True,
        },
    }


def search_case_law(
    query: str,
    jurisdiction: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Recherche la jurisprudence judiciaire dans Judilibre."""
    query = query.strip()
    if not query:
        raise LegifranceError("La requête de jurisprudence est obligatoire.", exit_code=2)
    if date_start:
        _iso_date(date_start)
    if date_end:
        _iso_date(date_end)
    safe_limit = max(1, min(int(limit), 50))
    payload = judilibre_get(
        "/search",
        {
            "query": query,
            "jurisdiction": jurisdiction,
            "date_start": date_start,
            "date_end": date_end,
            "page": 0,
            "page_size": safe_limit,
            "sort": "score",
            "order": "desc",
        },
    )
    results: list[dict[str, Any]] = []
    for decision in payload.get("results") or []:
        decision_id = str(decision.get("id") or "").strip()
        if not decision_id:
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
            }
        )
    return {
        "results": results,
        "total": payload.get("total", len(results)),
        "query": query,
        "provenance": {"source": "Judilibre API", "verified": True},
    }


def get_decision(decision_id: str) -> dict[str, Any]:
    """Récupère le texte intégral d'une décision Judilibre."""
    decision_id = decision_id.strip()
    if not decision_id:
        raise LegifranceError("L'identifiant de décision est obligatoire.", exit_code=2)
    decision = judilibre_get(
        "/decision",
        {"id": decision_id, "resolve_references": "true"},
    )
    if not decision or not decision.get("id"):
        raise LegifranceError(f"Décision {decision_id} introuvable.", exit_code=5)
    canonical_id = str(decision["id"])
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
            "solution": decision.get("solution"),
            "publication": decision.get("publication") or [],
            "source": "Judilibre API",
            "verified": True,
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
