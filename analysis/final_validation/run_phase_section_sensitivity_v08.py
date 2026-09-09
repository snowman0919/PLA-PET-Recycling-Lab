#!/usr/bin/env python3
"""CAD 최소 굽힘 관성을 원형 beam에 대응시킨 민감도 해석; release gate 아님."""

import json
import math
import tempfile
from pathlib import Path

from run_phase_load_v08 import INPUT, ROOT, plate, shaft, sha256


def torsion_cases(stations, torque_nm, diameter_mm):
    driven, slave = stations["153"], stations["105"]
    shear_modulus = 205e9 / (2 * (1 + .29))
    circular_j = math.pi * (diameter_mm / 1000)**4 / 32
    rows = []
    # Include both neighbours of each interior disc, including equal-distance ties.
    ordered = sorted((y, key) for key, rotor in stations.items() for y in rotor["cutter_y_mm"])
    for (a, key_a), (b, key_b) in zip(ordered, ordered[1:]):
        assert key_a != key_b, "Expected alternating cutter stack"
        driven_y, slave_y = (a, b) if key_a == "153" else (b, a)
        lengths = [driven["gear_y_mm"] - driven_y, slave["gear_y_mm"] - slave_y]
        assert min(lengths) > 0
        twist = torque_nm * sum(lengths) / 1000 / (shear_modulus * circular_j)
        rows.append({"jammed_slave_cutter_y_mm": slave_y,
                     "adjacent_driven_cutter_y_mm": driven_y,
                     "torque_nm_along_each_series_segment": torque_nm,
                     "series_lengths_mm": lengths,
                     "unkeyed_round_shaft_relative_twist_deg": math.degrees(twist)})
    return rows


