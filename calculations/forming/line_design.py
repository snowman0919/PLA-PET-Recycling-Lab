#!/usr/bin/env python3
"""Decision model for cooling, optical gauge, puller delay and 1 kg spooler."""

from __future__ import annotations

import json
from collections import deque
from math import cos, pi, radians, sin, sqrt, tan
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())
F = P["filament_forming"]
S = P["spooler"]


def line_speed_m_min(mass_flow_gph: float, density_kg_m3: float, diameter_mm: float) -> float:
    mass_flow_kg_s = mass_flow_gph / 1000 / 3600
    area_m2 = pi * (diameter_mm / 1000) ** 2 / 4
    return mass_flow_kg_s / (density_kg_m3 * area_m2) * 60


def cylinder_crossflow_h(air_speed_m_s: float, diameter_mm: float) -> dict[str, float]:
    """Churchill-Bernstein cylinder correlation using stated 25 C air assumptions."""

    rho_air = 1.184
    viscosity_pa_s = 1.85e-5
    conductivity_w_m_k = 0.0263
    prandtl = 0.707
    diameter_m = diameter_mm / 1000
    reynolds = rho_air * air_speed_m_s * diameter_m / viscosity_pa_s
    nusselt = 0.3 + (
        0.62 * sqrt(reynolds) * prandtl ** (1 / 3)
        / (1 + (0.4 / prandtl) ** (2 / 3)) ** 0.25
        * (1 + (reynolds / 282000) ** (5 / 8)) ** (4 / 5)
    )
    return {
        "air_speed_m_s": air_speed_m_s,
        "reynolds": reynolds,
        "nusselt": nusselt,
        "heat_transfer_coefficient_w_m2_k": nusselt * conductivity_w_m_k / diameter_m,
    }


def radial_cooling_time_s(material: dict, h_w_m2_k: float) -> dict[str, float]:
    """Explicit finite-volume radial conduction model for a long 1.75 mm cylinder."""

    radius = F["target_diameter_mm"] / 2000
    cells = 24
    dr = radius / cells
    dt = 0.001
    volumes = [pi * (((i + 1) * dr) ** 2 - (i * dr) ** 2) for i in range(cells)]
    temperatures = [material["die_temperature_c"]] * cells
    elapsed = 0.0
    while temperatures[0] > material["puller_center_temperature_limit_c"] and elapsed < 180:
        heat_w_m = [0.0] * cells
        for i in range(cells - 1):
            interface_area_m = 2 * pi * (i + 1) * dr
            flow = material["thermal_conductivity_w_m_k"] * interface_area_m / dr * (
                temperatures[i] - temperatures[i + 1]
            )
            heat_w_m[i] -= flow
            heat_w_m[i + 1] += flow
        heat_w_m[-1] -= h_w_m2_k * 2 * pi * radius * (temperatures[-1] - F["ambient_temperature_c"])
        temperatures = [
            value + dt * heat_w_m[i] / (material["density_kg_m3"] * material["specific_heat_j_kg_k"] * volumes[i])
            for i, value in enumerate(temperatures)
        ]
        elapsed += dt
    return {
        "time_s": elapsed,
        "center_temperature_c": temperatures[0],
        "surface_temperature_c": temperatures[-1],
    }


def cooling() -> dict:
    cases = {}
    for material_name, material in F["materials"].items():
        for flow_name, mass_flow, air_speed in (
            ("nominal", F["nominal_mass_flow_gph"], F["nominal_crossflow_air_speed_m_s"]),
            ("high", F["high_mass_flow_gph"], F["high_flow_crossflow_air_speed_m_s"]),
        ):
            convection = cylinder_crossflow_h(air_speed, F["target_diameter_mm"])
            transient = radial_cooling_time_s(material, convection["heat_transfer_coefficient_w_m2_k"])
            speed = line_speed_m_min(mass_flow, material["density_kg_m3"], F["target_diameter_mm"])
            required_length = transient["time_s"] * speed / 60 * 1000
            cases[f"{material_name}_{flow_name}"] = {
                "mass_flow_gph": mass_flow,
                "line_speed_m_min": speed,
                **convection,
                **transient,
                "required_cooling_length_mm": required_length,
                "tunnel_margin_mm": F["cooling_tunnel_length_mm"] - required_length,
                "passes_tunnel": required_length <= F["cooling_tunnel_length_mm"],
            }
    return cases


