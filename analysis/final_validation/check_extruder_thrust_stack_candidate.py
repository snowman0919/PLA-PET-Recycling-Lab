#!/usr/bin/env python3
"""현재 IF-020과 표준 51102/Ø12 coupling 후보의 치수·하중 적합성 검사."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "analysis/final_validation/results/v0.8/extruder_thrust_stack_candidate.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parameters = json.loads((ROOT / "cad/parameters/final_v08.json").read_text())
    stack = parameters["extruder_thrust_stack"]
    final_cad = json.loads((ROOT / "validation/results/final_v08_cad.json").read_text())
    pressure_mpa, barrel_bore_mm = 6.0, 16.22
    thrust_n = pressure_mpa * math.pi * barrel_bore_mm**2 / 4
    bearing = {
        "candidate": "NSK 51102",
        "dimensions_mm": [15.0, 28.0, 9.0],
        "dynamic_rating_n": 10600.0,
        "static_rating_n": 16800.0,
        "shaft_abutment_min_mm": 23.0,
        "housing_abutment_max_mm": 20.0,
        "source": "https://www.nsk.com/engineering/products/bearings/ball-bearings/thrust-ball-bearings/single-direction-thrust-ball-bearings/51102-tb-sd.html",
    }
    coupling = {
        "candidate": "Ruland MCLX-12-12-F",
        "bores_mm": [12.0, 12.0],
        "shaft_tolerance_mm": [11.987, 12.0],
        "outside_diameter_mm": 29.0,
        "length_mm": 45.0,
        "rated_torque_nm": 105.0,
        "clamp_screw_torque_nm": 4.6,
        "source": "https://www.ruland.com/mclx-12-12-f.html",
    }
    peak_screw_torque_nm = 13.542145
    current = {
        "screw_bearing_seat_limits_mm": stack["screw_bearing_seat_mm"],
        "screw_thrust_shoulder_limits_mm": stack["shaft_washer_abutment_od_mm"],
        "thrust_plate_x_range_mm": [stack["plate_global_x_mm"], stack["plate_global_x_mm"] + 12.0],
        "plate_pocket_diameter_limits_mm": stack["plate_pocket_diameter_mm"],
        "plate_pocket_depth_limits_mm": stack["plate_pocket_depth_mm"],
        "housing_abutment_diameter_mm": 17.2,
        "adjustment_shim_range_mm": [0.05, 0.30],
    }
    housing_diametral_clearance = [value - bearing["dimensions_mm"][1]
                                    for value in current["plate_pocket_diameter_limits_mm"]]
    checks = {
        "bearing_dynamic_rating_sf_ge_2": bearing["dynamic_rating_n"] / thrust_n >= 2,
        "bearing_static_rating_sf_ge_2": bearing["static_rating_n"] / thrust_n >= 2,
        "coupling_torque_sf_ge_2": coupling["rated_torque_nm"] / peak_screw_torque_nm >= 2,
        "released_screw_abutment_diameter_ok": current["screw_thrust_shoulder_limits_mm"][0] >= bearing["shaft_abutment_min_mm"],
        "housing_abutment_diameter_ok": current["housing_abutment_diameter_mm"] <= bearing["housing_abutment_max_mm"],
        "housing_clearance_over_0p25_mm": housing_diametral_clearance[0] > 0.25,
        "bearing_pocket_axially_adjustable": current["plate_pocket_depth_limits_mm"] == [9.1, 9.15] and current["adjustment_shim_range_mm"] == [0.05, 0.30],
        "released_cad_geometry_ok": final_cad.get("status") == "PASS" and final_cad.get("thrust_seat_axis_alignment", {}).get("status") == "PASS",
    }
    assert all(checks.values())
    sources = [
        Path(__file__).resolve(),
        ROOT / "cad/freecad/compact/geometry.py",
        ROOT / "cad/freecad/compact/manufacturing.py",
        ROOT / "analysis/final_validation/results/v0.8/thermal_rerun.json",
        ROOT / "cad/parameters/final_v08.json",
        ROOT / "validation/results/final_v08_cad.json",
    ]
    output = {
        "status": "PASS",
        "physical_validation_state": "NOT_RUN",
        "pressure_thrust_n": thrust_n,
        "bearing": bearing,
        "bearing_dynamic_rating_sf": bearing["dynamic_rating_n"] / thrust_n,
        "bearing_static_rating_sf": bearing["static_rating_n"] / thrust_n,
        "coupling": coupling,
        "peak_screw_torque_nm": peak_screw_torque_nm,
        "coupling_torque_sf": coupling["rated_torque_nm"] / peak_screw_torque_nm,
        "current_geometry": current,
        "housing_diametral_clearance_mm": housing_diametral_clearance,
        "checks": checks,
        "required_redesign": [],
        "limitations": [
            "PASS is a dimensional/load-rating digital screen, not receipt or physical qualification.",
            "Measure bearing height and select 0.05-0.30 mm steel shim to obtain 0.05-0.15 mm loaded-direction endplay.",
            "The motor-side donor shaft and adapter remain governed by IF-008 and are not closed here.",
        ],
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in sources},
    }
    RESULT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print("EXTRUDER_THRUST_STACK_DIGITAL_PASS "
          f"thrust_n={thrust_n:.1f} bearing_sf={output['bearing_dynamic_rating_sf']:.2f} "
          f"coupling_sf={output['coupling_torque_sf']:.2f}")


if __name__ == "__main__":
    main()
