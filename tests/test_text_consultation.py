"""Contrats de consultation CODE/LEGI : fixtures synthétiques, aucun réseau."""

from __future__ import annotations

import datetime as dt
import base64
import sys
import unittest
from pathlib import Path
from unittest import mock

import jwt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
sys.path.insert(0, str(ROOT))
from droit_francais import texts, tools  # noqa: E402
from droit_francais.errors import LegifranceError  # noqa: E402
from mcp_server import server  # noqa: E402

# Identifiants de forme valide, exclusivement synthétiques : pas des preuves.
TEXT = "LEGITEXT000000000001"
SECTION = "LEGISCTA000000000001"
ARTICLE = "LEGIARTI000000000001"
DATE = "2025-07-25"


def article():
    return {
        "id": ARTICLE,
        "num": "1",
        "content": "<p>Contenu &amp; officiel simulé.</p>",
        "dateDebut": "2020-01-01",
        "dateFin": "2999-01-01",
        "etat": "VIGUEUR",
        "nota": "Note article",
        "intOrdre": 2,
    }


def section():
    return {
        "id": SECTION,
        "cid": SECTION,
        "title": "Chapitre de test",
        "dateDebut": "2020-01-01",
        "dateFin": "2999-01-01",
        "etat": "VIGUEUR",
        "articles": [article()],
        "sections": [],
        "notaHtml": "<p>Note section</p>",
    }


def text():
    return {
        "id": TEXT + "_01-01-2020",
        "cid": "JORFTEXT000000000001",
        "title": "Texte de test",
        "nature": "LOI",
        "etat": "VIGUEUR",
        "dateDebutVersion": "2020-01-01",
        "dateFinVersion": "2999-01-01",
        "visa": "Visa test",
        "signers": "Signataire test",
        "articles": [],
        "sections": [section()],
    }


