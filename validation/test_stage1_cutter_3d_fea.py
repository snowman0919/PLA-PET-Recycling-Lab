#!/usr/bin/env python3
"""Regenerate and validate the Stage-1 CAD-based linear-static FEA screen."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "simulation" / "structural" / "stage1_cutter_3d_fea.json"


def main() -> None:
    result = subprocess.run(
        [sys.executable, "simulation/structural/stage1_cutter_3d_fea.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "STAGE1_CUTTER_3D_FEA_OK" in result.stdout
    report = json.loads(REPORT.read_text())
    assert report["status"] == (
        "CAD_BASED_LINEAR_STATIC_SCREEN_ONLY_NOT_CONTACT_IMPACT_FATIGUE_OR_PHYSICAL_VALIDATION"
    )
    assert report["solver"]["element"] == "C3D4 linear tetrahedron"
    assert report["input"]["proof_torque_nm"] == 60.0
    assert len(report["meshes"]) == 2
    coarse, fine = report["meshes"]
    assert coarse["maximum_element_size_mm"] == 2.0
    assert fine["maximum_element_size_mm"] == 1.5
    assert fine["node_count"] > coarse["node_count"]
    assert fine["tetrahedron_count"] > coarse["tetrahedron_count"]
    assert coarse["loaded_node_count"] >= 4
    assert fine["loaded_node_count"] >= 4
    assert fine["maximum_displacement_mm"] <= 0.0667
    assert report["derived"]["fine_mesh_provisional_yield_safety_factor"] >= 1.5
    assert report["derived"]["coarse_fine_displacement_relative_delta"] <= 0.05
    assert report["derived"]["fine_mesh_force_balance_relative_error"] <= 0.01
    load_cases = report["linear_load_cases"]
    assert [case["system_torque_nm"] for case in load_cases] == [6.3, 27.0, 36.8, 54.0, 60.0]
    assert all(case["provisional_yield_safety_factor"] >= 1.5 for case in load_cases)
    assert load_cases[-1]["maximum_displacement_mm"] == fine["maximum_displacement_mm"]
    assert all(report["acceptance_checks"].values())
    assert report["overall_screen_pass"] is True
    limitations = " ".join(report["limitations"]).lower()
    for required in ("contact", "impact", "fatigue", "physical", "certificate"):
        assert required in limitations
    print("STAGE1_CUTTER_3D_FEA_VALIDATION_OK")


if __name__ == "__main__":
    main()
