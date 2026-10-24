"""Garde-fous de contenu pour la déclinaison Vibe du skill juridique."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
VIBE = ROOT / "vibe_skill"
SKILL = VIBE / "SKILL.md"
REFERENCES = VIBE / "references"
CORE_AUDIT = ROOT / "skill" / "references" / "audit-documentaire.md"

NATIVE_TOOLS = {"web_search", "web_fetch"}


class VibeSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.modules = (REFERENCES / "modules.md").read_text(encoding="utf-8")
        cls.audit = (REFERENCES / "audit-documentaire.md").read_text(encoding="utf-8")
        cls.modes = (REFERENCES / "modes-erreur.md").read_text(encoding="utf-8")
        cls.files = {
            path.relative_to(VIBE).as_posix(): path.read_text(encoding="utf-8")
            for path in VIBE.rglob("*.md")
        }

    def test_version_is_3_6_0_vibe(self):
        self.assertIn("version: 3.6.0-vibe", self.skill)
        self.assertIn("# Skill : recherche-juridique (v3.6.0-vibe)", self.skill)

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
        rows = re.findall(r"(?m)^(\d+)\. \*\*", self.modes)
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
                self.assertNotRegex(text, r"(?m)^→ Bloque modes(?! [0-9])")
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


    def test_all_legal_references_match_core_verbatim(self):
        names = {p.name for p in (ROOT / "skill/references").glob("*.md")} - {"maintenance.md"}
        self.assertEqual({p.name for p in REFERENCES.glob("*.md")}, names)
        for name in names:
            with self.subTest(reference=name):
                core = (ROOT / "skill/references" / name).read_text(encoding="utf-8").splitlines()
                port = (REFERENCES / name).read_text(encoding="utf-8").splitlines()
                if name in {"audit-documentaire.md", "modules.md"}:
                    core[2] = port[2]
                self.assertEqual(port, core)

    def test_core_is_short_and_all_routes_resolve(self):
        self.assertLessEqual(len(self.skill.splitlines()), 400)
        self.assertLessEqual(len(self.skill), 21000)
        for name in ("procedure-detaillee.md", "techniques-raisonnement.md", "modes-et-profils.md",
                     "gabarits-sortie.md", "gabarits-requetes.md", "format-citation.md", "checklist-vigueur.md"):
            self.assertIn(f"references/{name}", self.skill)
        for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", self.skill):
            if "://" not in link:
                self.assertTrue((SKILL.parent / link).resolve().exists(), link)

    def test_nine_steps_and_seven_principles_are_preserved(self):
        for step in ("0", "0 bis", "1", "2", "3", "4", "5", "6", "7"):
            self.assertRegex(self.skill, rf"(?m)^### Étape {step} — ")
        for principle in range(1, 8):
            self.assertIn(f"### P{principle} — ", self.skill)
        self.assertIn("question obligatoire et fond suspendu", self.skill)
        self.assertIn("jamais gabarit C", self.skill)

    def test_temporal_history_and_internal_citation_rules(self):
        details = (REFERENCES / "procedure-detaillee.md").read_text(encoding="utf-8")
        for state in ("get_article_history", "VIGUEUR_DIFF", "ABROGE_DIFF", "_MORT_NE", "modifications_available"):
            self.assertIn(state, details)
        templates = (REFERENCES / "gabarits-sortie.md").read_text(encoding="utf-8")
        self.assertIn("skill et la section", templates)
        self.assertIn("jamais par un lien Markdown", templates)
        self.assertIn("sans lien Markdown ni chemin relatif/absolu", self.skill)

    def test_no_updater_is_promised_and_support_is_verbatim(self):
        self.assertIn("Aucun updater livré", self.skill)
        self.assertFalse((SKILL.parent / "scripts/update_skill.py").exists())
        self.assertFalse((REFERENCES / "maintenance.md").exists())
        self.assertEqual((SKILL.parent / "scripts/legifrance.py").read_bytes(),
                         (ROOT / "skill/scripts/legifrance.py").read_bytes())
        for path in (ROOT / "skill/profils").glob("*.md"):
            self.assertEqual((SKILL.parent / "profils" / path.name).read_bytes(), path.read_bytes())

    def test_source_dates_are_inherited_without_new_legal_validation(self):
        core = (ROOT / "skill/SKILL.md").read_text(encoding="utf-8")
        for key in ("date_derniere_revue_methodologique", "date_derniere_verification_sources"):
            self.assertEqual(re.search(rf"{key}: (.+)", self.skill)[1], re.search(rf"{key}: (.+)", core)[1])

    def test_platform_independent_core_rules_are_verbatim(self):
        core = (ROOT / "skill/SKILL.md").read_text(encoding="utf-8")
        headings = [f"### P{n} — " for n in range(2, 8)]
        headings += [f"### Étape {n} — " for n in ("0", "0 bis", "1", "3", "4", "5", "6", "7")]
        for heading in headings:
            with self.subTest(section=heading):
                pattern = rf"(?ms)^{re.escape(heading)}.*?(?=^##|\Z)"
                self.assertEqual(re.search(pattern, self.skill)[0], re.search(pattern, core)[0])

    def test_vibe_mechanism_and_wrapper_limits_are_preserved(self):
        self.assertIn("user-invocable: false", self.skill)
        for tool in ("web_search", "web_fetch", "read_file", "ask_user_question"):
            self.assertIn(f"  - {tool}\n", self.skill)
        self.assertIn("squelette non connecté", self.skill)
        self.assertIn("ne pas l'utiliser pour une citation", self.skill)
        readme = (SKILL.parent / "README.md").read_text(encoding="utf-8")
        for folder in (".vibe/skills/", ".agents/skills/", "~/.vibe/skills/"):
            self.assertIn(folder, readme)


if __name__ == "__main__":
    unittest.main()
