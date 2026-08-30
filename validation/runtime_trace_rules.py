#!/usr/bin/env python3
"""MachineSupervisor 런타임 trace용 fail-closed 안전 불변식.

상태 전이를 생성하지 않고 production harness가 관측한 행만 판정한다.
필수 관측 필드가 없으면 PASS가 아니라 실패로 처리한다.
"""

from __future__ import annotations

from collections.abc import Iterable

HAZARDOUS_COMMANDS = (
    "cmd_shredder",
    "cmd_screw",
    "cmd_process_heaters",
    "cmd_feeder",
    "cmd_puller",
    "cmd_spooler",
    "cmd_traverse",
    "cmd_cooling",
)
NON_COOLING_COMMANDS = tuple(name for name in HAZARDOUS_COMMANDS if name != "cmd_cooling")

REQUIRED_FIELDS = {
    "timestamp_ms",
    "scenario",
    "ui_state",
    "process_phase",
    "material_session",
    "forming_chain_state",
    "fault_reason",
    "drive_calibration_valid",
    "gauge_calibration_valid",
    "current_sensor_calibration_valid",
    "cooling_feedback_calibration_valid",
    "temperature_channels_valid",
    "driver_fault_free",
    "purge_feed_approved",
    "purge_waste_path_confirmed",
    "spool_eligible",
    "waste_mode",
    "heater_fault_latched",
    "shredder_fault_latched",
    "forming_fault_latched",
    "shredder_start_succeeded",
    "pending_material",
    "purge_run_completed",
    "cooling_command_pct",
    "cooling_feedback_valid",
    "cooling_failure_dwell_elapsed",
    "cooling_startup_request",
    "cooling_startup_probe_elapsed_ms",
    "cooling_startup_healthy_dwell_ms",
    "dancer_angle_rad",
    "dancer_hard_stop_rad",
    "nominal_spool_jam",
    "gauge_consecutive_valid_samples",
    "gauge_u95_mm",
    "diameter_error_mm",
    "ovality_mm",
    "stable_duration_ms",
    "transport_delay_elapsed",
    "puller_saturated",
    "estop_active",
    "explicit_restart_issued",
    "purge_screw_revolutions",
    "purge_revolutions_measured",
    "commanded_heater_power_w",
    "phase_peak_envelope_w",
    *HAZARDOUS_COMMANDS,
    "invariant_status",
}


def _enabled(row: dict, names: Iterable[str]) -> bool:
    return any(bool(row[name]) for name in names)


