#!/usr/bin/env python3
"""최악치 센서 보어의 3D 압력 응력 screen. 고온 재료/열구배 qualification 아님."""

import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import FreeCAD as App
import Part

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_calculix_v08 import ROOT, INPUT, mesh_step, nset, read_gmsh_inp, run, solve, ccx_executable

OUT = ROOT / "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json"
STEP = INPUT / "sensor_bore_local_candidate.step"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry():
    outer_radius, inner_radius, length = 16.985, 8.11, 12.0
    body = Part.makeCylinder(outer_radius, length).cut(Part.makeCylinder(inner_radius, length))
    tool = Part.makeCylinder(1.625, 5.45, App.Vector(0, outer_radius, length / 2), App.Vector(0, -1, 0))
    shape = body.cut(tool)
    assert shape.isValid() and len(shape.Solids) == 1
    shape.exportStep(str(STEP))
    return {"outer_radius_mm": outer_radius, "inner_radius_mm": inner_radius,
            "length_mm": length, "sensor_radius_mm": 1.625, "sensor_depth_mm": 5.45,
            "minimum_flat_tip_ligament_mm": outer_radius - inner_radius - 5.45}


def pressure_faces(nodes, elements, radius):
    faces = Counter()
    for line in elements:
        ids = list(map(int, line.split(",")))[1:]
        for face in ((ids[0], ids[1], ids[2]), (ids[0], ids[1], ids[3]),
                     (ids[0], ids[2], ids[3]), (ids[1], ids[2], ids[3])):
            faces[tuple(sorted(face))] += 1
    return [face for face, count in faces.items() if count == 1 and
            all(abs(math.hypot(nodes[n][0], nodes[n][1]) - radius) < 1e-4 for n in face)]


