"""Empêche le retour des renvois de référence vers leur propre fichier."""
from pathlib import Path
import csv
from copy import deepcopy
import unittest
from urllib.parse import unquote, urlsplit

from check_links import LINK_RE
from check_skill_structure import CORE_ROUTES, CORRESPONDANCE, check_rows

ROOT = Path(__file__).resolve().parents[1]


class ReferenceSelfLinksTests(unittest.TestCase):
    def test_les_references_ne_se_lient_pas_a_leur_propre_fichier(self):
        errors = []
        for path in sorted((ROOT / "skill/references").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in LINK_RE.finditer(text):
                target = match.group(1).strip().split(" ", 1)[0].strip("<>")
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                if (path.parent / unquote(url.path)).resolve() == path.resolve():
                    line = text.count("\n", 0, match.start()) + 1
                    errors.append(f"{path.name}:{line} : {target}")
        self.assertEqual(errors, [])

    def test_un_renvoi_relocalise_ne_peut_pas_etre_altere_dans_le_csv(self):
        with CORRESPONDANCE.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        for identifier in CORE_ROUTES:
            for field, value in (
                ("fichier_realise", "skill/references/format-citation.md"),
                ("texte_realise", "Lire une autre référence."),
            ):
                with self.subTest(identifier=identifier, field=field):
                    changed = deepcopy(rows)
                    row = next(r for r in changed if r["identifiant"] == identifier)
                    row[field] = value
                    self.assertTrue(check_rows(changed))
