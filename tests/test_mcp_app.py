#!/usr/bin/env python3
"""Tests hors réseau du service juridique et de son transport MCP."""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

from droit_francais.errors import LegifranceError  # noqa: E402
from droit_francais import tools as legal_tools  # noqa: E402
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
from mcp_server import server as mcp_app  # noqa: E402
from mcp_server.catalog import EXPECTED_TOOLS  # noqa: E402
from mcp_server.runtime import (  # noqa: E402
    RequestGovernor,
    RuntimeCapacityError,
    RuntimeConfigurationError,
    RuntimeSettings,
)


class LegalToolsTests(unittest.TestCase):
    @mock.patch("droit_francais.tools.get_token", return_value="token")
    @mock.patch("droit_francais.tools.api_call")
    def test_article_search_normalizes_official_results(self, api_call, get_token):
        api_call.return_value = {
            "results": [
                {
                    "titles": [{"title": "Code général des collectivités territoriales"}],
                    "sections": [
                        {
                            "title": "Police municipale",
                            "extracts": [
                                {
                                    "id": "LEGIARTI000042193463",
                                    "num": "L2212-2",
                                    "legalStatus": "VIGUEUR",
                                    "dateDebut": "2020-09-18",
                                },
                                {
                                    "id": "LEGIARTI000000000000",
                                    "num": "L2212-3",
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        result = legal_tools.search_articles(
            "L. 2212-2",
            "Code général des collectivités territoriales",
            "2026-08-29",
        )

        self.assertEqual(1, len(result["results"]))
        article = result["results"][0]
        self.assertEqual("LEGIARTI000042193463", article["id"])
        self.assertEqual("VIGUEUR", article["legal_status"])
        self.assertTrue(article["url"].startswith("https://www.legifrance.gouv.fr/"))
        body = api_call.call_args.args[1]
        self.assertEqual("CODE_DATE", body["fond"])
        self.assertEqual("L2212-2", body["recherche"]["champs"][0]["criteres"][0]["valeur"])
        get_token.assert_called_once_with()

    @mock.patch("droit_francais.tools.get_token", return_value="token")
    @mock.patch("droit_francais.tools.api_call")
    def test_get_article_returns_fetch_contract(self, api_call, _get_token):
        api_call.return_value = {
            "article": {
                "id": "LEGIARTI000042193463",
                "num": "L2212-2",
                "etat": "VIGUEUR",
                "dateDebut": "2020-09-18",
                "texteHtml": "<p>La police municipale comprend…</p>",
            }
        }

        article = legal_tools.get_article("legiarti000042193463")

        self.assertEqual("LEGIARTI000042193463", article["id"])
        self.assertEqual("Article L2212-2", article["title"])
        self.assertEqual("La police municipale comprend…", article["text"])
        self.assertTrue(article["metadata"]["verified"])

    @mock.patch("droit_francais.tools.judilibre_get")
    def test_case_law_search_and_fetch_are_traceable(self, judilibre_get):
        judilibre_get.side_effect = [
            {
                "total": 1,
                "results": [
                    {
                        "id": "abc123",
                        "jurisdiction": "cc",
                        "decision_date": "2025-01-15",
                        "number": "24-10.001",
                        "summary": "<p>Responsabilité administrative</p>",
                    }
                ],
            },
            {
                "id": "abc123",
                "jurisdiction": "cc",
                "decision_date": "2025-01-15",
                "number": "24-10.001",
                "text": "<p>Texte intégral</p>",
                "publication": ["b"],
            },
        ]

        results = legal_tools.search_case_law("responsabilité")
        decision = legal_tools.get_decision(results["results"][0]["id"])

        self.assertEqual("abc123", results["results"][0]["id"])
        self.assertEqual("Texte intégral", decision["text"])
        self.assertTrue(decision["metadata"]["verified"])
        self.assertEqual("https://www.courdecassation.fr/decision/abc123", decision["url"])

    @mock.patch("droit_francais.tools.search_articles")
    def test_standard_search_routes_explicit_articles(self, search_articles):
        search_articles.return_value = {
            "results": [
                {
                    "id": "LEGIARTI1",
                    "title": "Article L1 — Code test",
                    "url": "https://example.test/LEGIARTI1",
                    "legal_status": "VIGUEUR",
                }
            ]
        }
        result = legal_tools.search("article L. 1 du code test")
        self.assertEqual(
            {"id", "title", "url"},
            set(result["results"][0]),
        )
        search_articles.assert_called_once_with("L. 1")

    def test_invalid_date_stops_before_network(self):
        with self.assertRaises(LegifranceError) as caught:
            legal_tools.search_articles("L1", date="29/08/2026")
        self.assertEqual(2, caught.exception.exit_code)

    def test_mcp_error_masks_credentials(self):
        def fail():
            raise LegifranceError("clé super-secret refusée", exit_code=3)

        with mock.patch.dict(
            os.environ,
            {"LEGIFRANCE_CLIENT_SECRET": "super-secret"},
            clear=False,
        ):
            with self.assertRaises(mcp_app.ToolError) as caught:
                mcp_app._safe_call(fail)
        self.assertNotIn("super-secret", str(caught.exception))
        self.assertIn("secret masqué", str(caught.exception))


class RuntimeSafetyTests(unittest.TestCase):
    def test_production_requires_server_side_credentials(self):
        settings = RuntimeSettings.from_env({"MCP_ENV": "production"})
        with self.assertRaises(RuntimeConfigurationError) as caught:
            settings.validate_public({"MCP_ENV": "production"})
        message = str(caught.exception)
        self.assertIn("LEGIFRANCE_CLIENT_ID", message)
        self.assertIn("JUDILIBRE_KEY_ID", message)

    def test_production_accepts_judilibre_alias_without_exposing_values(self):
        env = {
            "MCP_ENV": "production",
            "LEGIFRANCE_CLIENT_ID": "client-secret-value",
            "LEGIFRANCE_CLIENT_SECRET": "oauth-secret-value",
            "PISTE_KEY_ID": "key-secret-value",
        }
        settings = RuntimeSettings.from_env(env)
        settings.validate_public(env)

    def test_invalid_port_is_explicit(self):
        with self.assertRaises(RuntimeConfigurationError) as caught:
            RuntimeSettings.from_env({"MCP_PORT": "not-a-port"})
        self.assertIn("MCP_PORT", str(caught.exception))

    def test_governor_rejects_calls_over_the_instance_budget(self):
        governor = RequestGovernor(
            max_concurrent=1,
            requests_per_minute=1,
            queue_timeout_seconds=0.01,
        )
        with governor.slot():
            pass
        with self.assertRaises(RuntimeCapacityError):
            with governor.slot():
                pass

    def test_health_and_domain_challenge_expose_no_configuration(self):
        health = asyncio.run(mcp_app.health(mock.Mock()))
        self.assertEqual(200, health.status_code)
        self.assertEqual(b'{"status":"ok","version":"0.5.0"}', health.body)

        with mock.patch.dict(
            os.environ, {"OPENAI_APPS_CHALLENGE": "challenge-token"}, clear=False
        ):
            challenge = asyncio.run(mcp_app.openai_apps_challenge(mock.Mock()))
        self.assertEqual(b"challenge-token", challenge.body)


class McpProtocolTests(unittest.TestCase):
    def test_stdio_protocol_lists_tools_and_returns_explicit_error(self):
        async def exercise() -> None:
            params = StdioServerParameters(
                command=sys.executable,
                args=[str(ROOT / "mcp_server" / "server.py")],
                cwd=str(ROOT),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    names = {tool.name for tool in listed.tools}
                    self.assertEqual(set(EXPECTED_TOOLS), names)
                    self.assertTrue(
                        all(
                            getattr(
                                tool.annotations,
                                "readOnlyHint",
                                getattr(tool.annotations, "read_only_hint", False),
                            )
                            for tool in listed.tools
                        )
                    )
                    self.assertTrue(
                        all(
                            not getattr(
                                tool.annotations,
                                "openWorldHint",
                                getattr(tool.annotations, "open_world_hint", True),
                            )
                            for tool in listed.tools
                        )
                    )
                    result = await session.call_tool("search", {"query": ""})
                    self.assertTrue(
                        getattr(result, "isError", getattr(result, "is_error", False))
                    )
                    self.assertIn("non vérifiée", result.content[0].text)

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
