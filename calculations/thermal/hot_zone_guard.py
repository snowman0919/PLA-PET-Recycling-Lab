#!/usr/bin/env python3
"""Steady-state guard and nearby-polymer thermal sensitivity model.

This is a deliberately small thermal-resistance network for design gating.  It
does not replace a transient model, CFD, material certification, or the
worst-point thermocouple test required before heater commissioning.
"""

from __future__ import annotations

import json
from math import log, pi
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SIGMA = 5.670374419e-8
AMBIENT_C = 25.0
POLYMER_LIMIT_C = 45.0
TOUCH_TARGET_C = 50.0


def effective_emissivity(first: float, second: float) -> float:
    return 1.0 / (1.0 / first + 1.0 / second - 1.0)


def solve_case(case: dict[str, float | str], geometry: dict[str, float]) -> dict[str, float | str | bool]:
    hot_radius = geometry["hot_radius_m"]
    insulation_radius = geometry["insulation_outer_radius_m"]
    hot_length = geometry["hot_length_m"]
    shield_radius = geometry["shield_outer_radius_m"]
    shield_length = geometry["shield_length_m"]
    conductivity = geometry["insulation_conductivity_w_mk"]

    # Side and two end paths in parallel.  The bridge factor lumps clamps,
    # fasteners, seams and penetrations into a conservative conductance scale.
    side_conductance = 2 * pi * conductivity * hot_length / log(insulation_radius / hot_radius)
    end_conductance = 2 * conductivity * pi * hot_radius**2 / (insulation_radius - hot_radius)
    conductance = (side_conductance + end_conductance) * float(case["thermal_bridge_factor"])
    # Both proof guards are open-ended cylinders.  Count only the outer side
    # area; treating their openings as solid radiating end caps is optimistic.
    area = 2 * pi * shield_radius * shield_length

    shield_emissivity = float(case["shield_emissivity"])
    polymer_emissivity = float(case["polymer_emissivity"])
    view_factor = float(case["shield_to_polymer_view_factor"])
    radiation_emissivity = effective_emissivity(shield_emissivity, polymer_emissivity)
    hot_c = float(case["hot_node_c"])
    shield_h = float(case["shield_convection_w_m2k"])
    polymer_h = float(case["polymer_convection_w_m2k"])
    plume_h = float(case["shield_to_polymer_plume_w_m2k"])

    def residual(shield_c: float, polymer_c: float) -> tuple[float, float, dict[str, float]]:
        shield_k = shield_c + 273.15
        polymer_k = polymer_c + 273.15
        ambient_k = AMBIENT_C + 273.15
        q_hot = conductance * (hot_c - shield_c)
        q_convection = shield_h * area * (shield_c - AMBIENT_C)
        q_ambient_radiation = (
            (1 - view_factor)
            * shield_emissivity
            * SIGMA
            * area
            * (shield_k**4 - ambient_k**4)
        )
        q_polymer_radiation = (
            view_factor
            * radiation_emissivity
            * SIGMA
            * area
            * (shield_k**4 - polymer_k**4)
        )
        q_plume = plume_h * area * (shield_c - polymer_c)
        q_polymer_loss = (
            polymer_h * area * (polymer_c - AMBIENT_C)
            + polymer_emissivity * SIGMA * area * (polymer_k**4 - ambient_k**4)
        )
        return (
            q_hot - q_convection - q_ambient_radiation - q_polymer_radiation - q_plume,
            q_polymer_radiation + q_plume - q_polymer_loss,
            {
                "hot_to_shield_w": q_hot,
                "shield_convection_w": q_convection,
                "shield_to_ambient_radiation_w": q_ambient_radiation,
                "shield_to_polymer_radiation_w": q_polymer_radiation,
                "shield_to_polymer_plume_w": q_plume,
                "polymer_to_ambient_w": q_polymer_loss,
            },
        )

    shield_c = (hot_c + AMBIENT_C) / 2
    polymer_c = (shield_c + 3 * AMBIENT_C) / 4
    for _ in range(60):
        first, second, _ = residual(shield_c, polymer_c)
        step = 0.001
        first_ds, second_ds, _ = residual(shield_c + step, polymer_c)
        first_dp, second_dp, _ = residual(shield_c, polymer_c + step)
        a = (first_ds - first) / step
        b = (first_dp - first) / step
        c = (second_ds - second) / step
        d = (second_dp - second) / step
        determinant = a * d - b * c
        shield_c += (-first * d + b * second) / determinant
        polymer_c += (-a * second + c * first) / determinant

    first, second, flows = residual(shield_c, polymer_c)
    assert abs(first) < 1e-6 and abs(second) < 1e-6
    polymer_pass = polymer_c <= POLYMER_LIMIT_C
    touch_pass = shield_c <= TOUCH_TARGET_C
    expected = str(case["expected_disposition"])
    if expected == "NORMAL_PASS":
        assert polymer_pass and touch_pass
    elif expected == "FAULT_COOLDOWN_REQUIRED":
        assert polymer_pass and not touch_pass
    elif expected == "PROHIBITED_DIRECT_VIEW":
        assert not polymer_pass
    else:
        raise AssertionError(f"unknown expected disposition: {expected}")

    return {
        "name": str(case["name"]),
        "expected_disposition": expected,
        "hot_node_c": hot_c,
        "shield_equilibrium_c": shield_c,
        "polymer_equilibrium_c": polymer_c,
        "touch_target_c": TOUCH_TARGET_C,
        "polymer_limit_c": POLYMER_LIMIT_C,
        "touch_target_pass": touch_pass,
        "polymer_limit_pass": polymer_pass,
        "thermal_conductance_w_k": conductance,
        "shield_area_m2": area,
        "energy_balance_residual_w": max(abs(first), abs(second)),
        **flows,
    }