class ConsultationTests(unittest.TestCase):
    def setUp(self):
        token = mock.patch.object(texts, "get_token", return_value="jeton-factice")
        self.token = token.start()
        self.addCleanup(token.stop)
        api = mock.patch.object(texts, "api_call", return_value=text())
        self.api = api.start()
        self.addCleanup(api.stop)

    def test_section_request_matches_official_schema(self):
        result = tools.get_section(SECTION.lower(), TEXT, DATE)
        self.api.assert_called_once_with(
            "/consult/code",
            {"textId": TEXT, "sctCid": SECTION, "date": DATE},
            "jeton-factice",
        )
        self.assertEqual(result["id"], SECTION)
        self.assertIn("Contenu & officiel simulé.", result["text"])
        self.assertIn("Note section", result["text"])
        self.assertIn("Note article", result["text"])
        self.assertIn(f"/{TEXT}/{SECTION}/{DATE}/", result["url"])
        self.assertTrue(result["metadata"]["verified"])
        self.assertTrue(result["metadata"]["applicable_at_as_of_date"])
        self.assertEqual(result["metadata"]["content_trust"], tools.UNTRUSTED_CONTENT)
        self.assertEqual(result["metadata"]["parent_version_id"], TEXT + "_01-01-2020")

    def test_text_request_and_root_notes(self):
        result = tools.get_text(TEXT, DATE)
        self.api.assert_called_once_with(
            "/consult/legiPart", {"textId": TEXT, "date": DATE}, "jeton-factice"
        )
        self.assertEqual(result["id"], TEXT)
        self.assertIn("Visa test", result["text"])
        self.assertIn("Signataire test", result["text"])
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertIn("hors documents liés", result["metadata"]["completeness_scope"])

    def test_no_date_uses_server_clock(self):
        result = tools.get_text(TEXT)
        self.assertEqual(
            self.api.call_args.args[1]["date"], dt.date.today().isoformat()
        )
        self.assertIsNone(result["metadata"]["requested_date"])
        self.assertEqual(result["metadata"]["date_basis"], "date du jour du serveur")

    def test_historical_version_is_not_silently_replaced(self):
        self.api.return_value["dateFinVersion"] = "2021-01-01"
        result = tools.get_text(TEXT, DATE)
        self.assertFalse(result["metadata"]["applicable_at_as_of_date"])
        self.assertTrue(result["metadata"]["verified"])
        self.assertEqual(self.api.call_count, 1)

    def test_explicit_past_date_caveat_survives(self):
        result = tools.get_text(TEXT, DATE)
        self.assertIn("Version applicable au", result["metadata"]["caveat"])

    def test_missing_or_bad_dates_never_confirm_applicability(self):
        for value in (
            None,
            "pas-une-date",
            "2025-02-31",
            10**100,
            {},
            [],
            "2999-01-01-invalide",
        ):
            with self.subTest(value=value):
                self.api.return_value = text()
                self.api.return_value["dateFinVersion"] = value
                result = tools.get_text(TEXT, DATE)
                self.assertIsNone(result["metadata"]["applicable_at_as_of_date"])

    def test_iso_timestamp_bounds_remain_supported(self):
        self.api.return_value["dateDebutVersion"] = "2020-01-01T00:00:00Z"
        self.api.return_value["dateFinVersion"] = "2999-01-01T00:00:00+00:00"
        self.assertTrue(
            tools.get_text(TEXT, DATE)["metadata"]["applicable_at_as_of_date"]
        )

    def test_expired_descendant_prevents_global_vigour_claim(self):
        self.api.return_value["sections"][0]["articles"][0]["dateFin"] = "2021-01-01"
        result = tools.get_section(SECTION, TEXT, DATE)
        self.assertFalse(result["metadata"]["applicable_at_as_of_date"])
        self.assertTrue(result["metadata"]["node_applicable_at_as_of_date"])

    def test_undated_descendant_prevents_global_vigour_claim(self):
        del self.api.return_value["sections"][0]["articles"][0]["dateDebut"]
        self.assertIsNone(
            tools.get_text(TEXT, DATE)["metadata"]["applicable_at_as_of_date"]
        )

    def test_parent_or_resource_identity_mismatch_refused(self):
        for identifier in (None, "LEGITEXT000000000002", TEXT + "_99-99-2020"):
            with self.subTest(id=identifier):
                self.api.return_value = text()
                self.api.return_value["id"] = identifier
                with self.assertRaises(LegifranceError):
                    tools.get_section(SECTION, TEXT, DATE)

    def test_selected_subtree_only_not_sibling_summaries(self):
        sibling = {"id": "LEGISCTA000000000002", "title": "Sommaire voisin"}
        self.api.return_value["sections"].append(sibling)
        self.assertNotIn(
            "Sommaire voisin", tools.get_section(SECTION, TEXT, DATE)["text"]
        )
        with self.assertRaises(LegifranceError):
            tools.get_text(TEXT, DATE)

    def test_cid_can_designate_version_but_returned_id_is_preserved(self):
        version = "LEGISCTA000000000003"
        self.api.return_value["sections"][0]["id"] = version
        result = tools.get_section(SECTION, TEXT, DATE)
        self.assertEqual(result["id"], version)
        self.assertEqual(result["metadata"]["requested_id"], SECTION)

    def test_missing_or_ambiguous_section_refused(self):
        for sections in ([], [section(), section()]):
            self.api.return_value["sections"] = sections
            with self.assertRaises(LegifranceError):
                tools.get_section(SECTION, TEXT, DATE)

    def test_nested_order_and_sections_are_preserved(self):
        child = section()
        child.update(
            id="LEGISCTA000000000002",
            cid="LEGISCTA000000000002",
            title="Sous-section",
            articles=[],
            commentaire="Sans dispositions",
            intOrdre=1,
        )
        self.api.return_value["sections"][0]["sections"] = [child]
        result = tools.get_section(SECTION, TEXT, DATE)
        self.assertEqual(result["sections"][0]["id"], child["id"])
        self.assertLess(
            result["text"].index("Sous-section"), result["text"].index("Article 1")
        )

    def test_section_with_explicit_no_disposition_comment_is_supported(self):
        self.api.return_value["sections"][0].update(
            articles=[], commentaire="Sans dispositions"
        )
        self.assertIn(
            "Sans dispositions", tools.get_section(SECTION, TEXT, DATE)["text"]
        )

    def test_footnote_does_not_turn_a_summary_into_full_content(self):
        self.api.return_value["sections"][0]["articles"] = []
        with self.assertRaises(LegifranceError):
            tools.get_section(SECTION, TEXT, DATE)

    def test_loda_nodes_do_not_invent_code_section_links(self):
        result = tools.get_text(TEXT, DATE)
        self.assertEqual(result["sections"][0]["url"], result["url"])
        self.assertIn("/loda/article_lc/", result["sections"][0]["articles"][0]["url"])

    def test_invalid_inputs_fail_before_token_or_network(self):
        for callback in (
            lambda: tools.get_text("https://example.test/"),
            lambda: tools.get_text("JORFTEXT000000000001"),
            lambda: tools.get_section("LEGISCTA000000000001/x", TEXT),
            lambda: tools.get_section(SECTION, "LEGIARTI000000000001"),
            lambda: tools.get_text(TEXT, "2025-02-31"),
            lambda: tools.get_text(TEXT, "20250725"),
            lambda: tools.get_text(TEXT, "2025-W30-5"),
        ):
            with self.assertRaises(LegifranceError) as error:
                callback()
            self.assertEqual(error.exception.exit_code, 2)
        self.api.assert_not_called()
        self.token.assert_not_called()

    def test_incomplete_and_malformed_payloads_refused(self):
        payloads = [None, {}, text()]
        payloads[-1]["sections"][0]["articles"][0]["content"] = ""
        for key, value in (
            ("nextCursor", "suite"),
            ("truncated", True),
            ("complete", False),
            ("articles", None),
            ("sections", ["invalide"]),
        ):
            payload = text()
            payload[key] = value
            payloads.append(payload)
        for payload in payloads:
            with self.subTest(payload=payload):
                self.api.return_value = payload
                with self.assertRaises(LegifranceError):
                    tools.get_text(TEXT, DATE)

    def test_volume_and_depth_limits_fail_closed(self):
        for limit in ("MAX_NODES", "MAX_DEPTH", "MAX_RESPONSE_BYTES"):
            with mock.patch.object(texts, limit, 0):
                with self.assertRaises(LegifranceError):
                    tools.get_text(TEXT, DATE)

    def test_upstream_error_is_propagated_not_fabricated(self):
        self.api.side_effect = LegifranceError("amont indisponible", exit_code=4)
        with self.assertRaises(LegifranceError):
            tools.get_text(TEXT)

    def test_fetch_routes_texts_and_refuses_sections_without_parent(self):
        tools.fetch(TEXT)
        self.assertEqual(self.api.call_args.args[0], "/consult/legiPart")
        with mock.patch.object(tools, "get_decision") as decision:
            with self.assertRaises(LegifranceError):
                tools.fetch(SECTION)
            with self.assertRaises(LegifranceError):
                tools.fetch("JORFTEXT000000000001")
            decision.assert_not_called()

    def test_server_wrappers_use_safe_call(self):
        with mock.patch.object(server, "_safe_call", return_value={}) as safe:
            server.get_section(SECTION, TEXT, DATE)
            safe.assert_called_once_with(tools.get_section, SECTION, TEXT, DATE)
            safe.reset_mock()
            server.get_text(TEXT, DATE)
            safe.assert_called_once_with(tools.get_text, TEXT, DATE)

    def test_server_masks_upstream_errors(self):
        self.api.side_effect = LegifranceError("contenu incomplet", exit_code=5)
        with self.assertRaises(server.ToolError) as error:
            server.get_text(TEXT)
        self.assertIn("non vérifiée", str(error.exception))


