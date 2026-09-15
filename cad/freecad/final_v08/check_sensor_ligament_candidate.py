#!/usr/bin/env python3
"""센서 flat-tip/편심/축 기울기의 BRep 거리 비교. 고온 강도/프로브 검증 아님."""
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]


def main():
    radius, melt_radius, sensor_radius, offset = 16.985, 8.11, 1.625, .05
    theta = math.atan(.10 / 5.5)
    melt = Part.makeCylinder(melt_radius, 280, App.Vector(0, offset, 0))
    rows = []
    for nominal_depth in (5.50, 5.40, 5.30):
        depth = nominal_depth + .05
        distances = []
        for angle in (-theta, 0, theta):
            axis = App.Vector(0, -math.cos(angle), math.sin(angle))
            sensor = Part.makeCylinder(sensor_radius, depth, App.Vector(0, radius, 170), axis)
            assert sensor.isValid() and melt.isValid()
            actual = sensor.distToShape(melt)[0]
            exact = radius - depth * math.cos(angle) - sensor_radius * abs(math.sin(angle)) - offset - melt_radius
            assert abs(actual - exact) < 1e-6, (actual, exact)
            distances.append(actual)
        conservative = radius - depth - offset - melt_radius - sensor_radius * math.sin(theta)
        assert conservative <= min(distances) + 1e-6
        rows.append({"nominal_depth_mm": nominal_depth, "depth_tolerance_mm": .05,
                     "brep_min_ligament_mm": min(distances), "conservative_bound_mm": conservative,
                     "required_minimum_mm": 3.32, "flat_tip_geometry_check": "PASS" if min(distances) >= 3.32 else "FAIL"})
    assert rows[0]["flat_tip_geometry_check"] == "FAIL"
    assert rows[1]["flat_tip_geometry_check"] == "PASS"
    drill_cases = []
    # Explicit geometric scenarios, not a claim about a supplier's selected tool.
    for included_angle in (118, 135):
        tip_length = sensor_radius / math.tan(math.radians(included_angle / 2))
        for depth_definition in ("full_diameter_depth", "deepest_tip_depth"):
            specified_max_depth = 5.45
            cylinder_length = specified_max_depth - (tip_length if depth_definition == "deepest_tip_depth" else 0)
            distances = []
            for tilt in (-theta, 0, theta):
                start = App.Vector(0, radius, 170)
                axis = App.Vector(0, -math.cos(tilt), math.sin(tilt))
                cylinder = Part.makeCylinder(sensor_radius, cylinder_length, start, axis)
                cone = Part.makeCone(sensor_radius, 0, tip_length, start + axis * cylinder_length, axis)
                hole = cylinder.fuse(cone)
                assert hole.isValid() and len(hole.Solids) == 1
                gap = hole.distToShape(melt)[0]
                if tilt == 0:
                    exact = radius - cylinder_length - tip_length - offset - melt_radius
                    assert abs(gap - exact) < 1e-6
                    probe = Part.makeCylinder(1.525, 5.25, start, axis)
                    probe_collision = probe.cut(hole).Volume
                distances.append(gap)
            drill_cases.append({"included_angle_deg": included_angle, "depth_definition": depth_definition,
                                "specified_max_depth_mm": specified_max_depth, "tip_length_mm": tip_length,
                                "full_diameter_depth_mm": cylinder_length, "minimum_ligament_mm": min(distances),
                                "flat_probe_insertion_mm": 5.25,
                                "flat_probe_outside_hole_volume_mm3": probe_collision,
                                "flat_probe_fit_check": "PASS" if probe_collision < 1e-7 else "FAIL",
                                "geometry_check": "PASS" if min(distances) >= 3.32 else "FAIL"})
    assert all(r["geometry_check"] == ("FAIL" if r["depth_definition"] == "full_diameter_depth" else "PASS") for r in drill_cases)
    assert all(r["flat_probe_fit_check"] == ("PASS" if r["depth_definition"] == "full_diameter_depth" else "FAIL") for r in drill_cases)
    # Proposed insertion and sheath envelope, not dimensions of a received probe.
    # The probe and bore must share an axis; an axial stop alone is insufficient.
    probe_fit = []
    hole = Part.makeCylinder(1.60, 5.35)
    for relative_angle in (0, theta, 2 * theta):
        probe = Part.makeCylinder(1.525, 5.25, App.Vector(),
                                  App.Vector(math.sin(relative_angle), 0, math.cos(relative_angle)))
        # The part above the entry plane is outside the barrel, not interference.
        inserted = probe.common(Part.makeBox(20, 20, 10, App.Vector(-10, -10, 0)))
        collision = inserted.cut(hole).Volume
        probe_fit.append({"relative_axis_angle_deg": math.degrees(relative_angle),
                          "outside_hole_volume_mm3": collision,
                          "geometry_check": "PASS" if collision < 1e-7 else "FAIL"})
    assert probe_fit[0]["geometry_check"] == "PASS"
    assert probe_fit[-1]["geometry_check"] == "FAIL"
    guide_angle = math.radians(.5)
    guide_offset = .02
    # Triangle inequality bounds every azimuth, not merely the sampled plane.
    radial_margin = 1.60 - (1.525 + guide_offset + 5.25 * math.sin(guide_angle))
    bottom_margin = 5.35 - (5.25 + 1.525 * math.sin(guide_angle))
    assert radial_margin > 0 and bottom_margin > 0
    guide_samples = []
    for shift in (-guide_offset, guide_offset):
        for angle in (-guide_angle, guide_angle):
            probe = Part.makeCylinder(1.525, 5.25, App.Vector(shift, 0, 0),
                                      App.Vector(math.sin(angle), 0, math.cos(angle)))
            inserted = probe.common(Part.makeBox(20, 20, 10, App.Vector(-10, -10, 0)))
            collision = inserted.cut(hole).Volume
            assert collision < 1e-7
            guide_samples.append({"offset_mm": shift, "relative_angle_deg": math.degrees(angle),
                                  "outside_hole_volume_mm3": collision})
    short_conical = []
    for included_angle in (118, 135):
        slope = math.tan(math.radians(included_angle / 2))
        tip_length = 1.60 / slope
        cylindrical_depth = 5.35 - tip_length
        conical_hole = Part.makeCylinder(1.60, cylindrical_depth).fuse(
            Part.makeCone(1.60, 0, tip_length, App.Vector(0, 0, cylindrical_depth)))
        # Bounding cylinder contains all azimuths of the tilted/offset probe.
        radial_bound = 1.525 + guide_offset + 4.25 * math.sin(guide_angle)
        axial_bound = 4.25 + 1.525 * math.sin(guide_angle)
        cone_axial_margin = 5.35 - radial_bound / slope - axial_bound
        assert radial_bound < 1.60 and cone_axial_margin > .10
        collisions = []
        for shift in (-guide_offset, guide_offset):
            for angle in (-guide_angle, guide_angle):
                probe = Part.makeCylinder(1.525, 4.25, App.Vector(shift, 0, 0),
                                          App.Vector(math.sin(angle), 0, math.cos(angle)))
                inserted = probe.common(Part.makeBox(20, 20, 10, App.Vector(-10, -10, 0)))
                collisions.append(inserted.cut(conical_hole).Volume)
        assert conical_hole.isValid() and max(collisions) < 1e-7
        short_conical.append({"drill_angle_deg": included_angle,
                              "minimum_deepest_tip_depth_mm": 5.35,
                              "insertion_candidate_mm": [4.15, 4.25],
                              "radial_margin_bound_mm": 1.60 - radial_bound,
                              "cone_axial_margin_bound_mm": cone_axial_margin,
                              "corner_collision_volumes_mm3": collisions,
                              "geometry_check": "PASS", "status": "HOLD"})
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN", "cases": rows,
              "short_conical_insertion_candidate": short_conical,
              "guide_error_allocation_candidate": {"maximum_radial_axis_offset_mm": guide_offset,
                  "maximum_relative_axis_angle_deg": .5, "radial_margin_lower_bound_mm": radial_margin,
                  "bottom_margin_lower_bound_mm": bottom_margin, "brep_corner_checks": guide_samples,
                  "status": "HOLD", "scope": "Cold geometric envelope only; measured relative to actual bore axis, not barrel datum. No guide geometry, stiffness, thermal expansion or retention qualification."},
              "drill_tip_scenarios": drill_cases,
              "probe_insertion_candidate": {"insertion_mm": [5.15, 5.25], "sheath_max_diameter_mm": 3.05,
                  "bore_depth_mm": [5.35, 5.45], "coaxial_bottom_gap_mm": [.10, .30],
                  "relative_axis_sweep": probe_fit,
                  "status": "HOLD", "basis": "Proposed5.20±0.05 insertion and3.05 maximum sheath, not received donor data. Metal retention/axis guidance and hot response unqualified."},
              "freecad_version": ".".join(App.Version()[:3]),
              "assumptions": {"full_axis_offset_mm": offset, "tilt_rad": theta,
                              "sensor_tip": "flat plane normal to sensor axis, per current CAD cylinder; no drill cone"},
              "limitations": ["Current perpendicularity/concentricity notation needs unambiguous datum interpretation.",
                              "Depth5.40 is a design candidate only; probe insertion/retention/thermal response must be checked.",
                              "Drill deepest-tip depth preserves ligament but conflicts with the proposed flat-ended probe insertion; flat-bottom fit evidence cannot qualify a conical bore.",
                              "Current assembly probe insertion5.50 exceeds candidate minimum depth5.35 by0.15 mm; do not adopt the bore alone.",
                              "Tip radius, local stress and elevated-temperature material remain unqualified."],
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  (Path(__file__).resolve(), ROOT / "cad/freecad/compact/manufacturing.py", ROOT / "cad/freecad/compact/geometry.py", ROOT / "cad/generation/generate_manufacturing.py")}}
    path = ROOT / "analysis/final_validation/results/v0.8/sensor_ligament_candidate.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print("SENSOR_LIGAMENT_BREP_CHECK_PASS", json.dumps(rows))


if __name__ == "__main__":
    main()
