"""Consultations datées de sections CODE et de textes consolidés LEGI.

Contrat PISTE Légifrance 2.4.2 : CodeConsultRequest, LegiConsultRequest,
ConsultTextResponse, ConsultSection et ConsultArticle. Aucun URL fourni par
l'appelant, aucune récupération secondaire ou substitution de version.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any

from .errors import LegifranceError
from .legifrance import api_call, get_token
from .tools import UNTRUSTED_CONTENT, _article_dating, _clean_text, _iso_date

MAX_NODES = 5000
MAX_DEPTH = 32
MAX_RESPONSE_BYTES = 2_000_000
_TEXT_ID = re.compile(r"LEGITEXT[0-9]{12}\Z")
_SECTION_ID = re.compile(r"LEGISCTA[0-9]{12}\Z")
_ARTICLE_ID = re.compile(r"LEGIARTI[0-9]{12}\Z")
_VERSION_ID = re.compile(r"(LEGITEXT[0-9]{12})(?:_([0-9]{2}-[0-9]{2}-[0-9]{4}))?\Z")
_SECTION_NOTES = (
    "commentaire",
    "renvoi",
    "renvoiNum",
    "notaHtml",
    "notaSectionsAafficher",
)
_ARTICLE_NOTES = (
    "surtitre",
    "nota",
    "renvoi",
    "conditionDiffere",
    "infosComplementaires",
    "infosComplementairesHtml",
    "infosRestructurationBranche",
    "infosRestructurationBrancheHtml",
    "notaSectionsAafficher",
)
_TEXT_NOTES = (
    "visa",
    "nota",
    "notice",
    "signers",
    "rectificatif",
    "observations",
    "prepWork",
)


def _fail(message: str) -> None:
    raise LegifranceError(message, exit_code=5)


def _identifier(value: str, pattern: re.Pattern[str], label: str) -> str:
    normalized = value.strip().upper()
    if not pattern.fullmatch(normalized):
        raise LegifranceError(
            f"Identifiant {label} suivi de 12 chiffres attendu.", exit_code=2
        )
    return normalized


def _consult_date(value: str | None) -> str:
    if value is not None and not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise LegifranceError(
            "Date de consultation attendue au format AAAA-MM-JJ.", exit_code=2
        )
    return _iso_date(value)


def _children(node: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = node.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        _fail(f"Schéma de consultation invalide : {key} n'est pas une liste d'objets.")
    return value


def _notes(node: dict[str, Any], fields: tuple[str, ...]) -> dict[str, str]:
    notes = {}
    for field in fields:
        value = node.get(field)
        if value is None:
            continue
        if isinstance(value, list):
            if any(not isinstance(item, str) for item in value):
                _fail("Schéma des notes de consultation invalide.")
            value = "\n".join(value)
        if not isinstance(value, str):
            _fail("Schéma du contenu de consultation invalide.")
        cleaned = _clean_text(value)
        if cleaned:
            notes[field] = cleaned
    return notes


def _metadata(
    node: dict[str, Any], date: str | None, *, root: bool = False
) -> dict[str, Any]:
    start = node.get("dateDebutVersion" if root else "dateDebut")
    end = node.get("dateFinVersion" if root else "dateFin")
    parsed = []
    malformed = False
    for value in (start, end):
        try:
            if not isinstance(value, str):
                raise ValueError("Borne de version non textuelle.")
            # Accepter une date ISO ou un horodatage ISO, pas un préfixe
            # ressemblant à une date suivi d'un contenu arbitraire.
            if len(value) == 10:
                parsed.append(dt.date.fromisoformat(value).isoformat())
            else:
                parsed.append(dt.datetime.fromisoformat(value).date().isoformat())
        except (TypeError, ValueError):
            parsed.append(None)
            malformed = malformed or value not in (None, "")
    dating = _article_dating(*parsed, date)
    # Les dates malformées ne deviennent jamais des bornes ouvertes.
    if malformed:
        dating["applicable_at_as_of_date"] = None
        dating["caveat"] = "Bornes de version illisibles : applicabilité non confirmée."
    if start in (None, "") or end in (None, ""):
        dating["applicable_at_as_of_date"] = None
        dating["caveat"] = (
            "Bornes de version incomplètes : applicabilité non confirmée."
        )
    return {
        "source": "Légifrance API",
        "verified": True,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "content_trust": UNTRUSTED_CONTENT,
        "legal_status": node.get("etat") or node.get("jurisState") or "UNKNOWN",
        "start_date": start,
        "end_date": end,
        **dating,
    }


def _aggregate(result: dict[str, Any]) -> dict[str, Any]:
    """La vigueur d'un titre n'atteste pas celle de tous ses articles."""
    own = result["metadata"]["applicable_at_as_of_date"]
    children = result.get("articles", []) + result.get("sections", [])
    values = [own] + [item["metadata"]["applicable_at_as_of_date"] for item in children]
    combined = False if False in values else (None if None in values else True)
    result["metadata"]["node_applicable_at_as_of_date"] = own
    result["metadata"]["applicable_at_as_of_date"] = combined
    if combined is not True:
        result["metadata"]["caveat"] = (
            "La période du titre ou d'au moins un descendant ne permet pas "
            "de confirmer l'applicabilité de l'ensemble à la date évaluée. "
            "Consulter les bornes et réserves de chaque élément."
        )
    return result


def _bounded(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        _fail("Réponse de consultation invalide.")
    try:
        size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    except (ValueError, TypeError, RecursionError):
        _fail("Réponse de consultation invalide ou trop profonde.")
    if size > MAX_RESPONSE_BYTES:
        _fail("Consultation trop volumineuse : aucun contenu tronqué n'est retourné.")
    # Le contrat de consultation n'est pas paginé. Une continuation ou une
    # marque de troncature inattendue interdit de prétendre disposer du tout.
    stack = [(payload, 0)]
    count = 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            _fail("Arborescence trop volumineuse : aucun résultat partiel retourné.")
        if any(
            node.get(key)
            for key in ("nextPage", "nextCursor", "next_cursor", "hasMore", "truncated")
        ):
            _fail("Réponse de consultation partielle : lecture complète non confirmée.")
        if node.get("complete") is False or node.get("content_complete") is False:
            _fail("Réponse de consultation explicitement incomplète.")
        stack.extend((child, depth + 1) for child in _children(node, "sections"))
        count += len(_children(node, "articles"))
        if count > MAX_NODES:
            _fail("Consultation trop volumineuse : aucun résultat partiel retourné.")
    return payload


def _validate_text(payload: dict[str, Any], text_id: str) -> None:
    response_id = payload.get("id")
    match = _VERSION_ID.fullmatch(response_id) if isinstance(response_id, str) else None
    if not match or match.group(1) != text_id or not _clean_text(payload.get("title")):
        _fail(
            "Identité du texte de consultation absente ou différente du texte demandé."
        )
    if match.group(2):
        try:
            dt.datetime.strptime(match.group(2), "%d-%m-%Y")
        except ValueError:
            _fail("Identifiant de version du texte invalide.")


def _article(
    node: dict[str, Any], date: str | None, collection: str = "codes"
) -> dict[str, Any]:
    identifier = node.get("id")
    if not isinstance(identifier, str) or not _ARTICLE_ID.fullmatch(identifier):
        _fail("Identité d'article absente ou invalide dans la consultation.")
    content = node.get("content")
    if not isinstance(content, str) or not _clean_text(content):
        _fail(
            "Article sans contenu : sommaire ou consultation partielle, non texte complet."
        )
    return {
        "id": identifier,
        "cid": node.get("cid"),
        "title": f"Article {_clean_text(node.get('num')) or '?'}",
        "text": _clean_text(content),
        "notes": _notes(node, _ARTICLE_NOTES),
        "order": node.get("intOrdre"),
        "url": f"https://www.legifrance.gouv.fr/{collection}/article_lc/{identifier}/{_iso_date(date)}/",
        "metadata": _metadata(node, date),
    }


def _section(
    node: dict[str, Any], text_id: str, date: str | None, collection: str = "codes"
) -> dict[str, Any]:
    identifier = node.get("id")
    cid = node.get("cid")
    if not isinstance(identifier, str) or not _SECTION_ID.fullmatch(identifier):
        _fail("Identité de section absente ou invalide dans la consultation.")
    if cid is not None and (not isinstance(cid, str) or not _SECTION_ID.fullmatch(cid)):
        _fail("Identifiant commun de section invalide.")
    title = _clean_text(node.get("title"))
    if not title:
        _fail("Titre de section absent.")
    articles = [
        _article(item, date, collection) for item in _children(node, "articles")
    ]
    sections = [
        _section(item, text_id, date, collection)
        for item in _children(node, "sections")
    ]
    notes = _notes(node, _SECTION_NOTES)
    if (
        not articles
        and not sections
        and not (notes.get("commentaire") or notes.get("renvoi"))
    ):
        _fail("Section sans contenu : sommaire ou consultation partielle.")
    url = f"https://www.legifrance.gouv.fr/codes/section_lc/{text_id}/{identifier}/{_iso_date(date)}/"
    if collection == "loda":
        # Le texte parent est la source consultée ; ne pas inventer une route
        # codes/section_lc pour une section LODA.
        url = f"https://www.legifrance.gouv.fr/loda/id/{text_id}/{_iso_date(date)}/"
    return _aggregate(
        {
            "id": identifier,
            "cid": cid,
            "title": title,
            "notes": notes,
            "order": node.get("intOrdre"),
            "articles": articles,
            "sections": sections,
            "url": url,
            "metadata": _metadata(node, date),
        }
    )


def _render(node: dict[str, Any]) -> str:
    lines = [node["title"]]
    lines.extend(node.get("notes", {}).values())
    if node.get("text"):
        lines.append(node["text"])
    # intOrdre compare les articles et les sous-sections d'un même parent.
    children = node.get("articles", []) + node.get("sections", [])
    children = sorted(
        children,
        key=lambda child: (
            child.get("order") if isinstance(child.get("order"), int) else float("inf")
        ),
    )
    lines.extend(_render(child) for child in children)
    return "\n\n".join(lines)


def get_section(
    section_id: str, text_id: str, date: str | None = None
) -> dict[str, Any]:
    """Lit uniquement le sous-arbre demandé d'un code, à la date évaluée."""
    section_id = _identifier(section_id, _SECTION_ID, "LEGISCTA")
    text_id = _identifier(text_id, _TEXT_ID, "LEGITEXT")
    effective = _consult_date(date)
    payload = _bounded(
        api_call(
            "/consult/code",
            {
                "textId": text_id,
                "sctCid": section_id,
                "date": effective,
            },
            get_token(),
        )
    )
    _validate_text(payload, text_id)
    matches = []
    stack = list(_children(payload, "sections"))
    while stack:
        node = stack.pop()
        if section_id in (node.get("id"), node.get("cid")):
            matches.append(node)
        stack.extend(_children(node, "sections"))
    if len(matches) != 1:
        _fail("Section demandée absente ou ambiguë dans le texte officiel retourné.")
    result = _section(matches[0], text_id, date)
    result["text"] = _render(result)
    result["metadata"].update(
        {
            "requested_id": section_id,
            "parent_text_id": text_id,
            "parent_title": payload["title"],
            "parent_version_id": payload["id"],
            "endpoint": "/consult/code",
            "content_complete": True,
            "completeness_scope": "Sous-arbre retourné par l'API, hors documents liés externes.",
        }
    )
    return result


