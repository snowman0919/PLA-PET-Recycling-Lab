#!/usr/bin/env python3
"""후단 유지판 pressure-thrust 굽힘 진단. 고정 보어 가정이며 체결 검증 아님."""

import json
import math
import tempfile
from collections import defaultdict
from pathlib import Path

from run_calculix_v08 import ROOT, INPUT, mesh_step, read_gmsh_inp, nset, sha256, solve, reactions


def main():
    evidence = ROOT / "analysis/final_validation/results/v0.8/axial_shoulder_candidate.json"
    candidate = json.loads(evidence.read_text())
    if candidate.get("geometry_check") != "PASS" or candidate.get("unexpected_collisions"):
        raise ValueError("Retainer candidate has not passed assembly geometry checks")
    assert all(sha256(ROOT/p) == h for p,h in candidate["source_sha256"].items())
    step = INPUT / "retainer_candidate.step"
    assert sha256(step) == candidate["retainer_step_sha256"]
    folder = Path(tempfile.mkdtemp(prefix="retainer-", dir=evidence.parent))
    thrust = 6 * math.pi * 16.22**2 / 4
    rows = []
    for size in (2.0, 1.5, 1.0, .7, .5):
        case = folder / f"mesh_{size}"
        case.mkdir()
        nodes, elements = read_gmsh_inp(mesh_step(step, case, size))
        fixed = [n for n,(x,y,z) in nodes.items() if any(abs(math.hypot(y-cy,z-cz)-1.65)<1e-5 for cy,cz in candidate["retainer_bolt_centres_yz_mm"])]
        weights = defaultdict(float)
        # All coplanar outer-face triangles of the tetrahedra occur once.
        for element in elements:
            ids = list(map(int, element.split(",")))[1:]
            face = [n for n in ids if abs(nodes[n][0]-candidate["retainer_front_x_mm"])<1e-6]
            if len(face) != 3:
                continue
            points = [nodes[n] for n in face]
            cy = sum(p[1] for p in points)/3
            cz = sum(p[2] for p in points)/3
            if not 17.05 <= math.hypot(cy-347,cz-382) <= 22 or cz > 398:
                continue
            a,b,c = points
            area = abs((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]))/2
            for n in face:
                weights[n] += area/3
        area = sum(weights.values())
        assert area > 100 and len(fixed) >= 12
        forces = {n: thrust*w/area for n,w in weights.items()}
        assert math.isclose(sum(forces.values()), thrust, rel_tol=1e-12)
        coords = {n: tuple(v/1000 for v in xyz) for n,xyz in nodes.items()}
        deck = ["*HEADING", "Retainer candidate; SI; fixed tapped-bore diagnostic",
                "*NODE", *[f"{n},{x},{y},{z}" for n,(x,y,z) in coords.items()],
                "*ELEMENT,TYPE=C3D4,ELSET=EALL", *elements, *nset("FIXED", fixed),
                "*SOLID SECTION,ELSET=EALL,MATERIAL=STEEL", "*MATERIAL,NAME=STEEL", "*ELASTIC", "1.9e11,0.3",
                "*BOUNDARY", "FIXED,1,3,0", "*STEP", "*STATIC", "0.1,1", "*CLOAD",
                *[f"{n},1,{f}" for n,f in forces.items()], "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", ""]
        result = solve(case, "\n".join(deck), (set(fixed), coords))
        supports = []
        for cy, cz in candidate["retainer_bolt_centres_yz_mm"]:
            group = {n for n in fixed if abs(math.hypot(nodes[n][1]-cy,nodes[n][2]-cz)-1.65)<1e-5}
            reaction = reactions(case/"model.frd", group, coords)
            assert group and reaction["node_count"] == len(group)
            supports.append({"centre_yz_mm": [cy,cz], **reaction})
        assert sum(r["node_count"] for r in supports) == len(fixed)
        assert all(abs(sum(r["force_n"][axis] for r in supports)-result["reaction"]["force_n"][axis]) < 1e-6 for axis in range(3))
        residual = result["reaction"]["force_n"][0]+thrust
        assert abs(residual)/thrust < 1e-3
        moment = [0, sum(coords[n][2]*f for n,f in forces.items()),
                  -sum(coords[n][1]*f for n,f in forces.items())]
        moment_residual = [a+b for a,b in zip(moment, result["reaction"]["moment_about_origin_nm"])]
        assert max(map(abs, moment_residual)) < .01
        peak = nodes[result["max_von_mises_node_id"]]
        bore_distance = min(abs(math.hypot(peak[1]-cy, peak[2]-cz)-1.65)
                            for cy,cz in candidate["retainer_bolt_centres_yz_mm"])
        rows.append({"mesh_mm": size, "loaded_area_mm2": area, "result": result,
                     "peak_stress_coordinate_mm": peak,
                     "peak_stress_distance_to_fixed_bore_mm": bore_distance,
                     "force_residual_n": residual, "moment_residual_nm": moment_residual,
                     "fixed_bore_reactions": supports,
                     "deck_sha256": sha256(case/"model.inp")})
    displacement_change = abs(rows[-1]["result"]["max_displacement_mm"]-rows[-2]["result"]["max_displacement_mm"])/rows[-1]["result"]["max_displacement_mm"]
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN", "thrust_n": thrust,
              "medium_to_fine_displacement_change": displacement_change,
              "displacement_convergence_5_percent": displacement_change <= .05,
              "meshes": rows, "raw_directory": str(folder.relative_to(ROOT)),
              "limitations": ["E190 GPa and nu0.3 assumed, not elevated-temperature qualified material.",
                              "Fully fixed tapped bores omit bolt stretch, prying/contact and thread failure.",
                              "Triangle-centroid pressure footprint is approximate; no stress acceptance claimed."],
              "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (Path(__file__).resolve(), evidence, step,
                  ROOT/"analysis/final_validation/run_calculix_v08.py", ROOT/"analysis/structural/run_load_checks.py")}}
    (evidence.parent/"retainer_candidate_fea.json").write_text(json.dumps(result, indent=2)+"\n")
    print(f"RETAINER_CANDIDATE_DIAGNOSTIC_DONE status=HOLD displacement_mm={rows[-1]['result']['max_displacement_mm']:.6f}")


if __name__ == "__main__":
    main()
