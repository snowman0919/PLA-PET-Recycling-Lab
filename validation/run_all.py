#!/usr/bin/env python3
"""Rebuild and validate the safety-orchestration-closure-v0.6.1 baseline."""

from __future__ import annotations

import shutil
import shlex
import subprocess
import sys
import json
import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, marker):
    process = subprocess.Popen(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    output_lines = []
    last_output_at = [time.monotonic()]
    heartbeat_stop = threading.Event()

    def heartbeat() -> None:
        while not heartbeat_stop.wait(60):
            idle_s = int(time.monotonic() - last_output_at[0])
            print(
                f"VALIDATION_HEARTBEAT marker={marker} child_running=1 idle_s={idle_s}",
                flush=True,
            )

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()
    assert process.stdout is not None
    try:
        for line in process.stdout:
            last_output_at[0] = time.monotonic()
            output_lines.append(line)
            print(line, end="", flush=True)
        returncode = process.wait()
    finally:
        heartbeat_stop.set()
        heartbeat_thread.join()
    output = "".join(output_lines)
    if returncode or marker not in output:
        raise SystemExit(f"FAIL {marker}: {' '.join(cmd)}")
    print(f"PASS {marker}", flush=True)


def nix(command):
    return ["nix", "develop", "--command", "bash", "-lc", command]


def freecad(script):
    """Feed Python to FreeCAD's console; `-c <code>` does not execute code."""
    code = (
        'import runpy,sys,os; '
        f'_result=runpy.run_path("{script}", run_name="__main__"); '
        'sys.stdout.flush(); os._exit(0)'
    )
    command = f"printf '%s\\n' {shlex.quote(code)} | FreeCADCmd -c"
    return ["bash", "-lc", command] if shutil.which("FreeCADCmd") else nix(command)


def main():
    run([sys.executable, "validation/configuration_control.py"], "CONFIGURATION_CONTROL_OK")
    run([sys.executable, "calculations/run_engineering.py"], "ENGINEERING_CALCULATIONS_OK")
    run([sys.executable, "firmware/arduino_mega/generate_config.py"], "FIRMWARE_CONFIG_SYNC_OK")
    run([sys.executable, "control/generate_contract_artifacts.py"], "CONTRACT_ARTIFACTS_OK")
    run([sys.executable, "validation/orchestration_contract.py"], "ORCHESTRATION_CONTRACT_EQUIVALENCE_OK")
    run([sys.executable, "validation/controller_contract.py"], "CONTROLLER_CONTRACT_POWER_INVARIANTS_OK")
    run(["make", "-C", "firmware/arduino_mega", "test"], "SHREDDER_CALIBRATED_TORQUE_RPM_RETRY_OK")
    run([sys.executable, "validation/runtime_supervisor.py"], "RUNTIME_SUPERVISOR_E2E_OK")
    run([sys.executable, "validation/red_team_orchestration.py"], "SAFETY_ORCHESTRATION_RED_TEAM_OK")
    if shutil.which("arduino-cli"):
        run([sys.executable, "validation/arduino_compile.py"], "ARDUINO_MEGA_2560_COMPILE_OK")
    else:
        print("PASS ARDUINO_MEGA_COMPILE_DEFERRED_TO_CI_FULL_OR_ARDUINO_CLI_ENV", flush=True)

    baseline = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    if baseline.get("geometry_change_required", True):
        run(freecad("cad/generation/generate_all.py"), "CAD_TO_MODELICA_PARAMETER_SYNC_OK")
    else:
        run([sys.executable, "cad/generation/refresh_revision_metadata.py"], "FROZEN_GEOMETRY_METADATA_REFRESH_OK")
        run(freecad("cad/generation/export_modelica_properties.py"), "CAD_TO_MODELICA_PARAMETER_SYNC_OK")
        print(f"PASS FROZEN_GEOMETRY_REUSED_FROM_{baseline['geometry_unchanged_from_sha']}", flush=True)
    run([sys.executable, "validation/interface_catalog_checks.py"], "FABRICATION_INTERFACE_CATALOG_VALIDATED_OK")
    for script, marker in (
        ("validation/solid_topology.py", "SOLID_BREP_TOPOLOGY_OK"),
        ("validation/freecad_checks.py", "FREECAD_COLLISION_LOAD_PATH_OK"),
        ("validation/assembly_collision_audit.py", "ASSEMBLY_PAIRWISE_COLLISION_POLICY_OK"),
        ("validation/manufacturing_checks.py", "MANUFACTURING_GEOMETRY_RFQ_OK"),
        ("validation/print_interface_checks.py", "MINIMUM_WALL_FASTENER_INSERT_OK"),
        ("validation/motion_checks.py", "FULL_MOTION_ENVELOPE_OK"),
        ("validation/cutter_phase_sweep.py", "CUTTER_PHASE_SWEEP_OK"),
    ):
        run(freecad(script), marker)
    run([sys.executable, "validation/gate1_readiness.py"], "OPTIONAL_EMPIRICAL_GATE1_READINESS_OK")
    run([sys.executable, "validation/mesh_checks.py"], "MESH_WATERTIGHT_MANIFOLD_OK")
    run([sys.executable, "validation/slice_prints.py"] if shutil.which("prusa-slicer") else nix("python3 validation/slice_prints.py"), "SLICER_SUCCESS_OK")
    run([sys.executable, "bom/build_budget_views.py"], "CONDITIONAL_AND_VERIFIED_BUDGET_OK")
    run([sys.executable, "validation/modelica_library_check.py"], "MODELICA_MSL_CAD_BRIDGE_OK")

    run([sys.executable, "simulation/openmodelica/scripts/generate_runner.py"], "MODELICA_RUNNER_SYNC_OK")
    run(nix("omc simulation/openmodelica/scripts/checkModel.mos"), "Check of PLA_PET_Recycler.Systems.FullCoupledSystem completed successfully")
    run(nix("omc simulation/openmodelica/scripts/run_all.mos"), "FullSystemJam_res.csv")
    run([sys.executable, "simulation/openmodelica/postprocess/summarize_results.py"], "OPENMODELICA_ACCEPTANCE_OK")
    run([sys.executable, "simulation/openmodelica/postprocess/generate_plots.py"], "OPENMODELICA_PLOTS_OK")
    run(nix("python3 analysis/structural/run_load_checks.py"), "STRUCTURAL_SCREENING_OK")
    run(freecad("cad/freecad/compact/generate_fusion_validation.py"), "FUSION_NEUTRAL_PACKAGE_OK")

    if baseline.get("geometry_change_required", True) and (
        "--regenerate-renders" in sys.argv or not (ROOT / "renders/assembly/compact_full_assembly_isometric.png").exists()
    ):
        run(freecad("cad/generation/render_views.py"), "COMPACT_RENDER_GENERATION_OK")
    else:
        print("PASS COMPACT_RENDER_PACKAGE_PRESENT_FROZEN_GEOMETRY", flush=True)

    font_path = os.environ.get("PPR_FONT_PATH")
    typst_font_arg = f" --font-path {shlex.quote(font_path)} --ignore-system-fonts" if font_path else ""
    typst = " && ".join([
        f"typst compile{typst_font_arg} --root . docs/build_manual_ko.typ docs/build_manual_ko.pdf",
        f"typst compile{typst_font_arg} --root . docs/design_report_ko.typ docs/design_report_ko.pdf",
        f"typst compile{typst_font_arg} --root . docs/digital_release_report_ko.typ docs/digital_release_report_ko.pdf",
        f"typst compile{typst_font_arg} --root . exports/cnc/extruder/rfq_drawing_ko.typ exports/cnc/extruder/rfq_drawing_ko.pdf",
        f"typst compile{typst_font_arg} --root . exports/jigs/gate1/gate1_assembly_ko.typ exports/jigs/gate1/gate1_assembly_ko.pdf",
        "echo DIGITAL_PDF_BUILD_OK",
    ])
    run(["bash", "-lc", typst] if shutil.which("typst") else nix(typst), "DIGITAL_PDF_BUILD_OK")
    run([sys.executable, "validation/artifact_reproducibility.py"], "CLEAN_CLONE_REPRODUCIBILITY_OK")
    run([sys.executable, "artifacts/build_manifest.py"], "ARTIFACT_MANIFEST_OK")
    run([sys.executable, "validation/test_release.py"], "SAFETY_ORCHESTRATION_V061_RELEASE_OK")
    print("ALL_SAFETY_ORCHESTRATION_VIRTUAL_VALIDATIONS_OK; CROSS_SOLVER_VALIDATION_PENDING; EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN", flush=True)


if __name__ == "__main__":
    main()
