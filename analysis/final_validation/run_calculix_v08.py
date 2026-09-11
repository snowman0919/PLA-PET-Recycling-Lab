#!/usr/bin/env python3
"""FreeCAD STEP -> Gmsh -> CalculiX v0.8 구조/열 mount 검증."""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUT = HERE / "input"
RAW = HERE / "results" / "v0.8" / "raw"
SUMMARY = HERE / "results" / "v0.8" / "summary.json"
from beam_torque_recovery import add_measured_root_torque

ENVELOPE = ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json"
LOAD = float(json.loads(ENVELOPE.read_text(encoding="utf-8"))["loads"]["peak_bearing_load_n"])
ALLOWABLE_MPA = 180.0

sys.path.insert(0, str(ROOT / "analysis" / "structural"))
from run_load_checks import parse_frd, plate_deck  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def helper_source_sha256() -> str:
    """Hash only helpers reused by independent CalculiX scripts, not unrelated pipeline code."""
    functions = (ccx_executable, run, mesh_step, read_gmsh_inp, nset, reactions, printed_reactions, solve, parse_frd)
    text = "\n---\n".join(inspect.getsource(fn) for fn in functions)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ccx_executable() -> str:
    candidates = []
    if os.environ.get("PPR_CCX"):
        candidates.append(Path(os.environ["PPR_CCX"]))
    candidates += sorted(Path("/nix/store").glob("*-calculix-ccx-2.23/bin/ccx")) if Path("/nix/store").is_dir() else []
    found = shutil.which("ccx")
    if found:
        candidates.append(Path(found))
    seen = set()
    for path in candidates:
        path = Path(path)
        if str(path) in seen or not path.is_file():
            continue
        seen.add(str(path))
        proc = subprocess.run([str(path), "-v"], text=True, capture_output=True, timeout=30)
        text = proc.stdout + proc.stderr
        if re.search(r"Version\s+2\.23(?:\s|$)", text):
            return str(path)
    raise RuntimeError("CalculiX 2.23 is required; refusing solver-version drift")


def run(command: list[str], cwd: Path, log: Path, env: dict[str, str] | None = None, input_text: str | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=env, input=input_text, timeout=300)
    output = result.stdout + result.stderr
    log.write_text(output)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{output[-2000:]}")
    return output


def freecad_export() -> dict:
    executable = shutil.which("FreeCADCmd") or shutil.which("freecadcmd")
    if not executable:
        raise RuntimeError("FreeCADCmd not on PATH")
    code = (
        'import runpy,sys,os,FreeCAD; '
        'runpy.run_path("cad/freecad/compact/export_validation_geometry_v08.py", run_name="__main__"); '
        'print("V08_FREECAD_VERSION="+".".join(FreeCAD.Version()[:3])); '
        'sys.stdout.flush(); os._exit(0)'
    )
    output = run([executable, "-c"], ROOT, RAW / "freecad_geometry.log", input_text=code + "\n")
    if "V08_FREECAD_GEOMETRY_OK" not in output:
        raise RuntimeError("FreeCAD geometry marker missing")
    geometry = json.loads((INPUT / "geometry_manifest.json").read_text())
    version = re.search(r"V08_FREECAD_VERSION=([0-9.]+)", output)
    if not version:
        raise RuntimeError("FreeCAD runtime version missing")
    geometry["runtime_freecad_version"] = version.group(1)
    return geometry


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


