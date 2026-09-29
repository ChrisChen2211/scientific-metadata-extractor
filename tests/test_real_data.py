"""Integrity checks for the manually curated real-paper dataset."""

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from manual_semantic_audit import validate_audit  # noqa: E402


FIELDS = {
    "study_design",
    "population",
    "sample_size",
    "intervention_or_exposure",
    "biospecimen",
    "measurement_method",
    "duration_or_timepoints",
}


class RealDataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = json.loads(
            (PROJECT_ROOT / "data" / "real" / "samples.json").read_text(
                encoding="utf-8"
            )
        )
        cls.truth = json.loads(
            (PROJECT_ROOT / "data" / "real" / "ground_truth.json").read_text(
                encoding="utf-8"
            )
        )
        cls.audit = json.loads(
            (PROJECT_ROOT / "data" / "real" / "manual_semantic_audit.json").read_text(
                encoding="utf-8"
            )
        )

    def test_five_samples_have_matching_ground_truth(self):
        self.assertEqual(len(self.samples), 5)
        self.assertEqual(
            {item["id"] for item in self.samples},
            {item["id"] for item in self.truth},
        )

    def test_required_source_metadata_is_present(self):
        for sample in self.samples:
            with self.subTest(sample=sample["id"]):
                for key in (
                    "paper_title",
                    "source_citation",
                    "pmcid",
                    "doi",
                    "source_url",
                    "excerpt",
                ):
                    self.assertTrue(sample[key])
                self.assertTrue(sample["source_url"].startswith("https://pmc.ncbi.nlm.nih.gov/"))

    def test_ground_truth_uses_only_schema_fields(self):
        for item in self.truth:
            with self.subTest(sample=item["id"]):
                self.assertEqual(set(item) - {"id"}, FIELDS)
                self.assertTrue(item["sample_size"] is None or isinstance(item["sample_size"], int))

    def test_semantic_audit_is_complete(self):
        counts, errors = validate_audit(self.audit)
        self.assertEqual(errors, [])
        self.assertEqual(len(self.audit["items"]), 35)
        self.assertEqual(counts["Correct"], 34)
        self.assertEqual(counts["Partially correct"], 1)
        self.assertEqual(counts["Incorrect"], 0)
        self.assertEqual(counts["Unsupported"], 0)

    def test_real_002_study_design_records_human_decision(self):
        item = next(
            item
            for item in self.audit["items"]
            if item["sample_id"] == "real_002" and item["field"] == "study_design"
        )
        self.assertIsNone(item["ground_truth"])
        self.assertEqual(item["label"], "Correct")
        self.assertFalse(item["schema_ambiguity"])


if __name__ == "__main__":
    unittest.main()
