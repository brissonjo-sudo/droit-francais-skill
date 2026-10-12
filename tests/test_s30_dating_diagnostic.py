"""Trace S30 sur fixtures factices, sans source officielle ni réseau."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from tests.test_text_consultation import text, DATE as OTHER_DATE
from droit_francais import texts, text_diagnostics as diag
from droit_francais.errors import LegifranceError


def sample():
    """Forme synthétique avec cibles fixes : aucune preuve juridique réelle."""
    payload = text()
    payload["id"] = diag.TEXT + "_01-01-2020"
    section = payload["sections"][0]
    section["id"] = diag.SECTION
    section["cid"] = diag.SECTION
    return payload


class DatingDiagnosticTests(unittest.TestCase):
    def read(self, payload, date=diag.DATE, identifier=diag.TEXT):
        with mock.patch.object(texts, "get_token", return_value="synthetic"), \
                mock.patch.object(texts, "api_call", return_value=payload) as api:
            result = texts.get_text(identifier, date)
        api.assert_called_once_with("/consult/legiPart", {"textId": identifier, "date": date}, "synthetic")
        return result

    def test_absent_and_null_bounds_are_distinct_without_inheritance(self):
        payload = sample()
        section = payload["sections"][0]
        del section["dateDebut"]
        section["dateFin"] = None
        original = copy.deepcopy(payload)
        result = self.read(payload)
        trace = result["metadata"]["source_dating_diagnostic"]
        self.assertEqual(trace["date_fields"]["dateDebut"], {"present": False})
        self.assertEqual(trace["date_fields"]["dateFin"], {"present": True, "type": "null"})
        self.assertIsNone(result["metadata"]["applicable_at_as_of_date"])
        self.assertIsNone(result["sections"][0]["metadata"]["applicable_at_as_of_date"])
        self.assertTrue(result["sections"][0]["articles"][0]["metadata"]["applicable_at_as_of_date"])
        self.assertEqual(payload, original)

    def test_alternative_fields_are_observed_not_used(self):
        payload = sample()
        section = payload["sections"][0]
        del section["dateDebut"]
        del section["dateFin"]
        section.update(dateDebutVersion="2020-01-01", dateFinVersion="2999-01-01")
        result = self.read(payload)
        trace = result["metadata"]["source_dating_diagnostic"]
        self.assertEqual(trace["date_fields"]["dateDebutVersion"]["raw"], "2020-01-01")
        self.assertIsNone(result["metadata"]["applicable_at_as_of_date"])

    def test_integer_float_iso_and_timestamp_preserve_safe_raw_types(self):
        for value in (925430400000, 925430400000.0, "1999-04-30", "1999-04-30T00:00:00Z"):
            with self.subTest(value=value):
                payload = sample()
                payload["sections"][0]["dateDebut"] = value
                trace = diag.s30_dating_diagnostic(payload)
                field = trace["date_fields"]["dateDebut"]
                self.assertEqual(field["raw"], value)
                self.assertEqual(field["type"], type(value).__name__)

    def test_malformed_values_and_unknown_keys_are_not_echoed(self):
        for value in (True, float("nan"), float("inf"), {}, [], 10**1000,
                      "SECRET", "https://secret.invalid/?token=SECRET", "2020-01-01SECRET"):
            with self.subTest(kind=type(value).__name__):
                payload = sample()
                section = payload["sections"][0]
                section.update(dateDebut=value, Authorization="SECRET", content="SECRET")
                section["SECRET_KEY"] = "SECRET"
                trace = diag.s30_dating_diagnostic(payload)
                encoded = json.dumps(trace, allow_nan=False)
                self.assertNotIn("SECRET", encoded)
                self.assertNotIn("Authorization", encoded)
                self.assertNotIn("raw", trace["date_fields"]["dateDebut"])
                self.assertEqual(trace["unlisted_key_count"], 3)

    def test_negative_date_stays_negative(self):
        payload = sample()
        payload["sections"][0]["dateFin"] = "2021-01-01"
        result = self.read(payload)
        self.assertFalse(result["metadata"]["applicable_at_as_of_date"])
        self.assertFalse(result["sections"][0]["metadata"]["node_applicable_at_as_of_date"])

    def test_positive_date_stays_positive(self):
        result = self.read(sample())
        self.assertTrue(result["metadata"]["applicable_at_as_of_date"])
        self.assertFalse(result["metadata"]["source_dating_diagnostic"]["changes_applicability"])

    def test_unrelated_text_and_other_date_have_no_trace(self):
        payload = text()
        result = self.read(payload, identifier=payload["id"].split("_")[0])
        self.assertNotIn("source_dating_diagnostic", result["metadata"])
        result = self.read(sample(), date=OTHER_DATE)
        self.assertNotIn("source_dating_diagnostic", result["metadata"])

    def test_no_date_has_no_trace(self):
        with mock.patch.object(texts, "_consult_date", return_value=diag.DATE), \
                mock.patch.object(texts, "get_token", return_value="synthetic"), \
                mock.patch.object(texts, "api_call", return_value=sample()) as api:
            result = texts.get_text(diag.TEXT)
        api.assert_called_once_with("/consult/legiPart", {"textId": diag.TEXT, "date": diag.DATE}, "synthetic")
        self.assertNotIn("source_dating_diagnostic", result["metadata"])

    def test_target_section_missing_or_ambiguous_is_not_qualified(self):
        for duplicate in (False, True):
            payload = sample()
            if duplicate:
                payload["sections"].append(copy.deepcopy(payload["sections"][0]))
            else:
                payload["sections"][0]["id"] = "LEGISCTA000000000001"
            trace = diag.s30_dating_diagnostic(payload)
            self.assertEqual(trace["status"], "section_ambiguous" if duplicate else "section_absent")
            self.assertNotIn("date_fields", trace)

    def test_deep_path_is_bounded(self):
        payload = sample()
        first = payload["sections"][0]
        payload["sections"] = [{"sections": [first]}]
        trace = diag.s30_dating_diagnostic(payload)
        self.assertEqual(trace["path"], ["sections", 0, "sections", 0])
        self.assertLess(len(json.dumps(trace).encode()), diag.MAX_DETAIL_BYTES)
        node = payload
        for _ in range(34):
            node["sections"] = [{}]
            node = node["sections"][0]
        self.assertEqual(diag.s30_dating_diagnostic(payload)["status"], "inventory_incomplete")

    def test_refusals_precede_trace_and_budgets_unchanged(self):
        payload = sample()
        payload["truncated"] = True
        with mock.patch.object(diag, "s30_dating_diagnostic") as trace, \
                self.assertRaises(LegifranceError):
            self.read(payload)
        trace.assert_not_called()
        self.assertEqual((texts.MAX_NODES, texts.MAX_DEPTH, texts.MAX_RESPONSE_BYTES),
                         (5000, 32, 2_000_000))

    def test_core_dating_functions_unchanged_from_delivery(self):
        import ast
        import hashlib
        expected = {
            "_metadata": "eda06b15c2ce591460d052c83bbef536d04d77cbefb5abf3767da259aaca5395",
            "_aggregate": "4c31844973c0996d5682ba130c00e2f2b57e858033eecdb3bb483d76adb049b2",
            "_bounded": "b90d46cbec3895295ea9c7a2afead143f0e6d11072ff1d6292469663b810e3b5",
            "_article": "de16926be589aea3d640682995c69efc560251b932542a0a976d6d9cbc075c13",
            "_section": "d2563977ed751273d1b3dbf6354a6fbbecb85ab440fe53ced6a8dd902c2f43f1",
            "get_section": "3376c805d8d4de79a8c85c3b4a2723327ac1abd2c6bbe4b30b3e61ccb9853282",
        }
        source = Path(texts.__file__).read_text(encoding="utf-8")
        lines = source.splitlines(keepends=True)
        actual = {node.name: hashlib.sha256("".join(lines[node.lineno-1:node.end_lineno]).encode()).hexdigest()
                  for node in ast.parse(source).body
                  if isinstance(node, ast.FunctionDef) and node.name in expected}
        self.assertEqual(actual, expected)

    def test_diagnostic_size_limit_is_explicit(self):
        with mock.patch.object(diag, "MAX_DETAIL_BYTES", 1):
            trace = diag.s30_dating_diagnostic(sample())
        self.assertEqual(trace["status"], "diagnostic_limit")
        self.assertNotIn("date_fields", trace)

    def test_trace_is_available_through_existing_mcp_tool(self):
        from mcp_server import server
        payload = sample()
        del payload["sections"][0]["dateDebut"]
        with mock.patch.object(texts, "get_token", return_value="synthetic"), \
                mock.patch.object(texts, "api_call", return_value=payload) as api:
            result = server.get_text(diag.TEXT, diag.DATE)
        self.assertEqual(result["metadata"]["source_dating_diagnostic"]["status"], "observed")
        self.assertIsNone(result["metadata"]["applicable_at_as_of_date"])
        api.assert_called_once()


if __name__ == "__main__":
    unittest.main()
