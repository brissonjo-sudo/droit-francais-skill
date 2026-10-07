"""Versions morte-nées : fixtures synthétiques, aucun accès à une source réelle."""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
sys.path.insert(0, str(ROOT))

from tests.test_structured_sections import body, structure  # noqa: E402
from tests.test_text_consultation import ARTICLE, DATE, SECTION, TEXT  # noqa: E402
from droit_francais import article_versions, sections, texts  # noqa: E402
from droit_francais.errors import LegifranceError  # noqa: E402

DEAD = "LEGIARTI000000000002"
CHILD = "LEGISCTA000000000002"
LOWER = 1704067200000
UPPER = 1703980800000


class MortNeVersionTests(unittest.TestCase):
    def setUp(self):
        self.structure = structure()
        self.active = body()
        self.dead = body()
        self.dead["article"].update(
            id=DEAD, etat=article_versions.MORT_NE, dateDebut=LOWER,
            dateFin=UPPER, texte="SECRET_EXCLUDED_BODY", titre="SECRET_TITLE",
        )
        self.link = {"id": DEAD, "dateDebut": LOWER, "dateFin": UPPER}
        self.structure["listSection"][0]["liensArticle"].append(self.link)
        self.network = mock.Mock(side_effect=self.api)
        for target, field, kwargs in (
            (texts, "get_token", {"return_value": "synthetic"}),
            (texts, "api_call", {"new": self.network}),
            (sections.time, "sleep", {}),
        ):
            patch = mock.patch.object(target, field, **kwargs)
            patch.start()
            self.addCleanup(patch.stop)

    def api(self, endpoint, arguments, token):
        if endpoint == "/consult/getSectionByCid":
            return self.structure
        if endpoint == "/consult/getArticle":
            return self.dead if arguments["id"] == DEAD else self.active
        self.fail(f"Appel imprévu : {endpoint}")

    def read(self, date=DATE):
        return sections.retrieve(SECTION, TEXT, date, {"id": TEXT, "title": "Parent"})

    def article_calls(self):
        return [call.args[1]["id"] for call in self.network.call_args_list
                if call.args[0] == "/consult/getArticle"]

    def test_no_duplicate_methods_in_new_test_file(self):
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                names = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
                self.assertEqual(len(names), len(set(names)), node.name)

    def test_confirmed_version_excluded_with_explicit_audit_and_no_body(self):
        before = copy.deepcopy(self.structure)
        result = self.read()
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertEqual([x["id"] for x in result["articles"]], [ARTICLE])
        self.assertEqual(self.article_calls(), [DEAD, ARTICLE])
        self.assertEqual(result["metadata"]["retrieval_plan"],
                         {"sections": 1, "articles": 1, "requests": 3, "version_checks": 1})
        record = result["metadata"]["excluded_article_versions"][0]
        self.assertEqual(record["id"], DEAD)
        self.assertEqual(record["legal_status"], article_versions.MORT_NE)
        self.assertEqual(record["lower"], {"type": "int", "raw": LOWER, "normalized": "2024-01-01"})
        self.assertEqual(record["upper"]["raw"], UPPER)
        self.assertEqual(record["path"], ["listSection", 0, "liensArticle", 1])
        self.assertEqual(record["parent_binding"], "official_section_link_and_dated_text_context")
        self.assertEqual(record["section_parent_id"], SECTION)
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertEqual(self.structure, before)

    def test_explicit_link_state_still_requires_article_confirmation(self):
        self.link["etat"] = article_versions.MORT_NE
        self.assertEqual(len(self.read()["metadata"]["excluded_article_versions"]), 1)
        del self.dead["article"]["etat"]
        with self.assertRaises(LegifranceError):
            self.read()

    def test_unconfirmed_article_state_refuses_before_active_bodies(self):
        for state in (None, "UNKNOWN", "VIGUEUR", "ABROGE", "MODIFIE", "PERIME", []):
            with self.subTest(state=state):
                self.dead["article"]["etat"] = state
                self.network.reset_mock()
                with self.assertRaises(LegifranceError) as caught:
                    self.read()
                self.assertEqual(str(caught.exception), "Intervalle de structure invalide.")
                self.assertEqual(json.loads(caught.exception.detail)["id"], DEAD)
                self.assertEqual(self.article_calls(), [DEAD])

    def test_contradictory_or_unknown_link_state_refuses_without_article_reads(self):
        for state in (None, "", "UNKNOWN", "VIGUEUR", "MODIFIE", []):
            self.link["etat"] = state
            self.network.reset_mock()
            with self.subTest(state=state), self.assertRaises(LegifranceError):
                self.read()
            self.assertEqual(self.article_calls(), [])

    def test_raw_bounds_must_match_not_only_normalized_day(self):
        for key, value in (("dateDebut", LOWER + 1000), ("dateFin", UPPER - 1000),
                           ("dateDebut", float(LOWER)), ("dateDebut", "2024-01-01")):
            self.dead["article"].update(dateDebut=LOWER, dateFin=UPPER)
            self.dead["article"][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(LegifranceError):
                self.read()

    def test_missing_bounds_fail_closed(self):
        for key in ("dateDebut", "dateFin"):
            article = copy.deepcopy(self.dead["article"])
            del self.dead["article"][key]
            with self.assertRaises(LegifranceError):
                self.read()
            self.dead["article"] = article

    def test_equal_or_unreadable_link_bounds_not_exempted(self):
        for value in (UPPER, None, True, {}, "SECRET", float("inf")):
            self.link["dateDebut"] = value
            self.dead["article"]["dateDebut"] = value
            self.network.reset_mock()
            with self.subTest(value=value), self.assertRaises(LegifranceError):
                self.read()
            self.assertEqual(self.article_calls(), [])

    def test_link_status_cannot_exclude_a_normally_ordered_version(self):
        self.link.update(dateDebut="2020-01-01", dateFin="2999-01-01",
                         etat=article_versions.MORT_NE)
        with self.assertRaises(LegifranceError):
            self.read()
        self.assertEqual(self.article_calls(), [])

    def test_active_article_cannot_be_mort_ne_even_without_link_state(self):
        self.structure["listSection"][0]["liensArticle"].pop()
        self.active["article"]["etat"] = article_versions.MORT_NE
        with self.assertRaises(LegifranceError):
            self.read()

    def test_wrong_identity_or_parent_refuses(self):
        for changes in ({"id": ARTICLE}, {"sectionParentId": CHILD},
                        {"idTexte": "LEGITEXT000000000002", "cidTexte": "LEGITEXT000000000002"},
                        {"idTexte": "LEGITEXT000000000002"}, {"context": {}}):
            original = copy.deepcopy(self.dead["article"])
            self.dead["article"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(LegifranceError):
                self.read()
            self.dead["article"] = original

    def test_optional_direct_parent_still_requires_dated_context(self):
        del self.dead["article"]["idTexte"]
        del self.dead["article"]["cidTexte"]
        self.assertTrue(self.read()["metadata"]["content_complete"])
        self.dead["article"]["context"]["titreTxt"][0]["fin"] = "2021-01-01"
        with self.assertRaises(LegifranceError):
            self.read()

    def test_record_xml_parent_supported_without_id_substitution(self):
        self.structure["listSection"][0]["id"] += ".xml"
        self.dead["article"]["sectionParentId"] += ".xml"
        self.active["article"]["sectionParentId"] += ".xml"
        result = self.read()
        self.assertEqual(result["metadata"]["source_record_id"], SECTION + ".xml")
        self.assertEqual(result["metadata"]["excluded_article_versions"][0]["id"], DEAD)

    def test_invalid_or_duplicate_ids_not_queued(self):
        for identifier in (ARTICLE, "SECRET", None):
            self.link["id"] = identifier
            self.network.reset_mock()
            with self.subTest(identifier=identifier), self.assertRaises(LegifranceError):
                self.read()
            self.assertEqual(self.article_calls(), [])

    def test_duplicate_excluded_versions_refused(self):
        self.structure["listSection"][0]["liensArticle"].append(copy.deepcopy(self.link))
        with self.assertRaises(LegifranceError):
            self.read()
        self.assertEqual(self.article_calls(), [])

    def test_inventory_admission_counts_all_version_checks_before_any_body(self):
        with mock.patch.object(sections, "MAX_REQUESTS", 2):
            with self.assertRaises(LegifranceError) as caught:
                self.read()
        self.assertIn("appels_requis=3, plafond=2", str(caught.exception))
        self.assertEqual(self.article_calls(), [])

    def test_nested_inventory_is_finished_before_version_confirmation(self):
        root = self.structure
        root["listSection"][0]["liensSection"] = [{"id": CHILD, "cid": CHILD,
            "dateDebut": "2020-01-01", "dateFin": "2999-01-01"}]
        child = structure()
        child["listSection"][0].update(id=CHILD, cid=CHILD, liensArticle=[])
        original = self.api
        self.network.side_effect = lambda endpoint, args, token: (
            child if args.get("cid") == CHILD else original(endpoint, args, token))
        with mock.patch.object(sections, "MAX_REQUESTS", 3):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertEqual(self.article_calls(), [])
        self.assertEqual([x.args[1] for x in self.network.call_args_list],
                         [{"cid": SECTION}, {"cid": CHILD}])

    def test_date_does_not_turn_empty_interval_into_active_version(self):
        for date in ("2023-12-30", "2023-12-31", "2024-01-01", "2026-10-05"):
            with self.subTest(date=date):
                result = self.read(date)
                self.assertEqual([x["id"] for x in result["articles"]], [ARTICLE])
                self.assertEqual(result["metadata"]["excluded_article_versions"][0]["as_of_date"], date)

    def test_future_normal_link_is_not_replaced_or_fetched(self):
        self.structure["listSection"][0]["liensArticle"].append({
            "id": "LEGIARTI000000000003", "dateDebut": "2029-01-01", "dateFin": "2999-01-01"})
        self.read()
        self.assertEqual(self.article_calls(), [DEAD, ARTICLE])

    def test_confirmation_failure_never_returns_previously_selected_content(self):
        self.dead["article"]["etat"] = "VIGUEUR"
        with self.assertRaises(LegifranceError):
            self.read()
        self.assertNotIn(ARTICLE, self.article_calls())

    def test_truncated_confirmation_response_not_accepted(self):
        for key in ("complete", "content_complete", "truncated", "hasMore", "nextCursor"):
            self.dead["article"][key] = False if key in ("complete", "content_complete") else True
            with self.subTest(key=key), self.assertRaises(LegifranceError):
                self.read()
            del self.dead["article"][key]

    def test_empty_section_not_claimed_complete_only_due_to_exclusion(self):
        self.structure["listSection"][0]["liensArticle"].pop(0)
        with self.assertRaises(LegifranceError):
            self.read()

    def test_cumulative_bytes_include_confirmation_body(self):
        stats = []
        for payload in (self.structure, self.dead, self.active):
            item = {}
            texts._bounded(payload, stats=item)
            stats.append(item)
        limit = max(item["bytes_json"] for item in stats) + 1
        with mock.patch.object(texts, "MAX_RESPONSE_BYTES", limit):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertEqual(self.article_calls(), [DEAD])

    def test_cumulative_nodes_include_confirmation_body(self):
        with mock.patch.object(texts, "MAX_NODES", 4):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertEqual(self.article_calls(), [DEAD])

    def test_time_limit_before_confirmation_stops_body_calls(self):
        with mock.patch.object(sections.time, "monotonic", side_effect=[0, 0, 91, 91]):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertEqual(self.article_calls(), [])

    def test_confirmation_depth_limit_unchanged(self):
        chain = self.dead["article"]
        for _ in range(texts.MAX_DEPTH + 1):
            child = {}
            chain["sections"] = [child]
            chain = child
        with self.assertRaises(LegifranceError):
            self.read()

    def test_existing_limits_are_unchanged(self):
        self.assertEqual((sections.MAX_REQUESTS, sections.MAX_SECONDS, texts.MAX_NODES,
                          texts.MAX_RESPONSE_BYTES, texts.MAX_DEPTH), (67, 90, 5000, 2_000_000, 32))


if __name__ == "__main__":
    unittest.main()
