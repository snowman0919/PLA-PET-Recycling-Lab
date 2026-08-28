#!/usr/bin/env python3
"""Compact v0.3 decision calculations; writes auditable JSON/Markdown outputs."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "cad/parameters/baseline.json").read_text())


def screw_sweep() -> list[dict]:
    rows = []
    for diameter_mm in P["extruder"]["candidate_diameters_mm"]:
        d = diameter_mm / 1000.0
        ld = 18.0 if diameter_mm <= 14 else 16.0
        rpm = 8.0 if diameter_mm <= 14 else 6.0
        # Feed-channel displacement: circumference * depth * pitch.  Range uses
        # bulk density 200..350 kg/m3, fill 0.15..0.35 and drag efficiency 0.45.
        displacement_m3_rev = math.pi * d * (0.16 * d) * d
        low = displacement_m3_rev * 0.15 * 0.45 * rpm * 60 * 200 * 1000
        high = displacement_m3_rev * 0.35 * 0.45 * rpm * 60 * 350 * 1000
        torque_3 = 1.5 * 3e6 * math.pi * d**3 / 16
        torque_6 = 1.5 * 6e6 * math.pi * d**3 / 16
        rows.append({
            "diameter_mm": diameter_mm,
            "ld": ld,
            "active_length_mm": diameter_mm * ld,
            "screening_rpm": rpm,
            "bulk_feed_range_gph": [round(low, 1), round(high, 1)],
            "torque_3mpa_sf1_5_nm": round(torque_3, 2),
            "torque_6mpa_sf1_5_nm": round(torque_6, 2),
            "selected": diameter_mm == 16.0,
        })
    return rows


def forming() -> dict:
    area = math.pi * (0.00175**2) / 4
    result = {}
    for material, density in (("PLA", 1240.0), ("PET", 1380.0)):
        speed = (0.2 / 3600) / (density * area)
        delay = (P["forming"]["die_to_gauge_mm"] / 1000) / speed
        result[material] = {
            "line_speed_m_min_at_200gph": round(speed * 60, 3),
            "transport_delay_s": round(delay, 2),
            "vertical_residence_s": round((P["forming"]["straight_length_die_to_puller_mm"] / 1000) / speed, 2),
        }
    # Lumped cooling screen: polymer cylinder cooling time constant for crossflow.
    # h range 35..65 W/m2K; target temperature is material Tg minus margin.
    for material, density, cp, start, target in (
        ("PLA", 1240, 1800, 200, 48), ("PET", 1380, 1200, 265, 65)
    ):
        h = 50.0
        tau = density * cp * 0.00175 / (4 * h)
        ambient = 25.0
        seconds = tau * math.log((start - ambient) / (target - ambient))
        result[material]["cooling_time_s_h50"] = round(seconds, 2)
        result[material]["cooling_length_mm_h50"] = round(seconds * result[material]["line_speed_m_min_at_200gph"] / 60 * 1000, 1)
        result[material]["required_h_w_m2k_for_installed_path"] = round(
            h * result[material]["cooling_length_mm_h50"] / P["forming"]["straight_length_die_to_puller_mm"], 1
        )
    return result


def control_sim(delay_s: float) -> dict:
    dt = 0.1
    steps = int(900 / dt)
    queue = [0.0] * max(1, int(delay_s / dt))
    diameter = 1.75
    puller = 1.0
    integral = 0.0
    errors = []
    for i in range(steps):
        disturbance = 0.025 if 2500 <= i < 4300 else (-0.018 if 6000 <= i < 7200 else 0.0)
        delayed = queue.pop(0)
        queue.append(puller - 1.0)
        diameter += dt * ((1.75 + disturbance - 0.42 * delayed) - diameter) / 6.0
        error = diameter - 1.75
        integral = max(-0.08, min(0.08, integral + error * dt))
        puller = max(0.88, min(1.12, 1.0 + 0.40 * error + 0.025 * integral))
        errors.append(error)
    rms = math.sqrt(sum(e * e for e in errors) / len(errors))
    return {"model": "first_order_plus_transport_delay", "duration_s": 900, "rms_error_mm": round(rms, 4), "max_abs_error_mm": round(max(map(abs, errors)), 4), "claim": "simulation_only"}


def main() -> None:
    out = ROOT / "simulation"
    out.mkdir(parents=True, exist_ok=True)
    screw = screw_sweep()
    forming_result = forming()
    power = P["power"] | {
        "calculated_concurrent_peak_w": sum((P["power"]["heater_peak_w"], P["power"]["shredder_peak_w"], P["power"]["extruder_peak_w"], P["power"]["motion_fans_logic_peak_w"])),
        "arbiter_margin_w": P["power"]["psu_rating_w"] - P["power"]["arbiter_peak_w"],
    }
    motor = P["shredder"]["motor"]
    conservative_cutter_torque = (
        motor["raw_motor_rated_torque_nm"] * motor["integrated_reduction_ratio"]
        * motor["gear_efficiency_assumption"] * motor["secondary_ratio"]
    )
    thermal = {
        "ambient_c": 25.0,
        "hot_path_c": P["extruder"]["hot_path_design_c"],
        "insulation_mm": 25.0,
        "metal_shield_air_gap_mm": 10.0,
        "screening_shield_c": 52.0,
        "polymer_keepout_c": 42.0,
        "assumptions": "1D resistance, k=0.04 W/mK, emissivity reduction by grounded shield; seams/slots unmodelled",
        "status": "physical_thermocouple_gate_required"
    }
    summary = {
        "revision": P["revision"],
        "screw_sweep": screw,
        "forming": forming_result,
        "diameter_loop": control_sim(forming_result["PLA"]["transport_delay_s"]),
        "power": power,
        "thermal": thermal,
        "cutter": {
            "curve": P["shredder"]["cutter_curve"],
            "motor_model": motor["model"],
            "motor_rated_current_a": motor["rated_current_a"],
            "secondary_ratio": motor["secondary_ratio"],
            "max_cutter_rpm": round(motor["output_no_load_rpm"] / motor["secondary_ratio"], 1),
            "profile_command_rpm": {"PLA": P["shredder"]["pla_rpm"], "PET": P["shredder"]["pet_rpm"]},
            "profile_trip_current_a": {"PLA": P["shredder"]["pla_trip_a"], "PET": P["shredder"]["pet_trip_a"]},
            "conservative_cutter_torque_nm": round(conservative_cutter_torque, 1),
            "design_torque_nm": P["shredder"]["trip_torque_nm"],
            "tangential_tip_force_n_at_trip": round(P["shredder"]["trip_torque_nm"] / (P["shredder"]["cutter_od_mm"] / 2000), 1),
            "phase_gear_model": "KHK SS3-16H modified bore 20 mm",
            "phase_gear_hardened_surface_limit_nm": 28.0,
            "brass_shear_key_mm": [6.0, 6.0, 4.0],
            "brass_key_shear_assumption_mpa": 100.0,
            "brass_key_nominal_shear_torque_nm": round(100.0 * 6.0 * 4.0 * 10.0 / 1000.0, 1),
            "shaft_diameter_mm": P["shredder"]["shaft_diameter_mm"],
            "torsional_shear_mpa": round(16 * P["shredder"]["trip_torque_nm"] * 1000 / (math.pi * P["shredder"]["shaft_diameter_mm"]**3), 1),
            "yield_safety_factor_at_145mpa_shear": round(145 / (16 * P["shredder"]["trip_torque_nm"] * 1000 / (math.pi * P["shredder"]["shaft_diameter_mm"]**3)), 2),
            "status": "coupon_and_impact_not_validated"
        }
    }
    (out / "engineering_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    calc_dir = ROOT / "calculations"
    screw_lines = [
        "# Screw sensitivity — 계산 screening",
        "",
        "이 계산은 bulk feed displacement와 pressure torque의 1차 screening이며 실제 melt flow를 증명하지 않는다.",
        "",
        "| D mm | L/D | 길이 mm | RPM | bulk feed g/h | T@3 MPa N·m | T@6 MPa N·m |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in screw:
        screw_lines.append(f"| {r['diameter_mm']:.0f} | {r['ld']:.0f} | {r['active_length_mm']:.0f} | {r['screening_rpm']:.0f} | {r['bulk_feed_range_gph'][0]:.0f}–{r['bulk_feed_range_gph'][1]:.0f} | {r['torque_3mpa_sf1_5_nm']:.2f} | {r['torque_6mpa_sf1_5_nm']:.2f} |")
    screw_lines += ["", "16 mm x 16 L/D를 선택한다. 15 N·m continuous drive는 6 MPa pressure-only screening보다 여유가 있으나 friction·nonuniform melt·screen blockage는 Gate 4에서 확인한다. 200 g/h는 stretch target이다."]
    (calc_dir / "screw_sensitivity.md").write_text("\n".join(screw_lines) + "\n")
    (calc_dir / "thermal_power_forming.md").write_text(
        "# 열·전력·forming screening\n\n"
        f"24 V PSU 600 W, arbiter limit {power['arbiter_peak_w']} W, margin {power['arbiter_margin_w']} W다. 모든 peak의 단순 합은 {power['calculated_concurrent_peak_w']} W이며 이를 동시에 허용하지 않는다. Shredder 구동 중 barrel heater와 screw drive를 hardware-enable/state-machine 양쪽에서 차단한다.\n\n"
        f"200 g/h에서 PLA/PET 선속은 {forming_result['PLA']['line_speed_m_min_at_200gph']}/{forming_result['PET']['line_speed_m_min_at_200gph']} m/min, die-gauge 지연은 {forming_result['PLA']['transport_delay_s']}/{forming_result['PET']['transport_delay_s']} s다. h=50 W/m2K 가정의 필요 길이는 PLA {forming_result['PLA']['cooling_length_mm_h50']} mm, PET {forming_result['PET']['cooling_length_mm_h50']} mm로 설치된 285 mm보다 길다. 285 mm에서 200 g/h를 유지하려면 등가 h가 각각 최소 {forming_result['PLA']['required_h_w_m2k_for_installed_path']}/{forming_result['PET']['required_h_w_m2k_for_installed_path']} W/m2K여야 한다. 따라서 200 g/h는 fan duct coupon 전 stretch target이며, strand 온도 Gate 실패 시 크기를 늘리지 않고 처리량을 낮춰 실측한다.\n\n"
        "300 °C hot path, 25 mm insulation, 10 mm air gap/grounded metal shield의 1D screening은 shield 52 °C, polymer keep-out 42 °C다. Seam, fastener, slot, airflow와 radiation view는 빠져 있으므로 열전대 Gate 없이는 합격이 아니다.\n"
    )
    (calc_dir / "shredder_drive_and_cutter.md").write_text(
        "# Cycloidal-derived cutter와 구동계 screening\n\n"
        "## 형상\n\n"
        "각 1/7 pitch에서 capture flank 76%는 `s(u)=u-sin(2*pi*u)/(2*pi)` cycloid displacement로 root radius 18 mm에서 tip radius 29 mm까지 상승한다. "
        "나머지 24%는 짧은 overhung nose와 빠른 cubic relief다. 따라서 기존 4점 saw-tooth polygon이 아니며 FreeCAD source와 CUT-01 DXF가 같은 곡선을 생성한다.\n\n"
        "## actuator\n\n"
        f"선정 후보는 `{motor['model']}` brushed geared-DC motor다. 24 V, 250 W, 75 rpm output, raw motor torque {motor['raw_motor_rated_torque_nm']} N·m, integrated ratio {motor['integrated_reduction_ratio']}:1, S2:60이다. "
        f"KTR ROTEX19 98ShA bore17/20 coupling으로 right cutter shaft를 직접 구동하므로 cutter 무부하 최대속도는 {motor['output_no_load_rpm']/motor['secondary_ratio']:.1f} rpm이다. integrated gear 효율 {motor['gear_efficiency_assumption']:.2f}를 적용한 보수적 cutter torque는 {conservative_cutter_torque:.1f} N·m다. "
        "이 값은 catalog 조합계산이며 실제 gearhead 출력토크 보증이 아니다. Gate 1에서 current/torque를 교정한다.\n\n"
        f"PLA/PET 명령은 {P['shredder']['pla_rpm']:.0f}/{P['shredder']['pet_rpm']:.0f} rpm, 정상 요구 {P['shredder']['continuous_torque_nm']:.0f} N·m, profile current trip은 {P['shredder']['pla_trip_a']:.0f}/{P['shredder']['pet_trip_a']:.0f} A, 20 A branch fuse, 3회 bounded reverse 뒤 latched fault다. "
        f"한 phase gear의 6 x 6 x 4 mm annealed brass key가 nominal {P['shredder']['mechanical_relief_torque_nm']:.0f} N·m 기계 relief이고, 이 torque에서 cutter tip tangential force는 {P['shredder']['trip_torque_nm']/(P['shredder']['cutter_od_mm']/2000):.0f} N이다. 두 cutter shaft의 반대회전/phase는 KHK `SS3-16H` M3 Z16 hardened gear pair가 유지한다. Catalog hardened surface durability 28.0 N·m보다 relief를 낮게 두고 coupon에서 실제 전단 torque를 확인한다.\n\n"
        "## 구매/치수 Gate\n\n"
        "Marketplace의 같은 모델명 제품 간 내부 감속과 shaft drawing이 일관되지 않다. Motor plate는 20/73.5 mm hole-spacing을 포괄하는 slot을 사용하지만, 입고 시 label, 17 x 44 mm shaft, no-load rpm, current, 회전방향을 확인하기 전 coupling과 full cutter를 발주하지 않는다.\n"
    )
    print("ENGINEERING_CALCULATIONS_OK")


if __name__ == "__main__":
    main()
