#!/usr/bin/env python3
"""v0.8 hot/LC09 및 권취 동역학 surrogate 검증. 실물/firmware 검증이 아니다."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "simulation/openmodelica/results_v0.8"
RAW = OUT / "raw"
NOMINAL = {
    "SpoolerTraverseEmptyToFull": (9.28, 1240, True),
    "SpoolerPETOneKg": (8.66, 1380, True),
    "SpoolerFullRadiusPLA": (9.28, 1240, False),
    "SpoolerFullRadiusPET": (8.66, 1380, False),
}


def read(name: str) -> list[dict[str, float]]:
    with (RAW / f"{name}_res.csv").open(newline="") as stream:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(stream)]


def parameters(name: str) -> dict[str, float]:
    values = {}
    for variable in ET.parse(RAW / f"{name}_init.xml").iter("ScalarVariable"):
        real = variable.find("Real")
        if real is not None and "start" in real.attrib:
            values[variable.attrib["name"]] = float(real.attrib["start"])
    return values


def dynamics(rows: list[dict[str, float]], speed: float, density: float, one_kg: bool) -> dict:
    directions, pitches = [], []
    for before, after in zip(rows, rows[1:]):
        delta = after["traversePositionMm"] - before["traversePositionMm"]
        turns = after["spoolTurns"] - before["spoolTurns"]
        if abs(delta) > 1e-7:
            directions.append((1 if delta > 0 else -1, before))
        if turns > 1e-7 and math.floor(before["spoolTurns"] * 1.85 / 68) == math.floor(after["spoolTurns"] * 1.85 / 68):
            pitches.append(abs(delta / turns))
    edges = [b[1] for a, b in zip(directions, directions[1:]) if a[0] != b[0]]
    settled = [r for r in rows if r["time"] >= 20]
    area = math.pi * (1.75e-3 / 2) ** 2
    volume_error = max(abs(math.pi * ((r["radiusMm"] / 1000) ** 2 - .026 ** 2) * .068 * .87
                           - area * r["plant.woundLength"]) for r in rows) if one_kg else None
    checks = {
        "finite_samples_and_complete_time": len(rows) > 1000 and all(math.isfinite(v) for r in rows for v in r.values()) and
            (34000 < rows[-1]["time"] < 38000 if one_kg else abs(rows[-1]["time"] - 12000) < 1e-7),
        "current_nominal_line_speed": all(abs(r["plant.commandedLineSpeed"] * 1000 - speed) < 1e-9 for r in rows),
        "no_nominal_fault_or_pause": all(r["faultLatched"] == 0 and r["safePause"] == 0 for r in rows),
        "radius_envelope": all(26 - 1e-7 <= r["radiusMm"] <= 100 + 1e-7 for r in rows),
        "settled_rpm_tracks_radius": bool(settled) and max(abs(r["actualRpm"] - r["targetRpm"]) for r in settled) < .02,
        "rpm_kinematics": all(abs(r["targetRpm"] - speed * 60 / (2 * math.pi * r["radiusMm"])) < 1e-8 for r in rows),
        "dancer_below_controlled_stop": max(abs(r["dancerAngleRad"]) for r in rows) < .36,
        "positive_hard_stop_margin": min(r["hardStopMarginRad"] for r in rows) > 0,
        "line_tension_below_8_n": max(r["plant.lineTension"] for r in rows) < 8,
        "traverse_width": all(-1e-6 <= r["traversePositionMm"] <= 68 + 1e-6 for r in rows),
        "at_least_two_real_edge_reversals": len(edges) >= 2 and all(min(abs(r["traversePositionMm"]), abs(r["traversePositionMm"] - 68)) < .01 for r in edges),
        "measured_pitch_1p85_mm_per_actual_turn": len(pitches) > 100 and max(abs(p - 1.85) for p in pitches) < 1e-5,
    }
    if one_kg:
        checks.update({
            "radius_from_accumulated_material_volume": volume_error < 1e-10,
            "empty_core_to_one_kg": abs(rows[0]["radiusMm"] - 26) < 1e-9 and abs(rows[-1]["addedMassKg"] - 1) < 1e-5 and rows[-1]["batchComplete"] == 1,
            "density_mass_balance": all(abs(r["addedMassKg"] - density * area * r["plant.woundLength"]) < 1e-8 for r in rows),
            "unidirectional_fill_domain": min(r["actualRpm"] for r in rows) >= -1e-7,
        })
    else:
        checks["full_radius_fixed_boundary"] = all(abs(r["radiusMm"] - 100) < 1e-9 for r in rows)
    return {
        "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL",
        "samples": len(rows), "duration_s": rows[-1]["time"],
        "line_speed_mm_s": speed, "assumed_density_kg_m3": density,
        "nominal_mass_flow_g_h": speed / 1000 * area * density * 3600 * 1000,
        "initial_radius_mm": rows[0]["radiusMm"], "final_radius_mm": rows[-1]["radiusMm"],
        "added_mass_kg": rows[-1]["addedMassKg"],
        "volume_residual_max_m3": volume_error,
        "volume_scope": "MATERIAL_CONSERVING_ONE_KG_FILL" if one_kg else "FIXED_100_MM_RADIUS_AND_FULL_INERTIA_BOUNDARY_NOT_CAPACITY_SIMULATION",
        "peak_dancer_angle_rad": max(abs(r["dancerAngleRad"]) for r in rows),
        "minimum_hard_stop_margin_rad": min(r["hardStopMarginRad"] for r in rows),
        "peak_tension_n": max(r["plant.lineTension"] for r in rows),
        "maximum_settled_rpm_error": max(abs(r["actualRpm"] - r["targetRpm"]) for r in settled),
        "actual_spool_turns": rows[-1]["spoolTurns"],
        "traverse_pitch_min_mm_per_turn": min(pitches) if pitches else None,
        "traverse_pitch_max_mm_per_turn": max(pitches) if pitches else None,
        "edge_reversals": len(edges),
        "edge_events": [{"time_s": r["time"], "position_mm": r["traversePositionMm"]} for r in edges],
    }


def jam_checks(rows: list[dict[str, float]], maximum_latency: float) -> dict[str, bool]:
    trip = next((i for i, r in enumerate(rows) if r["faultLatched"] == 1), None)
    eligible = next((r["time"] for r in rows if r["jamEligible"] == 1), None)
    return {
        "twenty_second_trace_complete": abs(rows[-1]["time"] - 20) < 1e-7,
        "locked_spindle_observed": any(r["plant.jamDetected"] == 1 for r in rows),
        "latched_pause_no_automatic_restart": trip is not None and all(r["safePause"] == 1 and r["faultLatched"] == 1 for r in rows[trip:]),
        "zero_motor_torque_and_feed_after_trip": trip is not None and all(abs(r["spoolCommandNm"]) < 1e-9 and r["plant.effectiveLineSpeed"] == 0 for r in rows[trip:]),
        "response_after_observation_within_contract": trip is not None and eligible is not None and 0 <= rows[trip]["time"] - eligible <= maximum_latency,
        "no_dancer_hard_stop_contact": min(r["hardStopMarginRad"] for r in rows) > 0 and max(r["plant.hardStopReactionTorque"] for r in rows) == 0,
    }


def main() -> None:
    hot, spool, jam = read("HotZoneControlledExpansion"), read("LC09SpoolScope"), read("SpoolerJamContainment")
    series = {name: read(name) for name in NOMINAL}
    scenarios = {name: dynamics(series[name], *settings) for name, settings in NOMINAL.items()}
    source_hashes = dict(line.rstrip().split("  ", 1)[::-1] for line in (OUT / "source_sha256.txt").read_text().splitlines())
    source_current = len(source_hashes) == 13 and all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha for path, sha in source_hashes.items())
    firmware = (ROOT / "firmware/arduino_mega/src/machine_supervisor.cpp").read_text()
    header = (ROOT / "firmware/arduino_mega/src/spooler_control.h").read_text()
    drive = json.loads((ROOT / "control/drive_actuation_contract_v0.6.2.1.json").read_text())["drives"]["spooler"]
    fault = json.loads((ROOT / "control/fault_response_contract.json").read_text())
    generated = (ROOT / "simulation/openmodelica/PLA_PET_Recycler/Generated.mo").read_text()
    generated_control = (ROOT / "simulation/openmodelica/PLA_PET_Recycler/GeneratedControl.mo").read_text()
    binding = {
        "all_simulation_source_hashes_current": source_current,
        "fresh_outputs_from_this_run": all((RAW / f"{name}_{suffix}").stat().st_mtime_ns >= (OUT / "source_sha256.txt").stat().st_mtime_ns
            for name in [*NOMINAL, "SpoolerJamContainment", "HotZoneControlledExpansion", "LC09SpoolScope"] for suffix in ["res.csv", "init.xml"]),
        "current_spool_drive_contract": drive["normal_line_speed_mm_s"] == [8.66, 9.28] and drive["radius_range_mm"] == [26, 100],
        "current_firmware_geometry": all(re.search(rf"spooler\.{field}\s*=\s*{value}f", firmware) for field, value in
            [("core_radius_mm", "26.0"), ("full_radius_mm", "100.0"), ("spool_width_mm", "68.0"), ("filament_diameter_mm", "1.75")]) and
            "{68.0f, 1.85f, 80.0f, 1200}" in firmware and "packing_factor{0.87f}" in header,
        "generated_CAD_matches_current_baseline": source_hashes["cad/parameters/baseline.json"] in generated,
        "generated_control_matches_current_contracts": all(source_hashes[f"control/{name}.json"] in generated_control for name in ("process_contract", "fault_response_contract")),
        "current_dancer_thresholds": all(f"{name}={value};" in generated_control for name, value in [("dancerControlledStop", "0.36"), ("dancerHardStop", "0.4363")]),
    }
    for name, (speed, density, one_kg) in NOMINAL.items():
        params = parameters(name)
        binding[f"{name}_compiled_parameters"] = all(abs(params[key] - expected) < 1e-9 for key, expected in {
            "coreRadiusMm": 26, "fullRadiusMm": 100, "windingWidthMm": 68, "packingFactor": .87,
            "filamentDiameterMm": 1.75, "traversePitchMm": 1.85, "lineSpeedMmS": speed,
            "densityKgM3": density, "initialFill": 0 if one_kg else 1,
        }.items())
    jam_result = jam_checks(jam, fault["timing"]["maximum_response_latency_s"])
    # Negative controls reject linear-time radius, frozen traverse, substituted
    # nominal speed, and a jam pause that unlatches without an explicit reset.
    corrupt_radius = [dict(row, radiusMm=26 + 74 * row["time"] / series["SpoolerTraverseEmptyToFull"][-1]["time"]) for row in series["SpoolerTraverseEmptyToFull"]]
    frozen = [dict(row, traversePositionMm=0) for row in series["SpoolerFullRadiusPLA"]]
    unlatch = [dict(row) for row in jam]
    unlatch[-1]["safePause"] = 0
    wrong_speed = [dict(row, **{"plant.commandedLineSpeed": .035}) for row in series["SpoolerFullRadiusPLA"]]
    negative_controls = {
        "linear_time_radius_rejected": not dynamics(corrupt_radius, 9.28, 1240, True)["checks"]["radius_from_accumulated_material_volume"],
        "frozen_traverse_rejected": not dynamics(frozen, 9.28, 1240, False)["checks"]["at_least_two_real_edge_reversals"],
        "35_mm_s_nominal_substitution_rejected": not dynamics(wrong_speed, 9.28, 1240, False)["checks"]["current_nominal_line_speed"],
        "jam_pause_unlatch_rejected": not jam_checks(unlatch, .25)["latched_pause_no_automatic_restart"],
    }
    checks = {
        "hot_zone_travel_margin_nonnegative": hot[-1]["travelMarginMm"] >= 0,
        "hot_zone_regional_sf_ge_2": hot[-1]["safetyFactor"] >= 2,
        "lc09_scope_contract": spool[-1]["scopePass"] == 1,
        "lc09_force_balance": abs(spool[-1]["forceResidualN"]) < 1e-8,
        "lc09_moment_balance": abs(spool[-1]["momentResidualNmm"]) < 1e-8,
        "source_parameter_binding": all(binding.values()),
        "spooler_dynamic_scenarios": all(s["status"] == "PASS" for s in scenarios.values()),
        "jam_containment": all(jam_result.values()),
        "validator_negative_controls": all(negative_controls.values()),
    }
    result = {
        "revision": "final-design-fabrication-closure-v0.8",
        "solver": (OUT / "solver_version.txt").read_text().strip() + " DASSL",
        "validation_scope": "PARAMETER_BOUND_MECHANICAL_AND_CONTROL_SURROGATE_NOT_FIRMWARE_OR_PHYSICAL_VALIDATION",
        "model_sha256": source_hashes["simulation/openmodelica/v0.8/V08ReleaseScenarios.mo"],
        "source_sha256": source_hashes,
        "raw_csv_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(RAW.glob("*_res.csv"))},
        "parameter_binding": binding,
        "hot_zone": {
            "scope": "UNIFORM_TEMPERATURE_FIRST_ORDER_EXPANSION_SCREEN_WITH_INHERITED_83_5_MPA_STRESS_NOT_CURRENT_CALCULIX_RESULT",
            "release_state": "HOLD",
            "hold_reasons": ["E/alpha material-source mismatch", "3D notch not verified", "die-joint not verified", "temperature gradient not verified"],
            **{key: hot[-1][key] for key in ("temperatureC", "axialGrowthMm", "travelMarginMm", "safetyFactor", "pass")}},
        "LC09": {"spindle_length_mm": 143, "bearing_spacing_mm": 88, "load_position_from_front_mm": 40.5,
            "spool_mass_kg": 1.35, "line_tension_n": 8,
            **{key: spool[-1][key] for key in ("radialLoadN", "frontReactionN", "rearReactionN", "forceResidualN", "momentResidualNmm", "scopePass")}},
        "spooler_traverse_dynamics": scenarios,
        "jam": {"fault": "LOCKED_SPINDLE_AT_STARTUP", "observation_grace_s": parameters("SpoolerJamContainment")["jamObservationGraceS"],
            "trip_time_s": next((r["time"] for r in jam if r["faultLatched"] == 1), None),
            "minimum_hard_stop_margin_rad": min(r["hardStopMarginRad"] for r in jam), "checks": jam_result},
        "negative_controls": negative_controls, "checks": checks,
        "limitations": [
            "Hot-zone는 균일 온도 1차 응답과 기존 83.5 MPa 입력의 screening이다. 현재 CalculiX 교차검증·hot release PASS가 아니며 E/alpha 출처 불일치·3D notch·die-joint·온도구배 미검증으로 hot release HOLD를 유지한다.",
            "DynamicSpoolSystem의 토크/관성/마찰/탄성/제어 gain은 기존 surrogate 가정이다. 실제 donor 전달함수·장력·dancer calibration은 NOT_RUN.",
            "1 kg 시나리오는 체적 적분으로 1 kg 도달 시 solver를 종료한다. 실제 정지·역권취·체적 감소는 검증하지 않는다.",
            "100 mm full-radius 시나리오는 고정 반경·full inertia 경계조건이다. 1 kg 배치 반경이나 추가 재료 체적 보존을 주장하지 않는다.",
            "Traverse는 실제 spool angle에 연결한 pitch/reversal kinematic surrogate이며 step loss, belt compliance, homing/endstop, firmware 실행 증거가 아니다.",
            "Jam은 시작부터 잠긴 spindle과 관측유예 후 latch의 surrogate이다. 운전 중 jam 충격·tach timeout·firmware dwell·하드웨어 안전회로 검증이 아니다.",
            "E-stop/interlock/fuse 안전기능은 firmware와 독립적이어야 한다. 수령검사·가공·배선·통전·물리 시험·구매 승인은 NOT_RUN.",
        ],
        "physical_validation_state": "NOT_RUN", "firmware_execution_state": "NOT_RUN_IN_THIS_SURROGATE",
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["status"] != "PASS":
        raise SystemExit("V08_OPENMODELICA_VALIDATION_FAIL: inspect summary.json; criteria were not relaxed")
    print(f"V08_OPENMODELICA_VALIDATION_OK scenarios={len(scenarios)} jam_latched=1 negative_controls=4 physical=NOT_RUN")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, TypeError, ET.ParseError) as error:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "summary.json").write_text(json.dumps({"status": "FAIL", "error": str(error), "physical_validation_state": "NOT_RUN"}, ensure_ascii=False, indent=2) + "\n")
        raise SystemExit(f"V08_OPENMODELICA_INPUT_FAIL: {error}") from error
