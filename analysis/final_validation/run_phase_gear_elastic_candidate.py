#!/usr/bin/env python3
"""25 mm 후보 단일 18 mm 기어가 34 N·m 역하중을 받는 CalculiX 검사."""
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from run_calculix_v08 import ROOT, nset, parse_frd, reactions, read_gmsh_inp, run, sha256, ccx_executable
from run_qualification_v08 import numbers_after

RESULTS = ROOT / "analysis/final_validation/results/v0.8"


def mesh_gear(step, case, size):
    mesh = case / "gmsh.inp"
    output = run([shutil.which("gmsh") or "gmsh", str(step), "-3", "-format", "inp",
                  "-setnumber", "Mesh.Algorithm3D", "10",
                  "-setnumber", "Mesh.CharacteristicLengthMin", str(size * .55),
                  "-setnumber", "Mesh.CharacteristicLengthMax", str(size), "-o", str(mesh)],
                 ROOT, case / "gmsh.log")
    assert "ill-shaped" not in output.lower()
    return mesh


def solve_gear(case, deck, fixed, coordinates):
    (case / "model.inp").write_text(deck)
    env = os.environ.copy(); env["OMP_NUM_THREADS"] = "1"
    completed = subprocess.run([ccx_executable(), "model"], cwd=case,
                               text=True, capture_output=True, env=env, timeout=1800)
    output = completed.stdout + completed.stderr; (case / "ccx.log").write_text(output)
    assert completed.returncode == 0 and "JOB FINISHED" in output.upper()
    assert "negative jacobian" not in output.lower()
    result = parse_frd(case / "model.frd")
    result.update(status="PASS", omp_num_threads=1, negative_jacobian=False,
                  reaction=reactions(case / "model.frd", fixed, coordinates))
    return result


def main():
    geometry_path = RESULTS / "phase_path_25_candidate.json"
    geometry = json.loads(geometry_path.read_text())
    assert all(sha256(ROOT / path) == digest for path, digest in geometry["source_sha256"].items())
    step = ROOT / geometry["solid_gear_step"]
    assert sha256(step) == geometry["solid_gear_step_sha256"]
    torque_nm, pitch_radius_mm = 34.0, 24.0
    force = torque_nm / (pitch_radius_mm / 1000)
    raw = RESULTS / "phase_gear_raw"
    raw.mkdir(exist_ok=True)
    prior_path = RESULTS / "phase_gear_elastic_candidate.json"
    prior = json.loads(prior_path.read_text()) if prior_path.is_file() else {}
    cache = {row["deck_sha256"]: row for row in prior.get("meshes", [])}
    folder = Path(tempfile.mkdtemp(prefix="gear25-", dir=raw))
    rows = []
    for size in (1.5, 1.0, .7, .5, .35, .30):
        case = folder / str(size).replace(".", "p")
        case.mkdir()
        nodes, elements = read_gmsh_inp(mesh_gear(step, case, size))
        fixed = sorted(n for n, (x, _y, z) in nodes.items()
                       if abs(math.hypot(x, z) - 12.505) <= .04 and z < 8.95)
        loaded = sorted(n for n, (x, _y, z) in nodes.items() if x >= 25.5 and z >= 0)
        assert len(fixed) >= 20 and len(loaded) >= 4
        each = force / len(loaded)
        coordinates = {n: tuple(v / 1000 for v in xyz) for n, xyz in nodes.items()}
        deck = ["*HEADING", "PPR 25 mm M3 Z16 phase gear lamination tooth-tip screen; SI",
                "*NODE", *[f"{n},{x/1000:.12g},{y/1000:.12g},{z/1000:.12g}" for n, (x, y, z) in nodes.items()],
                "*ELEMENT,TYPE=C3D4,ELSET=EALL", *elements,
                *nset("FIXED", fixed), *nset("LOADED", loaded),
                "*SOLID SECTION,ELSET=EALL,MATERIAL=S45C", "*MATERIAL,NAME=S45C", "*ELASTIC", "2.05e11,0.29",
                "*BOUNDARY", "FIXED,1,3,0", "*STEP", "*STATIC", "0.1,1", "*CLOAD",
                *[f"{n},3,{each:.12g}" for n in loaded],
                "*NODE PRINT,NSET=LOADED", "U", "*NODE FILE", "U,RF", "*EL FILE", "S", "*END STEP", ""]
        deck_text = "\n".join(deck)
        (case / "model.inp").write_text(deck_text)
        deck_hash = sha256(case / "model.inp")
        cached = cache.get(deck_hash)
        if cached:
            rows.append({**cached, "cache_revalidated_by_deck_sha256": True})
            continue
        result = solve_gear(case, deck_text, set(fixed), coordinates)
        displacements = numbers_after((case / "model.dat").read_text(), "displacements (vx,vy,vz) for set LOADED")
        mean_tangent_mm = sum(row[3] for row in displacements) / len(displacements) * 1000
        residual = result["reaction"]["force_n"][2] + force
        assert abs(residual) / force <= 1e-4
        rows.append({"mesh_mm": size, "fixed_nodes": len(fixed), "loaded_nodes": len(loaded),
                     "mean_tangential_displacement_mm": mean_tangent_mm,
                     "force_residual_n": residual, "result": result,
                     "deck_sha256": deck_hash})
    change = abs(rows[-1]["mean_tangential_displacement_mm"] - rows[-2]["mean_tangential_displacement_mm"]) / rows[-1]["mean_tangential_displacement_mm"]
    assert change <= .05
    stress_change = abs(rows[-1]["result"]["max_von_mises_mpa"] - rows[-2]["result"]["max_von_mises_mpa"]) / rows[-1]["result"]["max_von_mises_mpa"]
    relative_pair_mm = 2 * rows[-1]["mean_tangential_displacement_mm"]
    conditional_sf = 355 / rows[-1]["result"]["max_von_mises_mpa"]
    output = {"status": "HOLD", "physical_validation_state": "NOT_RUN",
              "solver_and_angle_screen": "PASS",
              "conditional_strength_screen": "PASS" if conditional_sf >= 2 and stress_change <= .05 else "NOT_QUALIFIED",
              "torque_nm": torque_nm, "pitch_radius_mm": pitch_radius_mm,
              "gear_piece_count": 1, "face_width_mm": 18.0,
              "force_on_solid_gear_n": force,
              "meshes": rows, "relative_mesh_change": change,
              "peak_stress_relative_mesh_change": stress_change,
              "two_gear_relative_tangential_deflection_mm": relative_pair_mm,
              "two_gear_elastic_angle_deg": math.degrees(relative_pair_mm / pitch_radius_mm),
              "conditional_sf_at_355_mpa": conditional_sf,
              "scope": "One M3 Z16 18 mm solid S45C gear carries the full 34 N.m reverse torque. The external envelope equals the former three-lamination 18 mm stack. All bore-surface translations are fixed and load is distributed over +X tooth-tip nodes. Contact/root fillet, hub/key load transfer and actual S45C condition remain unqualified.",
              "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (Path(__file__).resolve(), step)}}
    (RESULTS / "phase_gear_elastic_candidate.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"PHASE_GEAR_ELASTIC_HOLD angle_deg={output['two_gear_elastic_angle_deg']:.6f} conditional_sf={conditional_sf:.3f}")


if __name__ == "__main__":
    main()
