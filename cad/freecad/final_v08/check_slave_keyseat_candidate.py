#!/usr/bin/env python3
"""종동축만 후방 키홈4 mm 연장하는 미채택 후보. 강도/가공 승인 아님."""
import hashlib
import json
import sys
from pathlib import Path
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from geometry import cutter_shaft


def main():
    original = cutter_shaft()
    candidate = original.cut(Part.makeBox(6,4,3.5,App.Vector(-3,191,6.5))).removeSplitter()
    assert candidate.isValid() and len(candidate.Solids) == 1
    assert original.Volume > candidate.Volume
    # Slave datumY278 only: rear bearing455..467 -> local177..189.
    bearing_segment = Part.makeCylinder(10,12,App.Vector(0,177,0),App.Vector(0,1,0))
    assert original.common(bearing_segment).Volume-candidate.common(bearing_segment).Volume < 1e-6
    overlaps = [min(240,end)-max(191,start) for start,end in ((191,197),(197,203),(203,209))]
    assert overlaps == [6,6,6]
    rounded_ends = []
    for centre in (194,191):
        tool = Part.makeCylinder(3,3.5,App.Vector(0,centre,6.5)).fuse(
            Part.makeBox(6,240-centre,3.5,App.Vector(-3,centre,6.5)))
        rounded = original.cut(tool).removeSplitter()
        assert rounded.isValid() and len(rounded.Solids) == 1
        loss = original.common(bearing_segment).Volume-rounded.common(bearing_segment).Volume
        assert (loss < 1e-6) == (centre == 194)
        rounded_ends.append({"nose_start_mm":centre-3,"full_width_start_mm":centre,
                             "bearing_volume_removed_mm3":loss,
                             "first_lamination_full_width_overlap_mm":197-max(191,centre)})
    path = ROOT/"analysis/final_validation/results/v0.8/slave_keyseat_candidate.step"
    candidate.exportStep(str(path))
    restored = Part.read(str(path))
    assert restored.isValid() and len(restored.Solids)==1 and abs(restored.Volume-candidate.Volume)<1e-5
    # Diameter3 pocket cutter: leading cornerR1.5, full width beginsY191.
    pocket = Part.makeBox(6,49,3.5,App.Vector(-3,191,6.5))
    pocket = pocket.fuse(Part.makeBox(3,1.5,3.5,App.Vector(-1.5,189.5,6.5)))
    for x in (-1.5,1.5):
        pocket = pocket.fuse(Part.makeCylinder(1.5,3.5,App.Vector(x,191,6.5)))
    small_tool = original.cut(pocket).removeSplitter()
    assert small_tool.isValid() and len(small_tool.Solids)==1
    assert abs(original.common(bearing_segment).Volume-small_tool.common(bearing_segment).Volume)<1e-6
    full_width_target = Part.makeBox(6,18,3.5,App.Vector(-3,191,6.5)).common(original)
    assert small_tool.common(full_width_target).Volume < 1e-6
    small_path = path.with_name("slave_keyseat_R1p5_candidate.step")
    small_tool.exportStep(str(small_path))
    small_restored = Part.read(str(small_path))
    assert small_restored.isValid() and len(small_restored.Solids)==1
    relative_volume_error = abs(small_restored.Volume-small_tool.Volume)/small_tool.Volume
    assert relative_volume_error < 1e-6  # Same relative STEP criterion as other candidate exports.
    result = {"status":"HOLD","physical_validation_state":"NOT_RUN",
              "diameter3_pocket_candidate":{"leading_corner_radius_mm":1.5,
                  "nose_start_mm":189.5,"full_width_start_mm":191,
                  "bearing_end_to_nose_mm":.5,"full_width_keyseat_length_in_gear_mm":18,
                  "step":str(small_path.relative_to(ROOT)),"step_sha256":hashlib.sha256(small_path.read_bytes()).hexdigest(),
                  "step_relative_volume_error":relative_volume_error,
                  "status":"HOLD","limitations":"Only nominal pocket envelope; machining accessibility/tool deflection, tolerances, bearing-adjacent stress and bottom fillet unqualified."},
              "diameter6_round_end_cases":rounded_ends,
              "slave_only_local_rear_keyseat_mm":[191,240],"assembly_origin_y_mm":278,
              "bearing_end_to_keyseat_start_mm":2,"shifted_gear_lamination_overlap_mm":overlaps,
              "removed_volume_mm3":original.Volume-candidate.Volume,"step_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
              "limitations":"Unadopted slave-only variant. Rectangular keyseat end follows existing ideal CAD; cutter radius/runout, axial tolerance, bearing-seat stress, torsion and actual key length/contact unqualified. Do not apply to driven shaft.",
              "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (Path(__file__).resolve(),ROOT/"cad/freecad/compact/geometry.py")}}
    path.with_suffix('.json').write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
