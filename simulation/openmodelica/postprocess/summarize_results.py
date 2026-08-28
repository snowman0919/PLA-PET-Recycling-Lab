#!/usr/bin/env python3
"""OpenModelica CSV를 판정하고 구조해석용 동적 하중 envelope를 생성한다."""

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


def number(value: str) -> float:
    table = {"true": 1.0, "false": 0.0, "True": 1.0, "False": 0.0}
    return table[value] if value in table else float(value)


def load(name: str) -> list[dict[str, float]]:
    path = RAW / f"{name}_res.csv"
    if not path.exists():
        raise AssertionError(f"누락된 시뮬레이션 결과: {path}")
    with path.open(newline="") as stream:
        rows = [{key: number(value) for key, value in row.items()} for row in csv.DictReader(stream)]
    if not rows or any(not math.isfinite(value) for row in rows for value in row.values()):
        raise AssertionError(f"비정상 또는 비어 있는 결과: {name}")
    return rows


def peak(rows: list[dict[str, float]], key: str, *, after: float = -1) -> float:
    selected = [abs(row[key]) for row in rows if row["time"] >= after]
    return max(selected) if selected else 0.0


def maximum(rows: list[dict[str, float]], key: str) -> float:
    return max(row[key] for row in rows)


def final(rows: list[dict[str, float]], key: str) -> float:
    return rows[-1][key]


def evaluate(name: str, rows: list[dict[str, float]]) -> tuple[dict, list[str]]:
    failures: list[str] = []
    metrics: dict[str, float | str] = {"scenario": name, "samples": len(rows)}
    shredder = "cutterTorque" in rows[0]
    extruder = "throughputGPH" in rows[0]
    forming = "lineTension" in rows[0]

    if shredder:
        metrics.update(
            peak_cutter_torque_nm=peak(rows, "cutterTorque"),
            peak_requested_torque_nm=peak(rows, "requestedTorque"),
            peak_transmitted_torque_nm=peak(rows, "transmittedTorque"),
            peak_phase_torque_nm=peak(rows, "phaseTorque"),
            peak_phase_error_rad=peak(rows, "phaseError"),
            peak_bearing_load_n=peak(rows, "bearingLoad"),
            peak_chain_force_n=peak(rows, "chainForce"),
            peak_frame_reaction_n=peak(rows, "frameReaction"),
            peak_speed_rad_s=max(peak(rows, "rightRotor.speed"), peak(rows, "leftRotor.speed")),
            peak_current_a=peak(rows, "drive.current"),
            retry_count=int(maximum(rows, "retryCount")),
            fault_latched=int(maximum(rows, "faultLatched")),
            fuse_operated=int(maximum(rows, "fuseOperating")),
        )
        if metrics["peak_transmitted_torque_nm"] > CRITERIA["input_fuse_torque_nm"] + 1e-6:
            failures.append("입력 토크 퓨즈 한계 초과")
        if metrics["peak_phase_torque_nm"] > CRITERIA["phase_allowable_torque_nm"]:
            failures.append("phase drivetrain 허용토크 초과")
        if metrics["peak_phase_error_rad"] > CRITERIA["phase_error_limit_rad"]:
            failures.append("cutter 위상오차 한계 초과")
        if metrics["peak_speed_rad_s"] > CRITERIA["unbounded_speed_limit_rad_s"]:
            failures.append("비정상 속도 발산")
        if name in {"PLANominal", "PETNominal"} and metrics["peak_cutter_torque_nm"] > CRITERIA["normal_continuous_torque_nm"]:
            failures.append("정상운전 연속토크 한계 초과")
        if name in {"JamReverseRetry", "OneShaftJam", "MotorStall"}:
            if metrics["retry_count"] != CRITERIA["max_reverse_retries"] or metrics["fault_latched"] != 1:
                failures.append("bounded retry 후 latched fault가 아님")
        if name == "InputFuseOperation" and metrics["fuse_operated"] != 1:
            failures.append("입력 토크 퓨즈 작동 미검출")
        if name == "EmergencyStop" and peak(rows, "cutterTorque", after=2.1) > 0.1:
            failures.append("E-stop 후 구동토크 잔류")

    if extruder:
        metrics.update(
            peak_screw_load_torque_nm=peak(rows, "load.torque"),
            peak_screw_drive_torque_nm=peak(rows, "drive.motorTorque"),
            peak_pressure_pa=peak(rows, "load.pressure"),
            final_throughput_gph=final(rows, "throughputGPH"),
            peak_throughput_gph=peak(rows, "throughputGPH"),
            torque_trip=int(maximum(rows, "torqueTrip")),
        )
        if name == "ScrewPressureRamp" and metrics["torque_trip"]:
            failures.append("정상 압력 ramp에서 torque trip")
        if name == "ScrewJam" and not (metrics["torque_trip"] and metrics["peak_screw_load_torque_nm"] >= CRITERIA["input_fuse_torque_nm"]):
            failures.append("screw jam torque trip 미검출")

    if forming:
        metrics.update(
            peak_line_tension_n=peak(rows, "lineTension"),
            peak_dancer_angle_rad=peak(rows, "dancerAngle"),
            final_spool_radius_m=final(rows, "spoolRadius"),
            controlled_pause=int(maximum(rows, "controlledPause")),
        )
        if metrics["peak_line_tension_n"] > CRITERIA["line_tension_limit_n"]:
            failures.append("filament line tension 한계 초과")
        if name == "GaugeDropout" and metrics["controlled_pause"] != 1:
            failures.append("gauge dropout controlled pause 미검출")

    metrics["status"] = "PASS" if not failures else "FAIL"
    return metrics, failures


