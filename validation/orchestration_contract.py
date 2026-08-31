#!/usr/bin/env python3
"""Firmware–Modelica safety-orchestration 계약 동등성과 독립 전력 합산 검증."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "safety-orchestration-closure-v0.6.1"
PROCESS_PATH = ROOT / "control/process_contract.json"
FAULT_PATH = ROOT / "control/fault_response_contract.json"
HEADER_PATH = ROOT / "firmware/arduino_mega/src/generated_profiles.h"
MODELICA_PATH = ROOT / "simulation/openmodelica/PLA_PET_Recycler/GeneratedControl.mo"

EXPECTED_PHASES = [
    "IDLE", "SHREDDING", "PREHEATING", "EXTRUSION", "MAINTENANCE_PURGE",
    "FORMING_CHAIN_RUNDOWN", "THERMAL_HOLD", "REQUALIFYING", "COOLDOWN",
    "FAULT", "ESTOP",
]
EXPECTED_MATERIAL_STATES = [
    "CLEAN", "PLA_ACTIVE", "PET_ACTIVE", "PURGE_PREHEAT_REQUIRED",
    "PURGE_READY_CONFIRM_REQUIRED", "PURGE_RUNNING", "SCREEN_CLEAN_REQUIRED",
    "HOPPER_CLEAN_REQUIRED", "TEMPERATURE_TRANSITION_REQUIRED", "FINAL_CONFIRM_REQUIRED",
]
EXPECTED_FORMING_STATES = [
    "NORMAL", "RUNDOWN", "THERMAL_HOLD", "REQUALIFYING",
    "READY_TO_RETHREAD", "LATCHED_FAULT",
]
EXPECTED_FAULTS = {
    "GAUGE_INVALID", "GAUGE_UNCERTAINTY_INVALID", "COOLING_FAILURE",
    "PULLER_DRIVER_FAILURE", "PULLER_TACH_FAILURE", "SPOOLER_DRIVER_FAILURE",
    "DANCER_CONTROLLED_STOP", "DANCER_HARD_LIMIT", "TRAVERSE_PERMISSION_LOSS",
}
MANDATORY_POWER_PHASES = {
    "MAINTENANCE_PURGE", "FORMING_CHAIN_RUNDOWN", "THERMAL_HOLD", "REQUALIFYING",
}
MANDATORY_SAFETY_INVARIANTS = {
    "atomic_fault_clear_has_no_partial_state_change",
    "failed_start_rolls_back_phase_and_outputs",
    "heater_requires_permission_feedback_and_valid_sensor",
    "estop_zeros_hazardous_outputs_within_one_supervisor_cycle",
    "no_implicit_restart_after_fault_or_estop",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_token(text: str, name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*([-+0-9.eE]+)", text)
    if not match:
        raise AssertionError(f"generated numeric constant missing: {name}")
    return float(match.group(1))


def close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    require(abs(actual - expected) <= tolerance, f"{label} drift: {actual} != {expected}")


def cpp_method(source: str, name: str) -> str:
    start = source.find(f"MachineSupervisor::{name}(")
    require(start >= 0, f"production method missing: {name}")
    end = source.find("\n}\n", start)
    require(end >= 0, f"production method boundary missing: {name}")
    return source[start:end]


def main() -> None:
    process = json.loads(PROCESS_PATH.read_text())
    fault = json.loads(FAULT_PATH.read_text())
    header = HEADER_PATH.read_text()
    modelica = MODELICA_PATH.read_text()
    process_source = (ROOT / "firmware/arduino_mega/src/process_state.cpp").read_text()
    supervisor_source = (ROOT / "firmware/arduino_mega/src/machine_supervisor.cpp").read_text()
    ino_source = (ROOT / "firmware/arduino_mega/arduino_mega.ino").read_text()
    calibration_source = (ROOT / "firmware/arduino_mega/src/calibration_record.h").read_text()
    calibration_test = (ROOT / "firmware/arduino_mega/tests/test_calibration_record.cpp").read_text()
    require(process["revision"] == fault["revision"] == REVISION, "contract revision drift")
    require(list(process["states"]) == EXPECTED_PHASES, "process phase/order drift")
    require(process["material_session"]["states"] == EXPECTED_MATERIAL_STATES, "material-session drift")
    require(process["forming_chain"]["states"] == EXPECTED_FORMING_STATES, "forming-chain states drift")
    require(set(process["forming_chain"]["fault_reasons"]) == EXPECTED_FAULTS | {"NONE"}, "fault reason drift")
    require(set(fault["faults"]) == EXPECTED_FAULTS, "fault-response coverage drift")
    require(MANDATORY_SAFETY_INVARIANTS <= set(process.get("safety_invariants", [])), "mandatory safety invariant missing")
    evidence = process.get("safety_invariant_evidence", {})
    require(MANDATORY_SAFETY_INVARIANTS <= set(evidence), "mandatory safety invariant evidence missing")
    clear_method = cpp_method(supervisor_source, "clearAllFaults")
    for token in ("canClearFaults", "commitFaultClear", "return true"):
        require(token in clear_method, f"atomic clear two-phase commit missing: {token}")
    finalize_method = cpp_method(supervisor_source, "finalizeOutput")
    for token in ("invariantsHold(commands)", "process_.reportFault()", "commands = ActuatorCommands{}", "false"):
        require(token in finalize_method, f"production invariant fail-closed missing: {token}")
    require(
        "output.invariants_ok ? output.actuators : ActuatorCommands{}" in ino_source,
        "Arduino adapter invariant-false same-cycle zero missing",
    )
    require(
        "intent == UiIntent::PAUSE || intent == UiIntent::BACK" in ino_source
        and "supervisor.requestStop(input)" in ino_source,
        "physical PAUSE/BACK purge abort routing missing",
    )
    require(
        "record = CalibrationRecord{}" in calibration_source
        and "sanitizeCalibrationRecord(calibration_record)" in ino_source
        and "stale.version = 3" in calibration_test
        and "garbage.magic == 0 && garbage.version == 0 && garbage.readiness_flags == 0" in calibration_test
        and "calibrationDomainReady(record, CAL_TRAVERSE)" in calibration_test,
        "invalid EEPROM calibration zero-sanitize/reload regression missing",
    )

    transition_rows: dict[str, list[str]] = {}
    for state in EXPECTED_PHASES:
        match = re.search(
            rf"case MachineState::{state}: return (.*?);", process_source
        )
        require(match is not None, f"production transition row missing: {state}")
        transition_rows[state] = re.findall(r"next == MachineState::([A-Z_]+)", match.group(1))
    require(process.get("transitions") == transition_rows, "canonical/production transition matrix drift")
    transition_matrix = [
        [target in transition_rows[state] for target in EXPECTED_PHASES]
        for state in EXPECTED_PHASES
    ]
    transition_token = "transitionAllowed[11,11]=[" + ";".join(
        ",".join(str(value).lower() for value in row) for row in transition_matrix
    ) + "]"
    require(transition_token in modelica, "Modelica transition matrix drift")

    expected_readiness = {
        "SHREDDING": ["drive", "current_sensor"],
        "PREHEATING": ["gauge", "temperature_channels", "cooling_feedback"],
        "EXTRUSION": ["gauge", "temperature_channels", "cooling_feedback"],
        "MAINTENANCE_PURGE": ["temperature_channels", "cooling_feedback"],
        "REQUALIFYING": ["gauge", "temperature_channels", "cooling_feedback"],
    }
    readiness = process.get("calibration_readiness", {})
    require(readiness.get("state_requirements") == expected_readiness, "phase calibration-readiness drift")
    for calibration in {value for values in expected_readiness.values() for value in values}:
        require(calibration in readiness, f"calibration readiness definition missing: {calibration}")
    require(
        readiness["cooling_feedback"].get("readiness_kind") == "CALIBRATION_ONLY_NOT_LIVE_HEALTH",
        "cooling calibration readiness가 fan-off live feedback과 혼동됨",
    )
    production_gate_tokens = {
        "SHREDDING": ("requestShredding", "shredder_drive_valid", "current_sensor_valid", "shredder_tach_valid"),
        "PREHEATING": ("requestPreheat", "gauge_calibration_valid", "cooling_feedback_calibration_valid", "fan1_tach_valid", "fan2_tach_valid", "temperatureChannelsHealthy"),
        "EXTRUSION": ("armExtrusion", "gauge_xy_valid", "cooling_current_valid", "formingCalibrationReady", "temperatures_ready"),
        "MAINTENANCE_PURGE": ("requestPurgePreheat", "cooling_feedback_calibration_valid", "fan1_tach_valid", "fan2_tach_valid", "temperatureChannelsHealthy"),
        "REQUALIFYING": ("armExtrusion", "gauge_xy_valid", "cooling_current_valid", "formingCalibrationReady", "temperatures_ready"),
    }
    for phase, tokens in production_gate_tokens.items():
        method = cpp_method(supervisor_source, tokens[0])
        require(all(token in method for token in tokens[1:]), f"production readiness gate missing: {phase}")
    calibration_order = ["drive", "gauge", "current_sensor", "temperature_channels", "cooling_feedback"]
    calibration_matrix = [
        [domain in expected_readiness.get(state, []) for domain in calibration_order]
        for state in EXPECTED_PHASES
    ]
    calibration_token = "calibrationRequired[11,5]=[" + ";".join(
        ",".join(str(value).lower() for value in row) for row in calibration_matrix
    ) + "]"
    require(calibration_token in modelica, "Modelica calibration-readiness matrix drift")

    process_sha = digest(PROCESS_PATH)
    fault_sha = digest(FAULT_PATH)
    require(process_sha in header and fault_sha in header, "Arduino generated contract hash drift")
    require(process_sha in modelica and fault_sha in modelica, "Modelica generated contract hash drift")
    require("enum class MachineState : uint8_t { " + ", ".join(EXPECTED_PHASES) + " };" in header, "Arduino phase enum drift")
    require("enum class MaterialSession : uint8_t { " + ", ".join(EXPECTED_MATERIAL_STATES) + " };" in header, "Arduino material enum drift")
    for index, state in enumerate(EXPECTED_PHASES, 1):
        require(f"constant Integer {state}={index};" in modelica, f"Modelica phase index drift: {state}")
    for index, state in enumerate(EXPECTED_FORMING_STATES, 1):
        require(f"constant Integer FORMING_{state}={index};" in modelica, f"Modelica forming index drift: {state}")

    actuators = process["actuator_order"]
    require(actuators == ["shredder", "screw", "process_heaters", "feeder", "puller", "spooler", "traverse", "cooling"], "actuator order drift")
    permission_rows = [
        ",".join(str(bool(process["states"][state][actuator])).lower() for actuator in actuators)
        for state in EXPECTED_PHASES
    ]
    expected_permissions = f"permissions[{len(EXPECTED_PHASES)},{len(actuators)}]=[" + ";".join(permission_rows) + "]"
    require(expected_permissions in modelica, "Modelica permission matrix drift")
    require(process["states"]["SHREDDING"]["shredder"] and not process["states"]["SHREDDING"]["screw"] and not process["states"]["SHREDDING"]["process_heaters"], "shredder overlap contract")
    for state in process["spool_eligibility"]["false_states"]:
        phase = "FORMING_CHAIN_RUNDOWN" if state == "RUNDOWN" else state
        if phase in process["states"]:
            require(not process["states"][phase]["spooler"] and not process["states"][phase]["traverse"], f"spool eligibility permission drift: {phase}")

    common = fault["common_response"]
    require(common["feeder"] == "OFF_IMMEDIATE", "forming feeder response drift")
    require(common["screw"] == "BOUNDED_RUNDOWN_THEN_OFF", "forming screw response drift")
    require(common["spooler"] == common["traverse"] == "OFF_IMMEDIATE", "winding response drift")
    require(common["cooling"] == "KEEP_ON_IF_FEEDBACK_VALID_EXCEPT_COOLING_FAILURE_OR_ESTOP", "fault cooling policy drift")
    require(common["spool_eligible"] is False and common["waste_mode"] is True, "waste/spool common response drift")
    puller_grace = fault["timing"].get("puller_tach_startup_grace_s")
    require(puller_grace == 1.5, "puller tach startup grace contract drift")
    close(numeric_token(modelica, "pullerTachStartupGrace"), puller_grace, "Modelica puller tach startup grace")
    puller_method = cpp_method(supervisor_source, "pullerTachFault")
    for token in ("puller_tach_qualified_", "PULLER_TACH_STARTUP_GRACE_MS", "input.puller_tach_ok"):
        require(token in puller_method, f"production puller tach grace missing: {token}")
    for reason, response in fault["faults"].items():
        require(response["maximum_response_latency_s"] <= fault["timing"]["maximum_response_latency_s"], f"fault latency drift: {reason}")
        require(response["transition_target"] in EXPECTED_FORMING_STATES, f"fault target drift: {reason}")
        require(response["recovery_requirement"], f"fault recovery missing: {reason}")

    purge = process["purge"]
    require(purge.get("feed_approval_single_use") is True, "purge feed approval single-use missing")
    require(set(purge.get("feed_approval_consumed_on", [])) == {
        "completion", "abort", "new_material_change_request",
    }, "purge feed approval consumption points drift")
    require(purge.get("stale_feed_approval_reuse_forbidden") is True, "stale purge approval reuse allowed")
    require("purgeFeedApprovalSingleUse=true" in modelica, "Modelica purge approval single-use drift")
    require(purge.get("screw_revolution_evidence") == "COMMAND_DERIVED_ESTIMATE_NOT_MEASURED", "purge revolution evidence가 실측처럼 해석될 수 있음")
    require(purge.get("revolution_estimate_invalidated_by_driver_fault") is True, "purge revolution estimate driver-fault invalidation missing")
    require(purge["completion_is_mass_measured"] is False, "purge mass completion false claim")
    complete_purge_method = cpp_method(process_source.replace("ProcessController::", "MachineSupervisor::"), "completePurgeRun")
    abort_purge_method = cpp_method(process_source.replace("ProcessController::", "MachineSupervisor::"), "abortPurge")
    require("MachineState::COOLDOWN" in complete_purge_method, "hot purge completion bypasses COOLDOWN")
    require("MachineState::COOLDOWN" in abort_purge_method, "hot purge abort bypasses COOLDOWN")
    confirm_complete = cpp_method(supervisor_source, "confirmPurgeComplete")
    require(
        "input.cooling_feedback_valid" in confirm_complete or
        "coolingSnapshotHealthy(input)" in confirm_complete,
        "fresh purge completion cooling preflight missing",
    )
    for token in ("temperatureChannelsHealthy(input)", "guardsOk(input)"):
        require(token in confirm_complete, f"fresh purge completion preflight missing: {token}")

    requal = process["requalification"]
    startup_probe = process["cooling_feedback"]["startup_probe"]
    require(startup_probe == {
        "request_origin_state": "IDLE",
        "required_for_requested_phases": ["PREHEATING", "MAINTENANCE_PURGE"],
        "fan_only_during_probe": True,
        "command_percent_by_material": {"PLA": 100.0, "PET": 100.0},
        "healthy_feedback_dwell_s": 1.5,
        "timeout_s": 3.0,
        "success_commits_requested_phase": True,
        "failure_transition": "FAULT",
        "inhibited_until_proven": [
            "process_heaters", "screw", "feeder", "puller", "spooler", "traverse",
        ],
        "clear_does_not_require_live_feedback_when_fan_off": True,
        "next_start_requires_new_probe": True,
        "automatic_restart_forbidden": True,
    }, "cooling startup probe canonical contract drift")
    for method_name in ("requestPreheat", "requestPurgePreheat"):
        method = cpp_method(supervisor_source, method_name)
        require("cooling_feedback_calibration_valid" in method, f"{method_name} cooling calibration gate missing")
        require("input.cooling_feedback_valid" not in method, f"{method_name} fan-off live feedback deadlock")
    startup_method = cpp_method(supervisor_source, "updateCoolingStartupProbe")
    for token in ("COOLING_STARTUP_HEALTHY_DWELL_MS", "COOLING_STARTUP_PROBE_TIMEOUT_MS",
                  "CoolingStartupRequest::PREHEAT", "enterLatchedFormingFault"):
        require(token in startup_method, f"production cooling startup probe missing: {token}")
    close(numeric_token(modelica, "coolingStartupProbeDwell"), startup_probe["healthy_feedback_dwell_s"], "Modelica startup dwell")
    close(numeric_token(modelica, "coolingStartupProbeTimeout"), startup_probe["timeout_s"], "Modelica startup timeout")
    require("coolingStartupProbeCommandByMaterial[2]={100,100}" in modelica, "Modelica startup fan command drift")
    require("coolingStartupProbeFanOnly=true" in modelica, "Modelica startup fan-only drift")
    startup_required = [state in startup_probe["required_for_requested_phases"] for state in EXPECTED_PHASES]
    require(
        "coolingStartupProbeRequiredByState[11]={" + ",".join(str(value).lower() for value in startup_required) + "}" in modelica,
        "Modelica startup required-state matrix drift",
    )
    cooldown = process["cooldown_completion"]
    require(cooldown == {
        "max_process_temperature_c": 60.0,
        "required_channels": ["T1", "T2", "T3", "Tdie"],
        "all_channels_valid_required": True,
        "cooling_feedback_valid_required": True,
        "completion_transition": "IDLE",
        "automatic_when_satisfied": True,
    }, "cooldown completion contract drift")
    cooldown_method = cpp_method(supervisor_source, "canCompleteCooldown")
    for token in ("COOLDOWN_SAFE_TEMPERATURE_C", "cooling_feedback_valid"):
        require(token in cooldown_method, f"production cooldown gate missing: {token}")
    constants = {
        "purgeMinTime": purge["minimum_elapsed_s"],
        "purgeMinScrewRevolutions": purge["minimum_screw_revolutions"],
        "rundownDuration": fault["timing"]["screw_rundown_s"],
        "thermalHoldDuration": fault["timing"]["thermal_hold_s"],
        "pullerWasteDuration": fault["timing"]["puller_waste_s"],
        "coolingFeedbackDwell": process["cooling_feedback"]["fault_dwell_s"],
        "cooldownMaximumProcessTemperature": cooldown["max_process_temperature_c"],
        "requalGaugeSamples": requal["minimum_consecutive_valid_samples"],
        "requalU95Max": requal["u95_max_mm"],
        "requalDiameterTolerance": requal["diameter_tolerance_mm"],
        "requalStableDuration": requal["diameter_stable_duration_s"],
        "requalOvalityMax": requal["ovality_max_mm"],
        "dancerWarning": process["dancer"]["warning_rad"],
        "dancerControlledStop": process["dancer"]["controlled_stop_rad"],
        "dancerHardStop": process["dancer"]["mechanical_hard_stop_rad"],
    }
    for name, expected in constants.items():
        close(numeric_token(modelica, name), float(expected), "Modelica " + name)
    require(process["dancer"]["warning_rad"] < process["dancer"]["controlled_stop_rad"] < process["dancer"]["mechanical_hard_stop_rad"], "dancer threshold ordering")

    physical = requal.get("transport_delay_physical_minimum_s")
    basis = requal.get("transport_delay_basis", "")
    require(isinstance(physical, dict) and set(physical) == {"PLA", "PET"}, "transport physical minimum provenance missing")
    require("DIGITAL_STRETCH_TARGET" in basis and "nominal" in basis.lower(), "transport delay semantic distinction missing")
    for material in ("PLA", "PET"):
        require(requal["transport_delay_s"][material] >= physical[material], f"{material} qualification delay below physical minimum")
    require("transportDelayByMaterial[2]={" + ",".join(f"{requal['transport_delay_s'][m]:g}" for m in ("PLA", "PET")) + "}" in modelica, "Modelica transport delay drift")
    docs = (ROOT / "docs/design_report_ko.typ").read_text() + (ROOT / "docs/operation.md").read_text()
    for value in ("13.3", "14.9", "26.7", "28.6", "DIGITAL_STRETCH_TARGET"):
        require(value in docs, f"transport delay documentation missing: {value}")

    power = process["power"]
    require(MANDATORY_POWER_PHASES <= set(power["phases"]), "mandatory power phases missing")
    phase_rows = []
    for phase, values in power["phases"].items():
        require(len(values["components_average_w"]) == len(power["component_order"]), f"average component width: {phase}")
        require(len(values["components_peak_w"]) == len(power["component_order"]), f"peak component width: {phase}")
        calculated_average = sum(values["components_average_w"])
        calculated_peak = sum(values["components_peak_w"])
        close(calculated_average, values["average_w"], phase + " component average")
        close(calculated_peak, values["peak_w"], phase + " component peak")
        require(calculated_peak <= power["normal_phase_peak_limit_w"], f"{phase} >500 W")
        reserve_w = power["psu_rating_w"] - calculated_peak
        require(reserve_w >= power["minimum_reserve_w"], f"{phase} reserve <100 W")
        phase_rows.append({
            "phase": phase, "average_w": calculated_average, "peak_w": calculated_peak,
            "psu_current_a": round(calculated_peak / power["voltage_v"], 3),
            "remaining_w_margin": reserve_w,
            "remaining_a_margin": round(reserve_w / power["voltage_v"], 3),
        })

    result = {
        "revision": REVISION, "status": "PASS", "process_contract_sha256": process_sha,
        "fault_response_contract_sha256": fault_sha,
        "equivalence": {
            "process_phases": "PASS", "material_session_states": "PASS",
            "transition_matrix": "PASS", "calibration_readiness": "PASS",
            "cooling_startup_probe": "PASS", "invariant_fail_closed": "PASS",
            "physical_ui_purge_abort": "PASS", "eeprom_zero_sanitize": "PASS",
            "puller_tach_startup_grace": "PASS", "hot_purge_cooldown": "PASS",
            "purge_permissions": "PASS", "fault_response_table": "PASS",
            "rundown_durations": "PASS", "requalification_thresholds": "PASS",
            "spool_eligibility": "PASS", "dancer_thresholds": "PASS",
            "power_permissions": "PASS", "arduino_generated_header": "PASS",
            "openmodelica_generated_parameters": "PASS",
        },
        "transport_delay": {
            "physical_minimum_s_at_digital_stretch": physical,
            "qualification_delay_s_at_nominal": requal["transport_delay_s"],
            "semantic_equivalence": "DISTINCT_OPERATING_POINTS_DOCUMENTED",
        },
        "power_phases": phase_rows,
        "validator_sources": {
            str(Path(__file__).resolve().relative_to(ROOT)): digest(Path(__file__).resolve())
        },
        "production_audit_sources": {
            str(path.relative_to(ROOT)): digest(path)
            for path in (
                ROOT / "firmware/arduino_mega/arduino_mega.ino",
                ROOT / "firmware/arduino_mega/src/machine_supervisor.cpp",
                ROOT / "firmware/arduino_mega/src/process_state.cpp",
                ROOT / "firmware/arduino_mega/src/calibration_record.h",
                ROOT / "firmware/arduino_mega/tests/test_calibration_record.cpp",
                HEADER_PATH, MODELICA_PATH,
            )
        },
    }
    output = ROOT / "validation/results/orchestration_contract.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"ORCHESTRATION_CONTRACT_EQUIVALENCE_OK phases={len(EXPECTED_PHASES)} power={len(phase_rows)}")


if __name__ == "__main__":
    main()
