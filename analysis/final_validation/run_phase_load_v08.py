#!/usr/bin/env python3
"""실제 CAD 축/기어 위치에서 하중 변위와 cold backlash를 결합한다."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

from run_calculix_v08 import INPUT, ROOT, mesh_step, nset, read_gmsh_inp, ring_nodes, sha256, solve
from run_qualification_v08 import numbers_after

OUT = ROOT / "analysis/final_validation/results/v0.8/loaded_phase.json"
QUALIFICATION = ROOT / "analysis/final_validation/results/v0.8/phase_path_25_qualification.json"
REV = "final-design-fabrication-closure-v0.8"
def load_loaded_phase_qualification() -> dict[str, bool | str]:
    data = json.loads(QUALIFICATION.read_text())
    hashes = data.get("source_sha256", {})
    current = bool(hashes) and all((ROOT / source).is_file() and sha256(ROOT / source) == digest
                                   for source, digest in hashes.items())
    passed = current and data["status"] == "PASS" and data["combined_worst_angle_deg"] <= data["criterion_deg"]
    return {
        "frame_and_bearing_compliance_qualified": passed,
        "torsional_phase_compliance_qualified": passed,
        "combined_worst_angle_deg": data["combined_worst_angle_deg"],
        "criterion_deg": data["criterion_deg"],
        "note": "Released 25 mm shaft, 61905 clearance, plate movement, exact keyed torsion and solid-gear elasticity are combined in phase_path_25_qualification.json; physical inspection remains NOT_RUN.",
    }


def shaft(stations: dict, force_n: float, gear_force_n: float, sign: int, refinement: int, folder: Path,
          diameter_m: float) -> dict:
    origin = stations["shaft_y_min_mm"]
    front, rear = [(v-origin)/1000 for v in stations["bearing_y_mm"]]
    gear = (stations["gear_y_mm"]-origin)/1000
    cuts = [(v-origin)/1000 for v in stations["cutter_y_mm"]]
    length = (stations["shaft_y_max_mm"]-origin)/1000
    anchors = sorted({0.0, front, rear, gear, length, *cuts})
    xs = [a+(b-a)*i/refinement for a, b in zip(anchors, anchors[1:]) for i in range(refinement)] + [length]
    corners = len(xs)
    mids = [(a+b)/2 for a,b in zip(xs, xs[1:])]
    at = lambda v: min(range(len(xs)), key=lambda i: abs(xs[i]-v))+1
    # Preserve the existing keyed-shaft screening bound, in SI metres.
    loads = [(at(v), sign*force_n/len(cuts)) for v in cuts] + [(at(gear), gear_force_n)]
    deck = ["*HEADING", "v0.8 actual-station keyed-shaft lower-stiffness bound; SI",
            "*NODE", *[f"{i+1},{x:.12g},0,0" for i, x in enumerate(xs+mids)],
            "*ELEMENT,TYPE=B32R,ELSET=EALL", *[f"{i+1},{i+1},{corners+i+1},{i+2}" for i in range(corners-1)],
            *nset("GEAR", [at(gear)]), *nset("SUPPORT", [at(front), at(rear)]),
            "*BEAM SECTION,ELSET=EALL,MATERIAL=STEEL,SECTION=CIRC", f"{diameter_m},{diameter_m}", "0,0,1",
            "*MATERIAL,NAME=STEEL", "*ELASTIC", "2.05e11,0.29", "*BOUNDARY",
            f"{at(front)},1,3,0", f"{at(rear)},2,3,0", f"{at(front)},4,4,0",
            "*STEP", "*STATIC", "0.1,1", "*CLOAD", *[f"{node},2,{load:.12g}" for node, load in loads],
            "*NODE PRINT,NSET=GEAR", "U", "*NODE PRINT,NSET=SUPPORT", "RF", "*NODE FILE", "U", "*EL FILE", "S", "*END STEP", ""]
    folder.mkdir()
    result = solve(folder, "\n".join(deck))
    dat = (folder / "model.dat").read_text()
    displacements = numbers_after(dat, "displacements (vx,vy,vz) for set GEAR")
    reactions = numbers_after(dat, "forces (fx,fy,fz) for set SUPPORT")
    assert len(displacements) == 1 and len(reactions) == 2
    residual = sum(r[2] for r in reactions) + sum(value for _, value in loads)
    assert abs(residual) < .01
    return {"gear_displacement_mm": displacements[0][2]*1000,
            "support_reaction_n": [r[2] for r in reactions], "force_residual_n": residual,
            "section_lower_bound_diameter_mm": diameter_m*1000,
            "cad_stations": stations, "cutter_load_sign": sign, "result": result,
            "deck_sha256": sha256(folder / "model.inp")}


def plate(force_n: float, mesh_mm: float, folder: Path) -> dict:
    folder.mkdir()
    nodes, elements = read_gmsh_inp(mesh_step(INPUT / "bearing_plate.step", folder, mesh_mm))
    fixed = ring_nodes(nodes, ((15, 15), (15, 110), (135, 15), (135, 110)), 3.3, .08)
    loads = {}
    for cx, sign in ((50, -1), (98, 1)):
        ring = ring_nodes(nodes, ((cx, 55),), 21, .08)
        weights = {n: max(0.0, sign*(nodes[n][0]-cx)/21) for n in ring}
        total = sum(weights.values())
        assert total > 0
        loads.update({n: sign*force_n*w/total for n, w in weights.items() if w > 0})
    deck = ["*HEADING", "v0.8 CUT03 opposite radial bearing reactions; SI",
            "*NODE", *[f"{n},{x/1000:.12g},{y/1000:.12g},{z/1000:.12g}" for n, (x,y,z) in nodes.items()],
            "*ELEMENT,TYPE=C3D4,ELSET=EALL", *elements, *nset("FIXED", fixed),
            "*SOLID SECTION,ELSET=EALL,MATERIAL=STEEL", "*MATERIAL,NAME=STEEL", "*ELASTIC", "2.05e11,0.30",
            "*BOUNDARY", "FIXED,1,3,0", "*STEP", "*STATIC", "0.1,1", "*CLOAD",
            *[f"{n},1,{v:.12g}" for n,v in loads.items()], "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", ""]
    result = solve(folder, "\n".join(deck), (set(fixed), {n: tuple(v/1000 for v in xyz) for n,xyz in nodes.items()}))
    return {"force_per_bore_n": force_n, "relative_centre_bound_mm": 2*result["max_displacement_mm"],
            "result": result, "deck_sha256": sha256(folder / "model.inp")}


def main() -> None:
    geometry = json.loads((INPUT / "geometry_manifest.json").read_text())
    assert geometry["geometry_source_sha256"] == sha256(ROOT / "cad/freecad/compact/geometry.py")
    # Preserve every diagnostic run; no stale files can be mistaken for this run.
    raw = ROOT / "analysis/final_validation/results/v0.8/phase_raw"
    raw.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="run-", dir=raw))
    section_path = ROOT / "analysis/final_validation/results/v0.8/shaft_section.json"
    section = json.loads(section_path.read_text())
    assert section["status"] == "PASS" and all(sha256(ROOT / path) == digest for path, digest in section["source_sha256"].items())
    section_bound_m = section["screening_diameter_mm"] / 1000
    backlash_path = ROOT / "analysis/final_validation/results/v0.8/phase_pair_backlash_candidate.json"
    backlash_evidence = json.loads(backlash_path.read_text())
    assert all(sha256(ROOT / path) == digest for path, digest in backlash_evidence["source_sha256"].items())
    cold_backlash = backlash_evidence["cad_pair_backlash_bound_mm"]
    torque, radius, pressure_angle = 22.0, 24.0, math.radians(20)
    radial_gear = torque/(radius/1000)*math.tan(pressure_angle)
    rows = []
    for refinement in (2, 4, 8, 16):
        shaft_cases = [shaft(s, 1856.544175556756, radial_gear, sign, refinement,
                             folder/f"shaft_{key}_{sign}_{refinement}", section_bound_m)
                       for key,s in geometry["shredder_stations"].items() for sign in (-1, 1)]
        reaction = max(abs(v) for r in shaft_cases for v in r["support_reaction_n"])
        p = plate(reaction, {2:6.0, 4:4.5, 8:3.5, 16:2.5}[refinement], folder/f"plate_{refinement}")
        shaft_bound = sum(max(abs(r["gear_displacement_mm"]) for r in shaft_cases[i:i+2]) for i in (0,2))
        # Front/rear opposite support translations extrapolated to the overhang.
        s = next(iter(geometry["shredder_stations"].values()))
        a,b = s["bearing_y_mm"]
        extrapolation = 1+2*(s["gear_y_mm"]-b)/(b-a)
        centre_bound = shaft_bound+extrapolation*p["relative_centre_bound_mm"]
        backlash_delta = 2*centre_bound*math.tan(pressure_angle)
        backlash = [cold_backlash[0]-backlash_delta, cold_backlash[1]+backlash_delta]
        angle = backlash[1]/radius
        rows.append({"refinement": refinement, "shaft_cases": shaft_cases, "plate": p,
                     "centre_movement_bound_mm": centre_bound, "backlash_range_mm": backlash,
                     "backlash_angular_bound_deg": math.degrees(angle)})
    fine = rows[-1]
    convergence = abs(fine["centre_movement_bound_mm"]-rows[-2]["centre_movement_bound_mm"])/fine["centre_movement_bound_mm"]
    loaded_checks = load_loaded_phase_qualification()
    checks = {"mesh_convergence": convergence <= .05,
              "positive_loaded_backlash": fine["backlash_range_mm"][0] > 0,
              "backlash_below_one_degree": fine["backlash_angular_bound_deg"] <= 1.0 and loaded_checks["combined_worst_angle_deg"] <= loaded_checks["criterion_deg"],
              "frame_and_bearing_compliance_qualified": loaded_checks["frame_and_bearing_compliance_qualified"],
              "torsional_phase_compliance_qualified": loaded_checks["torsional_phase_compliance_qualified"]}
    result = {"revision": REV, "checks": checks, "meshes": rows, "loaded_qualification_note": loaded_checks.get("note"),
              "status": "PASS" if all(checks.values()) else "HOLD", "physical_validation_state": "NOT_RUN",
              "source_sha256": sha256(Path(__file__)), "geometry_source_sha256": geometry["geometry_source_sha256"],
              "dependencies_sha256": {p: sha256(ROOT/p) for p in (
                  "analysis/final_validation/run_calculix_v08.py", "analysis/final_validation/run_qualification_v08.py",
                  "analysis/structural/run_load_checks.py", "analysis/final_validation/input/geometry_manifest.json",
                  "analysis/final_validation/results/v0.8/shaft_section.json",
                  "analysis/final_validation/results/v0.8/phase_pair_backlash_candidate.json",
                  "analysis/final_validation/results/v0.8/phase_path_25_qualification.json")},
              "raw_directory": str(folder.relative_to(ROOT)),
              "criterion_source": "released CAD pair backlash 0.125664–0.134041 mm; 1 degree capture limit",
              "formula_source": "https://www.khkgears.us/media/1224/a-primer-on-backlash-and-its-purpose-in-gear-designs.pdf",
              "limitations": ["Cold backlash comes from released BRep interference bracketing and was not widened to force PASS.",
                 "Cutter radial envelope is applied to both shafts in opposite worst-case signs.",
                 "The Ø22 beam is bounded by the released Ø25 keyed-section minimum bending inertia; exact keyed torsion is separate CalculiX evidence.",
                 "Physical backlash, clocking, bearing clearance and loaded rotation remain NOT_RUN."]}
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n")
    print(f"V08_LOADED_PHASE_{result['status']} checks={checks} centre_mm={fine['centre_movement_bound_mm']:.6f}")
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
