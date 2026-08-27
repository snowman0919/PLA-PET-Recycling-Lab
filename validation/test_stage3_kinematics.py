#!/usr/bin/env python3
"""Stage-3 0.5-degree rotor/stator sweep and screen-family checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = ROOT / "cad" / "freecad" / "granulator_stage3"
sys.path.insert(0, str(GEOMETRY))
from geometry import make_bearing, make_carrier, make_plate, make_retainer, make_rotor, make_screen, make_stator  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["stage3"]
    a, plate = p["axial_layout"], p["plate"]
    cx, cy = plate["shaft_center_x_mm"], plate["shaft_center_y_mm"]
    rotor0, stator = make_rotor(p), make_stator(p)
    screen = make_screen(p, p["baseline_screen_opening_mm"])
    min_stator = float("inf")
    min_screen = float("inf")
    max_intersection = 0.0
    min_angle = None
    for index in range(721):
        angle = index * 0.5
        rotor = rotor0.copy()
        rotor.rotate(App.Vector(cx, cy, a["rotor_z_mm"]), App.Vector(0, 0, 1), angle)
        ds = rotor.distToShape(stator)[0]
        dg = rotor.distToShape(screen)[0]
        if ds < min_stator:
            min_stator, min_angle = ds, angle
        min_screen = min(min_screen, dg)
        if min(ds, dg) < 1e-7:
            max_intersection = max(max_intersection, rotor.common(stator).Volume, rotor.common(screen).Volume)

    left_plate = make_plate(p, a["left_plate_z_mm"], True)
    right_plate = make_plate(p, a["right_plate_z_mm"], False)
    carrier = make_carrier(p)
    left_bearing, right_bearing = make_bearing(p, a["left_bearing_z_mm"]), make_bearing(p, a["right_bearing_z_mm"])
    left_retainer, right_retainer = make_retainer(p, a["left_retainer_z_mm"]), make_retainer(p, a["right_retainer_z_mm"])
    contacts = [
        carrier.distToShape(left_plate)[0],
        carrier.distToShape(right_plate)[0],
        stator.distToShape(carrier)[0],
        left_retainer.distToShape(left_bearing)[0],
        right_retainer.distToShape(right_bearing)[0],
        left_bearing.distToShape(left_plate)[0],
        right_bearing.distToShape(right_plate)[0],
    ]
    contact_intersection = max(
        carrier.common(left_plate).Volume,
        carrier.common(right_plate).Volume,
        stator.common(carrier).Volume,
        left_retainer.common(left_bearing).Volume,
        right_retainer.common(right_bearing).Volume,
        left_bearing.common(left_plate).Volume,
        right_bearing.common(right_plate).Volume,
    )
    rotor_plate_gaps = [rotor0.distToShape(left_plate)[0], rotor0.distToShape(right_plate)[0]]
    root_ligament = p["rotor_core_diameter_mm"] / 2 - (
        p["shaft_diameter_mm"] / 2 - 0.4 + p["keyway_radial_depth_mm"] + 1.0
    )
    max_opening = max(p["screen_opening_candidates_mm"])
    pitch_web = p["screen_pitch_mm"] - max_opening
    screen_edge_web = min(p["screen_edge_margin_x_mm"], p["screen_edge_margin_z_mm"]) - max_opening / 2
    candidate_volumes = {f"{int(o)}mm": round(make_screen(p, o).Volume, 3) for o in p["screen_opening_candidates_mm"]}

    require(max_intersection < 1e-7, f"rotor fixed-part intersection {max_intersection} mm3")
    require(min_stator >= p["blade_clearance_mm"] - 0.005, f"stator clearance {min_stator:.3f} mm")
    require(min_screen >= p["screen_rotor_gap_mm"] - 0.005, f"screen gap {min_screen:.3f} mm")
    require(min(rotor_plate_gaps) >= 1.95, "rotor too close to side plate")
    require(max(contacts) < 1e-6 and contact_intersection < 1e-6, "invalid intended structural contact")
    require(root_ligament >= 4.5, f"keyway root ligament {root_ligament:.3f} mm")
    require(pitch_web >= 2.0 and screen_edge_web >= 1.0, "6 mm screen web too small")
    require(candidate_volumes["4mm"] > candidate_volumes["5mm"] > candidate_volumes["6mm"], "screen opening family volume order invalid")

    report = {
        "phase_step_deg": 0.5,
        "phase_samples": 721,
        "min_rotor_stator_clearance_mm": round(min_stator, 4),
        "minimum_clearance_angle_deg": min_angle,
        "min_rotor_screen_gap_mm": round(min_screen, 4),
        "max_fixed_part_intersection_mm3": round(max_intersection, 8),
        "rotor_plate_gaps_mm": [round(x, 4) for x in rotor_plate_gaps],
        "intended_contact_intersection_mm3": round(contact_intersection, 8),
        "rotor_keyway_root_ligament_mm": round(root_ligament, 4),
        "screen_6mm_pitch_web_mm": round(pitch_web, 4),
        "screen_6mm_min_edge_web_mm": round(screen_edge_web, 4),
        "screen_candidate_solid_volumes_mm3": candidate_volumes,
        "status": "PASS",
        "limits": [
            "Rigid perfect geometry excludes runout, deflection, thermal growth and flake wedging.",
            "Flat screen is unsupported proof geometry, not fatigue-qualified containment.",
            "Nominal 0.15 mm stator clearance requires measured metal shims.",
        ],
    }
    path = ROOT / "simulation" / "kinematic" / "stage3_rotor_screen_sweep.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("STAGE3_KINEMATIC_VALIDATION_OK")


if __name__ == "__main__":
    main()
