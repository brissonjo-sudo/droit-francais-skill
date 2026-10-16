"""Garde-fous de contenu pour le portage Manus du skill juridique."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANUS = ROOT / "manus_skill"
SKILL = MANUS / "SKILL.md"


class ManusSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.files = {
            path.relative_to(MANUS).as_posix(): path.read_text(encoding="utf-8")
            for path in MANUS.rglob("*.md")
        }

    def test_exact_abstention_reserve_is_present(self):
        self.assertIn("Source non confirmée — abstention sur ce point.", self.skill)

    def test_applicability_field_is_present(self):
        self.assertIn("applicable_at_as_of_date", self.skill)

    def test_search_and_fetch_only_appear_in_mcp_connector_section(self):
        start = self.skill.index("**1. Connecteur MCP dédié")
        end = self.skill.index("**2. Capacité web native de Manus", start)
        mcp_section = self.skill[start:end]
        outside_mcp = self.skill[:start] + self.skill[end:]
        self.assertIn("`search`", mcp_section)
        self.assertIn("`fetch`", mcp_section)
        self.assertNotIn("`search`", outside_mcp)
        self.assertNotIn("`fetch`", outside_mcp)
        self.assertIn("l'identifiant renvoyé par `search`", mcp_section)
        self.assertIn("ne prend pas une URL", mcp_section)

    def test_application_fields_and_verified_caveat_are_present(self):
        for field in (
            "`verified`",
            "`as_of_date`",
            "`version_start_date` / `version_end_date`",
            "`applicable_at_as_of_date`",
            "`caveat`",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.skill)
        self.assertIn("`verified: true` signifie seulement que la source officielle a répondu", self.skill)

    def test_mcp_tool_contract_and_article_route_are_documented(self):
        for fragment in (
            "`search` | `query`",
            "`fetch` | `id`",
            "`search_articles` | `number`, `code`, `date`",
            "`get_article` | `id`, `date`",
            "`search_case_law` | `query`, `jurisdiction`, `date_start`, `date_end`",
            "`get_decision` | `id`",
            "`search_articles` → `get_article`",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.skill)

    def test_required_triangulation_and_contention_rule_are_present(self):
        for fragment in (
            "élément constitutif discutable",
            "qualification concurrente",
            "analogie apparente",
            "divergence ou revirement connu",
            "articulation de compétences",
            "proportionnalité interprétative",
            "citation officielle portant une interprétation discutable",
            "deux chemins indépendants",
            "Une décision est requise pour présenter comme établie une interprétation contentieuse",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.skill)

    def test_no_undefined_modes_or_step_zero_bis_in_manus_tree(self):
        defined_modes = bool(re.search(r"(?im)^.*(?:Bloque modes|bloque les modes).*$", self.skill))
        defined_step_zero_bis = bool(re.search(r"(?im)^.*(?:Étape|step) 0 bis\b.*$", self.skill))
        for path, text in self.files.items():
            if "Bloque modes" in text:
                self.assertTrue(defined_modes, f"Bloque modes non défini dans SKILL.md ({path})")
            if re.search(r"\b0 bis\b", text):
                self.assertTrue(defined_step_zero_bis, f"étape 0 bis non définie dans SKILL.md ({path})")

    def test_update_is_reimport_of_manus_folder_not_npx(self):
        self.assertIn("mettre à jour ce skill en réimportant le dossier `manus_skill/`", self.skill)
        self.assertNotIn("npx skills update", self.skill)


if __name__ == "__main__":
    unittest.main()