def hot_mount_deck(case: str, temperature_c: float, spring_n_m: float = 0.0,
                   pressure_mpa: float = 0.0, feed_temperature_c: float | None = None) -> str:
    nodes = [f"{index+1},{index*0.280/14:.9f},0,0" for index in range(15)]
    elements = [f"{index+1},{index+1},{index+2}" for index in range(14)]
    deck = [
        "*HEADING", f"PPR v0.8 hot-zone mount {case}; SI units m N Pa K", "*NODE", *nodes,
        "*ELEMENT,TYPE=B31,ELSET=BARREL", *elements,
        "*NSET,NSET=ALL", ",".join(str(index) for index in range(1, 16)),
        "*NSET,NSET=REAR", "1", "*NSET,NSET=FRONT", "15",
        "*BEAM SECTION,ELSET=BARREL,MATERIAL=SCM440,SECTION=RECT", "0.0265,0.0265", "0,0,1",
        "** Screening E/CTE assumptions; not qualified SCM440 temperature-dependent data",
        "*MATERIAL,NAME=SCM440", "*ELASTIC", "1.90E11,0.30", "*EXPANSION", "1.70E-5",
        "*INITIAL CONDITIONS,TYPE=TEMPERATURE", "ALL,25", "*BOUNDARY", "REAR,1,6,0",
    ]
    deck += ["FRONT,1,6,0"] if case == "A_FULLY_FIXED" else ["FRONT,2,3,0"]
    if spring_n_m:
        # ccx distinguishes DOF integers from stiffness reals by the decimal point.
        deck += ["*ELEMENT,TYPE=SPRING1,ELSET=AXIAL_SPRING", "1001,15", "*SPRING,ELSET=AXIAL_SPRING", "1", f"{spring_n_m:.9e}"]
    deck += ["*STEP", "*STATIC", "0.1,1.0", "*TEMPERATURE"]
    cold = temperature_c if feed_temperature_c is None else feed_temperature_c
    deck += [f"{i+1},{cold + (temperature_c-cold)*i/14:.9g}" for i in range(15)]
    if pressure_mpa:
        # Full bore thrust is applied; relief operation is NOT assumed successful.
        thrust_n = pressure_mpa * math.pi * 16.22**2 / 4
        deck += ["*CLOAD", f"FRONT,1,{thrust_n:.12g}"]
    deck += ["*NODE PRINT,NSET=FRONT", "U", "*NODE PRINT,NSET=REAR", "RF",
             "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", ""]
    return "\n".join(deck)


