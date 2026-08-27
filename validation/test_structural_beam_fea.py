#!/usr/bin/env python3
"""Validate analytic/finite-element cross-checks and intentional open gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = subprocess.run(
        [sys.executable, "calculations/structural/beam_fea.py"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    assert "STRUCTURAL_BEAM_FEA_OK cases=7" in result.stdout
    report = json.loads((ROOT / "simulation" / "structural" / "beam_crosscheck.json").read_text())
    assert report["status"] == "SCREENING_ONLY_NOT_3D_FEA_OR_PHYSICAL_VALIDATION"
    cases = {case["name"]: case for case in report["cases"]}
    assert len(cases) == 7
    for case in cases.values():
        assert case["elements"] == 20
        assert case["deflection_relative_error"] < 1e-8
        assert case["moment_relative_error"] < 1e-8
        assert case["screening_status"] in {"PASS_1D_SCREEN", "REVIEW_REQUIRED"}
    assert cases["stage1_cutter_shaft"]["fea_max_nodal_deflection_mm"] <= 0.2 / 3
    assert cases["spooler_shaft"]["fea_max_nodal_deflection_mm"] <= 0.05
    assert cases["reducer_output_overhang"]["screening_status"] == "REVIEW_REQUIRED"
    assert cases["tower_frame_column"]["screening_status"] == "REVIEW_REQUIRED"
    print("STRUCTURAL_BEAM_FEA_VALIDATION_OK")


if __name__ == "__main__":
    main()
