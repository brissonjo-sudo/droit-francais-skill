"""Reconstruction CODE via les liens versionnés officiels, jamais via leurs URL."""

from __future__ import annotations

import datetime as dt
import re
import time

from . import article_versions, texts
from .section_diagnostics import interval_detail

# S01 : inventaire officiel du 05/10/2026 = 11 sections + 56 articles.
# Observation précédente : 40 appels / 50 s ; 67 à cette cadence ≈ 84 s.
# Délai arrondi borné, sans augmenter cadence ni plafonds de contenu.
MAX_REQUESTS = 67
MAX_SECONDS = 90


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


def _active(node, date, start="dateDebut", end="dateFin", *, role="version", path=()):
    lower, upper = _date(node.get(start)), _date(node.get(end))
    if lower >= upper:
        texts._fail("Intervalle de structure invalide.",
                    detail=interval_detail(node, lower, upper, start, end, role, path))
    return lower <= date < upper


def retrieve(section_id: str, text_id: str, date: str, parent: dict,
             lookup_cid: str | None = None) -> dict:
    """Lit toutes les branches liées à la date, sous budgets cumulés inchangés."""
    token = texts.get_token()
    seen = set()
    calls = []
    pending_articles = []
    pending_version_checks = []
    excluded_versions = []
    planned_requests = None
    total_bytes = total_nodes = 0
    started = time.monotonic()
    identity_resolution = None

    def call(endpoint, arguments):
        nonlocal total_bytes, total_nodes
        if calls:
            time.sleep(1.1)
        if len(calls) >= MAX_REQUESTS or time.monotonic() - started > MAX_SECONDS:
            texts._fail(
                f"Budget de récupération structurée atteint : appels={len(calls)}/{MAX_REQUESTS}, "
                f"secondes={int(time.monotonic() - started)}/{MAX_SECONDS}. Aucun résultat partiel."
                f" Inventaire_appels_requis={planned_requests}."
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

    def parent_context(node, path):
        context = node.get("context")
        if not isinstance(context, dict):
            texts._fail("Contexte parent absent de la structure officielle.")
        titles = texts._children(context, "titreTxt")
        active = [item for index, item in enumerate(titles) if _active(
            item, date, "debut", "fin", role="context", path=path + ("context", "titreTxt", index))]
        if len(active) != 1 or text_id not in (
            active[0].get("id"),
            active[0].get("cid"),
        ):
            texts._fail(
                f"Rattachement daté au texte parent absent ou ambigu (contextes_applicables={len(active)})."
            )

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
                    r"LEGI(?:SCTA|ARTI)[0-9]{12}(?:[-_0-9T:Z+.]{0,60}|[._-][A-Za-z]{3})",
                    identifier,
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

    def resolve_version_cid():
        """Résout un ID de version dans le sommaire officiel daté, sans corps."""
        nonlocal identity_resolution
        endpoint = "/consult/legi/tableMatieres"
        index = call(endpoint, {"textId": text_id, "date": date, "nature": "CODE"})
        texts._validate_text(index, text_id)
        if (index["id"] != parent["id"] or
                texts._metadata(index, date, root=True)["applicable_at_as_of_date"] is not True):
            texts._fail("Sommaire et parent de versions différentes ou non datées.")
        matches = []
        stack = [(item, True, ("sections", i)) for i, item in enumerate(texts._children(index, "sections"))]
        visited = set()
        while stack:
            node, path_active, path = stack.pop()
            if id(node) in visited:
                texts._fail("Sommaire de section dupliqué ou cyclique.")
            visited.add(id(node))
            active = _active(node, date, role="contents", path=path) and path_active
            if node.get("id") == section_id:
                matches.append((node, active))
            stack.extend((item, active, path + ("sections", i))
                         for i, item in enumerate(texts._children(node, "sections")))
        if len(matches) != 1 or not matches[0][1]:
            texts._fail("ID de version demandé absent, ambigu ou non applicable dans le sommaire.")
        node = matches[0][0]
        cid = node.get("cid")
        if not isinstance(cid, str) or not texts._SECTION_ID.fullmatch(cid) or cid == section_id:
            texts._fail("CID distinct et valide de la version demandée non confirmé.")
        identity_resolution = {
            "requested_version_id": section_id, "resolved_cid": cid,
            "parent_text_id": text_id, "parent_version_id": index["id"],
            "as_of_date": date, "endpoint": endpoint,
            "binding": "exact_dated_version_id_in_official_code_contents",
        }
        return cid

    def read_section(cid, expected_id=None, depth=0, path=()):
        if depth > texts.MAX_DEPTH:
            texts._limit_fail("depth", depth, texts.MAX_DEPTH, "selected_section")
        payload = call("/consult/getSectionByCid", {"cid": cid})
        versions = texts._children(payload, "listSection")
        if not versions or any(v.get("cid") != cid for v in versions):
            # Une seule résolution de la racine, jamais d'un lien enfant :
            # le CID est relu à la source, l'ID de version original reste exigé.
            if depth == 0 and expected_id is None and cid == section_id:
                resolved = resolve_version_cid()
                return read_section(resolved, expected_id=section_id, path=path)
            texts._fail(
                "Liste des versions de section absente ou différente de la demande."
            )
        candidates = [(v, path + ("listSection", i)) for i, v in enumerate(versions)
                      if _active(v, date, role="version", path=path + ("listSection", i))]
        if len(candidates) != 1:
            texts._fail("Version de section applicable absente ou ambiguë.")
        node, node_path = candidates[0]
        record_id = node.get("id")
        # Le CID, déjà contrôlé, désigne la section demandée ; l'ID de version
        # peut être distinct. Retenir exactement le nom de record XML, sans
        # remplacer sa base par le CID ni accepter un suffixe libre.
        record = (
            re.fullmatch(r"(LEGISCTA[0-9]{12})\.xml", record_id)
            if isinstance(record_id, str)
            else None
        )
        if record:
            node = {**node, "id": record.group(1), "source_record_id": record_id}
        if "liensArticle" not in node or "liensSection" not in node:
            texts._fail(
                "Inventaire des enfants absent : section complète non confirmée."
            )
        if expected_id is not None and node.get("id") != expected_id:
            texts._fail("Identité de sous-section différente du lien officiel.")
        register(node.get("id"), texts._SECTION_ID)
        parent_context(node, node_path)
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
        for index, link in enumerate(texts._children(node, "liensArticle")):
            link_path = node_path + ("liensArticle", index)
            lower, upper = _date(link.get("dateDebut")), _date(link.get("dateFin"))
            if lower > upper:
                # Différer uniquement un lien potentiellement morte-née. Ne pas
                # lire son corps avant l'inventaire/admission du plan complet.
                # L'absence d'état n'est pas une preuve : getArticle doit confirmer.
                if "etat" in link and link["etat"] != article_versions.MORT_NE:
                    _active(link, date, role="article_link", path=link_path)
                identifier = link.get("id")
                register(identifier, texts._ARTICLE_ID)
                pending_version_checks.append((node, record_id, link, link_path, lower, upper))
                continue
            if link.get("etat") == article_versions.MORT_NE:
                texts._fail("Version morte-née aux bornes non inversées : confirmation refusée.")
            if not _active(link, date, role="article_link", path=link_path):
                continue
            identifier = link.get("id")
            register(identifier, texts._ARTICLE_ID)
            pending_articles.append((converted, node, record_id, identifier, link_path))
        for index, link in enumerate(texts._children(node, "liensSection")):
            link_path = node_path + ("liensSection", index)
            if not _active(link, date, role="section_link", path=link_path):
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
            child = read_section(child_cid, link.get("id"), depth + 1, path=link_path)
            child["intOrdre"] = link.get("ordre")
            converted["sections"].append(child)
        return converted

    def bound_article(node, record_id, identifier, *, strict_parent=False):
        """Même contrôle d'identité/parent pour contenu actif et version exclue."""
        article = call("/consult/getArticle", {"id": identifier}).get("article")
        direct_parent = (
            (article.get("idTexte"), article.get("cidTexte"))
            if isinstance(article, dict) else (None, None)
        )
        parent_fields_present = any(value not in (None, "") for value in direct_parent)
        parent_matches = any(value in (text_id, text_id + ".xml") for value in direct_parent)
        if strict_parent and parent_fields_present:
            parent_matches = all(
                value in (text_id, text_id + ".xml")
                for value in direct_parent if value not in (None, "")
            )
        public_parents = [
            value if isinstance(value, str)
            and re.fullmatch(r"(?:LEGI|JORF)TEXT[0-9]{12}(?:\.xml)?", value)
            else type(value).__name__ for value in direct_parent
        ]
        diagnostic = (
            "Article non conforme au lien, au parent ou à la date officielle "
            f"(objet={isinstance(article, dict)}, "
            f"id={isinstance(article, dict) and article.get('id') == identifier}, "
            f"champs_parent_presents={parent_fields_present}, texte_parent={parent_matches}, "
            f"champs_parent_publics={public_parents}, "
            f"section_parent={isinstance(article, dict) and article.get('sectionParentId') in (node['id'], record_id)})."
        )
        if (not isinstance(article, dict) or article.get("id") != identifier
                or (parent_fields_present and not parent_matches)
                or article.get("sectionParentId") not in (node["id"], record_id)):
            texts._fail(diagnostic)
        return article, parent_fields_present, diagnostic

    def confirm_excluded_versions():
        for node, record_id, link, link_path, lower, upper in pending_version_checks:
            article, _, _ = bound_article(node, record_id, link["id"], strict_parent=True)
            if not article_versions.confirms_mort_ne(link, article):
                # Restituer le refus diagnostique initial ; aucune exemption
                # pour l'absence d'état ou des dates seulement proches.
                _active(link, date, role="article_link", path=link_path)
                texts._fail("Version morte-née non confirmée : confirmation refusée.")
            parent_context(article, link_path + ("article",))
            excluded_versions.append(article_versions.exclusion_record(
                link, lower, upper, link_path, node["id"], text_id, date,
            ))

    def read_articles():
        for converted, node, record_id, identifier, link_path in pending_articles:
            article, parent_fields_present, diagnostic = bound_article(node, record_id, identifier)
            if article.get("etat") == article_versions.MORT_NE:
                texts._fail("Version morte-née annoncée applicable par un lien : confirmation refusée.")
            if not _active(article, date, role="article", path=link_path + ("article",)):
                texts._fail(diagnostic)
            parent_context(article, link_path + ("article",))
            converted["articles"].append(
                {
                    **article,
                    "content": article.get("texteHtml") or article.get("texte"),
                    "dateDebut": _date(article.get("dateDebut")),
                    "dateFin": _date(article.get("dateFin")),
                    "intOrdre": article.get("ordre"),
                    "parent_binding": "official_section_link_and_dated_text_context",
                    "direct_parent_fields_present": parent_fields_present,
                }
            )

    raw = read_section(lookup_cid if lookup_cid is not None else section_id,
                       expected_id=section_id if lookup_cid is not None else None)
    if lookup_cid is not None:
        identity_resolution = {
            "requested_version_id": section_id, "resolved_cid": lookup_cid,
            "parent_text_id": text_id, "parent_version_id": parent["id"],
            "as_of_date": date, "endpoint": "/consult/getSectionByCid",
            "binding": "explicit_locator_and_exact_dated_version_id",
        }
    structure_calls = len(calls)
    section_count = sum(bool(texts._SECTION_ID.fullmatch(identifier)) for identifier in seen)
    planned_requests = structure_calls + len(pending_articles) + len(pending_version_checks)
    if planned_requests > MAX_REQUESTS:
        texts._fail(
            f"Inventaire officiel complet : sections={section_count}, articles={len(pending_articles)}, "
            f"appels_requis={planned_requests}, plafond={MAX_REQUESTS}. Aucun corps partiel lu ou retourné."
        )
    confirm_excluded_versions()
    read_articles()
    if excluded_versions:
        # Les octets de la trace font aussi partie du plafond de restitution.
        raw["excluded_article_versions"] = excluded_versions
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
            "content_endpoints": list(dict.fromkeys(item["endpoint"] for item in calls)),
            "retrieval_strategy": "official_structure_links",
            "content_complete": True,
            "section_volume": stats,
            "structured_total_volume": {
                "bytes_json": total_bytes,
                "nodes": total_nodes,
            },
            "source_calls": calls,
            "retrieval_plan": {
                "sections": section_count,
                "articles": len(pending_articles),
                "requests": planned_requests,
            },
            "completeness_scope": "Tous les liens de la section applicables à la date ; hors documents externes.",
        }
    )
    if identity_resolution is not None:
        result["metadata"]["section_identity_resolution"] = identity_resolution
        result["metadata"]["retrieval_plan"]["identity_requests"] = structure_calls - section_count
    if lookup_cid is not None:
        result["metadata"]["requested_cid"] = lookup_cid
    if excluded_versions:
        result["metadata"]["excluded_article_versions"] = excluded_versions
        result["metadata"]["retrieval_plan"]["version_checks"] = len(pending_version_checks)
    return result
