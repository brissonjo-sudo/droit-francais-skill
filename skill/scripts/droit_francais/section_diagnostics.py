"""Diagnostics d'intervalles bornés, sans chaîne libre ni payload amont."""

from __future__ import annotations

import datetime as dt
import json
import math
import re

ROLES = frozenset(("version", "context", "section_link", "article_link", "article", "contents"))
KEYS = frozenset(("listSection", "context", "titreTxt", "liensArticle", "liensSection", "article", "sections"))
TYPES = frozenset(("null", "bool", "int", "float", "str", "list", "dict", "other"))
ID = re.compile(r"(?:LEGI(?:SCTA|ARTI|TEXT)|JORFTEXT)[0-9]{12}(?:\.xml)?")
ISO = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})?)?")
MAX_DETAIL = 4096


def _safe_raw(value):
    if type(value) is int:
        return value if value.bit_length() <= 64 else None
    if type(value) is float:
        return value if math.isfinite(value) else None
    if type(value) is str and len(value) <= 32 and ISO.fullmatch(value):
        try:
            dt.datetime.fromisoformat(value)
            return value
        except ValueError:
            pass
    return None


def _normalized(value):
    if type(value) is str and len(value) == 10 and ISO.fullmatch(value):
        try:
            return dt.date.fromisoformat(value).isoformat()
        except ValueError:
            pass
    return None


def _boundary(value, normalized):
    kind = "null" if value is None else type(value).__name__
    result = {"type": kind if kind in TYPES else "other", "normalized": _normalized(normalized)}
    raw = _safe_raw(value)
    if raw is not None:
        result["raw"] = raw
    return result


def interval_detail(node: dict, lower: str, upper: str, start: str, end: str,
                    role: str, path: tuple) -> str:
    """Décrit un refus sans changer sa condition ni publier son détail au client."""
    safe_path = list(path) if len(path) <= 128 and all(
        (type(part) is str and part in KEYS)
        or (type(part) is int and 0 <= part <= 5000) for part in path
    ) else []
    result = {"kind": "structure_interval", "role": role if role in ROLES else "version",
              "path": safe_path,
              "start_key": start if start in ("dateDebut", "debut") else "dateDebut",
              "end_key": end if end in ("dateFin", "fin") else "dateFin",
              "lower": _boundary(node.get(start), lower), "upper": _boundary(node.get(end), upper)}
    identifier = node.get("id")
    if type(identifier) is str and ID.fullmatch(identifier):
        result["id"] = identifier
    encoded = json.dumps(result, ensure_ascii=True, allow_nan=False)
    # Une chaîne de chemins trop longue ne doit jamais changer le refus.
    if len(encoded) > MAX_DETAIL:
        result["path"] = []
        encoded = json.dumps(result, ensure_ascii=True, allow_nan=False)
    return encoded


def safe_interval(detail: str | None) -> dict | None:
    """Revalide la liste blanche avant propagation au journal existant."""
    if type(detail) is not str or len(detail) > MAX_DETAIL:
        return None
    try:
        value = json.loads(detail)
        expected = {"kind", "role", "path", "start_key", "end_key", "lower", "upper"}
        if (type(value) is not dict or set(value) not in (expected, expected | {"id"})
                or value["kind"] != "structure_interval" or value["role"] not in ROLES
                or type(value["path"]) is not list or len(value["path"]) > 128
                or any(not ((type(p) is str and p in KEYS) or
                            (type(p) is int and 0 <= p <= 5000)) for p in value["path"])
                or value["start_key"] not in ("dateDebut", "debut")
                or value["end_key"] not in ("dateFin", "fin")
                or ("id" in value and (type(value["id"]) is not str or not ID.fullmatch(value["id"])) )):
            return None
        for key in ("lower", "upper"):
            bound = value[key]
            if (type(bound) is not dict or set(bound) not in ({"type", "normalized"}, {"type", "normalized", "raw"})
                    or bound["type"] not in TYPES
                    or _normalized(bound["normalized"]) != bound["normalized"]):
                return None
            if "raw" in bound:
                raw = _safe_raw(bound["raw"])
                if raw is None or raw != bound["raw"] or type(raw).__name__ != bound["type"]:
                    return None
        return value
    except (ValueError, TypeError, KeyError):
        return None


def combined_detail(primary: dict, detail: str | None, fallback: str | None) -> str | None:
    """Garde le diagnostic parent intact si le détail structuré n'est pas sûr."""
    interval = safe_interval(detail)
    if interval is None:
        return fallback
    return json.dumps({"kind": "structured_consultation_refusal", "primary": primary,
                       "structure": interval}, ensure_ascii=True, allow_nan=False)
