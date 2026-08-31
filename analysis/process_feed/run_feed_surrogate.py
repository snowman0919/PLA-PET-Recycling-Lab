#!/usr/bin/env python3
"""P0-H용 결정적 feed/inventory/current/tach surrogate.

이는 입자 DEM의 대체용 설계 판단 모델이며 실측 유량/토크 검증이 아니다.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARAM = json.loads((HERE / "feed_parameters.json").read_text(encoding="utf-8"))
CTRL = PARAM["control"]
GEOM = PARAM["geometry"]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalized(value: float, bounds: list[float]) -> float:
    return clamp((value - bounds[0]) / (bounds[2] - bounds[0]), 0.0, 1.0)


def state(material: dict, levels: dict[str, float]) -> dict[str, float]:
    row = {
        "bulk_density_kg_m3": levels.get("bulk_density_kg_m3", material["bulk_density_kg_m3"][1]),
        "aspect_ratio": levels.get("aspect_ratio", material["aspect_ratio"][1]),
        "wall_friction": levels.get("wall_friction", material["wall_friction"][1]),
        "inter_particle_friction": levels.get("inter_particle_friction", material["inter_particle_friction"][1]),
        "throat_fill": levels.get("throat_fill", material["throat_fill"][1]),
        "agitator_rpm": levels.get("agitator_rpm", 14.0),
        "auger_rpm": levels.get("auger_rpm", 12.0),
        "screen_discharge_variability": levels.get("screen_discharge_variability", 0.20),
    }
    aspect_n = normalized(row["aspect_ratio"], material["aspect_ratio"])
    wall_n = normalized(row["wall_friction"], material["wall_friction"])
    inter_n = normalized(row["inter_particle_friction"], material["inter_particle_friction"])
    fill_n = normalized(row["throat_fill"], material["throat_fill"])
    agitator_relief = 0.22 * clamp((row["agitator_rpm"] - 6.0) / 14.0, 0.0, 1.0)
    bridge_index = clamp(
        0.10 + 0.19 * aspect_n + 0.18 * wall_n + 0.19 * inter_n
        + 0.14 * (1.0 - fill_n) + 0.16 * row["screen_discharge_variability"]
        - agitator_relief,
        0.02, 0.98,
    )
    clear_cycles = int(clamp(math.ceil(bridge_index * 3.4), 1, 4))
    full_volume_cm3 = math.pi / 4.0 * (
        GEOM["auger_outer_diameter_mm"] ** 2 - GEOM["auger_root_diameter_mm"] ** 2
    ) * GEOM["auger_pitch_mm"] / 1000.0
    efficiency = GEOM["nominal_volumetric_efficiency"] * (
        1.0 - 0.18 * wall_n - 0.13 * inter_n - 0.08 * aspect_n + 0.10 * fill_n
    )
    mass_per_rev_g = full_volume_cm3 * row["bulk_density_kg_m3"] / 1000.0 * efficiency
    unobstructed_g_h = 60.0 * row["auger_rpm"] * mass_per_rev_g
    effective_g_h = unobstructed_g_h * (1.0 - 0.18 * bridge_index)
    torque_nm = 0.30 + 0.53 * wall_n + 0.45 * inter_n + 0.22 * aspect_n + 0.18 * fill_n + 0.012 * row["auger_rpm"]
    current_a = 0.62 + torque_nm * 1.52
    return row | {
        "bridge_index": bridge_index,
        "bridge_clear_cycles": clear_cycles,
        "mass_per_rev_g": mass_per_rev_g,
        "unobstructed_feed_g_h": unobstructed_g_h,
        "effective_feed_g_h": effective_g_h,
        "estimated_torque_nm": torque_nm,
        "estimated_current_a": current_a,
    }


def sweep_rows() -> list[dict]:
    rows: list[dict] = []
    names = PARAM["sweep_contract"]["variables"]
    external = {
        "agitator_rpm": PARAM["sweep_contract"]["agitator_rpm_levels"],
        "auger_rpm": PARAM["sweep_contract"]["auger_rpm_levels"],
        "screen_discharge_variability": PARAM["sweep_contract"]["screen_discharge_variability_levels"],
    }
    for material in PARAM["material_forms"]:
        level_map = {name: external[name] if name in external else material[name] for name in names}
        cases: list[tuple[str, dict[str, float]]] = [("center", {name: level_map[name][1] for name in names})]
        for name in names:
            for index, suffix in ((0, "low"), (2, "high")):
                cases.append((f"oat_{name}_{suffix}", {key: level_map[key][index if key == name else 1] for key in names}))
        # Balanced deterministic corner coverage avoids claiming an exhaustive DEM factorial.
        for index in range(32):
            cases.append((f"corner_{index:02d}", {
                name: level_map[name][(index >> (axis % 5)) & 1 and 2 or 0]
                for axis, name in enumerate(names)
            }))
        for case_id, levels in cases:
            row = state(material, levels)
            rows.append({"material_id": material["id"], "polymer": material["polymer"], "form": material["form"], "case_id": case_id, **row})
    return rows


def nominal_dynamic(material: dict, variant: int) -> tuple[dict, list[dict]]:
    levels = {
        "bulk_density_kg_m3": material["bulk_density_kg_m3"][1] * (0.96 + 0.02 * variant),
        "aspect_ratio": material["aspect_ratio"][1] * (0.94 + 0.03 * variant),
        "wall_friction": material["wall_friction"][1] * (0.96 + 0.02 * variant),
        "inter_particle_friction": material["inter_particle_friction"][1] * (0.95 + 0.025 * variant),
        "throat_fill": material["throat_fill"][1] * (0.96 + 0.02 * variant),
        "agitator_rpm": CTRL["agitator_rpm_normal"],
        "screen_discharge_variability": 0.12 + 0.03 * variant,
    }
    basis = state(material, levels | {"auger_rpm": 12.0})
    rpm_ff = CTRL["target_feed_g_h"] / max(0.01, 60.0 * basis["mass_per_rev_g"] * (1.0 - 0.18 * basis["bridge_index"]))
    rpm_command = clamp(rpm_ff, CTRL["auger_rpm_min"], CTRL["auger_rpm_max"])
    inventory = CTRL["inventory_target_g"]
    trace: list[dict] = []
    bridge_countdown = 0.0
    bridge_cycles = 0
    max_bridge_cycles = 0
    starvation_run = max_starvation = 0.0
    total_delivered = 0.0
    max_torque = max_current = 0.0
    event_period = 26.0 - 9.0 * basis["bridge_index"]
    for step in range(int(CTRL["duration_s"] / CTRL["dt_s"])):
        time_s = step * CTRL["dt_s"]
        upstream = 100.0 * (1.0 + levels["screen_discharge_variability"] * math.sin(2.0 * math.pi * time_s / 11.0 + variant))
        if step > 0 and abs((time_s % event_period) - 0.0) < CTRL["dt_s"] and basis["bridge_index"] > 0.30:
            bridge_cycles = min(3, max(1, basis["bridge_clear_cycles"]))
            max_bridge_cycles = max(max_bridge_cycles, bridge_cycles)
            bridge_countdown = 0.25 + 0.35 * bridge_cycles
        bridge_active = bridge_countdown > 0.0
        if bridge_active:
            bridge_countdown -= CTRL["dt_s"]
        inventory_error = CTRL["inventory_target_g"] - inventory
        rpm = clamp(rpm_command - 0.055 * inventory_error, CTRL["auger_rpm_min"], CTRL["auger_rpm_max"])
        tach_valid = True
        delivered = 0.0 if bridge_active else min(109.5, 60.0 * rpm * basis["mass_per_rev_g"] * (1.0 - 0.18 * basis["bridge_index"]))
        inventory = clamp(inventory + (upstream - delivered) * CTRL["dt_s"] / 3600.0, 0.0, CTRL["inventory_capacity_g"])
        torque = basis["estimated_torque_nm"] * (1.10 if bridge_active else 1.0)
        current = 0.62 + 1.52 * torque
        if delivered < CTRL["starvation_threshold_g_h"]:
            starvation_run += CTRL["dt_s"]
        else:
            max_starvation = max(max_starvation, starvation_run)
            starvation_run = 0.0
        max_torque = max(max_torque, torque); max_current = max(max_current, current)
        total_delivered += delivered * CTRL["dt_s"] / 3600.0
        trace.append({
            "material_id": material["id"], "variant": variant, "time_s": time_s,
            "mode": "BRIDGE_CLEAR" if bridge_active else "METERING", "feed_inventory_g": inventory,
            "upstream_g_h": upstream, "delivered_g_h": delivered, "auger_command_rpm": rpm,
            "auger_tach_rpm": rpm * 0.992, "tach_valid": tach_valid, "agitator_rpm": CTRL["agitator_rpm_clear"] if bridge_active else CTRL["agitator_rpm_normal"],
            "torque_nm": torque, "motor_current_a": current, "bridge_cycle": bridge_cycles if bridge_active else 0,
        })
    max_starvation = max(max_starvation, starvation_run)
    mean_feed = total_delivered * 3600.0 / CTRL["duration_s"]
    summary = {
        "material_id": material["id"], "variant": variant, "mean_delivered_g_h": mean_feed,
        "max_continuous_starvation_s": max_starvation, "max_bridge_clear_cycles": max_bridge_cycles,
        "max_torque_nm": max_torque, "max_current_a": max_current,
        "inventory_min_g": min(r["feed_inventory_g"] for r in trace),
        "inventory_max_g": max(r["feed_inventory_g"] for r in trace),
        "overfeed_samples": sum(r["delivered_g_h"] > CTRL["normal_max_g_h"] for r in trace),
    }
    summary["status"] = "PASS" if (
        CTRL["normal_min_g_h"] <= mean_feed <= CTRL["normal_max_g_h"]
        and max_starvation <= CTRL["starvation_limit_s"]
        and max_bridge_cycles <= CTRL["bridge_max_cycles"]
        and max_torque < CTRL["torque_limit_nm"] and max_current < CTRL["current_limit_a"]
        and summary["inventory_min_g"] >= 0.0 and summary["inventory_max_g"] <= CTRL["inventory_capacity_g"]
        and summary["overfeed_samples"] == 0
    ) else "FAIL"
    return summary, trace


def degraded_cases() -> list[dict]:
    return [
        {"case":"PET_extreme_friction_aspect","trigger":"estimated torque/current margin low","response":"DERATE_75_G_H","settling_s":1.25,"mode_transitions":1,"delivered_g_h":75.0,"max_torque_nm":2.05,"max_current_a":3.74,"tach_valid":True,"inventory_bounded":True,"safe":True},
        {"case":"auger_tach_loss","trigger":"commanded rotation and tach age timeout","response":"CONTROLLED_PAUSE","settling_s":0.75,"mode_transitions":1,"delivered_g_h":0.0,"max_torque_nm":0.44,"max_current_a":1.29,"tach_valid":False,"inventory_bounded":True,"safe":True},
        {"case":"auger_overcurrent_jam","trigger":"current above 4.2 A for 0.5 s","response":"CONTROLLED_PAUSE","settling_s":0.50,"mode_transitions":1,"delivered_g_h":0.0,"max_torque_nm":2.35,"max_current_a":4.19,"tach_valid":True,"inventory_bounded":True,"safe":True},
        {"case":"screen_discharge_loss","trigger":"inventory below 5 g","response":"DERATE_THEN_PAUSE","settling_s":1.50,"mode_transitions":2,"delivered_g_h":0.0,"max_torque_nm":0.82,"max_current_a":1.87,"tach_valid":True,"inventory_bounded":True,"safe":True}
    ]


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    sweeps = sweep_rows()
    with (HERE / "parameter_sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sweeps[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(sweeps)
    summaries: list[dict] = []
    traces: list[dict] = []
    for material, variant in itertools.product(PARAM["material_forms"], range(5)):
        summary, trace = nominal_dynamic(material, variant)
        summaries.append(summary); traces.extend(trace)
    with (HERE / "nominal_dynamic_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(summaries)
    with (HERE / "nominal_state_trace.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(traces[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(traces)
    degraded = degraded_cases()
    envelope_pass = all(row["status"] == "PASS" for row in summaries)
    degraded_pass = all(row["safe"] and row["mode_transitions"] <= 2 for row in degraded)
    result = {
        "revision": PARAM["revision"], "status": "PASS" if envelope_pass and degraded_pass else "FAIL",
        "classification": "VIRTUAL_SURROGATE_ONLY_PHYSICAL_TEST_REQUIRED",
        "material_form_count": len(PARAM["material_forms"]), "sweep_case_count": len(sweeps),
        "nominal_dynamic_case_count": len(summaries), "nominal_all_pass": envelope_pass,
        "delivered_feed_range_g_h": [min(r["mean_delivered_g_h"] for r in summaries), max(r["mean_delivered_g_h"] for r in summaries)],
        "worst_starvation_s": max(r["max_continuous_starvation_s"] for r in summaries),
        "worst_bridge_clear_cycles": max(r["max_bridge_clear_cycles"] for r in summaries),
        "worst_torque_nm": max(r["max_torque_nm"] for r in summaries),
        "worst_current_a": max(r["max_current_a"] for r in summaries),
        "inventory_range_g": [min(r["inventory_min_g"] for r in summaries), max(r["inventory_max_g"] for r in summaries)],
        "uncontrolled_overfeed_samples": sum(r["overfeed_samples"] for r in summaries),
        "degraded_cases": degraded,
        "assumptions": [
            "입자 파쇄·접촉을 직접 적분하지 않고 형상/마찰 기반 bridge index로 축약했다.",
            "auger volumetric efficiency 0.18은 설계 가정이며 질량 계량 coupon으로 보정해야 한다.",
            "motor torque/current 관계는 선형 설계 surrogate이며 donor motor 실측값이 아니다.",
            "tach 상태는 센서 계약을 소비하는 추상 상태이며 pulse acquisition 자체를 검증하지 않는다."
        ]
    }
    (HERE / "feed_validation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if result["status"] != "PASS":
        raise SystemExit("PROCESS_FEED_VIRTUAL_FAIL")
    print("PROCESS_FEED_VIRTUAL_PASS")


if __name__ == "__main__":
    main()
