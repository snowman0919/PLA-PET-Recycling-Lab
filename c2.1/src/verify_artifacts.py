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

assert summary["overall"] == "DIGITAL_INTEGRATION_PASS_RATING_AND_PERFORMANCE_HOLD"
assert all(x["return_code"] == 0 for x in summary["commands"])
assert (R/"docs/HANDOFF_KO.md").is_file()
assert kin["all_cases_passed"] and len(kin["cases"]) == 9
assert all(x["full_labeled_cycle_input_turns"] == x["parameters"]["q"] for x in kin["cases"])
assert all(x["maximum_velocity_fd_error_mm_s"] < 1e-5 for x in kin["cases"])
assert kin["gear_mesh_parity"] == {"one_external_mesh": -1, "one_idler_two_external_meshes": 1}
assert abs(kin["ideal_virtual_work"]["power_residual_W"]) < 1e-12
assert abs(kin["rotor_force_virtual_work"]["power_residual_W"]) < 1e-12
assert abs(kin["nominal_coupling"]["relative_center_speed_mm_s"]-98.96016858807846) < 1e-9
assert kin["nominal_coupling"]["loaded_contact_transfer_status"] == "RIGID_FIRST_CONTACT_EQUILIBRIUM_PASS_ELASTIC_SHARING_RATING_HOLD"
assert kin["loaded_contact_takeup"]["result"] == "RIGID_FIRST_CONTACT_EQUILIBRIUM_PASS_RATING_HOLD"
assert kin["loaded_contact_takeup"]["maximum_equilibrium_residual_Nm"] < 1e-12
assert kin["loaded_contact_takeup"]["phase_takeup_deg"]["max"] < .4
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
assert cad["assembly"]["object_count"] == 41
assert summary["cad"]["assembly_objects"] == summary["cad"]["reimported_solids"] == 41
assert summary["cad"]["static_all_pair"] == cad["static_all_pair"]
assert summary["cad"]["dynamic"]["pair_checks"] == cad["dynamic_collision"]["pair_checks"]
assert summary["mechanism"]["loaded_contact"] == kin["loaded_output_contact"]
for key,path in (("transmission_py_sha256",R/"src/transmission.py"),
                 ("build_cad_py_sha256",R/"src/build_cad.py"),
                 ("test_sha256",R/"tests/test_transmission.py")):
    assert summary["artifacts"][key] == hashlib.sha256(path.read_bytes()).hexdigest()
assert "perforated screen" in cad["interfaces"]["process_elements"]
assert "axial_retention" in cad["not_checked"]
assert "sensor_mount_wiring_and_response" in cad["not_checked"]
assert kin["performance_gate"] == req["performance_gate"] == "BLOCKED_PERFORMANCE_DATA"
assert req["motors"]["shared_shredder_M1"] == 1 and req["motors"]["M1_selected"] is False
for stage in ("procurement", "fabrication", "energization"):
    assert req["deployment"][stage] == kin[stage] == cad[stage] == "HOLD"
print("C2.1 transmission kinematic/CAD artifacts passed; fabrication and ratings remain HOLD.")
