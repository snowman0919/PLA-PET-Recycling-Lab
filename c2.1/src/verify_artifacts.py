"""Verify the C2.1 P0-P6 digital package without granting hardware approval."""
from pathlib import Path
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile

R = Path(__file__).resolve().parents[1]
REPO = R.parent


def load(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


kin = load(R/"results/kinematic_validation.json")
cad = load(R/"results/cad_validation.json")
motion = load(R/"results/motion_samples.json")
req = load(R/"design/requirements.json")
summary = load(R/"results/validation_summary.json")
machine = load(R/"results/machine_integration.json")
native = load(R/"results/machine_freecad.json")
bom = load(R/"results/system_bom_summary.json")
wiring = load(R/"results/machine_wiring.json")
firmware = load(R/"results/firmware_build.json")
drawings = load(R/"results/p6_drawings.json")
manifest = load(R/"results/p6_manifest.json")

# C2.1 drivetrain evidence.
assert summary["overall"] == "DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD"
assert kin["all_cases_passed"] and len(kin["cases"]) == 9
assert all(case["full_labeled_cycle_input_turns"] == case["parameters"]["q"] for case in kin["cases"])
assert all(case["maximum_velocity_fd_error_mm_s"] < 1e-5 for case in kin["cases"])
assert kin["gear_mesh_parity"] == {"one_external_mesh": -1, "one_idler_two_external_meshes": 1}
assert abs(kin["ideal_virtual_work"]["power_residual_W"]) < 1e-12
assert abs(kin["rotor_force_virtual_work"]["power_residual_W"]) < 1e-12
assert kin["loaded_contact_takeup"]["result"] == "RIGID_FIRST_CONTACT_EQUILIBRIUM_PASS_RATING_HOLD"
assert kin["loaded_contact_takeup"]["maximum_equilibrium_residual_Nm"] < 1e-12
assert len(motion["samples"]) == motion["nominal"]["q"]*24+1
assert cad["unexpected_collision_count"] == 0
assert cad["static_all_pair"]["passed"] and cad["static_all_pair"]["pair_checks"] == 820
assert cad["dynamic_collision"]["executed"] and cad["dynamic_collision"]["pair_checks"] == 11360
assert cad["continuous_analytical_bounds"]["passed"] and cad["functional_pin_clearance"]["passed"]
assert cad["cad_numeric_frame_check"]["passed"]
for record in (cad["assembly"], cad["exploded"]):
    path = REPO/record["file"]
    assert path.is_file() and digest(path) == record["sha256"]
    assert record["step_reimport_valid"] and record["reimported_solid_count"] == record["object_count"] == 41

# Complete-machine integration, native CAD and envelope checks.
machine_step = REPO/machine["assembly_step"]
assert machine["status"] == "DIGITAL_MACHINE_INTEGRATION_PASS_RELEASE_HOLD"
# VP1 Stage 3: 191 legacy instances (S2/guard/puller/spool envelope
# instances excluded; the severed jackshaft counts its 2 solids as one
# record) + 41 S2 solids + 2 chains + 2 chute + 4 guards + 13 winder
# + 8 electrical = 222 objects; GUARD_CHAIN_B (4 segments) and the severed
# jackshaft (+1) bring the total to 225 solids
assert machine["assembly_objects"] == 222
assert machine["expected_solids"] == machine["reimported_solids"] == 225
assert machine["step_reimport_valid"] and digest(machine_step) == machine["assembly_step_sha256"]
assert not machine["missing_required_groups"]
assert machine["interface_collision"]["passed"] and not machine["interface_collision"]["unexpected"]
assert machine["relocated_support_collision"]["passed"]
assert machine["body"]["passed"] and machine["operating_envelope"]["passed"]
native_path = REPO/native["file"]
assert native["objects"] == native["valid_objects"] == 185
assert digest(native_path) == native["sha256"]
assert digest(R/"src/build_machine_freecad.py") == native["source_sha256"]

# Active BOM and review drawings.
for key in ("csv", "xlsx"):
    path = REPO/bom[key]["file"]
    assert digest(path) == bom[key]["sha256"]
assert zipfile.ZipFile(REPO/bom["xlsx"]["file"]).testzip() is None
assert bom["active_rows"] == bom["unique_part_ids"] == 163
assert bom["unknown_cost_rows"] == 152 and bom["procurement"] == "HOLD"
assert bom["vp1_delta_rows"] == 30 and bom["revision"] == "C2.1-P6+VP1-STAGE3"
assert bom["unselected_motor_landed_floor_KRW"] > bom["soft_total_budget_KRW"]
assert drawings["status"] == "NOMINAL_RFQ_REVIEW_ONLY_FABRICATION_RELEASE_HOLD"
for item in drawings["dxf"].values():
    assert digest(REPO/item["file"]) == item["sha256"]
pdf_path = REPO/drawings["pdf"]["file"]
assert pdf_path.read_bytes().startswith(b"%PDF-") and digest(pdf_path) == drawings["pdf"]["sha256"]
assert drawings["pdf"]["pages"] == 3 and drawings["fabrication"] == "HOLD"

# KiCad netlist is compared pin-for-pin with the source ledger; native ERC must be empty.
schematic = REPO/wiring["schematic"]
connections = REPO/wiring["connections"]
assert digest(schematic) == wiring["schematic_sha256"]
assert digest(connections) == wiring["connections_sha256"]
with connections.open(newline="", encoding="utf-8") as handle:
    expected = {(row["reference"], row["pin"]): row["net"] for row in csv.DictReader(handle)}
xml = ET.parse(R/"electrical/PPR_C2_1_machine_wiring.xml")
actual = {}
for net in xml.findall("./nets/net"):
    name = net.attrib["name"].removeprefix("/")
    for node in net.findall("node"):
        actual[(node.attrib["ref"], node.attrib["pin"])] = name
assert actual == expected and len(actual) == wiring["pins"] == 174
assert len(xml.findall("./components/comp")) == wiring["components"] == 43
assert len(xml.findall("./nets/net")) == wiring["nets"] == 67
erc = load(R/"electrical/PPR_C2_1_machine_wiring_erc.json")
assert not [violation for sheet in erc["sheets"] for violation in sheet["violations"]]
assert (R/"electrical/PPR_C2_1_machine_wiring.pdf").read_bytes().startswith(b"%PDF-")
analysis = load(R/"results/machine_wiring_analysis.json")
assert analysis["bom_lock"]["lock_pct"] == 0 and analysis["bom_lock"]["status"] == "fail"
assert wiring["hardware_release"] == wiring["energization"] == "HOLD"

# Portable logic build is evidence only; target build, flash and energization did not run.
assert firmware["compile_return_code"] == firmware["self_test_return_code"] == 0
assert firmware["cases"] == 11 and "11 cases passed" in firmware["self_test_stdout"]
assert digest(REPO/firmware["source"]) == firmware["source_sha256"]
assert firmware["target_cross_compile"] == firmware["flash"] == "DID_NOT_RUN"
assert firmware["energization"] == "HOLD"

# The manifest is self-excluding and must exactly match every listed artifact.
assert manifest["artifact_count"] == len(manifest["artifacts"])
for record in manifest["artifacts"]:
    path = REPO/record["file"]
    assert path.stat().st_size == record["bytes"] and digest(path) == record["sha256"]

assert req["performance_gate"] == "BLOCKED_PERFORMANCE_DATA"
assert req["motors"]["shared_shredder_M1"] == 1 and req["motors"]["M1_selected"] is False
for stage in ("procurement", "fabrication", "energization"):
    assert summary["release_boundary"][stage] == req["deployment"][stage] == "HOLD"
assert summary["release_boundary"]["physical_tests"] == "DID_NOT_RUN"
assert (R/"docs/ASSEMBLY_SERVICE_KO.md").is_file()
assert (R/"docs/OPEN_ACTIONS_KO.md").is_file()
print("C2.1 P0-P6 digital package passed; physical release, ratings and performance remain HOLD.")
