#!/usr/bin/env python3
"""실제 키홈 STEP의 전장 비틀림 진단; 실제 기어→커터 하중경로 승인 아님."""
import json
import math
import tempfile
from collections import defaultdict
from pathlib import Path
from run_calculix_v08 import ROOT, mesh_step, read_gmsh_inp, nset, solve, sha256
from run_qualification_v08 import numbers_after


def main(span=None):
    evidence = ROOT/"analysis/final_validation/results/v0.8"/(
        "phase_path_25_candidate.json" if span and span.startswith("25") else
        "torsion_load_path_geometry.json" if span else "slave_keyseat_candidate.json")
    meta = json.loads(evidence.read_text())
    assert all(sha256(ROOT/p)==h for p,h in meta["source_sha256"].items())
    item = ({"step": meta["shaft_step"], "step_sha256": meta["shaft_step_sha256"],
             "length_mm": meta["shaft_length_mm"]} if span == "25" else
            next(r for r in meta["spans"] if r["shaft"] == span.split("_")[1]) if span and span.startswith("25_") else
            next(r for r in meta["spans"] if r["shaft"] == span) if span else meta["diameter3_pocket_candidate"])
    length_mm = item["length_mm"] if span else 240.
    assert math.isfinite(length_mm) and length_mm > 0
    if span and not span.startswith("25"):
        assert meta["load_case"]["torque_nm_along_each_series_segment"] == 22.
    step = ROOT/item["step"]
    assert sha256(step)==item["step_sha256"]
    folder = Path(tempfile.mkdtemp(prefix="keyed-torsion-",dir=evidence.parent))
    rows = []
    for size in (3.,2.,1.5,1.):
        case = folder/f"mesh_{size}"
        case.mkdir()
        nodes,elements = read_gmsh_inp(mesh_step(step,case,size))
        coords = {n:tuple(v/1000 for v in p) for n,p in nodes.items()}
        fixed = {n for n,p in coords.items() if abs(p[1])<1e-8}
        tip = {n for n,p in coords.items() if abs(p[1]-length_mm/1000)<1e-8}
        assert len(fixed)>5 and len(tip)>5
        weights = defaultdict(float)
        for element in elements:
            face = [n for n in list(map(int,element.split(',')))[1:] if n in tip]
            if len(face)!=3:
                continue
            a,b,c = [coords[n] for n in face]
            area = abs((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0]))/2
            for n in face:
                weights[n] += area/3
        assert set(weights)==tip and all(w>0 for w in weights.values())
        cx = sum(weights[n]*coords[n][0] for n in tip)/sum(weights.values())
        cz = sum(weights[n]*coords[n][2] for n in tip)/sum(weights.values())
        radii = {n:(coords[n][0]-cx,coords[n][2]-cz) for n in tip}
        denom = sum(weights[n]*(x*x+z*z) for n,(x,z) in radii.items())
        forces = {n:(weights[n]*22*z/denom,-weights[n]*22*x/denom) for n,(x,z) in radii.items()}
        assert abs(sum(f[0] for f in forces.values()))<1e-8
        assert abs(sum(f[1] for f in forces.values()))<1e-8
        assert math.isclose(sum(coords[n][2]*fx-coords[n][0]*fz for n,(fx,fz) in forces.items()),22,abs_tol=1e-8)
        deck = ["*HEADING","Keyed shaft torsion diagnostic; SI","*NODE",
                *[f"{n},{x:.12g},{y:.12g},{z:.12g}" for n,(x,y,z) in coords.items()],
                "*ELEMENT,TYPE=C3D4,ELSET=EALL",*elements,*nset("FIXED",sorted(fixed)),*nset("TIP",sorted(tip)),
                "*SOLID SECTION,ELSET=EALL,MATERIAL=STEEL","*MATERIAL,NAME=STEEL","*ELASTIC","2.05e11,0.29",
                "*BOUNDARY","FIXED,1,3,0","*STEP","*STATIC","0.1,1","*CLOAD",
                *[line for n,(fx,fz) in forces.items() for line in (f"{n},1,{fx:.12g}",f"{n},3,{fz:.12g}")],
                "*NODE PRINT,NSET=TIP","U","*NODE FILE","U,RF","*EL FILE","S","*END STEP",""]
        result = solve(case,"\n".join(deck),(fixed,coords))
        assert abs(result["reaction"]["moment_about_origin_nm"][1]+22)<.01
        disp = numbers_after((case/"model.dat").read_text(),"displacements (vx,vy,vz) for set TIP")
        assert {int(r[0]) for r in disp}==tip
        twist = sum(weights[int(r[0])]*(radii[int(r[0])][1]*r[1]-radii[int(r[0])][0]*r[3]) for r in disp)/denom
        peak = coords[result["max_von_mises_node_id"]]
        rows.append({"mesh_mm":size,"tip_rotation_deg":math.degrees(twist),"loaded_area_mm2":sum(weights.values())*1e6,
                     "peak_coordinate_mm":[v*1000 for v in peak],"result":result,"deck_sha256":sha256(case/"model.inp")})
    rotation_change = abs(rows[-1]["tip_rotation_deg"]-rows[-2]["tip_rotation_deg"])/abs(rows[-1]["tip_rotation_deg"])
    stress_change = abs(rows[-1]["result"]["max_von_mises_mpa"]-rows[-2]["result"]["max_von_mises_mpa"])/rows[-1]["result"]["max_von_mises_mpa"]
    assert all(math.isfinite(r["tip_rotation_deg"]) and r["tip_rotation_deg"]>0 for r in rows)
    output = {"status":"HOLD","physical_validation_state":"NOT_RUN","meshes":rows,
              "rotation_relative_mesh_change":rotation_change,"rotation_within_5_percent":rotation_change<=.05,
              "peak_stress_relative_mesh_change":stress_change,"stress_qualification":"NOT_QUALIFIED",
              "length_mm":length_mm,
              "scope":f"{'25 mm candidate shaft '+span if span and span.startswith('25') else 'Baseline cutter-to-gear span '+span if span else 'Full candidate shaft'}; {length_mm} mm end-to-end22 Nm; triangle-area-lumped pure couple and area-weighted rotation, fixed cutter-side end warping. Not actual cutter/gear contact traction. Sharp bottom corners, mesh stress and material/contact qualification unresolved.",
              "raw_directory":str(folder.relative_to(ROOT)),
              "source_sha256":{str(p.relative_to(ROOT)):sha256(p) for p in (Path(__file__).resolve(),step,ROOT/"analysis/final_validation/run_calculix_v08.py",ROOT/"analysis/final_validation/run_qualification_v08.py")}}
    evidence.with_name(f"torsion_load_path_{span}.json" if span else "keyed_shaft_torsion_candidate.json").write_text(json.dumps(output,indent=2)+"\n")
    print("KEYED_SHAFT_TORSION_DIAGNOSTIC_HOLD",[(r["mesh_mm"],r["tip_rotation_deg"]) for r in rows])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--span", choices=("153", "105", "25", "25_153", "25_105"))
    main(parser.parse_args().span)
