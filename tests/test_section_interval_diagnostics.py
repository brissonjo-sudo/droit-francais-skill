"""Instrumentation S28 : refus identiques et journal à liste blanche, hors réseau."""

from __future__ import annotations

import copy
import json
import unittest
from unittest import mock

from tests.test_structured_sections import structure, body
from tests.test_text_consultation import SECTION, TEXT, DATE, text
from droit_francais import sections, texts, tools, section_diagnostics as diag
from droit_francais.errors import LegifranceError
from mcp_server import server


class IntervalDiagnosticTests(unittest.TestCase):
    def test_inversion_and_equality_still_refuse_with_identical_public_message(self):
        for start, end in (("2025-01-02", "2025-01-01"), ("2025-01-01", "2025-01-01")):
            with self.subTest(start=start, end=end), self.assertRaises(LegifranceError) as caught:
                sections._active({"id": SECTION, "dateDebut": start, "dateFin": end}, DATE,
                                 path=("listSection", 0))
            self.assertEqual(str(caught.exception), "Intervalle de structure invalide.")
            self.assertEqual(caught.exception.exit_code, 5)
            value = json.loads(caught.exception.detail)
            self.assertEqual(value["path"], ["listSection", 0])
            self.assertEqual(value["lower"], {"type": "str", "raw": start, "normalized": start})
            self.assertEqual(value["upper"]["normalized"], end)
            self.assertEqual(value["id"], SECTION)
            self.assertEqual(diag.safe_interval(caught.exception.detail), value)

    def test_same_normalized_day_preserves_both_numeric_raw_bounds(self):
        with self.assertRaises(LegifranceError) as caught:
            sections._active({"dateDebut": 1735689600000, "dateFin": 1735689601000.0}, DATE)
        value = json.loads(caught.exception.detail)
        self.assertEqual(value["lower"]["normalized"], "2025-01-01")
        self.assertEqual(value["upper"]["normalized"], "2025-01-01")
        self.assertEqual(value["lower"]["raw"], 1735689600000)
        self.assertEqual(value["upper"]["raw"], 1735689601000.0)

    def test_ill_readable_bounds_still_refuse_without_echoing_values(self):
        for value in (True, float("nan"), float("inf"), float("-inf"), None, {}, [], "https://secret.invalid/?token=SECRET"):
            with self.subTest(value=value), self.assertRaises(LegifranceError) as caught:
                sections._active({"dateDebut": value, "dateFin": "2999-01-01"}, DATE)
            self.assertNotIn("SECRET", str(caught.exception))
            self.assertIsNone(caught.exception.detail)

    def test_only_finite_or_strict_iso_raw_values_are_journaled(self):
        for value in (True, float("nan"), float("inf"), {}, [], None, 10 ** 1000,
                      "SECRET", "2025-01-01SECRET00:00:00", "2025-01-01 00:00:00", "1735689600000"):
            detail = diag.interval_detail({"dateDebut": value, "dateFin": "2025-01-01"},
                                         "2025-01-01", "2025-01-01", "dateDebut", "dateFin", "version", ())
            self.assertNotIn("raw", json.loads(detail)["lower"])
            self.assertNotIn("SECRET", detail)
            self.assertIsNotNone(diag.safe_interval(detail))
        for value in (0, 1.5, "2025-01-01", "2025-01-01T00:00:00Z", "2025-01-01T00:00:00+01:00"):
            detail = diag.interval_detail({"dateDebut": value, "dateFin": value},
                                         "2025-01-01", "2025-01-01", "dateDebut", "dateFin", "article", ())
            self.assertEqual(json.loads(detail)["lower"]["raw"], value)

    def test_unknown_paths_identifiers_roles_and_free_payload_are_omitted(self):
        detail = diag.interval_detail({"id": "SECRET", "titre": "SECRET", "texte": "SECRET",
                                      "dateDebut": "SECRET", "dateFin": "SECRET"},
                                     "2025-01-01", "2025-01-01", "dateDebut", "dateFin", "SECRET", ("SECRET",))
        value = json.loads(detail)
        self.assertNotIn("SECRET", detail)
        self.assertNotIn("id", value)
        self.assertEqual(value["path"], [])
        self.assertEqual(value["role"], "version")
        self.assertLess(len(detail), diag.MAX_DETAIL)
        detail = diag.interval_detail({}, "2025-01-01", "2025-01-01", "dateDebut", "dateFin",
                                     "version", ("sections", 5000) * 65)
        self.assertEqual(json.loads(detail)["path"], [])

    def test_untrusted_failure_detail_is_not_propagated(self):
        valid = json.loads(diag.interval_detail({}, "2025-01-01", "2025-01-01", "dateDebut", "dateFin", "version", ()))
        mutations = [lambda x: x.update(secret="SECRET"), lambda x: x.update(role="SECRET"),
                     lambda x: x.update(path=["SECRET"]), lambda x: x.update(path=[True]),
                     lambda x: x.update(id="SECRET"), lambda x: x["lower"].update(raw="SECRET"),
                     lambda x: x["upper"].update(normalized="SECRET"),
                     lambda x: x["lower"].update(raw=float("nan")),
                     lambda x: x.update(role=[])]
        for mutate in mutations:
            value = copy.deepcopy(valid)
            mutate(value)
            detail = json.dumps(value)
            self.assertIsNone(diag.safe_interval(detail))
            self.assertEqual(diag.combined_detail({}, detail, "parent"), "parent")
        for detail in (None, "not-json", "[]", "x" * 4097):
            self.assertEqual(diag.combined_detail({}, detail, "parent"), "parent")

    def test_historical_link_selection_and_budgets_are_unchanged(self):
        self.assertFalse(sections._active({"dateDebut": "2000-01-01", "dateFin": "2020-01-01"}, DATE))
        self.assertTrue(sections._active({"dateDebut": "2020-01-01", "dateFin": "2999-01-01"}, DATE))
        self.assertEqual((sections.MAX_REQUESTS, sections.MAX_SECONDS, texts.MAX_NODES,
                          texts.MAX_RESPONSE_BYTES, texts.MAX_DEPTH), (67, 90, 5000, 2_000_000, 32))


