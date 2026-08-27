#!/usr/bin/env python3
"""Conservative design sweep for the 200 g/h PLA/PET single-screw extruder."""

from __future__ import annotations

import json
from math import atan, log, pi, sin, cos, sqrt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["extruder"]


def channel(diameter_mm: float) -> dict[str, float]:
    d = diameter_mm / 1000
    pitch = P["pitch_ratio"] * d
    flight = P["flight_width_ratio"] * d
    feed_h = P["feed_depth_ratio"] * d
    meter_h = P["metering_depth_ratio"] * d
    angle = atan(pitch / (pi * d))
    width = pitch * cos(angle) - flight
    axial_lengths = [value * d for value in P["zone_lengths_d"]]
    channel_volume = width / sin(angle) * (
        axial_lengths[0] * feed_h
        + axial_lengths[1] * (feed_h + meter_h) / 2
        + axial_lengths[2] * meter_h
    )
    # Couette drag projected from the helical channel onto the screw axis.
    drag_per_rps = 0.5 * width * meter_h * pi * d * cos(angle) * sin(angle)
    return {
        "diameter_m": d,
        "pitch_m": pitch,
        "flight_width_m": flight,
        "feed_depth_m": feed_h,
        "meter_depth_m": meter_h,
        "helix_angle_deg": angle * 180 / pi,
        "channel_width_m": width,
        "meter_length_m": axial_lengths[2],
        "channel_volume_m3": channel_volume,
        "drag_m3_per_rev": drag_per_rps,
    }


def pressure_backflow_m3_s(c: dict[str, float], pressure_pa: float, viscosity_pa_s: float) -> float:
    angle = c["helix_angle_deg"] * pi / 180
    return (
        c["channel_width_m"]
        * c["meter_depth_m"] ** 3
        * pressure_pa
        * sin(angle) ** 2
        / (12 * viscosity_pa_s * c["meter_length_m"])
    )


def net_flow_m3_s(c: dict[str, float], rpm: float, pressure_pa: float, viscosity_pa_s: float) -> float:
    drag = c["drag_m3_per_rev"] * rpm / 60
    return max(0.0, drag - pressure_backflow_m3_s(c, pressure_pa, viscosity_pa_s))


def mass_flow_gph(c: dict[str, float], rpm: float, pressure_pa: float, viscosity_pa_s: float, density_kg_m3: float) -> float:
    return net_flow_m3_s(c, rpm, pressure_pa, viscosity_pa_s) * density_kg_m3 * 3.6e6


def required_rpm(c: dict[str, float], target_gph: float, pressure_pa: float, viscosity_pa_s: float, density_kg_m3: float) -> float:
    target_q = target_gph / 3.6e6 / density_kg_m3
    return 60 * (target_q + pressure_backflow_m3_s(c, pressure_pa, viscosity_pa_s)) / c["drag_m3_per_rev"]


def capillary_pressure_pa(flow_m3_s: float, radius_m: float, length_m: float, n: float, viscosity_at_ref_pa_s: float, ref_shear_s: float) -> float:
    # Power-law fluid: eta=m*gamma^(n-1), solved for pressure in a round capillary.
    consistency = viscosity_at_ref_pa_s * ref_shear_s ** (1 - n)
    return 2 * consistency * length_m / radius_m * (
        flow_m3_s * (3 + 1 / n) / (pi * radius_m**3)
    ) ** n


def torsion_von_mises_mpa(torque_nm: float, diameter_mm: float, concentration: float) -> float:
    shear_mpa = 16 * torque_nm * 1000 / (pi * diameter_mm**3) * concentration
    return sqrt(3) * shear_mpa


