#!/usr/bin/env python3
"""Decision gates for the analytical extruder sweep."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calculations" / "extruder"))
from screw_design import main  # noqa: E402


def run() -> None:
    result = main()
    sweep = {row["diameter_mm"]: row for row in result["diameter_sweep"]}
    selected = result["selection"]
    structure = result["structure"]
    die = result["die"]

    assert not sweep[12.0]["passes_required_model_margin"]
    assert not sweep[14.0]["passes_required_model_margin"]
    assert not sweep[16.0]["passes_required_model_margin"]
    assert sweep[18.0]["passes_required_model_margin"]
    assert selected["diameter_mm"] == 18.0
    assert selected["worst_normal_output_gph_at_45rpm"] >= 250.0
    assert 20.0 <= selected["nominal_rpm_for_200_gph"] <= 45.0
    assert selected["metering_wall_shear_rate_s_at_45rpm"] < 50.0
    assert 3.0 <= selected["residence_time_min_at_35_to_60pct_fill"][0]
    assert selected["residence_time_min_at_35_to_60pct_fill"][1] <= 10.0
    assert max(die["capillary_only_pressure_mpa_by_viscosity_at_20s"].values()) < die["clean_system_pressure_budget_mpa"]
    assert 2.9 <= die["area_drawdown_ratio_3mm_to_1_75mm"] <= 3.0
    assert 0.9 <= die["final_filament_line_speed_m_min_at_200gph"]["pet"] <= 1.1
    assert 1.0 <= die["final_filament_line_speed_m_min_at_200gph"]["pla"] <= 1.2
    assert structure["51102_static_safety_factor_at_proof"] >= 3.0
    assert structure["screw_root_safety_factor"] >= 3.0
    assert structure["barrel_hot_safety_factor"] >= 2.0
    assert result["thermal"]["profiles"]["pet"]["steady_heater_duty"] < 0.35
    assert result["drive"]["electrical_input_w_at_75pct_efficiency"] < 130.0
    assert max(result["power_arbitration"]["modes"].values()) <= result["power_arbitration"]["temporary_usable_ceiling_w_at_90pct"]
    print("EXTRUDER_DESIGN_SWEEP_OK")


if __name__ == "__main__":
    run()
