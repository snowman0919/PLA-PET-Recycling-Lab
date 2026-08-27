#!/usr/bin/env python3
"""Clearance checks for the high-temperature dryer/feeder proof."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "freecad" / "dryer_feeder"))
from geometry import make_agitator, make_auger, make_auger_housing, make_base_and_load_cells, make_heat_shield, make_hopper, make_insulation  # noqa: E402


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["dryer_feeder"]
    hopper, insulation, shield = make_hopper(p), make_insulation(p), make_heat_shield(p)
    agitator, auger, housing = make_agitator(p), make_auger(p), make_auger_housing(p)
    support = make_base_and_load_cells(p)
    auger_common = auger.common(housing)
    checks = {
        "agitator_to_hopper_mm": agitator.distToShape(hopper)[0],
        "agitator_hopper_intersection_mm3": agitator.common(hopper).Volume,
        "auger_to_housing_mm": auger.distToShape(housing)[0],
        "auger_housing_intersection_mm3": auger_common.Volume,
        "support_to_housing_mm": support.distToShape(housing)[0],
        "insulation_to_shield_mm": insulation.distToShape(shield)[0],
        "insulation_shield_intersection_mm3": insulation.common(shield).Volume,
        "paddle_radial_clearance_mm": p["hopper_inner_diameter_mm"] / 2 - p["agitator_paddle_radius_mm"],
        "auger_radial_clearance_mm": p["auger_housing_inner_diameter_mm"] / 2 - p["auger_outer_diameter_mm"] / 2,
    }
    assert checks["agitator_hopper_intersection_mm3"] < 1e-7, checks
    assert checks["auger_housing_intersection_mm3"] < 1e-7, checks
    assert checks["support_to_housing_mm"] < 1e-7, checks
    assert checks["insulation_shield_intersection_mm3"] < 1e-7, checks
    assert checks["paddle_radial_clearance_mm"] >= 15.0
    assert checks["auger_radial_clearance_mm"] >= 2.0
    assert checks["insulation_to_shield_mm"] >= p["shield_air_gap_mm"] - 0.01
    report = {
        "checks": {key: round(value, 5) for key, value in checks.items()},
        "status": "PASS",
        "limits": [
            "Rigid nominal geometry excludes shaft runout, thermal expansion, flake wedging and seal drag.",
            "Ring flights are pitch envelopes and do not prove continuous-auger transport.",
            "Insulation compression, hot bridges and guard deflection require physical measurement.",
        ],
    }
    path = ROOT / "simulation" / "thermal" / "dryer_feeder_geometry.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("DRYER_GEOMETRY_OK")


if __name__ == "__main__":
    main()