def build_report() -> dict:
    parameters = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())
    extruder = parameters["extruder"]
    dryer = parameters["dryer_feeder"]

    extruder_hot_radius = extruder["barrel_outer_diameter_mm"] / 2000 + 0.003
    extruder_insulation_radius = extruder_hot_radius + extruder["insulation_thickness_mm"] / 1000
    extruder_geometry = {
        "hot_radius_m": extruder_hot_radius,
        "insulation_outer_radius_m": extruder_insulation_radius,
        "hot_length_m": 0.396,
        "shield_outer_radius_m": extruder_insulation_radius
        + (extruder["shield_air_gap_mm"] + extruder["shield_thickness_mm"]) / 1000,
        "shield_length_m": 0.396,
        "insulation_conductivity_w_mk": 0.04,
    }
    dryer_hot_radius = (dryer["hopper_inner_diameter_mm"] / 2 + dryer["hopper_wall_mm"]) / 1000
    dryer_insulation_radius = dryer_hot_radius + dryer["insulation_thickness_mm"] / 1000
    dryer_geometry = {
        "hot_radius_m": dryer_hot_radius,
        "insulation_outer_radius_m": dryer_insulation_radius,
        "hot_length_m": dryer["hopper_active_height_mm"] / 1000,
        "shield_outer_radius_m": dryer_insulation_radius
        + (dryer["shield_air_gap_mm"] + dryer["shield_thickness_mm"]) / 1000,
        "shield_length_m": (dryer["hopper_active_height_mm"] + 24.0) / 1000,
        "insulation_conductivity_w_mk": dryer["insulation_conductivity_w_mk"],
    }

    common_normal = {
        "shield_emissivity": 0.30,
        "polymer_emissivity": 0.90,
        "shield_to_polymer_view_factor": 0.35,
        "shield_convection_w_m2k": 8.0,
        "polymer_convection_w_m2k": 6.0,
        "shield_to_polymer_plume_w_m2k": 0.5,
        "expected_disposition": "NORMAL_PASS",
    }
    common_fault = {
        "shield_emissivity": 0.80,
        "polymer_emissivity": 0.90,
        "shield_convection_w_m2k": 3.0,
        "polymer_convection_w_m2k": 3.0,
        "shield_to_polymer_plume_w_m2k": 1.0,
    }
    cases: list[tuple[dict, dict]] = [
        (
            {
                **common_normal,
                "name": "extruder_pet_ventilated",
                "hot_node_c": max(extruder["pet_profile_c"]),
                "thermal_bridge_factor": extruder["thermal_bridge_factor"],
            },
            extruder_geometry,
        ),
        (
            {
                **common_fault,
                "name": "extruder_design_max_baffled",
                "hot_node_c": extruder["hot_zone_design_max_c"],
                "thermal_bridge_factor": extruder["thermal_bridge_factor"] * 1.5,
                "shield_to_polymer_view_factor": 0.60,
                "expected_disposition": "FAULT_COOLDOWN_REQUIRED",
            },
            extruder_geometry,
        ),
        (
            {
                **common_fault,
                "name": "extruder_design_max_direct_view",
                "hot_node_c": extruder["hot_zone_design_max_c"],
                "thermal_bridge_factor": extruder["thermal_bridge_factor"] * 1.5,
                "shield_to_polymer_view_factor": 1.00,
                "expected_disposition": "PROHIBITED_DIRECT_VIEW",
            },
            extruder_geometry,
        ),
        (
            {
                **common_normal,
                "name": "dryer_pet_ventilated",
                "hot_node_c": dryer["pet_profile"]["dry_setpoint_c"],
                "thermal_bridge_factor": dryer["thermal_bridge_factor"],
            },
            dryer_geometry,
        ),
        (
            {
                **common_fault,
                "name": "dryer_trip_direct_view",
                "hot_node_c": dryer["pet_profile"]["independent_trip_c"],
                "thermal_bridge_factor": dryer["thermal_bridge_factor"] * 1.5,
                "shield_to_polymer_view_factor": 1.00,
                "expected_disposition": "FAULT_COOLDOWN_REQUIRED",
            },
            dryer_geometry,
        ),
    ]
    results = [solve_case(case, geometry) for case, geometry in cases]
    return {
        "status": "SENSITIVITY_GATE_NOT_PHYSICAL_VALIDATION",
        "limits": {
            "accessible_metal_shield_target_c": TOUCH_TARGET_C,
            "nearby_pla_abs_design_limit_c": POLYMER_LIMIT_C,
        },
        "design_change": {
            "extruder_insulation_previous_mm": 40.0,
            "extruder_insulation_current_mm": extruder["insulation_thickness_mm"],
            "reason": "40 mm model exceeded the 50 C normal accessible-shield target; 50 mm closes the nominal calculation gate.",
        },
        "mandatory_gates": [
            "No PLA/ABS part may have direct radiative sightline to the extruder shield; effective view factor must be 0.60 or lower by a grounded metal baffle.",
            "A shield above 50 C is fault/cooldown state only; RUN remains inhibited until the measured guard temperature is below the release threshold.",
            "Thermocouples at seams, clamps, slots, cable penetrations and the nearest polymer point must pass before heater commissioning.",
            "The 45 C polymer criterion is a conservative project design limit, not a generic material certification.",
        ],
        "model_limits": [
            "Steady two-node lumped resistance network; no transient heat soak, contact map, airflow CFD or sun/room heat load.",
            "Bridge, convection, emissivity and view factors are bounded assumptions and must be replaced by measured values.",
            "The model does not approve insulation chemistry, electrical clearances, guard strength or burn protection.",
        ],
        "cases": results,
    }


