#!/usr/bin/env python3
"""기어 −Y2 mm 후보 민감도. 실제 위치 변경/조립체 승인 아님."""
import json
import math
import tempfile
from pathlib import Path
from run_phase_load_v08 import INPUT, ROOT, shaft, plate, sha256


def main():
    manifest = INPUT / "geometry_manifest.json"
    geometry = json.loads(manifest.read_text())
    assert geometry["geometry_source_sha256"] == sha256(ROOT/"cad/freecad/compact/geometry.py")
    stations = geometry["shredder_stations"]
    key_overlap = []
    for key, s in stations.items():
        assert s["gear_y_mm"] == 480
        s["gear_y_mm"] -= 2
        # CUT-05 rear keyseat local Y195..240; geometric overlap, not full tooth engagement.
        seat_start, seat_end = s["shaft_y_min_mm"]+195, s["shaft_y_min_mm"]+240
        length = min(seat_end,s["gear_y_mm"]+9)-max(seat_start,s["gear_y_mm"]-9)
        assert length > 0
        key_overlap.append({"shaft":key,"rear_keyseat_y_mm":[seat_start,seat_end],
                            "gear_keyseat_overlap_mm":length,"full18_mm_overlap":length>=18})
    folder = Path(tempfile.mkdtemp(prefix="overhang-", dir=ROOT/"analysis/final_validation/results/v0.8/phase_raw"))
    angle = math.radians(20)
    rows = []
    for refinement, mesh in ((8,3.5),(16,2.5)):
        cases = [shaft(s,1856.544175556756,22/.024*math.tan(angle),sign,refinement,
                       folder/f"shaft_{key}_{sign}_{refinement}")
                 for key,s in stations.items() for sign in (-1,1)]
        support = plate(max(abs(v) for c in cases for v in c["support_reaction_n"]),mesh,folder/f"plate_{refinement}")
        s = next(iter(stations.values()))
        front,rear = s["bearing_y_mm"]
        centre = sum(max(abs(c["gear_displacement_mm"]) for c in cases[i:i+2]) for i in (0,2))
        centre += (1+2*(s["gear_y_mm"]-rear)/(rear-front))*support["relative_centre_bound_mm"]
        backlash = [.15-2*centre*math.tan(angle),.35+2*centre*math.tan(angle)]
        rows.append({"refinement":refinement,"shaft_cases":cases,"plate":support,
                     "centre_movement_mm":centre,"backlash_range_mm":backlash,
                     "angular_bound_deg":math.degrees(backlash[1]/24)})
    change = abs(rows[1]["centre_movement_mm"]-rows[0]["centre_movement_mm"])/rows[1]["centre_movement_mm"]
    assert change <= .05
    result = {"status":"HOLD","physical_validation_state":"NOT_RUN","meshes":rows,
              "geometric_key_overlap":key_overlap,
              "relative_mesh_change":change,"raw_directory":str(folder.relative_to(ROOT)),
              "scope":"Unadopted gear centre478 instead of480; same reduced16.5 mm shaft and loads. Key/hub/gear contact, axial retention, frame/bearing/torsional compliance unqualified.",
              "source_sha256":{str(p.relative_to(ROOT)):sha256(p) for p in (
                  Path(__file__).resolve(),manifest,INPUT/"bearing_plate.step",
                  ROOT/"analysis/final_validation/run_phase_load_v08.py",
                  ROOT/"analysis/final_validation/run_calculix_v08.py")}}
    (ROOT/"analysis/final_validation/results/v0.8/phase_overhang_candidate.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"OVERHANG_CANDIDATE_HOLD angle_deg={rows[-1]['angular_bound_deg']:.6f} mesh_change={change:.6f}")


if __name__ == "__main__":
    main()
