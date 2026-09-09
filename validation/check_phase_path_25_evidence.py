#!/usr/bin/env python3
"""Bind the 25 mm FreeCAD and CalculiX phase-path candidate evidence."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis/final_validation/results/v0.8"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_current(name):
    data = json.loads((RESULTS / name).read_text())
    assert all((ROOT / path).exists() and sha(ROOT / path) == digest
               for path, digest in data["source_sha256"].items())
    return data


def main():
    geometry = load_current("phase_path_25_candidate.json")
    torsion = [load_current(f"torsion_load_path_25_{shaft}.json") for shaft in ("153", "105")]
    gear_elastic = load_current("phase_gear_elastic_candidate.json")
    pair_backlash = load_current("phase_pair_backlash_candidate.json")
    assert gear_elastic["torque_nm"] == 34 and gear_elastic["gear_piece_count"] == 1
    assert gear_elastic["face_width_mm"] == 18 and gear_elastic["status"] == "HOLD"
    expected_strength = ("PASS" if gear_elastic["conditional_sf_at_355_mpa"] >= 2
                         and gear_elastic["peak_stress_relative_mesh_change"] <= .05
                         else "NOT_QUALIFIED")
    assert gear_elastic["conditional_strength_screen"] == expected_strength
    assert geometry["nominal_geometry_check"] == "PASS"
    assert geometry["status"] == "PASS"
    assert geometry["cutter_matched_keyway_width_mm"] == 6.0075
    assert geometry["gear_matched_keyway_width_mm"] == 8.0075 and geometry["gear_key_nominal_mm"] == [8.0, 7.0]
    assert geometry["gear_root_fillet_mm"] == 1.0
    assert geometry["cad_pair_backlash_target_mm"] == .125
    assert pair_backlash["cad_pair_backlash_bound_mm"][0] >= .12
    assert pair_backlash["cad_pair_backlash_bound_mm"][1] <= .14
    assert geometry["bearing"]["static_rating_ratio"] >= 2
    assert all(row["rotation_within_5_percent"] for row in torsion)
    exact_twist = sum(row["meshes"][-1]["tip_rotation_deg"] for row in torsion)
    phase = load_current("phase_section_sensitivity.json")["diameter25_candidate"]
    gear = phase["meshes"][-1]["backlash_angle_deg"]
    keys = phase["four_matched_key_interfaces_peak_to_peak_deg"]
    cn_relative = geometry["bearing"]["two_shaft_worst_relative_clearance_mm"]
    cn_angle = math.degrees(2 * cn_relative * math.tan(math.radians(20)) / 24)
    gear_elastic_angle = gear_elastic["two_gear_elastic_angle_deg"]
    combined = gear + keys + exact_twist + cn_angle + gear_elastic_angle
    assert combined <= phase["criterion_deg"]
    output = {
        "status": "PASS", "physical_validation_state": "NOT_RUN",
        "numeric_screen": "PASS", "gear_loaded_backlash_deg": gear,
        "four_key_interfaces_deg": keys, "exact_keyed_shaft_twist_deg": exact_twist,
        "bearing_cn_clearance_deg": cn_angle,
        "calculix_gear_elastic_angle_deg": gear_elastic_angle,
        "gear_conditional_strength_sf": gear_elastic["conditional_sf_at_355_mpa"],
        "gear_peak_stress_relative_mesh_change": gear_elastic["peak_stress_relative_mesh_change"],
        "gear_conditional_strength_screen": gear_elastic["conditional_strength_screen"],
        "cad_pair_backlash_bound_mm": pair_backlash["cad_pair_backlash_bound_mm"],
        "combined_worst_angle_deg": combined, "criterion_deg": phase["criterion_deg"],
        "limitations": ["Released 25 mm geometry passes the scoped digital phase screen; physical validation remains NOT_RUN.",
                        "SKF rating and clearance are catalogue-based; shock, misalignment and seat-ring receipt inspection remain physical gates.",
                        "Rear plate response is included in loaded backlash; common-mode frame motion cancels from relative gear-centre motion. The solid18 mm gear carries full34 N.m in the conservative tooth-tip FEA, while actual flank contact is a receipt/blue-check gate.",
                        "Matched key fits, clocking, backlash and bearing clearance require CMM/optical/indicator verification before powered operation."],
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in (
            Path(__file__).resolve(), RESULTS / "phase_path_25_candidate.json",
            RESULTS / "torsion_load_path_25_153.json", RESULTS / "torsion_load_path_25_105.json",
            RESULTS / "phase_gear_elastic_candidate.json", RESULTS / "phase_pair_backlash_candidate.json", RESULTS / "phase_section_sensitivity.json")}
    }
    (RESULTS / "phase_path_25_qualification.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"PHASE_PATH_25_EVIDENCE_PASS angle={combined:.6f} status=PASS physical=NOT_RUN")


if __name__ == "__main__":
    main()
