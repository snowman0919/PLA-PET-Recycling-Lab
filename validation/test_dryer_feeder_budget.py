#!/usr/bin/env python3
"""Regression checks for dryer heat and feed sizing."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calculations" / "thermal"))
from dryer_feeder import build_report  # noqa: E402


def main() -> None:
    r = build_report()
    assert 2.0 <= r["hopper_geometric_volume_l"] <= 2.2
    assert r["hopper_bulk_capacity_kg"] >= 0.5
    assert abs(r["residence_at_target_gph_h"] - 5.0) < 1e-9
    assert r["pla"]["steady_heater_duty"] < 0.2
    assert r["pet"]["steady_heater_duty"] < 0.25
    assert 1.5 <= r["auger"]["rpm_for_target_gph"] <= 2.0
    assert r["pet_profile_gate"]["maximum_dew_point_c"] <= -40
    print(r)
    print("DRYER_FEEDER_BUDGET_OK")


if __name__ == "__main__":
    main()