def validate_rows(rows: list[dict], contract: dict) -> list[str]:
    errors: list[str] = []
    if not rows:
        return ["EMPTY_RUNTIME_TRACE"]

    requal = contract["requalification"]
    dancer = contract["dancer"]
    power = contract["power"]
    cooling = contract["cooling_feedback"]
    previous: dict | None = None
    for index, row in enumerate(rows):
        missing = sorted(REQUIRED_FIELDS - row.keys())
        if missing:
            errors.append(f"row[{index}] MISSING_FIELDS:{','.join(missing)}")
            previous = row
            continue

        prefix = f"row[{index}] {row['scenario']}@{row['timestamp_ms']}"
        if not row["invariant_status"]:
            errors.append(prefix + " PRODUCTION_INVARIANT_FALSE")
        phase = row["process_phase"]
        lower_latch = bool(
            row["heater_fault_latched"]
            or row["shredder_fault_latched"]
            or row["forming_fault_latched"]
        )
        if phase == "IDLE" and lower_latch:
            errors.append(prefix + " IDLE_WITH_SUBSYSTEM_LATCH")
        if phase == "SHREDDING" and (
            not row["shredder_start_succeeded"] or not row["cmd_shredder"]
        ):
            errors.append(prefix + " SHREDDING_WITH_FAILED_START")
        if row["cmd_shredder"] and (
            row["cmd_screw"] or row["cmd_process_heaters"]
        ):
            errors.append(prefix + " SHREDDER_PROCESS_OVERLAP")

        pending = row["pending_material"]
        if pending in ("PLA", "PET") and row["material_session"] == pending + "_ACTIVE" and not row["purge_run_completed"]:
            errors.append(prefix + " PENDING_MATERIAL_ACTIVE_WITHOUT_PURGE")

        cooling_missing = (
            row["cooling_command_pct"] >= cooling["command_threshold_percent"]
            and not row["cooling_feedback_valid"]
            and row["cooling_failure_dwell_elapsed"]
        )
        if cooling_missing and (
            row["forming_chain_state"] == "NORMAL"
            or row["cmd_feeder"]
            or row["cmd_spooler"]
            or row["cmd_traverse"]
        ):
            errors.append(prefix + " COOLING_FEEDBACK_LOSS_NOT_CONTAINED")

        startup_request = row["cooling_startup_request"]
        if startup_request != "NONE":
            if phase != "IDLE":
                errors.append(prefix + " COOLING_STARTUP_COMMITTED_BEFORE_PROOF")
            if not row["cmd_cooling"]:
                errors.append(prefix + " COOLING_STARTUP_FAN_NOT_COMMANDED")
            if _enabled(row, NON_COOLING_COMMANDS):
                errors.append(prefix + " COOLING_STARTUP_HAZARDOUS_OUTPUT_BEFORE_PROOF")

        if row["nominal_spool_jam"] and row["dancer_angle_rad"] >= dancer["mechanical_hard_stop_rad"]:
            errors.append(prefix + " NOMINAL_JAM_CROSSED_HARD_STOP")
        if row["nominal_spool_jam"] and row["dancer_angle_rad"] >= dancer["controlled_stop_rad"] and row["cmd_spooler"]:
            errors.append(prefix + " SPOOLER_ACTIVE_AT_CONTROLLED_STOP")

        if (row["cmd_spooler"] or row["cmd_traverse"]) and not row["spool_eligible"]:
            errors.append(prefix + " INELIGIBLE_STRAND_TO_PRODUCTION_SPOOL")
        if row["spool_eligible"] and row["forming_chain_state"] in (
            "REQUALIFYING",
            "READY_TO_RETHREAD",
        ):
            errors.append(prefix + " SPOOL_ELIGIBLE_BEFORE_MANUAL_RETHREAD")
        if row["spool_eligible"] and (
            row["gauge_consecutive_valid_samples"] < requal["minimum_consecutive_valid_samples"]
            or row["gauge_u95_mm"] > requal["u95_max_mm"]
            or abs(row["diameter_error_mm"]) > requal["diameter_tolerance_mm"]
            or row["ovality_mm"] > requal["ovality_max_mm"]
            or row["stable_duration_ms"] < requal["diameter_stable_duration_s"] * 1000
            or not row["transport_delay_elapsed"]
            or row["puller_saturated"]
            or not row["cooling_feedback_valid"]
        ):
            errors.append(prefix + " SPOOL_ELIGIBILITY_WITHOUT_REQUALIFICATION")

        if phase == "MAINTENANCE_PURGE" and (
            row["phase_peak_envelope_w"] > power["normal_phase_peak_limit_w"]
            or power["psu_rating_w"] - row["phase_peak_envelope_w"] < power["minimum_reserve_w"]
        ):
            errors.append(prefix + " PURGE_POWER_ENVELOPE_EXCEEDED")
        if phase == "MAINTENANCE_PURGE" and not row["driver_fault_free"] and _enabled(row, HAZARDOUS_COMMANDS):
            errors.append(prefix + " PURGE_DRIVER_FAULT_MOTION_ACTIVE")
        if phase == "MAINTENANCE_PURGE" and row["material_session"] == "PURGE_RUNNING" and (
            not row["purge_feed_approved"] or not row["purge_waste_path_confirmed"]
        ):
            errors.append(prefix + " PURGE_RUNNING_WITHOUT_OPERATOR_PATH_CONFIRMATION")
        if phase == "MAINTENANCE_PURGE" and row["material_session"] in (
            "PURGE_PREHEAT_REQUIRED", "PURGE_READY_CONFIRM_REQUIRED",
        ) and _enabled(row, ("cmd_screw", "cmd_feeder", "cmd_puller", "cmd_spooler", "cmd_traverse")):
            errors.append(prefix + " PURGE_MOTION_BEFORE_WASTE_CONFIRMATION")

        if phase == "FAULT":
            cooling_failure = row["fault_reason"] == "COOLING_FAILURE"
            if cooling_failure and _enabled(row, HAZARDOUS_COMMANDS):
                errors.append(prefix + " COOLING_FAILURE_FAULT_OUTPUT_NOT_ZERO")
            if not cooling_failure and row["cmd_cooling"] and _enabled(row, NON_COOLING_COMMANDS):
                errors.append(prefix + " GENERAL_FAULT_NON_COOLING_COMMAND_ACTIVE")

        if row["estop_active"] and _enabled(row, HAZARDOUS_COMMANDS):
            errors.append(prefix + " ESTOP_HAZARDOUS_COMMAND_ACTIVE")
        if (
            previous is not None
            and previous.get("estop_active")
            and not row["estop_active"]
            and not row["explicit_restart_issued"]
            and _enabled(row, HAZARDOUS_COMMANDS)
        ):
            errors.append(prefix + " ESTOP_CLEAR_IMPLICIT_RESTART")
        previous = row
    return errors


def validate_fusion_binding(binding: dict, expected_source_sha: str) -> list[str]:
    actual = (
        binding.get("engineering_source_sha")
        or binding.get("source_commit_sha")
        or binding.get("source_git_sha")
    )
    if not actual:
        return ["FUSION_BINDING_SOURCE_SHA_MISSING"]
    if actual != expected_source_sha:
        return ["STALE_FUSION_BINDING_ACCEPTED"]
    if binding.get("fusion_result_state") not in ("PENDING_EXTERNAL_EXECUTION", "PENDING"):
        return ["FUSION_EXTERNAL_RESULT_STATE_NOT_PENDING"]
    return []


def validate_purge_contract(contract: dict) -> list[str]:
    purge = contract.get("purge", {})
    if purge.get("feed_approval_single_use") is not True:
        return ["STALE_PURGE_FEED_APPROVAL_REUSE_ALLOWED"]
    if purge.get("stale_feed_approval_reuse_forbidden") is not True:
        return ["STALE_PURGE_FEED_APPROVAL_REUSE_ALLOWED"]
    if set(purge.get("feed_approval_consumed_on", [])) != {
        "completion", "abort", "new_material_change_request",
    }:
        return ["STALE_PURGE_FEED_APPROVAL_REUSE_ALLOWED"]
    return []