class IntervalPipelineTests(unittest.TestCase):
    def setUp(self):
        self.section = structure()
        self.article = body()
        for target, name, kwargs in ((texts, "get_token", {"return_value": "synthetic"}),
                                     (sections.time, "sleep", {}),
                                     (texts, "api_call", {"side_effect": self.api})):
            patch = mock.patch.object(target, name, **kwargs)
            result = patch.start()
            self.addCleanup(patch.stop)
            if name == "api_call":
                self.network = result

    def api(self, endpoint, arguments, token):
        if endpoint == "/consult/getSectionByCid":
            return self.section
        if endpoint == "/consult/getArticle":
            return self.article
        parent = text()
        parent["sections"] = [{"id": SECTION}] * 5001
        return parent

    def read(self):
        return tools.get_section(SECTION, TEXT, DATE)

    def test_parent_and_interval_details_survive_for_all_actual_roles(self):
        cases = (
            ("version", ["listSection", 0], lambda n: n.update(dateFin="2020-01-01")),
            ("context", ["listSection", 0, "context", "titreTxt", 0],
             lambda n: n["context"]["titreTxt"][0].update(fin="2020-01-01")),
            ("article_link", ["listSection", 0, "liensArticle", 0],
             lambda n: n["liensArticle"][0].update(dateFin="2020-01-01")),
            ("section_link", ["listSection", 0, "liensSection", 0],
             lambda n: n["liensSection"].append({"dateDebut": "2020-01-01", "dateFin": "2020-01-01"})),
        )
        for role, path, mutate in cases:
            self.section = structure()
            mutate(self.section["listSection"][0])
            with self.subTest(role=role), self.assertRaises(LegifranceError) as caught:
                self.read()
            value = json.loads(caught.exception.detail)
            self.assertEqual(value["kind"], "structured_consultation_refusal")
            self.assertEqual(value["primary"]["kind"], "consultation_limit")
            self.assertEqual(value["primary"]["limit"], 5000)
            self.assertEqual(value["structure"]["role"], role)
            self.assertEqual(value["structure"]["path"], path)
            self.assertIn("Récupération structurée refusée : Intervalle de structure invalide.", str(caught.exception))
        self.section = structure()
        for context in (False, True):
            self.article = body()
            node = self.article["article"]
            if context:
                node["context"]["titreTxt"][0]["fin"] = "2020-01-01"
            else:
                node["dateFin"] = "2020-01-01"
            with self.assertRaises(LegifranceError) as caught:
                self.read()
            value = json.loads(caught.exception.detail)["structure"]
            self.assertEqual(value["role"], "context" if context else "article")
            self.assertEqual(value["path"], ["listSection", 0, "liensArticle", 0, "article"]
                             + (["context", "titreTxt", 0] if context else []))

    def test_existing_server_logs_safe_detail_without_publishing_it(self):
        self.section["listSection"][0].update(dateFin="2020-01-01", titre="SECRET", texte="SECRET")
        with self.assertLogs("droit_francais.mcp", level="WARNING") as log:
            with self.assertRaises(server.ToolError) as caught:
                server._safe_call(self.read)
        journal, public = " ".join(log.output), str(caught.exception)
        self.assertIn("structured_consultation_refusal", journal)
        self.assertIn("2020-01-01", journal)
        self.assertNotIn("SECRET", journal)
        self.assertNotIn("structure_interval", public)
        self.assertNotIn("2020-01-01", public)
        self.assertRegex(public, r"\[réf\. [a-f0-9]{8}\]$")
        self.assertEqual(self.network.call_count, 2)

    def test_nested_section_path_is_preserved_across_official_calls(self):
        child_id = "LEGISCTA000000000002"
        self.section["listSection"][0]["liensArticle"] = []
        self.section["listSection"][0]["liensSection"] = [{"id": child_id, "cid": child_id,
            "dateDebut": "2020-01-01", "dateFin": "2999-01-01"}]
        child = structure()
        child["listSection"][0].update(id=child_id, cid=child_id, dateFin="2020-01-01")
        original = self.api
        self.network.side_effect = lambda endpoint, args, token: (
            child if args.get("cid") == child_id else original(endpoint, args, token))
        with self.assertRaises(LegifranceError) as caught:
            self.read()
        value = json.loads(caught.exception.detail)["structure"]
        self.assertEqual(value["path"], ["listSection", 0, "liensSection", 0, "listSection", 0])
        self.assertEqual(value["id"], child_id)

    def test_contents_resolution_path_and_refusal_are_preserved(self):
        self.section["listSection"] = []
        index = text()
        index["sections"] = [{"id": SECTION, "cid": "LEGISCTA000000000002",
                              "dateDebut": "2020-01-01", "dateFin": "2020-01-01", "sections": []}]
        original = self.api
        self.network.side_effect = lambda endpoint, args, token: (
            index if endpoint == "/consult/legi/tableMatieres" else original(endpoint, args, token))
        with self.assertRaises(LegifranceError) as caught:
            self.read()
        value = json.loads(caught.exception.detail)["structure"]
        self.assertEqual(value["role"], "contents")
        self.assertEqual(value["path"], ["sections", 0])

    def test_nested_section_path_is_preserved_across_official_calls(self):
        child_id = "LEGISCTA000000000002"
        self.section["listSection"][0]["liensArticle"] = []
        self.section["listSection"][0]["liensSection"] = [{"id": child_id, "cid": child_id,
            "dateDebut": "2020-01-01", "dateFin": "2999-01-01"}]
        child = structure()
        child["listSection"][0].update(id=child_id, cid=child_id, dateFin="2020-01-01")
        original = self.api
        self.network.side_effect = lambda endpoint, args, token: (
            child if args.get("cid") == child_id else original(endpoint, args, token))
        with self.assertRaises(LegifranceError) as caught:
            self.read()
        value = json.loads(caught.exception.detail)["structure"]
        self.assertEqual(value["path"], ["listSection", 0, "liensSection", 0, "listSection", 0])
        self.assertEqual(value["id"], child_id)

    def test_contents_resolution_path_and_refusal_are_preserved(self):
        self.section["listSection"] = []
        index = text()
        index["sections"] = [{"id": SECTION, "cid": "LEGISCTA000000000002",
                              "dateDebut": "2020-01-01", "dateFin": "2020-01-01", "sections": []}]
        original = self.api
        self.network.side_effect = lambda endpoint, args, token: (
            index if endpoint == "/consult/legi/tableMatieres" else original(endpoint, args, token))
        with self.assertRaises(LegifranceError) as caught:
            self.read()
        value = json.loads(caught.exception.detail)["structure"]
        self.assertEqual(value["role"], "contents")
        self.assertEqual(value["path"], ["sections", 0])


if __name__ == "__main__":
    unittest.main()
