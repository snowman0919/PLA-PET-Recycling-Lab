#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_fusion_results as importer


class FusionImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.binding, self.models, _ = importer.load_contract()
        self.temp = tempfile.TemporaryDirectory()
        evidence = Path(self.temp.name) / "fusion-evidence.txt"
        evidence.write_text("actual external solver evidence fixture")
        model = self.models["bearing_plate.step"]
        self.row = {
            "run_id": "fixture", "case_id": "LC04", "study_type": "static_stress",
            "source_git_sha": self.binding["engineering_source_sha"],
            "step_file": "bearing_plate.step", "step_sha256": model["step_sha256"],
            "load_case_manifest_sha256": self.binding["load_case_manifest_sha256"],
            "mesh_level": "fine", "element_count": "1000", "metric": "global displacement",
            "value": "0.35", "unit": "mm", "solver_version": "fixture",
            "completed_utc": "2026-08-31T00:00:00Z", "evidence_file": str(evidence),
            "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            "operator": "test", "status": "COMPLETE",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_bound_row_reaches_review_only(self) -> None:
        result = importer.validate_rows([self.row])
        self.assertEqual(result["state"], "CORRELATION_REVIEW")

    def test_each_binding_failure_is_rejected(self) -> None:
        for key in ("source_git_sha", "step_sha256", "load_case_manifest_sha256"):
            bad = dict(self.row)
            bad[key] = "0" * 64
            self.assertEqual(importer.validate_rows([bad])["state"], "INVALID_BINDING")

    def test_case_geometry_study_and_units_are_rejected(self) -> None:
        mutations = [
            ("case_id", "LC99"), ("step_file", "frame.step"),
            ("study_type", "thermal"), ("unit", "inch"),
        ]
        for key, value in mutations:
            bad = dict(self.row)
            bad[key] = value
            self.assertEqual(importer.validate_rows([bad])["state"], "INVALID_BINDING")


if __name__ == "__main__":
    unittest.main()
