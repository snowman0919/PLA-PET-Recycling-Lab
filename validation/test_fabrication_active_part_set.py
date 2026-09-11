#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release"))
import build_fabrication_release as release


class FabricationActivePartSetTest(unittest.TestCase):
    def test_adds_only_required_purchased_sprockets(self):
        parts = {"CUT-01": 12}
        rows = [
            {"part_id": "GGM_SH_12T", "quantity": "1", "classification": "purchased_reference_envelope"},
            {"part_id": "GGM_SH_30T", "quantity": "1", "classification": "purchased_reference_envelope"},
            {"part_id": "GGM_Shredder", "quantity": "1", "classification": "purchased_reference_envelope"},
        ]
        release.add_purchased_ggm_parts(parts, rows)
        self.assertEqual(parts, {"CUT-01": 12, "GGM_SH_12T": 1, "GGM_SH_30T": 1})

    def test_rejects_classification_drift(self):
        rows = [
            {"part_id": "GGM_SH_12T", "quantity": "1", "classification": "manufactured_or_stock"},
            {"part_id": "GGM_SH_30T", "quantity": "1", "classification": "purchased_reference_envelope"},
        ]
        with self.assertRaises(AssertionError):
            release.add_purchased_ggm_parts({}, rows)


    def test_drawing_register_requires_canonical_revision(self):
        rows = [{"revision": release.REV, "status": "PASS"} for _ in range(20)]
        release.validate_drawing_rows(rows)
        rows[0]["revision"] = "v0.8"
        with self.assertRaises(AssertionError):
            release.validate_drawing_rows(rows)

    def test_rejects_quantity_conflict(self):
        rows = [
            {"part_id": "GGM_SH_12T", "quantity": "1", "classification": "purchased_reference_envelope"},
            {"part_id": "GGM_SH_30T", "quantity": "1", "classification": "purchased_reference_envelope"},
        ]
        with self.assertRaises(AssertionError):
            release.add_purchased_ggm_parts({"GGM_SH_12T": 2}, rows)


if __name__ == "__main__":
    unittest.main()
