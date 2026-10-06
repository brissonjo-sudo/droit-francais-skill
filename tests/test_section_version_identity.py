"""ID de version demandé : résolution officielle du CID, sans substitution."""
from __future__ import annotations

import copy
import unittest
from unittest import mock

from tests.test_structured_sections import structure, body
from tests.test_text_consultation import DATE, SECTION, TEXT, text
from droit_francais import sections, texts, tools
from droit_francais.errors import LegifranceError

VERSION = "LEGISCTA000000000002"
TOC = "/consult/legi/tableMatieres"


class SectionVersionIdentityTests(unittest.TestCase):
    def setUp(self):
        self.index = text()
        self.index["sections"] = [{"id": VERSION, "cid": SECTION, "title": "Version",
            "dateDebut": "2020-01-01", "dateFin": "2999-01-01", "sections": []}]
        self.structure = structure()
        self.structure["listSection"][0]["id"] = VERSION + ".xml"
        self.body = body()
        self.body["article"]["sectionParentId"] = VERSION + ".xml"
        self.calls = []
        for obj, name, options in (
            (texts, "get_token", {"return_value": "jeton-factice"}),
            (sections.time, "sleep", {}),
            (texts, "api_call", {"side_effect": self.api}),
        ):
            patch = mock.patch.object(obj, name, **options)
            patch.start(); self.addCleanup(patch.stop)

    def api(self, endpoint, arguments, token):
        self.calls.append((endpoint, arguments))
        if endpoint == TOC:
            return self.index
        if endpoint == "/consult/getSectionByCid":
            return self.structure if arguments["cid"] == SECTION else {"listSection": []}
        if endpoint == "/consult/getArticle":
            return self.body
        parent = text()
        parent["sections"] = [{"id": "LEGISCTA000000000003"}] * 5001
        return parent

    def read(self):
        return tools.get_section(VERSION, TEXT, DATE)

    def test_original_version_id_and_dated_parent_are_preserved(self):
        result = self.read()
        self.assertEqual(result["id"], VERSION)
        self.assertEqual(result["cid"], SECTION)
        self.assertEqual(result["metadata"]["requested_id"], VERSION)
        self.assertEqual(result["metadata"]["source_record_id"], VERSION + ".xml")
        binding = result["metadata"]["section_identity_resolution"]
        self.assertEqual(binding["requested_version_id"], VERSION)
        self.assertEqual(binding["resolved_cid"], SECTION)
        self.assertEqual(binding["as_of_date"], DATE)
        self.assertEqual(result["metadata"]["retrieval_plan"], {
            "sections": 1, "articles": 1, "requests": 4, "identity_requests": 2})
        self.assertEqual(self.calls[2], (TOC, {"textId": TEXT, "date": DATE, "nature": "CODE"}))
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertEqual(result["metadata"]["legal_status"], "UNKNOWN")

    def test_parent_identity_version_and_dates_cannot_be_relaxed(self):
        for mutation in (
            lambda t: t.update(id="LEGITEXT000000000003"),
            lambda t: t.update(id=TEXT + "_01-01-2020"),
            lambda t: t.update(dateFinVersion="2020-01-01"),
            lambda t: t.update(dateDebutVersion=None),
        ):
            self.index = text()
            mutation(self.index)
            with self.assertRaises(LegifranceError):
                self.read()
            self.assertNotEqual(self.calls[-1][0], "/consult/getArticle")

    def test_version_in_index_must_be_exact_unique_active_and_have_distinct_cid(self):
        original = copy.deepcopy(self.index)
        for mutation in (
            lambda n: n.update(id="LEGISCTA000000000003"),
            lambda n: n.update(cid=None),
            lambda n: n.update(cid=VERSION),
            lambda n: n.update(cid="HTML_OR_SECRET"),
            lambda n: n.update(dateFin="2020-01-01"),
        ):
            self.index = copy.deepcopy(original)
            mutation(self.index["sections"][0])
            with self.assertRaises(LegifranceError):
                self.read()
        self.index = copy.deepcopy(original)
        self.index["sections"] *= 2
        with self.assertRaises(LegifranceError):
            self.read()

    def test_expired_ancestor_cannot_supply_a_version_mapping(self):
        self.index["sections"] = [{"id": "LEGISCTA000000000003", "cid": "LEGISCTA000000000003",
            "dateDebut": "1990-01-01", "dateFin": "2000-01-01", "sections": self.index["sections"]}]
        with self.assertRaises(LegifranceError):
            self.read()

    def test_resolved_cid_does_not_authorize_a_different_active_version(self):
        self.structure["listSection"][0]["id"] = "LEGISCTA000000000003.xml"
        with self.assertRaises(LegifranceError):
            self.read()
        self.assertNotEqual(self.calls[-1][0], "/consult/getArticle")

    def test_second_cid_failure_cannot_repeat_resolution(self):
        self.structure["listSection"][0]["cid"] = "LEGISCTA000000000003"
        with self.assertRaises(LegifranceError):
            self.read()
        self.assertEqual(sum(endpoint == TOC for endpoint, _ in self.calls), 1)

    def test_index_body_is_never_used_as_section_content(self):
        self.index["visa"] = "CONTENU_SOMMAIRE_A_NE_PAS_SERVIR"
        result = self.read()
        self.assertNotIn("CONTENU_SOMMAIRE_A_NE_PAS_SERVIR", result["text"])
        self.assertIn("Contenu officiel simulé", result["text"])

    def test_index_limits_and_incomplete_responses_are_still_blocking(self):
        for mutation in (
            lambda t: t.update(visa="X" * (texts.MAX_RESPONSE_BYTES + 1)),
            lambda t: t.update(complete=False),
            lambda t: t.update(sections="schema-invalide"),
        ):
            self.index = text()
            mutation(self.index)
            with self.assertRaises(LegifranceError):
                self.read()

    def test_identity_reads_count_against_original_request_budget(self):
        with mock.patch.object(sections, "MAX_REQUESTS", 3):
            with self.assertRaises(LegifranceError):
                self.read()
        self.assertEqual(len(self.calls), 4)  # parent + 3 lectures d'identité
        self.assertNotEqual(self.calls[-1][0], "/consult/getArticle")

    def test_cid_request_needs_no_extra_table_of_contents_read(self):
        result = tools.get_section(SECTION, TEXT, DATE)
        self.assertEqual(result["metadata"]["requested_id"], SECTION)
        self.assertNotIn("section_identity_resolution", result["metadata"])
        self.assertFalse(any(endpoint == TOC for endpoint, _ in self.calls))

    def test_child_cid_failure_cannot_resolve_root_again(self):
        node = self.structure["listSection"][0]
        node["liensSection"] = [{"id": "LEGISCTA000000000003", "cid": "LEGISCTA000000000003",
            "dateDebut": "2020-01-01", "dateFin": "2999-01-01"}]
        with self.assertRaises(LegifranceError):
            tools.get_section(SECTION, TEXT, DATE)
        self.assertFalse(any(endpoint == TOC for endpoint, _ in self.calls))