def optics() -> dict:
    gauge = F["gauge"]
    counts_per_mm = gauge["adc_counts_per_axis"] / gauge["qualified_field_width_mm"]
    return {
        "sensor_type": gauge["sensor_candidate"],
        "adc_counts_per_mm": counts_per_mm,
        "adc_counts_across_1_75mm": counts_per_mm * F["target_diameter_mm"],
        "ideal_mm_per_count": 1 / counts_per_mm,
        "qualification_gate": "Report U95 <= 0.020 mm after two-axis linearity, edge threshold, ambient-light and thermal-drift calibration; ADC count size alone is not accuracy.",
    }


def controller_simulation() -> dict:
    """Compare delayed diameter controllers under a repeatable mass-flow disturbance."""

    target = F["target_diameter_mm"]
    density = F["materials"]["pla"]["density_kg_m3"]
    nominal_speed = line_speed_m_min(F["nominal_mass_flow_gph"], density, target)
    delay_s = F["die_to_gauge_distance_mm"] / 1000 / (nominal_speed / 60)
    dt = 0.1
    duration_s = 900.0

    def run(kind: str) -> dict[str, float]:
        delay_steps = round(delay_s / dt)
        formed = deque([target] * (delay_steps + 1), maxlen=delay_steps + 1)
        nominal_model = deque([target] * (delay_steps + 1), maxlen=delay_steps + 1)
        flow_model_history = deque([target] * (delay_steps + 1), maxlen=delay_steps + 1)
        flow = 1.0
        flow_model = 1.0
        command = nominal_speed
        integral = 0.0
        filtered = target
        previous_error = 0.0
        errors: list[float] = []
        commands: list[float] = []
        out_of_initial = 0
        for step in range(round(duration_s / dt)):
            t = step * dt
            requested_flow = 1.0 if t < 180 else (1.08 if t < 480 else 0.94)
            flow += dt / 60.0 * (requested_flow - flow)
            flow_model += dt / 60.0 * (requested_flow - flow_model)
            # A slow unmodelled +/-1.5% conveying ripple prevents the
            # feed-forward result from being an unrealistically exact inverse.
            effective_flow = flow * (1 + 0.015 * sin(2 * pi * t / 180.0))
            actual_formed = target * sqrt(effective_flow * nominal_speed / max(command, 1e-9))
            formed.append(actual_formed)
            current_model = target * sqrt(nominal_speed / max(command, 1e-9))
            current_flow_model = target * sqrt(flow_model * nominal_speed / max(command, 1e-9))
            nominal_model.append(current_model)
            flow_model_history.append(current_flow_model)
            measured = formed[0]
            filtered += dt / F["puller"]["diameter_measurement_filter_s"] * (measured - filtered)
            error = filtered / target - 1.0

            if step % round(1 / dt) == 0:
                if kind == "aggressive_pid":
                    integral += error
                    derivative = error - previous_error
                    requested = nominal_speed * (1 + 2.2 * error + 0.18 * integral + 1.2 * derivative)
                elif kind == "filtered_pi":
                    integral = max(-0.25, min(0.25, integral + 0.008 * error))
                    requested = nominal_speed * (1 + 0.55 * error + integral)
                elif kind == "bounded_smith_pi":
                    delayed_model = nominal_model[0]
                    predicted = current_model + (filtered - delayed_model)
                    prediction_error = predicted / target - 1.0
                    integral = max(-0.25, min(0.25, integral + 0.012 * prediction_error))
                    requested = nominal_speed * (1 + 0.8 * prediction_error + integral)
                elif kind == "feedforward_smith_pi":
                    # Commanded feeder/screw flow supplies the causal model;
                    # delayed optical residual corrects mismatch without making
                    # the winder part of the diameter loop.
                    delayed_model = flow_model_history[0]
                    predicted = current_flow_model + (filtered - delayed_model)
                    prediction_error = predicted / target - 1.0
                    integral = max(-0.20, min(0.20, integral + 0.008 * prediction_error))
                    requested = nominal_speed * flow_model * (1 + 0.55 * prediction_error + integral)
                else:
                    raise ValueError(kind)
                requested = max(F["puller"]["line_speed_range_m_min"][0], min(F["puller"]["line_speed_range_m_min"][1], requested))
                maximum_change = F["puller"]["maximum_speed_slew_m_min_s"]
                command += max(-maximum_change, min(maximum_change, requested - command))
                previous_error = error
            errors.append(measured - target)
            commands.append(command)
            if abs(measured - target) > F["initial_tolerance_mm"]:
                out_of_initial += 1
        tail = errors[round(120 / dt):]
        return {
            "delay_s": delay_s,
            "rms_error_after_120s_mm": sqrt(sum(value * value for value in tail) / len(tail)),
            "maximum_absolute_error_mm": max(abs(value) for value in errors),
            "time_outside_initial_tolerance_s": out_of_initial * dt,
            "command_min_m_min": min(commands),
            "command_max_m_min": max(commands),
        }

    results = {
        kind: run(kind)
        for kind in ("aggressive_pid", "filtered_pi", "bounded_smith_pi", "feedforward_smith_pi")
    }
    return {
        "scenario": {
            "duration_s": duration_s,
            "flow_steps": [[0, 1.0], [180, 1.08], [480, 0.94]],
            "flow_time_constant_s": 60.0,
            "unmodelled_conveying_ripple_fraction": 0.015,
            "production_sensor_dropout_policy": "Hold the last bounded puller command for at most 3 s; then pause feed/extrusion and keep the winder tension-safe.",
        },
        **results,
    }


