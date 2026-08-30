#!/usr/bin/env python3
"""v0.6.1 OpenModelica 결과를 transient·orchestration acceptance로 판정한다."""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SIM = ROOT / "simulation/openmodelica"
RAW = SIM / "results/raw"
OUT = SIM / "results"
C = json.loads((SIM / "acceptance_criteria.json").read_text())
GROUP = {name: set(values) for name, values in C["scenario_groups"].items()}
RELEASE_STATE = "SAFETY_ORCHESTRATION_BASELINE"
IMPLEMENTATION_STATE = "IMPLEMENTATION_BASELINE"


def number(value: str | None) -> float:
    if value is None or value == "":
        raise ValueError("empty CSV value")
    if value.lower() == "true":
        return 1.0
    if value.lower() == "false":
        return 0.0
    return float(value)


def load(name: str) -> list[dict[str, float]]:
    path = RAW / f"{name}_res.csv"
    if not path.exists():
        raise AssertionError(f"누락된 결과: {path}")
    with path.open(newline="") as stream:
        rows = [{key: number(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    if not rows or any(not math.isfinite(v) for row in rows for v in row.values()):
        raise AssertionError(f"비정상 결과: {name}")
    return rows


def maximum(rows, key): return max(row[key] for row in rows)
def minimum(rows, key): return min(row[key] for row in rows)
def peak(rows, key): return max(abs(row[key]) for row in rows)
def tail(rows, fraction=.2): return rows[max(0, int(len(rows)*(1-fraction))):]
def max_temperature(rows, prefix=""): return max(maximum(rows, prefix+k) for k in ("T1", "T2", "T3", "Tdie"))


def boolean_duration(rows: list[dict[str, float]], predicate) -> float:
    """CSV sample interval의 왼쪽 상태를 적분한다(마지막 sample은 폭 0)."""
    return sum(max(0, right["time"]-left["time"]) for left, right in zip(rows, rows[1:]) if predicate(left))


def first_time(rows: list[dict[str, float]], predicate) -> float | None:
    return next((row["time"] for row in rows if predicate(row)), None)


def speed_metrics(name: str, rows: list[dict[str, float]]) -> dict:
    target = 24 if name in {"PETNominal", "ColdStartPET"} else 28 if name in {"MotorRatedLoad", "MotorRatedLoadStrict"} else 32
    speed_key = "filteredCutterRPM" if "filteredCutterRPM" in rows[0] else "cutterRPM"
    final = tail(rows)
    steady = statistics.fmean(row[speed_key] for row in final)
    rise = next((row["time"] for row in rows if row[speed_key] >= .9*target), rows[-1]["time"])
    violations = [row["time"] for row in rows if row["time"] >= rise and abs(row[speed_key]-target) > .1*target]
    return {
        "rise_time_s": round(rise, 3),
        "settling_time_s": round(max(violations), 3) if violations else round(rise, 3),
        "steady_state_error_percent": round(abs(steady-target)/target*100, 3),
        "overshoot_percent": round(max(0, maximum(rows, speed_key)-target)/target*100, 3),
        "steady_rpm": round(steady, 3),
    }


def evaluate_shredder(name, rows, item, fail):
    item |= speed_metrics(name, rows)
    item |= {
        "peak_cutter_torque_nm": peak(rows, "estimatedCutterTorque"),
        "peak_phase_torque_nm": peak(rows, "phase.meshTorque"),
        "peak_phase_error_rad": peak(rows, "phase.phaseError"),
        "peak_bearing_load_n": peak(rows, "bearingLoad"),
        "peak_chain_force_n": peak(rows, "chain.tightSideForce"),
        "peak_motor_current_a": peak(rows, "motor.current"),
        "peak_cutter_rpm": peak(rows, "cutterRPM"),
        "retry_count": int(maximum(rows, "retryCount")),
        "retry_state": int(maximum(rows, "retryState")),
        "jam_detected": int(maximum(rows, "jamDetected")),
        "jam_fault": int(maximum(rows, "jamFault")),
        "fuse_broken": int(maximum(rows, "inputFuse.broken")),
        "min_duty": minimum(rows, "dutyCommand"),
    }
    if item["peak_phase_error_rad"] > C["phase_error_limit_rad"]: fail.append("phase error")
    if item["peak_cutter_torque_nm"] > C["mechanical_fuse_cutter_equivalent_nm"]+.05: fail.append("22 N.m hierarchy")
    if item["peak_cutter_rpm"] >= C["overspeed_hard_limit_rpm"]: fail.append("80 rpm hard overspeed")
    if item["peak_motor_current_a"] > C["stall_motor_current_a"]: fail.append("stall current")
    if name in {"PLANominal", "PETNominal"}:
        if item["steady_state_error_percent"] > C["speed_error_limit_percent"]: fail.append("steady speed error")
        if item["overshoot_percent"] > C["overshoot_limit_percent"]: fail.append("overshoot")
        if item["jam_fault"] or item["fuse_broken"]: fail.append("nominal false trip")
    if name in {"MotorRatedLoad", "MotorRatedLoadStrict"} and (item["peak_motor_current_a"] > C["rated_motor_current_a"] or item["steady_state_error_percent"] > C["speed_error_limit_percent"] or item["overshoot_percent"] > C["overshoot_limit_percent"]):
        fail.append("strict rated current/speed/overshoot")
    if name in {"ColdStartNoLoad", "ColdStartPLA", "ColdStartPET", "SlowAcceleration", "HighInertiaStart", "BrownoutLikeVoltageDrop", "MotorNoLoadStart"} and (item["jam_detected"] or item["fuse_broken"]): fail.append("startup false jam/fuse")
    if name == "MotorLoadStep" and (item["steady_state_error_percent"] > 12 or item["overshoot_percent"] > C["overshoot_limit_percent"] or item["jam_fault"]): fail.append("load-step recovery")
    if name in {"OneShaftJam", "LeftShaftJam", "FullJam", "RetryFailure"} and not (item["retry_count"] == 3 and item["retry_state"] == 4 and item["jam_fault"] and item["min_duty"] < 0 and not item["fuse_broken"]): fail.append("production three-retry FSM")
    if name == "ReverseClear" and not (item["retry_count"] == 1 and item["jam_detected"] and not item["jam_fault"] and not item["fuse_broken"] and item["min_duty"] < 0): fail.append("reverse clear")
    if name == "PhaseGearLoadReversal" and (item["peak_phase_torque_nm"] >= C["phase_allowable_torque_nm"] or item["peak_phase_error_rad"] > C["phase_error_limit_rad"] or item["min_duty"] >= 0): fail.append("phase reversal bound")
    if name == "MultiHookProtectiveTrip" and (not (item["jam_detected"] or item["jam_fault"] or item["fuse_broken"]) or item["peak_phase_torque_nm"] >= C["phase_allowable_torque_nm"] or item["peak_cutter_torque_nm"] >= C["shaft_allowable_torque_nm"]): fail.append("protective action before drivetrain allowables")
    if name == "MechanicalFuseTrip":
        broken = [row for row in rows if row["inputFuse.broken"] > .5]
        if not broken or max(abs(row["inputFuse.transmittedTorque"]) for row in broken[1:]) > 1e-6 or maximum(broken, "motor.enable") > 0: fail.append("ideal fuse separation/output removal")
    if name == "EmergencyStop":
        after = [row for row in rows if row["time"] >= 2.05]
        if max(abs(row["dutyCommand"]) for row in after) > 1e-6 or maximum(after, "motor.enable") > 0: fail.append("E-stop output removal")
    if name == "ChainBacklashReverse": item["classification"] = "SENSITIVITY_ONLY"


def evaluate_thermal(name, rows, item, fail):
    heaters = [row["power1"]+row["power2"]+row["power3"]+row["powerDie"] for row in rows]
    item |= {
        "max_temperature_c": max_temperature(rows), "peak_process_heater_w": max(heaters),
        "peak_net_flow_gph": peak(rows, "netFlowGPH"), "peak_screw_rpm": peak(rows, "screwRPM"),
        "peak_pressure_mpa": maximum(rows, "meltPressureMPa"), "peak_raw_pressure_mpa": maximum(rows, "rawPressureMPa"),
        "peak_screw_torque_nm": peak(rows, "motorTorque"), "peak_screw_current_a": peak(rows, "motorCurrent"),
        "ready": int(maximum(rows, "ready")), "drive_tripped": int(maximum(rows, "driveTripped")),
        "fuse_blown": int(maximum(rows, "fuseBlown")), "relief_state": int(maximum(rows, "reliefState")),
        "peak_relief_flow_gph": maximum(rows, "reliefFlowGPH"), "final_normal_flow_gph": rows[-1]["netFlowGPH"],
    }
    if item["peak_process_heater_w"] > C["process_heater_limit_w"]+1e-6: fail.append("360 W heater budget")
    if name in {"ExtruderWarmupPLA", "ExtruderWarmupPET", "ExtruderNominalPLA", "ExtruderNominalPET", "ExtruderHighFlow"} and not item["ready"]: fail.append("thermal ready")
    if name in {"ExtruderNominalPLA", "ExtruderNominalPET"} and (item["peak_net_flow_gph"] <= 0 or item["drive_tripped"]): fail.append("nominal closed flow-drive")
    if name == "ExtruderHighFlow": item["classification"] = "DIGITAL_STRETCH_TARGET"
    if name == "HeaterOpen" and (maximum(rows, "power2") > 1e-9 or item["ready"]): fail.append("heater open")
    if name == "SensorOpen" and item["peak_process_heater_w"] > 1e-9: fail.append("sensor-open inhibit")
    if name in {"MOSFETStuckOn", "ThermalFuseLongDuration"}:
        late = tail(rows, .05)
        equilibrium_delta = max_temperature(late)-max(minimum(late, k) for k in ("T1", "T2", "T3", "Tdie"))
        protected = item["fuse_blown"] or (item["max_temperature_c"] < 300 and equilibrium_delta < 2)
        item["protection_mechanism"] = "THERMAL_FUSE" if item["fuse_blown"] else "SUB_300C_STABLE_EQUILIBRIUM"
        if not protected: fail.append("stuck-on equilibrium/fuse")
    if name.startswith("HotExtrusionJam") and not (item["ready"] and item["drive_tripped"] and item["relief_state"] == 2 and item["peak_pressure_mpa"] < 6 and abs(rows[-1]["screwRPM"]) < .1 and rows[-1]["netFlowGPH"] < .1): fail.append("hot jam relief/trip propagation")
    if name.startswith("ReliefOpening") and not (item["relief_state"] == 2 and item["peak_raw_pressure_mpa"] >= 4.32 and item["peak_relief_flow_gph"] > 0 and item["final_normal_flow_gph"] < .1 and item["peak_pressure_mpa"] < 6): fail.append("retainer relief state/flow")


def evaluate_full(name, rows, item, fail):
    item |= {
        "peak_bus_power_w": peak(rows, "busPower"), "safe_state": int(minimum(rows, "safeState")),
        "feeder_enabled": int(maximum(rows, "feederEnable")), "puller_enabled": int(maximum(rows, "pullerEnable")),
        "spooler_enabled": int(maximum(rows, "spoolerEnable")), "final_screw_rpm": rows[-1]["extruder.screwRPM"],
        "final_net_flow_gph": rows[-1]["extruder.netFlowGPH"], "peak_pressure_mpa": maximum(rows, "extruder.meltPressureMPa"),
        "forming_chain_state_final": int(rows[-1]["formingChain.state"]), "fault_reason": int(maximum(rows, "formingChain.faultReason")),
        "spool_eligible_during_fault": int(max((row["spoolEligible"] for row in rows if row["formingChain.faultReason"] > .5), default=0)),
        "waste_mode_seen": int(maximum(rows, "wasteMode")), "cooling_feedback_min_a": minimum(rows, "coolingFeedbackCurrent"),
    }
    if item["peak_bus_power_w"] > C["normal_phase_peak_limit_w"]: fail.append("full-system power")
    if name in {"FullSystemPLA", "FullSystemPET"} and not item["safe_state"]: fail.append("nominal full-system invariants")
    if name in {"FullSystemGaugeFailure", "FullSystemJam"}:
        late = tail(rows, .05)
        if maximum(late, "feederEnable") or maximum(late, "pullerEnable") or maximum(late, "spoolerEnable"): fail.append("fault propagation")
    if name == "GaugeFailureControlledPause":
        fault_index = next((i for i,row in enumerate(rows) if int(row["formingChain.state"]) == 2 and row["formingChain.faultReason"] > .5),None)
        fault_entry = None if fault_index is None else rows[fault_index]["time"]
        containment_index = None if fault_index is None else next((i for i,row in enumerate(rows[fault_index:],fault_index) if row["feederEnable"]<.5 and row["spoolerEnable"]<.5),None)
        after = [] if containment_index is None else rows[containment_index:]
        rundown = [] if fault_entry is None else [row for row in rows if fault_entry <= row["time"] <= fault_entry+C["rundown_duration_s"]]
        thermal_hold = [row for row in rows if int(row["formingChain.state"]) == 3]
        after_rundown = [] if fault_entry is None else [row for row in rows if row["time"] >= fault_entry+C["rundown_duration_s"]+.01]
        production_before_fault = [] if fault_entry is None else [row for row in rows if row["time"] < fault_entry and int(row["formingChain.state"]) == 1]
        containment_latency = None if containment_index is None else rows[containment_index]["time"]-fault_entry
        if not production_before_fault or maximum(production_before_fault,"spoolEligible")<.5 or containment_latency is None or containment_latency>C["maximum_fault_response_latency_s"]+1e-6 or not after or maximum(after, "feederEnable") or maximum(after, "spoolerEnable") or not after_rundown or maximum(after_rundown, "pullerEnable") or rows[-1]["extruder.screwRPM"] >= .1 or rows[-1]["extruder.netFlowGPH"] >= .1 or not any(row["screwScale"] > 0 for row in rundown) or not any(row["pullerEnable"] > .5 for row in rundown) or not thermal_hold or not any(row["processHeaterEnabled"] > .5 for row in thermal_hold): fail.append("controlled gauge pause sequence")
    if name == "FeederLossDuringExtrusion" and not (maximum(rows, "extruder.feedRateGPH") > 0 and rows[-1]["extruder.feedRateGPH"] == 0 and rows[-1]["extruder.netFlowGPH"] < 1): fail.append("feeder physical coupling")
    if name == "CoolingLossDuringExtrusion":
        rundown_or_hold = [row for row in rows if int(row["formingChain.state"]) in {2,3} and row["formingChain.coolingRecoveryProbe"]<.5]
        recovery_probe = [row for row in rows if row["formingChain.coolingRecoveryProbe"]>.5]
        production_before_fault = [row for row in rows if row["time"]<1500 and int(row["formingChain.state"])==1]
        if not production_before_fault or maximum(production_before_fault,"spoolEligible")<.5 or maximum(rows,"forming.effectiveFanPercent")<=0 or not rundown_or_hold or maximum(rundown_or_hold,"forming.effectiveFanPercent")>.5 or not recovery_probe or maximum(recovery_probe,"forming.effectiveFanPercent")<=0 or maximum(recovery_probe,"coolingFeedbackValid")>.5 or maximum(recovery_probe,"spoolerEnable")>.5: fail.append("cooling permission/rundown/recovery-probe coupling")
    if name == "SpoolerPermissionLoss" and not (rows[-1]["spool.motorTorque"] == 0 and rows[-1]["spool.safePause"] > .5 and rows[-1]["pullerEnable"] < .5): fail.append("spooler actuator permission coupling")
    if name in {"GaugeLossRundown", "CoolingLossRundown", "SpoolPermissionLossRundown"}:
        fault_index = next((i for i,row in enumerate(rows) if row["rawFaultReason"]>.5),None)
        if fault_index is None:
            fail.append("forming-chain fault detection")
            return
        fault_time = rows[fault_index]["time"]
        entry_index = next((i for i,row in enumerate(rows[fault_index:],fault_index) if int(row["formingChain.state"])==2),None)
        entry = None if entry_index is None else rows[entry_index]["formingChain.stateEntryTime"]
        response_latency = None if entry is None else entry-fault_time
        item["response_latency_s"] = None if response_latency is None else round(response_latency,3)
        rundown = [row for row in rows if fault_time <= row["time"] <= fault_time+C["rundown_duration_s"]]
        if response_latency is None or response_latency < -1e-9 or response_latency > C["maximum_fault_response_latency_s"]+1e-6 or item["spool_eligible_during_fault"] or not rundown or not any(row["screwScale"] > 0 for row in rundown) or rows[-1]["spoolerEnable"] > .5: fail.append("common forming-chain rundown")
        if name == "CoolingLossRundown":
            states = {int(row["formingChain.state"]) for row in rows}
            if not {2,3,4}.issubset(states) or maximum(rows,"formingChain.coolingRecoveryProbe")<.5 or maximum(rows,"coolingFeedbackValid")<.5: fail.append("cooling recovery probe/requalification")
    if name == "GaugeRequalification":
        states = {int(row["formingChain.state"]) for row in rows}
        post_rethread = [row for row in rows if row["time"] >= 1900]
        ready = [row for row in rows if int(row["formingChain.state"]) == 5]
        recovery_states = [row for row in rows if int(row["formingChain.state"]) in {2,3,4,5} and row["time"]<1900]
        production_before_fault = [row for row in rows if row["time"]<1500 and int(row["formingChain.state"])==1]
        if not production_before_fault or maximum(production_before_fault,"spoolEligible")<.5 or not {2,3,4,5}.issubset(states) or item["spool_eligible_during_fault"] or not recovery_states or maximum(recovery_states,"spoolerEnable") > .5 or not ready or any(maximum(ready,key)>.5 for key in ("feederEnable","pullerEnable","spoolerEnable","traverseEnable")) or not post_rethread or maximum(post_rethread,"spoolEligible") < .5: fail.append("gauge requalification/rethread sequence")


def evaluate_power(name, rows, item, fail):
    components = ("shredderMotorPower", "driverLossPower", "heaterPower", "screwDrivePower", "feederPower", "pullerPower", "spoolerPower", "traversePower", "coolingPower", "electronicsPower")
    item |= {
        "average_power_w": statistics.fmean(row["phasePeakPower"] for row in rows), "peak_power_w": maximum(rows, "phasePeakPower"),
        "psu_current_a": maximum(rows, "psuCurrent"), "remaining_watt_margin": minimum(rows, "remainingWattMargin"),
        "remaining_ampere_margin": minimum(rows, "remainingAmpereMargin"), "overlap_blocked": int(minimum(rows, "overlapBlocked")),
        "power_budget_safe": int(minimum(rows, "powerBudgetSafe")),
    }
    item |= {f"peak_{key}_w": maximum(rows, key) for key in components}
    component_peak = max(sum(row[key] for key in components) for row in rows)
    if abs(component_peak-item["peak_power_w"]) > 1e-4: fail.append("dynamic component power sum")
    if not item["overlap_blocked"] or not item["power_budget_safe"] or item["peak_power_w"] > C["normal_phase_peak_limit_w"] or item["remaining_watt_margin"] < C["minimum_psu_reserve_w"]: fail.append("phase arbiter/power reserve")
    if name == "PreheatRequiresExplicitExtrusionArm" and any(maximum(rows,key)>.5 for key in ("screwEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled")): fail.append("explicit extrusion arm")
    if name == "PreheatRequiresExplicitExtrusionArm" and int(rows[-1]["processState"]) != 3: fail.append("failed-start phase rollback")
    if name == "PreheatRejectsUncalibratedCooling" and (int(rows[-1]["processState"]) != 1 or any(maximum(rows,key)>.5 for key in ("shredderEnabled","screwEnabled","processHeaterEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled","coolingEnabled"))): fail.append("preheat cooling-readiness rollback")
    if name == "PreheatRejectsInvalidCoolingFeedback":
        probe = [row for row in rows if row["coolingStartupProbeActive"]>.5]
        if int(rows[-1]["processState"]) != 10 or not probe or maximum(rows,"coolingEnabled")<.5 or any(maximum(probe,key)>.5 for key in ("shredderEnabled","screwEnabled","processHeaterEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled")): fail.append("preheat cooling startup timeout containment")
    if name == "PreheatCoolingStartupProbe":
        probe = [row for row in rows if row["coolingStartupProbeActive"]>.5]
        commit = first_time(rows, lambda row: row["processState"]==3)
        if not probe or commit is None or commit<2+1.5 or maximum(rows,"coolingStartupHealthyDwell")<1.5 or any(maximum(probe,key)>.5 for key in ("shredderEnabled","screwEnabled","processHeaterEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled")) or maximum(rows,"processHeaterEnabled")<.5: fail.append("preheat fan-first startup proof")
    if name == "PreheatCoolingProbeDropout":
        commit = first_time(rows, lambda row: row["processState"]==3)
        dropout = [row for row in rows if 2.5<=row["time"]<3.0]
        if commit is None or commit<4.5 or not dropout or minimum(dropout,"coolingStartupHealthyDwell")>1e-6 or maximum(rows,"processHeaterEnabled")<.5: fail.append("cooling startup consecutive-dwell reset")
    if name == "PurgeCoolingStartupProbe":
        probe = [row for row in rows if row["coolingStartupProbeActive"]>.5]
        commit = first_time(rows, lambda row: row["processState"]==5)
        if not probe or commit is None or commit<2+1.5 or maximum(rows,"coolingStartupHealthyDwell")<1.5 or any(maximum(rows,key)>.5 for key in ("screwEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled")) or maximum(rows,"processHeaterEnabled")<.5: fail.append("purge fan-first startup/waste approval separation")
    if name == "ShreddingRejectsUncalibratedCurrent" and (int(rows[-1]["processState"]) != 1 or maximum(rows,"shredderEnabled")>.5): fail.append("shredding current-readiness rollback")
    if name == "AtomicFaultClearNoPartial":
        if int(rows[-1]["processState"]) != 10 or any(maximum(rows,key)>.5 for key in ("shredderEnabled","screwEnabled","processHeaterEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled")): fail.append("atomic fault-clear rollback")
    if name == "CooldownAutomaticCompletion":
        idle = first_time(rows, lambda row: row["processState"] == 1)
        if idle is None or maximum([row for row in rows if row["time"] < idle],"coolingEnabled") < .5 or rows[-1]["coolingEnabled"] > .5 or next(row["cooldownProcessTemperature"] for row in rows if row["time"] == idle) > 60.0+1e-6: fail.append("cooldown automatic completion")
    if name == "FaultCoolingRetention" and (maximum(rows,"coolingEnabled") < .5 or any(maximum(rows,key)>.5 for key in ("shredderEnabled","screwEnabled","processHeaterEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled"))): fail.append("fault cooling retention")
    if name == "FaultCoolingInvalidFeedbackOff" and maximum(rows,"coolingEnabled") > .5: fail.append("invalid fault cooling inhibit")


def evaluate_forming(name, rows, item, fail):
    settled = [row for row in rows if row["time"] >= 10]
    disturbance = [row for row in rows if row["time"] >= 20]
    invalid = [row for row in rows if row["time"] >= 10 and (abs(row["diameterError"]) > C["diameter_initial_tolerance_mm"]+1e-6 or row["measuredOvality"] > C["diameter_initial_tolerance_mm"]+1e-6 or row["effectiveGaugeValid"] < .5)]
    invalid_start = invalid[0]["time"] if invalid else None
    invalid_end = invalid[-1]["time"] if invalid else None
    resumed = first_time(rows, lambda row: invalid_end is not None and row["time"] > invalid_end and row["spoolEligible"] > .5)
    qualification_scenarios = {"DiameterFlowStep","DiameterPullerDisturbance","GaugeNoise","GaugeBias","GaugeDropout","PullerSlip","PullerSaturation","OvalityDisturbance"}
    prequalified = any(row["spoolEligible"]>.5 and (invalid_start is None or row["time"]<invalid_start) for row in rows)
    item |= {
        "mass_flow_gph": maximum(rows, "effectiveMassFlowGPH"), "line_velocity_m_s": rows[-1]["pullerVelocity"],
        "cooling_residence_s": rows[-1]["coolingResidenceTime"], "puller_entry_mean_c": rows[-1]["meanTemperature"],
        "puller_entry_surface_c": rows[-1]["surfaceTemperature"], "predicted_diameter_mm": rows[-1]["predictedDiameter"],
        "diameter_error_mm": rows[-1]["diameterError"], "max_settled_diameter_error_mm": max(abs(row["diameterError"]) for row in settled),
        "control_margin_m_s": rows[-1]["controlMargin"], "virtual_diameter_pass": int(rows[-1]["virtualDiameterPass"]),
        "peak_ovality_mm": maximum(rows, "measuredOvality"), "safe_pause": int(maximum(rows, "safePause")),
        "maximum_absolute_diameter_error_mm": max(abs(row["diameterError"]) for row in settled),
        "out_of_tolerance_duration_s": round(boolean_duration(rows, lambda row: row["time"] >= 10 and (abs(row["diameterError"]) > C["diameter_initial_tolerance_mm"]+1e-6 or row["measuredOvality"] > C["diameter_initial_tolerance_mm"]+1e-6 or row["effectiveGaugeValid"] < .5)),3),
        "recovery_time_s": None if invalid_start is None or resumed is None else round(resumed-invalid_start,3),
        "spool_eligible_during_invalid": int(max((row["spoolEligible"] for row in invalid),default=0)),
    }
    if name in {"PLAFormingNominal", "PETFormingNominal"} and not item["virtual_diameter_pass"]: fail.append("nominal virtual forming")
    if name in qualification_scenarios and not prequalified: fail.append("disturbance injected before spool qualification")
    if name in {"DiameterFlowStep", "DiameterPullerDisturbance", "GaugeNoise", "GaugeBias", "PullerSlip"} and invalid:
        if item["spool_eligible_during_invalid"] or resumed is None: fail.append("transient containment/requalification")
    if name == "GaugeDropout":
        item["classification"] = "FAULT_CONTAINMENT_AND_REQUALIFICATION"
        if not (item["safe_pause"] and rows[-1]["safePause"] < .5) or item["spool_eligible_during_invalid"] or resumed is None or rows[-1]["spoolEligible"]<.5: fail.append("gauge dropout containment/requalification")
    if name == "PullerSaturation":
        item["classification"] = "CONTROL_LIMIT_DETECTED"
        if minimum(rows, "controlMargin") > 1e-5 or max(abs(row["diameterError"]) for row in disturbance) <= C["diameter_initial_tolerance_mm"] or item["spool_eligible_during_invalid"]: fail.append("puller saturation detection")
    if name == "OvalityDisturbance":
        item["classification"] = "OVALITY_FAULT_DETECTED"
        if item["peak_ovality_mm"] <= C["diameter_initial_tolerance_mm"] or maximum(rows, "ovalityRisk") < .5 or item["spool_eligible_during_invalid"]: fail.append("ovality disturbance detection")
    if name in {"PLAFormingHighFlow", "PETFormingHighFlow"}: item["classification"] = "DIGITAL_STRETCH_TARGET" if not item["virtual_diameter_pass"] else "VIRTUAL_DIAMETER_CONTROL_PASS"


def evaluate_purge(name, rows, item, fail):
    item |= {
        "purge_elapsed_s": maximum(rows,"purgeElapsed"),
        "purge_screw_revolutions": maximum(rows,"purgeScrewRevolutions"),
        "purge_complete": int(maximum(rows,"purgeComplete")),
        "pending_material_activated": int(maximum(rows,"pendingMaterialActivated")),
        "peak_power_w": maximum(rows,"busPower"),
        "minimum_reserve_w": C["psu_rating_w"]-maximum(rows,"busPower"),
        "spooler_enabled": int(maximum(rows,"spoolerEnable")),
        "traverse_enabled": int(maximum(rows,"traverseEnable")),
        "waste_mode_continuous": int(minimum(rows,"wasteMode")),
    }
    if item["peak_power_w"] > C["normal_phase_peak_limit_w"] or item["minimum_reserve_w"] < C["minimum_psu_reserve_w"]: fail.append("purge power reserve")
    if item["spooler_enabled"] or item["traverse_enabled"] or not item["waste_mode_continuous"]: fail.append("purge production winding isolation")
    if name in {"PurgePLAtoPET","PurgePETtoPLA"}:
        if not item["purge_complete"] or not item["pending_material_activated"] or item["purge_screw_revolutions"] < 32 or item["purge_elapsed_s"] < 120: fail.append("enforced purge completion")
    if name in {"PurgeWastePathBlocked","PurgeFeedApprovalMissing"} and (maximum(rows,"purgeActive") or maximum(rows,"screwEnabled") or maximum(rows,"feederEnable") or maximum(rows,"pullerEnable") or item["purge_complete"] or item["pending_material_activated"]): fail.append("independent waste-path/feed-approval start inhibit")
    if name in {"PurgeEmergencyStop","PurgeHeaterFault","PurgeScrewFault","PurgeCoolingFault"}:
        if item["purge_complete"] or item["pending_material_activated"]: fail.append("aborted purge material isolation")
        if name == "PurgeEmergencyStop":
            after = [row for row in rows if row["time"]>=1550.25]
            if not after or any(maximum(after,key)>.5 for key in ("screwEnabled","feederEnable","processHeaterEnabled","coolingEnabled")): fail.append("purge E-stop output removal")
        if name == "PurgeCoolingFault":
            after = [row for row in rows if row["time"]>=1501.75]
            if not after or maximum(after,"coolingHardFault")<.5 or any(maximum(after,key)>.5 for key in ("screwEnabled","feederEnable","pullerEnable","spoolerEnable","traverseEnable","processHeaterEnabled","coolingEnabled")): fail.append("purge cooling-loss same-cycle latch")


def evaluate_purge_lifecycle(name, rows, item, fail):
    cooldown = [row for row in rows if int(row["processState"])==9]
    hazardous = ("screwEnabled","processHeaterEnabled","feederEnabled","pullerEnabled","spoolerEnabled","traverseEnabled")
    item |= {
        "cooldown_seen": int(bool(cooldown)),
        "cooldown_max_temperature_c": maximum(cooldown,"cooldownProcessTemperature") if cooldown else None,
        "final_process_state": int(rows[-1]["processState"]),
        "final_material_session": int(rows[-1]["materialSession"]),
    }
    if not cooldown or maximum(cooldown,"coolingEnabled")<.5 or any(maximum(cooldown,key)>.5 for key in hazardous) or int(rows[-1]["processState"])!=1: fail.append("hot purge cooldown containment/exit")
    if name == "PurgeNormalAbortCooldown" and int(rows[-1]["materialSession"])!=4: fail.append("purge abort session recovery")
    if name == "PurgeSuccessfulCompletionCooldown":
        screen_while_hot = [row for row in rows if int(row["processState"])==9 and int(row["materialSession"])==7]
        if not screen_while_hot or maximum(screen_while_hot,"processState")!=9 or rows[-1]["pendingMaterialActivated"]<.5: fail.append("purge completion screen-clean/cooldown ordering")


def evaluate_orchestration_supervisor(name, rows, item, fail):
    states = {int(row["state"]) for row in rows}
    before_rethread = [row for row in rows if row["time"]>=1 and int(row["state"])!=1]
    requal_entry = first_time(rows,lambda row: row["time"]>=1 and int(row["state"])==4)
    ready_entry = first_time(rows,lambda row: row["time"]>=1 and int(row["state"])==5)
    normal_after_confirm = first_time(rows,lambda row: row["time"]>=35 and int(row["state"])==1)
    item |= {"states_seen": sorted(states), "spool_eligible_before_rethread": int(maximum(before_rethread,"spoolEligible")), "final_state": int(rows[-1]["state"]), "requal_entry_s": requal_entry, "ready_to_rethread_s": ready_entry, "normal_after_confirm_s": normal_after_confirm, "requalification_entry_to_ready_s": None if requal_entry is None or ready_entry is None else round(ready_entry-requal_entry,3)}
    if 2 in states or not {1,4,5}.issubset(states) or not before_rethread or maximum(before_rethread,"spoolEligible")>.5 or maximum(before_rethread,"wasteMode")<.5 or int(rows[-1]["state"])!=1: fail.append("quality violation direct requalification/fresh rethread")


def evaluate_tach_monitor(name, rows, item, fail):
    item |= {"startup_grace_seen": int(maximum(rows,"startupGraceActive")), "tach_qualified": int(maximum(rows,"tachQualified")), "rundown_requested": int(maximum(rows,"rundownRequested"))}
    if name == "PullerTachStartupGrace" and (not item["startup_grace_seen"] or not item["tach_qualified"] or item["rundown_requested"]): fail.append("puller tach startup false trip")
    if name == "PullerTachStartupFailure":
        detected = first_time(rows, lambda row: row["rundownRequested"]>.5)
        if detected is None or detected<1.5 or detected>1.5+0.01 or item["tach_qualified"]: fail.append("puller tach startup grace bound/rundown")


def evaluate(name: str, rows: list[dict[str, float]]) -> tuple[dict, list[str]]:
    fail: list[str] = []
    item: dict = {"scenario": name, "samples": len(rows)}
    if name in GROUP["shredder"]: evaluate_shredder(name, rows, item, fail)
    elif name in GROUP["thermal"]: evaluate_thermal(name, rows, item, fail)
    elif name in GROUP["spool"]:
        item |= {"radius_m": rows[-1]["spoolRadius"], "inertia_kg_m2": rows[-1]["spoolInertia"], "peak_spool_speed_rad_s": peak(rows, "spoolSpeed"), "peak_motor_torque_nm": peak(rows, "motorTorque"), "peak_motor_current_a": peak(rows, "motorCurrent"), "peak_dancer_angle_rad": peak(rows, "dancerAngle"), "peak_line_tension_n": peak(rows, "lineTension"), "peak_length_imbalance_m": peak(rows, "lineLengthImbalance"), "jam_detected": int(maximum(rows, "jamDetected")), "fault_detected": int(maximum(rows, "tensionFault")), "safe_pause": int(maximum(rows, "safePause")), "warning_seen": int(maximum(rows,"dancerWarning")), "controlled_stop_seen": int(maximum(rows,"dancerControlledStop")), "hard_stop_engaged": int(maximum(rows,"dancerHardStop")), "peak_hard_stop_reaction_nm": peak(rows,"hardStopReactionTorque")}
        if name in {"EmptySpool", "HalfSpool", "FullSpool"} and (item["peak_line_tension_n"] > C["line_tension_limit_n"] or item["peak_dancer_angle_rad"] > C["dancer_hard_stop_rad"] or item["fault_detected"]): fail.append("nominal spool dynamics")
        if name in {"SpoolJam", "RealSpoolJam", "SpoolJamPropagation", "EmptySpoolJam", "HalfSpoolJam", "FullSpoolJam"} and not (item["jam_detected"] and item["safe_pause"] and item["peak_spool_speed_rad_s"] < .02 and item["peak_length_imbalance_m"] < .1 and item["peak_dancer_angle_rad"] > .01 and not item["hard_stop_engaged"]): fail.append("locked-rotor controlled pause before hard stop")
        if name == "DancerLimit" and not item["fault_detected"]: fail.append("spool fault detection")
        if name == "DancerPrelimitStop" and not (item["warning_seen"] and item["controlled_stop_seen"] and item["safe_pause"] and not item["hard_stop_engaged"]): fail.append("dancer prelimit stop")
        if name == "DancerHardStopSensitivity":
            item["classification"]="SENSITIVITY_ONLY_NOT_NORMAL_SAFE_BEHAVIOR"
            if not item["hard_stop_engaged"] or item["peak_hard_stop_reaction_nm"]<=0: fail.append("hard-stop contact sensitivity")
    elif name in GROUP["full_system"]: evaluate_full(name, rows, item, fail)
    elif name in GROUP["process_power"]: evaluate_power(name, rows, item, fail)
    elif name in GROUP["forming"]: evaluate_forming(name, rows, item, fail)
    elif name in GROUP["purge"]: evaluate_purge(name, rows, item, fail)
    elif name in GROUP["purge_lifecycle"]: evaluate_purge_lifecycle(name, rows, item, fail)
    elif name in GROUP["orchestration_supervisor"]: evaluate_orchestration_supervisor(name, rows, item, fail)
    elif name in GROUP["tach_monitor"]: evaluate_tach_monitor(name, rows, item, fail)
    item["status"] = "PASS" if not fail else "FAIL"
    return item, fail


def main() -> None:
    names = C["required_scenarios"]
    if len(names) < 74 or len(set(names)) != len(names): raise AssertionError("74+ unique scenarios required")
    metrics, failures = [], {}
    for index, name in enumerate(names, 1):
        rows = load(name)
        if index % 5 == 0 or index == len(names):
            print(f"MODELICA_SUMMARY_PROGRESS loaded={index}/{len(names)}", flush=True)
        item, reasons = evaluate(name, rows); metrics.append(item)
        if reasons: failures[name] = reasons
        if index % 10 == 0 or index == len(names):
            print(f"MODELICA_ACCEPTANCE_PROGRESS evaluated={index}/{len(names)}", flush=True)
    shred = [row for row in metrics if row["scenario"] in GROUP["shredder"]]
    envelope = {"revision": C["revision"], "source": "OpenModelica DASSL virtual model; physical tests not run", "loads": {key: max(float(row[key]) for row in shred) for key in ("peak_cutter_torque_nm", "peak_phase_torque_nm", "peak_bearing_load_n", "peak_chain_force_n")}, "design_caps": {key: C[key] for key in ("electrical_trip_torque_nm", "mechanical_fuse_cutter_equivalent_nm", "phase_allowable_torque_nm", "shaft_allowable_torque_nm")}}
    summary = {"revision": C["revision"], "solver": C["solver"], "status": "PASS" if not failures else "FAIL", "release_state": RELEASE_STATE, "implementation_state": IMPLEMENTATION_STATE, "virtual_physics_state": "VIRTUAL_PHYSICS_VALIDATED" if not failures else "VIRTUAL_PHYSICS_FAILED", "cross_solver_state": "CROSS_SOLVER_VALIDATION_PENDING", "empirical_state": "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN", "failures": failures, "scenario_count": len(metrics), "scenarios": metrics}
    if summary["release_state"] != "SAFETY_ORCHESTRATION_BASELINE" or summary["implementation_state"] != "IMPLEMENTATION_BASELINE":
        raise AssertionError("release/implementation metadata drift")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    (OUT/"dynamic_load_envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2)+"\n")
    (ROOT/"analysis/load_cases/openmodelica_dynamic_envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2)+"\n")
    fields = sorted({key for row in metrics for key in row})
    with (OUT/"scenario_metrics.csv").open("w", newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(metrics)
    report = ["# OpenModelica virtual physics validation v0.6.1", "", f"- 판정: **{summary['status']}**", f"- 시나리오: {len(metrics)}개", f"- release: `{summary['release_state']}`", f"- implementation: `{summary['implementation_state']}`", f"- virtual physics: `{summary['virtual_physics_state']}`", "- cross solver: `CROSS_SOLVER_VALIDATION_PENDING`", "- empirical: `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`", "- 결과는 실제 제작품 성능·안전·직경 인증이 아니다.", "", "|시나리오|판정|분류|", "|---|---:|---|"] + [f"|{row['scenario']}|{row['status']}|{row.get('classification','RELEASE_ACCEPTANCE')}|" for row in metrics]
    (SIM/"reports/mechanical_validation_ko.md").write_text("\n".join(report)+"\n")
    if failures: raise SystemExit("OPENMODELICA_ACCEPTANCE_FAIL "+json.dumps(failures,ensure_ascii=False))
    print(f"OPENMODELICA_ACCEPTANCE_OK scenarios={len(metrics)} virtual=VALIDATED fusion=PENDING")


if __name__ == "__main__": main()