def nodal_pressure(nodes, faces, pressure_mpa, radius):
    loads = defaultdict(lambda: [0.0, 0.0, 0.0])
    area = 0.0
    for face in faces:
        a, b, c = (nodes[n] for n in face)
        cross = ((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]),
                 (b[2]-a[2])*(c[0]-a[0])-(b[0]-a[0])*(c[2]-a[2]),
                 (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
        triangle_area = math.sqrt(sum(v*v for v in cross)) / 2
        x, y = sum(nodes[n][0] for n in face) / 3, sum(nodes[n][1] for n in face) / 3
        r = math.hypot(x, y); direction = (x/r, y/r, 0.0)
        for node in face:
            for axis in range(3):
                loads[node][axis] += pressure_mpa * triangle_area * direction[axis] / 3
        area += triangle_area
    assert faces and area > 2 * math.pi * radius * 10
    return loads, area


def stress_records(path):
    import re
    pattern = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")
    mode = False; records = {}
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            mode = "STRESS" in line
        elif line.startswith(" -3"):
            mode = False
        elif mode and line.startswith(" -1"):
            row = [float(value) for value in pattern.findall(line)]
            assert len(row) == 8 and all(math.isfinite(value) for value in row)
            sx, sy, sz, txy, tyz, tzx = row[2:]
            vm = math.sqrt(.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(txy*txy+tyz*tyz+tzx*tzx))
            records[int(row[1])] = vm / 1e6
    assert records
    return records


def temperature_records(path):
    import re
    pattern = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")
    mode = False; records = {}
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            mode = "NDTEMP" in line
        elif line.startswith(" -3"):
            mode = False
        elif mode and line.startswith(" -1"):
            row = [float(value) for value in pattern.findall(line)]
            assert len(row) == 3 and math.isfinite(row[2])
            records[int(row[1])] = row[2]
    assert records
    return records


def thermal_field(case, nodes, elements, dimensions):
    inner = sorted(n for n, xyz in nodes.items() if abs(math.hypot(xyz[0], xyz[1])-dimensions["inner_radius_mm"]) < 1e-4)
    outer = sorted(n for n, xyz in nodes.items() if abs(math.hypot(xyz[0], xyz[1])-dimensions["outer_radius_mm"]) < 1e-4)
    deck = ["*HEADING", "Sensor bore conditional radial thermal field; SI m W K",
            "*NODE", *[f"{n},{x/1000:.12g},{y/1000:.12g},{z/1000:.12g}" for n,(x,y,z) in nodes.items()],
            "*ELEMENT,TYPE=DC3D4,ELSET=EALL", *elements, *nset("ALL", sorted(nodes)),
            *nset("INNER", inner), *nset("OUTER", outer),
            "*SOLID SECTION,ELSET=EALL,MATERIAL=SCM440", "*MATERIAL,NAME=SCM440",
            "*CONDUCTIVITY", "35", "*INITIAL CONDITIONS,TYPE=TEMPERATURE", "ALL,245",
            "*STEP", "*HEAT TRANSFER,STEADY STATE", "1,1", "*BOUNDARY",
            "INNER,11,11,270", "OUTER,11,11,245", "*NODE FILE", "NT", "*END STEP", ""]
    (case / "model.inp").write_text("\n".join(deck))
    env = os.environ.copy(); env["OMP_NUM_THREADS"] = "1"
    output = run([ccx_executable(), "model"], case, case / "ccx.log", env)
    assert "JOB FINISHED" in output.upper() and "negative jacobian" not in output.lower()
    values = temperature_records(case / "model.frd")
    assert set(values) == set(nodes) and 244.99 <= min(values.values()) <= 245.01 and 269.99 <= max(values.values()) <= 270.01
    return values, sha(case / "model.inp")


def main():
    dimensions = geometry()
    released_source = ROOT / "cad/freecad/compact/manufacturing.py"
    released_text = released_source.read_text(encoding="utf-8")
    release_geometry_adopted = all(token in released_text for token in (
        "3xØ3.20 +0.05/0 flat-bottom blind5.40 +/-0.05",
        "sensor=Part.makeCylinder(1.60,5.4",
    ))
    folder = Path(tempfile.mkdtemp(prefix="sensor-bore-", dir=OUT.parent))
    meshes = []
    for size in (1.0, .75, .55, .40):
        case = folder / f"mesh_{size}"; case.mkdir()
        nodes, elements = read_gmsh_inp(mesh_step(STEP, case, size))
        thermal_case = case / "thermal"; thermal_case.mkdir()
        temperatures, thermal_deck_sha = thermal_field(thermal_case, nodes, elements, dimensions)
        faces = pressure_faces(nodes, elements, dimensions["inner_radius_mm"])
        loads, loaded_area = nodal_pressure(nodes, faces, 6.0, dimensions["inner_radius_mm"])
        zfixed = sorted(n for n, xyz in nodes.items() if abs(xyz[2]) < 1e-6)
        anchor1 = min(zfixed, key=lambda n: math.dist(nodes[n], (dimensions["outer_radius_mm"], 0, 0)))
        anchor2 = min(zfixed, key=lambda n: math.dist(nodes[n], (0, dimensions["outer_radius_mm"], 0)))
        anchor3 = min(zfixed, key=lambda n: math.dist(nodes[n], (-dimensions["outer_radius_mm"], 0, 0)))
        cload = [f"{node},{axis+1},{force:.12g}" for node, vector in loads.items()
                 for axis, force in enumerate(vector) if abs(force) > 1e-12]
        deck = ["*HEADING", "Sensor bore pressure screen; SI m N Pa; assumed linear SCM440",
                "*NODE", *[f"{n},{x/1000:.12g},{y/1000:.12g},{z/1000:.12g}" for n,(x,y,z) in nodes.items()],
                "*ELEMENT,TYPE=C3D4,ELSET=EALL", *elements, *nset("ALL", sorted(nodes)),
                "*SOLID SECTION,ELSET=EALL,MATERIAL=SCM440", "*MATERIAL,NAME=SCM440",
                "*ELASTIC", "1.90e11,0.30", "*EXPANSION", "1.20e-5",
                "*INITIAL CONDITIONS,TYPE=TEMPERATURE", "ALL,20", "*BOUNDARY",
                f"{anchor1},1,3,0", f"{anchor2},2,3,0", f"{anchor3},3,3,0",
                "*STEP", "*STATIC", "0.1,1", "*TEMPERATURE",
                *[f"{node},{temperatures[node]:.12g}" for node in sorted(nodes)],
                "*CLOAD", *cload, "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", ""]
        solved = solve(case, "\n".join(deck))
        stresses = stress_records(case / "model.frd")
        regional = {n:s for n,s in stresses.items() if abs(nodes[n][2]-6) <= 3 and nodes[n][1] >= 9.5}
        assert regional
        peak_node = max(regional, key=regional.get)
        net_force = [sum(vector[i] for vector in loads.values()) for i in range(3)]
        meshes.append({"mesh_mm": size, "nodes": len(nodes), "elements": len(elements),
                       "loaded_inner_area_mm2": loaded_area, "applied_net_force_n": net_force,
                       "result": solved, "sensor_region_peak_stress_mpa": regional[peak_node],
                       "sensor_region_peak_coordinate_mm": nodes[peak_node],
                       "temperature_range_c":[min(temperatures.values()), max(temperatures.values())],
                       "thermal_deck_sha256":thermal_deck_sha, "deck_sha256": sha(case / "model.inp")})
    convergence = abs(meshes[-1]["sensor_region_peak_stress_mpa"]-meshes[-2]["sensor_region_peak_stress_mpa"])/meshes[-1]["sensor_region_peak_stress_mpa"]
    peak_stress = meshes[-1]["sensor_region_peak_stress_mpa"]
    checks = {
        "release_geometry_adopted": release_geometry_adopted,
        "four_mesh_levels_solved": len(meshes) == 4,
        "medium_to_fine_change_le_5pct": convergence <= .05,
        "conditional_regional_sf_ge_2": 177.5 / peak_stress >= 2,
        "pressure_load_self_equilibrated": all(math.sqrt(sum(v*v for v in row["applied_net_force_n"])) < .01 for row in meshes),
    }
    result = {"status":"PASS" if all(checks.values()) else "FAIL", "physical_validation_state":"NOT_RUN", "geometry":dimensions,
              "pressure_mpa":6.0, "conditional_temperature_boundary_c":{"inner":270.0,"outer":245.0},
              "meshes":meshes, "medium_to_fine_regional_stress_change":convergence,
              "required_yield_mpa_for_regional_sf_2":2*peak_stress,
              "conditional_sf_at_177p5_mpa":177.5/peak_stress,
              "checks": checks,
              "qualification_scope":"released sensor-bore geometry and converged local 3D thermoelastic stress; strength remains conditional on qualified elevated-temperature material allowable",
              "limitations":["12 mm segment with prescribed inner270/outer245 C bounds; no heater/contact/mount/die load coupling.",
                             "Sharp flat-bottom bore edge is manufacturing-tool dependent and may remain mesh sensitive.",
                             "Uniform k=35 W/mK, E=190 GPa, nu=0.30, alpha=12e-6/K and 177.5 MPa yield are conditional, not qualified actual QT/nitrided SCM440 data.",
                             "Released depth5.40±0.05 is represented; the purchased probe/retention and physical bore remain unselected/NOT_RUN."],
              "raw_directory":str(folder.relative_to(ROOT)),
              "source_sha256":{str(path.relative_to(ROOT)):sha(path) for path in
                  (Path(__file__).resolve(), STEP, ROOT/"analysis/final_validation/run_calculix_v08.py",
                   ROOT/"cad/freecad/final_v08/check_sensor_ligament_candidate.py", released_source)}}
    OUT.write_text(json.dumps(result, indent=2)+"\n")
    print(f"SENSOR_BORE_LOCAL_{result['status']} stress_mpa={peak_stress:.3f} required_yield_sf2_mpa={2*peak_stress:.3f} change={convergence:.3%}")


if __name__ == "__main__":
    main()
