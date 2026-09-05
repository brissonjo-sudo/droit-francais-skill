"""
Package vibe_skill.tools — Outils de récupération Légifrance pour Vibe.

Ce package fournit un wrapper optionnel autour des outils MCP natifs de Vibe
(`web_search_web_search`, `web_search_open_url`) pour faciliter la récupération
de textes juridiques depuis Légifrance et autres sources officielles.

Utilisation :
    from vibe_skill.tools.legifrance_vibe import search_legifrance, get_article

Note : Ce package est **optionnel**. Les outils MCP natifs de Vibe suffisent
pour satisfaire toutes les exigences du noyau méthodologique (P1–P7).
"""

__version__ = "1.0.0"
__all__ = ["legifrance_vibe"]
