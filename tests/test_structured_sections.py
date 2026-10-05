"""Structure officielle synthétique : complétude, parent, dates et budgets."""

from __future__ import annotations

import copy
import json
import unittest
from unittest import mock

from tests.test_text_consultation import ARTICLE, DATE, SECTION, TEXT, text
from droit_francais import sections, texts, tools
from droit_francais.errors import LegifranceError


def context():
    return {
        "titreTxt": [
            {"id": TEXT, "cid": TEXT, "debut": "2020-01-01", "fin": "2999-01-01"}
        ]
    }


def structure():
    return {
        "listSection": [
            {
                "id": SECTION,
                "cid": SECTION,
                "titre": "Chapitre officiel simulé",
                "dateDebut": "2020-01-01",
                "dateFin": "2999-01-01",
                "context": context(),
                "liensArticle": [
                    {"id": ARTICLE, "dateDebut": "2020-01-01", "dateFin": "2999-01-01"}
                ],
                "liensSection": [],
            }
        ]
    }


def body():
    return {
        "article": {
            "id": ARTICLE,
            "idTexte": TEXT,
            "cidTexte": TEXT,
            "sectionParentId": SECTION,
            "dateDebut": "2020-01-01",
            "dateFin": "2999-01-01",
            "context": context(),
            "texte": "Contenu officiel simulé. " * 12,
            "num": "1",
            "ordre": 1,
        }
    }


