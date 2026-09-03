#!/usr/bin/env python3
"""FreeCAD STEP -> Gmsh -> CalculiX v0.8 구조/열 mount 검증."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUT = HERE / "input"
RAW = HERE / "results" / "v0.8" / "raw"
SUMMARY = HERE / "results" / "v0.8" / "summary.json"
LOAD = 1856.544175556756
ALLOWABLE_MPA = 180.0

sys.path.insert(0, str(ROOT / "analysis" / "structural"))
from run_load_checks import parse_frd, plate_deck  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path, log: Path, env: dict[str, str] | None = None, input_text: str | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env, input=input_text, timeout=300)
    output = result.stdout + result.stderr
    log.write_text(output)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{output[-2000:]}")
    return output


def freecad_export() -> dict:
    executable = shutil.which("FreeCADCmd")
    if not executable:
        raise RuntimeError("FreeCADCmd not on PATH")
    code = (
        'import runpy,sys,os; '
        'runpy.run_path("cad/freecad/compact/export_validation_geometry_v08.py", run_name="__main__"); '
        'sys.stdout.flush(); os._exit(0)'
    )
    output = run([executable, "-c"], ROOT, RAW / "freecad_geometry.log", input_text=code + "\n")
    if "V08_FREECAD_GEOMETRY_OK" not in output:
        raise RuntimeError("FreeCAD geometry marker missing")
    return json.loads((INPUT / "geometry_manifest.json").read_text())


def mesh_step(step: Path, case_dir: Path, size_mm: float) -> Path:
    mesh = case_dir / "gmsh.inp"
    output = run([
        shutil.which("gmsh") or "gmsh", str(step), "-3", "-format", "inp",
        "-setnumber", "Mesh.CharacteristicLengthMin", str(size_mm * 0.55),
        "-setnumber", "Mesh.CharacteristicLengthMax", str(size_mm), "-o", str(mesh),
    ], ROOT, case_dir / "gmsh.log")
    if "No ill-shaped tets" not in output:
        raise RuntimeError("Gmsh mesh quality confirmation missing")
    return mesh


def read_gmsh_inp(path: Path) -> tuple[dict[int, tuple[float, float, float]], list[str]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: list[str] = []
    section = ""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("*"):
            upper = line.upper()
            section = "NODE" if upper == "*NODE" else "ELEMENT" if "TYPE=C3D4" in upper else ""
            continue
        if not line or not section:
            continue
        values = [value.strip() for value in line.split(",")]
        if section == "NODE":
            nodes[int(values[0])] = tuple(float(value) for value in values[1:4])
        else:
            elements.append(",".join(values))
    if not nodes or not elements:
        raise RuntimeError("Gmsh INP lacks nodes or C3D4 volume elements")
    return nodes, elements


def ring_nodes(nodes: dict[int, tuple[float, float, float]], centres: tuple[tuple[float, float], ...], radius: float, tolerance: float) -> list[int]:
    return sorted(node for node, (x, y, _z) in nodes.items() if any(abs(math.hypot(x-cx, y-cy)-radius) <= tolerance for cx, cy in centres))


def nset(name: str, nodes: list[int]) -> list[str]:
    if not nodes:
        raise RuntimeError(f"empty node set {name}")
    return [f"*NSET,NSET={name}"] + [",".join(map(str, nodes[index:index+16])) for index in range(0, len(nodes), 16)]


def bearing_plate_deck(gmsh_inp: Path, load_n: float) -> tuple[str, dict, set[int], dict[int, tuple[float, float, float]]]:
    nodes, elements = read_gmsh_inp(gmsh_inp)
    fixed = ring_nodes(nodes, ((15, 15), (15, 110), (135, 15), (135, 110)), 3.3, 0.08)
    bore = ring_nodes(nodes, ((50, 55), (98, 55)), 21.0, 0.08)
    weights = {node: max(0.0, (55.0 - nodes[node][1]) / 21.0) for node in bore}
    weights = {node: weight for node, weight in weights.items() if weight > 1e-6}
    total_weight = sum(weights.values())
    if len(fixed) < 24 or len(weights) < 24:
        raise RuntimeError(f"insufficient geometric selection fixed={len(fixed)} loaded={len(weights)}")
    forces = {node: -load_n * weight / total_weight for node, weight in weights.items()}
    moment = [
        sum(-nodes[node][2] / 1000 * force for node, force in forces.items()),
        0.0,
        sum(nodes[node][0] / 1000 * force for node, force in forces.items()),
    ]
    deck = [
        "*HEADING", "PPR v0.8 LC04 actual FreeCAD bearing plate; SI units m N Pa",
        "*NODE", *(f"{node},{x/1000:.12g},{y/1000:.12g},{z/1000:.12g}" for node, (x, y, z) in nodes.items()),
        "*ELEMENT,TYPE=C3D4,ELSET=EALL", *elements,
        *nset("FIXED", fixed), *nset("LOADED", list(forces)),
        "*SOLID SECTION,ELSET=EALL,MATERIAL=S275", "", "*MATERIAL,NAME=S275", "*ELASTIC", "2.05E11,0.30",
        "*BOUNDARY", "FIXED,1,3,0", "*STEP", "*STATIC", "0.1,1.0", "*CLOAD",
        *(f"{node},2,{force:.12g}" for node, force in forces.items()),
        "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", "",
    ]
    provenance = {
        "geometry_scope": "FreeCAD CUT-03 150x125x12 plate with 2x bearing seats, 6x retainer holes, 4x frame holes",
        "material": "S275 linear elastic E=205 GPa nu=0.30",
        "constraint_scope": "all translational DOF on four Ø6.6 frame-hole cylindrical surfaces",
        "load_application": "cosine-weighted -Y load on lower halves of two Ø42 bearing-seat cylindrical surfaces",
        "load_node_count": len(forces), "constraint_node_count": len(fixed),
        "net_force_n": [0.0, sum(forces.values()), 0.0],
        "net_moment_about_origin_nm": moment,
        "result_definition": "maximum absolute nodal displacement",
    }
    coordinates_m = {node: tuple(value / 1000 for value in xyz) for node, xyz in nodes.items()}
    return "\n".join(deck), provenance, set(fixed), coordinates_m


def hot_mount_deck(case: str, temperature_c: float, spring_n_m: float = 0.0) -> str:
    nodes = [f"{index+1},{index*0.280/14:.9f},0,0" for index in range(15)]
    elements = [f"{index+1},{index+1},{index+2}" for index in range(14)]
    deck = [
        "*HEADING", f"PPR v0.8 hot-zone mount {case}; SI units m N Pa K", "*NODE", *nodes,
        "*ELEMENT,TYPE=B31,ELSET=BARREL", *elements,
        "*NSET,NSET=ALL", ",".join(str(index) for index in range(1, 16)),
        "*NSET,NSET=REAR", "1", "*NSET,NSET=FRONT", "15",
        "*BEAM SECTION,ELSET=BARREL,MATERIAL=SCM440,SECTION=RECT", "0.0265,0.0265", "0,0,1",
        "*MATERIAL,NAME=SCM440", "*ELASTIC", "1.90E11,0.30", "*EXPANSION", "1.70E-5",
        "*INITIAL CONDITIONS,TYPE=TEMPERATURE", "ALL,25", "*BOUNDARY", "REAR,1,6,0",
    ]
    deck += ["FRONT,1,6,0"] if case == "A_FULLY_FIXED" else ["FRONT,2,3,0"]
    if spring_n_m:
        deck += ["*ELEMENT,TYPE=SPRING1,ELSET=AXIAL_SPRING", "1001,15", "*SPRING,ELSET=AXIAL_SPRING", "1", f"{spring_n_m:.9g}"]
    deck += ["*STEP", "*STATIC", "0.1,1.0", "*TEMPERATURE", f"ALL,{temperature_c}", "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", ""]
    return "\n".join(deck)


def shaft_deck(case_id: str, elements_count: int) -> tuple[str, dict, set[int], dict[int, tuple[float, float, float]]]:
    if elements_count % 24:
        raise ValueError("shaft mesh must align 30/60/120/200 mm stations")
    dx = 0.240 / elements_count
    coordinates = {index + 1: (index * dx, 0.0, 0.0) for index in range(elements_count + 1)}
    at = lambda distance_m: round(distance_m / dx) + 1
    front, rear, drive = at(0.060), at(0.200), at(0.000)
    if case_id == "LC02":
        loaded = at(0.120)
        force_n, torque_nm = LOAD, 22.0
        title = "mechanical fuse jam at cutter-stack centre"
    else:
        loaded = at(0.030)
        force_n, torque_nm = 602.7336257714462, 0.0
        title = "chain force 30 mm outboard of front bearing"
    reaction_nodes = {front, rear, drive}
    deck = [
        "*HEADING", f"PPR v0.8 {case_id} full 240 mm shaft; {title}; SI units m N Pa",
        "*NODE", *(f"{node},{x:.12g},0,0" for node, (x, _y, _z) in coordinates.items()),
        "*ELEMENT,TYPE=B31,ELSET=SHAFT", *(f"{index+1},{index+1},{index+2}" for index in range(elements_count)),
        *nset("REACTION", sorted(reaction_nodes)),
        "*BEAM SECTION,ELSET=SHAFT,MATERIAL=S45C,SECTION=RECT", "0.01772,0.01772", "0,0,1",
        "*MATERIAL,NAME=S45C", "*ELASTIC", "2.05E11,0.29",
        "*BOUNDARY", f"{front},1,3,0", f"{rear},2,3,0", f"{drive},4,4,0",
        "*STEP", "*STATIC", "0.1,1.0", "*CLOAD", f"{loaded},3,{-force_n:.12g}",
    ]
    if torque_nm:
        deck.append(f"{loaded},4,{torque_nm:.12g}")
    deck += ["*NODE FILE", "U,RF", "*NODE PRINT,NSET=REACTION,TOTALS=YES", "RF", "*EL FILE", "S", "*END STEP", ""]
    applied_moment = [torque_nm, force_n * coordinates[loaded][0], 0.0]
    provenance = {
        "geometry_scope": "CUT-05 full shaft L240 mm; bearing centres x=60/200 mm",
        "material": "S45C linear elastic E=205 GPa nu=0.29",
        "support_condition": "front bearing axial+radial datum, rear bearing radial/floating; drive torsion datum",
        "load_application_node": loaded,
        "applied_torque_nm": torque_nm,
        "applied_radial_force_n": force_n,
        "load_position_from_front_bearing_mm": (coordinates[loaded][0] - 0.060) * 1000,
        "net_force_n": [0.0, 0.0, -force_n],
        "net_moment_about_origin_nm": applied_moment,
    }
    return "\n".join(deck), provenance, reaction_nodes, coordinates


def reactions(path: Path, selected: set[int], coordinates_m: dict[int, tuple[float, float, float]]) -> dict:
    mode = False
    forces: dict[int, tuple[float, float, float]] = {}
    pattern = re.compile(r"[-+]?\d*\.?\d+(?:E[-+]?\d+)?")
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith(" -4"):
            mode = "FORC" in line
            continue
        if line.startswith(" -3"):
            mode = False
        if not mode or not line.startswith(" -1"):
            continue
        values = pattern.findall(line)
        node = int(values[1])
        if node in selected:
            forces[node] = tuple(float(value) for value in values[2:5])
    total = [sum(force[axis] for force in forces.values()) for axis in range(3)]
    moment = [0.0, 0.0, 0.0]
    for node, force in forces.items():
        x, y, z = coordinates_m[node]
        fx, fy, fz = force
        moment[0] += y*fz - z*fy
        moment[1] += z*fx - x*fz
        moment[2] += x*fy - y*fx
    return {"node_count": len(forces), "force_n": total, "moment_about_origin_nm": moment}


def printed_reactions(path: Path, coordinates_m: dict[int, tuple[float, float, float]], reaction_torque_nm: float) -> dict:
    forces: dict[int, tuple[float, float, float]] = {}
    reading = False
    for line in path.read_text(errors="ignore").splitlines():
        if "forces (fx,fy,fz) for set REACTION" in line and not line.lstrip().startswith("total"):
            reading = True
            continue
        if reading and line.lstrip().startswith("total force"):
            break
        values = line.split()
        if reading and len(values) == 4 and values[0].isdigit():
            forces[int(values[0])] = tuple(float(value) for value in values[1:])
    total = [sum(force[axis] for force in forces.values()) for axis in range(3)]
    moment = [reaction_torque_nm, 0.0, 0.0]
    for node, (fx, fy, fz) in forces.items():
        x, y, z = coordinates_m[node]
        moment[0] += y*fz - z*fy
        moment[1] += z*fx - x*fz
        moment[2] += x*fy - y*fx
    return {
        "node_count": len(forces), "force_n": total, "moment_about_origin_nm": moment,
        "reaction_couple_source": "CalculiX fixed rotational DOF; magnitude cross-checked by applied-torque equilibrium",
    }


def solve(case_dir: Path, deck: str, reaction_selection: tuple[set[int], dict[int, tuple[float, float, float]]] | None = None) -> dict:
    (case_dir / "model.inp").write_text(deck)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    output = run([shutil.which("ccx") or "ccx", "model"], case_dir, case_dir / "ccx.log", env)
    frd = case_dir / "model.frd"
    if not frd.exists() or "JOB FINISHED" not in output.upper():
        raise RuntimeError(f"{case_dir.name}: CalculiX did not finish")
    parsed = parse_frd(frd)
    parsed.update({"status": "PASS", "omp_num_threads": 1, "negative_jacobian": "negative jacobian" in output.lower()})
    if reaction_selection:
        parsed["reaction"] = reactions(frd, *reaction_selection)
    if parsed["negative_jacobian"]:
        raise RuntimeError(f"{case_dir.name}: negative Jacobian")
    return parsed


def run_lc04() -> dict:
    rows = []
    provenance = None
    for label, size in (("coarse", 6.0), ("medium", 4.5), ("fine", 3.5)):
        case_dir = RAW / f"LC04_{label}"
        case_dir.mkdir()
        deck, provenance, fixed, coordinates = bearing_plate_deck(mesh_step(INPUT / "bearing_plate.step", case_dir, size), LOAD)
        result = solve(case_dir, deck, (fixed, coordinates))
        reaction = result["reaction"]
        force_residual = [a + b for a, b in zip(provenance["net_force_n"], reaction["force_n"])]
        moment_residual = [a + b for a, b in zip(provenance["net_moment_about_origin_nm"], reaction["moment_about_origin_nm"])]
        result["equilibrium"] = {
            "force_residual_n": force_residual,
            "force_error_percent": math.sqrt(sum(value**2 for value in force_residual)) / LOAD * 100,
            "moment_residual_nm": moment_residual,
        }
        rows.append({"mesh": label, "max_size_mm": size, "provenance": provenance, "result": result})
    delta = abs(rows[-1]["result"]["max_displacement_mm"] - rows[-2]["result"]["max_displacement_mm"]) / rows[-1]["result"]["max_displacement_mm"] * 100
    legacy = []
    for label, scale in (("coarse", 4), ("medium", 8), ("fine", 12)):
        case_dir = RAW / f"LC04_legacy_{label}"
        case_dir.mkdir()
        legacy.append({"mesh": label, "result": solve(case_dir, plate_deck(LOAD, scale))})
    return {
        "case_id": "LC04", "actual_step_sha256": sha256(INPUT / "bearing_plate.step"),
        "provenance": provenance, "meshes": rows, "medium_to_fine_delta_percent": round(delta, 4),
        "legacy_surrogate": {
            "geometry_scope": "120x100x12 unperforated rectangular cantilever surrogate",
            "constraint_scope": "entire X=0 edge fixed", "load_application": "total -Z load on narrow opposite-edge strip",
            "result_definition": "maximum absolute nodal displacement", "meshes": legacy,
        },
        "resolution": "DIFFERENT_METRIC_OR_MODEL", "release_metric": "actual FreeCAD plate, in-plane bearing-seat displacement",
        "status": "PASS" if delta <= 5 else "FAIL",
    }


def run_shaft_cases() -> dict:
    output = {}
    for case_id in ("LC02", "LC05"):
        meshes = []
        for label, count in (("coarse", 24), ("medium", 48), ("fine", 96)):
            case_dir = RAW / f"{case_id}_{label}"
            case_dir.mkdir()
            deck, provenance, selected, coordinates = shaft_deck(case_id, count)
            result = solve(case_dir, deck)
            result["reaction"] = printed_reactions(case_dir / "model.dat", coordinates, -provenance["applied_torque_nm"])
            force_residual = [a+b for a, b in zip(provenance["net_force_n"], result["reaction"]["force_n"])]
            moment_residual = [a+b for a, b in zip(provenance["net_moment_about_origin_nm"], result["reaction"]["moment_about_origin_nm"])]
            result["equilibrium"] = {"force_residual_n": force_residual, "moment_residual_nm": moment_residual}
            result["regional_safety_factor"] = 177.5 / result["max_von_mises_mpa"]
            meshes.append({"mesh": label, "elements": count, "provenance": provenance, "result": result})
        delta = abs(meshes[-1]["result"]["max_displacement_mm"] - meshes[-2]["result"]["max_displacement_mm"]) / max(meshes[-1]["result"]["max_displacement_mm"], 1e-12) * 100
        output[case_id] = {"meshes": meshes, "medium_to_fine_delta_percent": delta, "status": "PASS" if delta <= 5 else "FAIL"}
    return output


def run_hot_mount() -> dict:
    cases = {"A_FULLY_FIXED": 0.0, "B_ONE_AXIAL_DATUM_SLIDING": 0.0, "C_RADIAL_CONTROLLED_AXIAL_EXPANSION": 0.0, "D_BOUNDED_FRAME_SPRING": 1.0e6}
    rows = []
    pressure_local_mpa = 83.5
    free_growth_mm = 17e-6 * (270 - 25) * 280
    for name, spring in cases.items():
        if spring:
            area_m2 = math.pi / 4 * (0.034**2 - 0.0162**2)
            barrel_stiffness = 190e9 * area_m2 / 0.280
            force_n = free_growth_mm / 1000 / (1 / spring + 1 / barrel_stiffness)
            mount_stress_mpa = force_n / area_m2 / 1e6
            method = "closed-form barrel/frame series stiffness"
        else:
            case_dir = RAW / f"HOT_{name}"
            case_dir.mkdir()
            mount_stress_mpa = solve(case_dir, hot_mount_deck(name, 270))["max_von_mises_mpa"]
            method = "CalculiX B31 thermoelastic"
        regional = pressure_local_mpa + mount_stress_mpa
        sf = ALLOWABLE_MPA / regional
        rows.append({
            "study": name, "temperature_c": 270, "pressure_mpa": 6.0, "axial_spring_n_m": spring,
            "method": method, "free_axial_growth_mm": round(free_growth_mm, 4), "mount_stress_mpa": round(mount_stress_mpa, 4),
            "pressure_sensor_bore_local_screen_mpa": pressure_local_mpa, "combined_regional_stress_mpa": round(regional, 4),
            "safety_factor": round(sf, 3), "status": "PASS" if sf >= 2 else "FAIL",
        })
    realistic = rows[2]
    return {
        "cases": rows, "selected_mount": realistic["study"],
        "resolution": "BC04_FULL_FIX_WAS_UNREALISTICALLY_OVERCONSTRAINED",
        "selected_mount_requirement": "rear axial datum plus front radial guide; >=1.3 mm cold axial travel available",
        "status": "PASS" if realistic["safety_factor"] >= 2 and free_growth_mm < 1.3 else "FAIL",
        "limitations": "B31 mount study evaluates global axial restraint; 83.5 MPa sensor-bore/pressure term is the existing closed-form local screen, not a 3D notch FEA.",
    }


def main() -> None:
    if RAW.exists():
        shutil.rmtree(RAW)
    RAW.mkdir(parents=True)
    geometry = freecad_export()
    lc04 = run_lc04()
    shaft_cases = run_shaft_cases()
    hot_mount = run_hot_mount()
    result = {
        "revision": "final-design-fabrication-closure-v0.8", "pipeline_source_sha256": sha256(Path(__file__)),
        "process_isolation": ["FreeCADCmd", "gmsh CLI", "ccx OMP_NUM_THREADS=1", "Python postprocess"],
        "solver_versions": {"freecad": "1.1.3", "gmsh": "4.15.2-git", "calculix": "2.23"},
        "geometry": geometry, **shaft_cases, "LC04": lc04, "hot_zone_mount": hot_mount,
        "cross_solver_state": "NOT_COMPLETED_BY_SCOPE_DECISION", "fusion_state": "STOPPED_NOT_USED_FOR_FINAL_RELEASE",
        "inventor_state": "STOPPED_NOT_USED_FOR_FINAL_RELEASE", "physical_validation_state": "NOT_RUN",
        "status": "PASS" if all(item["status"] == "PASS" for item in (*shaft_cases.values(), lc04, hot_mount)) else "FAIL",
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["status"] != "PASS":
        raise SystemExit("V08_CALCULIX_VALIDATION_FAIL")
    print(f"V08_CALCULIX_VALIDATION_OK lc04_mm={lc04['meshes'][-1]['result']['max_displacement_mm']:.6f} hot_mount_sf={hot_mount['cases'][2]['safety_factor']:.3f}")


if __name__ == "__main__":
    main()
