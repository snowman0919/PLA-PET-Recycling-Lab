#!/usr/bin/env python3
"""필수 safety-orchestration false-PASS 10종 mutation regression."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from runtime_trace_rules import validate_fusion_binding, validate_purge_contract, validate_rows

ROOT = Path(__file__).resolve().parents[1]
REVISION = "safety-orchestration-closure-v0.6.1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_row() -> dict:
    return {
        "timestamp_ms": 1000,
        "scenario": "red_team_baseline",
        "ui_state": "RUNNING",
        "process_phase": "EXTRUSION",
        "material_session": "PLA_ACTIVE",
        "forming_chain_state": "NORMAL",
        "fault_reason": "NONE",
        "drive_calibration_valid": True,
        "gauge_calibration_valid": True,
        "current_sensor_calibration_valid": True,
        "cooling_feedback_calibration_valid": True,
        "temperature_channels_valid": True,
        "driver_fault_free": True,
        "purge_feed_approved": False,
        "purge_waste_path_confirmed": False,
        "spool_eligible": True,
        "waste_mode": False,
        "heater_fault_latched": False,
        "shredder_fault_latched": False,
        "forming_fault_latched": False,
        "shredder_start_succeeded": False,
        "pending_material": "NONE",
        "purge_run_completed": True,
        "cooling_command_pct": 100.0,
        "cooling_feedback_valid": True,
        "cooling_failure_dwell_elapsed": False,
        "cooling_startup_request": "NONE",
        "cooling_startup_probe_elapsed_ms": 0,
        "cooling_startup_healthy_dwell_ms": 0,
        "dancer_angle_rad": 0.10,
        "dancer_hard_stop_rad": 0.4363,
        "nominal_spool_jam": False,
        "gauge_consecutive_valid_samples": 20,
        "gauge_u95_mm": 0.03,
        "diameter_error_mm": 0.0,
        "ovality_mm": 0.0,
        "stable_duration_ms": 10000,
        "transport_delay_elapsed": True,
        "puller_saturated": False,
        "estop_active": False,
        "explicit_restart_issued": True,
        "purge_screw_revolutions": 0.0,
        "purge_revolutions_measured": False,
        "commanded_heater_power_w": 300.0,
        "phase_peak_envelope_w": 454.0,
        "cmd_shredder": False,
        "cmd_screw": True,
        "cmd_process_heaters": True,
        "cmd_feeder": True,
        "cmd_puller": True,
        "cmd_spooler": True,
        "cmd_traverse": True,
        "cmd_cooling": True,
        "invariant_status": True,
    }


def main() -> None:
    contract = json.loads((ROOT / "control/process_contract.json").read_text())
    baseline = safe_row()
    if validate_rows([baseline], contract):
        raise AssertionError("red-team baseline 자체가 유효하지 않음")
    if validate_purge_contract(contract):
        raise AssertionError("purge contract baseline 자체가 유효하지 않음")

    mutations: dict[str, tuple[list[dict], str]] = {}
    row = copy.deepcopy(baseline)
    row.update(process_phase="IDLE", cmd_screw=False, cmd_process_heaters=False, cmd_feeder=False, cmd_puller=False, cmd_spooler=False, cmd_traverse=False, heater_fault_latched=True)
    mutations["residual_subsystem_latch"] = ([row], "IDLE_WITH_SUBSYSTEM_LATCH")

    row = copy.deepcopy(baseline)
    row.update(process_phase="SHREDDING", cmd_screw=False, cmd_process_heaters=False, cmd_feeder=False, cmd_puller=False, cmd_spooler=False, cmd_traverse=False, cmd_shredder=False, shredder_start_succeeded=False)
    mutations["failed_start_in_shredding"] = ([row], "SHREDDING_WITH_FAILED_START")

    row = copy.deepcopy(baseline)
    row.update(material_session="PET_ACTIVE", pending_material="PET", purge_run_completed=False)
    mutations["pet_active_without_purge"] = ([row], "PENDING_MATERIAL_ACTIVE_WITHOUT_PURGE")

    row = copy.deepcopy(baseline)
    row.update(cooling_feedback_valid=False, cooling_failure_dwell_elapsed=True)
    mutations["cooling_feedback_absent"] = ([row], "COOLING_FEEDBACK_LOSS_NOT_CONTAINED")

    row = copy.deepcopy(baseline)
    row.update(nominal_spool_jam=True, dancer_angle_rad=0.44)
    mutations["dancer_hard_limit_crossing"] = ([row], "NOMINAL_JAM_CROSSED_HARD_STOP")

    row = copy.deepcopy(baseline)
    row.update(spool_eligible=False)
    mutations["invalid_strand_spool"] = ([row], "INELIGIBLE_STRAND_TO_PRODUCTION_SPOOL")

    row = copy.deepcopy(baseline)
    row.update(gauge_consecutive_valid_samples=1)
    mutations["one_sample_recovery"] = ([row], "SPOOL_ELIGIBILITY_WITHOUT_REQUALIFICATION")

    row = copy.deepcopy(baseline)
    row.update(process_phase="MAINTENANCE_PURGE", material_session="PURGE_RUNNING", spool_eligible=False, waste_mode=True, cmd_spooler=False, cmd_traverse=False, phase_peak_envelope_w=501.0)
    mutations["purge_over_500w"] = ([row], "PURGE_POWER_ENVELOPE_EXCEEDED")

    estop = copy.deepcopy(baseline)
    estop.update(timestamp_ms=1000, process_phase="ESTOP", estop_active=True, explicit_restart_issued=False, cmd_screw=False, cmd_process_heaters=False, cmd_feeder=False, cmd_puller=False, cmd_spooler=False, cmd_traverse=False, cmd_cooling=False)
    restart = copy.deepcopy(baseline)
    restart.update(timestamp_ms=1001, explicit_restart_issued=False)
    mutations["estop_clear_implicit_restart"] = ([estop, restart], "ESTOP_CLEAR_IMPLICIT_RESTART")

    row = copy.deepcopy(baseline)
    row.update(
        process_phase="IDLE", ui_state="COOLING_STARTUP_PROBE",
        cooling_startup_request="PREHEAT", cooling_feedback_valid=False,
        cmd_shredder=False, cmd_cooling=True,
    )
    mutations["startup_probe_heater_before_feedback_proof"] = (
        [row], "COOLING_STARTUP_HAZARDOUS_OUTPUT_BEFORE_PROOF",
    )

    row = copy.deepcopy(baseline)
    row.update(
        process_phase="MAINTENANCE_PURGE", ui_state="MAINTENANCE_PURGE",
        material_session="PURGE_READY_CONFIRM_REQUIRED", purge_feed_approved=True,
        purge_waste_path_confirmed=False, spool_eligible=False, waste_mode=True,
        cmd_shredder=False, cmd_process_heaters=True, cmd_feeder=False,
        cmd_spooler=False, cmd_traverse=False,
    )
    mutations["purge_motion_before_waste_confirmation"] = (
        [row], "PURGE_MOTION_BEFORE_WASTE_CONFIRMATION",
    )

    row = copy.deepcopy(baseline)
    row.update(invariant_status=False)
    mutations["production_invariant_false"] = ([row], "PRODUCTION_INVARIANT_FALSE")

    results: dict[str, str] = {}
    detected = {}
    for name, (rows, expected_error) in mutations.items():
        errors = validate_rows(rows, contract)
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"mutation false PASS/wrong reason: {name}: {errors}")
        results[name] = "FAIL_DETECTED"
        detected[name] = errors

    stale_binding = {
        "engineering_source_sha": "0" * 40,
        "fusion_result_state": "PENDING_EXTERNAL_EXECUTION",
    }
    if not validate_fusion_binding(stale_binding, "1" * 40):
        raise AssertionError("mutation false PASS: stale_fusion_binding")
    results["stale_fusion_binding"] = "FAIL_DETECTED"

    stale_purge_contract = copy.deepcopy(contract)
    stale_purge_contract["purge"]["feed_approval_single_use"] = False
    stale_purge_errors = validate_purge_contract(stale_purge_contract)
    if "STALE_PURGE_FEED_APPROVAL_REUSE_ALLOWED" not in stale_purge_errors:
        raise AssertionError("mutation false PASS: stale_purge_feed_approval")
    results["stale_purge_feed_approval"] = "FAIL_DETECTED"

    output = {
        "revision": REVISION,
        "status": "PASS",
        "method": "deterministic trace mutation/fault injection",
        "mutation_count": len(results),
        "mutations": results,
        "detected_errors": detected | {
            "stale_fusion_binding": ["STALE_FUSION_BINDING_ACCEPTED"],
            "stale_purge_feed_approval": stale_purge_errors,
        },
        "source_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (
                Path(__file__).resolve(),
                ROOT / "validation/runtime_trace_rules.py",
                ROOT / "control/process_contract.json",
            )
        },
    }
    path = ROOT / "validation/results/red_team_orchestration.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"SAFETY_ORCHESTRATION_RED_TEAM_OK mutations={len(results)}")


if __name__ == "__main__":
    main()
