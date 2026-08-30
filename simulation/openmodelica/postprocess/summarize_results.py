#!/usr/bin/env python3
"""v0.5 coupled OpenModelica CSV 32종을 판정하고 하중 envelope를 고정한다."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SIM = ROOT / "simulation" / "openmodelica"
RAW = SIM / "results" / "raw"
OUT = SIM / "results"
CRITERIA = json.loads((SIM / "acceptance_criteria.json").read_text())


def number(value: str | None) -> float:
    if value is None or value == "":
        raise ValueError("empty CSV value")
    return {"true": 1.0, "false": 0.0, "True": 1.0, "False": 0.0}.get(value, float(value))


def load(name: str) -> list[dict[str, float]]:
    path = RAW / f"{name}_res.csv"
    if not path.exists():
        raise AssertionError(f"누락된 결과: {path}")
    with path.open(newline="") as stream:
        rows = [{key: number(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    if not rows or any(not math.isfinite(v) for row in rows for v in row.values()):
        raise AssertionError(f"비정상 결과: {name}")
    return rows


def peak(rows, key):
    return max(abs(row[key]) for row in rows)


def maximum(rows, key):
    return max(row[key] for row in rows)


def minimum(rows, key):
    return min(row[key] for row in rows)


def max_temperature(rows, prefix=""):
    return max(maximum(rows, prefix + key) for key in ("T1", "T2", "T3", "Tdie"))


SHREDDER = set(CRITERIA["required_scenarios"][:13])
THERMAL = set(CRITERIA["required_scenarios"][13:22])
SPOOL = set(CRITERIA["required_scenarios"][22:28])


def evaluate(name: str, rows: list[dict[str, float]]) -> tuple[dict, list[str]]:
    fail: list[str] = []
    item: dict[str, float | int | str] = {"scenario": name, "samples": len(rows)}
    if name in SHREDDER:
        item.update(
            peak_cutter_torque_nm=peak(rows, "estimatedCutterTorque"),
            peak_phase_torque_nm=peak(rows, "phase.meshTorque"),
            peak_phase_error_rad=peak(rows, "phase.phaseError"),
            peak_bearing_load_n=peak(rows, "bearingLoad"),
            peak_chain_force_n=peak(rows, "chain.tightSideForce"),
            peak_motor_current_a=peak(rows, "motor.current"),
            peak_cutter_rpm=peak(rows, "cutterRPM"),
            min_duty=minimum(rows, "dutyCommand"),
            jam_detected=int(maximum(rows, "jamDetected")),
            jam_fault=int(maximum(rows, "jamFault")),
            fuse_broken=int(maximum(rows, "inputFuse.broken")),
        )
        if item["peak_phase_error_rad"] > CRITERIA["phase_error_limit_rad"]:
            fail.append("phase error limit")
        if item["peak_cutter_torque_nm"] > CRITERIA["mechanical_fuse_cutter_equivalent_nm"] + 0.05:
            fail.append("22 N.m protection hierarchy")
        if item["peak_cutter_rpm"] > CRITERIA["overspeed_hard_limit_rpm"]:
            fail.append("80 rpm overspeed hard limit")
        if item["peak_motor_current_a"] > CRITERIA["stall_motor_current_a"]:
            fail.append("31 A reference stall current")
        if name in {"PLANominal", "PETNominal"}:
            if item["peak_cutter_torque_nm"] > CRITERIA["normal_continuous_torque_nm"]:
                fail.append("14 N.m nominal torque")
            if item["jam_fault"] or item["fuse_broken"]:
                fail.append("nominal false trip")
        if name == "MotorNoLoadStart" and (item["peak_motor_current_a"] > CRITERIA["rated_motor_current_a"] or item["fuse_broken"]):
            fail.append("no-load start current/fuse")
        if name in {"OneShaftJam", "FullJam", "RetryFailure", "ChainBacklashReverse"}:
            if not (item["jam_detected"] and item["jam_fault"] and item["min_duty"] < 0):
                fail.append("bounded reverse and latched fault")
        if name == "ReverseClear" and not (item["jam_detected"] and not item["jam_fault"] and not item["fuse_broken"] and item["min_duty"] < 0):
            fail.append("reverse-clear recovery")
        if name == "MechanicalFuseTrip" and not item["fuse_broken"]:
            fail.append("mechanical fuse event")
        if name == "EmergencyStop":
            after = [row for row in rows if row["time"] >= 2.05]
            if not after or max(abs(row["dutyCommand"]) for row in after) > 1e-6 or max(row["motor.enable"] for row in after) > 0:
                fail.append("E-stop output removal")

    elif name in THERMAL:
        item.update(
            max_temperature_c=max_temperature(rows),
            peak_process_heater_w=max(row["power1"] + row["power2"] + row["power3"] + row["powerDie"] for row in rows),
            peak_net_flow_gph=peak(rows, "netFlowGPH"),
            ready=int(maximum(rows, "ready")),
            fuse_blown=int(maximum(rows, "fuseBlown")),
        )
        if item["peak_process_heater_w"] > CRITERIA["process_heater_limit_w"] + 1e-6:
            fail.append("360 W heater budget")
        if name in {"ExtruderWarmupPLA", "ExtruderWarmupPET", "ExtruderNominalPLA", "ExtruderNominalPET", "ExtruderHighFlow"} and not item["ready"]:
            fail.append("thermal ready not reached")
        if name in {"ExtruderNominalPLA", "ExtruderNominalPET"} and item["peak_net_flow_gph"] <= 0:
            fail.append("nominal net flow")
        if name == "ExtruderHighFlow" and item["peak_net_flow_gph"] < 200:
            fail.append("200 g/h digital stretch")
        if name == "HeaterOpen" and (maximum(rows, "power2") != 0 or item["ready"]):
            fail.append("heater-open detection")
        if name == "SensorOpen" and item["peak_process_heater_w"] != 0:
            fail.append("sensor-open heater inhibit")
        if name == "MOSFETStuckOn" and item["max_temperature_c"] >= 300 and not item["fuse_blown"]:
            fail.append("stuck-on without thermal fuse")

    elif name in SPOOL:
        item.update(
            peak_line_tension_n=peak(rows, "lineTension"),
            peak_dancer_angle_rad=peak(rows, "dancerAngle"),
            peak_spool_motor_torque_nm=peak(rows, "motorTorque"),
            tension_fault=int(maximum(rows, "tensionFault")),
        )
        if name in {"EmptySpool", "HalfSpool", "FullSpool"}:
            if item["peak_line_tension_n"] > CRITERIA["line_tension_limit_n"] or item["peak_dancer_angle_rad"] > CRITERIA["dancer_limit_rad"]:
                fail.append("nominal spool tension/dancer")
        if name in {"SpoolJam", "GaugeDropout"} and item["peak_spool_motor_torque_nm"] > 1e-9:
            fail.append("spool/gauge fault torque inhibit")
        if name == "DancerLimit" and not item["tension_fault"]:
            fail.append("dancer limit fault")

    else:
        item.update(
            peak_bus_power_w=peak(rows, "busPower"),
            safe_state=int(minimum(rows, "safeState")),
            feeder_enabled=int(maximum(rows, "feederEnable")),
            puller_enabled=int(maximum(rows, "pullerEnable")),
        )
        if item["peak_bus_power_w"] > CRITERIA["psu_limit_w"] or not item["safe_state"]:
            fail.append("600 W bus/safe-state")
        if name in {"FullSystemGaugeFailure", "FullSystemJam"} and (item["feeder_enabled"] or item["puller_enabled"]):
            fail.append("coupled fault propagation")

    item["status"] = "PASS" if not fail else "FAIL"
    return item, fail


def main() -> None:
    names = CRITERIA["required_scenarios"]
    if len(names) != 32 or len(set(names)) != 32:
        raise AssertionError("required_scenarios must contain exactly 32 unique names")
    results = {name: load(name) for name in names}
    evaluated = [evaluate(name, results[name]) for name in names]
    metrics = [row for row, _ in evaluated]
    failures = {row["scenario"]: reasons for row, reasons in evaluated if reasons}
    shred = [row for row in metrics if row["scenario"] in SHREDDER]
    envelope = {
        "revision": CRITERIA["revision"],
        "source": "OpenModelica DASSL coupled surrogate; PHYSICAL_VALIDATION_PENDING",
        "loads": {
            key: max(float(row[key]) for row in shred)
            for key in ("peak_cutter_torque_nm", "peak_phase_torque_nm", "peak_bearing_load_n", "peak_chain_force_n")
        },
        "design_caps": {
            "electrical_trip_torque_nm": CRITERIA["electrical_trip_torque_nm"],
            "mechanical_fuse_cutter_equivalent_nm": CRITERIA["mechanical_fuse_cutter_equivalent_nm"],
            "phase_allowable_torque_nm": CRITERIA["phase_allowable_torque_nm"],
            "shaft_allowable_torque_nm": CRITERIA["shaft_allowable_torque_nm"],
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps({
        "revision": CRITERIA["revision"], "solver": CRITERIA["solver"],
        "physical_state": "PHYSICAL_VALIDATION_PENDING",
        "status": "PASS" if not failures else "FAIL", "failures": failures,
        "scenario_count": len(metrics), "scenarios": metrics,
    }, ensure_ascii=False, indent=2) + "\n")
    (OUT / "dynamic_load_envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n")
    (ROOT / "analysis" / "load_cases" / "openmodelica_dynamic_envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n")
    fields = sorted({key for row in metrics for key in row})
    with (OUT / "scenario_metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(metrics)
    report = [
        "# OpenModelica coupled digital validation v0.5", "",
        f"- 판정: **{'PASS' if not failures else 'FAIL'}**", f"- 시나리오: {len(metrics)}개",
        "- 상태: `PHYSICAL_VALIDATION_PENDING`; cutter torque/chip size/melt/filament 품질의 실증이 아니다.", "",
        "|시나리오|판정|", "|---|---:|",
    ] + [f"|{row['scenario']}|{row['status']}|" for row in metrics]
    (SIM / "reports" / "mechanical_validation_ko.md").write_text("\n".join(report) + "\n")
    if failures:
        raise SystemExit("OPENMODELICA_ACCEPTANCE_FAIL " + json.dumps(failures, ensure_ascii=False))
    print(f"OPENMODELICA_ACCEPTANCE_OK scenarios={len(metrics)} physical=NOT_RUN")


if __name__ == "__main__":
    main()
