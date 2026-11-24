"""Recherche d'un texte non codifié (loi, décret, arrêté) par numéro ou NOR.

Interroge le fonds LODA_DATE de ``/search``. Constats sur réponses réelles
(24/11/2026) qui fondent les choix ci-dessous :

* un résultat par version datée du texte : 29 résultats pour le décret 88-547,
  d'où le dédoublonnage par LEGITEXT (le suffixe ``_JJ-MM-AAAA`` de
  ``titles[0].id`` est la date de version) ;
* ``num`` est vide dans les résultats : le numéro se lit dans le titre ;
* ``NUM`` ne trouve que des numéros et ``NOR`` que des NOR ; le filtre
  ``DATE_VERSION`` fonctionne sur ce fonds et ne garde qu'une version ;
* ``TITLE`` répond mais renvoie aussi les textes modificateurs qui citent le
  titre, sans ordre fiable : la recherche par titre n'est pas exposée.
"""

from __future__ import annotations

import re
from typing import Any

from .errors import LegifranceError
from .legifrance import api_call, get_token
from .tools import UNTRUSTED_CONTENT, _clean_text, _dating, _epoch_ms, _iso_date

_PAGE_SIZE = 100
_MAX_INPUT = 40
_NUMBER = re.compile(r"[\w-]+\Z")
_NOR = re.compile(r"[A-Z0-9]{8,14}\Z")
_NUMBER_PREFIX = re.compile(r"^(?:n\s*°|no\b\.?)\s*", flags=re.IGNORECASE)
_TITLE_NUMBER = re.compile(r"\bn\s*°\s*([0-9][\w-]*)", flags=re.IGNORECASE)
_BEFORE_DATE = re.compile(r"\s+du\s+", flags=re.IGNORECASE)
_VERSION_SUFFIX = re.compile(r"_(\d{2})-(\d{2})-(\d{4})\Z")
#: Tirets typographiques, « nº » (U+00BA) et espaces insécables, en entrée comme
#: dans les titres.
_TYPO = str.maketrans(
    {c: "-" for c in "‐‑‒–—−"}
    | {"º": "°", " ": " ", " ": " "}
)
TEXT_URL = "https://www.legifrance.gouv.fr/loda/id/{id}/"


def _field(champ: str, value: str) -> dict[str, Any]:
    return {
        "typeChamp": champ,
        "criteres": [{"typeRecherche": "EXACTE", "valeur": value, "operateur": "ET"}],
        "operateur": "ET",
    }


def _title_number(title: str) -> str | None:
    """Numéro du texte lui-même : segment avant « du », jamais celui d'un texte cité."""
    head = _BEFORE_DATE.split(title.translate(_TYPO), 1)[0]
    found = _TITLE_NUMBER.search(head)
    return found[1].lower() if found else None


def _entry(result: dict[str, Any]) -> dict[str, Any] | None:
    """Résultat brut -> entrée normalisée, ou None sans identifiant exploitable."""
    titles = result.get("titles")
    head = titles[0] if isinstance(titles, list) and titles and isinstance(titles[0], dict) else {}
    raw_id = str(head.get("id") or "")
    suffix = _VERSION_SUFFIX.search(raw_id)
    text_id = raw_id[: suffix.start()] if suffix else raw_id
    if not text_id:
        return None
    title = _clean_text(head.get("title"))
    cid = str(head.get("cid") or "")
    return {
        "_key": text_id,
        "legitext_id": text_id if text_id.startswith("LEGITEXT") else None,
        "jorftext_id": cid if cid.startswith("JORFTEXT") else None,
        "nature": result.get("nature"),
        "number": _title_number(title),
        "nor": result.get("nor"),
        "title": title,
        "legal_status": result.get("etat"),
        "publication_date": str(result.get("datePublication") or "")[:10] or None,
        "version_date": f"{suffix[3]}-{suffix[2]}-{suffix[1]}" if suffix else None,
        "url": TEXT_URL.format(id=text_id) if text_id.startswith("LEGITEXT") else None,
    }


