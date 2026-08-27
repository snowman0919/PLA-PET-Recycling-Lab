#!/usr/bin/env python3
"""0.5-degree rotor sweep and assembly-interface checks for Stage 2."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = ROOT / "cad" / "freecad" / "shredder_stage2"
sys.path.insert(0, str(GEOMETRY))
from geometry import make_bearing, make_bed_knife, make_carrier, make_plate, make_retainer, make_rotor  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    params = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["stage2"]
    axial = params["axial_layout"]
    plate = params["plate"]
    cx, cy = plate["shaft_center_x_mm"], plate["shaft_center_y_mm"]
    rotor_base = make_rotor(params)
    bed_knife = make_bed_knife(params)
    min_clearance_mm = float("inf")
    minimum_angle_deg = None
    max_intersection_mm3 = 0.0
    samples = 721
    for index in range(samples):
        angle = index * 0.5
        rotor = rotor_base.copy()
        rotor.rotate(App.Vector(cx, cy, axial["rotor_z_mm"]), App.Vector(0, 0, 1), angle)
        distance = rotor.distToShape(bed_knife)[0]
        if distance < min_clearance_mm:
            min_clearance_mm = distance
            minimum_angle_deg = angle
        if distance < 1e-7:
            max_intersection_mm3 = max(max_intersection_mm3, rotor.common(bed_knife).Volume)

    left_plate = make_plate(params, axial["left_plate_z_mm"], True)
    right_plate = make_plate(params, axial["right_plate_z_mm"], False)
    left_bearing = make_bearing(params, axial["left_bearing_z_mm"])
    right_bearing = make_bearing(params, axial["right_bearing_z_mm"])
    left_retainer = make_retainer(params, axial["left_retainer_z_mm"])
    right_retainer = make_retainer(params, axial["right_retainer_z_mm"])
    carrier = make_carrier(params)
    rotor_to_left_plate_mm = rotor_base.distToShape(left_plate)[0]
    rotor_to_right_plate_mm = rotor_base.distToShape(right_plate)[0]
    carrier_to_left_plate_mm = carrier.distToShape(left_plate)[0]
    carrier_to_right_plate_mm = carrier.distToShape(right_plate)[0]
    knife_to_carrier_mm = bed_knife.distToShape(carrier)[0]
    contact_intersection_mm3 = max(
        carrier.common(left_plate).Volume,
        carrier.common(right_plate).Volume,
        bed_knife.common(carrier).Volume,
        left_retainer.common(left_bearing).Volume,
        right_retainer.common(right_bearing).Volume,
        left_bearing.common(left_plate).Volume,
        right_bearing.common(right_plate).Volume,
    )
    root_ligament_mm = params["rotor_core_diameter_mm"] / 2 - (
        params["shaft_diameter_mm"] / 2 - 0.4 + params["keyway_radial_depth_mm"] + 1.0
    )

    require(max_intersection_mm3 < 1e-7, f"rotor/bed-knife intersection {max_intersection_mm3} mm3")
    require(min_clearance_mm >= params["blade_clearance_mm"] - 0.005, f"blade clearance {min_clearance_mm:.3f} mm")
    require(min(rotor_to_left_plate_mm, rotor_to_right_plate_mm) >= 1.95, "rotor too close to side plate")
    require(max(carrier_to_left_plate_mm, carrier_to_right_plate_mm, knife_to_carrier_mm) < 1e-6, "intended structural contact missing")
    require(contact_intersection_mm3 < 1e-6, "intended Stage 2 contacts have solid intersection")
    require(root_ligament_mm >= 5.0, f"rotor keyway root ligament {root_ligament_mm:.3f} mm")

    report = {
        "phase_step_deg": 0.5,
        "phase_samples": samples,
        "min_rotor_to_bed_knife_clearance_mm": round(min_clearance_mm, 4),
        "minimum_clearance_angle_deg": minimum_angle_deg,
        "max_rotor_to_bed_knife_intersection_mm3": round(max_intersection_mm3, 8),
        "rotor_to_left_plate_mm": round(rotor_to_left_plate_mm, 4),
        "rotor_to_right_plate_mm": round(rotor_to_right_plate_mm, 4),
        "carrier_plate_contacts_mm": [round(carrier_to_left_plate_mm, 6), round(carrier_to_right_plate_mm, 6)],
        "bed_knife_carrier_contact_mm": round(knife_to_carrier_mm, 6),
        "contact_intersection_mm3": round(contact_intersection_mm3, 8),
        "rotor_keyway_root_ligament_mm": round(root_ligament_mm, 4),
        "status": "PASS",
        "limits": [
            "Rigid perfect geometry; runout, bearing play, shaft deflection and thermal growth are excluded.",
            "The 0.2 mm value is nominal and must be set with metal shims after measured tolerance stack.",
            "The fused rotor does not validate replaceable blade retention or dynamic balance.",
        ],
    }
    output = ROOT / "simulation" / "kinematic" / "stage2_rotor_sweep.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("STAGE2_KINEMATIC_VALIDATION_OK")


if __name__ == "__main__":
    main()
