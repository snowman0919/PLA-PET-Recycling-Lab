"""Verify C2.1 generated evidence without granting hardware approval."""
from pathlib import Path
import hashlib
import json

R = Path(__file__).resolve().parents[1]
kin = json.loads((R/"results/kinematic_validation.json").read_text())
cad = json.loads((R/"results/cad_validation.json").read_text())
motion = json.loads((R/"results/motion_samples.json").read_text())
req = json.loads((R/"design/requirements.json").read_text())
summary = json.loads((R/"results/validation_summary.json").read_text())

assert summary["overall"] == "KINEMATIC_DIGITAL_PASS_NOT_FABRICATION_RELEASE"
assert all(x["return_code"] == 0 for x in summary["commands"])
assert (R/"docs/HANDOFF_KO.md").is_file()
assert kin["all_cases_passed"] and len(kin["cases"]) == 9
assert all(x["full_labeled_cycle_input_turns"] == x["parameters"]["q"] for x in kin["cases"])
assert all(x["maximum_velocity_fd_error_mm_s"] < 1e-5 for x in kin["cases"])
assert kin["gear_mesh_parity"] == {"one_external_mesh": -1, "one_idler_two_external_meshes": 1}
assert abs(kin["ideal_virtual_work"]["power_residual_W"]) < 1e-12
assert abs(kin["rotor_force_virtual_work"]["power_residual_W"]) < 1e-12
assert abs(kin["nominal_coupling"]["relative_center_speed_mm_s"]-98.96016858807846) < 1e-9
assert kin["nominal_coupling"]["loaded_contact_transfer_status"].startswith("HOLD")
assert len(motion["samples"]) == motion["nominal"]["q"]*24+1
assert cad["unexpected_collision_count"] == 0
assert cad["sampled_input_turns"] == motion["nominal"]["q"]
assert cad["process_reference_width_mm"] == 40
assert cad["static_all_pair"]["passed"] and cad["static_all_pair"]["pair_checks"] > 400
assert cad["dynamic_collision"]["executed"]
assert cad["dynamic_collision"]["positions_over_q_turns"] == 33
assert cad["dynamic_collision"]["pair_checks"] > 1000
assert cad["continuous_analytical_bounds"]["passed"]
assert cad["functional_pin_clearance"]["passed"]
assert cad["cad_numeric_frame_check"]["passed"]
for record in (cad["assembly"], cad["exploded"]):
    p = R.parent/record["file"]
    assert p.is_file(), p
    assert hashlib.sha256(p.read_bytes()).hexdigest() == record["sha256"]
    assert record["step_reimport_valid"] and record["reimported_solid_count"] == record["object_count"]
assert (R/"cad/PPR_C2_1_S2_transmission_schematic.svg").is_file()
assert cad["interfaces"]["nominal_clearance"].endswith("HOLD")
assert cad["interfaces"]["process_elements"].endswith("HOLD")
assert "axial_retention" in cad["not_checked"]
assert "sensor_integration" in cad["not_checked"]
assert kin["performance_gate"] == req["performance_gate"] == "BLOCKED_PERFORMANCE_DATA"
assert req["motors"]["shared_shredder_M1"] == 1 and req["motors"]["M1_selected"] is False
for stage in ("procurement", "fabrication", "energization"):
    assert req["deployment"][stage] == kin[stage] == cad[stage] == "HOLD"
print("C2.1 transmission kinematic/CAD artifacts passed; fabrication and ratings remain HOLD.")