def _query(fields: list[dict[str, Any]], day: str | None) -> dict[str, Any]:
    filters = [{"facette": "DATE_VERSION", "singleDate": _epoch_ms(day)}] if day else []
    body = {
        "fond": "LODA_DATE",
        "recherche": {
            "champs": fields,
            "filtres": filters,
            "pageNumber": 1,
            "pageSize": _PAGE_SIZE,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "DEFAUT",
        },
    }
    return api_call("/search", body, get_token())


def search_texts(
    number: str | None = None,
    nor: str | None = None,
    date: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Retrouve un texte LEGI par numéro et/ou NOR exacts, une ligne par texte."""
    number = _NUMBER_PREFIX.sub("", (number or "").translate(_TYPO).strip()).strip()
    nor = (nor or "").translate(_TYPO).strip().upper()
    if not number and not nor:
        raise LegifranceError("Indiquer un numéro de texte ou un NOR.", exit_code=2)
    if number and (len(number) > _MAX_INPUT or not _NUMBER.match(number)):
        raise LegifranceError(f"Numéro de texte invalide : {number[:_MAX_INPUT]!r}.", exit_code=2)
    if nor and (len(nor) > _MAX_INPUT or not _NOR.match(nor)):
        raise LegifranceError(f"NOR invalide : {nor[:_MAX_INPUT]!r}.", exit_code=2)
    as_of = _iso_date(date)
    fields = [f for f in (number and _field("NUM", number), nor and _field("NOR", nor)) if f]
    def matching(payload: dict[str, Any]) -> tuple[list, dict[str, list[dict[str, Any]]], int]:
        raw = [r for r in payload.get("results") or [] if isinstance(r, dict)]
        versions: dict[str, list[dict[str, Any]]] = {}
        rejected = 0
        for item in raw:
            entry = _entry(item)
            # Un champ ignoré en silence renverrait tout le fonds : contrôle exact côté serveur.
            if (
                entry is None
                or (number and entry["number"] != number.lower())
                or (nor and str(entry["nor"] or "").upper() != nor)
            ):
                rejected += 1
                continue
            versions.setdefault(entry["_key"], []).append(entry)
        return raw, versions, rejected

    # Sans date : version du jour d'abord (une ligne par texte) ; la lecture de
    # toutes les versions, plafonnée à une page, ne sert que si aucun texte
    # correspondant n'en sort (texte dont la première version est à venir).
    payload = _query(fields, as_of)
    raw, versions, rejected = matching(payload)
    if not date and not versions:
        payload = _query(fields, None)
        raw, versions, rejected = matching(payload)

    def pick(group: list[dict[str, Any]]) -> dict[str, Any]:
        """Dernière version non postérieure à la date visée, à défaut la plus proche."""
        dated = [e for e in group if e["version_date"]]
        past = [e for e in dated if e["version_date"] <= as_of]
        if past:
            return max(past, key=lambda e: e["version_date"])
        if dated:
            return {**min(dated, key=lambda e: e["version_date"]), "future_version": True}
        return group[0]

    texts = [
        {k: v for k, v in pick(group).items() if k != "_key" and v is not None}
        for group in versions.values()
    ]
    safe_limit = max(1, min(int(limit), 50))
    total = payload.get("totalResultNumber")
    return {
        "results": texts[:safe_limit],
        "query": {"number": number or None, "nor": nor or None, "date": as_of if date else None},
        "rejected_results": rejected,
        # Page pleine ou plus de versions que lues, ou coupe à limit : un texte peut manquer.
        "truncated": len(texts) > safe_limit
        or len(raw) >= _PAGE_SIZE
        or (isinstance(total, int) and total > len(raw)),
        "provenance": {
            "source": "Légifrance API",
            "verified": True,
            "content_trust": UNTRUSTED_CONTENT,
        },
        **({"dating": _dating(date)} if date else {}),
    }
