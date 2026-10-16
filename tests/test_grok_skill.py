"""Garde-fous de contenu pour la déclinaison Grok du skill juridique."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
GROK = ROOT / "grok_skill"
SKILL = GROK / "SKILL.md"
REFERENCES = GROK / "references"
CORE_AUDIT = ROOT / "skill" / "references" / "audit-documentaire.md"

NATIVE_TOOLS = {"web_search", "open_page", "open_page_with_find", "browser_tab"}


class GrokSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.modules = (REFERENCES / "modules.md").read_text(encoding="utf-8")
        cls.audit = (REFERENCES / "audit-documentaire.md").read_text(encoding="utf-8")
        cls.modes = (REFERENCES / "modes-erreur.md").read_text(encoding="utf-8")
        cls.files = {
            path.relative_to(GROK).as_posix(): path.read_text(encoding="utf-8")
            for path in GROK.rglob("*.md")
        }

    def test_version_is_3_5_0_grok(self):
        self.assertIn("version: 3.5.0-grok", self.skill)
        self.assertIn("# Skill : recherche-juridique (v3.5.0-grok)", self.skill)

    def test_doc_audit_3_5_0_controls_are_present(self):
        for name, text in (("SKILL.md", self.skill), ("modules.md", self.modules),
                           ("audit-documentaire.md", self.audit)):
            for fragment in ("exécution forcée d'office", "amende forfaitaire",
                             "classe de contravention"):
                with self.subTest(file=name, fragment=fragment):
                    self.assertIn(fragment.lower(), text.lower())

    def test_audit_protocol_matches_core_except_header(self):
        core = CORE_AUDIT.read_text(encoding="utf-8").splitlines()
        grok = self.audit.splitlines()
        self.assertEqual(len(core), len(grok))
        differences = [i for i, (a, b) in enumerate(zip(core, grok)) if a != b]
        self.assertEqual(differences, [2], "Seule la ligne de renvoi d'en-tête peut différer du noyau")

    def test_eighteen_error_modes_are_listed_and_referenced(self):
        rows = re.findall(r"(?m)^\| (\d+) \|", self.modes)
        self.assertEqual([int(n) for n in rows], list(range(1, 19)))
        self.assertIn("references/modes-erreur.md", self.skill)

    def test_references_are_linked_from_skill(self):
        for name in ("modules.md", "sources-autorisees.md", "audit-documentaire.md",
                     "modes-erreur.md"):
            with self.subTest(reference=name):
                self.assertIn(f"references/{name}", self.skill)

    def test_no_undefined_markers(self):
        for path, text in self.files.items():
            with self.subTest(path=path):
                self.assertNotIn("Bloque modes", text)
                self.assertNotIn("npx skills update", text)

    def test_modules_title_is_unversioned(self):
        self.assertEqual(self.modules.splitlines()[0], "# Modules activables — détail")

    def test_abstention_and_applicability_are_present(self):
        self.assertIn("applicable_at_as_of_date", self.skill)
        self.assertIn("`verified: true` atteste seulement la réponse officielle", self.skill)

    def test_only_known_native_tools_are_named(self):
        named = set(re.findall(r"`(web_\w+|open_\w+|browser_\w+)`", self.skill))
        self.assertTrue(named, "Aucun outil natif nommé dans SKILL.md")
        self.assertLessEqual(named, NATIVE_TOOLS)


if __name__ == "__main__":
    unittest.main()
