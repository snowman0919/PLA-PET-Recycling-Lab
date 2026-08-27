#!/usr/bin/env python3
"""Run every automated design-package check with explicit PASS markers."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PYTHON_TESTS = (
    ("validation/test_dryer_feeder_budget.py", "DRYER_FEEDER_BUDGET_OK"),
    ("validation/test_hot_zone_guard.py", "HOT_ZONE_GUARD_VALIDATION_OK"),
    ("validation/test_two_tower_contract.py", "TWO_TOWER_ARCHITECTURE_VALIDATION_OK"),
    ("validation/test_two_tower_gpu_evidence.py", "TWO_TOWER_GPU_EVIDENCE_VALIDATION_OK"),
    ("validation/test_electronics_interfaces.py", "ELECTRONICS_INTERFACES_OK"),
    ("validation/test_kicad_interface_board.py", "KICAD_INTERFACE_BOARD_OK"),
    ("validation/test_extruder_design.py", "EXTRUDER_DESIGN_SWEEP_OK"),
    ("validation/test_forming_line.py", "FORMING_LINE_DESIGN_OK"),
    ("validation/test_sorter_dynamics.py", "SORTER_DYNAMICS_OK"),
    ("validation/test_bom.py", "BOM_VALIDATION_OK"),
    ("validation/test_requirements_traceability.py", "REQUIREMENTS_TRACEABILITY_OK"),
    ("validation/test_cnc_quote_packages.py", "CNC_QUOTE_PACKAGES_OK"),
    ("validation/test_structural_beam_fea.py", "STRUCTURAL_BEAM_FEA_VALIDATION_OK"),
    ("validation/test_review_variants.py", "CAD_REVIEW_VARIANTS_OK"),
    ("validation/test_manual_coverage.py", "MANUAL_40_TOPIC_COVERAGE_OK"),
)
FREECAD_TESTS = (
    ("validation/test_dryer_geometry.py", "DRYER_GEOMETRY_OK"),
    ("validation/test_forming_geometry.py", "FORMING_GEOMETRY_OK"),
    ("validation/test_sorter_geometry.py", "SORTER_GEOMETRY_OK"),
    ("validation/test_spooler_geometry.py", "SPOOLER_GEOMETRY_OK"),
    ("validation/test_stage1_kinematics.py", "STAGE1_KINEMATIC_VALIDATION_OK"),
    ("validation/test_stage2_kinematics.py", "STAGE2_KINEMATIC_VALIDATION_OK"),
    ("validation/test_stage3_kinematics.py", "STAGE3_KINEMATIC_VALIDATION_OK"),
    ("validation/test_extruder_geometry.py", "EXTRUDER_GEOMETRY_OK"),
    ("validation/test_input_classifier_geometry.py", "INPUT_CLASSIFIER_GEOMETRY_OK"),
    ("validation/test_control_enclosure_geometry.py", "CONTROL_ENCLOSURE_GEOMETRY_OK"),
    ("validation/test_two_tower_geometry.py", "TWO_TOWER_GEOMETRY_VALIDATION_OK"),
    ("validation/test_cad_generation.py", "CAD_VALIDATION_OK"),
)


def run(command: list[str], marker: str, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or marker not in output or "Traceback (most recent call last)" in output:
        print(output, file=sys.stderr)
        raise SystemExit(f"FAIL {marker}: {' '.join(command)}")
    print(f"PASS {marker}")


def main() -> None:
    run([sys.executable, "bom/build_design_boms.py"], '"bom_row_count": 82')
    for script, marker in PYTHON_TESTS:
        run([sys.executable, script], marker)
    for script, marker in FREECAD_TESTS:
        code = f"import runpy; runpy.run_path({script!r}, run_name='__main__')"
        run(["FreeCADCmd", "-c", code], marker)
    run(["make", "-C", "firmware/arduino_mega", "test"], "MEGA_UI_CORE_OK")
    pi_env = os.environ.copy()
    pi_env["PYTHONPATH"] = str(ROOT / "software" / "raspberry_pi")
    run(
        [sys.executable, "-m", "unittest", "discover", "-s", "software/raspberry_pi/tests", "-v"],
        "OK",
        pi_env,
    )
    run([sys.executable, "artifacts/build_manifest.py"], "manifest artifacts=353")
    run([sys.executable, "validation/test_release_package.py"], "RELEASE_PACKAGE_OK")
    print("ALL_AUTOMATED_VALIDATIONS_OK (32 gates)")


if __name__ == "__main__":
    main()
