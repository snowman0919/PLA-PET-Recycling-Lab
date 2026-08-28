#!/usr/bin/env python3
"""Run a reproducible CAD-based linear-static Stage-1 cutter screen.

The model intentionally fixes the cutter bore and distributes a tangential
force over a finite tooth-tip node patch.  It is a geometry/root stress screen,
not nonlinear shaft contact, impact, fatigue, or physical validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STEP = ROOT / "exports" / "step" / "stage1_cutter_disc.step"
OUTPUT = ROOT / "simulation" / "structural" / "stage1_cutter_3d_fea.json"


@dataclass(frozen=True)
class Mesh:
    nodes: dict[int, tuple[float, float, float]]
    tetrahedra: dict[int, tuple[int, int, int, int]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    text = (result.stdout + result.stderr).strip()
    if not text:
        raise RuntimeError(f"version command produced no output: {' '.join(command)}")
    return text.splitlines()[0]


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}\n{result.stderr}"
        )


def read_msh2(path: Path) -> Mesh:
    lines = path.read_text().splitlines()
    nodes: dict[int, tuple[float, float, float]] = {}
    tetrahedra: dict[int, tuple[int, int, int, int]] = {}
    i = 0
    while i < len(lines):
        if lines[i] == "$Nodes":
            count = int(lines[i + 1])
            for line in lines[i + 2 : i + 2 + count]:
                fields = line.split()
                nodes[int(fields[0])] = tuple(float(v) for v in fields[1:4])
            i += count + 2
        elif lines[i] == "$Elements":
            count = int(lines[i + 1])
            for line in lines[i + 2 : i + 2 + count]:
                fields = [int(v) for v in line.split()]
                element_id, element_type, tag_count = fields[:3]
                connectivity = fields[3 + tag_count :]
                if element_type == 4:  # linear four-node tetrahedron
                    tetrahedra[element_id] = tuple(connectivity)  # type: ignore[assignment]
            i += count + 2
        i += 1
    if not nodes or not tetrahedra:
        raise ValueError(f"no 3D tetrahedral mesh in {path}")
    return Mesh(nodes, tetrahedra)


def chunks(values: list[int], width: int = 16) -> list[str]:
    return [", ".join(str(v) for v in values[i : i + width]) for i in range(0, len(values), width)]


def boundary_nodes(mesh: Mesh) -> set[int]:
    faces: dict[tuple[int, int, int], int] = {}
    for a, b, c, d in mesh.tetrahedra.values():
        for face in ((a, b, c), (a, b, d), (a, c, d), (b, c, d)):
            key = tuple(sorted(face))
            faces[key] = faces.get(key, 0) + 1
    return {node for face, count in faces.items() if count == 1 for node in face}


def write_ccx_input(path: Path, mesh: Mesh, proof_torque_nm: float) -> dict[str, object]:
    exterior = boundary_nodes(mesh)
    # STEP axis is Z.  Excluding the z=0/6 end faces prevents an artificial
    # clamped annulus; only the cylindrical/keyway bore surface is restrained.
    fixed = sorted(
        node for node, (x, y, _z) in mesh.nodes.items()
        if node in exterior and math.hypot(x, y) <= 12.8 and 0.2 < _z < 5.8
    )
    # One finite patch on the +X tooth tip.  A 2.0 mm radial band provides
    # multiple load nodes at both faces and avoids a single-node point load.
    loaded = sorted(
        node for node, (x, y, _z) in mesh.nodes.items()
        if node in exterior and math.hypot(x, y) >= 28.0 and x >= 28.0 and abs(y) <= 2.8
    )
    if len(fixed) < 12 or len(loaded) < 4:
        raise ValueError(f"invalid node selections fixed={len(fixed)} loaded={len(loaded)}")

    effective_radius_mm = sum(mesh.nodes[n][0] for n in loaded) / len(loaded)
    represented_torque_nm = proof_torque_nm / 2.0
    total_force_n = represented_torque_nm / (effective_radius_mm / 1000.0)
    force_per_node_n = total_force_n / len(loaded)
    lines = ["*HEADING", "Stage 1 cutter CAD linear static screen", "*NODE"]
    lines.extend(f"{n}, {x:.9g}, {y:.9g}, {z:.9g}" for n, (x, y, z) in sorted(mesh.nodes.items()))
    lines.append("*ELEMENT, TYPE=C3D4, ELSET=ECUTTER")
    lines.extend(f"{e}, {a}, {b}, {c}, {d}" for e, (a, b, c, d) in sorted(mesh.tetrahedra.items()))
    lines.extend(["*NSET, NSET=NFIX", *chunks(fixed), "*NSET, NSET=NLOAD", *chunks(loaded)])
    lines.extend(["*NSET, NSET=NALL", *chunks(sorted(mesh.nodes))])
    lines.extend([
        "*MATERIAL, NAME=STEEL_PROVISIONAL",
        "*ELASTIC",
        "210000., 0.30",
        "*SOLID SECTION, ELSET=ECUTTER, MATERIAL=STEEL_PROVISIONAL",
        "*BOUNDARY",
        "NFIX, 1, 3, 0.",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ])
    # Tangential -Y loading on the +X tooth.  Individual records keep total
    # force exactly independent of solver set-load interpretation.
    lines.extend(f"{node}, 2, {-force_per_node_n:.12g}" for node in loaded)
    lines.extend([
        "*NODE PRINT, NSET=NALL",
        "U",
        "*NODE PRINT, NSET=NFIX",
        "RF",
        "*EL PRINT, ELSET=ECUTTER",
        "S",
        "*NODE FILE, NSET=NALL",
        "U",
        "*EL FILE, ELSET=ECUTTER",
        "S",
        "*END STEP",
    ])
    path.write_text("\n".join(lines) + "\n")
    return {
        "fixed_node_count": len(fixed),
        "loaded_node_count": len(loaded),
        "effective_load_radius_mm": effective_radius_mm,
        "represented_single_tooth_torque_nm": represented_torque_nm,
        "total_applied_force_n": total_force_n,
        "force_per_node_n": force_per_node_n,
    }


FLOAT = r"[-+]?(?:\d+\.?(?:\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?"


def numbers(line: str) -> list[float]:
    return [float(token.replace("D", "E")) for token in re.findall(FLOAT, line)]


def parse_dat(path: Path) -> dict[str, float]:
    lines = path.read_text(errors="replace").splitlines()
    mode = ""
    max_displacement_mm = 0.0
    max_von_mises_mpa = 0.0
    reaction = [0.0, 0.0, 0.0]
    displacement_rows = stress_rows = reaction_rows = 0
    for line in lines:
        lower = line.lower()
        if "displacements (vx,vy,vz)" in lower:
            mode = "u"
            continue
        if "forces (fx,fy,fz)" in lower:
            mode = "rf"
            continue
        if "stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)" in lower:
            mode = "s"
            continue
        vals = numbers(line)
        if mode == "u" and len(vals) == 4:
            max_displacement_mm = max(max_displacement_mm, math.sqrt(sum(v * v for v in vals[1:4])))
            displacement_rows += 1
        elif mode == "rf" and len(vals) == 4:
            for axis in range(3):
                reaction[axis] += vals[axis + 1]
            reaction_rows += 1
        elif mode == "s" and len(vals) == 8:
            sxx, syy, szz, sxy, sxz, syz = vals[2:8]
            vm = math.sqrt(
                0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
                + 3.0 * (sxy * sxy + sxz * sxz + syz * syz)
            )
            max_von_mises_mpa = max(max_von_mises_mpa, vm)
            stress_rows += 1
    if not displacement_rows or not stress_rows or not reaction_rows:
        raise ValueError(
            f"incomplete CalculiX .dat parse: U={displacement_rows} S={stress_rows} RF={reaction_rows}"
        )
    return {
        "maximum_displacement_mm": max_displacement_mm,
        "maximum_integration_point_von_mises_mpa": max_von_mises_mpa,
        "reaction_x_n": reaction[0],
        "reaction_y_n": reaction[1],
        "reaction_z_n": reaction[2],
    }


def solve_case(work: Path, label: str, mesh_size_mm: float, proof_torque_nm: float) -> dict[str, object]:
    msh = work / f"{label}.msh"
    run([
        "gmsh", str(STEP), "-3", "-format", "msh2", "-clmax", str(mesh_size_mm),
        "-v", "2", "-o", str(msh),
    ], work)
    mesh = read_msh2(msh)
    job = work / label
    selection = write_ccx_input(job.with_suffix(".inp"), mesh, proof_torque_nm)
    run(["ccx", "-i", label], work)
    result = parse_dat(job.with_suffix(".dat"))
    return {
        "label": label,
        "maximum_element_size_mm": mesh_size_mm,
        "node_count": len(mesh.nodes),
        "tetrahedron_count": len(mesh.tetrahedra),
        **selection,
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if not STEP.exists():
        raise SystemExit(f"missing CAD input: {STEP}")
    for executable in ("gmsh", "ccx"):
        if shutil.which(executable) is None:
            raise SystemExit(f"missing {executable}; enter `nix develop`")

    proof_torque_nm = 60.0
    provisional_yield_mpa = 650.0
    with tempfile.TemporaryDirectory(prefix="ppr-stage1-fea-") as tmp:
        work = Path(tmp)
        coarse = solve_case(work, "coarse", 2.0, proof_torque_nm)
        fine = solve_case(work, "fine", 1.5, proof_torque_nm)

    convergence = abs(
        float(fine["maximum_displacement_mm"]) - float(coarse["maximum_displacement_mm"])
    ) / float(fine["maximum_displacement_mm"])
    reaction_error = abs(float(fine["reaction_y_n"]) - float(fine["total_applied_force_n"])) / float(
        fine["total_applied_force_n"]
    )
    safety_factor = provisional_yield_mpa / float(fine["maximum_integration_point_von_mises_mpa"])
    checks = {
        "maximum_displacement_le_0_0667_mm": float(fine["maximum_displacement_mm"]) <= 0.0667,
        "provisional_linear_static_yield_sf_ge_1_5": safety_factor >= 1.5,
        "coarse_fine_displacement_delta_le_5_percent": convergence <= 0.05,
        "force_balance_error_le_1_percent": reaction_error <= 0.01,
    }
    load_case_torques = (
        ("PET nominal tear", 6.3),
        ("PLA printed shell nominal", 27.0),
        ("PET folded/local double engagement", 36.8),
        ("PLA thick shell overload", 54.0),
        ("structural proof", 60.0),
    )
    linear_load_cases = []
    for name, system_torque_nm in load_case_torques:
        scale = system_torque_nm / proof_torque_nm
        stress_mpa = float(fine["maximum_integration_point_von_mises_mpa"]) * scale
        linear_load_cases.append({
            "name": name,
            "system_torque_nm": system_torque_nm,
            "represented_single_tooth_torque_nm": system_torque_nm / 2.0,
            "maximum_displacement_mm": float(fine["maximum_displacement_mm"]) * scale,
            "maximum_integration_point_von_mises_mpa": stress_mpa,
            "provisional_yield_safety_factor": provisional_yield_mpa / stress_mpa,
            "method": "linear scaling of the converged 60 N.m system proof case",
        })
    report = {
        "schema": "ppr.stage1_cutter_3d_linear_static.v1",
        "status": "CAD_BASED_LINEAR_STATIC_SCREEN_ONLY_NOT_CONTACT_IMPACT_FATIGUE_OR_PHYSICAL_VALIDATION",
        "input": {
            "step_path": str(STEP.relative_to(ROOT)),
            "step_sha256": sha256(STEP),
            "proof_torque_nm": proof_torque_nm,
            "load_sharing": "two simultaneously engaged teeth; one modeled tooth receives half total force",
            "material": {
                "name": "provisional heat-treated steel candidate",
                "elastic_modulus_mpa": 210000.0,
                "poisson_ratio": 0.3,
                "yield_strength_mpa": provisional_yield_mpa,
                "qualification": "TBD by supplier certificate and heat-treatment coupon",
            },
            "boundary": "all translational DOF fixed on exterior CAD bore/keyway cylindrical surface nodes; end faces excluded",
            "load": "finite +X tooth-tip node patch, tangential -Y force",
        },
        "solver": {
            "gmsh": version(["gmsh", "--version"]),
            "calculix": version(["ccx", "-v"]),
            "element": "C3D4 linear tetrahedron",
        },
        "meshes": [coarse, fine],
        "derived": {
            "fine_mesh_provisional_yield_safety_factor": safety_factor,
            "coarse_fine_displacement_relative_delta": convergence,
            "fine_mesh_force_balance_relative_error": reaction_error,
        },
        "linear_load_cases": linear_load_cases,
        "acceptance_checks": checks,
        "limitations": [
            "fixed bore is not shaft/keyway contact and omits fit, slip, and bearing compliance",
            "distributed nodal load is not nonlinear cutter/material contact",
            "linear elasticity omits impact, plasticity, fracture, fatigue, wear, and residual stress",
            "maximum stress can remain mesh/load-patch sensitive; physical cutter coupon remains mandatory",
            "provisional material properties require supplier certificate and heat-treatment verification",
        ],
        "overall_screen_pass": all(checks.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if not report["overall_screen_pass"]:
        raise SystemExit("STAGE1_CUTTER_3D_FEA_SCREEN_FAILED")
    print(
        "STAGE1_CUTTER_3D_FEA_OK "
        f"nodes={fine['node_count']} tets={fine['tetrahedron_count']} "
        f"disp={fine['maximum_displacement_mm']:.6f}mm sf={safety_factor:.3f}"
    )


if __name__ == "__main__":
    main()