def main() -> dict:
    density_min = 1100.0
    viscosity_worst_backflow = 300.0
    pressure_limit = P["normal_pressure_limit_mpa"] * 1e6
    sweep = []
    for diameter in P["candidate_screw_diameters_mm"]:
        c = channel(diameter)
        worst = mass_flow_gph(c, P["speed_range_rpm"][1], pressure_limit, viscosity_worst_backflow, density_min)
        nominal_rpm = required_rpm(c, P["stable_mass_flow_target_gph"], 5e6, 600.0, density_min)
        sweep.append(
            {
                "diameter_mm": diameter,
                "length_mm": diameter * P["length_to_diameter_ratio"],
                "feed_depth_mm": c["feed_depth_m"] * 1000,
                "metering_depth_mm": c["meter_depth_m"] * 1000,
                "compression_ratio": c["feed_depth_m"] / c["meter_depth_m"],
                "helix_angle_deg": c["helix_angle_deg"],
                "drag_displacement_mm3_rev": c["drag_m3_per_rev"] * 1e9,
                "worst_normal_output_gph_at_45rpm": worst,
                "capacity_margin_over_200gph": worst / P["stable_mass_flow_target_gph"],
                "rpm_for_200gph_at_5mpa_600pas": nominal_rpm,
                "passes_200_gph_worst_normal": worst >= P["stable_mass_flow_target_gph"],
                "passes_required_model_margin": worst >= P["stable_mass_flow_target_gph"] * P["minimum_model_capacity_margin"],
            }
        )

    c = channel(P["screw_diameter_mm"])
    target_q = P["stable_mass_flow_target_gph"] / 3.6e6 / density_min
    occupied_volume = [c["channel_volume_m3"] * fill for fill in (0.35, 0.60)]
    residence_min = [volume / target_q / 60 for volume in occupied_volume]
    purge_min = [7 * value for value in residence_min]

    die_radius = P["die_bore_mm"] / 2000
    die_length = P["die_land_mm"] / 1000
    apparent_shear = 4 * target_q / (pi * die_radius**3)
    n = 0.4
    corrected_shear = apparent_shear * (3 * n + 1) / (4 * n)
    die_pressure = {
        str(viscosity): capillary_pressure_pa(target_q, die_radius, die_length, n, viscosity, 20.0) / 1e6
        for viscosity in (300.0, 600.0, 1500.0)
    }
    final_area_mm2 = pi * 1.75**2 / 4
    final_line_speed_m_min = {
        material: (P["stable_mass_flow_target_gph"] / 3600) / (density_g_mm3 * final_area_mm2) * 60 / 1000
        for material, density_g_mm3 in (("pla", 0.00124), ("pet", 0.00138))
    }

    d_m = P["screw_diameter_mm"] / 1000
    projected_area = pi * d_m**2 / 4
    thrust_working = projected_area * pressure_limit
    thrust_proof = projected_area * P["structural_proof_pressure_mpa"] * 1e6
    bearing = P["thrust_bearing"]
    root_diameter_mm = P["screw_diameter_mm"] - 2 * c["feed_depth_m"] * 1000
    proof_torque = P["torque_trip_nm"]
    root_vm = torsion_von_mises_mpa(proof_torque, root_diameter_mm, 1.5)
    tail_vm = torsion_von_mises_mpa(proof_torque, bearing["bore_mm"], 1.6)

    ri = P["barrel_inner_diameter_mm"] / 2000
    ro = P["barrel_outer_diameter_mm"] / 2000
    barrel_hoop = P["structural_proof_pressure_mpa"] * (ro**2 + ri**2) / (ro**2 - ri**2)
    barrel_hot_allowable = 100.0
    barrel_stress_with_features = barrel_hoop * 1.5

    length = P["screw_diameter_mm"] * P["length_to_diameter_ratio"] / 1000
    insulation_outer_r = ro + P["insulation_thickness_mm"] / 1000
    radial_r = log(insulation_outer_r / ro) / (2 * pi * 0.04 * length)
    heater_coupled_power = P["heater_peak_power_w"] * 0.85
    barrel_mass_kg = pi * (ro**2 - ri**2) * length * 7850
    metal_mass_kg = barrel_mass_kg + 1.3  # screw, breaker, die and clamp-envelope allowance
    metal_cp_j_kgk = 500.0
    thermal = {}
    for material, target_c, cp_kj, fusion_kj in (("pla", 210.0, 1.8, 50.0), ("pet", 280.0, 1.3, 80.0)):
        delta = target_c - 25.0
        material_w = P["stable_mass_flow_target_gph"] / 1000 / 3600 * (cp_kj * 1000 * delta + fusion_kj * 1000)
        loss_w = delta / radial_r * 2.5
        ramp_s = metal_mass_kg * metal_cp_j_kgk * delta / (heater_coupled_power - loss_w / 2)
        thermal[material] = {
            "target_melt_c": target_c,
            "cold_feed_material_heating_w": material_w,
            "insulated_loss_with_bridges_w": loss_w,
            "steady_heater_duty": (material_w + loss_w) / P["heater_peak_power_w"],
            "empty_cold_ramp_minutes": ramp_s / 60,
        }

    usable_psu_w = 600.0 * 0.90
    auxiliary_reserve_w = 48.0 + 40.0 + 36.0 + 24.0
    power_modes = {
        "heatup_drive_off_w": auxiliary_reserve_w + 300.0,
        "extrude_normal_w": auxiliary_reserve_w + 250.0 + 126.0,
        "torque_transient_w": auxiliary_reserve_w + 150.0 + 240.0,
    }

    output = {
        "model_status": "SENSITIVITY_MODEL_NOT_PHYSICALLY_VALIDATED",
        "assumptions": {
            "melt_density_min_kg_m3": density_min,
            "viscosity_sweep_pa_s": [300.0, 600.0, 1500.0],
            "normal_pressure_limit_mpa": P["normal_pressure_limit_mpa"],
            "power_law_index": n,
            "channel_model": "isothermal Newtonian Couette drag minus pressure backflow; leakage and solids conveying omitted",
        },
        "diameter_sweep": sweep,
        "selection": {
            "diameter_mm": P["screw_diameter_mm"],
            "length_mm": length * 1000,
            "l_over_d": P["length_to_diameter_ratio"],
            "pitch_mm": c["pitch_m"] * 1000,
            "flight_width_mm": c["flight_width_m"] * 1000,
            "feed_depth_mm": c["feed_depth_m"] * 1000,
            "metering_depth_mm": c["meter_depth_m"] * 1000,
            "root_diameter_mm": root_diameter_mm,
            "compression_ratio": c["feed_depth_m"] / c["meter_depth_m"],
            "zones_mm": [value * d_m * 1000 for value in P["zone_lengths_d"]],
            "speed_range_rpm": P["speed_range_rpm"],
            "worst_normal_output_gph_at_45rpm": mass_flow_gph(c, 45.0, pressure_limit, viscosity_worst_backflow, density_min),
            "nominal_rpm_for_200_gph": required_rpm(c, 200.0, 5e6, 600.0, density_min),
            "metering_wall_shear_rate_s_at_45rpm": pi * d_m * (45 / 60) * cos(c["helix_angle_deg"] * pi / 180) / c["meter_depth_m"],
            "geometric_channel_volume_cm3": c["channel_volume_m3"] * 1e6,
            "residence_time_min_at_35_to_60pct_fill": residence_min,
            "seven_residence_purge_min": purge_min,
        },
        "die": {
            "bore_mm": P["die_bore_mm"],
            "land_mm": P["die_land_mm"],
            "apparent_shear_rate_s": apparent_shear,
            "power_law_corrected_shear_rate_s": corrected_shear,
            "capillary_only_pressure_mpa_by_viscosity_at_20s": die_pressure,
            "clean_system_pressure_budget_mpa": P["clean_pressure_target_mpa"],
            "area_drawdown_ratio_3mm_to_1_75mm": (P["die_bore_mm"] / 1.75) ** 2,
            "final_filament_line_speed_m_min_at_200gph": final_line_speed_m_min,
            "note": "Entrance, breaker and screen-pack loss are excluded from the capillary values and dominate the allocated pressure budget.",
        },
        "structure": {
            "working_thrust_n_at_8mpa": thrust_working,
            "proof_thrust_n_at_20mpa": thrust_proof,
            "51102_static_safety_factor_at_proof": bearing["static_rating_n"] / thrust_proof,
            "screw_root_von_mises_mpa_at_30nm_with_kt1_5": root_vm,
            "screw_tail_von_mises_mpa_at_30nm_with_kt1_6": tail_vm,
            "candidate_4140_yield_mpa": 650.0,
            "screw_root_safety_factor": 650.0 / root_vm,
            "barrel_proof_hoop_mpa_with_feature_factor_1_5": barrel_stress_with_features,
            "barrel_hot_allowable_mpa_assumption": barrel_hot_allowable,
            "barrel_hot_safety_factor": barrel_hot_allowable / barrel_stress_with_features,
        },
        "drive": {
            "continuous_output_torque_target_nm": P["continuous_torque_target_nm"],
            "trip_torque_nm": P["torque_trip_nm"],
            "mechanical_power_w_at_20nm_45rpm": P["continuous_torque_target_nm"] * 2 * pi * 45 / 60,
            "electrical_input_w_at_75pct_efficiency": P["continuous_torque_target_nm"] * 2 * pi * 45 / 60 / 0.75,
        },
        "thermal": {
            "barrel_metal_length_mm": length * 1000,
            "insulation_thickness_mm": P["insulation_thickness_mm"],
            "radial_thermal_resistance_k_w": radial_r,
            "heater_peak_w": P["heater_peak_power_w"],
            "heated_metal_mass_kg": metal_mass_kg,
            "profiles": thermal,
        },
        "power_arbitration": {
            "psu_nominal_w_unverified": 600.0,
            "temporary_usable_ceiling_w_at_90pct": usable_psu_w,
            "auxiliary_reserve_w": auxiliary_reserve_w,
            "auxiliary_assumptions_w": {
                "dryer_feeder_blower": 48.0,
                "puller_spooler": 40.0,
                "controls": 36.0,
                "cooling_fans": 24.0,
            },
            "modes": power_modes,
            "rule": "300 W heater is heat-up only; cap to 250 W while extruding and 150 W during a drive torque transient.",
        },
    }
    path = ROOT / "simulation" / "extruder" / "screw_design_sweep.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    main()
