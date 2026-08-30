#!/usr/bin/env python3
"""Canonical controller contract drift, power and invariant mutation checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "control/process_contract.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def invariant_results(permission: dict, actual: dict) -> dict[str, bool]:
    hazardous_off = not any(actual[key] for key in ("shredder", "screw", "process_heaters", "feeder", "puller", "spooler"))
    return {
        "shredder_drive_safe": actual["shredder"] == permission["shredder"] and not (actual["shredder"] and (actual["screw"] or actual["process_heaters"])),
        "screw_drive_safe": actual["screw"] == permission["screw"] and not (actual["screw"] and actual["shredder"]),
        "heater_safe": actual["process_heaters"] == permission["process_heaters"] and (not actual["thermal_fault"] or not actual["process_heaters"]),
        "feeder_safe": actual["feeder"] == permission["feeder"] and (not actual["feeder"] or actual["screw"]),
        "puller_safe": actual["puller"] == permission["puller"] and (not actual["puller"] or actual["gauge_valid"]),
        "spooler_safe": actual["spooler"] == permission["spooler"] and (not actual["spooler"] or actual["spool_eligible"]),
        "power_budget_safe": actual["power_w"] <= actual["power_limit_w"],
        "mechanical_fuse_state_safe": not actual["fuse_broken"] or actual["motor_command"] == 0,
        "restart_inhibited": not actual["fault_latched"] or not actual["restart_command"],
        "guard_chain_safe": actual["guard_ok"] or hazardous_off,
    }


def nominal(permission: dict, peak_w: float, limit_w: float) -> dict:
    return permission | {
        "thermal_fault": False, "gauge_valid": True, "spool_eligible": True,
        "power_w": peak_w, "power_limit_w": limit_w, "fuse_broken": False,
        "motor_command": 1 if permission["shredder"] or permission["screw"] else 0,
        "fault_latched": False, "restart_command": False, "guard_ok": True,
    }


def main() -> None:
    raw = CONTRACT_PATH.read_bytes()
    contract = json.loads(raw)
    baseline = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    require(contract["revision"] == baseline["revision"], "revision drift")
    require(contract["release"]["release_state"] == "SAFETY_ORCHESTRATION_BASELINE", "release state drift")
    require(contract["release"]["implementation_state"] == baseline["release_class"] == "IMPLEMENTATION_BASELINE", "implementation state drift")
    require(contract["release"]["virtual_physics_state"] == baseline["virtual_physics_state"], "virtual state drift")
    require(contract["release"]["empirical_state"] == baseline["empirical_state"], "empirical state drift")
    require(
        contract["jam"]["equation"] == "startup_grace_elapsed AND (torque_overload OR (current_sensor_saturated AND rpm_deficit))",
        "canonical jam Boolean equation drift",
    )
    digest = hashlib.sha256(raw).hexdigest()
    for rel in ("firmware/arduino_mega/src/generated_profiles.h", "simulation/openmodelica/PLA_PET_Recycler/GeneratedControl.mo"):
        require(digest in (ROOT / rel).read_text(), f"generated contract hash drift: {rel}")

    for material in ("PLA", "PET"):
        source = contract["materials"][material]
        require(source["shredder_rpm"] == baseline["shredder"][f"{material.lower()}_rpm"], f"{material} shredder RPM drift")
        require(source["screw_rpm"] == baseline["profiles"][material]["screw_rpm"], f"{material} screw RPM drift")
        require(source["fan_percent"] == baseline["profiles"][material]["fan_percent"], f"{material} fan drift")

    session = contract["material_session"]
    require(
        session["change_sequence"] == [
            "PURGE_PREHEAT_REQUIRED", "PURGE_READY_CONFIRM_REQUIRED", "PURGE_RUNNING",
            "SCREEN_CLEAN_REQUIRED", "HOPPER_CLEAN_REQUIRED",
            "TEMPERATURE_TRANSITION_REQUIRED", "FINAL_CONFIRM_REQUIRED",
        ],
        "material change sequence drift",
    )
    require(set(session["start_requires"]) == {
        "process_phase_IDLE_or_PREHEATING", "previous_material_thermal_profile_active",
        "thermal_chain_healthy", "cooling_feedback_calibrated",
    }, "material start interlock drift")
    require(set(session["purge_feed_requires"]) == {
        "cooling_startup_probe_proven", "waste_path_confirmed",
        "single_use_feed_approval", "screw_drive_healthy",
    }, "purge feed interlock drift")
    require(set(session["production_allowed"]) == {"PLA_ACTIVE", "PET_ACTIVE"}, "material production lock drift")
    readiness = contract["calibration_readiness"]
    require(readiness["temperature_channels"]["channels"] == ["T1", "T2", "T3", "Tdie", "Thopper"], "temperature channel drift")
    require(readiness["material_selection_does_not_imply_calibration"], "material/calibration separation drift")
    require(contract["cooling_feedback"]["backend"] == "fan_current_feedback_analog", "cooling feedback backend drift")
    heater = contract["heater_control"]
    require(heater["sample_period_ms"] == 250 and heater["time_proportion_window_ms"] == 2000, "heater timing drift")
    require(set(heater["process_heater_allowed_phases"]) == {"PREHEATING", "EXTRUSION", "MAINTENANCE_PURGE", "FORMING_CHAIN_RUNDOWN", "THERMAL_HOLD", "REQUALIFYING"}, "heater phase permission drift")
    require(heater["overtemperature_c"] < heater["maximum_valid_c"], "heater overtemperature must precede sensor ceiling")

    phase_rows = []
    voltage = contract["power"]["voltage_v"]
    rating = contract["power"]["psu_rating_w"]
    limit = contract["power"]["normal_phase_peak_limit_w"]
    for state, power in contract["power"]["phases"].items():
        require(sum(power["components_average_w"]) == power["average_w"], f"{state} average component sum drift")
        require(sum(power["components_peak_w"]) == power["peak_w"], f"{state} peak component sum drift")
        require(power["peak_w"] <= limit, f"{state} exceeds 500 W normal limit")
        require(rating - power["peak_w"] >= contract["power"]["minimum_reserve_w"], f"{state} reserve below 100 W")
        permission = contract["states"][state]
        results = invariant_results(permission, nominal(permission, power["peak_w"], limit))
        require(all(results.values()), f"nominal invariant failure {state}: {results}")
        phase_rows.append({
            "state": state, "average_w": power["average_w"], "peak_w": power["peak_w"],
            "peak_current_a": round(power["peak_w"] / voltage, 3),
            "remaining_w_margin": rating - power["peak_w"],
            "remaining_a_margin": round((rating - power["peak_w"]) / voltage, 3),
        })

    permission = contract["states"]["EXTRUSION"]
    base = nominal(permission, contract["power"]["phases"]["EXTRUSION"]["peak_w"], limit)
    mutations = {
        "shredder_drive_safe": {"shredder": True},
        "screw_drive_safe": {"screw": False},
        "heater_safe": {"thermal_fault": True},
        "feeder_safe": {"screw": False},
        "puller_safe": {"gauge_valid": False},
        "spooler_safe": {"spool_eligible": False},
        "power_budget_safe": {"power_w": 501.0},
        "mechanical_fuse_state_safe": {"fuse_broken": True, "motor_command": 1},
        "restart_inhibited": {"fault_latched": True, "restart_command": True},
        "guard_chain_safe": {"guard_ok": False},
    }
    mutation_results = {}
    for expected, mutation in mutations.items():
        result = invariant_results(permission, base | mutation)
        require(not result[expected], f"mutation did not fail {expected}")
        mutation_results[expected] = "FAIL_DETECTED"

    overlap = contract["states"]["SHREDDING"]
    require(overlap["shredder"] and not overlap["screw"] and not overlap["process_heaters"], "SHREDDING permission invariant")
    out = {
        "revision": contract["revision"], "status": "PASS", "contract_sha256": digest,
        "power_phases": phase_rows, "mutation_regressions": mutation_results,
        "hard_assertion": "not (shredder_enabled and (screw_enabled or process_heater_enabled))",
        "material_session": "ORDERED_CHANGE_AND_EXPLICIT_CONFIRMATION_PASS",
        "hardware_abstractions": "MEGA_IO_HEATER_GAUGE_COOLING_FEEDBACK_CONTRACT_PASS",
        "validator_sources": {
            str(Path(__file__).resolve().relative_to(ROOT)): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        },
    }
    path = ROOT / "validation/results/controller_contract.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("CONTROLLER_CONTRACT_POWER_INVARIANTS_OK")


if __name__ == "__main__":
    main()
