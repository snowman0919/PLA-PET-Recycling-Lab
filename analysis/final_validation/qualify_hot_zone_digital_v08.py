#!/usr/bin/env python3
"""Close the v0.8 hot-zone digital design envelope without claiming physical qualification."""
from pathlib import Path
import hashlib, json, math

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def bound_current(path: Path, record: dict) -> bool:
    sources = record.get("source_sha256", {})
    return path.is_file() and bool(sources) and all((ROOT/p).is_file() and sha(ROOT/p) == h for p,h in sources.items())

def main() -> None:
    thermal_path = ROOT/"analysis/final_validation/results/v0.8/thermal_fit_closure.json"
    sensor_path = ROOT/"analysis/final_validation/results/v0.8/sensor_bore_local_candidate.json"
    joint_path = ROOT/"analysis/final_validation/results/v0.8/die_joint_qualification.json"
    om_path = ROOT/"simulation/openmodelica/results_v0.8/summary.json"
    params_path = ROOT/"cad/parameters/final_v08.json"
    contract_path = ROOT/"analysis/final_validation/contracts/thermomechanical_closure_v08.json"
    thermal, sensor, joint, om = [json.loads(p.read_text()) for p in (thermal_path,sensor_path,joint_path,om_path)]
    params = json.loads(params_path.read_text())
    hot_yield_floor_mpa = 360.0
    analysis_allowable_mpa = 180.0
    alpha_reference = 12.0e-6
    alpha_upper = 17.0e-6
    design_upper_c = 300.0
    normal_target_c = 270.0

    free_pairs = thermal.get("nominal_dimension_pairs", [])
    travel = thermal.get("full_length_arithmetic", [])
    worst_free_gap = min((r["diametral_clearance_mm"] for r in free_pairs), default=-math.inf)
    worst_travel_margin = min((r["arithmetic_1p3_travel_margin_mm"] for r in travel), default=-math.inf)

    # Same-material screw/barrel differential sensitivity, including the retained alpha upper bound.
    screw_gap = []
    for alpha in (alpha_reference, 12.3e-6, alpha_upper):
        for bore_c, screw_c in ((245.0,270.0),(270.0,245.0)):
            bore = 16.20*(1+alpha*(bore_c-20.0))
            screw = 15.92*(1+alpha*(screw_c-20.0))
            screw_gap.append({"alpha_per_k":alpha,"bore_c":bore_c,"screw_c":screw_c,
                              "radial_clearance_mm":(bore-screw)/2})
    minimum_hot_screw_gap = min(r["radial_clearance_mm"] for r in screw_gap)

    om_hot = om.get("hot_zone", {})
    checks = {
        "material_design_floor_ge_2x_allowable": hot_yield_floor_mpa >= 2*analysis_allowable_mpa,
        "thermal_fit_sources_current": bound_current(thermal_path, thermal),
        "all_48_radial_fit_bounds_noninterfering": len(free_pairs)==48 and all(r.get("free_clearance_pass") for r in free_pairs),
        "full_length_300c_travel_margin_ge_0p15mm": worst_travel_margin >= 0.15,
        "hot_screw_barrel_radial_clearance_ge_0p13mm": minimum_hot_screw_gap >= 0.13,
        "sensor_bore_thermoelastic_current_and_pass": bound_current(sensor_path,sensor) and sensor.get("status")=="PASS",
        "sensor_bore_sf2_yield_requirement_below_allowable": sensor.get("required_yield_mpa_for_regional_sf_2",math.inf) <= analysis_allowable_mpa,
        "die_joint_current_and_pass": bound_current(joint_path,joint) and joint.get("status")=="PASS",
        "openmodelica_current_and_pass": bound_current(om_path,om) and om.get("status")=="PASS",
        "openmodelica_normal_hot_zone_le_270c": om_hot.get("temperatureC",math.inf) <= normal_target_c,
    }
    sources = [Path(__file__).resolve(), thermal_path, sensor_path, joint_path, om_path,
               params_path, contract_path]
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "scope": "DIGITAL_DESIGN_ENVELOPE_ONLY",
        "physical_validation_state": "NOT_RUN", "machine_release": "HOLD",
        "material_design_contract": {
            "source_material": "SCM440 / 42CrMo4-equivalent QT steel per released manufacturing requirement",
            "minimum_yield_at_270c_mpa": hot_yield_floor_mpa,
            "analysis_allowable_mpa": analysis_allowable_mpa,
            "reference_cte_per_k": alpha_reference,
            "upper_cte_sensitivity_per_k": alpha_upper,
            "design_temperature_upper_c": design_upper_c,
            "normal_process_target_upper_c": normal_target_c,
            "provenance_note": "360 MPa is a project procurement/design floor, not an assertion that every SCM440 heat meets it.",
            "references": [
                "https://steelnavigator.ovako.com/steel-grades/42crmo4/",
                "https://doi.org/10.1515/htmp-2014-0011"
            ]
        },
        "thermal_fit": {"case_count":len(free_pairs),"minimum_diametral_clearance_mm":worst_free_gap,
                        "minimum_full_length_travel_margin_mm":worst_travel_margin,
                        "declared_cold_axial_travel_mm":params["hot_zone_mount"]["cold_axial_travel_mm"]},
        "screw_barrel_hot_clearance": {"cases":screw_gap,"minimum_radial_clearance_mm":minimum_hot_screw_gap},
        "sensor_bore": {"status":sensor.get("status"),"required_yield_mpa_for_sf2":sensor.get("required_yield_mpa_for_regional_sf_2"),
                        "mesh_change":sensor.get("medium_to_fine_regional_stress_change")},
        "die_joint": {"status":joint.get("status"),"separation_sf":joint.get("separation_sf"),
                      "hot_bolt_proof_sf":joint.get("hot_bolt_proof_sf"),"thread_shear_sf":joint.get("thread_shear_sf")},
        "openmodelica_normal_hot_zone_c": om_hot.get("temperatureC"),
        "checks": checks,
        "physical_followup": [
            "Verify received hot-zone steel lot/heat-treatment identity and hardness before machining acceptance.",
            "Verify actual cold free slide/travel and first thermal-cycle motion after full digital release and user authorization.",
            "Verify die joint leak-tightness/witness marks after first authorized thermal cycle; no hot-retorque value is inferred here.",
        ],
        "source_sha256": {str(p.relative_to(ROOT)):sha(p) for p in sources},
    }
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(f"HOT_ZONE_DIGITAL_{result['status']} gap={worst_free_gap:.4f}mm travel={worst_travel_margin:.4f}mm screw={minimum_hot_screw_gap:.4f}mm")
    if result["status"] != "PASS":
        for name,value in checks.items():
            if not value: print("FAIL_CHECK",name)
        raise SystemExit(2)

if __name__ == "__main__":
    main()
