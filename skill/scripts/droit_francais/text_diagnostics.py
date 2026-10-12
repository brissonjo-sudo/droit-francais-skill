"""Trace S30 bornée : liste blanche, aucun calcul de vigueur ni corps amont."""

from __future__ import annotations

import json
import re
from typing import Any

from .section_diagnostics import TYPES, _safe_raw

TEXT = "LEGITEXT000005627880"
SECTION = "LEGISCTA000006098957"
DATE = "2026-10-05"
MAX_DETAIL_BYTES = 4096
DATE_FIELDS = ("dateDebut", "dateFin", "dateDebutVersion", "dateFinVersion", "debut", "fin")
KNOWN_KEYS = frozenset((*DATE_FIELDS, "id", "cid", "title", "etat", "intOrdre",
                        "articles", "sections", "commentaire", "renvoi", "renvoiNum",
                        "notaHtml", "notaSectionsAafficher", "context"))
VERSION = re.compile(r"LEGITEXT000005627880(?:_[0-9]{2}-[0-9]{2}-[0-9]{4})?\Z")


def _field(node: dict[str, Any], key: str) -> dict[str, Any]:
    if key not in node:
        return {"present": False}
    value = node[key]
    kind = "null" if value is None else type(value).__name__
    result = {"present": True, "type": kind if kind in TYPES else "other"}
    raw = _safe_raw(value)
    if raw is not None:
        result["raw"] = raw
    return result


def s30_dating_diagnostic(payload: dict[str, Any]) -> dict[str, Any]:
    """Décrit uniquement la section fixe ; les clés inconnues ne sont pas émises.

    Appelé après les contrôles de volume/identité et la normalisation. Une
    trace ne fournit aucune borne de remplacement et n'atteste pas la vigueur.
    Le périmètre borné couvre seulement les champs directs de la section.
    """
    result: dict[str, Any] = {"kind": "s30_section_dating", "text_id": TEXT,
        "section_id": SECTION, "as_of_date": DATE, "endpoint": "/consult/legiPart",
        "scope": "direct_section_fields_allowlist", "content_trust": "untrusted_source_data",
        "changes_applicability": False}
    version = payload.get("id")
    if type(version) is str and VERSION.fullmatch(version):
        result["parent_version_id"] = version
    matches = []
    stack = [(node, ["sections", index], 1)
             for index, node in enumerate(payload.get("sections", []))]
    count = 0
    while stack:
        node, path, depth = stack.pop()
        count += 1
        if count > 5000 or depth > 32 or type(node) is not dict:
            result["status"] = "inventory_incomplete"
            return result
        if node.get("id") == SECTION:
            matches.append((node, path))
        children = node.get("sections", [])
        if type(children) is not list:
            result["status"] = "inventory_incomplete"
            return result
        stack.extend((child, path + ["sections", index], depth + 1)
                     for index, child in enumerate(children))
    result["section_matches"] = len(matches)
    if len(matches) != 1:
        result["status"] = "section_absent" if not matches else "section_ambiguous"
        return result
    node, path = matches[0]
    result.update(status="observed", path=path,
        known_keys_present=sorted(key for key in KNOWN_KEYS if key in node),
        unlisted_key_count=sum(key not in KNOWN_KEYS for key in node),
        date_fields={key: _field(node, key) for key in DATE_FIELDS})
    if len(json.dumps(result, ensure_ascii=True, allow_nan=False).encode("utf-8")) > MAX_DETAIL_BYTES:
        # Pas de troncature présentée comme une trace complète.
        return {"kind": "s30_section_dating", "status": "diagnostic_limit",
                "changes_applicability": False}
    return result