def main():
    parameters_path = ROOT / "cad/parameters/baseline.json"
    parameters = json.loads(parameters_path.read_text())["shredder"]
    torque_nm = parameters["mechanical_relief_torque_nm"]
    section_path = ROOT / "analysis/final_validation/results/v0.8/shaft_section.json"
    section = json.loads(section_path.read_text())
    assert section["status"] == "PASS"
    assert all(sha256(ROOT / p) == digest for p, digest in section["source_sha256"].items())
    geometry = json.loads((INPUT / "geometry_manifest.json").read_text())
    assert geometry["geometry_source_sha256"] == sha256(ROOT / "cad/freecad/compact/geometry.py")
    inertia = min(row["Imin_mm4"] for row in section["sections"])
    diameter_mm = (64 * inertia / math.pi)**0.25
    assert math.isclose(math.pi * diameter_mm**4 / 64, inertia, rel_tol=1e-12)
    raw = ROOT / "analysis/final_validation/results/v0.8/phase_raw"
    raw.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="section-sensitivity-", dir=raw))
    angle, radius = math.radians(20), 24.0
    radial_gear = torque_nm / (radius / 1000) * math.tan(angle)
    rows = []
    for refinement, mesh in ((8, 3.5), (16, 2.5)):
        cases = [shaft(stations, 1856.544175556756, radial_gear, sign, refinement,
                       folder / f"shaft_{key}_{sign}_{refinement}", diameter_mm / 1000)
                 for key, stations in geometry["shredder_stations"].items() for sign in (-1, 1)]
        reaction = max(abs(v) for case in cases for v in case["support_reaction_n"])
        support = plate(reaction, mesh, folder / f"plate_{refinement}")
        stations = next(iter(geometry["shredder_stations"].values()))
        front, rear = stations["bearing_y_mm"]
        extrapolation = 1 + 2 * (stations["gear_y_mm"] - rear) / (rear - front)
        centre = sum(max(abs(c["gear_displacement_mm"]) for c in cases[i:i+2]) for i in (0, 2))
        centre += extrapolation * support["relative_centre_bound_mm"]
        backlash = [.15 - 2 * centre * math.tan(angle), .35 + 2 * centre * math.tan(angle)]
        angular = math.degrees(backlash[1] / radius)
        rows.append({"refinement": refinement, "shaft_cases": cases, "plate": support,
                     "centre_movement_mm": centre, "backlash_range_mm": backlash,
                     "backlash_angle_deg": angular, "remaining_angle_budget_deg": 1 - angular})
    convergence = abs(rows[-1]["centre_movement_mm"] - rows[-2]["centre_movement_mm"]) / rows[-1]["centre_movement_mm"]
    assert convergence <= .05
    # A defined load path, not 22 N.m independently invented on both rotors:
    # input -> driven shaft -> rear gear pair -> one jammed slave cutter.
    # The driven rotor has no cutting resistance in this scenario.
    torsion_rows = torsion_cases(geometry["shredder_stations"], torque_nm, parameters["shaft_diameter_mm"])
    # 25 mm is the smallest practical standard-bearing redesign worth solving:
    # the existing 20 mm path already exceeds the 1 degree budget before key lash.
    candidate_diameter = 25.0
    candidate_meshes = []
    for refinement, mesh in ((8, 3.5), (16, 2.5)):
        cases = [shaft(stations, 1856.544175556756, radial_gear, sign, refinement,
                       folder / f"shaft25_{key}_{sign}_{refinement}", candidate_diameter / 1000)
                 for key, stations in geometry["shredder_stations"].items() for sign in (-1, 1)]
        reaction = max(abs(v) for case in cases for v in case["support_reaction_n"])
        support = plate(reaction, mesh, folder / f"plate25_{refinement}")
        stations = next(iter(geometry["shredder_stations"].values()))
        front, rear = stations["bearing_y_mm"]
        extrapolation = 1 + 2 * (stations["gear_y_mm"] - rear) / (rear - front)
        centre = sum(max(abs(c["gear_displacement_mm"]) for c in cases[i:i+2]) for i in (0, 2))
        centre += extrapolation * support["relative_centre_bound_mm"]
        backlash = [.10 - 2 * centre * math.tan(angle), .15 + 2 * centre * math.tan(angle)]
        gear_angle = math.degrees(backlash[1] / radius)
        candidate_meshes.append({"refinement": refinement, "shaft_cases": cases, "plate": support,
                                 "centre_movement_mm": centre, "backlash_range_mm": backlash,
                                 "backlash_angle_deg": gear_angle})
    candidate_convergence = abs(candidate_meshes[-1]["centre_movement_mm"] - candidate_meshes[-2]["centre_movement_mm"]) / candidate_meshes[-1]["centre_movement_mm"]
    assert candidate_convergence <= .05
    candidate_torsion = torsion_cases(geometry["shredder_stations"], torque_nm, candidate_diameter)
    four_matched_key_interfaces_deg = 2 * .1375197729683561
    combined_angle = (candidate_meshes[-1]["backlash_angle_deg"]
                      + max(row["unkeyed_round_shaft_relative_twist_deg"] for row in candidate_torsion)
                      + four_matched_key_interfaces_deg)
    assert candidate_meshes[-1]["backlash_range_mm"][0] > 0
    assert combined_angle <= 1.0
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN",
              "scope": "Bending-section sensitivity only; no assembly qualification",
              "equivalent_bending_diameter_mm": diameter_mm, "Imin_mm4": inertia,
              "relative_mesh_change": convergence, "meshes": rows,
              "torsion_diagnostic": {
                  "scenario": "All input relief torque goes through rear phase gears to one slave cutter; driven cutting load zero",
                  "model": "Ideal unkeyed uniform circular shafts; theta=sum(TL/GJ), J=pi*d^4/32",
                  "input_torque_nm": torque_nm, "shaft_diameter_mm": parameters["shaft_diameter_mm"],
                  "source": "https://mechref.engr.illinois.edu/sol/torsion.html",
                  "cases": torsion_rows,
                  "scope": "Load-path diagnostic; excludes keyways, hubs, gear teeth and bearing/frame compliance; not a release qualification"},
              "diameter25_candidate": {
                  "status": "PASS", "shaft_diameter_mm": candidate_diameter,
                  "cold_backlash_target_mm": [.10, .15], "meshes": candidate_meshes,
                  "relative_mesh_change": candidate_convergence,
                  "torsion_cases": candidate_torsion,
                  "four_matched_key_interfaces_peak_to_peak_deg": four_matched_key_interfaces_deg,
                  "combined_worst_angle_deg": combined_angle,
                  "criterion_deg": 1.0,
                  "numeric_screen": "PASS" if combined_angle <= 1 else "FAIL",
                  "scope": "Released 25 mm shaft and current plate surrogate; four interfaces use key5.995..6.000/slot6.005..6.010 rigid-contact bound. Exact keyed CAD, 61905 clearance, keyed torsion and gear elasticity are bound by separate release evidence; physical fit remains NOT_RUN."},
              "limitations": ["Equivalent circle matches minimum bending inertia, not keyed-section torsion or shear compliance.",
                              "Key contact, gear tooth compliance, frame and bearing deflection remain unqualified.",
                              "Remaining angle budget is not a demonstrated assembly safety margin."],
              "raw_directory": str(folder.relative_to(ROOT)),
              "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (
                  Path(__file__).resolve(), section_path, parameters_path, INPUT / "geometry_manifest.json",
                  ROOT / "analysis/final_validation/run_phase_load_v08.py",
                  ROOT / "analysis/final_validation/run_calculix_v08.py")}}
    out = ROOT / "analysis/final_validation/results/v0.8/phase_section_sensitivity.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"V08_PHASE_SECTION_SENSITIVITY_DONE assembly=HOLD angle_deg={rows[-1]['backlash_angle_deg']:.6f}")


if __name__ == "__main__":
    main()
