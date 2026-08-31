#!/usr/bin/env python3
"""Fusion frozen package를 재생성하지 않는 v0.6.2 exact-worktree gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], marker: str) -> str:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or marker not in output:
        raise SystemExit(f"FAIL {marker}\n{output}")
    print(f"PASS {marker}")
    return output


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    commands = [
        ([sys.executable, "validation/fusion_delta_classification.py"], "FUSION_DELTA_CLASSIFICATION_OK"),
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
        ([sys.executable, "simulation/openmodelica/postprocess/validate_v062_shadow.py"], "V062_SHADOW_PASS"),
        ([sys.executable, "bom/build_budget_views.py"], "CONDITIONAL_AND_VERIFIED_BUDGET_OK"),
    ]
    for command, marker in commands:
        run(command, marker)
    if args.full:
        run(["nix", "develop", "-c", "omc", "simulation/openmodelica/scripts/checkModel.mos"],
            "Check of PLA_PET_Recycler.Systems.FullCoupledSystem completed successfully")
        run(["nix", "develop", "-c", "omc", "simulation/openmodelica/scripts/run_v062_shadow.mos"],
            "ManualRethreadToProduction_res.csv")
        run([sys.executable, "simulation/openmodelica/postprocess/validate_v062_shadow.py"], "V062_SHADOW_PASS")
        for script, marker in (
            ("validation/freecad_checks.py", "FREECAD_COLLISION_LOAD_PATH_OK"),
            ("validation/manufacturing_checks.py", "MANUFACTURING_GEOMETRY_RFQ_OK"),
            ("validation/print_interface_checks.py", "MINIMUM_WALL_FASTENER_INSERT_OK"),
            ("validation/motion_checks.py", "FULL_MOTION_ENVELOPE_OK"),
        ):
            run(freecad(script), marker)
        run([sys.executable, "validation/interface_catalog_checks.py"], "FABRICATION_INTERFACE_CATALOG_VALIDATED_OK")
        run([sys.executable, "validation/controller_contract.py"], "CONTROLLER_CONTRACT_POWER_INVARIANTS_OK")
        run([sys.executable, "simulation/openmodelica/scripts/generate_runner.py"], "MODELICA_RUNNER_SYNC_OK")
        run(["nix", "develop", "-c", "omc", "simulation/openmodelica/scripts/run_all.mos"], "FullSystemJam_res.csv")
        run([sys.executable, "simulation/openmodelica/postprocess/summarize_results.py"], "OPENMODELICA_ACCEPTANCE_OK")
        run(["nix", "develop", "-c", "python3", "analysis/structural/run_load_checks.py"], "STRUCTURAL_SCREENING_OK")
        pdf_command = " && ".join([
            "typst compile --root . docs/build_manual_ko.typ docs/build_manual_ko.pdf",
            "typst compile --root . docs/design_report_ko.typ docs/design_report_ko.pdf",
            "typst compile --root . docs/digital_release_report_ko.typ docs/digital_release_report_ko.pdf",
            "echo V062_PDF_BUILD_OK",
        ])
        run(["nix", "develop", "-c", "bash", "-lc", pdf_command], "V062_PDF_BUILD_OK")
        run([sys.executable, "artifacts/build_manifest.py"], "ARTIFACT_MANIFEST_OK")
        run([sys.executable, "validation/artifact_reproducibility.py"], "CLEAN_CLONE_REPRODUCIBILITY_OK")
    result_paths = [
        ROOT / "validation/results/arduino_mega_compile.json",
        ROOT / "validation/results/runtime_supervisor.json",
        ROOT / "validation/results/v062_runtime_audit.json",
        ROOT / "validation/results/v062_mutation_tests.json",
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
