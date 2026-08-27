#!/usr/bin/env python3
"""Forced-response and transport-envelope calculation for the sorter proof."""

from __future__ import annotations

import json
from math import pi, sqrt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
G = 9.80665


def forced_response(params: dict, frequency_hz: float) -> dict[str, float]:
    mass = params["moving_mass_kg"]
    eccentric_mass = params["eccentric_mass_kg"]
    eccentric_radius = params["eccentric_radius_mm"] / 1000
    natural_omega = 2 * pi * params["isolator_natural_frequency_hz"]
    omega = 2 * pi * frequency_hz
    damping_ratio = params["damping_ratio"]
    stiffness = mass * natural_omega**2
    damping = 2 * damping_ratio * mass * natural_omega
    excitation = eccentric_mass * eccentric_radius * omega**2
    denominator = sqrt((stiffness - mass * omega**2) ** 2 + (damping * omega) ** 2)
    amplitude = excitation / denominator
    transmitted = amplitude * sqrt(stiffness**2 + (damping * omega) ** 2)
    return {
        "frequency_hz": frequency_hz,
        "speed_rpm": frequency_hz * 60,
        "excitation_force_peak_n": excitation,
        "amplitude_mm": amplitude * 1000,
        "acceleration_peak_g": amplitude * omega**2 / G,
        "velocity_peak_mm_s": amplitude * omega * 1000,
        "transmitted_force_peak_n": transmitted,
        "force_transmissibility": transmitted / excitation,
    }


def build_report() -> dict:
    params = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["vibratory_sorter"]
    if len(params["isolator_positions_mm"]) != params["isolator_count"]:
        raise ValueError("isolator position count differs from isolator_count")
    baseline_frequency = params["motor_speed_rpm"] / 60
    baseline = forced_response(params, baseline_frequency)
    active_length = params["screen_outer_length_mm"] - 2 * params["screen_border_x_mm"]
    fractions = params["transport_fraction_of_peak_velocity"]
    transport = [baseline["velocity_peak_mm_s"] * fraction for fraction in fractions]
    residence = [active_length / transport[1], active_length / transport[0]]
    mass_flow_g_s = params["stable_throughput_target_gph"] / 3600
    inventory = [mass_flow_g_s * value for value in residence]
    mass = params["moving_mass_kg"]
    total_stiffness = mass * (2 * pi * params["isolator_natural_frequency_hz"]) ** 2
    report = {
        "model": "single-degree-of-freedom force-excited moving tray",
        "assumptions": {
            "linear_isolators": True,
            "rigid_tray": True,
            "material_motion_fraction_is_empirical_range": fractions,
            "frame_modes_and_motor_harmonics_excluded": True,
        },
        "eccentric_moment_g_mm": params["eccentric_mass_kg"] * 1000 * params["eccentric_radius_mm"],
        "total_isolator_stiffness_n_m": total_stiffness,
        "per_isolator_stiffness_n_m": total_stiffness / params["isolator_count"],
        "static_deflection_mm": mass * G / total_stiffness * 1000,
        "baseline": {key: round(value, 5) for key, value in baseline.items()},
        "transport_velocity_mm_s_range": [round(x, 2) for x in transport],
        "active_deck_residence_s_range": [round(x, 2) for x in residence],
        "in_process_mass_at_200_gph_g_range": [round(x, 3) for x in inventory],
        "screen_nominal_open_area": {
            "top_6mm": round((params["top_screen_aperture_mm"] / params["top_screen_pitch_mm"]) ** 2, 4),
            "bottom_3mm": round((params["bottom_screen_aperture_mm"] / params["bottom_screen_pitch_mm"]) ** 2, 4),
        },
        "frequency_sweep": [
            {key: round(value, 5) for key, value in forced_response(params, frequency).items()}
            for frequency in (5, 8, 12, 20, 25, 30, 35, 40)
        ],
        "control_gates": [
            "Ramp through the 8 Hz isolator resonance without dwelling.",
            "Stop on isolator displacement, fastener migration, abnormal current or frame acceleration.",
            "Disable diameter/image measurement while sorter runs until measured camera-frame RMS is below 0.05 g.",
        ],
        "status": "CALCULATED_NOT_PHYSICALLY_VALIDATED",
    }
    return report


def main() -> None:
    report = build_report()
    path = ROOT / "simulation" / "vibration" / "vibratory_sorter_response.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
