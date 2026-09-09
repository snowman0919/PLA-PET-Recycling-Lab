#!/usr/bin/env python3
"""Bind rear-retainer CAD, tolerance and CalculiX evidence."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis/final_validation/results/v0.8"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current(name):
    data = json.loads((RESULTS / name).read_text())
    assert all((ROOT / path).is_file() and sha(ROOT / path) == digest
               for path, digest in data["source_sha256"].items())
    return data


def main():
    geometry = current("axial_shoulder_candidate.json")
    fea = current("retainer_candidate_fea.json")
    access = current("retainer_tool_access.json")
    assert geometry["geometry_check"] == "PASS" and not geometry["unexpected_collisions"]
    assert geometry["axial_tolerance_stack"]["status"] == "PASS_RELEASE_DIGITAL"
    assert fea["displacement_convergence_5_percent"]
    finest = fea["meshes"][-1]
    per_bolt = max(abs(row["force_n"][0]) for row in finest["fixed_bore_reactions"])
    design_bolt_load = 2 * per_bolt  # explicit prying/load-share uncertainty factor
    m4_tensile_area, class88_proof = 8.78, 580.0
    bolt_sf = class88_proof * m4_tensile_area / design_bolt_load
    spacer_area = math.pi / 4 * (8**2 - 4.5**2)
    spacer_stress = design_bolt_load / spacer_area
    spacer_yield_sf = 275 / spacer_stress
    engagement = geometry["minimum_full_thread_engagement_mm"]
    pitch_diameter = 4 - .6495190528 * .7
    parent_yield = 177.5
    parent_shear = parent_yield / math.sqrt(3)
    thread_pullout = math.pi * pitch_diameter * parent_shear * engagement / 3
    thread_pullout_sf = thread_pullout / design_bolt_load
    torque_nm = [2.8, 3.0]
    nut_factor = [.18, .25]
    preload_n = [torque_nm[0] / (nut_factor[1] * .004), torque_nm[1] / (nut_factor[0] * .004)]
    proof_load = class88_proof * m4_tensile_area
    separation_sf = preload_n[0] / design_bolt_load
    maximum_proof_fraction = preload_n[1] / proof_load
    assert engagement >= 1.5 * 4
    assert bolt_sf >= 2 and spacer_yield_sf >= 2 and thread_pullout_sf >= 2
    assert separation_sf >= 2 and maximum_proof_fraction <= .90
    l_key_rows = [row for row in access["rows"] if row["envelope"] == "L_key_same_sweep_HotShield_removed"]
    assert len(l_key_rows) == 2 and all(row["nominal_space_check"] == "PASS" for row in l_key_rows)
    output = {
        "status": "PASS", "physical_validation_state": "NOT_RUN",
        "numeric_screen": "PASS", "geometry_check": "PASS",
        "cold_endplay_mm": geometry["axial_tolerance_stack"]["worst_case_cold_endplay_mm"],
        "hot_endplay_mm": geometry["axial_tolerance_stack"]["worst_case_hot_endplay_mm"],
        "finest_mesh_mm": finest["mesh_mm"],
        "finest_displacement_mm": finest["result"]["max_displacement_mm"],
        "finest_singular_peak_stress_mpa": finest["result"]["max_von_mises_mpa"],
        "per_bolt_reaction_n": per_bolt, "design_bolt_load_n": design_bolt_load,
        "m4_class88_proof_safety_factor": bolt_sf,
        "m4_pitch_diameter_mm": pitch_diameter,
        "minimum_full_thread_engagement_mm": engagement,
        "parent_material_yield_requirement_mpa_at_service_temperature": parent_yield,
        "nasa_rp1228_thread_pullout_capacity_n": thread_pullout,
        "thread_pullout_safety_factor": thread_pullout_sf,
        "thread_formula_source": "https://ntrs.nasa.gov/api/citations/19900009424/downloads/19900009424.pdf",
        "candidate_installation_torque_nm": torque_nm,
        "screening_nut_factor_range": nut_factor,
        "calculated_preload_range_n": preload_n,
        "minimum_preload_to_design_load_ratio": separation_sf,
        "maximum_preload_proof_fraction": maximum_proof_fraction,
        "spacer_compressive_stress_mpa": spacer_stress,
        "spacer_yield_safety_factor": spacer_yield_sf,
        "nominal_l_key_access_with_shield_removed": "PASS",
        "limitations": ["Release geometry and its specified retention load path pass the scoped digital screen; physical validation remains NOT_RUN.",
                        "Thread pullout and torque/preload are conservative closed-form screens; local contact/prying is bounded by the explicit 2x bolt-load factor, not a nonlinear contact solve.",
                        "The parent material certificate must prove >=177.5 MPa yield at the measured service temperature.",
                        "The actual dry-thread nut factor, relaxation and thermal-cycle preload must be verified before adopting the candidate torque.",
                        "Nominal L-key access requires shield removal; selected-tool insertion, hand space and service sequence remain unqualified.",
                        "The fixed-bore peak is a mesh-sensitive boundary singularity and is not a stress acceptance result.",
                        "Manufactured parts still require receipt inspection against released tolerances."],
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in (
            Path(__file__).resolve(), RESULTS / "axial_shoulder_candidate.json",
            RESULTS / "retainer_candidate_fea.json", RESULTS / "retainer_tool_access.json")}
    }
    (RESULTS / "axial_retainer_qualification.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"AXIAL_RETAINER_CANDIDATE_PASS bolt_sf={bolt_sf:.3f} spacer_sf={spacer_yield_sf:.3f} status=PASS")


if __name__ == "__main__":
    main()
