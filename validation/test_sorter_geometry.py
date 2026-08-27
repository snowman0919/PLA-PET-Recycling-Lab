#!/usr/bin/env python3
"""Clearance and structural-contact checks for the sorter proof."""

from __future__ import annotations

import json
import sys
from math import cos, radians
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "freecad" / "vibratory_sorter"))
from geometry import (  # noqa: E402
    make_base,
    make_eccentric,
    make_fines_bin,
    make_isolators,
    make_motor,
    make_motor_bracket,
    make_tray_frame,
)


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["vibratory_sorter"]
    shapes = {
        "base": make_base(p),
        "isolators": make_isolators(p),
        "frame": make_tray_frame(p),
        "motor": make_motor(p),
        "bracket": make_motor_bracket(p),
        "eccentric": make_eccentric(p),
        "fines_bin": make_fines_bin(p),
    }

    def pair(a: str, b: str) -> dict[str, float]:
        return {
            "distance_mm": shapes[a].distToShape(shapes[b])[0],
            "intersection_mm3": shapes[a].common(shapes[b]).Volume,
        }

    checks = {
        "isolator_to_frame": pair("isolators", "frame"),
        "motor_to_bracket": pair("motor", "bracket"),
        "motor_to_base": pair("motor", "base"),
        "bracket_to_base": pair("bracket", "base"),
        "motor_to_fines_bin": pair("motor", "fines_bin"),
        "eccentric_to_bracket": pair("eccentric", "bracket"),
    }
    deck_normal_separation = p["deck_spacing_mm"] - p["screen_thickness_mm"]
    deck_vertical_separation = p["deck_spacing_mm"] * cos(radians(p["tray_slope_deg"]))
    motion_allowance = 2 * 0.40 + 2.0
    assert checks["isolator_to_frame"]["distance_mm"] < 0.01, checks["isolator_to_frame"]
    assert checks["motor_to_bracket"]["distance_mm"] < 0.01, checks["motor_to_bracket"]
    for name in ("motor_to_base", "bracket_to_base", "motor_to_fines_bin", "eccentric_to_bracket"):
        assert checks[name]["distance_mm"] >= motion_allowance, (name, checks[name])
        assert checks[name]["intersection_mm3"] < 1e-7, (name, checks[name])
    assert deck_normal_separation >= 30.0
    assert p["top_screen_pitch_mm"] - p["top_screen_aperture_mm"] >= 1.5
    assert p["bottom_screen_pitch_mm"] - p["bottom_screen_aperture_mm"] >= 2.0
    report = {
        "motion_clearance_allowance_mm": motion_allowance,
        "checks": {
            name: {key: round(value, 5) for key, value in result.items()}
            for name, result in checks.items()
        },
        "deck_normal_clearance_mm": round(deck_normal_separation, 5),
        "deck_vertical_pitch_mm": round(deck_vertical_separation, 5),
        "top_screen_wire_mm": p["top_screen_pitch_mm"] - p["top_screen_aperture_mm"],
        "bottom_screen_wire_mm": p["bottom_screen_pitch_mm"] - p["bottom_screen_aperture_mm"],
        "status": "PASS",
        "limits": [
            "Nominal rigid geometry does not replace one-isolator-failed or startup resonance testing.",
            "Motor bracket contact is an envelope; sourced motor mounting face and bolts are not modeled.",
            "Flexible chute boots and wiring service loops are not modeled.",
        ],
    }
    path = ROOT / "simulation" / "vibration" / "vibratory_sorter_geometry.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("SORTER_GEOMETRY_OK")


if __name__ == "__main__":
    main()
