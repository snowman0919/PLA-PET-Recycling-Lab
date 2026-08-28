#!/usr/bin/env python3
"""Decision gates for the cooling, gauge, puller and spooler design model."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calculations" / "forming"))
from line_design import main  # noqa: E402


def run() -> None:
    result = main()
    assert all(case["passes_tunnel"] for case in result["cooling"].values()), result["cooling"]
    assert result["optical_gauge"]["adc_counts_across_1_75mm"] >= 700.0
    assert result["optical_gauge"]["ideal_mm_per_count"] <= 0.0025
    control = result["diameter_control"]
    selected = control["feedforward_smith_pi"]
    assert selected["rms_error_after_120s_mm"] < control["aggressive_pid"]["rms_error_after_120s_mm"]
    assert selected["rms_error_after_120s_mm"] < control["filtered_pi"]["rms_error_after_120s_mm"]
    assert selected["maximum_absolute_error_mm"] <= 0.05
    assert selected["time_outside_initial_tolerance_s"] == 0.0
    spool = result["spooler"]
    assert spool["shaft_safety_factor_at_250mpa_yield"] >= 5.0
    assert spool["shaft_center_deflection_mm"] <= 0.05
    assert 0.5 <= spool["pla_spool_rpm_core_to_full"][1]
    assert spool["pla_spool_rpm_core_to_full"][0] <= 4.0
    assert spool["torque_limit_equivalent_full_spool_tension_n"] <= 3.0
    print("FORMING_LINE_DESIGN_OK")


if __name__ == "__main__":
    run()
