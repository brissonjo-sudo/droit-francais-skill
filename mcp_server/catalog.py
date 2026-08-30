#!/usr/bin/env python3
"""Catalogue des outils MCP publiés — source unique du dépôt.

Le nom des outils apparaissait dans quatre fichiers indépendants : le serveur,
la sonde HTTP, le contrôle du socle plugin et les tests de protocole. Ajouter
ou renommer un outil demandait quatre éditions cohérentes, sans garde-fou.

Ce module ne dépend que de la bibliothèque standard : `tests/check_plugin.py`
peut l'importer sans installer le SDK MCP. L'accord entre ce catalogue et les
outils réellement enregistrés par `mcp_server/server.py` est vérifié par le
test de protocole stdio de `tests/test_mcp_app.py`.
"""
from __future__ import annotations

#: Outils annoncés au client, dans l'ordre de déclaration du serveur.
TOOL_NAMES: tuple[str, ...] = (
    "search",
    "fetch",
    "search_articles",
    "get_article",
    "search_case_law",
    "get_decision",
)

#: Même contrat, sous la forme attendue par les comparaisons d'ensembles.
EXPECTED_TOOLS: frozenset[str] = frozenset(TOOL_NAMES)
