#!/usr/bin/env python3
"""실제 CUT-01 profile과 금속 spacer/shim의 명목 조립 후보. 제작 승인 아님."""
import hashlib
import json
import sys
import math
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
from geometry import hook_disc, cutter_shaft, spur_phase_gear
from manufacturing import generic_phase_gear_lamination


def main():
    discs, supports = [], []
    for cx, stagger in ((105, 0), (153, 6.375)):
        for i in range(6):
            y = 339 + stagger + i * 12.75
            disc = hook_disc()
            if cx == 153:
                disc.rotate(App.Vector(), App.Vector(0, 1, 0), 25.714)
            disc.translate(App.Vector(cx, y, 590))
            assert disc.isValid() and len(disc.Solids) == 1
            assert abs(disc.BoundBox.YLength - 6) < 1e-6
            discs.append((f"Hook{cx}_{i}", disc))
            if i < 5:
                for label, start, length in (("Spacer", y+6, 6.6), ("Shim", y+12.6, .15)):
                    base, axis = App.Vector(cx, start, 590), App.Vector(0, 1, 0)
                    shape = Part.makeCylinder(14, length, base, axis).cut(Part.makeCylinder(10.1, length, base, axis))
                    assert shape.isValid() and len(shape.Solids) == 1
                    supports.append((f"{label}{cx}_{i}", shape))
    discs.sort(key=lambda item: item[1].BoundBox.YMin)
    gaps = []
    for (aname, a), (bname, b) in zip(discs, discs[1:]):
        axial = b.BoundBox.YMin - a.BoundBox.YMax
        distance = a.distToShape(b)[0]
        assert abs(axial - .375) < 1e-6 and distance >= axial - 1e-6
        gaps.append({"a": aname, "b": bname, "axial_gap_mm": axial, "brep_distance_mm": distance})
    collisions = []
    parts = discs + supports
    for i, (name, shape) in enumerate(parts):
        for other, mate in parts[i+1:]:
            volume = shape.common(mate).Volume
            if volume > 1e-6:
                collisions.append({"a": name, "b": other, "volume_mm3": volume})
    assert len(gaps) == 11 and not collisions, collisions
    shaft_checks = []
    for cx, origin_y in ((105, 278), (153, 258)):
        shaft = cutter_shaft()
        shaft.translate(App.Vector(cx, origin_y, 590))
        rotor = [shape for name, shape in discs if name.startswith(f"Hook{cx}_")]
        low = min(s.BoundBox.YMin for s in rotor)
        high = max(s.BoundBox.YMax for s in rotor)
        assert origin_y + 55 <= low and high <= origin_y + 160
        shaft_overlap = sum(shaft.common(shape).Volume for shape in rotor)
        assert shaft_overlap < 1e-6
        # Candidate common6x6 key, at existing shaft keyseat clocking0deg.
        key = Part.makeBox(6, high-low, 6, App.Vector(cx-3, low, 596.5))
        current_overlap = sum(key.common(shape).Volume for shape in rotor)
        aligned_key = key.copy()
        aligned_shaft = shaft.copy()
        if cx == 153:
            for shape in (aligned_key, aligned_shaft):
                shape.rotate(App.Vector(cx, 0, 590), App.Vector(0, 1, 0), 25.714)
        aligned_overlap = sum(aligned_key.common(shape).Volume for shape in rotor)
        assert aligned_overlap < 1e-6
        assert aligned_key.common(aligned_shaft).Volume < 1e-6
        shaft_checks.append({"shaft_x_mm": cx, "stack_y_mm": [low, high],
                             "keyseat_y_mm": [origin_y+55, origin_y+160],
                             "shaft_disc_overlap_mm3": shaft_overlap,
                             "current_clocking_key_disc_overlap_mm3": current_overlap,
                             "aligned_clocking_key_disc_overlap_mm3": aligned_overlap})
    assert shaft_checks[0]["current_clocking_key_disc_overlap_mm3"] < 1e-6
    assert shaft_checks[1]["current_clocking_key_disc_overlap_mm3"] > 1
    # Preserve tooth phase11.25deg while aligning the driven-shaft key25.714deg.
    tooth_phase, shaft_phase = 11.25, 25.714
    local_key_angle = shaft_phase - tooth_phase
    gear = spur_phase_gear(module=3, teeth=16, thickness=6, bore=20.2)
    holes = []
    for angle, diameter in ((0,4.5),(120,4.5),(240,3.0)):
        a = math.radians(angle)
        hole = Part.makeCylinder(diameter/2, 6, App.Vector(15*math.cos(a),0,15*math.sin(a)),App.Vector(0,1,0))
        holes.append((angle, diameter, hole))
        gear = gear.cut(hole)
    slot = Part.makeBox(6.2,6,6,App.Vector(-3.1,0,7))
    slot.rotate(App.Vector(),App.Vector(0,1,0),local_key_angle)
    bore = Part.makeCylinder(10.1,6,App.Vector(),App.Vector(0,1,0))
    ligaments = []
    for angle, diameter, hole in holes:
        bore_gap = bore.distToShape(hole)[0]
        slot_gap = slot.distToShape(hole)[0]
        assert abs(bore_gap - (15-10.1-diameter/2)) < 1e-6
        assert slot_gap > 0
        ligaments.append({"hole_angle_deg": angle, "hole_diameter_mm": diameter,
                          "bore_to_hole_mm": bore_gap, "keyway_to_hole_mm": slot_gap})
    tight_candidates = []
    for side, angle in (("L", 0), ("R", local_key_angle)):
        tight_slot = Part.makeBox(6.0075,6,6,App.Vector(-6.0075/2,0,7))
        tight_slot.rotate(App.Vector(),App.Vector(0,1,0),angle)
        tight_gear = gear.cut(tight_slot)
        fit_key = Part.makeBox(6,6,6,App.Vector(-3,0,6.5))
        fit_key.rotate(App.Vector(),App.Vector(0,1,0),angle)
        assert tight_gear.isValid() and tight_gear.common(fit_key).Volume < 1e-6
        oversized_key = Part.makeBox(6.02,6,6,App.Vector(-3.01,0,6.5))
        oversized_key.rotate(App.Vector(),App.Vector(0,1,0),angle)
        assert tight_gear.common(oversized_key).Volume > .01
        tight_candidates.append((f"DRV-03-{side}-MATCHED-CANDIDATE", tight_gear, angle, 6.0075))
    gear = gear.cut(slot)
    existing = generic_phase_gear_lamination()
    candidate_dir = ROOT / "analysis/final_validation/results/v0.8/phase_gear_candidates"
    candidate_dir.mkdir(exist_ok=True)
    candidate_parts = []
    for part_id, shape, key_angle, width in [
            ("DRV-03-L-CANDIDATE", existing, 0, 6.2),
            ("DRV-03-R-CANDIDATE", gear, local_key_angle, 6.2), *tight_candidates]:
        path = candidate_dir / f"{part_id}.step"
        shape.exportStep(str(path))
        restored = Part.read(str(path))
        assert restored.isValid() and len(restored.Solids) == 1
        assert abs(restored.Volume - shape.Volume) < 1e-5
        candidate_parts.append({"part_id": part_id, "quantity": 3,
                                "local_keyway_offset_deg": key_angle,
                                "nominal_keyway_width_mm": width,
                                "file": str(path.relative_to(ROOT)),
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                "status": "HOLD", "step_reimport": "PASS"})
    for shape in (gear, existing):
        shape.rotate(App.Vector(),App.Vector(0,1,0),tooth_phase)
        shape.translate(App.Vector(153,471,590))
    key = Part.makeBox(6,6,6,App.Vector(150,471,596.5))
    key.rotate(App.Vector(153,0,590),App.Vector(0,1,0),shaft_phase)
    gear_key_overlap = gear.common(key).Volume
    existing_gear_key_overlap = existing.common(key).Volume
    assert gear.isValid() and len(gear.Solids) == 1 and gear_key_overlap < 1e-6
    assert existing_gear_key_overlap > 1
    # Rigid key/hub only: contact onset is not loaded compliance or shaft-key fit.
    contact_angles = []
    for direction in (-1, 1):
        low, high = 0.0, 2.0
        def overlap_at(angle):
            rotated = key.copy()
            rotated.rotate(App.Vector(153,0,590), App.Vector(0,1,0), direction*angle)
            return gear.common(rotated).Volume
        assert overlap_at(low) < 1e-6 and overlap_at(high) > 1e-6
        for _ in range(22):
            midpoint = (low+high)/2
            if overlap_at(midpoint) > 1e-6:
                high = midpoint
            else:
                low = midpoint
        # Key outer corner reaches the slot side: 3cos(a)+12.5sin(a)=3.1.
        assert abs(3*math.cos(math.radians(high))+12.5*math.sin(math.radians(high))-3.1) < 0.001
        contact_angles.append(high)
    fit_corners = []
    # Custom matched-fit proposal, not an ISO fit or a supplier capability claim.
    for key_width in (5.995, 6.000):
        for slot_width in (6.005, 6.010):
            half_key = key_width/2
            angle = math.asin((slot_width/2)/math.hypot(half_key, 12.5)) - math.atan2(half_key, 12.5)
            assert angle > 0
            assert abs(half_key*math.cos(angle)+12.5*math.sin(angle)-slot_width/2) < 1e-12
            fit_corners.append({"key_width_mm": key_width, "slot_width_mm": slot_width,
                                "total_side_clearance_mm": slot_width-key_width,
                                "two_hubs_reversal_deg": 4*math.degrees(angle)})
    assert max(row["two_hubs_reversal_deg"] for row in fit_corners) < 0.15
    tightest_half_angle = min(row["two_hubs_reversal_deg"] for row in fit_corners)/4
    stack_alignment = []
    for spread in (0., .01, .02):
        slot_angles = [-spread, 0., spread]
        lower = max(a-tightest_half_angle for a in slot_angles)
        upper = min(a+tightest_half_angle for a in slot_angles)
        stack_alignment.append({"lamination_offsets_deg": slot_angles,
                                "common_key_angle_interval_deg": [lower, upper] if lower <= upper else None,
                                "geometrically_assemblable": lower <= upper})
    assert [r["geometrically_assemblable"] for r in stack_alignment] == [True, True, False]
    result = {"status": "HOLD", "nominal_geometry_check": "PASS", "physical_validation_state": "NOT_RUN",
              "driven_gear_clocking_candidate": {"tooth_phase_deg": tooth_phase, "shaft_key_phase_deg": shaft_phase,
                  "local_keyway_offset_deg": local_key_angle, "existing_key_overlap_per_lamination_mm3": existing_gear_key_overlap,
                  "candidate_key_overlap_per_lamination_mm3": gear_key_overlap,
                  "nominal_ligaments": ligaments, "candidate_parts": candidate_parts,
                  "matched_fit_proposal": {"status": "HOLD", "corners": fit_corners,
                      "tightest_key_half_angle_deg": tightest_half_angle,
                      "lamination_alignment_scenarios": stack_alignment,
                      "scope": "Custom key5.995..6.000/slot6.005..6.010 mm; top radius12.5 assumed unchanged. Proposal budget0.15deg for two hub-key joints only, not an allocated system requirement. MATCHED-CANDIDATE STEP uses slot6.0075 midpoint; not release geometry. Excludes shaft-key fit, form/alignment/thermal errors, wear and elastic contact."},
                  "key_hub_rigid_reversal": {
                      "contact_angles_from_centred_deg": contact_angles,
                      "single_hub_peak_to_peak_deg": sum(contact_angles),
                      "two_identical_hubs_serial_peak_to_peak_deg": 2*sum(contact_angles),
                      "scope": "Nominal rigid key/hub contact onset, overlap threshold1e-6 mm3. Two-hub value assumes independent identical clearances in series; excludes shaft-key clearance, tooth backlash and elasticity. Not the loaded phase metric."},
                  "scope": "Separate driven-gear keyway variant; tooth envelope unchanged. Nominal void distances only; manufacturing tolerance, minimum strength criterion, tooth strength, loaded mesh and full drive datum not qualified."},
              "shaft_key_checks": shaft_checks, "current_key_clocking_check": "FAIL",
              "discs": len(discs), "spacers_and_shims": len(supports), "gaps": gaps,
              "collisions": collisions, "freecad_version": ".".join(App.Version()[:3]),
              "scope": "Nominal12.75 pitch/6.375 stagger; actual hook profiles, spacer/shim and shaft/key geometry. Existing153 shaft keyseat clocking conflicts with rotated discs; rotating shaft+key25.714deg is a candidate only and requires phase-gear/drive datum review. Excludes collars/bearings/frame, loaded rotation and tolerance envelopes. Not adopted.",
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  (Path(__file__).resolve(), ROOT / "cad/freecad/compact/geometry.py", ROOT / "cad/freecad/compact/manufacturing.py")}}
    (ROOT / "analysis/final_validation/results/v0.8/cutter_shim_cad_candidate.json").write_text(json.dumps(result, indent=2) + "\n")
    print("CUTTER_SHIM_CAD_CANDIDATE_PASS gaps=11 parts=32 collisions=0 status=HOLD")


if __name__ == "__main__":
    main()
