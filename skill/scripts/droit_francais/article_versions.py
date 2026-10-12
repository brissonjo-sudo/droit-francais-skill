"""Confirmation stricte d'une version morte-née, sans réparation de dates."""

from __future__ import annotations

import json
from typing import Any

from .section_diagnostics import interval_detail

MORT_NE = "MODIFIE_MORT_NE"


def confirms_mort_ne(link: dict[str, Any], article: dict[str, Any]) -> bool:
    """Exige état officiel, ID exact et bornes brutes identiques et typées.

    Le demandeur doit aussi vérifier le parent et le contexte daté. Une absence
    d'état sur le lien n'est jamais suffisante : l'article doit le confirmer.
    """
    return (
        article.get("etat") == MORT_NE
        and ("etat" not in link or link["etat"] == MORT_NE)
        and article.get("id") == link.get("id")
        and all(
            key in link
            and key in article
            and type(link[key]) is type(article[key])
            and link[key] == article[key]
            for key in ("dateDebut", "dateFin")
        )
    )


def exclusion_record(
    link: dict[str, Any], lower: str, upper: str, path: tuple,
    section_id: str, text_id: str, date: str,
) -> dict[str, Any]:
    """Trace à liste blanche, construite après confirmation et rattachement."""
    record = json.loads(interval_detail(
        link, lower, upper, "dateDebut", "dateFin", "article_link", path,
    ))
    record.update(
        kind="confirmed_excluded_article_version", legal_status=MORT_NE,
        section_parent_id=section_id, parent_text_id=text_id, as_of_date=date,
        confirmation_endpoint="/consult/getArticle",
        parent_binding="official_section_link_and_dated_text_context",
        disposition="inventoried_not_applicable_not_rendered",
    )
    return record