class StructuredSectionTests(unittest.TestCase):
    def setUp(self):
        self.structure = structure()
        self.body = body()
        for target, value in ((texts, "get_token"),):
            patch = mock.patch.object(target, value, return_value="jeton-factice")
            patch.start()
            self.addCleanup(patch.stop)
        patch = mock.patch.object(sections.time, "sleep")
        patch.start()
        self.addCleanup(patch.stop)
        patch = mock.patch.object(texts, "api_call", side_effect=self.api)
        self.network = patch.start()
        self.addCleanup(patch.stop)

    def api(self, endpoint, arguments, token):
        if endpoint == "/consult/getSectionByCid":
            return self.structure
        if endpoint == "/consult/getArticle":
            return self.body
        parent = text()
        parent["sections"] = [{"id": "LEGISCTA000000000002"}] * 5001
        return parent

    def read(self):
        return tools.get_section(SECTION, TEXT, DATE)

    def test_recovers_all_children_after_refusing_large_code_parent(self):
        result = self.read()
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertTrue(result["metadata"]["applicable_at_as_of_date"])
        self.assertEqual(
            result["metadata"]["retrieval_strategy"], "official_structure_links"
        )
        self.assertEqual(result["articles"][0]["id"], ARTICLE)
        self.assertEqual(self.network.call_count, 3)
        self.assertEqual(
            [x["endpoint"] for x in result["metadata"]["source_calls"]],
            ["/consult/getSectionByCid", "/consult/getArticle"],
        )
        self.assertEqual(result["metadata"]["legal_status"], "UNKNOWN")

    def bytes_parent(self):
        parent = text()
        parent["visa"] = "X" * (texts.MAX_RESPONSE_BYTES + 1)
        original = self.api
        self.network.side_effect = lambda endpoint, arguments, token: (
            parent if endpoint == "/consult/code" else original(endpoint, arguments, token)
        )
        return parent

    def test_byte_limit_recovers_structure_without_reusing_oversized_parent_body(self):
        self.bytes_parent()
        result = self.read()
        diagnostic = result["metadata"]["primary_consultation_refused"]
        self.assertEqual(diagnostic["metric"], "bytes_json")
        self.assertEqual(diagnostic["scope"], "response")
        self.assertGreater(diagnostic["observed_at_least"], 2_000_000)
        self.assertEqual(result["metadata"]["retrieval_strategy"], "official_structure_links")
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertTrue(result["metadata"]["applicable_at_as_of_date"])
        self.assertEqual(result["articles"][0]["id"], ARTICLE)
        self.assertNotIn("X" * 100, result["text"])
        self.assertEqual(self.network.call_count, 3)

    def test_byte_limit_does_not_relax_parent_identity_or_version(self):
        for identifier in ("LEGITEXT000000000002", TEXT + "_31-02-2020"):
            with self.subTest(identifier=identifier):
                parent = self.bytes_parent()
                parent["id"] = identifier
                self.network.reset_mock()
                with self.assertRaises(LegifranceError):
                    self.read()
                self.assertEqual(self.network.call_count, 1)

    def test_byte_limit_does_not_relax_child_dates_identity_or_completeness(self):
        for mutate in (
            lambda node: node.update(dateFin="2020-01-01"),
            lambda node: node.update(id="LEGIARTI000000000002"),
            lambda node: node.update(complete=False),
        ):
            self.body = body()
            mutate(self.body["article"])
            self.bytes_parent()
            with self.assertRaises(LegifranceError):
                self.read()

    def test_depth_and_incomplete_parent_do_not_trigger_structure_recovery(self):
        for partial in (False, True):
            parent = text()
            if partial:
                parent["truncated"] = True
            else:
                node = parent
                for _ in range(texts.MAX_DEPTH + 1):
                    child = {"sections": []}
                    node["sections"] = [child]
                    node = child
            self.network.reset_mock()
            self.network.side_effect = lambda endpoint, arguments, token: parent
            with self.assertRaises(LegifranceError):
                self.read()
            self.assertEqual(self.network.call_count, 1)

    def test_only_parent_response_size_or_node_limits_can_trigger_recovery(self):
        for metric, scope in (
            ("bytes_json", "selected_section"),
            ("nodes", "structured_total"),
            ("depth", "response"),
        ):
            failure = LegifranceError("Refus synthétique", 5, detail=json.dumps({
                "kind": "consultation_limit", "metric": metric, "scope": scope,
            }))
            with mock.patch.object(texts, "_bounded", side_effect=failure), \
                 mock.patch.object(sections, "retrieve") as retrieve:
                with self.assertRaises(LegifranceError):
                    self.read()
                retrieve.assert_not_called()

    def test_byte_limit_keeps_cumulative_content_and_request_admission_limits(self):
        self.bytes_parent()
        with mock.patch.object(sections, "MAX_REQUESTS", 1):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertNotIn("/consult/getArticle", [c.args[0] for c in self.network.call_args_list])
        self.network.reset_mock()
        with mock.patch.object(texts, "MAX_NODES", 3):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertEqual(sections.MAX_REQUESTS, 67)
        self.assertEqual(sections.MAX_SECONDS, 90)
        self.assertEqual(texts.MAX_RESPONSE_BYTES, 2_000_000)
        self.assertEqual(texts.MAX_DEPTH, 32)

    def test_identity_diagnostic_is_bounded_and_does_not_echo_arbitrary_content(self):
        for identifier, displayed in (
            (None, "type=NoneType"),
            (SECTION + "_2026-10-05", SECTION + "_2026-10-05"),
            ("SECRET_OR_UPSTREAM_HTML" * 100, "type=str"),
        ):
            self.structure = structure()
            self.structure["listSection"][0]["id"] = identifier
            with self.assertRaises(LegifranceError) as raised:
                self.read()
            self.assertIn(displayed, str(raised.exception))
            self.assertNotIn("SECRET_OR_UPSTREAM_HTML", str(raised.exception))
            self.assertLess(len(str(raised.exception)), 400)
            if isinstance(identifier, str):
                self.assertNotIn("SECRET_OR_UPSTREAM_HTML", str(raised.exception))

    def test_refuses_missing_and_ambiguous_versions(self):
        for versions in ([], self.structure["listSection"] * 2):
            self.structure["listSection"] = versions
            with self.assertRaises(LegifranceError):
                self.read()

    def test_exact_index_identity_keeps_official_cid_and_raw_provenance(self):
        for suffix in (".xml",):
            self.structure["listSection"][0]["id"] = SECTION + suffix
            for parent in (SECTION, SECTION + suffix):
                self.body["article"]["sectionParentId"] = parent
                result = self.read()
                self.assertEqual(result["id"], SECTION)
                self.assertEqual(
                    result["metadata"]["source_record_id"], SECTION + suffix
                )
                self.assertEqual(result["metadata"]["legal_status"], "UNKNOWN")

    def test_index_identity_does_not_relax_parent_date_or_unknown_suffix(self):
        for identifier in (
            SECTION + "_XXX",
            SECTION + "_VIG",
            SECTION + "_vig",
            "LEGISCTA000000000002.xml",
        ):
            self.structure = structure()
            self.structure["listSection"][0]["id"] = identifier
            with self.assertRaises(LegifranceError):
                self.read()
        self.structure = structure()
        self.structure["listSection"][0].update(
            id=SECTION + ".xml", dateFin="2020-01-01"
        )
        with self.assertRaises(LegifranceError):
            self.read()

    def test_refuses_wrong_section_cid_or_parent_context(self):
        for mutate in (
            lambda node: node.update(cid="LEGISCTA000000000002"),
            lambda node: node.update(context={}),
            lambda node: node["context"]["titreTxt"][0].update(
                id="LEGITEXT000000000002", cid="LEGITEXT000000000002"
            ),
        ):
            self.structure = structure()
            mutate(self.structure["listSection"][0])
            with self.assertRaises(LegifranceError):
                self.read()

    def test_refuses_missing_wrong_or_expired_articles(self):
        for mutate in (
            lambda article: article.update(id="LEGIARTI000000000002"),
            lambda article: article.update(sectionParentId="LEGISCTA000000000002"),
            lambda article: article.update(
                idTexte="LEGITEXT000000000002", cidTexte="LEGITEXT000000000002"
            ),
            lambda article: article.update(dateFin="2021-01-01"),
            lambda article: article.update(texte=""),
            lambda article: article.update(complete=False),
        ):
            self.body = body()
            mutate(self.body["article"])
            with self.assertRaises(LegifranceError):
                self.read()

    def test_optional_parent_fields_need_dated_context_and_exact_section(self):
        self.body["article"].pop("idTexte")
        self.body["article"].pop("cidTexte")
        result = self.read()
        self.assertEqual(
            result["articles"][0]["metadata"]["parent_binding"],
            "official_section_link_and_dated_text_context",
        )
        self.assertFalse(
            result["articles"][0]["metadata"]["direct_parent_fields_present"]
        )
        self.body["article"]["context"] = {}
        with self.assertRaises(LegifranceError):
            self.read()

    def test_complete_inventory_precedes_bodies_and_admission_is_bounded(self):
        with mock.patch.object(sections, "MAX_REQUESTS", 1):
            with self.assertRaises(LegifranceError) as raised:
                self.read()
        self.assertIn("sections=1, articles=1, appels_requis=2", str(raised.exception))
        self.assertNotIn(
            "/consult/getArticle",
            [args.args[0] for args in self.network.call_args_list],
        )

    def test_measured_execution_budget_preserves_content_limits(self):
        self.assertEqual(sections.MAX_REQUESTS, 67)
        self.assertEqual(sections.MAX_SECONDS, 90)
        self.assertEqual(texts.MAX_NODES, 5000)
        self.assertEqual(texts.MAX_RESPONSE_BYTES, 2_000_000)
        self.assertEqual(texts.MAX_DEPTH, 32)

    def test_refuses_duplicate_active_links_and_cycles(self):
        node = self.structure["listSection"][0]
        node["liensArticle"] *= 2
        with self.assertRaises(LegifranceError):
            self.read()
        self.structure = structure()
        self.structure["listSection"][0]["liensSection"] = [
            {
                "id": SECTION,
                "cid": SECTION,
                "dateDebut": "2020-01-01",
                "dateFin": "2999-01-01",
            }
        ]
        with self.assertRaises(LegifranceError):
            self.read()

    def test_historical_links_are_not_silently_replaced(self):
        self.structure["listSection"][0]["liensArticle"].append(
            {
                "id": "LEGIARTI000000000002",
                "dateDebut": "2000-01-01",
                "dateFin": "2010-01-01",
            }
        )
        self.assertEqual(len(self.read()["articles"]), 1)
        self.assertEqual(self.network.call_count, 3)

    def test_unknown_link_dates_fail_closed(self):
        for value in (None, "2020-01-01-corrompu", {}, True, float("inf")):
            self.structure = structure()
            self.structure["listSection"][0]["liensArticle"][0]["dateDebut"] = value
            with self.assertRaises(LegifranceError):
                self.read()

    def test_numeric_dates_supported_without_inventing_legal_status(self):
        self.structure["listSection"][0]["dateDebut"] = 1577836800000
        self.assertEqual(self.read()["metadata"]["version_start_date"], "2020-01-01")

    def test_limits_are_cumulative_and_request_budget_is_enforced(self):
        for limit in (1,):
            with mock.patch.object(sections, "MAX_REQUESTS", limit):
                with self.assertRaises(LegifranceError):
                    self.read()
        raw = structure()
        stats = {}
        texts._bounded(raw, stats=stats)
        article_stats = {}
        texts._bounded(body(), stats=article_stats)
        per_response = max(stats["bytes_json"], article_stats["bytes_json"]) + 1
        with mock.patch.object(texts, "MAX_RESPONSE_BYTES", per_response):
            with self.assertRaises(LegifranceError):
                sections.retrieve(SECTION, TEXT, DATE, {"id": TEXT, "title": "Parent"})

    def test_all_raw_structure_nodes_are_counted(self):
        stats = {}
        texts._bounded(structure(), stats=stats)
        self.assertEqual(stats["nodes"], 3)

    def test_no_url_from_structure_is_followed(self):
        self.structure["listSection"][0]["liensArticle"][0]["url"] = (
            "https://malveillant.test/"
        )
        self.read()
        self.assertTrue(
            all(
                call.args[0].startswith("/consult/")
                for call in self.network.call_args_list
            )
        )

    def test_missing_child_inventory_never_becomes_an_empty_complete_section(self):
        for key in ("liensArticle", "liensSection"):
            self.structure = structure()
            del self.structure["listSection"][0][key]
            with self.assertRaises(LegifranceError):
                self.read()

    def test_missing_subsection_id_is_not_replaced_by_cid(self):
        self.structure["listSection"][0]["liensSection"] = [
            {"cid": SECTION, "dateDebut": "2020-01-01", "dateFin": "2999-01-01"}
        ]
        with self.assertRaises(LegifranceError):
            self.read()

    def test_nested_subtree_is_read_entirely_with_exact_child_id(self):
        child_id = "LEGISCTA000000000002"
        child_article = "LEGIARTI000000000002"
        child = copy.deepcopy(self.structure)
        child["listSection"][0].update(id=child_id, cid=child_id)
        child["listSection"][0]["liensArticle"][0]["id"] = child_article
        child_body = body()
        child_body["article"].update(id=child_article, sectionParentId=child_id)
        self.structure["listSection"][0]["liensArticle"] = []
        self.structure["listSection"][0]["liensSection"] = [
            {
                "id": child_id,
                "cid": child_id,
                "dateDebut": "2020-01-01",
                "dateFin": "2999-01-01",
                "ordre": 1,
            }
        ]
        original = self.api

        def api(endpoint, arguments, token):
            if endpoint == "/consult/getSectionByCid" and arguments["cid"] == child_id:
                return child
            if endpoint == "/consult/getArticle":
                return child_body
            return original(endpoint, arguments, token)

        self.network.side_effect = api
        result = self.read()
        self.assertEqual(result["sections"][0]["articles"][0]["id"], child_article)
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertTrue(result["metadata"]["applicable_at_as_of_date"])

    def test_cumulative_node_and_time_budgets_fail_without_partial_result(self):
        with mock.patch.object(texts, "MAX_NODES", 3):
            with self.assertRaises(LegifranceError):
                sections.retrieve(SECTION, TEXT, DATE, {"id": TEXT, "title": "Parent"})
        self.network.reset_mock()
        with mock.patch.object(sections, "MAX_SECONDS", -1):
            with self.assertRaises(LegifranceError):
                sections.retrieve(SECTION, TEXT, DATE, {"id": TEXT, "title": "Parent"})
        self.network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