def markdown(report: dict) -> str:
    rows = []
    for case in report["cases"]:
        rows.append(
            f"| {case['name']} | {case['hot_node_c']:.0f} | {case['shield_equilibrium_c']:.1f} | "
            f"{case['polymer_equilibrium_c']:.1f} | {case['expected_disposition']} |"
        )
    return "\n".join(
        [
            "# Hot-zone guard and nearby-polymer thermal gate",
            "",
            "상태: **SENSITIVITY GATE — PHYSICAL THERMOCOUPLE VALIDATION OPEN**",
            "",
            "압출기/건조기 hot node→단열재→금속 shield→인접 polymer의 정상상태 열저항망이다. "
            "원통 측면과 양단 전도, shield 대류·복사, polymer 복사·plume 결합을 동시에 푼다. "
            "Clamp·seam·penetration은 thermal-bridge factor로만 묶었으므로 실제 hotspot을 승인하지 않는다.",
            "",
            "| Case | Hot °C | Shield °C | Polymer °C | 판정 |",
            "|---|---:|---:|---:|---|",
            *rows,
            "",
            "## 설계 결정",
            "",
            "- 기존 압출기 40 mm 단열은 PET 정상 case에서 shield 약 54 °C로 50 °C 목표를 넘었다. "
            "Baseline과 CAD 실두께를 50 mm로 변경하면 동일 case가 약 48.8 °C다.",
            "- 압출기 310 °C, 열교 1.5배, 낮은 대류, 고방사율 fault envelope에서는 metal baffle로 "
            "shield→polymer 유효 view factor를 0.60 이하로 제한해야 45 °C polymer limit 아래다.",
            "- 직접 시야(view factor 1.0)는 약 48.6 °C로 실패하므로 hot zone의 PLA/ABS cover, bracket, "
            "cable carrier와 sensor mount를 금지한다. 해당 영역은 접지 금속 또는 정격 무기 절연물만 쓴다.",
            "- Fault/cooldown에서 shield는 50 °C를 넘을 수 있으므로 guard sensor 실측값이 release threshold "
            "아래가 될 때까지 RUN과 service access를 금지한다.",
            "",
            "## 물리 시험 gate",
            "",
            "최대 setpoint와 independent-trip fault에서 seam, clamp, slot, cable penetration, 가장 가까운 polymer "
            "point에 열전대를 설치한다. 정상 shield ≤50 °C, 인접 PLA/ABS 후보 ≤45 °C를 확인하고, "
            "모델보다 높은 지점이 하나라도 있으면 insulation/baffle/airflow를 재설계한다. 본 계산만으로 heater를 인가하지 않는다.",
            "",
            "상세 수치와 에너지수지는 `simulation/thermal/hot_zone_guard.json`에 있다.",
            "",
        ]
    )


def main() -> None:
    report = build_report()
    (ROOT / "simulation" / "thermal" / "hot_zone_guard.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "calculations" / "thermal" / "hot_zone_guard.md").write_text(markdown(report))
    print(json.dumps(report, indent=2))
    print("HOT_ZONE_GUARD_MODEL_OK")


if __name__ == "__main__":
    main()
