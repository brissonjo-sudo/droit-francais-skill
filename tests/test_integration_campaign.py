"""Recette distincte du catalogue stdio réel, activée explicitement avec le SDK."""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


@unittest.skipUnless(os.environ.get("BENCH_TEST_MCP_INTEGRATION") == "1", "recette stdio explicite, SDK MCP requis")
class IntegrationCampaign(unittest.TestCase):
    def test_catalogue_reel_huit_schemas(self):
        from bench.preconditions import catalogue
        from mcp_server.catalog import EXPECTED_TOOLS
        tools = catalogue(ROOT, sys.executable)
        self.assertEqual({t["name"] for t in tools}, EXPECTED_TOOLS)
        self.assertTrue(all(isinstance(t["inputSchema"], dict) for t in tools))