def spooler() -> dict:
    diameter = S["shaft_diameter_mm"] / 1000
    span = S["bearing_span_mm"] / 1000
    proof_load = S["maximum_loaded_mass_kg"] * S["proof_acceleration_g"] * 9.80665
    moment = proof_load * span / 4
    stress = 32 * moment / (pi * diameter**3) / 1e6
    inertia_area = pi * diameter**4 / 64
    deflection = proof_load * span**3 / (48 * 200e9 * inertia_area) * 1000
    pla_speed = line_speed_m_min(F["nominal_mass_flow_gph"], F["materials"]["pla"]["density_kg_m3"], F["target_diameter_mm"])
    core_rpm = pla_speed * 1000 / (pi * S["minimum_supported_core_diameter_mm"])
    full_rpm = pla_speed * 1000 / (pi * S["maximum_spool_outer_diameter_mm"])
    angle = max(abs(value) for value in S["dancer_angle_range_deg"])
    total_buffer = 4 * S["dancer_arm_length_mm"] * sin(radians(angle))
    return {
        "shaft_proof_load_n": proof_load,
        "shaft_max_bending_stress_mpa": stress,
        "shaft_safety_factor_at_250mpa_yield": 250 / stress,
        "shaft_center_deflection_mm": deflection,
        "pla_spool_rpm_core_to_full": [core_rpm, full_rpm],
        "torque_at_full_radius_for_target_tension_nm": S["dancer_target_tension_n"] * S["maximum_spool_outer_diameter_mm"] / 2000,
        "torque_limit_equivalent_full_spool_tension_n": S["spool_torque_limit_nm"] / (S["maximum_spool_outer_diameter_mm"] / 2000),
        "dancer_total_line_buffer_mm": total_buffer,
        "dancer_total_buffer_time_s_at_nominal_pla": total_buffer / (pla_speed * 1000 / 60),
        "traverse_speed_mm_min_core_to_full": [core_rpm * S["traverse_layer_pitch_mm"], full_rpm * S["traverse_layer_pitch_mm"]],
    }


def main() -> dict:
    result = {
        "status": "CALCULATED_NOT_PHYSICALLY_VALIDATED",
        "cooling": cooling(),
        "optical_gauge": optics(),
        "diameter_control": controller_simulation(),
        "spooler": spooler(),
        "limitations": [
            "Cooling properties and the cross-flow coefficient are screening assumptions; an instrumented strand test must measure center/shape stability.",
            "The delay model omits melt elasticity, neck-down location, tension propagation, roller compliance and camera processing jitter.",
            "Optical pixel scale is not measurement uncertainty; distortion, mirror pose, threshold, vibration and contamination require calibration.",
            "Spool shaft analysis excludes printed adapter creep, bearing-seat fit, frame torsion and resonance.",
        ],
    }
    output = ROOT / "simulation" / "forming" / "line_design.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
