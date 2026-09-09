#!/usr/bin/env python3
"""후보 볼트 공구 공간 검사. 실제 공구/작업자 승인 아님."""
import hashlib
import json
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis/final_validation"))
from generate import final_objects
from retainer_support_sensitivity import verify_sources


def overlaps(envelope, shapes):
    return [{"part": name, "volume_mm3": volume}
            for name, shape in shapes.items()
            if (volume := envelope.common(shape).Volume) > .01]


def main():
    evidence = ROOT / "analysis/final_validation/results/v0.8/axial_shoulder_candidate.json"
    candidate = json.loads(evidence.read_text(encoding="utf-8"))
    verify_sources(candidate, ROOT)
    assert candidate["geometry_check"] == "PASS"
    shapes = {item["name"]: item["shape"] for item in final_objects()}
    service_shield = shapes["HotShield"].copy()
    hole_centres = [(x, z) for x in (321, 341) for z in (352, 412)]
    for wall_y in (309, 382):
        service_shield = service_shield.cut(Part.makeBox(12, 4, 52, App.Vector(325, wall_y, 356)))
        for x, z in hole_centres:
            service_shield = service_shield.cut(Part.makeCylinder(1.7, 4, App.Vector(x, wall_y, z), App.Vector(0, 1, 0)))
    assert service_shield.isValid() and len(service_shield.Solids) == 1
    candidate_step = evidence.with_name("shield_service_window_candidate.step")
    service_shield.exportStep(str(candidate_step))
    restored = Part.read(str(candidate_step))
    assert restored.isValid() and len(restored.Solids) == 1
    assert abs(restored.Volume-service_shield.Volume) < 1e-5
    access_candidates = []
    rows = []
    for y, z in candidate["retainer_bolt_centres_yz_mm"]:
        # ponytail: conservative nominal envelopes; selected tool/hand validation remains required.
        # Candidate head rear face X351. Added mount solids are all X>=351.
        shank = Part.makeCylinder(2, 100, App.Vector(251, y, z), App.Vector(1, 0, 0))
        grip = Part.makeCylinder(15, 60, App.Vector(191, y, z), App.Vector(1, 0, 0))
        for name, envelope in (("shaft_OD4_L100", shank), ("grip_OD30_L60", grip)):
            assert envelope.isValid() and len(envelope.Solids) == 1
            assert overlaps(envelope, {"negative_control": envelope.copy()})
            collisions = overlaps(envelope, shapes)
            rows.append({"bolt_centre_yz_mm": [y, z], "envelope": name,
                         "collisions": collisions,
                         "nominal_space_check": "FAIL" if collisions else "PASS"})
        # OD4 tube: short arm20 ends at head face; long arm40 points away
        # from barrel. This box contains its entire +/-30 degree rotation:
        # radial extent <=40+2, transverse extent <=40*sin(30deg)+2.
        short_arm = Part.makeCylinder(2, 20, App.Vector(331, y, z), App.Vector(1, 0, 0))
        sweep_box = Part.makeBox(4, 44, 44, App.Vector(329, y-42 if y<347 else y-2, z-22))
        envelope = short_arm.fuse(sweep_box).removeSplitter()
        assert envelope.isValid() and len(envelope.Solids) == 1
        assert overlaps(envelope, {"negative_control": envelope.copy()})
        collisions = overlaps(envelope, shapes)
        rows.append({"bolt_centre_yz_mm": [y, z],
                     "envelope": "L_key_OD4_short20_long40_outward_plus_minus30_conservative_box",
                     "collisions": collisions,
                     "nominal_space_check": "FAIL" if collisions else "PASS"})
        service_collisions = overlaps(envelope, {name: shape for name, shape in shapes.items() if name != "HotShield"})
        assert "HotShield" in shapes
        rows.append({"bolt_centre_yz_mm": [y, z],
                     "envelope": "L_key_same_sweep_HotShield_removed",
                     "required_removed_parts": ["HotShield"],
                     "collisions": service_collisions,
                     "nominal_space_check": "FAIL" if service_collisions else "PASS"})
        opened = shapes | {"HotShield": service_shield}
        cover_y = 308 if y < 347 else 385
        cover = Part.makeBox(28, 2, 68, App.Vector(317, cover_y, 348))
        for x, hole_z in hole_centres:
            cover = cover.cut(Part.makeCylinder(1.7, 2, App.Vector(x, cover_y, hole_z), App.Vector(0, 1, 0)))
        edge_ligament = min(min(x-317, 345-x, hole_z-348, 416-hole_z)-1.7
                            for x, hole_z in hole_centres)
        assert math.isclose(edge_ligament, 2.3, abs_tol=1e-9)
        assert math.isclose(cover.Volume, 28*2*68-4*math.pi*1.7**2*2, abs_tol=1e-6)
        cover_step = evidence.with_name(f"shield_service_cover_{y}_candidate.step")
        cover.exportStep(str(cover_step))
        restored_cover = Part.read(str(cover_step))
        assert restored_cover.isValid() and len(restored_cover.Solids) == 1
        assert abs(restored_cover.Volume-cover.Volume) < 1e-5
        # Conservative full-box sweep, including the removed hole volumes.
        removal = Part.makeBox(28, 22, 68, App.Vector(317, 288 if y < 347 else 385, 348))
        assert cover.isValid() and removal.isValid()
        access_candidates.append({"bolt_centre_yz_mm": [y, z],
                                  "window_xz_mm": [325, 356, 12, 52],
                                  "cover_box_mm": [317, cover_y, 348, 28, 2, 68],
                                  "hole_centres_xz_mm": hole_centres,
                                  "hole_diameter_mm": 3.4,
                                  "cover_edge_ligament_mm": edge_ligament,
                                  "cover_step": str(cover_step.relative_to(ROOT)),
                                  "cover_step_sha256": hashlib.sha256(cover_step.read_bytes()).hexdigest(),
                                  "closed_cover_collisions": overlaps(cover, opened),
                                  "cover_outward20_sweep_collisions": overlaps(removal, opened),
                                  "open_window_tool_collisions": overlaps(envelope, opened),
                                  "status": "HOLD"})
    shield_motion = []
    for distance in (.1, 1, 5, 20):
        moved = shapes["HotShield"].copy()
        moved.translate(App.Vector(0, 0, distance))
        collisions = overlaps(moved, {name: shape for name, shape in shapes.items() if name != "HotShield"})
        shield_motion.append({"upward_translation_mm": distance, "collisions": collisions,
                              "sample_check": "FAIL" if collisions else "PASS"})
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN", "rows": rows,
              "service_window_candidate": access_candidates,
              "service_window_step_sha256": hashlib.sha256(candidate_step.read_bytes()).hexdigest(),
              "service_window_limitations": "Unadopted geometry only: cover fasteners, retention, PE bonding, hot-surface protection, edge finishing, stiffness and hand access unqualified. Cover removal requires lockout, cooling and user confirmation.",
              "shield_upward_removal_samples": shield_motion,
              "shield_motion_scope": "Baseline assembly, four discrete vertical translations, not continuous path clearance or candidate mount clearance. No cable disconnection or fastener removal credited.",
              "scope": "Tool envelopes end at head rear face X351; candidate added solids lie at X>=351. L-key bounding box contains nominal outward +/-30 degree rotation. No socket engagement, insertion sweep, hand space or selected tool qualification; a box collision alone does not prove actual L-key collision.",
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (Path(__file__).resolve(), evidence, HERE / "generate.py",
                                          ROOT / "cad/freecad/compact/geometry.py")}}
    output = evidence.with_name("retainer_tool_access.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(rows, indent=2))
    print(json.dumps(shield_motion, indent=2))
    print(json.dumps(access_candidates, indent=2))
    print("RETAINER_TOOL_SPACE_CHECK_DONE assembly=HOLD")


if __name__ == "__main__":
    main()
