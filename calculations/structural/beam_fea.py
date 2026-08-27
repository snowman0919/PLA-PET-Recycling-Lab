#!/usr/bin/env python3
"""Deterministic Euler-Bernoulli finite-element screening cross-checks.

This is a 1D linear-elastic model for early load-path screening. It is not a
3D contact, impact, fatigue, joint, keyway, weld, pressure, or certification
analysis.
"""

from __future__ import annotations

import json
from math import pi, sqrt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def solve_linear(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    a = [row[:] + [value] for row, value in zip(matrix, rhs)]
    n = len(rhs)
    for pivot in range(n):
        best = max(range(pivot, n), key=lambda row: abs(a[row][pivot]))
        assert abs(a[best][pivot]) > 1e-18, "singular stiffness matrix"
        a[pivot], a[best] = a[best], a[pivot]
        scale = a[pivot][pivot]
        a[pivot] = [value / scale for value in a[pivot]]
        for row in range(n):
            if row == pivot:
                continue
            factor = a[row][pivot]
            if factor:
                a[row] = [left - factor * right for left, right in zip(a[row], a[pivot])]
    return [a[row][-1] for row in range(n)]


def beam_element_stiffness(ei: float, length: float) -> list[list[float]]:
    factor = ei / length**3
    return [[factor * value for value in row] for row in (
        (12.0, 6.0 * length, -12.0, 6.0 * length),
        (6.0 * length, 4.0 * length**2, -6.0 * length, 2.0 * length**2),
        (-12.0, -6.0 * length, 12.0, -6.0 * length),
        (6.0 * length, 2.0 * length**2, -6.0 * length, 4.0 * length**2),
    )]


def beam_fea(length: float, elastic_modulus: float, inertia: float, load: float,
             support: str, elements: int = 20) -> dict[str, float]:
    assert elements >= 2 and (support != "simply_supported_center" or elements % 2 == 0)
    dofs = 2 * (elements + 1)
    stiffness = [[0.0] * dofs for _ in range(dofs)]
    element_length = length / elements
    local = beam_element_stiffness(elastic_modulus * inertia, element_length)
    for element in range(elements):
        indices = (2 * element, 2 * element + 1, 2 * element + 2, 2 * element + 3)
        for i, gi in enumerate(indices):
            for j, gj in enumerate(indices):
                stiffness[gi][gj] += local[i][j]
    forces = [0.0] * dofs
    if support == "simply_supported_center":
        forces[2 * (elements // 2)] = -load
        constrained = {0, 2 * elements}
        analytic_deflection = load * length**3 / (48 * elastic_modulus * inertia)
        analytic_moment = load * length / 4
    elif support == "cantilever_tip":
        forces[2 * elements] = -load
        constrained = {0, 1}
        analytic_deflection = load * length**3 / (3 * elastic_modulus * inertia)
        analytic_moment = load * length
    else:
        raise ValueError(support)
    free = [index for index in range(dofs) if index not in constrained]
    reduced = [[stiffness[i][j] for j in free] for i in free]
    solved = solve_linear(reduced, [forces[i] for i in free])
    displacement = [0.0] * dofs
    for index, value in zip(free, solved):
        displacement[index] = value
    moments = []
    for element in range(elements):
        indices = (2 * element, 2 * element + 1, 2 * element + 2, 2 * element + 3)
        local_d = [displacement[index] for index in indices]
        local_force = [sum(local[i][j] * local_d[j] for j in range(4)) for i in range(4)]
        moments.extend((abs(local_force[1]), abs(local_force[3])))
    fea_deflection = max(abs(displacement[2 * node]) for node in range(elements + 1))
    fea_moment = max(moments)
    return {
        "analytic_max_deflection_mm": analytic_deflection * 1000,
        "fea_max_nodal_deflection_mm": fea_deflection * 1000,
        "deflection_relative_error": abs(fea_deflection - analytic_deflection) / analytic_deflection,
        "analytic_max_moment_nm": analytic_moment,
        "fea_max_element_end_moment_nm": fea_moment,
        "moment_relative_error": abs(fea_moment - analytic_moment) / analytic_moment,
    }


def circle_section(diameter_m: float) -> dict[str, float]:
    return {
        "inertia_m4": pi * diameter_m**4 / 64,
        "extreme_fiber_m": diameter_m / 2,
        "area_m2": pi * diameter_m**2 / 4,
        "transverse_shear_factor": 4 / 3,
        "polar_inertia_m4": pi * diameter_m**4 / 32,
        "torsion_radius_m": diameter_m / 2,
    }


def rectangle_section(width_m: float, depth_m: float) -> dict[str, float]:
    return {
        "inertia_m4": width_m * depth_m**3 / 12,
        "extreme_fiber_m": depth_m / 2,
        "area_m2": width_m * depth_m,
        "transverse_shear_factor": 1.5,
        "polar_inertia_m4": 0.0,
        "torsion_radius_m": 0.0,
    }


def hollow_square_section(outer_m: float, wall_m: float) -> dict[str, float]:
    inner = outer_m - 2 * wall_m
    return {
        "inertia_m4": (outer_m**4 - inner**4) / 12,
        "extreme_fiber_m": outer_m / 2,
        "area_m2": outer_m**2 - inner**2,
        "transverse_shear_factor": 1.5,
        "polar_inertia_m4": 0.0,
        "torsion_radius_m": 0.0,
    }


def build_cases() -> list[dict[str, object]]:
    return [
        dict(name="stage1_cutter_shaft", support="simply_supported_center", length_m=0.081,
             load_n=60.0 / 0.025, torque_nm=60.0, e_pa=200e9,
             section=circle_section(0.020),
             yield_mpa=305.0, deflection_limit_mm=0.2 / 3,
             basis="60 N m proof torque at 25 mm radius; 20 mm shaft; 81 mm bearing span"),
        dict(name="stage1_cutter_tooth_ligament", support="cantilever_tip", length_m=0.008,
             load_n=60.0 / 0.025 / 2, torque_nm=0.0, e_pa=200e9,
             section=rectangle_section(0.006, 0.008),
             yield_mpa=650.0, deflection_limit_mm=0.2 / 3,
             basis="two-way 60 N m jam sharing; 6 by 8 mm idealized tooth ligament"),
        dict(name="stage1_bearing_plate_strip", support="cantilever_tip", length_m=0.050,
             load_n=(60.0 / 0.025) / 2, torque_nm=0.0, e_pa=200e9,
             section=rectangle_section(0.050, 0.014),
             yield_mpa=250.0, deflection_limit_mm=0.2 / 3,
             basis="one bearing reaction; 50 mm effective strip; 14 mm steel plate"),
        dict(name="reducer_output_overhang", support="cantilever_tip", length_m=0.030,
             load_n=60.0 / 0.025, torque_nm=60.0, e_pa=200e9,
             section=circle_section(0.015),
             yield_mpa=305.0, deflection_limit_mm=0.050,
             basis="unverified 15 mm donor output; 30 mm overhang; full 60 N m radial equivalent"),
        dict(name="extruder_thrust_plate_strip", support="simply_supported_center", length_m=0.080,
             load_n=5089.3801, torque_nm=0.0, e_pa=200e9,
             section=rectangle_section(0.060, 0.012),
             yield_mpa=250.0, deflection_limit_mm=0.050,
             basis="20 MPa proof thrust; 80 by 60 by 12 mm effective steel strip"),
        dict(name="spooler_shaft", support="simply_supported_center", length_m=0.105,
             load_n=1.35 * 4.0 * 9.80665, torque_nm=0.25, e_pa=200e9,
             section=circle_section(0.012),
             yield_mpa=250.0, deflection_limit_mm=0.050,
             basis="1.35 kg full spool at 4 g; 12 mm shaft; 105 mm bearing span"),
        dict(name="tower_frame_column", support="cantilever_tip", length_m=0.720,
             load_n=200.0, torque_nm=0.0, e_pa=69e9,
             section=hollow_square_section(0.040, 0.002),
             yield_mpa=160.0, deflection_limit_mm=720 / 500,
             basis="single idealized 4040 by 2 mm wall column under assumed 200 N lateral service load"),
    ]


def main() -> None:
    results = []
    for case in build_cases():
        section = case.pop("section")
        inertia = section["inertia_m4"]
        extreme_fiber = section["extreme_fiber_m"]
        result = beam_fea(
            case["length_m"], case["e_pa"], inertia, case["load_n"], case["support"]
        )
        bending_stress_mpa = (
            result["fea_max_element_end_moment_nm"] * extreme_fiber / inertia / 1e6
        )
        maximum_shear_force_n = (
            case["load_n"] / 2
            if case["support"] == "simply_supported_center"
            else case["load_n"]
        )
        transverse_shear_mpa = (
            section["transverse_shear_factor"] * maximum_shear_force_n /
            section["area_m2"] / 1e6
        )
        torsional_shear_mpa = 0.0
        if case["torque_nm"]:
            assert section["polar_inertia_m4"] > 0, "torsion needs a defined section model"
            torsional_shear_mpa = (
                case["torque_nm"] * section["torsion_radius_m"] /
                section["polar_inertia_m4"] / 1e6
            )
        von_mises_mpa = sqrt(
            bending_stress_mpa**2 +
            3 * (transverse_shear_mpa**2 + torsional_shear_mpa**2)
        )
        safety_factor = case["yield_mpa"] / von_mises_mpa
        passes = (result["fea_max_nodal_deflection_mm"] <= case["deflection_limit_mm"] and
                  safety_factor >= 1.5)
        results.append({
            **case,
            "elements": 20,
            "section_inertia_m4": inertia,
            "extreme_fiber_m": extreme_fiber,
            "section_area_m2": section["area_m2"],
            **result,
            "maximum_support_reaction_n": maximum_shear_force_n,
            "nominal_bending_stress_mpa": bending_stress_mpa,
            "nominal_transverse_shear_mpa": transverse_shear_mpa,
            "nominal_torsional_shear_mpa": torsional_shear_mpa,
            "nominal_von_mises_mpa": von_mises_mpa,
            "yield_safety_factor_without_notch_contact_or_joint_factor": safety_factor,
            "deflection_limit_utilization": (
                result["fea_max_nodal_deflection_mm"] / case["deflection_limit_mm"]
            ),
            "screening_status": "PASS_1D_SCREEN" if passes else "REVIEW_REQUIRED",
        })
    report = {
        "model": "two-node Euler-Bernoulli beam finite elements; 2 DOF per node",
        "status": "SCREENING_ONLY_NOT_3D_FEA_OR_PHYSICAL_VALIDATION",
        "case_count": len(results),
        "cases": results,
        "limitations": [
            "Linear small-deflection uniform-beam elements plus nominal section shear/torsion do not resolve cutter roots, keyways, bearing fits, holes, welds, contacts or extrusion pressure seals.",
            "Loads are static equivalents; cutter impact, reverse shock, fatigue, vibration and frame-joint slip are excluded.",
            "Material values are screening assumptions, not certificates or temperature-reduced allowables.",
            "Reducer geometry is unverified; its REVIEW_REQUIRED result is a donor-selection gate, not a final component prediction.",
            "The frame case is one idealized column and intentionally excludes cross-bracing and anchors; jointed 3D frame analysis remains open.",
        ],
    }
    output = ROOT / "simulation" / "structural" / "beam_crosscheck.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"STRUCTURAL_BEAM_FEA_OK cases={len(results)} review=" +
          ",".join(case["name"] for case in results if case["screening_status"] == "REVIEW_REQUIRED"))


if __name__ == "__main__":
    main()
