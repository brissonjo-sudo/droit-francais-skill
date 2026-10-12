"""Bornes millisecondes CODE : fixtures synthétiques, aucun réseau."""
from __future__ import annotations

import copy
import datetime as dt
import unittest
from unittest import mock

from tests.test_text_consultation import DATE, SECTION, TEXT, text
from droit_francais import texts, tools


def milliseconds(value: str) -> int:
    epoch = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    instant = dt.datetime.combine(dt.date.fromisoformat(value), dt.time(), dt.timezone.utc)
    return int((instant - epoch).total_seconds() * 1000)


class NumericSectionDateTests(unittest.TestCase):
    def test_numeric_milliseconds_preserve_raw_and_normalized_bounds(self):
        node = {"dateDebut": milliseconds("2017-04-21"),
                "dateFin": milliseconds("2999-01-01")}
        result = texts._metadata(node, "2026-10-05")
        self.assertEqual(result["start_date"], node["dateDebut"])
        self.assertEqual(result["end_date"], node["dateFin"])
        self.assertEqual(result["version_start_date"], "2017-04-21")
        self.assertEqual(result["version_end_date"], "2999-01-01")
        self.assertIs(result["applicable_at_as_of_date"], True)

    def test_whole_section_with_numeric_child_dates_remains_dated(self):
        payload = text()
        child = payload["sections"][0]["articles"][0]
        child["dateDebut"] = milliseconds("2020-01-01")
        child["dateFin"] = milliseconds("2999-01-01")
        before = copy.deepcopy(payload)
        with mock.patch.object(texts, "get_token", return_value="jeton-factice"), \
             mock.patch.object(texts, "api_call", return_value=payload) as api:
            result = tools.get_section(SECTION, TEXT, DATE)
        self.assertIs(result["metadata"]["applicable_at_as_of_date"], True)
        self.assertIs(result["articles"][0]["metadata"]["applicable_at_as_of_date"], True)
        self.assertTrue(result["metadata"]["content_complete"])
        self.assertEqual(payload, before)
        self.assertEqual(api.call_count, 1)

    def test_numeric_root_and_section_bounds(self):
        for root in (False, True):
            with self.subTest(root=root):
                node = {"dateDebutVersion" if root else "dateDebut": milliseconds("2020-01-01"),
                        "dateFinVersion" if root else "dateFin": milliseconds("2999-01-01")}
                self.assertIs(texts._metadata(node, DATE, root=root)["applicable_at_as_of_date"], True)

    def test_numeric_end_is_exclusive_and_future_start_is_false(self):
        for start, end in (("2020-01-01", DATE), ("2030-01-01", "2999-01-01")):
            with self.subTest(start=start, end=end):
                result = texts._metadata({"dateDebut": milliseconds(start),
                    "dateFin": milliseconds(end)}, DATE)
                self.assertIs(result["applicable_at_as_of_date"], False)

    def test_invalid_numbers_do_not_create_open_bounds_or_raise(self):
        for value in (True, False, float("nan"), float("inf"), float("-inf"), 10**100, -10**100):
            for key in ("dateDebut", "dateFin"):
                with self.subTest(value=value, key=key):
                    node = {"dateDebut": "2020-01-01", "dateFin": "2999-01-01", key: value}
                    self.assertIsNone(texts._metadata(node, DATE)["applicable_at_as_of_date"])

    def test_missing_and_non_date_types_still_unknown(self):
        for value in (None, "", {}, [], "2999-01-01-junk", "32472144000000"):
            with self.subTest(value=value):
                self.assertIsNone(texts._metadata({"dateDebut": "2020-01-01",
                    "dateFin": value}, DATE)["applicable_at_as_of_date"])

    def test_iso_dates_and_timestamps_still_supported(self):
        for end in ("2999-01-01", "2999-01-01T00:00:00Z", "2999-01-01T00:00:00+00:00"):
            with self.subTest(end=end):
                self.assertIs(texts._metadata({"dateDebut": "2020-01-01",
                    "dateFin": end}, DATE)["applicable_at_as_of_date"], True)

    def test_epoch_and_pre_epoch_are_not_missing_or_local_dates(self):
        for value, expected in ((0, "1970-01-01"), (-1, "1969-12-31"), (0.0, "1970-01-01")):
            with self.subTest(value=value):
                metadata = texts._metadata({"dateDebut": value, "dateFin": "2999-01-01"}, DATE)
                self.assertEqual(metadata["version_start_date"], expected)


if __name__ == "__main__":
    unittest.main()
