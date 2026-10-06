"""CID de transport explicite : jamais une identité de version substituée."""
import copy
import unittest
from unittest import mock

from tests.test_structured_sections import structure, body
from tests.test_text_consultation import DATE, SECTION, TEXT, text
from droit_francais import sections, texts, tools
from droit_francais.errors import LegifranceError
from mcp_server import server

VERSION = "LEGISCTA000000000002"


class ExplicitSectionCidTests(unittest.TestCase):
    def setUp(self):
        self.parent = text()
        self.parent["sections"][0]["id"] = VERSION
        self.root = structure()
        self.root["listSection"][0]["id"] = VERSION + ".xml"
        self.article = body()
        self.article["article"]["sectionParentId"] = VERSION + ".xml"
        self.oversized = False
        self.calls = []
        for obj, name, options in (
            (texts, "get_token", {"return_value": "jeton-factice"}),
            (sections.time, "sleep", {}),
            (texts, "api_call", {"side_effect": self.api}),
        ):
            p = mock.patch.object(obj, name, **options)
            p.start(); self.addCleanup(p.stop)

    def api(self, endpoint, arguments, token):
        self.calls.append((endpoint, arguments))
        if endpoint == "/consult/code":
            p = copy.deepcopy(self.parent)
            if self.oversized:
                p["visa"] = "X" * (texts.MAX_RESPONSE_BYTES + 1)
            return p
        if endpoint == "/consult/getSectionByCid":
            return self.root
        if endpoint == "/consult/getArticle":
            return self.article
        raise AssertionError("Sommaire ou repli non autorisé dans cette voie")

    def read(self, cid=SECTION):
        return tools.get_section(VERSION, TEXT, DATE, cid=cid)

    def test_bounded_primary_lookup_uses_cid_but_preserves_exact_version(self):
        result = self.read(SECTION.lower())
        self.assertEqual(self.calls, [("/consult/code", {"textId": TEXT, "sctCid": SECTION, "date": DATE})])
        self.assertEqual(result["id"], VERSION)
        self.assertEqual(result["cid"], SECTION)
        self.assertEqual(result["metadata"]["requested_id"], VERSION)
        self.assertEqual(result["metadata"]["requested_cid"], SECTION)

    def test_oversized_parent_is_not_served_and_no_toc_is_read(self):
        self.oversized = True
        result = self.read()
        self.assertEqual(result["id"], VERSION)
        self.assertEqual(result["metadata"]["source_record_id"], VERSION + ".xml")
        self.assertEqual(result["metadata"]["retrieval_plan"], {
            "sections": 1, "articles": 1, "requests": 2, "identity_requests": 0})
        self.assertEqual(self.calls[1], ("/consult/getSectionByCid", {"cid": SECTION}))
        self.assertNotIn("X" * 100, result["text"])
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertEqual(result["metadata"]["section_identity_resolution"]["binding"],
                         "explicit_locator_and_exact_dated_version_id")

    def test_invalid_cid_is_rejected_before_any_network(self):
        for cid in ("", "LEGIARTI000000000001", "https://example.test", 1):
            with self.assertRaises(LegifranceError):
                self.read(cid)
        self.assertEqual(self.calls, [])

    def test_primary_cid_does_not_authorize_different_id_or_cid(self):
        for field, value in (("id", SECTION), ("cid", VERSION)):
            p = copy.deepcopy(self.parent)
            p["sections"][0][field] = value
            with mock.patch.object(self, "parent", p), self.assertRaises(LegifranceError):
                self.read()

    def test_primary_duplicates_dates_and_parent_are_blocking(self):
        for mutate in (
            lambda p: p["sections"].append(copy.deepcopy(p["sections"][0])),
            lambda p: p["sections"][0].update(dateFin="2020-01-01"),
            lambda p: p.update(dateDebutVersion=None),
            lambda p: p.update(id="LEGITEXT000000000003"),
        ):
            p = copy.deepcopy(self.parent); mutate(p)
            with mock.patch.object(self, "parent", p), self.assertRaises(LegifranceError):
                self.read()

    def test_structured_other_version_wrong_cid_or_no_versions_cannot_fallback(self):
        self.oversized = True
        for root in (
            {"listSection": []},
            {"listSection": [{**self.root["listSection"][0], "id": SECTION + ".xml"}]},
            {"listSection": [{**self.root["listSection"][0], "cid": VERSION}]},
        ):
            with mock.patch.object(self, "root", root), self.assertRaises(LegifranceError):
                self.read()
            self.assertEqual(self.calls[-1][0], "/consult/getSectionByCid")

    def test_structured_ambiguous_inactive_or_wrong_parent_is_rejected(self):
        self.oversized = True
        for mutate in (
            lambda r: r["listSection"].append(copy.deepcopy(r["listSection"][0])),
            lambda r: r["listSection"][0].update(dateFin="2020-01-01"),
            lambda r: r["listSection"][0]["context"]["titreTxt"][0].update(cid="LEGITEXT000000000003", id="LEGITEXT000000000003"),
        ):
            r = copy.deepcopy(self.root); mutate(r)
            with mock.patch.object(self, "root", r), self.assertRaises(LegifranceError):
                self.read()
            self.assertNotEqual(self.calls[-1][0], "/consult/getArticle")

    def test_structured_body_wrong_parent_or_date_is_rejected(self):
        self.oversized = True
        for mutate in (
            lambda a: a.update(sectionParentId=SECTION),
            lambda a: a.update(dateFin="2020-01-01"),
        ):
            a = copy.deepcopy(self.article); mutate(a["article"])
            with mock.patch.object(self, "article", a), self.assertRaises(LegifranceError):
                self.read()

    def test_original_request_and_content_budgets_are_unchanged(self):
        self.oversized = True
        with mock.patch.object(sections, "MAX_REQUESTS", 1), self.assertRaises(LegifranceError):
            self.read()
        root = copy.deepcopy(self.root)
        root["listSection"][0]["titre"] = "X" * (texts.MAX_RESPONSE_BYTES + 1)
        with mock.patch.object(self, "root", root), self.assertRaises(LegifranceError):
            self.read()
        self.assertEqual(sections.MAX_REQUESTS, 67)
        self.assertEqual(sections.MAX_SECONDS, 90)

    def test_mcp_adapter_forwards_cid_and_keeps_read_only_contract(self):
        with mock.patch.object(server, "_safe_call", return_value={}) as safe:
            server.get_section(VERSION, TEXT, DATE, cid=SECTION)
        safe.assert_called_once_with(tools.get_section, VERSION, TEXT, DATE, cid=SECTION)


if __name__ == "__main__":
    unittest.main()
