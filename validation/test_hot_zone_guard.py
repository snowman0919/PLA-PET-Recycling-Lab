#!/usr/bin/env python3
"""Regression checks for hot-zone shield and nearby-polymer sensitivity gates."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calculations" / "thermal"))
from hot_zone_guard import build_report  # noqa: E402


def main() -> None:
    report = build_report()
    assert report["status"] == "SENSITIVITY_GATE_NOT_PHYSICAL_VALIDATION"
    assert report["design_change"]["extruder_insulation_current_mm"] == 50.0
    cases = {case["name"]: case for case in report["cases"]}
    assert len(cases) == 5

    nominal = cases["extruder_pet_ventilated"]
    assert 48.0 <= nominal["shield_equilibrium_c"] <= 50.0
    assert nominal["polymer_limit_pass"] and nominal["touch_target_pass"]

    baffled = cases["extruder_design_max_baffled"]
    assert baffled["polymer_equilibrium_c"] <= 45.0
    assert not baffled["touch_target_pass"]

    direct = cases["extruder_design_max_direct_view"]
    assert direct["polymer_equilibrium_c"] > 45.0
    assert direct["expected_disposition"] == "PROHIBITED_DIRECT_VIEW"

    dryer = cases["dryer_trip_direct_view"]
    assert dryer["polymer_limit_pass"] and not dryer["touch_target_pass"]
    assert max(case["energy_balance_residual_w"] for case in cases.values()) < 1e-6
    print("HOT_ZONE_GUARD_VALIDATION_OK")


if __name__ == "__main__":
    main()
