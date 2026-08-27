#!/usr/bin/env python3
"""Thermal inventory and auger-feed screening for the dryer/feeder."""

from __future__ import annotations

import json
from math import log, pi
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def heat_loss(params: dict, temperature_c: float) -> float:
    radius_inner = params["hopper_inner_diameter_mm"] / 2000
    radius_outer = radius_inner + params["insulation_thickness_mm"] / 1000
    height = params["hopper_active_height_mm"] / 1000
    conductivity = params["insulation_conductivity_w_mk"]
    delta = temperature_c - params["ambient_temperature_c"]
    cylindrical = 2 * pi * conductivity * height * delta / log(radius_outer / radius_inner)
    end_area = pi * radius_inner**2
    ends = 2 * conductivity * end_area * delta / (params["insulation_thickness_mm"] / 1000)
    return (cylindrical + ends) * params["thermal_bridge_factor"]


def thermal_profile(params: dict, setpoint_c: float, heater_power_w: float) -> dict[str, float]:
    delta = setpoint_c - params["ambient_temperature_c"]
    resin_capacity = params["design_inventory_kg"] * 1200
    metal_capacity = params["hopper_metal_mass_kg"] * 500
    energy = (resin_capacity + metal_capacity) * delta
    loss = heat_loss(params, setpoint_c)
    average_net = heater_power_w - loss / 2
    mass_flow_kg_s = params["stable_mass_flow_gph"] / 1000 / 3600
    feed_heating = mass_flow_kg_s * 1200 * delta
    return {
        "sensible_energy_kj": energy / 1000,
        "steady_heat_loss_w": loss,
        "continuous_cold_feed_heating_w": feed_heating,
        "ideal_ramp_minutes": energy / average_net / 60,
        "steady_heater_duty": (loss + feed_heating) / heater_power_w,
    }


def build_report() -> dict:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["dryer_feeder"]
    volume = pi * (p["hopper_inner_diameter_mm"] / 2000) ** 2 * (p["hopper_active_height_mm"] / 1000)
    bulk_capacity = volume * p["flake_bulk_density_kg_m3"]
    residence = p["design_inventory_kg"] / (p["stable_mass_flow_gph"] / 1000)
    auger_area = pi / 4 * (p["auger_outer_diameter_mm"] ** 2 - p["auger_shaft_diameter_mm"] ** 2)
    displacement_cm3_rev = auger_area * p["auger_pitch_mm"] / 1000
    grams_per_rev = displacement_cm3_rev * (p["flake_bulk_density_kg_m3"] / 1000) * p["auger_fill_fraction"]
    feed_rpm = (p["stable_mass_flow_gph"] / 60) / grams_per_rev
    report = {
        "hopper_geometric_volume_l": volume * 1000,
        "hopper_bulk_capacity_kg": bulk_capacity,
        "design_inventory_kg": p["design_inventory_kg"],
        "residence_at_200_gph_h": residence,
        "pla": thermal_profile(p, p["pla_profile"]["setpoint_c"], p["pla_profile"]["heater_power_w"]),
        "pet": thermal_profile(p, p["pet_profile"]["dry_setpoint_c"], p["pet_profile"]["heater_power_w"]),
        "auger": {
            "theoretical_displacement_cm3_rev": displacement_cm3_rev,
            "assumed_grams_per_rev": grams_per_rev,
            "rpm_for_200_gph": feed_rpm,
            "configured_range_rpm": p["auger_speed_range_rpm"],
        },
        "pet_profile_gate": {
            "preheat": f"{p['pet_profile']['preheat_setpoint_c']:.0f} C for {p['pet_profile']['preheat_hours']:.0f} h",
            "dry": f"{p['pet_profile']['dry_setpoint_c']:.0f} C for {p['pet_profile']['dry_hours']:.0f} h",
            "maximum_dew_point_c": p["pet_profile"]["dry_air_dew_point_max_c"],
            "target_moisture_ppm": p["pet_profile"]["moisture_target_ppm"],
            "note": "PET profile is not approved until crystallization/agglomeration and outlet moisture are physically verified.",
        },
        "status": "CALCULATED_NOT_PHYSICALLY_VALIDATED",
    }
    return report


def main() -> None:
    report = build_report()
    path = ROOT / "simulation" / "thermal" / "dryer_feeder_budget.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
