"""Reconstruction CODE via les liens versionnés officiels, jamais via leurs URL."""

from __future__ import annotations

import datetime as dt
import re
import time

from . import texts

MAX_REQUESTS = 64
MAX_SECONDS = 50


def _date(value) -> str:
    try:
        if isinstance(value, bool) or value in (None, ""):
            raise ValueError
        if isinstance(value, (int, float)) or (
            isinstance(value, str) and value.isdigit()
        ):
            return (
                dt.datetime.fromtimestamp(float(value) / 1000, dt.timezone.utc)
                .date()
                .isoformat()
            )
        if not isinstance(value, str):
            raise ValueError
        if len(value) == 10:
            return dt.date.fromisoformat(value).isoformat()
        return dt.datetime.fromisoformat(value).date().isoformat()
    except (ValueError, TypeError, OverflowError, OSError):
        texts._fail("Bornes de structure illisibles : récupération complète refusée.")


def _active(node, date, start="dateDebut", end="dateFin"):
    lower, upper = _date(node.get(start)), _date(node.get(end))
    if lower >= upper:
        texts._fail("Intervalle de structure invalide.")
    return lower <= date < upper


def retrieve(section_id: str, text_id: str, date: str, parent: dict) -> dict:
    """Lit toutes les branches liées à la date, sous budgets cumulés inchangés."""
    token = texts.get_token()
    seen = set()
    calls = []
    total_bytes = total_nodes = 0
    started = time.monotonic()

    def call(endpoint, arguments):
        nonlocal total_bytes, total_nodes
        if calls:
            time.sleep(1.1)
        if len(calls) >= MAX_REQUESTS or time.monotonic() - started > MAX_SECONDS:
            texts._fail(
                "Budget de récupération structurée atteint : aucun résultat partiel."
            )
        stats = {}
        payload = texts._bounded(
            texts.api_call(endpoint, arguments, token), stats=stats
        )
        total_bytes += stats["bytes_json"]
        total_nodes += stats["nodes"]
        if total_bytes > texts.MAX_RESPONSE_BYTES:
            texts._limit_fail(
                "bytes_json", total_bytes, texts.MAX_RESPONSE_BYTES, "structured_total"
            )
        if total_nodes > texts.MAX_NODES:
            texts._limit_fail("nodes", total_nodes, texts.MAX_NODES, "structured_total")
        calls.append({"endpoint": endpoint, "arguments": arguments, "volume": stats})
        return payload

    def parent_context(node):
        context = node.get("context")
        if not isinstance(context, dict):
            texts._fail("Contexte parent absent de la structure officielle.")
        titles = texts._children(context, "titreTxt")
        active = [item for item in titles if _active(item, date, "debut", "fin")]
        if len(active) != 1 or text_id not in (
            active[0].get("id"),
            active[0].get("cid"),
        ):
            texts._fail("Rattachement daté au texte parent absent ou ambigu.")

    def register(identifier, pattern):
        if (
            not isinstance(identifier, str)
            or not pattern.fullmatch(identifier)
            or identifier in seen
        ):
            # Ne jamais refléter librement une chaîne provenant de l'amont.
            # Seuls les identifiants de nomenclature publique sont affichables.
            safe = (
                identifier
                if isinstance(identifier, str)
                and re.fullmatch(
                    r"LEGI(?:SCTA|ARTI)[0-9]{12}[-_0-9T:Z+.]{0,60}", identifier
                )
                else f"type={type(identifier).__name__}"
            )
            if isinstance(identifier, str) and safe == "type=str":
                prefix = re.match(r"LEGI(?:SCTA|ARTI)[0-9]{12}", identifier)
                shape = "".join(
                    "D" if char.isdigit() else "A" if char.isalpha() else "P"
                    for char in identifier[:80]
                )
                safe += f", longueur={len(identifier)}, prefixe={prefix.group(0) if prefix else '-'}, forme={shape}"
            cause = (
                "dupliquée"
                if isinstance(identifier, str) and identifier in seen
                else "invalide"
            )
            texts._fail(f"Identité {cause} dans la structure officielle ({safe}).")
        seen.add(identifier)
        if len(seen) > texts.MAX_NODES:
            texts._limit_fail("nodes", len(seen), texts.MAX_NODES, "selected_section")

    def read_section(cid, expected_id=None, depth=0):
        if depth > texts.MAX_DEPTH:
            texts._limit_fail("depth", depth, texts.MAX_DEPTH, "selected_section")
        payload = call("/consult/getSectionByCid", {"cid": cid})
        versions = texts._children(payload, "listSection")
        if not versions or any(v.get("cid") != cid for v in versions):
            texts._fail(
                "Liste des versions de section absente ou différente de la demande."
            )
        candidates = [v for v in versions if _active(v, date)]
        if len(candidates) != 1:
            texts._fail("Version de section applicable absente ou ambiguë.")
        node = candidates[0]
        if "liensArticle" not in node or "liensSection" not in node:
            texts._fail(
                "Inventaire des enfants absent : section complète non confirmée."
            )
        if expected_id is not None and node.get("id") != expected_id:
            texts._fail("Identité de sous-section différente du lien officiel.")
        register(node.get("id"), texts._SECTION_ID)
        parent_context(node)
        converted = {
            **node,
            "title": node.get("titre"),
            "dateDebut": _date(node.get("dateDebut")),
            "dateFin": _date(node.get("dateFin")),
            "etat": node.get("etat") or "UNKNOWN",
            "articles": [],
            "sections": [],
        }
        # Les liens historiques restent inventoriés ; seuls ceux dont la
        # période couvre la date demandée sont lus, sans substitution d'ID.
        for link in texts._children(node, "liensArticle"):
            if not _active(link, date):
                continue
            identifier = link.get("id")
            register(identifier, texts._ARTICLE_ID)
            article = call("/consult/getArticle", {"id": identifier}).get("article")
            if (
                not isinstance(article, dict)
                or article.get("id") != identifier
                or text_id not in (article.get("idTexte"), article.get("cidTexte"))
                or node["id"] != article.get("sectionParentId")
                or not _active(article, date)
            ):
                texts._fail(
                    "Article non conforme au lien, au parent ou à la date officielle."
                )
            parent_context(article)
            converted["articles"].append(
                {
                    **article,
                    "content": article.get("texteHtml") or article.get("texte"),
                    "dateDebut": _date(article.get("dateDebut")),
                    "dateFin": _date(article.get("dateFin")),
                    "intOrdre": article.get("ordre"),
                }
            )
        for link in texts._children(node, "liensSection"):
            if not _active(link, date):
                continue
            child_cid = link.get("cid")
            if not isinstance(child_cid, str) or not texts._SECTION_ID.fullmatch(
                child_cid
            ):
                texts._fail("CID de sous-section absent du lien officiel.")
            if not isinstance(link.get("id"), str) or not texts._SECTION_ID.fullmatch(
                link["id"]
            ):
                texts._fail("Identifiant de sous-section absent du lien officiel.")
            child = read_section(child_cid, link.get("id"), depth + 1)
            child["intOrdre"] = link.get("ordre")
            converted["sections"].append(child)
        return converted

    raw = read_section(section_id)
    stats = {}
    texts._bounded(raw, scope="selected_section", stats=stats)
    result = texts._section(raw, text_id, date)
    result["text"] = texts._render(result)
    result["metadata"].update(
        {
            "requested_id": section_id,
            "parent_text_id": text_id,
            "parent_title": parent["title"],
            "parent_version_id": parent["id"],
            "endpoint": "/consult/code",
            "content_endpoints": ["/consult/getSectionByCid", "/consult/getArticle"],
            "retrieval_strategy": "official_structure_links",
            "content_complete": True,
            "section_volume": stats,
            "structured_total_volume": {
                "bytes_json": total_bytes,
                "nodes": total_nodes,
            },
            "source_calls": calls,
            "completeness_scope": "Tous les liens de la section applicables à la date ; hors documents externes.",
        }
    )
    return result
