"""Mesures de consultation et refus sans troncature : données synthétiques."""

from __future__ import annotations

import json
import unittest
from unittest import mock

from tests.test_text_consultation import DATE, SECTION, TEXT, article, server, text
from droit_francais import texts, tools
from droit_francais.errors import LegifranceError


class ConsultationLimitTests(unittest.TestCase):
    def setUp(self):
        token = mock.patch.object(texts, "get_token", return_value="jeton-factice")
        token.start()
        self.addCleanup(token.stop)
        api = mock.patch.object(texts, "api_call", return_value=text())
        self.api = api.start()
        self.addCleanup(api.stop)

    def assert_metric(self, callback, metric, limit):
        with self.assertRaises(LegifranceError) as error:
            callback()
        diagnostic = json.loads(error.exception.detail)
        self.assertEqual(error.exception.exit_code, 5)
        self.assertEqual(diagnostic["kind"], "consultation_limit")
        self.assertEqual(diagnostic["metric"], metric)
        self.assertEqual(diagnostic["limit"], limit)
        self.assertGreater(diagnostic["observed_at_least"], limit)
        return error.exception, diagnostic

    def test_precise_byte_node_and_depth_metrics(self):
        for constant, metric, limit in (
            ("MAX_RESPONSE_BYTES", "bytes_json", 100),
            ("MAX_NODES", "nodes", 2),
            ("MAX_DEPTH", "depth", 1),
        ):
            with self.subTest(metric=metric), mock.patch.object(texts, constant, limit):
                self.assert_metric(
                    lambda: tools.get_section(SECTION, TEXT, DATE), metric, limit
                )

    def test_utf8_measure_and_exact_boundary_match_historical_encoding(self):
        payload = text()
        payload["title"] = "Épreuve 🚓"
        exact = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        stats = {}
        with mock.patch.object(texts, "MAX_RESPONSE_BYTES", exact):
            self.assertIs(texts._bounded(payload, stats=stats), payload)
        self.assertEqual(stats, {"bytes_json": exact, "nodes": 3, "max_depth": 2})
        with mock.patch.object(texts, "MAX_RESPONSE_BYTES", exact - 1):
            self.assert_metric(lambda: texts._bounded(payload), "bytes_json", exact - 1)

    def test_size_control_does_not_build_another_full_serialized_response(self):
        # json.dumps de l'ancien chemin doit être absent pour un succès.
        with mock.patch.object(
            texts.json, "dumps", side_effect=AssertionError("Copie complète interdite")
        ):
            self.assertIsInstance(texts._bounded(text()), dict)

    def test_stops_encoding_as_soon_as_limit_is_known_exceeded(self):
        payload = text()
        original_iterencode = json.JSONEncoder.iterencode

        def chunks():
            yield "x" * 101
            raise AssertionError("L'encodeur ne doit pas être consommé après le refus")

        def encode(encoder, value, *args, **kwargs):
            # Le petit diagnostic d'erreur utilise lui aussi JSONEncoder.
            if value is payload:
                return chunks()
            return original_iterencode(encoder, value, *args, **kwargs)

        with (
            mock.patch.object(texts, "MAX_RESPONSE_BYTES", 100),
            mock.patch.object(texts.json.JSONEncoder, "iterencode", encode),
        ):
            self.assert_metric(lambda: texts._bounded(payload), "bytes_json", 100)

    def test_parent_and_selected_subtree_measures_are_separate(self):
        self.api.return_value["sections"].append(
            {"id": "LEGISCTA000000000002", "title": "Sommaire voisin"}
        )
        result = tools.get_section(SECTION, TEXT, DATE)
        response = result["metadata"]["response_volume"]
        selected = result["metadata"]["section_volume"]
        self.assertEqual(response["nodes"], 4)
        self.assertEqual(selected["nodes"], 2)
        self.assertGreater(response["bytes_json"], selected["bytes_json"])
        self.assertNotIn("Sommaire voisin", result["text"])

    def test_large_parent_is_not_bypassed_by_selecting_a_small_subtree(self):
        self.api.return_value["extra"] = "x" * (texts.MAX_RESPONSE_BYTES + 1)
        with mock.patch.object(texts, "_section") as normalize:
            self.assert_metric(
                lambda: tools.get_section(SECTION, TEXT, DATE),
                "bytes_json",
                texts.MAX_RESPONSE_BYTES,
            )
        normalize.assert_not_called()
        # Le parent refusé n'est toujours pas exploité. Seule une lecture
        # indépendante de structure est tentée ; la fixture la rend également
        # trop volumineuse, donc aucun article ni résultat partiel n'est servi.
        self.assertEqual(
            [call.args[0] for call in self.api.call_args_list],
            ["/consult/code", "/consult/getSectionByCid"],
        )

    def test_incomplete_article_flags_are_checked_before_normalization(self):
        for key, value in (
            ("complete", False),
            ("content_complete", False),
            ("truncated", True),
            ("nextCursor", "suite"),
        ):
            for callback in (
                lambda: tools.get_section(SECTION, TEXT, DATE),
                lambda: tools.get_text(TEXT, DATE),
            ):
                with self.subTest(key=key):
                    self.api.return_value = text()
                    self.api.return_value["sections"][0]["articles"][0][key] = value
                    with self.assertRaises(LegifranceError):
                        callback()

    def test_root_article_counts_and_depth_are_measured(self):
        payload = text()
        payload.update(sections=[], articles=[article()])
        self.api.return_value = payload
        result = tools.get_text(TEXT, DATE)
        stats = result["metadata"]["response_volume"]
        self.assertEqual(stats["nodes"], 2)
        self.assertEqual(stats["max_depth"], 1)

    def test_structure_checked_before_encoding_deep_or_cyclic_sections(self):
        payload = text()
        payload["sections"][0]["sections"].append(payload["sections"][0])
        original_iterencode = json.JSONEncoder.iterencode

        def encode(encoder, value, *args, **kwargs):
            if value is payload:
                raise AssertionError("Le parcours borné doit refuser avant l'encodage")
            return original_iterencode(encoder, value, *args, **kwargs)

        with mock.patch.object(texts.json.JSONEncoder, "iterencode", encode):
            self.assert_metric(
                lambda: texts._bounded(payload), "depth", texts.MAX_DEPTH
            )

    def test_unknown_field_cycle_and_invalid_unicode_fail_closed(self):
        for value in ("\ud800", object()):
            payload = text()
            payload["extra"] = value
            with self.assertRaises(LegifranceError):
                texts._bounded(payload)
        payload = text()
        payload["extra"] = payload
        with self.assertRaises(LegifranceError):
            texts._bounded(payload)

    def test_errors_never_export_source_content_or_identifiers(self):
        payload = text()
        payload["extra"] = "canari-source-confidentielle-" * 20
        with mock.patch.object(texts, "MAX_RESPONSE_BYTES", 100):
            error, diagnostic = self.assert_metric(
                lambda: texts._bounded(payload), "bytes_json", 100
            )
        public_and_log = str(error) + error.detail
        for forbidden in ("canari-source", TEXT, SECTION, "jeton-factice"):
            self.assertNotIn(forbidden, public_and_log)
        self.assertEqual(
            set(diagnostic), {"kind", "scope", "metric", "observed_at_least", "limit"}
        )

    def test_selected_section_must_still_be_complete_and_dated(self):
        self.api.return_value["sections"][0]["articles"][0]["dateFin"] = "2021-01-01"
        result = tools.get_section(SECTION, TEXT, DATE)
        self.assertFalse(result["metadata"]["applicable_at_as_of_date"])
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertIn("section_volume", result["metadata"])

    def test_mcp_exposes_only_safe_metrics_with_correlation_reference(self):
        self.api.return_value["extra"] = "canari-source-confidentielle-" * 20
        with (
            mock.patch.object(texts, "MAX_RESPONSE_BYTES", 100),
            self.assertLogs("droit_francais.mcp", level="WARNING") as logs,
        ):
            with self.assertRaises(server.ToolError) as error:
                server.get_section(SECTION, TEXT, DATE)
        public = str(error.exception)
        self.assertIn("response, bytes_json", public)
        self.assertIn("plafond 100", public)
        self.assertIn("non vérifiée", public)
        self.assertRegex(public, r"\[réf\. [0-9a-f]{8}\]")
        for forbidden in ("canari-source", TEXT, SECTION, "jeton-factice"):
            self.assertNotIn(forbidden, public + " ".join(logs.output))


if __name__ == "__main__":
    unittest.main()
