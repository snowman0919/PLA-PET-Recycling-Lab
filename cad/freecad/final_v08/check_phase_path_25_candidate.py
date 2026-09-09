#!/usr/bin/env python3
"""Released 25 mm shaft/61905/matched-key phase path."""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
from geometry import cycloidal_hook_profile_points, bearing_side_plate, bearing_retainer_plate, cutter_shaft, spur_phase_gear
from manufacturing import generic_phase_gear_lamination, solid_phase_gear


def stable_step(path):
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"(FILE_NAME\('[^']*',)'[^']*'", r"\1'1970-01-01T00:00:00'", text, count=1)
    assert count == 1
    path.write_text(text, encoding="utf-8")


def keyed_bore(shape, length, bore, key_width, key_top):
    void = Part.makeCylinder(bore / 2, length, App.Vector(), App.Vector(0, 1, 0))
    slot = Part.makeBox(key_width, length, key_top - 9.0,
                        App.Vector(-key_width / 2, 0, 9.0))
    return shape.cut(void.fuse(slot))


def main():
    bore, cutter_key_width, gear_key_width, shaft_diameter = 25.01, 6.0075, 8.0075, 25.0
    profile = Part.Face(Part.makePolygon(cycloidal_hook_profile_points(58, 36, 7, 18, 8)))
    disc = keyed_bore(profile.extrude(App.Vector(0, 6, 0)), 6, bore, cutter_key_width, 15.0)
    phase_gear = generic_phase_gear_lamination(bore, gear_key_width, 15.5)
    root_edges = [edge for edge in phase_gear.Edges if len(edge.Vertexes) == 2
                  and all(abs(math.hypot(vertex.Point.x, vertex.Point.z) - 20.25) < 1e-5 for vertex in edge.Vertexes)
                  and abs(abs(edge.Vertexes[1].Point.y - edge.Vertexes[0].Point.y) - 6) < 1e-6]
    assert len(root_edges) == 64
    phase_gear = phase_gear.makeFillet(1.0, root_edges)
    solid_gear = spur_phase_gear(module=3.0, teeth=16, thickness=18.0, bore=bore, pair_backlash_mm=.125)
    for angle, diameter in ((0, 4.5), (120, 4.5), (240, 3.0)):
        a = math.radians(angle)
        hole = Part.makeCylinder(diameter / 2, 18, App.Vector(15 * math.cos(a), 0, 15 * math.sin(a)), App.Vector(0, 1, 0))
        solid_gear = solid_gear.cut(hole)
    solid_gear = solid_gear.cut(Part.makeBox(gear_key_width, 18, 6, App.Vector(-gear_key_width / 2, 0, 9.5)))
    solid_root_edges = [edge for edge in solid_gear.Edges if len(edge.Vertexes) == 2
                        and all(abs(math.hypot(vertex.Point.x, vertex.Point.z) - 20.25) < 1e-5 for vertex in edge.Vertexes)
                        and abs(abs(edge.Vertexes[1].Point.y - edge.Vertexes[0].Point.y) - 18) < 1e-6]
    assert len(solid_root_edges) == 64
    solid_gear = solid_gear.makeFillet(1.0, solid_root_edges)
    shaft = Part.makeCylinder(shaft_diameter / 2, 240, App.Vector(), App.Vector(0, 1, 0))
    for y, length, width, depth in ((0, 35, 6.0, 3.5), (55, 105, 6.0, 3.5), (195, 45, 8.0, 4.0)):
        shaft = shaft.cut(Part.makeBox(width, length, depth,
                                      App.Vector(-width / 2, y, shaft_diameter / 2 - depth)))
    spacer = Part.makeCylinder(17, 6.75).cut(Part.makeCylinder(12.55, 6.75))
    seat_ring = Part.makeCylinder(21, 3).cut(Part.makeCylinder(12.75, 3))
    bearing = Part.makeCylinder(21, 9).cut(Part.makeCylinder(12.5, 9))
    assert all(s.isValid() and len(s.Solids) == 1 for s in (disc, phase_gear, solid_gear, shaft, spacer, seat_ring, bearing))
    assert math.isclose(solid_gear.BoundBox.YLength, 18, abs_tol=1e-9)
    assert math.isclose(cutter_shaft().Volume, shaft.Volume, rel_tol=1e-9)
    assert math.isclose(solid_phase_gear().Volume, solid_gear.Volume, rel_tol=1e-9)

    keyway_root_ligament = 20.25 - 15.5
    assert keyway_root_ligament >= 4.5
    key = Part.makeBox(6, 105, 6, App.Vector(-3, 55, 9))
    gear_key = Part.makeBox(8, 45, 7, App.Vector(-4, 195, 8.5))
    disc_key = Part.makeBox(6, 6, 6, App.Vector(-3, 0, 9))
    oversized_disc_key = Part.makeBox(6.02, 6, 6, App.Vector(-3.01, 0, 9))
    assert shaft.common(key).Volume < 1e-6 and shaft.common(gear_key).Volume < 1e-6
    assert disc.common(disc_key).Volume < 1e-6
    assert disc.common(oversized_disc_key).Volume > .01

    bearings = []
    for x in (50, 98):
        placed = bearing.copy(); placed.translate(App.Vector(x, 0, 55))
        placed.rotate(App.Vector(x, 0, 55), App.Vector(1, 0, 0), 90)
        bearings.append(placed)
    assert bearings[0].distToShape(bearings[1])[0] >= 6 - 1e-6
    assert bearings[0].common(bearings[1]).Volume < 1e-6

    plate = bearing_side_plate()
    retainer = bearing_retainer_plate()
    assert plate.isValid() and retainer.isValid()
    assert math.isclose(seat_ring.BoundBox.ZLength + bearing.BoundBox.ZLength, 12, abs_tol=1e-9)

    phase = json.loads((ROOT / "analysis/final_validation/results/v0.8/phase_section_sensitivity.json").read_text())
    candidate = phase["diameter25_candidate"]
    assert phase["source_sha256"]["analysis/final_validation/run_phase_section_sensitivity_v08.py"] == hashlib.sha256(
        (ROOT / "analysis/final_validation/run_phase_section_sensitivity_v08.py").read_bytes()).hexdigest()
    reaction = max(abs(v) for mesh in candidate["meshes"] for case in mesh["shaft_cases"]
                   for v in case["support_reaction_n"])
    static_rating, dynamic_rating = 4300.0, 7020.0
    assert static_rating / reaction >= 2 and candidate["numeric_screen"] == "PASS"
    shaft_step = ROOT / "analysis/final_validation/results/v0.8/phase_path_25_shaft.step"
    shaft.exportStep(str(shaft_step))
    stable_step(shaft_step)
    restored = Part.read(str(shaft_step))
    assert restored.isValid() and len(restored.Solids) == 1
    assert math.isclose(restored.Volume, shaft.Volume, rel_tol=1e-9)
    gear_step = shaft_step.with_name("phase_path_25_gear_lamination.step")
    phase_gear.exportStep(str(gear_step))
    stable_step(gear_step)
    restored_gear = Part.read(str(gear_step))
    assert restored_gear.isValid() and len(restored_gear.Solids) == 1
    assert math.isclose(restored_gear.Volume, phase_gear.Volume, rel_tol=1e-9)
    solid_gear_step = shaft_step.with_name("phase_path_25_solid_gear.step")
    solid_gear.exportStep(str(solid_gear_step))
    stable_step(solid_gear_step)
    restored_solid_gear = Part.read(str(solid_gear_step))
    assert restored_solid_gear.isValid() and len(restored_solid_gear.Solids) == 1
    assert math.isclose(restored_solid_gear.Volume, solid_gear.Volume, rel_tol=1e-9)
    geometry = json.loads((ROOT / "analysis/final_validation/input/geometry_manifest.json").read_text())
    load_case = max(candidate["torsion_cases"], key=lambda row: sum(row["series_lengths_mm"]))
    spans = []
    for label, cutter_y in (("153", load_case["adjacent_driven_cutter_y_mm"]),
                            ("105", load_case["jammed_slave_cutter_y_mm"])):
        station = geometry["shredder_stations"][label]
        start = cutter_y - station["shaft_y_min_mm"]
        length = station["gear_y_mm"] - cutter_y
        shape = shaft.common(Part.makeBox(27, length, 27, App.Vector(-13.5, start, -13.5)))
        shape.translate(App.Vector(0, -start, 0))
        assert shape.isValid() and len(shape.Solids) == 1
        path = shaft_step.with_name(f"phase_path_25_{label}.step")
        shape.exportStep(str(path))
        stable_step(path)
        restored = Part.read(str(path))
        assert restored.isValid() and math.isclose(restored.Volume, shape.Volume, rel_tol=1e-9)
        spans.append({"shaft": label, "length_mm": length, "step": str(path.relative_to(ROOT)),
                      "step_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    assert math.isclose(sum(row["length_mm"] for row in spans), sum(load_case["series_lengths_mm"]))

    out = {
        "status": "PASS", "physical_validation_state": "NOT_RUN",
        "nominal_geometry_check": "PASS", "shaft_diameter_mm": shaft_diameter,
        "shaft_length_mm": 240, "shaft_step": str(shaft_step.relative_to(ROOT)),
        "shaft_step_sha256": hashlib.sha256(shaft_step.read_bytes()).hexdigest(),
        "gear_lamination_step": str(gear_step.relative_to(ROOT)),
        "gear_lamination_step_sha256": hashlib.sha256(gear_step.read_bytes()).hexdigest(),
        "solid_gear_step": str(solid_gear_step.relative_to(ROOT)),
        "solid_gear_step_sha256": hashlib.sha256(solid_gear_step.read_bytes()).hexdigest(),
        "solid_gear_face_width_mm": 18.0, "solid_gear_piece_count": 1,
        "gear_root_fillet_mm": 1.0,
        "cad_pair_backlash_target_mm": 0.125,
        "spans": spans,
        "cutter_bore_mm": bore, "cutter_matched_keyway_width_mm": cutter_key_width,
        "gear_matched_keyway_width_mm": gear_key_width,
        "gear_key_nominal_mm": [8.0, 7.0],
        "keyway_to_root_ligament_mm": keyway_root_ligament,
        "bearing": {
            "candidate_mpn": "SKF 61905-2RS1", "dimensions_mm": [25, 42, 9],
            "basic_dynamic_rating_n": dynamic_rating, "basic_static_rating_n": static_rating,
            "cn_unmounted_radial_internal_clearance_mm": [.005, .020],
            "two_shaft_worst_relative_clearance_mm": .040,
            "candidate_max_reaction_n": reaction,
            "dynamic_rating_ratio": dynamic_rating / reaction,
            "static_rating_ratio": static_rating / reaction,
            "official_source": "https://cdn.skfmediahub.skf.com/api/public/0901d196802809de/pdf_preview_medium/0901d196802809de_pdf_preview_medium.pdf"
        },
        "existing_plate_bearing_bore_mm": 42, "bearing_pair_edge_gap_mm": 6,
        "seat_ring_mm": {"od": 42, "id": 25.5, "width": 3, "quantity": 4},
        "combined_phase_screen_deg": candidate["combined_worst_angle_deg"],
        "scope": "Released nominal cold CAD and bearing-rating screen. Exact keyed-shaft and gear FEA are bound separately; shock/misalignment, manufacturing tolerance and physical fit remain NOT_RUN.",
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            Path(__file__).resolve(), ROOT / "cad/freecad/compact/geometry.py",
            ROOT / "cad/freecad/compact/manufacturing.py",
            ROOT / "analysis/final_validation/run_phase_section_sensitivity_v08.py",
            ROOT / "analysis/final_validation/results/v0.8/phase_section_sensitivity.json")}
    }
    path = ROOT / "analysis/final_validation/results/v0.8/phase_path_25_candidate.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"PHASE_PATH_25_RELEASE_PASS phase={candidate['combined_worst_angle_deg']:.6f} static_ratio={static_rating/reaction:.3f} physical=NOT_RUN")


if __name__ == "__main__":
    main()