def main() -> None:
    scenario_rows = {name: load(name) for name in CRITERIA["required_scenarios"]}
    evaluated = [evaluate(name, rows) for name, rows in scenario_rows.items()]
    metrics = [item[0] for item in evaluated]
    failures = {m["scenario"]: reasons for m, reasons in evaluated if reasons}
    sweep_names = ["SweepEfficiencyLow", "SweepTorqueConstantLow", "SweepFrictionHigh", "SweepLoadHigh", "SweepInertiaLow", "SweepBacklashHigh"]
    sweep_metrics = []
    for name in sweep_names:
        rows = load(name)
        item = {
            "sweep": name,
            "peak_cutter_torque_nm": peak(rows, "cutterTorque"),
            "peak_phase_error_rad": peak(rows, "phaseError"),
            "peak_speed_rad_s": max(peak(rows, "rightRotor.speed"), peak(rows, "leftRotor.speed")),
            "peak_current_a": peak(rows, "drive.current"),
        }
        item["status"] = "PASS" if item["peak_phase_error_rad"] <= CRITERIA["phase_error_limit_rad"] and item["peak_speed_rad_s"] <= CRITERIA["unbounded_speed_limit_rad_s"] else "FAIL"
        if item["status"] != "PASS":
            failures[name] = ["sensitivity sweep acceptance 초과"]
        sweep_metrics.append(item)

    full_rows = scenario_rows["FullMechanicalNominal"]
    full_anchor = peak(full_rows, "anchorTension")
    full_base = peak(full_rows, "baseReaction")
    full_tip = peak(full_rows, "tippingMoment")
    if full_anchor > CRITERIA["anchor_tension_limit_n"]:
        failures["FullMechanicalNominal"] = ["M8 table anchor 요구하중 한계 초과"]
        next(m for m in metrics if m["scenario"] == "FullMechanicalNominal")["status"] = "FAIL"

    shredder_metrics = [m for m in metrics if "peak_cutter_torque_nm" in m]
    envelope = {
        "revision": CRITERIA["revision"],
        "source": "OpenModelica DASSL scenario maximum; PHYSICAL_NOT_RUN",
        "governing_scenarios": {
            field: max(shredder_metrics, key=lambda m: m[field])["scenario"]
            for field in ["peak_cutter_torque_nm", "peak_phase_torque_nm", "peak_bearing_load_n", "peak_chain_force_n", "peak_frame_reaction_n"]
        },
        "loads": {
            field: max(float(m[field]) for m in shredder_metrics)
            for field in ["peak_cutter_torque_nm", "peak_phase_torque_nm", "peak_bearing_load_n", "peak_chain_force_n", "peak_frame_reaction_n"]
        },
        "full_system": {
            "peak_base_reaction_n": full_base,
            "peak_tipping_moment_nm": full_tip,
            "peak_anchor_tension_n": full_anchor,
            "anchor_tension_limit_n": CRITERIA["anchor_tension_limit_n"],
        },
        "design_caps": {
            "input_fuse_torque_nm": CRITERIA["input_fuse_torque_nm"],
            "phase_allowable_torque_nm": CRITERIA["phase_allowable_torque_nm"],
            "shaft_allowable_torque_nm": CRITERIA["shaft_allowable_torque_nm"],
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps({
        "revision": CRITERIA["revision"],
        "solver": CRITERIA["solver"],
        "physical_state": "PHYSICAL_NOT_RUN",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "scenarios": metrics,
        "sensitivity_sweeps": sweep_metrics,
    }, indent=2) + "\n")
    (OUT / "dynamic_load_envelope.json").write_text(json.dumps(envelope, indent=2) + "\n")
    analysis_copy = ROOT / "analysis" / "load_cases" / "openmodelica_dynamic_envelope.json"
    analysis_copy.write_text(json.dumps(envelope, indent=2) + "\n")

    fields = sorted({key for row in metrics for key in row})
    with (OUT / "scenario_metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(metrics)
    with (OUT / "sensitivity_metrics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sweep_metrics[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sweep_metrics)

    report = [
        "# OpenModelica 기계 검증 결과",
        "",
        f"- revision: `{CRITERIA['revision']}`",
        f"- 판정: **{'PASS' if not failures else 'FAIL'}**",
        "- 상태: `PHYSICAL_NOT_RUN` — 이 결과는 물리 성능이나 안전 인증을 대체하지 않는다.",
        f"- 시나리오: {len(metrics)}개 + sensitivity sweep {len(sweep_metrics)}개, solver `{CRITERIA['solver']}`, tolerance `{CRITERIA['tolerance']}`",
        "",
        "## 하중 envelope",
        "",
        f"- cutter 전달토크: {envelope['loads']['peak_cutter_torque_nm']:.2f} N·m",
        f"- phase gear 토크: {envelope['loads']['peak_phase_torque_nm']:.2f} N·m",
        f"- bearing 합성하중: {envelope['loads']['peak_bearing_load_n']:.0f} N",
        f"- chain 장력: {envelope['loads']['peak_chain_force_n']:.0f} N",
        f"- table anchor 최대 인장: {full_anchor:.0f} N / {CRITERIA['anchor_tension_limit_n']:.0f} N",
        "",
        "## 시나리오 판정",
        "",
        "|시나리오|판정|핵심 결과|",
        "|---|---:|---|",
    ]
    for item in metrics:
        key = []
        if "peak_cutter_torque_nm" in item:
            key.append(f"T={item['peak_cutter_torque_nm']:.2f} N·m")
            key.append(f"phase={item['peak_phase_error_rad']:.4f} rad")
        if "peak_screw_load_torque_nm" in item:
            key.append(f"screw={item['peak_screw_load_torque_nm']:.2f} N·m")
        if "peak_line_tension_n" in item:
            key.append(f"line={item['peak_line_tension_n']:.2f} N")
        report.append(f"|{item['scenario']}|{item['status']}|{', '.join(key)}|")
    report += [
        "",
        "## 해석 경계",
        "",
        "Cutter load는 Gate-1 실측 전 surrogate이다. 14/18/22/34/48 N·m는 모두 cutter-shaft equivalent다. 물리 DRV-F01은 motor-side에 두며 22 N·m cutter-equivalent가 되도록 선택 ratio와 효율로 환산한다. Cutter-side DRV-02는 sacrificial element가 아니다. 이 보호 순서는 디지털 모델에서만 검증했다. M8 table anchor 체결은 운전 전 필수이며, 실제 토크·충격·입도·jam은 Gate-1에서 검증한다.",
        "",
    ]
    (SIM / "reports" / "mechanical_validation_ko.md").write_text("\n".join(report))

    if failures:
        raise SystemExit(f"OPENMODELICA_ACCEPTANCE_FAIL {json.dumps(failures, ensure_ascii=False)}")
    print(f"OPENMODELICA_ACCEPTANCE_OK scenarios={len(metrics)} sweeps={len(sweep_metrics)} anchor_N={full_anchor:.1f}")


if __name__ == "__main__":
    main()
