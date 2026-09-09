#!/usr/bin/env python3
"""Digital die-joint load-path qualification; physical leak/retorque remains NOT_RUN."""
from pathlib import Path
import hashlib, json, math

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis/final_validation/results/v0.8/die_joint_qualification.json"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    # Released geometry contract. M4x45 is cut/deburred to this under-head length.
    length = (42.4, 42.6)
    die_grip = (34.95, 35.05)
    gasket = (0.25, 0.53)
    thread_depth = 8.0
    engagement = (length[0]-die_grip[1]-gasket[1], length[1]-die_grip[0]-gasket[0])
    bottom_clearance = (thread_depth-engagement[1], thread_depth-engagement[0])
    assert engagement[0] > 0 and bottom_clearance[0] > 0
    pressure_mpa = 6.0
    gasket_id_max = 16.30
    gasket_od = 34.0
    hole_area = 4*math.pi*4.5**2/4 + 2*math.pi*3.2**2/4
    gasket_net_area = math.pi*(gasket_od**2-gasket_id_max**2)/4 - hole_area
    separation_n = pressure_mpa*math.pi*gasket_id_max**2/4

    # Practical dry-thread design envelope, not a measured preload.
    torque_nm = 1.50
    nut_factor = (0.18, 0.28)
    bolt_d_m = 0.004
    preload_each = (torque_nm/(nut_factor[1]*bolt_d_m), torque_nm/(nut_factor[0]*bolt_d_m))
    retained_fraction = 0.50
    retained_total_n = 4*preload_each[0]*retained_fraction
    separation_sf = retained_total_n/separation_n
    residual_contact_mpa = (retained_total_n-separation_n)/gasket_net_area

    # M4 coarse / class 10.9 screening values. Elevated proof is deliberately derated.
    stress_area_mm2 = 8.78
    room_proof_mpa = 830.0
    hot_proof_screen_mpa = 580.0
    max_bolt_load_n = preload_each[1] + separation_n/4
    bolt_stress_mpa = max_bolt_load_n/stress_area_mm2
    hot_bolt_proof_sf = hot_proof_screen_mpa/bolt_stress_mpa
    # Internal SCM440 thread: conservative half-cylinder shear-area screen.
    material_hot_yield_floor_mpa = 360.0
    thread_shear_yield_mpa = material_hot_yield_floor_mpa/math.sqrt(3)
    m4_internal_minor_mm = 3.14
    shear_area_min_mm2 = math.pi*m4_internal_minor_mm*engagement[0]*0.5
    thread_shear_capacity_n = shear_area_min_mm2*thread_shear_yield_mpa
    thread_shear_sf = thread_shear_capacity_n/max_bolt_load_n

    checks = {
        "minimum_engagement_ge_1p5d": engagement[0] >= 6.0,
        "thread_bottom_clearance_ge_0p5mm": bottom_clearance[0] >= 0.5,
        "retained_clamp_vs_6mpa_separation_sf_ge_2": separation_sf >= 2.0,
        "positive_residual_gasket_contact": residual_contact_mpa > 0,
        "hot_bolt_proof_screen_sf_ge_2": hot_bolt_proof_sf >= 2.0,
        "internal_thread_shear_screen_sf_ge_2": thread_shear_sf >= 2.0,
    }
    sources = [Path(__file__).resolve(), ROOT/"cad/freecad/compact/geometry.py",
               ROOT/"cad/freecad/compact/manufacturing.py", ROOT/"cad/parameters/final_v08.json"]
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "physical_validation_state": "NOT_RUN", "machine_release": "HOLD",
        "joint": "EX-DIE-01 to EX-BAR-01 through EX-DIE-05 C110 gasket",
        "fastener": "4x M4 class 10.9 SHCS; M4x45 stock cut/deburred to 42.5+/-0.1 mm",
        "assembly_torque_nm": torque_nm, "pressure_design_case_mpa": pressure_mpa,
        "engagement_mm": engagement, "thread_bottom_clearance_mm": bottom_clearance,
        "gasket_net_area_mm2": gasket_net_area, "separation_force_n": separation_n,
        "preload_each_n": preload_each, "retained_preload_fraction_design_floor": retained_fraction,
        "retained_total_clamp_n": retained_total_n, "separation_sf": separation_sf,
        "residual_average_gasket_contact_mpa": residual_contact_mpa,
        "bolt_stress_mpa": bolt_stress_mpa, "room_proof_reference_mpa": room_proof_mpa,
        "hot_proof_screen_mpa": hot_proof_screen_mpa, "hot_bolt_proof_sf": hot_bolt_proof_sf,
        "internal_material_hot_yield_floor_mpa": material_hot_yield_floor_mpa,
        "thread_shear_capacity_n": thread_shear_capacity_n, "thread_shear_sf": thread_shear_sf,
        "checks": checks,
        "limitations": [
            "Torque-to-preload and 50% retained-preload values are design envelopes, not measured preload.",
            "PASS qualifies the defined digital load path, not hot leak-tightness or first-cycle retorque.",
            "Received bolt class, cut length, gasket thickness and material lot remain physical receipt gates.",
        ],
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in sources},
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n")
    print(f"DIE_JOINT_DIGITAL_{result['status']} sep_sf={separation_sf:.3f} bolt_hot_sf={hot_bolt_proof_sf:.3f} thread_sf={thread_shear_sf:.3f}")
    if result["status"] != "PASS":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
