#!/usr/bin/env python3
"""v0.6.2 actuation extension과 production code/evidence의 semantic binding 검사."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "parallel-actuation-hardening-v0.6.2"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source(relative: str) -> str:
    return (ROOT / relative).read_text()


def require_tokens(relative: str, tokens: tuple[str, ...]) -> None:
    text = source(relative)
    missing = [token for token in tokens if token not in text]
    require(not missing, f"{relative} semantic token missing: {missing}")


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def main() -> None:
    contract = json.loads(source("control/actuation_contract_v0.6.2.json"))
    require(contract["revision"] == REVISION, "actuation revision mismatch")
    require(contract["extends_frozen_process_contract"] == "safety-orchestration-closure-v0.6.1",
            "frozen process contract binding mismatch")
    require(contract["screw_motion"]["purge_evidence"] == "ACTUAL_MEASURED_REVOLUTIONS",
            "purge evidence is not measured")
    require(contract["cooling"]["tach_proves_airflow"] is False,
            "fan tach incorrectly claims measured airflow")
    require(contract["traverse"]["wall_clock_reversal_forbidden"] is True,
            "time-based traverse reversal allowed")

    require_tokens("firmware/arduino_mega/src/machine_supervisor.cpp", (
        "diameter_integral_allowed", "puller_output_.tach_valid", "!puller_output_.saturated",
        "purge_screw_revolutions_measured_", "FORMING_SCREW_MOTION_MISMATCH",
        "FORMING_PULLER_SATURATION", "FORMING_SPOOL_JAM", "heater_allocator_.allocate",
        "heaters_.applyAllocation", "waste_path_active",
    ))
    require_tokens("firmware/arduino_mega/src/puller_speed_control.cpp", (
        "target_rpm", "measured_mm_s", "pwm_limited", "saturation_duration_ms",
        "tach_loss_timeout_ms", "candidate_integral",
    ))
    require_tokens("firmware/arduino_mega/src/screw_motion_monitor.cpp", (
        "cumulative_revolutions_", "last_valid_tach_ms_", "MOTION_MISMATCH_DWELL_MS",
    ))
    require_tokens("firmware/arduino_mega/src/cooling_monitor.cpp", (
        "COOLING_FAN1_STOPPED", "COOLING_FAN2_STOPPED", "COOLING_IMPLAUSIBLE_WHILE_OFF",
    ))
    require_tokens("firmware/arduino_mega/src/heater_control.cpp", (
        "z.applied_duty - z.requested_duty", "applyAllocation", "HEATER_UNEXPECTED_RISE",
    ))
    require_tokens("firmware/arduino_mega/src/spooler_control.cpp", (
        "dancer - config_.dancer_target_rad", "estimated_radius_mm", "jam_since_ms_",
    ))
    require_tokens("firmware/arduino_mega/src/traverse_control.cpp", (
        "spool_turns * config_.winding_pitch_mm", "left_limit", "right_limit",
        "missed_limit_timeout_ms",
    ))
    require_tokens("firmware/arduino_mega/arduino_mega.ino", (
        "input.puller_saturated = supervisor.lastPullerSaturated()",
        "forming_fault_detected_ms", "forming_state_changed_ms", "Serial.write(",
    ))

    runtime = json.loads(source("validation/results/runtime_supervisor.json"))
    require(runtime["status"] == "PASS" and runtime["scenario_count"] >= 43,
            "production runtime harness evidence missing")
    runtime_names = {row["name"] for row in runtime["scenarios"]}
    require({
        "cold_boot_no_calibration", "separate_calibration_loading",
        "puller_tach_startup_grace_and_loss", "gauge_loss_controlled_rundown",
        "spool_jam_before_hard_stop", "gauge_requalification_manual_rethread",
        "estop_during_purge", "estop_during_extrusion",
    } <= runtime_names, "mandatory production runtime scenario missing")

    with (ROOT / "validation/v062_high_signal_test_matrix.csv").open(newline="") as handle:
        matrix = list(csv.DictReader(handle))
    require(len(matrix) == 22, "high-signal scenario count drift")
    require(len({row["scenario_id"] for row in matrix}) == len(matrix), "duplicate high-signal scenario")
    required_fields = {
        "protected_requirement", "input", "method", "expected_evidence",
        "pass_fail_threshold", "result", "evidence_path",
    }
    for row in matrix:
        require(all(row[field] for field in required_fields), f"test documentation incomplete: {row['scenario_id']}")
        require(row["result"] == "PASS", f"high-signal scenario failed: {row['scenario_id']}")
        require((ROOT / row["evidence_path"]).exists(), f"test evidence missing: {row['evidence_path']}")

    mutation = json.loads(source("validation/results/v062_mutation_tests.json"))
    shadow = json.loads(source("simulation/openmodelica/results_v0.6.2/summary.json"))
    require(mutation["status"] == "PASS" and mutation["mutation_count"] == 7,
            "mutation evidence incomplete")
    require(shadow["status"] == "PASS" and shadow["scenario_count"] == 24,
            "OpenModelica shadow evidence incomplete")

    result = {
        "revision": REVISION,
        "status": "PASS",
        "contract_sha256": sha256("control/actuation_contract_v0.6.2.json"),
        "production_runtime_scenarios": runtime["scenario_count"],
        "documented_high_signal_scenarios": len(matrix),
        "mutation_count": mutation["mutation_count"],
        "shadow_scenario_count": shadow["scenario_count"],
        "fusion_solve_claimed": False,
    }
    path = ROOT / "validation/results/v062_actuation_contract.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("V062_ACTUATION_CONTRACT_HIGH_SIGNAL_OK")


if __name__ == "__main__":
    main()
