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
_NUMBER = re.compile(r"[\w-]+\Z")
_NOR = re.compile(r"[A-Z0-9]{8,14}\Z")
_NUMBER_PREFIX = re.compile(r"^(?:n\s*°|n°|no\b\.?)\s*", flags=re.IGNORECASE)
_TITLE_NUMBER = re.compile(r"\bn\s*°\s*(\S+)", flags=re.IGNORECASE)
_VERSION_SUFFIX = re.compile(r"_(\d{2})-(\d{2})-(\d{4})\Z")
TEXT_URL = "https://www.legifrance.gouv.fr/loda/id/{id}/"


def _field(champ: str, value: str) -> dict[str, Any]:
    return {
        "typeChamp": champ,
        "criteres": [{"typeRecherche": "EXACTE", "valeur": value, "operateur": "ET"}],
        "operateur": "ET",
    }


def _title_number(title: str) -> str | None:
    found = _TITLE_NUMBER.search(title)
    return found[1].rstrip(",.;").lower() if found else None


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
    entry = {
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
    entry["_key"] = text_id
    return entry


def search_texts(
    number: str | None = None,
    nor: str | None = None,
    date: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Retrouve un texte LEGI par numéro et/ou NOR exacts, une ligne par texte."""
    number = _NUMBER_PREFIX.sub("", (number or "").strip()).strip()
    nor = (nor or "").strip().upper()
    if not number and not nor:
        raise LegifranceError("Indiquer un numéro de texte ou un NOR.", exit_code=2)
    if number and not _NUMBER.match(number):
        raise LegifranceError(f"Numéro de texte invalide : {number!r}.", exit_code=2)
    if nor and not _NOR.match(nor):
        raise LegifranceError(f"NOR invalide : {nor!r}.", exit_code=2)
    filters: list[dict[str, Any]] = []
    if date:
        filters.append({"facette": "DATE_VERSION", "singleDate": _epoch_ms(_iso_date(date))})
    fields = [f for f in (number and _field("NUM", number), nor and _field("NOR", nor)) if f]
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
    payload = api_call("/search", body, get_token())
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
    # Versions futures (entrées en vigueur programmées) : on retient la dernière
    # version non postérieure à la date visée, à défaut la plus proche.
    as_of = _iso_date(date)

    def pick(group: list[dict[str, Any]]) -> dict[str, Any]:
        dated = [e for e in group if e["version_date"]]
        past = [e for e in dated if e["version_date"] <= as_of]
        if past:
            return max(past, key=lambda e: e["version_date"])
        return min(dated, key=lambda e: e["version_date"]) if dated else group[0]

    texts = [pick(group) for group in versions.values()]
    results = [{k: v for k, v in e.items() if k != "_key" and v is not None} for e in texts]
    total = payload.get("totalResultNumber")
    out: dict[str, Any] = {
        "results": results[: max(1, min(int(limit), 50))],
        "query": {"number": number or None, "nor": nor or None, "date": date},
        "rejected_results": rejected,
        # Plus de versions que la page lue : un texte peut manquer.
        "truncated": isinstance(total, int) and total > len(raw),
        "provenance": {
            "source": "Légifrance API",
            "verified": True,
            "content_trust": UNTRUSTED_CONTENT,
        },
    }
    if date:
        out["dating"] = _dating(date)
    return out