def get_text(text_id: str, date: str | None = None) -> dict[str, Any]:
    """Lit un texte consolidé LEGI, sans confondre source et vigueur."""
    text_id = _identifier(text_id, _TEXT_ID, "LEGITEXT")
    effective = _consult_date(date)
    payload = _bounded(
        api_call(
            "/consult/legiPart",
            {
                "textId": text_id,
                "date": effective,
            },
            get_token(),
        )
    )
    _validate_text(payload, text_id)
    result = {
        "id": text_id,
        "title": _clean_text(payload["title"]),
        "notes": _notes(payload, _TEXT_NOTES),
        "articles": [
            _article(item, date, "loda") for item in _children(payload, "articles")
        ],
        "sections": [
            _section(item, text_id, date, "loda")
            for item in _children(payload, "sections")
        ],
        "url": f"https://www.legifrance.gouv.fr/loda/id/{text_id}/{effective}/",
        "metadata": {
            **_metadata(payload, date, root=True),
            "version_id": payload["id"],
            "cid": payload.get("cid"),
            "nature": payload.get("nature"),
            "nor": payload.get("nor"),
            "endpoint": "/consult/legiPart",
            "content_complete": True,
            "completeness_scope": "Texte consolidé retourné par l'API, hors documents liés externes.",
        },
    }
    if not result["articles"] and not result["sections"]:
        _fail("Texte sans articles : consultation complète non confirmée.")
    result["text"] = _render(result)
    return _aggregate(result)
