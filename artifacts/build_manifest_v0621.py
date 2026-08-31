#!/usr/bin/env python3
"""v0.6.2.1 blocker-closure source와 경량 증거의 결정적 manifest를 만든다."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/manifest_v0.6.2.1.json"

EXPLICIT_FILES = [
    "control/tach_contract.json",
    "control/drive_actuation_contract_v0.6.2.1.json",
    "cad/parameters/process_v0621.json",
    "cad/freecad/compact/process_v0621.py",
    "bom/bom.csv",
    "bom/budget_policy.json",
    "electronics/io_schedule.csv",
    "exports/fabrication/interface_catalog.csv",
    "firmware/arduino_mega/README.md",
    "firmware/arduino_mega/timer_pin_budget.csv",
    "docs/hardware_adapter_validation_ko.md",
    "docs/process_feed_validation_ko.md",
    "docs/cross_solver_release_report_ko.md",
    "docs/build_manual_ko.pdf",
    "docs/design_report_ko.pdf",
    "docs/digital_release_report_ko.pdf",
    "validation/source_lock_v0.6.2.1.json",
    "validation/blocker_closure_matrix.csv",
    "validation/blocker_closure_report_ko.md",
    "validation/run_v0621.py",
    "validation/fusion_release_gate_v0621.py",
    "validation/fusion_external_blocker_v0.6.2.1.json",
    "validation/exact_head_evidence_v0621.py",
    ".github/workflows/ci-light.yml",
    ".github/workflows/ci-full.yml",
    "analysis/fusion_delta_queue/v0.6.2.1_delta_report.json",
    "analysis/cross_solver/correlation_matrix.csv",
    "analysis/cross_solver/correlation_report_ko.md",
    "simulation/openmodelica/results_v0.6.2.1/scenario_manifest.json",
    "simulation/openmodelica/results_v0.6.2.1/solver_execution.json",
    "simulation/openmodelica/results_v0.6.2.1/summary.json",
    "analysis/process_feed/feed_validation.json",
    "analysis/shredder_recirculation/recirculation_validation.json",
    "exports/process_v0621/manifest.json",
    "exports/process_v0621/collision_and_clearance.json",
    "exports/process_v0621/fusion_change_classification.json",
    "exports/fusion_validation_v0621/package_state.json",
    "exports/fusion_validation_v0621/engineering_source_lock.json",
    "exports/fusion_validation_v0621/run_binding.json",
    "exports/fusion_validation_v0621/model_manifest.csv",
    "exports/fusion_validation_v0621/load_case_manifest.csv",
    "fusion_worker/result_validation/validate_fusion_v0621_package.py",
    "validation/results/hardware_adapter_tach/summary.json",
    "validation/results/hardware_adapter_e2e/summary.json",
    "validation/results/hardware_adapter_e2e/scenario_trace.csv",
    "validation/results/v0621_mutation_tests.json",
    "validation/results/budget_policy_v0.6.2.1.json",
]

TREE_PATTERNS = [
    "firmware/arduino_mega/src/*.h",
    "firmware/arduino_mega/src/*.cpp",
    "firmware/arduino_mega/tests/test_*.*",
    "exports/process_v0621/parts/*/*.step",
    "exports/process_v0621/parts/*/*.stl",
    "exports/fusion_validation_v0621/geometry/*.step",
]

GENERATION_COMMANDS = [
    "python3 control/generate_tach_contract.py",
    "nix develop --command FreeCADCmd cad/freecad/compact/process_v0621.py",
    "python3 analysis/process_feed/verify_process_lane.py",
    "python3 simulation/openmodelica/scripts/generate_v0621_shadow.py",
    "omc simulation/openmodelica/scripts/run_v0621_shadow.mos",
    "python3 simulation/openmodelica/postprocess/validate_v0621_shadow.py",
    "python3 validation/run_v0621.py --allow-fusion-pending",
    "python3 artifacts/build_manifest_v0621.py",
    "graphify --update",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    paths = {ROOT / relative for relative in EXPLICIT_FILES}
    for pattern in TREE_PATTERNS:
        paths.update(ROOT.glob(pattern))
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("V0621_MANIFEST_FAIL missing=" + ",".join(sorted(missing)))
    artifacts = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(paths)
    ]
    binding = json.loads((ROOT / "exports/fusion_validation_v0621/run_binding.json").read_text())
    payload = {
        "schema_version": 1,
        "revision": "technical-blocker-closure-v0.6.2.1",
        "classification": "DIGITAL_ENGINEERING_EVIDENCE_PHYSICAL_TEST_NOT_RUN",
        "engineering_source_sha": binding.get("engineering_source_sha"),
        "fusion_result_state": binding.get("fusion_result_state"),
        "artifact_count": len(artifacts),
        "generation_commands": GENERATION_COMMANDS,
        "artifacts": artifacts,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"V0621_ARTIFACT_MANIFEST_OK count={len(artifacts)}")


if __name__ == "__main__":
    main()
