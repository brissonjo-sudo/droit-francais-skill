#!/usr/bin/env python3
"""La CI teste le serveur sur la version de Python de l'image de production.

Si le ``FROM`` du Dockerfile change de version mineure sans que le job
``tests-version-prod`` de la CI suive, la production tournerait de nouveau
sur une version jamais testée (cas du FutureWarning corrigé par la #179).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class VersionPythonProdTests(unittest.TestCase):
    def test_ci_suit_la_version_du_dockerfile(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        image = re.search(r"^FROM python:(\d+\.\d+)", dockerfile, re.MULTILINE)
        self.assertIsNotNone(image, "FROM python:X.Y introuvable dans le Dockerfile")
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        job = re.search(r'PYTHON_PROD_VERSION: "(\d+\.\d+)"', ci)
        self.assertIsNotNone(job, "PYTHON_PROD_VERSION introuvable dans ci.yml")
        self.assertEqual(image.group(1), job.group(1),
                         "Mettre PYTHON_PROD_VERSION de ci.yml à la version du Dockerfile.")


if __name__ == "__main__":
    unittest.main()