class DependencyRegressionTests(unittest.TestCase):
    def test_recursive_unsigned_payload_has_a_controlled_decode_error(self):
        """GHSA-42vr-xj54-vc7v : vrai parseur, sans signature ni réseau."""

        # Déterministe même si le runtime refuse une grande charge utile
        # avant JSON : tester aussi la conversion à la frontière du parseur.
        with mock.patch.object(jwt.api_jwt.json, "loads", side_effect=RecursionError):
            with self.assertRaises(jwt.DecodeError):
                jwt.api_jwt.PyJWT()._decode_payload({"payload": b"{}"})

        def encode(value: bytes) -> bytes:
            return base64.urlsafe_b64encode(value).rstrip(b"=")

        depth = max(2000, sys.getrecursionlimit() + 100)
        header = encode(b'{"alg":"RS256","kid":"fixture"}')
        payload = encode(b"[" * depth + b"]" * depth)
        token = (header + b"." + payload + b"." + encode(b"signature-factice")).decode()
        client = jwt.PyJWKClient("https://example.test/jwks")
        with mock.patch.object(
            client, "fetch_data", side_effect=AssertionError("Réseau interdit")
        ):
            for decode in (
                lambda: jwt.decode(token, options={"verify_signature": False}),
                lambda: client.get_signing_key_from_jwt(token),
            ):
                with self.subTest(path=decode), self.assertRaises(jwt.DecodeError):
                    decode()


if __name__ == "__main__":
    unittest.main()
