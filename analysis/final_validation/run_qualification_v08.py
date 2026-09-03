#!/usr/bin/env python3
"""CalculiX torsion/thermal/modal benchmark와 subsystem SF를 clean-run한다."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "analysis/final_validation/results/v0.8/qualification_raw"
OUT = ROOT / "analysis/final_validation/results/v0.8/qualification_summary.json"
E, NU, RHO = 205e9, 0.29, 7850.0


def run(name: str, deck: str) -> tuple[Path, str]:
    case = RAW / name
    if case.exists():
        shutil.rmtree(case)
    case.mkdir(parents=True)
    (case / "model.inp").write_text(deck)
    env = dict(os.environ); env["OMP_NUM_THREADS"] = "1"
    proc = subprocess.run(["ccx", "model"], cwd=case, env=env, text=True, capture_output=True, timeout=120)
    log = proc.stdout + proc.stderr
    (case / "ccx.log").write_text(log)
    if proc.returncode or not (case / "model.dat").is_file():
        raise RuntimeError(f"{name}: CalculiX failed\n{log[-2000:]}")
    return case, (case / "model.dat").read_text(errors="ignore")


def numbers_after(text: str, heading: str) -> list[list[float]]:
    block = text.split(heading, 1)[-1]
    rows = []
    for line in block.splitlines():
        vals = re.findall(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?", line)
        if len(vals) >= 2:
            rows.append([float(v) for v in vals])
        elif rows and not line.strip():
            break
    return rows


def beam_nodes(length: float, count: int) -> tuple[list[str], list[str]]:
    nodes = [f"{i + 1},{length * i / (2 * count):.9f},0,0" for i in range(2 * count + 1)]
    elements = [f"{i + 1},{2*i + 1},{2*i + 2},{2*i + 3}" for i in range(count)]
    return nodes, elements


def set_lines(values: list[str]) -> list[str]:
    return [",".join(values[i:i + 16]) for i in range(0, len(values), 16)]


def torsion() -> dict:
    length, side, torque, nx, ny = 0.24, 0.020, 22.0, 24, 6
    node_id = lambda i, j, k: i * (ny + 1) ** 2 + j * (ny + 1) + k + 1
    nodes, elements, fixed, free, loads = [], [], [], [], []
    transverse = [(j, k, -side / 2 + side * j / ny, -side / 2 + side * k / ny)
                  for j in range(ny + 1) for k in range(ny + 1)]
    radius_sum = sum(y * y + z * z for _, _, y, z in transverse)
    for i in range(nx + 1):
        for j, k, y, z in transverse:
            nid = node_id(i, j, k)
            nodes.append(f"{nid},{length * i / nx:.9f},{y:.9f},{z:.9f}")
            if i == 0:
                fixed.append(str(nid))
            if i == nx:
                free.append(str(nid))
                loads.extend((f"{nid},2,{-torque * z / radius_sum:.12g}",
                              f"{nid},3,{torque * y / radius_sum:.12g}"))
    eid = 1
    for i in range(nx):
        for j in range(ny):
            for k in range(ny):
                elements.append(f"{eid},{node_id(i,j,k)},{node_id(i+1,j,k)},{node_id(i+1,j+1,k)},"
                                f"{node_id(i,j+1,k)},{node_id(i,j,k+1)},{node_id(i+1,j,k+1)},"
                                f"{node_id(i+1,j+1,k+1)},{node_id(i,j+1,k+1)}")
                eid += 1
    deck = "\n".join(["*HEADING", "v0.8 torsion qualification; SI",
        "*NODE", *nodes, "*ELEMENT,TYPE=C3D8,ELSET=EALL", *elements,
        "*NSET,NSET=FIXED", *set_lines(fixed), "*NSET,NSET=FREE", *set_lines(free),
        "*SOLID SECTION,ELSET=EALL,MATERIAL=STEEL", "*MATERIAL,NAME=STEEL", "*ELASTIC", f"{E},{NU}",
        "*BOUNDARY", "FIXED,1,6,0", "*STEP", "*STATIC", "0.1,1",
        "*CLOAD", *loads, "*NODE PRINT,NSET=FREE", "U",
        "*NODE PRINT,NSET=FIXED,TOTALS=YES", "RF", "*END STEP", ""])
    _, dat = run("torsion", deck)
    disp = numbers_after(dat, "displacements (vx,vy,vz) for set FREE")
    reaction = numbers_after(dat, "forces (fx,fy,fz) for set FIXED")
    coords = {node_id(nx, j, k): (y, z) for j, k, y, z in transverse}
    rotations = [(-coords[int(row[0])][1] * row[2] + coords[int(row[0])][0] * row[3],
                  coords[int(row[0])][0] ** 2 + coords[int(row[0])][1] ** 2)
                 for row in disp if len(row) >= 4 and int(row[0]) in coords]
    twist = abs(sum(value for value, _ in rotations) / sum(weight for _, weight in rotations)) if rotations else 0.0
    fixed_coords = {node_id(0, j, k): (y, z) for j, k, y, z in transverse}
    reacted = abs(sum(-fixed_coords[int(row[0])][1] * row[2] + fixed_coords[int(row[0])][0] * row[3]
                      for row in reaction if len(row) >= 4 and int(row[0]) in fixed_coords))
    shear_modulus = E / (2 * (1 + NU)); torsion_constant = 0.1406 * side**4
    expected = torque * length / (shear_modulus * torsion_constant)
    error = abs(twist - expected) / expected if expected else 1
    equilibrium_error = abs(reacted - torque) / torque if reacted else 1
    return {"method": "CalculiX C3D8 square bar vs Saint-Venant", "twist_rad": twist, "expected_rad": expected,
            "relative_error": error, "reaction_moment_nm": reacted, "equilibrium_error": equilibrium_error,
            "status": "PASS" if error <= 0.08 and equilibrium_error <= 1e-4 else "FAIL"}


def thermal() -> dict:
    length, alpha, delta_t, count = 0.35, 12e-6, 250.0, 14
    nodes, elements = beam_nodes(length, count)
    deck = "\n".join(["*HEADING", "v0.8 free thermal expansion qualification; SI",
        "*NODE", *nodes, "*ELEMENT,TYPE=B32,ELSET=EALL", *elements,
        "*NSET,NSET=FIXED", "1", "*NSET,NSET=FREE", str(2 * count + 1), "*NSET,NSET=NALL,GENERATE", f"1,{2*count+1},1",
        "*BEAM SECTION,ELSET=EALL,MATERIAL=STEEL,SECTION=CIRC", "0.008,0.008", "0,0,1",
        "*MATERIAL,NAME=STEEL", "*ELASTIC", f"{E},{NU}", "*EXPANSION", str(alpha),
        "*INITIAL CONDITIONS,TYPE=TEMPERATURE", "NALL,20", "*BOUNDARY", "FIXED,1,6,0", f"FREE,2,6,0",
        "*STEP", "*STATIC", "0.1,1", "*TEMPERATURE", f"NALL,{20+delta_t}",
        "*NODE PRINT,NSET=FREE", "U", "*END STEP", ""])
    _, dat = run("thermal", deck)
    disp = numbers_after(dat, "displacements (vx,vy,vz) for set FREE")
    growth = abs(disp[-1][1]) if disp and len(disp[-1]) >= 4 else 0.0
    expected = alpha * delta_t * length
    error = abs(growth - expected) / expected if expected else 1
    return {"method": "CalculiX B32 vs alpha*dT*L", "growth_mm": growth * 1000, "expected_mm": expected * 1000,
            "relative_error": error, "status": "PASS" if error <= 0.01 else "FAIL"}


def modal() -> dict:
    length, diameter, count = 0.60, 0.020, 40
    nodes, elements = beam_nodes(length, count)
    deck = "\n".join(["*HEADING", "v0.8 cantilever modal qualification; SI",
        "*NODE", *nodes, "*ELEMENT,TYPE=B32,ELSET=EALL", *elements,
        "*NSET,NSET=FIXED", "1", "*BEAM SECTION,ELSET=EALL,MATERIAL=STEEL,SECTION=CIRC", f"{diameter},{diameter}", "0,0,1",
        "*MATERIAL,NAME=STEEL", "*ELASTIC", f"{E},{NU}", "*DENSITY", str(RHO),
        "*BOUNDARY", "FIXED,1,6,0", "*STEP", "*FREQUENCY", "3", "*NODE FILE", "U", "*END STEP", ""])
    _, dat = run("modal", deck)
    match = re.search(r"E\s+I\s+G\s+E\s+N\s+V\s+A\s+L\s+U\s+E\s+O\s+U\s+T\s+P\s+U\s+T(.*?)"
                      r"(?:P\s+A\s+R\s+T\s+I\s+C\s+I\s+P\s+A\s+T\s+I\s+O\s+N|$)", dat, re.S)
    rows = []
    if match:
        for line in match.group(1).splitlines():
            vals = re.findall(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?", line)
            if len(vals) >= 4:
                rows.append([float(v) for v in vals])
    frequency = rows[0][-2] if rows else 0.0
    area = math.pi * diameter**2 / 4; inertia = math.pi * diameter**4 / 64
    expected = 1.875104**2 / (2 * math.pi) * math.sqrt(E * inertia / (RHO * area * length**4))
    error = abs(frequency - expected) / expected if expected else 1
    return {"method": "CalculiX B32 vs Euler-Bernoulli cantilever", "frequency_hz": frequency, "expected_hz": expected,
            "relative_error": error, "status": "PASS" if error <= 0.05 else "FAIL"}


def subsystem_checks() -> dict[str, dict]:
    radial = json.loads((ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json").read_text())["loads"]["peak_bearing_load_n"]

    def result(method: str, stress: float, allowable: float, **evidence: float | str) -> dict:
        safety_factor = allowable / stress
        return {"method": method, "equivalent_stress_mpa": stress, "allowable_mpa": allowable,
                "safety_factor": safety_factor, "status": "PASS" if safety_factor >= 2 else "FAIL", **evidence}

    cutter_force = 22.0 / 0.029
    cutter_stress = 6 * cutter_force * 0.011 / (0.006 * 0.012**2) / 1e6
    cutter = result("CUT-01 D2 tooth-root closed-form bending", cutter_stress, 350.0,
                    design_torque_nm=22.0, root_width_mm=12.0, thickness_mm=6.0,
                    limitations="impact/notch factor requires Gate-1 physical coupon; digital SF uses conservative 350 MPa allowable")
    feeder_torque, feeder_diameter = 2.2, 0.008
    feeder_vm = math.sqrt(3) * 16 * feeder_torque / (math.pi * feeder_diameter**3) / 1e6
    feeder = result("FD-MET-03 Ø8 solid-shaft torsion", feeder_vm, 102.5,
                    design_torque_nm=feeder_torque, shaft_diameter_mm=8.0,
                    limitations="donor torque and 304 shaft material require receipt verification before fabrication")
    spool_load, bearing_span, diameter = 1.35 * 9.80665 + 8.0, 0.088, 0.012
    spool_moment = spool_load * bearing_span / 4
    spool_stress = 32 * spool_moment / (math.pi * diameter**3) / 1e6
    spool = result("SP-SH-01 Ø12 simply-supported midspan bending", spool_stress, 100.0,
                   radial_load_n=spool_load, bearing_span_mm=88.0, shaft_diameter_mm=12.0,
                   limitations="received spool mass, bearing fit and dynamic tension require Gate-5 physical verification")
    anchor_area = math.pi * 0.006466**2 / 4
    frame_stress = radial / anchor_area / 1e6
    frame = result("FR-ANCHOR-01 one-anchor conservative tension", frame_stress, 320.0,
                   applied_load_n=radial, anchor_minor_diameter_mm=6.466,
                   limitations="four-anchor table installation and substrate require physical verification")
    return {"cutter_root": cutter, "frame": frame, "feeder": feeder, "spool": spool}


def main() -> None:
    checks = {"torsion": torsion(), "thermal": thermal(), "modal": modal(), **subsystem_checks()}
    result = {"revision": "final-design-fabrication-closure-v0.8", "solver": "CalculiX OMP_NUM_THREADS=1",
              "checks": checks, "status": "PASS" if all(v["status"] == "PASS" for v in checks.values()) else "FAIL",
              "physical_validation_state": "NOT_RUN"}
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"V08_CALCULIX_QUALIFICATION_{result['status']} " + " ".join(f"{k}={v['status']}" for k, v in checks.items()))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
