#!/usr/bin/env python3
"""실제 MachineSupervisor를 빌드·실행하고 결정적 trace를 검증한다."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from runtime_trace_rules import HAZARDOUS_COMMANDS, validate_rows

ROOT = Path(__file__).resolve().parents[1]
REVISION = "safety-orchestration-closure-v0.6.1"
FIRMWARE = ROOT / "firmware/arduino_mega"
RESULTS = ROOT / "validation/results"
TRACE_DIR = RESULTS / "runtime_traces"

FIELDS = (
    "scenario", "timestamp_ms", "ui_state", "process_phase", "material_session",
    "forming_chain_state", "fault_reason", "drive_calibration_valid",
    "gauge_calibration_valid", "current_sensor_calibration_valid",
    "cooling_feedback_calibration_valid", "temperature_channels_valid",
    "driver_fault_free", "purge_feed_approved", "purge_waste_path_confirmed",
    "spool_eligible", "waste_mode",
    "heater_fault_latched", "shredder_fault_latched", "forming_fault_latched",
    "shredder_start_succeeded", "pending_material", "purge_run_completed",
    "cooling_command_pct", "cooling_feedback_valid",
    "cooling_failure_dwell_elapsed", "cooling_startup_request",
    "cooling_startup_probe_elapsed_ms", "cooling_startup_healthy_dwell_ms",
    "dancer_angle_rad", "dancer_hard_stop_rad",
    "nominal_spool_jam", "gauge_consecutive_valid_samples", "gauge_u95_mm",
    "diameter_error_mm", "ovality_mm", "stable_duration_ms",
    "transport_delay_elapsed", "puller_saturated", "estop_active",
    "explicit_restart_issued", "purge_screw_revolutions",
    "purge_revolutions_measured", "commanded_heater_power_w",
    "phase_peak_envelope_w", "cmd_shredder", "cmd_screw",
    "cmd_process_heaters", "cmd_feeder", "cmd_puller", "cmd_spooler",
    "cmd_traverse", "cmd_cooling", "invariant_status",
)
BOOL_FIELDS = {
    "drive_calibration_valid", "gauge_calibration_valid",
    "current_sensor_calibration_valid", "cooling_feedback_calibration_valid",
    "temperature_channels_valid", "driver_fault_free", "purge_feed_approved",
    "purge_waste_path_confirmed", "purge_revolutions_measured",
    "spool_eligible", "waste_mode", "heater_fault_latched",
    "shredder_fault_latched", "forming_fault_latched",
    "shredder_start_succeeded", "purge_run_completed", "cooling_feedback_valid",
    "cooling_failure_dwell_elapsed", "nominal_spool_jam",
    "transport_delay_elapsed", "puller_saturated", "estop_active",
    "explicit_restart_issued", "cmd_shredder", "cmd_screw",
    "cmd_process_heaters", "cmd_feeder", "cmd_puller", "cmd_spooler",
    "cmd_traverse", "cmd_cooling", "invariant_status",
}
INT_FIELDS = {
    "timestamp_ms", "gauge_consecutive_valid_samples", "stable_duration_ms",
    "cooling_startup_probe_elapsed_ms", "cooling_startup_healthy_dwell_ms",
}
FLOAT_FIELDS = {
    "cooling_command_pct", "dancer_angle_rad", "dancer_hard_stop_rad",
    "gauge_u95_mm", "diameter_error_mm", "ovality_mm",
    "commanded_heater_power_w", "phase_peak_envelope_w",
    "purge_screw_revolutions",
}
REQUIRED_SCENARIOS = {
    "cold_boot_no_calibration", "separate_calibration_loading",
    "calibration_readiness_phase_gates",
    "explicit_material_selection", "successful_shredder_start",
    "rejected_shredder_start_rollback", "shredder_jam_three_retries_atomic_clear",
    "heater_sensor_fault_atomic_clear", "preheat_waits_explicit_arm",
    "normal_pla_extrusion", "pla_to_pet_maintenance_purge",
    "pet_to_pla_maintenance_purge",
    "stale_purge_feed_approval_rejected",
    "purge_screw_driver_fault_containment",
    "purge_cooling_loss_containment", "preheat_cooling_loss_containment",
    "cooldown_cooling_loss_containment", "cooldown_to_idle_completion",
    "general_fault_valid_cooling",
    "gauge_loss_controlled_rundown", "cooling_loss_controlled_rundown",
    "spool_jam_before_hard_stop", "gauge_requalification_manual_rethread",
    "estop_during_shredding", "estop_during_preheating", "estop_during_purge",
    "estop_during_extrusion", "estop_during_cooldown",
    "estop_clear_no_implicit_restart",
    "preheat_fan_first_startup_proof", "purge_fan_first_startup_proof",
    "startup_probe_feedback_absent_containment", "cooling_fault_clear_then_reprobe",
    "purge_cooling_fault_clear_then_reprobe", "cooldown_cooling_fault_clear_then_reprobe",
    "purge_ready_waits_ordered_confirmations",
    "phase_specific_readiness_ui",
    "purge_panel_abort_all_stages",
    "puller_tach_startup_grace_and_loss", "extrusion_quality_same_cycle_interlocks",
    "requalification_invalid_quality_resets_counter", "manual_rethread_fresh_invalid_rejected",
    "purge_completion_fresh_fault_preflight",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_row(line: str) -> dict:
    values = line.split("|")
    if len(values) != len(FIELDS):
        raise AssertionError(f"runtime trace 열 수 불일치: {len(values)} != {len(FIELDS)}")
    row: dict = dict(zip(FIELDS, values, strict=True))
    for field in BOOL_FIELDS:
        if row[field] not in ("0", "1"):
            raise AssertionError(f"bool trace 형식 오류 {field}={row[field]}")
        row[field] = row[field] == "1"
    for field in INT_FIELDS:
        row[field] = int(row[field])
    for field in FLOAT_FIELDS:
        row[field] = float(row[field])
    return row


def main() -> None:
    compile_sources = [
        FIRMWARE / "src/process_state.cpp", FIRMWARE / "src/shredder_control.cpp",
        FIRMWARE / "src/heater_control.cpp", FIRMWARE / "src/gauge_control.cpp",
        FIRMWARE / "src/machine_supervisor.cpp",
        ROOT / "validation/runtime_supervisor_harness.cpp",
    ]
    production_headers = [
        FIRMWARE / "src/process_state.h", FIRMWARE / "src/shredder_control.h",
        FIRMWARE / "src/heater_control.h", FIRMWARE / "src/gauge_control.h",
        FIRMWARE / "src/machine_supervisor.h", FIRMWARE / "src/generated_profiles.h",
    ]
    for source in [*compile_sources, *production_headers]:
        if not source.is_file():
            raise AssertionError(f"runtime production source 없음: {source.relative_to(ROOT)}")

    with tempfile.TemporaryDirectory(prefix="ppr-runtime-supervisor-") as temp:
        binary = Path(temp) / "runtime_supervisor"
        compile_result = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             f"-I{FIRMWARE / 'src'}", *(str(path) for path in compile_sources), "-o", str(binary)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if compile_result.returncode:
            raise AssertionError("MachineSupervisor host compile 실패:\n" + compile_result.stdout + compile_result.stderr)
        run_result = subprocess.run([str(binary)], cwd=ROOT, text=True, capture_output=True)
        if run_result.returncode:
            raise AssertionError("MachineSupervisor runtime harness 실패:\n" + run_result.stdout + run_result.stderr)

    rows: list[dict] = []
    bounded_marker = None
    for line in run_result.stdout.splitlines():
        if line.startswith("BOUNDED_SEQUENCE_OK|"):
            bounded_marker = line
        elif line.strip():
            rows.append(parse_row(line))
    if bounded_marker != "BOUNDED_SEQUENCE_OK|4|64":
        raise AssertionError("고정 seed bounded sequence 증거 누락")

    scenarios = {row["scenario"] for row in rows}
    missing = sorted(REQUIRED_SCENARIOS - scenarios)
    if missing:
        raise AssertionError("필수 runtime trace 누락: " + ", ".join(missing))

    contract = json.loads((ROOT / "control/process_contract.json").read_text())
    if contract.get("revision") != REVISION:
        raise AssertionError("runtime harness contract revision 불일치")
    # Harness는 command를 관측하고, 전력은 별도의 component-summed phase model로
    # 계산한다. production code가 같은 peak 상수를 expected로 되읽는 self-check가 아니다.
    for row in rows:
        phase_power = contract["power"]["phases"].get(row["process_phase"])
        row["phase_peak_envelope_w"] = sum(phase_power["components_peak_w"]) if phase_power else 0.0
    errors = validate_rows(rows, contract)
    if errors:
        raise AssertionError("runtime invariant 실패:\n" + "\n".join(errors[:30]))

    general_fault_rows = [row for row in rows if row["scenario"] == "general_fault_valid_cooling"]
    if len(general_fault_rows) != 1 or not general_fault_rows[0]["cmd_cooling"] or any(
        general_fault_rows[0][field] for field in (
            "cmd_shredder", "cmd_screw", "cmd_process_heaters", "cmd_feeder",
            "cmd_puller", "cmd_spooler", "cmd_traverse",
        )
    ):
        raise AssertionError("general FAULT valid cooling-only trace 불충분")
    cooling_fault_scenarios = {
        "preheat_cooling_loss_containment", "purge_cooling_loss_containment",
        "cooldown_cooling_loss_containment",
    }
    cooling_fault_rows = [
        row for row in rows
        if row["scenario"] in cooling_fault_scenarios and row["process_phase"] == "FAULT"
    ]
    if {row["scenario"] for row in cooling_fault_rows} != cooling_fault_scenarios or any(
        any(row[field] for field in (
            "cmd_shredder", "cmd_screw", "cmd_process_heaters", "cmd_feeder",
            "cmd_puller", "cmd_spooler", "cmd_traverse", "cmd_cooling",
        )) for row in cooling_fault_rows
    ):
        raise AssertionError("CoolingFailure same-cycle all-zero trace 불충분")
    purge_running_rows = [
        row for row in rows
        if row["scenario"] in {
            "pla_to_pet_maintenance_purge", "pet_to_pla_maintenance_purge"
        } and row["material_session"] == "PURGE_RUNNING"
    ]
    if len(purge_running_rows) != 2 or any(
        not row["purge_feed_approved"] or not row["purge_waste_path_confirmed"]
        for row in purge_running_rows
    ):
        raise AssertionError("purge internal feed approval/waste confirmation ordered trace 불충분")
    stale_approval_rows = [
        row for row in rows if row["scenario"] == "stale_purge_feed_approval_rejected"
    ]
    if len(stale_approval_rows) != 1 or (
        stale_approval_rows[0]["material_session"] != "PURGE_READY_CONFIRM_REQUIRED"
        or stale_approval_rows[0]["purge_feed_approved"]
        or stale_approval_rows[0]["purge_run_completed"]
    ):
        raise AssertionError("stale purge approval reuse rejection trace 불충분")
    startup = contract["cooling_feedback"]["startup_probe"]
    dwell_ms = int(startup["healthy_feedback_dwell_s"] * 1000)
    for scenario, request, committed_phase in (
        ("preheat_fan_first_startup_proof", "PREHEAT", "PREHEATING"),
        ("purge_fan_first_startup_proof", "PURGE_PREHEAT", "MAINTENANCE_PURGE"),
    ):
        proof_rows = sorted(
            (row for row in rows if row["scenario"] == scenario),
            key=lambda row: row["timestamp_ms"],
        )
        if (
            len(proof_rows) != 3
            or [row["process_phase"] for row in proof_rows] != ["IDLE", "IDLE", committed_phase]
            or [row["cooling_startup_request"] for row in proof_rows] != [request, request, "NONE"]
            or any(row[field] for row in proof_rows[:2] for field in (
                "cmd_shredder", "cmd_screw", "cmd_process_heaters", "cmd_feeder",
                "cmd_puller", "cmd_spooler", "cmd_traverse",
            ))
            or any(not row["cmd_cooling"] for row in proof_rows[:2])
            or proof_rows[0]["cooling_feedback_valid"]
            or not proof_rows[1]["cooling_feedback_valid"]
            or proof_rows[1]["cooling_startup_healthy_dwell_ms"] >= dwell_ms
        ):
            raise AssertionError(f"{scenario} fan-first bounded proof trace 불충분")
    absent = sorted(
        (row for row in rows if row["scenario"] == "startup_probe_feedback_absent_containment"),
        key=lambda row: row["timestamp_ms"],
    )
    if (
        len(absent) != 2 or absent[0]["process_phase"] != "IDLE"
        or not absent[0]["cmd_cooling"] or any(absent[0][field] for field in (
            "cmd_shredder", "cmd_screw", "cmd_process_heaters", "cmd_feeder",
            "cmd_puller", "cmd_spooler", "cmd_traverse",
        ))
        or absent[1]["process_phase"] != "FAULT"
        or any(absent[1][field] for field in HAZARDOUS_COMMANDS)
    ):
        raise AssertionError("startup probe absent-feedback fail-safe trace 불충분")
    ready_rows = sorted(
        (row for row in rows if row["scenario"] == "purge_ready_waits_ordered_confirmations"),
        key=lambda row: row["timestamp_ms"],
    )
    if len(ready_rows) != 3 or [row["purge_feed_approved"] for row in ready_rows] != [False, True, True] or any(
        row[field] for row in ready_rows for field in (
            "cmd_screw", "cmd_feeder", "cmd_puller", "cmd_spooler", "cmd_traverse",
        )
    ) or ready_rows[-1]["cooling_feedback_valid"]:
        raise AssertionError("purge ready/approval-before-waste motion inhibit trace 불충분")
    abort_rows = [row for row in rows if row["scenario"] == "purge_panel_abort_all_stages"]
    expected_abort = {
        "PROBE_ABORTED": "IDLE",
        "READY_ABORTED": "COOLDOWN",
        "READY_ABORT_COOLED_IDLE": "IDLE",
        "RUNNING_ABORTED": "COOLDOWN",
        "RUNNING_ABORT_COOLED_IDLE": "IDLE",
    }
    if {row["fault_reason"] for row in abort_rows} != set(expected_abort) or any(
        row["process_phase"] != expected_abort[row["fault_reason"]]
        or row["material_session"] != "PURGE_PREHEAT_REQUIRED"
        or row["purge_feed_approved"] or row["purge_run_completed"]
        or any(row[field] for field in (
            "cmd_shredder", "cmd_screw", "cmd_process_heaters", "cmd_feeder",
            "cmd_puller", "cmd_spooler", "cmd_traverse",
        ))
        or (row["process_phase"] == "COOLDOWN") != row["cmd_cooling"]
        for row in abort_rows
    ):
        raise AssertionError("purge probe/ready/running panel abort trace 불충분")
    ui_rows = sorted(
        (row for row in rows if row["scenario"] == "phase_specific_readiness_ui"),
        key=lambda row: row["timestamp_ms"],
    )
    if [row["ui_state"] for row in ui_rows] != ["COOLING_STARTUP_PROBE", "READY_TO_EXTRUDE"] or any(
        row["drive_calibration_valid"] or row["current_sensor_calibration_valid"] for row in ui_rows
    ):
        raise AssertionError("phase-specific calibration readiness UI trace 불충분")
    tach_rows = [row for row in rows if row["scenario"] == "puller_tach_startup_grace_and_loss"]
    if {row["fault_reason"] for row in tach_rows} != {
        "PRE_GRACE_ZERO_RPM_ACCEPTED", "PULLER_TACH_FAILURE_AFTER_GRACE",
        "NORMAL_PULSE_QUALIFIED", "PULLER_TACH_FAILURE_AFTER_QUALIFICATION",
    } or any(
        row["forming_chain_state"] != "RUNDOWN"
        for row in tach_rows
        if row["fault_reason"].startswith("PULLER_TACH_FAILURE")
    ):
        raise AssertionError("puller tach startup grace/qualified-loss trace 불충분")
    quality_rows = [row for row in rows if row["scenario"] == "extrusion_quality_same_cycle_interlocks"]
    expected_quality = {
        "DIAMETER_OUT_OF_TOLERANCE", "DIAMETER_ONE_SAMPLE_RECOVERY_BLOCKED",
        "OVALITY_OUT_OF_TOLERANCE", "OVALITY_ONE_SAMPLE_RECOVERY_BLOCKED",
        "PULLER_SATURATED", "PULLER_ONE_SAMPLE_RECOVERY_BLOCKED",
    }
    if {row["fault_reason"] for row in quality_rows} != expected_quality or any(
        row["spool_eligible"] or row["cmd_spooler"] or row["cmd_traverse"] or not row["waste_mode"]
        for row in quality_rows
    ):
        raise AssertionError("production diameter/ovality/puller saturation winding interlock trace 불충분")
    reset_rows = [row for row in rows if row["scenario"] == "requalification_invalid_quality_resets_counter"]
    if len(reset_rows) != 1 or reset_rows[0]["gauge_consecutive_valid_samples"] != 0 or not reset_rows[0]["waste_mode"]:
        raise AssertionError("requalification invalid-quality counter reset trace 불충분")
    rethread_rows = [row for row in rows if row["scenario"] == "manual_rethread_fresh_invalid_rejected"]
    if len(rethread_rows) != 1 or rethread_rows[0]["spool_eligible"] or rethread_rows[0]["cmd_spooler"] or rethread_rows[0]["cmd_traverse"]:
        raise AssertionError("manual rethread fresh-invalid rejection trace 불충분")
    completion_fault_rows = [row for row in rows if row["scenario"] == "purge_completion_fresh_fault_preflight"]
    if {row["fault_reason"] for row in completion_fault_rows} != {
        "FRESH_LID_OPEN_REJECTED", "FRESH_ESTOP_REJECTED",
        "FRESH_THERMAL_CHAIN_REJECTED", "FRESH_COOLING_INVALID_REJECTED",
    } or any(
        row["purge_run_completed"] or row["material_session"] == "PET_ACTIVE"
        or any(row[field] for field in (
            "cmd_screw", "cmd_process_heaters", "cmd_feeder", "cmd_puller",
            "cmd_spooler", "cmd_traverse",
        ))
        for row in completion_fault_rows
    ):
        raise AssertionError("purge completion fresh-input guard race trace 불충분")
    cooldown_rows = sorted(
        (row for row in rows if row["scenario"] == "cooldown_to_idle_completion"),
        key=lambda row: row["timestamp_ms"],
    )
    if (
        [row["process_phase"] for row in cooldown_rows] != ["COOLDOWN", "IDLE"]
        or not cooldown_rows[0]["cmd_cooling"]
        or any(cooldown_rows[1][field] for field in HAZARDOUS_COMMANDS)
    ):
        raise AssertionError("cooldown threshold automatic IDLE/no-restart trace 불충분")

    successful_purge_rows = [
        row for row in rows
        if row["scenario"] in {
            "pla_to_pet_maintenance_purge", "pet_to_pla_maintenance_purge"
        } and row["purge_run_completed"]
        and row["material_session"] == "SCREEN_CLEAN_REQUIRED"
        and row["process_phase"] == "COOLDOWN"
    ]
    minimum_revolutions = contract["purge"]["minimum_screw_revolutions"]
    if len(successful_purge_rows) != 2 or any(
        row["purge_screw_revolutions"] < minimum_revolutions
        or row["purge_revolutions_measured"]
        for row in successful_purge_rows
    ):
        raise AssertionError("purge 완료의 command-derived revolution 증거 불충분/측정값 오표기")
    if any(
        not row["cmd_cooling"] or any(row[field] for field in (
            "cmd_shredder", "cmd_screw", "cmd_process_heaters", "cmd_feeder",
            "cmd_puller", "cmd_spooler", "cmd_traverse",
        )) or row["purge_feed_approved"]
        for row in successful_purge_rows
    ):
        raise AssertionError("hot purge completion COOLDOWN/approval-consumed trace 불충분")
    fault_rows = [
        row for row in rows
        if row["scenario"] == "purge_screw_driver_fault_containment"
    ]
    if not fault_rows or any(
        row["driver_fault_free"]
        or row["material_session"] in ("PLA_ACTIVE", "PET_ACTIVE")
        or row["purge_run_completed"]
        for row in fault_rows
    ):
        raise AssertionError("purge driver-fault containment/pending material 유지 증거 불충분")

    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    for old in TRACE_DIR.glob("*.csv"):
        old.unlink()
    scenario_records = []
    for scenario in sorted(scenarios):
        scenario_rows = [row for row in rows if row["scenario"] == scenario]
        path = TRACE_DIR / f"{scenario}.csv"
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(scenario_rows)
        scenario_records.append({
            "name": scenario, "status": "PASS",
            "trace_file": str(path.relative_to(ROOT)), "event_count": len(scenario_rows),
            "sha256": sha256(path),
        })

    result = {
        "revision": REVISION, "status": "PASS",
        "harness": "production MachineSupervisor linked with fake InputSnapshot backend",
        "trace_power_method": "independent component-summed phase peak envelope",
        "purge_revolution_evidence": "COMMAND_DERIVED_ESTIMATE_NOT_MEASURED",
        "purge_operator_sequence": "approvePurgeFeed_then_independent_waste_path_confirmation",
        "production_sources": {
            str(path.relative_to(ROOT)): sha256(path) for path in compile_sources[:-1]
        },
        "production_headers": {
            str(path.relative_to(ROOT)): sha256(path) for path in production_headers
        },
        "validator_sources": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (
                Path(__file__).resolve(), ROOT / "validation/runtime_trace_rules.py"
            )
        },
        "harness_sha256": sha256(compile_sources[-1]), "scenario_count": len(scenarios),
        "trace_count": len(rows), "invariant_failure_count": 0,
        "bounded_sequence": {"fixed_seeds": 4, "maximum_events_per_seed": 64, "status": "PASS"},
        "calibration_readiness": {
            "state_requirements": contract["calibration_readiness"]["state_requirements"],
            "missing_one_gate_scenario": "calibration_readiness_phase_gates",
            "status": "PASS",
        },
        "scenarios": scenario_records,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "runtime_supervisor.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"RUNTIME_SUPERVISOR_E2E_OK scenarios={len(scenarios)} traces={len(rows)}")


if __name__ == "__main__":
    main()
