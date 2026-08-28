#!/usr/bin/env python3
"""Rebuild and validate the v0.4 digital fabrication baseline."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, marker):
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or marker not in output:
        print(output, file=sys.stderr)
        raise SystemExit(f"FAIL {marker}: {' '.join(cmd)}")
    print(f"PASS {marker}")


def nix(command):
    return ["nix", "develop", "--command", "bash", "-lc", command]


def main():
    run([sys.executable, "validation/configuration_control.py"], "CONFIGURATION_CONTROL_OK")
    run([sys.executable, "bom/build_budget_views.py"], "CONDITIONAL_AND_VERIFIED_BUDGET_OK")
    run([sys.executable, "calculations/run_engineering.py"], "ENGINEERING_CALCULATIONS_OK")
    run([sys.executable, "firmware/arduino_mega/generate_config.py"], "FIRMWARE_CONFIG_SYNC_OK")
    run(["make", "-C", "firmware/arduino_mega", "test"], "SHREDDER_CALIBRATED_TORQUE_RPM_RETRY_OK")

    generation = 'FreeCADCmd -c \'import runpy; runpy.run_path("cad/generation/generate_all.py", run_name="__main__")\''
    run(["bash", "-lc", generation] if shutil.which("FreeCADCmd") else nix(generation), "CAD_TO_MODELICA_PARAMETER_SYNC_OK")
    for script, marker in (
        ("validation/solid_topology.py", "SOLID_BREP_TOPOLOGY_OK"),
        ("validation/freecad_checks.py", "FREECAD_COLLISION_LOAD_PATH_OK"),
        ("validation/manufacturing_checks.py", "MANUFACTURING_GEOMETRY_RFQ_OK"),
        ("validation/print_interface_checks.py", "MINIMUM_WALL_FASTENER_INSERT_OK"),
        ("validation/motion_checks.py", "FULL_MOTION_ENVELOPE_OK"),
        ("validation/cutter_phase_sweep.py", "CUTTER_PHASE_SWEEP_OK"),
    ):
        command = f'FreeCADCmd -c \'import runpy; runpy.run_path("{script}", run_name="__main__")\''
        run(["bash", "-lc", command] if shutil.which("FreeCADCmd") else nix(command), marker)
    run([sys.executable, "validation/mesh_checks.py"], "MESH_WATERTIGHT_MANIFOLD_OK")
    run([sys.executable, "validation/slice_prints.py"] if shutil.which("prusa-slicer") else nix("python3 validation/slice_prints.py"), "SLICER_SUCCESS_OK")
    run([sys.executable, "validation/modelica_library_check.py"], "MODELICA_MSL_CAD_BRIDGE_OK")

    run(nix("omc simulation/openmodelica/scripts/checkModel.mos"), "Check of PLA_PET_Recycler.Systems.FullMechanicalSystem completed successfully")
    run(nix("omc simulation/openmodelica/scripts/run_all.mos"), "FullMechanicalNominal_res.csv")
    run(nix("omc simulation/openmodelica/scripts/run_parameter_sweeps.mos"), "SweepBacklashHigh_res.csv")
    run([sys.executable, "simulation/openmodelica/postprocess/summarize_results.py"], "OPENMODELICA_ACCEPTANCE_OK")
    run([sys.executable, "simulation/openmodelica/postprocess/generate_plots.py"], "OPENMODELICA_PLOTS_OK")
    run(nix("python3 analysis/structural/run_load_checks.py"), "STRUCTURAL_SCREENING_OK")

    if "--regenerate-renders" in sys.argv or not (ROOT / "renders/assembly/compact_full_assembly_isometric.png").exists():
        render = 'FreeCADCmd -c \'import runpy; runpy.run_path("cad/generation/render_views.py", run_name="__main__")\''
        run(["bash", "-lc", render] if shutil.which("FreeCADCmd") else nix(render), "COMPACT_RENDER_GENERATION_OK")
    else:
        print("PASS COMPACT_RENDER_PACKAGE_PRESENT")

    typst = " && ".join([
        "typst compile --root . docs/build_manual_ko.typ docs/build_manual_ko.pdf",
        "typst compile --root . docs/design_report_ko.typ docs/design_report_ko.pdf",
        "typst compile --root . docs/digital_release_report_ko.typ docs/digital_release_report_ko.pdf",
        "typst compile --root . exports/cnc/extruder/rfq_drawing_ko.typ exports/cnc/extruder/rfq_drawing_ko.pdf",
        "typst compile --root . exports/jigs/gate1/gate1_assembly_ko.typ exports/jigs/gate1/gate1_assembly_ko.pdf",
        "echo DIGITAL_PDF_BUILD_OK",
    ])
    run(["bash", "-lc", typst] if shutil.which("typst") else nix(typst), "DIGITAL_PDF_BUILD_OK")
    run([sys.executable, "artifacts/build_manifest.py"], "ARTIFACT_MANIFEST_OK")
    run([sys.executable, "validation/test_release.py"], "SOLID_MANIFOLD_OPENMODELICA_RELEASE_VALIDATION_OK")
    print("ALL_DIGITAL_VALIDATIONS_OK; PHYSICAL_NOT_RUN; MAIN_PROMOTION_LOCKED")


if __name__ == "__main__":
    main()
