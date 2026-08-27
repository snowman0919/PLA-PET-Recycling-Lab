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
    assert 4.8 <= r["hopper_geometric_volume_l"] <= 5.1
    assert r["hopper_bulk_capacity_kg"] >= 1.2
    assert abs(r["residence_at_200_gph_h"] - 6.0) < 1e-9
    assert r["pla"]["steady_heater_duty"] < 0.2
    assert r["pet"]["steady_heater_duty"] < 0.25
    assert 3.0 <= r["auger"]["rpm_for_200_gph"] <= 4.0
    assert r["pet_profile_gate"]["maximum_dew_point_c"] <= -40
    print(r)
    print("DRYER_FEEDER_BUDGET_OK")


if __name__ == "__main__":
    main()
