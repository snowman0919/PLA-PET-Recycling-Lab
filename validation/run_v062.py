#!/usr/bin/env python3
"""Fusion frozen package를 재생성하지 않는 v0.6.2 exact-worktree gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_PATHS = (
    "cad/freecad/compact/geometry.py",
    "cad/freecad/compact/manufacturing.py",
    "cad/parameters/baseline.json",
    "exports/fusion_validation/geometry",
    "exports/fusion_validation/loads",
    "exports/fusion_validation/load_case_manifest.csv",
    "exports/fusion_validation/model_manifest.csv",
    "exports/fusion_validation/materials.csv",
    "exports/fusion_validation/contact_pairs.csv",
    "exports/fusion_validation/constraints.csv",
    "exports/fusion_validation/run_binding.json",
    "analysis/load_cases/openmodelica_dynamic_envelope.json",
    "analysis/structural/generated",
)


def run(command: list[str], marker: str) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or marker not in output:
        raise SystemExit(f"FAIL {marker}\n{output}")
    print(f"PASS {marker}")
    return output


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_hashes(paths: tuple[str, ...] | list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in paths:
        path = ROOT / relative
        members = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
        for member in members:
            hashes[str(member.relative_to(ROOT))] = file_hash(member)
    return hashes


def run_generated_drift_check(command: list[str], marker: str, outputs: list[str]) -> None:
    before = path_hashes(outputs)
    run(command, marker)
    after = path_hashes(outputs)
    if before != after:
        changed = sorted(set(before) | set(after))
        raise SystemExit("FAIL GENERATED_CONTRACT_DRIFT\n" + "\n".join(changed))
    print(f"PASS GENERATED_CONTRACT_DRIFT {','.join(outputs)}")


def freecad(script: str) -> list[str]:
    code = (
        "import runpy,sys,os; "
        f'_result=runpy.run_path("{script}", run_name="__main__"); '
        "sys.stdout.flush(); os._exit(0)"
    )
    command = f"printf '%s\\n' {shlex.quote(code)} | FreeCADCmd -c"
    return ["nix", "develop", "-c", "bash", "-lc", command]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    frozen_before = path_hashes(list(FROZEN_PATHS))
    run([sys.executable, "validation/configuration_control.py"], "CONFIGURATION_CONTROL_OK")
    run_generated_drift_check(
        [sys.executable, "firmware/arduino_mega/generate_config.py"],
        "FIRMWARE_CONFIG_SYNC_OK", ["firmware/arduino_mega/src/generated_profiles.h"],
    )
    run_generated_drift_check(
        [sys.executable, "control/generate_contract_artifacts.py"],
        "CONTRACT_ARTIFACTS_OK", ["simulation/openmodelica/PLA_PET_Recycler/GeneratedControl.mo"],
    )
    commands = [
        ([sys.executable, "validation/fusion_delta_classification.py"], "FUSION_DELTA_CLASSIFICATION_OK"),
        ([sys.executable, "validation/orchestration_contract.py"], "ORCHESTRATION_CONTRACT_EQUIVALENCE_OK"),
        ([sys.executable, "validation/controller_contract.py"], "CONTROLLER_CONTRACT_POWER_INVARIANTS_OK"),
        (["make", "-C", "firmware/arduino_mega", "test"], "MACHINE_SUPERVISOR_TRANSACTIONS_PURGE_RUNDOWN_REQUALIFICATION_OK"),
        ([sys.executable, "validation/runtime_supervisor.py"], "RUNTIME_SUPERVISOR_E2E_OK"),
        ([sys.executable, "validation/arduino_compile.py"], "ARDUINO_MEGA_2560_COMPILE_OK"),
        ([sys.executable, "validation/v062_runtime_audit.py"], "V062_RUNTIME_SCHEDULER_PIN_TIMER_AUDIT_OK"),
        ([sys.executable, "validation/v062_mutation_tests.py"], "V062_MUTATION_TESTS_PASS"),
        ([sys.executable, "-m", "unittest", "analysis/cross_solver/test_import_fusion_results.py"], "OK"),
        ([sys.executable, "analysis/cross_solver/import_fusion_results.py",
          "exports/fusion_validation/results/fusion_result_template.csv",
          "--output", "analysis/cross_solver/fusion_import_review.json"], "PENDING_EXTERNAL_EXECUTION"),
        ([sys.executable, "analysis/process_risk/run_screening.py"], "PROCESS_RISK_SCREENING_OK"),
        ([sys.executable, "simulation/openmodelica/postprocess/validate_v062_shadow.py", "--summary-only"], "V062_SHADOW_PASS"),
        ([sys.executable, "validation/v062_actuation_contract.py"], "V062_ACTUATION_CONTRACT_HIGH_SIGNAL_OK"),
        ([sys.executable, "bom/build_budget_views.py"], "CONDITIONAL_AND_VERIFIED_BUDGET_OK"),
    ]
    for command, marker in commands:
        run(command, marker)
    if args.full:
        run([sys.executable, "cad/generation/refresh_revision_metadata.py"],
            "FROZEN_GEOMETRY_METADATA_REFRESH_OK")
        run(freecad("cad/generation/export_modelica_properties.py"),
            "CAD_TO_MODELICA_PARAMETER_SYNC_OK")
        run(["nix", "develop", "-c", "omc", "simulation/openmodelica/scripts/checkModel.mos"],
            "Check of PLA_PET_Recycler.Systems.FullCoupledSystem completed successfully")
        run(["nix", "develop", "-c", "omc", "simulation/openmodelica/scripts/run_v062_shadow.mos"],
            "ManualRethreadToProduction_res.csv")
        run([sys.executable, "simulation/openmodelica/postprocess/validate_v062_shadow.py"], "V062_SHADOW_PASS")
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
        run([sys.executable, "validation/interface_catalog_checks.py"], "FABRICATION_INTERFACE_CATALOG_VALIDATED_OK")
        run([sys.executable, "validation/mesh_checks.py"], "MESH_WATERTIGHT_MANIFOLD_OK")
        slicer = [sys.executable, "validation/slice_prints.py"] if shutil.which("prusa-slicer") else [
            "nix", "develop", "-c", "python3", "validation/slice_prints.py"
        ]
        run(slicer, "SLICER_SUCCESS_OK")
        run([sys.executable, "validation/modelica_library_check.py"], "MODELICA_MSL_CAD_BRIDGE_OK")
        run_generated_drift_check(
            [sys.executable, "simulation/openmodelica/scripts/generate_runner.py"],
            "MODELICA_RUNNER_SYNC_OK", ["simulation/openmodelica/scripts/run_all.mos"],
        )
        run(["nix", "develop", "-c", "omc", "simulation/openmodelica/scripts/run_all.mos"], "FullSystemJam_res.csv")
        run([sys.executable, "simulation/openmodelica/postprocess/summarize_results.py"], "OPENMODELICA_ACCEPTANCE_OK")
        with tempfile.TemporaryDirectory(prefix="ppr-v062-calculix-") as calculix_scratch:
            run(["nix", "develop", "-c", "python3", "analysis/structural/run_load_checks.py",
                 "--generated-dir", calculix_scratch], "STRUCTURAL_SCREENING_OK")
        pdf_command = " && ".join([
            "typst compile --root . docs/build_manual_ko.typ docs/build_manual_ko.pdf",
            "typst compile --root . docs/design_report_ko.typ docs/design_report_ko.pdf",
            "typst compile --root . docs/digital_release_report_ko.typ docs/digital_release_report_ko.pdf",
            "echo V062_PDF_BUILD_OK",
        ])
        run(["nix", "develop", "-c", "bash", "-lc", pdf_command], "V062_PDF_BUILD_OK")
        run([sys.executable, "artifacts/build_manifest.py"], "ARTIFACT_MANIFEST_OK")
        run([sys.executable, "validation/artifact_reproducibility.py"], "CLEAN_CLONE_REPRODUCIBILITY_OK")
    frozen_after = path_hashes(list(FROZEN_PATHS))
    if frozen_before != frozen_after:
        changed = sorted(path for path in set(frozen_before) | set(frozen_after)
                         if frozen_before.get(path) != frozen_after.get(path))
        raise SystemExit("FAIL FROZEN_FUSION_INPUT_CHANGED\n" + "\n".join(changed))
    print("PASS FROZEN_FUSION_INPUT_UNCHANGED")
    result_paths = [
        ROOT / "validation/results/arduino_mega_compile.json",
        ROOT / "validation/results/runtime_supervisor.json",
        ROOT / "validation/results/v062_runtime_audit.json",
        ROOT / "validation/results/v062_mutation_tests.json",
        ROOT / "validation/results/v062_actuation_contract.json",
        ROOT / "validation/results/fusion_delta_classification.json",
        ROOT / "simulation/openmodelica/results_v0.6.2/summary.json",
        ROOT / "analysis/process_risk/process_risk_summary.json",
        ROOT / "analysis/fusion_delta_queue/shadow_envelope_comparison.json",
        ROOT / "analysis/cross_solver/fusion_import_review.json",
    ]
    payload = {
        "revision": "parallel-actuation-hardening-v0.6.2",
        "gate": "CI-FULL" if args.full else "CI-LIGHT",
        "status": "PASS", "fusion_solve_claimed": False,
        "fusion_input_delta": "NONE",
        "evidence_hashes": {str(path.relative_to(ROOT)): file_hash(path) for path in result_paths},
    }
    out = ROOT / ("validation/results/ci_full_v062.json" if args.full else "validation/results/ci_light_v062.json")
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"V062_{payload['gate'].replace('-', '_')}_OK")


if __name__ == "__main__":
    main()
