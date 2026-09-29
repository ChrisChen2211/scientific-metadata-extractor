"""Unit tests for deterministic real-data evaluation behavior."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from evaluate_real import classify_mismatch, normalize  # noqa: E402


class NormalizeTests(unittest.TestCase):
    def test_case_punctuation_and_whitespace(self):
        self.assertEqual(normalize("  LC-MS/MS  "), normalize("lc ms ms"))

    def test_numbers_remain_numbers(self):
        self.assertEqual(normalize(23), 23)

    def test_null_remains_null(self):
        self.assertIsNone(normalize(None))


class ErrorClassificationTests(unittest.TestCase):
    def test_missing_information(self):
        self.assertEqual(classify_mismatch("plasma", None), ["missing information"])

    def test_unsupported_information(self):
        self.assertEqual(
            classify_mismatch(None, "serum"),
            ["reference-null disagreement (manual review required)"],
        )

    def test_overly_broad(self):
        self.assertEqual(
            classify_mismatch("healthy adult participants", "participants"),
            ["overly broad extraction"],
        )

    def test_overly_specific(self):
        self.assertEqual(
            classify_mismatch("plasma", "fasting EDTA plasma"),
            ["overly specific extraction"],
        )


if __name__ == "__main__":
    unittest.main()
