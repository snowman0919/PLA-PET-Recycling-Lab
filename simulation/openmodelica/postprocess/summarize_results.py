#!/usr/bin/env python3
"""55개 virtual-physics scenario를 비자명한 물리 acceptance로 판정한다."""

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


def number(value: str | None) -> float:
    if value is None or value == "": raise ValueError("empty CSV value")
    if value.lower() == "true": return 1.0
    if value.lower() == "false": return 0.0
    return float(value)


def load(name: str) -> list[dict[str, float]]:
    path = RAW / f"{name}_res.csv"
    if not path.exists(): raise AssertionError(f"누락된 결과: {path}")
    with path.open(newline="") as stream:
        rows = [{key: number(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    if not rows or any(not math.isfinite(v) for row in rows for v in row.values()): raise AssertionError(f"비정상 결과: {name}")
    return rows


def maximum(rows, key): return max(row[key] for row in rows)
def minimum(rows, key): return min(row[key] for row in rows)
def peak(rows, key): return max(abs(row[key]) for row in rows)
def tail(rows, fraction=.2): return rows[max(0, int(len(rows)*(1-fraction))):]
def max_temperature(rows, prefix=""): return max(maximum(rows, prefix+k) for k in ("T1", "T2", "T3", "Tdie"))


def speed_metrics(name: str, rows: list[dict[str, float]]) -> dict:
    target = 24 if name in {"PETNominal", "ColdStartPET"} else 28 if name == "MotorRatedLoad" else 32
    final = tail(rows)
    steady = statistics.fmean(row["cutterRPM"] for row in final)
    rise = next((row["time"] for row in rows if row["cutterRPM"] >= .9*target), rows[-1]["time"])
    violations = [row["time"] for row in rows if row["time"] >= rise and abs(row["cutterRPM"]-target) > .1*target]
    return {
        "rise_time_s": round(rise, 3),
        "settling_time_s": round(max(violations), 3) if violations else round(rise, 3),
        "steady_state_error_percent": round(abs(steady-target)/target*100, 3),
        "overshoot_percent": round(max(0, maximum(rows, "cutterRPM")-target)/target*100, 3),
        "steady_rpm": round(steady, 3),
    }


def evaluate(name: str, rows: list[dict[str, float]]) -> tuple[dict, list[str]]:
    fail: list[str] = []
    item: dict = {"scenario": name, "samples": len(rows)}
    if name in GROUP["shredder"]:
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
        if name in {"ColdStartNoLoad", "ColdStartPLA", "ColdStartPET", "SlowAcceleration", "HighInertiaStart", "BrownoutLikeVoltageDrop", "MotorNoLoadStart"} and (item["jam_detected"] or item["fuse_broken"]): fail.append("startup false jam/fuse")
        if name == "MotorLoadStep" and (item["steady_state_error_percent"] > 12 or item["overshoot_percent"] > C["overshoot_limit_percent"] or item["jam_fault"]): fail.append("load-step recovery")
        if name in {"OneShaftJam", "FullJam", "RetryFailure"} and not (item["retry_count"] == 3 and item["retry_state"] == 4 and item["jam_fault"] and item["min_duty"] < 0 and not item["fuse_broken"]): fail.append("production three-retry FSM")
        if name == "ReverseClear" and not (item["retry_count"] == 1 and item["jam_detected"] and not item["jam_fault"] and not item["fuse_broken"] and item["min_duty"] < 0): fail.append("reverse clear")
        if name == "MechanicalFuseTrip":
            broken = [row for row in rows if row["inputFuse.broken"] > .5]
            if not broken or max(abs(row["inputFuse.transmittedTorque"]) for row in broken[1:]) > 1e-6 or maximum(broken, "motor.enable") > 0: fail.append("ideal fuse separation/output removal")
        if name == "EmergencyStop":
            after = [row for row in rows if row["time"] >= 2.05]
            if max(abs(row["dutyCommand"]) for row in after) > 1e-6 or maximum(after, "motor.enable") > 0: fail.append("E-stop output removal")
        if name == "ChainBacklashReverse": item["classification"] = "SENSITIVITY_ONLY"

    elif name in GROUP["thermal"]:
        heaters = [row["power1"]+row["power2"]+row["power3"]+row["powerDie"] for row in rows]
        item |= {
            "max_temperature_c": max_temperature(rows), "peak_process_heater_w": max(heaters),
            "peak_net_flow_gph": peak(rows, "netFlowGPH"), "peak_screw_rpm": peak(rows, "screwRPM"),
            "peak_pressure_mpa": maximum(rows, "meltPressureMPa"), "peak_screw_torque_nm": peak(rows, "motorTorque"),
            "peak_screw_current_a": peak(rows, "motorCurrent"), "ready": int(maximum(rows, "ready")),
            "drive_tripped": int(maximum(rows, "driveTripped")), "fuse_blown": int(maximum(rows, "fuseBlown")),
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
        if name.startswith("HotExtrusionJam") and not (item["ready"] and item["drive_tripped"] and item["peak_pressure_mpa"] <= 8.01 and abs(rows[-1]["screwRPM"]) < .1 and rows[-1]["netFlowGPH"] < .1): fail.append("hot jam propagation")

    elif name in GROUP["spool"]:
        item |= {
            "radius_m": rows[-1]["spoolRadius"], "inertia_kg_m2": rows[-1]["spoolInertia"],
            "peak_spool_speed_rad_s": peak(rows, "spoolSpeed"), "peak_motor_torque_nm": peak(rows, "motorTorque"),
            "peak_motor_current_a": peak(rows, "motorCurrent"), "peak_dancer_angle_rad": peak(rows, "dancerAngle"),
            "peak_line_tension_n": peak(rows, "lineTension"), "peak_length_imbalance_m": peak(rows, "lineLengthImbalance"),
            "jam_detected": int(maximum(rows, "jamDetected")), "fault_detected": int(maximum(rows, "tensionFault")),
            "safe_pause": int(maximum(rows, "safePause")),
        }
        if name in {"EmptySpool", "HalfSpool", "FullSpool"} and (item["peak_line_tension_n"] > C["line_tension_limit_n"] or item["peak_dancer_angle_rad"] > C["dancer_limit_rad"] or item["fault_detected"]): fail.append("nominal spool dynamics")
        if name in {"SpoolJam", "RealSpoolJam", "SpoolJamPropagation"} and not (item["jam_detected"] and item["safe_pause"] and item["peak_spool_speed_rad_s"] < .02 and item["peak_length_imbalance_m"] < .1 and item["peak_dancer_angle_rad"] > .01): fail.append("real locked-rotor jam propagation")
        if name in {"DancerLimit", "GaugeDropout"} and not item["fault_detected"]: fail.append("spool fault detection")

    elif name in GROUP["full_system"]:
        item |= {"peak_bus_power_w": peak(rows, "busPower"), "safe_state": int(minimum(rows, "safeState")), "feeder_enabled": int(maximum(rows, "feederEnable")), "puller_enabled": int(maximum(rows, "pullerEnable"))}
        if item["peak_bus_power_w"] > C["normal_phase_peak_limit_w"] or not item["safe_state"]: fail.append("full-system power/invariants")
        if name in {"FullSystemGaugeFailure", "FullSystemJam"} and (item["feeder_enabled"] or item["puller_enabled"]): fail.append("fault propagation")

    elif name in GROUP["process_power"]:
        item |= {
            "average_power_w": maximum(rows, "phaseAveragePower"), "peak_power_w": maximum(rows, "phasePeakPower"),
            "psu_current_a": maximum(rows, "psuCurrent"), "remaining_watt_margin": minimum(rows, "remainingWattMargin"),
            "remaining_ampere_margin": minimum(rows, "remainingAmpereMargin"), "overlap_blocked": int(minimum(rows, "overlapBlocked")),
            "power_budget_safe": int(minimum(rows, "powerBudgetSafe")),
        }
        if not item["overlap_blocked"] or not item["power_budget_safe"] or item["peak_power_w"] > C["normal_phase_peak_limit_w"] or item["remaining_watt_margin"] < C["minimum_psu_reserve_w"]: fail.append("phase arbiter/power reserve")

    elif name in GROUP["forming"]:
        settled = [row for row in rows if row["time"] >= 10]
        disturbance = [row for row in rows if row["time"] >= 20]
        item |= {
            "mass_flow_gph": maximum(rows, "effectiveMassFlowGPH"), "line_velocity_m_s": rows[-1]["pullerVelocity"],
            "cooling_residence_s": rows[-1]["coolingResidenceTime"], "puller_entry_mean_c": rows[-1]["meanTemperature"],
            "puller_entry_surface_c": rows[-1]["surfaceTemperature"], "predicted_diameter_mm": rows[-1]["predictedDiameter"],
            "diameter_error_mm": rows[-1]["diameterError"], "max_settled_diameter_error_mm": max(abs(row["diameterError"]) for row in settled),
            "control_margin_m_s": rows[-1]["controlMargin"], "virtual_diameter_pass": int(rows[-1]["virtualDiameterPass"]),
        }
        if name in {"PLAFormingNominal", "PETFormingNominal"} and not item["virtual_diameter_pass"]: fail.append("nominal virtual forming")
        if name in {"DiameterFlowStep", "DiameterPullerDisturbance"} and max(abs(row["diameterError"]) for row in disturbance) > C["diameter_initial_tolerance_mm"]+1e-6: fail.append("diameter disturbance")
        if name in {"PLAFormingHighFlow", "PETFormingHighFlow"}:
            item["classification"] = "DIGITAL_STRETCH_TARGET" if not item["virtual_diameter_pass"] else "VIRTUAL_DIAMETER_CONTROL_PASS"

    item["status"] = "PASS" if not fail else "FAIL"
    return item, fail


def main() -> None:
    names = C["required_scenarios"]
    if len(names) != 55 or len(set(names)) != 55: raise AssertionError("55 unique scenarios required")
    metrics, failures = [], {}
    results = {name: load(name) for name in names}
    for name in names:
        item, reasons = evaluate(name, results[name]); metrics.append(item)
        if reasons: failures[name] = reasons
    shred = [row for row in metrics if row["scenario"] in GROUP["shredder"]]
    envelope = {
        "revision": C["revision"], "source": "OpenModelica DASSL virtual-physics model; empirical validation optional not run",
        "loads": {key: max(float(row[key]) for row in shred) for key in ("peak_cutter_torque_nm", "peak_phase_torque_nm", "peak_bearing_load_n", "peak_chain_force_n")},
        "design_caps": {key: C[key] for key in ("electrical_trip_torque_nm", "mechanical_fuse_cutter_equivalent_nm", "phase_allowable_torque_nm", "shaft_allowable_torque_nm")},
    }
    summary = {
        "revision": C["revision"], "solver": C["solver"], "status": "PASS" if not failures else "FAIL",
        "release_state": "DIGITAL_FABRICATION_BASELINE", "virtual_physics_state": "VIRTUAL_PHYSICS_VALIDATED" if not failures else "VIRTUAL_PHYSICS_FAILED",
        "empirical_state": "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN", "failures": failures,
        "scenario_count": len(metrics), "scenarios": metrics,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    (OUT/"dynamic_load_envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2)+"\n")
    (ROOT/"analysis/load_cases/openmodelica_dynamic_envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2)+"\n")
    fields = sorted({key for row in metrics for key in row})
    with (OUT/"scenario_metrics.csv").open("w", newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(metrics)
    report = [
        "# OpenModelica virtual physics validation v0.5.1", "", f"- 판정: **{summary['status']}**", f"- 시나리오: {len(metrics)}개",
        "- release: `DIGITAL_FABRICATION_BASELINE`", f"- virtual physics: `{summary['virtual_physics_state']}`",
        "- empirical: `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`", "- 본 결과는 실제 제작품 성능·안전·직경 측정 인증이 아니다.", "",
        "|시나리오|판정|분류|", "|---|---:|---|",
    ] + [f"|{row['scenario']}|{row['status']}|{row.get('classification','RELEASE_ACCEPTANCE')}|" for row in metrics]
    (SIM/"reports/mechanical_validation_ko.md").write_text("\n".join(report)+"\n")
    if failures: raise SystemExit("OPENMODELICA_ACCEPTANCE_FAIL "+json.dumps(failures,ensure_ascii=False))
    print(f"OPENMODELICA_ACCEPTANCE_OK scenarios={len(metrics)} virtual=VALIDATED empirical=OPTIONAL_NOT_RUN")


if __name__ == "__main__": main()
