#!/usr/bin/env python3
"""1-degree counter-rotation and fabrication-envelope checks for Stage 1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = ROOT / "cad" / "freecad" / "shredder_stage1"
sys.path.insert(0, str(GEOMETRY))
from geometry import make_bearing, make_cutter, make_plate, make_retainer, make_spacer, make_timing_envelope  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rotated(shape, center, degrees):
    result = shape.copy()
    result.rotate(App.Vector(center[0], center[1], 0), App.Vector(0, 0, 1), degrees)
    return result


def main() -> None:
    params = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["stage1"]
    axial = params["axial_layout"]
    center_a, center_b = (50.0, 60.0), (100.0, 60.0)
    cutter_t = params["cutter_thickness_mm"]
    spacer_t = params["spacer_thickness_mm"]
    clearance = params["axial_cutter_clearance_mm"]

    cutter_a_base = make_cutter(params, center_a, 0.0, 0.0)
    cutter_b_base = make_cutter(params, center_b, spacer_t - clearance, 0.0)
    spacer_b_same_lane = make_spacer(params, center_b, -clearance)
    spacer_a_next_lane = make_spacer(params, center_a, cutter_t)

    min_adjacent_cutter_mm = float("inf")
    min_cutter_spacer_mm = float("inf")
    max_intersection_mm3 = 0.0
    minimum_angle = None
    for angle in range(361):
        cutter_a = rotated(cutter_a_base, center_a, angle)
        cutter_b = rotated(cutter_b_base, center_b, params["phase_offset_deg"] - angle)
        adjacent_distance = cutter_a.distToShape(cutter_b)[0]
        radial_a = cutter_a.distToShape(spacer_b_same_lane)[0]
        radial_b = cutter_b.distToShape(spacer_a_next_lane)[0]
        local_min = min(radial_a, radial_b)
        if adjacent_distance < min_adjacent_cutter_mm:
            min_adjacent_cutter_mm = adjacent_distance
            minimum_angle = angle
        min_cutter_spacer_mm = min(min_cutter_spacer_mm, local_min)
        if adjacent_distance < 1e-7:
            max_intersection_mm3 = max(max_intersection_mm3, cutter_a.common(cutter_b).Volume)

    left_plate = make_plate(params, axial["left_plate_z_mm"], True)
    right_plate = make_plate(params, axial["right_plate_z_mm"], False)
    first_cutter = make_cutter(params, center_a, 0.0, 0.0)
    pair_pitch = cutter_t + spacer_t
    last_b_cutter_z = (params["cutter_count_per_shaft"] - 1) * pair_pitch - clearance + spacer_t
    last_b_cutter = make_cutter(params, center_b, last_b_cutter_z, params["phase_offset_deg"])
    plate_gap_left = first_cutter.distToShape(left_plate)[0]
    plate_gap_right = last_b_cutter.distToShape(right_plate)[0]

    plate_web_mm = params["shaft_center_distance_mm"] - params["plate"]["counterbore_mm"]
    root_ligament_mm = params["cutter_root_diameter_mm"] / 2 - (
        params["shaft_diameter_mm"] / 2 - 0.4 + params["keyway_radial_depth_mm"] + 1.0
    )
    timing_gap_mm = params["shaft_center_distance_mm"] - params["timing_pitch_envelope_diameter_mm"]

    right_retainer = make_retainer(params, axial["right_retainer_z_mm"])
    timing_envelope = make_timing_envelope(params, center_a, axial["timing_envelope_z_mm"])
    support_retainer = make_retainer(params, axial["timing_support_retainer_z_mm"])
    support_bearing = make_bearing(params, center_a, axial["timing_support_bearing_z_mm"])
    support_plate = make_plate(params, axial["timing_support_plate_z_mm"], True)
    right_retainer_to_timing_mm = right_retainer.distToShape(timing_envelope)[0]
    timing_to_support_retainer_mm = timing_envelope.distToShape(support_retainer)[0]
    support_retainer_to_bearing_mm = support_retainer.distToShape(support_bearing)[0]
    support_bearing_to_plate_mm = support_bearing.distToShape(support_plate)[0]
    support_contact_intersection_mm3 = max(
        support_retainer.common(support_bearing).Volume,
        support_bearing.common(support_plate).Volume,
    )

    require(max_intersection_mm3 < 1e-7, f"cutter intersection {max_intersection_mm3} mm3")
    require(min_adjacent_cutter_mm >= clearance - 0.005, f"adjacent cutter gap {min_adjacent_cutter_mm:.3f} mm")
    require(min_cutter_spacer_mm >= 0.8, f"hook-to-spacer radial gap {min_cutter_spacer_mm:.3f} mm")
    require(min(plate_gap_left, plate_gap_right) >= 1.0, "cutter stack too close to bearing plate")
    require(plate_web_mm >= 8.0, f"bearing counterbore web {plate_web_mm:.3f} mm")
    require(root_ligament_mm >= 5.0, f"cutter keyway root ligament {root_ligament_mm:.3f} mm")
    require(timing_gap_mm >= 1.0, f"timing pitch-envelope gap {timing_gap_mm:.3f} mm")
    require(right_retainer_to_timing_mm >= 0.25, "right retainer too close to timing envelope")
    require(timing_to_support_retainer_mm >= 0.45, "timing envelope too close to support retainer")
    require(support_retainer_to_bearing_mm < 1e-6, "support retainer does not contact bearing")
    require(support_bearing_to_plate_mm < 1e-6, "support bearing does not seat in plate")
    require(support_contact_intersection_mm3 < 1e-6, "intended support contacts have solid intersection")

    report = {
        "phase_step_deg": 1,
        "phase_samples": 361,
        "phase_offset_deg": params["phase_offset_deg"],
        "min_adjacent_cutter_gap_mm": round(min_adjacent_cutter_mm, 4),
        "minimum_gap_angle_deg": minimum_angle,
        "max_cutter_intersection_mm3": round(max_intersection_mm3, 8),
        "min_hook_to_opposite_spacer_gap_mm": round(min_cutter_spacer_mm, 4),
        "plate_gap_left_mm": round(plate_gap_left, 4),
        "plate_gap_right_mm": round(plate_gap_right, 4),
        "counterbore_center_web_mm": round(plate_web_mm, 4),
        "cutter_keyway_root_ligament_mm": round(root_ligament_mm, 4),
        "timing_pitch_envelope_gap_mm": round(timing_gap_mm, 4),
        "right_retainer_to_timing_gap_mm": round(right_retainer_to_timing_mm, 4),
        "timing_to_support_retainer_gap_mm": round(timing_to_support_retainer_mm, 4),
        "support_retainer_to_bearing_contact_mm": round(support_retainer_to_bearing_mm, 6),
        "support_bearing_to_plate_contact_mm": round(support_bearing_to_plate_mm, 6),
        "support_contact_intersection_mm3": round(support_contact_intersection_mm3, 8),
        "status": "PASS",
        "limits": [
            "Rigid perfect geometry; shaft/cutter runout and deflection are not included.",
            "Timing cylinders are pitch envelopes, not real gear teeth.",
            "Nominal zero gaps at retainer/bearing and bearing/counterbore are intended seats, not running interfaces.",
            "The 0.3/0.5 mm gear-side values are nominal CAD gaps; tolerance stack and thermal growth remain unverified.",
            "0.2 mm axial gap must be established by ground spacers/shims, not FDM tolerance.",
        ],
    }
    output = ROOT / "simulation" / "kinematic" / "stage1_clearance_sweep.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("STAGE1_KINEMATIC_VALIDATION_OK")


if __name__ == "__main__":
    main()
