#!/usr/bin/env python3
"""Contrôles statiques du paquet de déploiement, sans Docker ni réseau."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class DeploymentPackageTests(unittest.TestCase):
    def test_container_runs_as_non_root_and_serves_http(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("USER app", dockerfile)
        self.assertIn('"--transport", "streamable-http"', dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertNotIn("LEGIFRANCE_CLIENT_SECRET=", dockerfile)
        self.assertNotIn("JUDILIBRE_KEY_ID=", dockerfile)

    def test_container_context_excludes_local_secrets(self):
        ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".env", ignored)
        self.assertIn(".env.*", ignored)
        self.assertIn(".git", ignored)

        gitignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".env.*", gitignored)

    def test_production_documentation_exists(self):
        self.assertTrue((ROOT / "docs" / "deployment.md").is_file())


if __name__ == "__main__":
    unittest.main()
