#!/usr/bin/env python3
"""검증된 gate 결과에서 결정론적 v0.6.2.1 release metadata를 생성한다."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/results/release_metadata_v0.6.2.1.json"
REVISION = "technical-blocker-closure-v0.6.2.1"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = load("validation/fusion_policy_v0.6.2.1.json")
    gate = load("validation/results/fusion_release_gate_v0.6.2.1.json")
    binding = load("exports/fusion_validation_v0621/run_binding.json")
    with (ROOT / "validation/blocker_closure_matrix.csv").open(newline="") as handle:
        blockers = {row["blocker_id"]: row for row in csv.DictReader(handle)}
    require(policy.get("fusion_gate_policy") == "DEFERRED", "release policy must be DEFERRED")
    require(gate.get("status") == "FUSION_GATE_DEFERRED", "deferred gate evidence missing")
    require(gate.get("gate_outcome") == "DEFERRED", "deferred gate outcome mismatch")
    require(gate.get("deferred_is_solver_pass") is False, "deferred cannot be solver pass")
    require(gate.get("package_integrity", {}).get("status") == "PASS", "Fusion package integrity")
    require(all(blockers[f"P0-{letter}"]["status"].startswith("PASS") for letter in "ABCDEFGHIJK"),
            "P0-A~K non-Fusion blocker open")
    require(blockers["P0-L"]["status"] == "DEFERRED_USER_DECISION", "P0-L deferred status")
    payload = {
        "schema_version": "1.0",
        "revision": REVISION,
        "release_state": "TECHNICAL_CLOSURE_BASELINE",
        "implementation_state": "IMPLEMENTATION_BASELINE",
        "hardware_adapter_state": "HARDWARE_ADAPTER_VALIDATED",
        "actuation_state": "CLOSED_LOOP_ACTUATION_VALIDATED",
        "process_feed_state": "PROCESS_FEED_VIRTUAL_VALIDATED",
        "virtual_physics_state": "VIRTUAL_PHYSICS_VALIDATED",
        "cross_solver_state": "CROSS_SOLVER_VALIDATION_DEFERRED",
        "fusion_state": "DEFERRED_TO_POST_V0.6.2.1_MACBOOK_STAGE",
        "fusion_gate_policy": "DEFERRED",
        "fusion_gate_outcome": "DEFERRED",
        "fusion_solver_pass": False,
        "fusion_package_integrity": "PASS",
        "fusion_result_presence": gate.get("present_results", {}).get("presence"),
        "fusion_engineering_source_sha": binding.get("engineering_source_sha"),
        "price_state": "INFORMATIONAL_NON_BLOCKING",
        "empirical_state": "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN",
        "procurement_gate": "USER_APPROVAL_REQUIRED",
        "commissioning_gate": "USER_APPROVAL_REQUIRED",
        "physical_test_performed": False,
        "forbidden_claims": ["CROSS_SOLVER_VALIDATED", "FUSION_VALIDATED"],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print("V0621_RELEASE_METADATA_OK fusion=DEFERRED solver_pass=false")


if __name__ == "__main__":
    main()