def shaft_deck(case_id: str, elements_count: int, stations: dict) -> tuple[str, dict, set[int], dict[int, tuple[float, float, float]]]:
    if case_id not in ("LC02", "LC05") or elements_count <= 0:
        raise ValueError("known load case and positive refinement required")
    origin = stations["shaft_y_min_mm"]
    front_x, rear_x = [(value-origin)/1000 for value in stations["bearing_y_mm"]]
    length = (stations["shaft_y_max_mm"]-origin)/1000
    cuts = [(value-origin)/1000 for value in stations["cutter_y_mm"]]
    if case_id == "LC05" and "chain_sprocket_y_mm" not in stations:
        raise ValueError("LC05 requires a CAD chain sprocket on this shaft")
    load_x = sum(cuts)/len(cuts) if case_id == "LC02" else (stations["chain_sprocket_y_mm"]-origin)/1000
    assert 0 < front_x < rear_x < length and 0 <= load_x <= length
    # Reuse the phase solver's station-preserving mesh pattern; never round supports.
    anchors = sorted({0.0, front_x, rear_x, load_x, length})
    refinement = max(1, elements_count//len(anchors))
    xs = [a+(b-a)*i/refinement for a,b in zip(anchors,anchors[1:]) for i in range(refinement)]+[length]
    coordinates = {index+1:(x,0.0,0.0) for index,x in enumerate(xs)}
    at = lambda value: xs.index(value)+1
    front, rear, drive = at(front_x), at(rear_x), at(0.0)
    loaded = at(load_x)
    if case_id == "LC02":
        force_n, torque_nm = LOAD, 22.0
        title = "mechanical fuse jam at cutter-stack centre"
    else:
        force_n, torque_nm = 602.7336257714462, 0.0
        title = "chain radial force at CAD driven-sprocket centre"
    reaction_nodes = {front, rear, drive}
    deck = [
        "*HEADING", f"PPR v0.8 {case_id} full 240 mm shaft; {title}; SI units m N Pa",
        "*NODE", *(f"{node},{x:.12g},0,0" for node, (x, _y, _z) in coordinates.items()),
        "*ELEMENT,TYPE=B31,ELSET=SHAFT", *(f"{index+1},{index+1},{index+2}" for index in range(len(xs)-1)),
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
        "geometry_scope": "CAD-bound shaft extent, support stations and cutter-stack centre",
        "cad_stations": stations,
        "actual_elements": len(xs)-1,
        "limitations": "Equivalent square section, assumed end torque datum and chain-force magnitude/direction remain unqualified; not keyed/contact assembly validation.",
        "material": "S45C linear elastic E=205 GPa nu=0.29",
        "support_condition": "front bearing axial+radial datum, rear bearing radial/floating; drive torsion datum",
        "load_application_node": loaded,
        "applied_torque_nm": torque_nm,
        "applied_radial_force_n": force_n,
        "load_position_from_front_bearing_mm": (coordinates[loaded][0] - front_x) * 1000,
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


def printed_reactions(path: Path, coordinates_m: dict[int, tuple[float, float, float]]) -> dict:
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
    if not forces:
        raise ValueError("No solver reaction forces in DAT")
    moment = [0.0, 0.0, 0.0]
    for node, (fx, fy, fz) in forces.items():
        x, y, z = coordinates_m[node]
        moment[0] += y*fz - z*fy
        moment[1] += z*fx - x*fz
        moment[2] += x*fy - y*fx
    return {
        "node_count": len(forces), "force_n": total, "moment_about_origin_nm": moment,
        "reaction_couple_source": "NOT_EXTRACTED; moments above are r cross measured nodal force only, excluding rotational reaction couples",
        "torsional_reaction_qualified": False,
    }


def solve(case_dir: Path, deck: str, reaction_selection: tuple[set[int], dict[int, tuple[float, float, float]]] | None = None) -> dict:
    (case_dir / "model.inp").write_text(deck)
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = "1"
    output = run([ccx_executable(), "model"], case_dir, case_dir / "ccx.log", env)
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
    geometry = json.loads((INPUT / "geometry_manifest.json").read_text())
    assert geometry["geometry_source_sha256"] == sha256(ROOT / "cad/freecad/compact/geometry.py")
    solid_path = ROOT / "analysis/final_validation/results/v0.8/solid_load_path_closure.json"
    solid = json.loads(solid_path.read_text()) if solid_path.is_file() else {}
    solid_sources = solid.get("source_sha256", {})
    solid_current = bool(solid_sources) and all((ROOT/path).is_file() and sha256(ROOT/path) == digest for path,digest in solid_sources.items())
    solid_current &= solid.get("calculix_helper_source_sha256") == helper_source_sha256()
    solid_pass = solid_current and solid.get("status") == "PASS" and bool(solid.get("checks")) and all(solid["checks"].values())
    def run_case(case_id: str, shaft_id: str, stations: dict) -> dict:
        meshes = []
        for label, count in (("coarse", 24), ("medium", 48), ("fine", 96)):
            case_dir = RAW / f"{case_id}_{shaft_id}_{label}"
            case_dir.mkdir()
            deck, provenance, selected, coordinates = shaft_deck(case_id, count, stations)
            result = solve(case_dir, deck)
            result["reaction"] = printed_reactions(case_dir / "model.dat", coordinates)
            result["reaction"] = add_measured_root_torque(result["reaction"], case_dir / "model.frd", provenance["applied_torque_nm"])
            force_residual = [a+b for a, b in zip(provenance["net_force_n"], result["reaction"]["force_n"])]
            moment_residual = [a+b for a, b in zip(provenance["net_moment_about_origin_nm"], result["reaction"]["moment_about_origin_nm"])]
            result["equilibrium"] = {"force_residual_n": force_residual, "moment_residual_nm": moment_residual}
            result["regional_safety_factor"] = 177.5 / result["max_von_mises_mpa"]
            meshes.append({"mesh": label, "elements": count, "provenance": provenance, "result": result})
        delta = abs(meshes[-1]["result"]["max_displacement_mm"] - meshes[-2]["result"]["max_displacement_mm"]) / max(meshes[-1]["result"]["max_displacement_mm"], 1e-12) * 100
        return {"meshes": meshes, "medium_to_fine_delta_percent": delta,
                "screening_status": "PASS" if delta <= 5 else "FAIL", "status": "HOLD"}
    for case_id in ("LC02", "LC05"):
        cases = {key:run_case(case_id,key,stations) for key,stations in geometry["shredder_stations"].items()
                 if case_id != "LC05" or "chain_sprocket_y_mm" in stations}
        worst = max(cases, key=lambda key: cases[key]["meshes"][-1]["result"]["max_displacement_mm"])
        beam_ok = all(row.get("screening_status") == "PASS" for row in cases.values())
        output[case_id] = {**cases[worst], "representative_shaft": worst, "per_shaft": cases,
                          "solid_load_path_evidence": {"path": str(solid_path.relative_to(ROOT)), "source_current": solid_current, "status": solid.get("status")},
                          "status": "PASS" if beam_ok and solid_pass else "HOLD",
                          "qualification_note": "CAD-station beam screen plus current keyed-solid 22 N.m load-path envelope; actual receipt/fatigue remain NOT_RUN."}
    return output


def run_hot_mount() -> dict:
    sensor_path = ROOT / "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json"
    sensor = json.loads(sensor_path.read_text()) if sensor_path.is_file() else {}
    digital_path = ROOT / "analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json"
    digital = json.loads(digital_path.read_text()) if digital_path.is_file() else {}
    digital_sources = digital.get("source_sha256", {})
    digital_current = bool(digital_sources) and all((ROOT/path).is_file() and sha256(ROOT/path) == digest for path,digest in digital_sources.items())
    digital_pass = digital_current and digital.get("status") == "PASS"
    params = json.loads((ROOT / "cad/parameters/final_v08.json").read_text())
    sensor_sources = sensor.get("source_sha256", {})
    sensor_current = bool(sensor_sources) and all((ROOT / path).is_file() and sha256(ROOT / path) == digest for path, digest in sensor_sources.items())
    sensor_checks = sensor.get("checks", {})
    sensor_qualified = sensor_current and sensor.get("status") == "PASS" and bool(sensor_checks) and all(sensor_checks.values())
    cases = (
        ("A_FULLY_FIXED", 270.0, 270.0, 6.0, 10.0, 0.0),
        ("B_ONE_AXIAL_DATUM_SLIDING", 270.0, 270.0, 6.0, 10.0, 0.0),
        ("C_RADIAL_CONTROLLED_AXIAL_EXPANSION", 270.0, 270.0, 6.0, 10.0, 0.0),
        ("D_BOUNDED_FRAME_SPRING", 270.0, 270.0, 6.0, 10.0, 1e6),
        ("E_THERMAL_ONLY", 245.0, 270.0, 0.0, 10.0, 0.0),
        ("F_PRESSURE_ONLY", 25.0, 25.0, 6.0, 0.0, 0.0),
        ("G_PET_THERMAL_BLOCKED_DIE_PRESSURE", 245.0, 270.0, 6.0, 10.0, 0.0),
    )
    rows = []
    # Source: EX-BAR-01 OD34 -0.03/0, ID16.20 +0.02/0, blind5.50±0.05.
    # The previous 83.5 MPa nominal shortcut did not include these limit sizes.
    ro, ri, depth = 33.97 / 2, 16.22 / 2, 5.55
    wall, ligament = ro-ri, ro-ri-depth
    young_mpa, alpha, poisson, kt = 190000.0, 17e-6, .30, 1.5
    assert ligament >= 3.30
    free_growth_mm = 17e-6 * (270 - 25) * 280
    for name, feed_c, die_c, pressure, gradient, spring in cases:
        case_dir = RAW / f"HOT_{name}"
        case_dir.mkdir()
        deck = hot_mount_deck(name, die_c, spring, pressure, feed_c)
        solved = solve(case_dir, deck)
        mount_stress_mpa = solved["max_von_mises_mpa"]
        pressure_local_mpa = pressure * (ro**2+ri**2)/(ro**2-ri**2) * wall/ligament * kt
        thermal_local_mpa = young_mpa * alpha * gradient/(1-poisson)
        regional = pressure_local_mpa + thermal_local_mpa + mount_stress_mpa
        sf = ALLOWABLE_MPA / regional
        rows.append({
            "study": name, "temperature_c": die_c, "feed_temperature_c": feed_c,
            "pressure_mpa": pressure, "axial_spring_n_m": spring,
            "method": "CalculiX B31 prescribed axial field + full pressure thrust; closed-form local ligament/gradient bound",
            "free_axial_growth_mm": round(alpha*((feed_c+die_c)/2-25)*280, 4),
            "mount_stress_mpa": round(mount_stress_mpa, 4),
            "pressure_sensor_bore_local_screen_mpa": pressure_local_mpa,
            "local_gradient_stress_mpa": thermal_local_mpa,
            "combined_regional_stress_mpa": round(regional, 4),
            "applied_thrust_n": pressure * math.pi * (2*ri)**2 / 4,
            "deck_sha256": sha256(case_dir / "model.inp"), "solver_result": solved,
            "safety_factor": round(sf, 3), "status": "PASS" if sf >= 2 else "FAIL",
        })
    realistic = rows[2]
    return {
        "cases": rows, "selected_mount": realistic["study"],
        "resolution": "BC04_FULL_FIX_WAS_UNREALISTICALLY_OVERCONSTRAINED",
        "selected_mount_requirement": "rear axial datum plus front radial guide; >=1.3 mm cold axial travel available",
        "local_screen_inputs": {"outer_radius_mm": ro, "inner_radius_mm": ri, "blind_depth_mm": depth,
            "ligament_mm": ligament, "young_mpa": young_mpa, "alpha_per_k": alpha,
            "poisson": poisson, "notch_factor_assumption": kt, "allowable_mpa": ALLOWABLE_MPA},
        "screening_status": "PASS" if free_growth_mm < params["hot_zone_mount"]["cold_axial_travel_mm"] and all(row["status"] == "PASS" for row in rows[1:]) else "FAIL",
        "qualification_checks": {"scm440_temperature_dependent_material_qualified": digital_pass and digital.get("checks",{}).get("material_design_floor_ge_2x_allowable") is True,
            "sensor_bore_local_stress_qualified": sensor_qualified and digital_pass,
            "die_joint_qualified": digital_pass and digital.get("checks",{}).get("die_joint_current_and_pass") is True,
            "local_temperature_gradient_qualified": digital_pass and digital.get("checks",{}).get("sensor_bore_thermoelastic_current_and_pass") is True and digital.get("checks",{}).get("all_48_radial_fit_bounds_noninterfering") is True},
        "sensor_bore_local_evidence": {"source_current": sensor_current, "status": sensor.get("status"),
            "checks": sensor_checks, "required_yield_mpa_for_sf2": sensor.get("required_yield_mpa_for_regional_sf_2")},
        "digital_qualification_evidence": {"source_current": digital_current, "status": digital.get("status"), "path": str(digital_path.relative_to(ROOT))},
        "status": "PASS" if digital_pass and all(row["status"] == "PASS" for row in rows[1:]) else "HOLD",
        "material_provenance": "Digital design contract requires >=360 MPa yield at 270 C and uses 180 MPa analysis allowable; CTE12e-6 reference with 17e-6 upper sensitivity. Received material remains a later physical gate.",
        "limitations": "Global mount remains a first-order B31 restraint screen. Independent 3D sensor-bore thermoelastic, 48-case thermal-fit and die-joint load-path evidence close the digital envelope; received material, leak-tightness and first thermal cycle remain NOT_RUN.",
    }


def main() -> None:
    global RAW
    RAW.mkdir(parents=True, exist_ok=True)
    RAW = Path(tempfile.mkdtemp(prefix="run-", dir=RAW))
    geometry = freecad_export()
    # This installed ccx prints its version but exits 201 for informational -v.
    # Solver jobs still use run()'s strict zero-exit check.
    version_proc = subprocess.run([ccx_executable(), "-v"], text=True, capture_output=True, timeout=30)
    version_text = version_proc.stdout + version_proc.stderr
    (RAW / "ccx_version.log").write_text(f"exit_code={version_proc.returncode}\n{version_text}")
    ccx_version = re.search(r"Version\s+(\S+)", version_text)
    if not ccx_version:
        raise RuntimeError("CalculiX runtime version missing")
    gmsh_version = run([shutil.which("gmsh") or "gmsh", "--version"], ROOT, RAW / "gmsh_version.log").strip()
    lc04 = run_lc04()
    shaft_cases = run_shaft_cases()
    hot_mount = run_hot_mount()
    result = {
        "revision": "final-design-fabrication-closure-v0.8", "pipeline_source_sha256": sha256(Path(__file__)),
        "process_isolation": ["FreeCADCmd", "gmsh CLI", "ccx OMP_NUM_THREADS=1", "Python postprocess"],
        "solver_versions": {"freecad": geometry["runtime_freecad_version"], "gmsh": gmsh_version, "calculix": ccx_version.group(1)},
        "geometry": geometry, **shaft_cases, "LC04": lc04, "hot_zone_mount": hot_mount,
        "raw_directory": str(RAW.relative_to(ROOT)),
        "dependencies_sha256": {"analysis/final_validation/beam_torque_recovery.py": sha256(HERE / "beam_torque_recovery.py"),
                                "cad/freecad/compact/geometry.py": sha256(ROOT / "cad/freecad/compact/geometry.py"),
                                "cad/parameters/baseline.json": sha256(ROOT / "cad/parameters/baseline.json"),
                                "cad/parameters/final_v08.json": sha256(ROOT / "cad/parameters/final_v08.json"),
                                "analysis/load_cases/openmodelica_dynamic_envelope.json": sha256(ENVELOPE),
                                "analysis/final_validation/input/geometry_manifest.json": sha256(INPUT / "geometry_manifest.json"),
                                "analysis/structural/run_load_checks.py": sha256(ROOT / "analysis/structural/run_load_checks.py"),
                                "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json": sha256(ROOT / "analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json")},
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
