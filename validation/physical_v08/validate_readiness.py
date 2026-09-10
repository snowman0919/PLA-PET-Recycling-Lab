#!/usr/bin/env python3
"""Cross-check physical-readiness documents against current v0.8 design evidence."""
from __future__ import annotations
import csv, json, math, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent

def j(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def rows(path: str):
    with (ROOT / path).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))

def close(a, b, tol=1e-9):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=tol)

def main():
    sim = j("validation/physical_v08/simulation_prerequisite.json")
    gate = j("validation/physical_v08/physical_gate_contract.json")
    ggm = j("control/ggm_drive_contract.json")
    params = j("cad/parameters/final_v08.json")
    hot = j("analysis/final_validation/results/v0.8/hot_zone_digital_qualification.json")
    die = j("analysis/final_validation/results/v0.8/die_joint_qualification.json")
    packet = j("analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json")
    inv = {r["item_id"]: r for r in rows("validation/physical_v08/inventory_confirmation.csv")}
    seq = rows("validation/physical_v08/fabrication_sequence.csv")
    equipment = rows("validation/physical_v08/measurement_equipment.csv")
    stage_bom = rows("validation/physical_v08/stage_minimum_bom.csv")
    p3_fixture = j("validation/physical_v08/p3_fixture_contract.json")
    p3_bom = rows("validation/physical_v08/p3_bench_bom.csv")
    p5 = j("validation/physical_v08/p5_coupon_contract.json")
    io = {r["signal"]: r for r in rows("electronics/io_schedule.csv")}
    pin_schedule = {r["symbol"]: r["mega_pin"] for r in rows("exports/final/electrical/pin_schedule.csv")}
    wire_schedule = {r["wire_id"]: r for r in rows("exports/final/electrical/wire_schedule.csv")}
    fuse_schedule = {r["fuse_id"]: r for r in rows("exports/final/electrical/fuse_schedule.csv")}

    assert sim["status"] == "PASS" and sim["required_technical_gate_count"] == 23
    assert sim["failed_technical_gates"] == []
    assert set(sim["excluded_release_only_gates"]) == {"20_release_package", "21_release_policy"}
    assert all(v is False for v in gate["global_state"].values() if isinstance(v, bool))
    assert [row["id"] for row in gate["gates"]] == [f"P{i}" for i in range(13)]
    p3 = next(row for row in gate["gates"] if row["id"] == "P3")
    assert not any("calibrated against independent reference" in x for x in p3["prerequisites"]), "P3 must not require its own calibration result as an entry condition"
    assert any("independent current reference available" in x for x in p3["prerequisites"])
    assert "P2 applicable cold-fit/fixture PASS" in p3["prerequisites"]
    assert any("pre-power evidence record check PASS" in x and "does not itself authorize" in x for x in p3["prerequisites"])
    p2_gate = next(row for row in gate["gates"] if row["id"] == "P2")
    assert any("470 +/-0.8 x 700 +/-0.8" in x for x in p2_gate["acceptance"])
    assert any("diagonal difference" in x and "<=1.0 mm" in x for x in p2_gate["acceptance"])

    assert ggm["selected"]["shredder"] == "GGM K9DG60N2 + K9G75C"
    assert ggm["selected"]["screw"] == "GGM K9DG60N2 + K9G150C"
    assert close(ggm["protection"]["command_limit_gearbox_nm"], 8.0)
    assert ggm["protection"]["mechanical_release_acceptance_nm"] == [8.8, 9.3]
    assert close(ggm["screw"]["hard_speed_limit_rpm"], 20)

    # GGM electrical handoff must agree across semantic I/O, generated pins, wires and branch protection.
    assert "SHREDDER_CURRENT_50A" not in io and "SCREW_PWM_DIR" not in io and "HOPPER_PTC" not in io
    assert io["SHREDDER_CURRENT"]["owner"].startswith("A0 ")
    assert "0-6 A" in io["SHREDDER_CURRENT"]["verification"] and "<=0.10 A" in io["SHREDDER_CURRENT"]["verification"]
    assert io["EXTRUDER_CURRENT"]["owner"].startswith("A9 ")
    assert "0-6 A" in io["EXTRUDER_CURRENT"]["verification"] and "<=0.40 N.m" in io["EXTRUDER_CURRENT"]["verification"]
    assert io["SCREW_BTS7960_PWM"]["owner"] == "D6 RPWM / D33 LPWM / D34 enable"
    assert "reverse request is rejected" in io["SCREW_BTS7960_PWM"]["verification"]
    assert "A10 puller / A11 spooler / D47 feeder" in io["DRIVER_FAULTS"]["owner"]
    assert pin_schedule["CURRENT_PIN"] == "A0" and pin_schedule["EX_CURRENT_PIN"] == "A9"
    assert "SHREDDER_FAULT_PIN" not in pin_schedule and "SCREW_FAULT_PIN" not in pin_schedule
    assert wire_schedule["SIG-A0"]["from"] == "Shredder Current" and wire_schedule["SIG-A0"]["to"] == "Mega A0"
    assert wire_schedule["SIG-A9"]["from"] == "Extruder Current" and wire_schedule["SIG-A9"]["to"] == "Mega A9"
    assert "GGM rated 4.6 A" in fuse_schedule["F-SH"]["maximum_current"]
    assert "not the motor operating-current or torque-limit setpoint" in fuse_schedule["F-SH"]["basis"]
    assert "GGM rated 4.6 A" in fuse_schedule["F-SCREW"]["maximum_current"]

    controller_text = (ROOT / "electronics/controller_wiring_v0.6.md").read_text(encoding="utf-8")
    topology_text = (ROOT / "electronics/safety_power_topology.md").read_text(encoding="utf-8")
    drive_text = (ROOT / "electronics/shredder_drive_wiring.md").read_text(encoding="utf-8")
    for text in (controller_text, topology_text, drive_text):
        assert "8.0 N.m" in text and "8.8" in text and "9.3" in text
    assert "A0" in controller_text and "A9" in controller_text and "D6 RPWM" in controller_text and "D33 LPWM" in controller_text
    assert "24 V 800 W" in topology_text and "F-MAIN = 30 A DC" in topology_text
    assert "GGM K9DG60N2 24 V + K9G75C" in drive_text and "D5" in drive_text and "D4" in drive_text and "D32" in drive_text

    hz = params["hot_zone_mount"]
    assert close(hz["fixed_collar_bore_mm"], 34.25)
    assert close(hz["sliding_guide_bore_mm"], 34.6)
    assert close(hz["cold_axial_travel_mm"], 1.5)
    assert close(params["rear_axial_retainer"]["collar_counterbore_mm"], 44.25)
    assert hot["status"] == "PASS" and close(hot["thermal_fit"]["declared_cold_axial_travel_mm"], 1.5)
    assert die["status"] == "PASS" and close(die["assembly_torque_nm"], 1.5)

    frame = rows("exports/fabrication/frame_cut_list.csv")
    totals = {}
    for r in frame:
        totals.setdefault(r["stock"], 0.0)
        totals[r["stock"]] += float(r["cut_length_mm"]) * int(r["quantity"])
    assert close(totals["20x20 aluminum profile"], 13348.0)
    assert close(totals["20x40 aluminum profile"], 1320.0)
    assert "13.348" in inv["ASSET-2020"]["required_quantity_or_capacity"]
    assert "1.320" in inv["ASSET-2040"]["required_quantity_or_capacity"]

    assert inv["ASSET-BTS"]["current_state"] == "USER_REPORTED_AVAILABLE"
    assert inv["ASSET-MEGA"]["current_state"] == "USER_REPORTED_AVAILABLE"
    assert inv["ASSET-ESTOP"]["current_state"] == "USER_REPORTED_AVAILABLE"
    assert inv["BUY-GGM-SH"]["current_state"] == "SELECTED_NOT_ORDERED"
    assert inv["BUY-GGM-EX"]["current_state"] == "SELECTED_NOT_ORDERED"
    assert len(equipment) >= 15 and len(seq) == 14
    required_execution_files = [
        "validation/physical_v08/P1_EXECUTION_KO.md",
        "validation/physical_v08/P2_COLD_FIT_KO.md",
        "validation/physical_v08/analyze_p2_records.py",
        "validation/physical_v08/templates/p2_cold_fit.csv",
        "validation/physical_v08/P3_GGM_BENCH_KO.md",
        "validation/physical_v08/profile_nesting.py",
        "validation/physical_v08/analyze_p3_preflight.py",
        "validation/physical_v08/templates/p3_preflight.csv",
        "validation/physical_v08/analyze_p3_records.py",
        "validation/physical_v08/p3_bench_bom.csv",
        "validation/physical_v08/templates/p1_inventory_record.csv",
        "validation/physical_v08/templates/p3_current_sensor_calibration.csv",
        "validation/physical_v08/templates/p3_no_load.csv",
        "validation/physical_v08/templates/p3_torque_map.csv",
        "validation/physical_v08/templates/p3_pin_release.csv",
        "validation/physical_v08/P5_PROCESS_COUPON_KO.md",
        "validation/physical_v08/p5_coupon_contract.json",
        "validation/physical_v08/analyze_p5_records.py",
        "validation/physical_v08/templates/p5_supplier_capability.csv",
        "validation/physical_v08/templates/p5_coupon_measurements.csv",
        "validation/physical_v08/templates/p5_coupon_certificates.csv",
        "validation/physical_v08/p5_supplier_inspection_requirements.csv",
        "validation/physical_v08/build_p5_inquiry_package.py",
        "validation/physical_v08/analyze_ggm_mount_compatibility.py",
        "validation/physical_v08/build_p3_inspection_packet.py",
        "validation/physical_v08/build_p3_firmware_profile.py",
        "validation/physical_v08/validate_p3_stage_release.py",
        "validation/physical_v08/test_p3_packet_builder.py",
        "validation/physical_v08/analyze_p4_records.py",
        "validation/physical_v08/test_p4_execution.py",
        "validation/physical_v08/validate_p4_stage_release.py",
        "validation/physical_v08/templates/p4_stage_release.json",
        "validation/physical_v08/templates/p4_preflight.csv",
        "validation/physical_v08/templates/p4_quasistatic.csv",
        "validation/physical_v08/templates/p4_jam.csv",
        "validation/physical_v08/templates/p4_chip.csv",
        "validation/physical_v08/validate_fabrication_handoff.py",
    ]
    assert all((ROOT / f).is_file() and (ROOT / f).stat().st_size > 0 for f in required_execution_files)
    by_stage_id = {(r["gate"], r["item_id"]): r for r in stage_bom}
    assert len(stage_bom) == 29 and by_stage_id[("P4", "CUT-01")]["quantity"] == "2"
    assert by_stage_id[("P3", "PIN-COUPON")]["quantity"] == "9"
    sprockets = by_stage_id[("P4", "GGM-SPROCKETS")]
    assert sprockets["quantity"] == "1 pair" and "direct-keyed" in sprockets["item"] and "DRV-02 superseded" in sprockets["notes"]
    assert by_stage_id[("P3", "GGM-SH")]["item"] == "GGM K9DG60N2 + K9G75C"
    assert by_stage_id[("P3", "GGM-EX")]["item"] == "GGM K9DG60N2 + K9G150C"
    assert by_stage_id[("P5", "EX-CPN-SCR")]["quantity"] == "1" and by_stage_id[("P5", "EX-CPN-BAR")]["quantity"] == "1"
    assert p3_fixture["status"] == "DESIGN_ONLY_NOT_FABRICATED" and p3_fixture["physical_action_authorized"] is False
    assert close(p3_fixture["prony"]["reaction_arm_mm"], 250.0) and close(p3_fixture["prony"]["reaction_arm_tolerance_mm"], 0.5)
    assert close(p3_fixture["calculated_force_n_at_250mm"]["8.00"], 32.0)
    assert close(p3_fixture["calculated_force_n_at_250mm"]["9.30"], 37.2)
    assert p3_fixture["mechanical_release"]["coupon_count"] == 9
    assert any(r["id"] == "P3-BRK-01" and "OPTIONAL" in r["disposition"] for r in p3_bom)
    registry = j("validation/physical_v08/physical_execution_registry.json")
    p3_registry = next(stage for stage in registry["stages"] if stage["id"] == "P3")
    assert p3_registry["preflight_analyzer"] == "analyze_p3_preflight.py"
    assert p3_registry["packet_builder"] == "build_p3_inspection_packet.py"
    assert p3_registry["firmware_profile_builder"] == "build_p3_firmware_profile.py"
    assert p3_registry["stage_release_validator"] == "validate_p3_stage_release.py"
    assert "templates/p3_preflight.csv" in p3_registry["templates"]
    p3_preflight_header = (ROOT / "validation/physical_v08/templates/p3_preflight.csv").read_text(encoding="utf-8").splitlines()[0]
    assert p3_preflight_header == "check_id,observed,status,operator,reviewer,checked_at,evidence_path,sha256,notes"
    p3_doc = (ROOT / "validation/physical_v08/P3_GGM_BENCH_KO.md").read_text(encoding="utf-8")
    assert "--preflight-result" in p3_doc and "PREPOWER_RECORD_CHECK_PASS" in p3_doc
    assert "validate_p3_stage_release.py" in p3_doc and "P3_STAGE_RELEASE_VALIDATED" in p3_doc
    assert "build_p3_firmware_profile.py" in p3_doc and "p8_entry_prerequisite`는 false" in p3_doc
    p4_doc = (ROOT / "validation/physical_v08/P4_SHREDDER_COUPON_KO.md").read_text(encoding="utf-8")
    assert "validate_p3_stage_release.py" in p4_doc and "P3_STAGE_RELEASE_VALIDATED" in p4_doc
    p4_analyzer = (ROOT / "validation/physical_v08/analyze_p4_records.py").read_text(encoding="utf-8")
    assert "validate_p3_stage_release.py" in p4_analyzer and "p3_prerequisite" in p4_analyzer
    launch_builder = (ROOT / "validation/physical_v08/build_physical_launch_package.py").read_text(encoding="utf-8")
    assert "validate_*_stage_release.py" in launch_builder
    assert "torque_from_force" in p4_analyzer and "fraction_3_6_lower_percent" in p4_analyzer
    p4_registry = next(stage for stage in registry["stages"] if stage["id"] == "P4")
    assert p4_registry["templates"] == ["templates/p4_preflight.csv", "templates/p4_quasistatic.csv", "templates/p4_jam.csv", "templates/p4_chip.csv", "templates/p4_stage_release.json"]
    assert p4_registry["stage_release_validator"] == "validate_p4_stage_release.py"
    p4_release = j("validation/physical_v08/templates/p4_stage_release.json")
    assert p4_release["status"] == "NOT_RUN" and p4_release["remaining_cut01_quantity"] == 10
    assert p4_release["remaining_cut01_fabrication_authorized"] is False and p4_release["downstream_energization_authorized"] is False
    assert len(rows("validation/physical_v08/templates/p4_preflight.csv")) == 27
    assert len(rows("validation/physical_v08/templates/p4_quasistatic.csv")) == 25
    assert len(rows("validation/physical_v08/templates/p4_jam.csv")) == 6
    assert len(rows("validation/physical_v08/templates/p4_chip.csv")) == 2
    assert "P4_STAGE_RELEASE_VALIDATED" in p4_doc and "remaining_cut01_fabrication_authorized" in p4_doc
    for token in ("GGM_SH_12T", "GGM_SH_30T", "DRV-02", "radial TIR", "axial shift"):
        assert token in p4_doc
    chain = ggm["shredder"]["chain_drive"]
    assert chain["input_sprocket"]["part_id"] == "GGM_SH_12T" and chain["output_sprocket"]["part_id"] == "GGM_SH_30T"
    assert close(chain["assembled_axial_shift_u95_mm_max"], .20) and close(chain["output_sprocket"]["radial_tir_mm_max"], .10)
    p4_gate = next(row for row in gate["gates"] if row["id"] == "P4")
    assert any("DRV-02 is not an active P4 part" in x for x in p4_gate["acceptance"])
    p3_builder = (ROOT / "validation/physical_v08/build_p3_inspection_packet.py").read_text(encoding="utf-8")
    assert 'add_argument("--preflight-result"' in p3_builder and 'result["p3_preflight"]' in p3_builder
    p3_inspector = (ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py").read_text(encoding="utf-8")
    assert "authenticated P3 preflight is required" in p3_inspector
    assert p5["status"] == "DESIGN_ONLY_NOT_ORDERED" and p5["purchase_or_manufacturing_authorized"] is False
    assert p5["screw"]["quantity"] == 1 and p5["barrel"]["quantity"] == 1
    assert p5["screw"]["effective_case_after_final_grind_mm"] == [0.30, 0.50]
    assert close(p5["barrel"]["effective_case_after_final_hone_mm_min"], 0.25)
    assert p5["barrel"]["nitriding_effective_case_process_target_mm"] == [0.30, 0.50]
    assert p5["matched_pair"]["actual_diametral_clearance_mm"] == [0.28, 0.32]
    assert "absence alone does not reject P5" in p5["traceability"]["hot_properties_policy"]
    meas15 = next(r for r in equipment if r["id"] == "MEAS-15")
    assert "microhardness" in meas15["minimum_capability"] and "test load" in meas15["minimum_capability"]

    assert packet["all_physical_actions_authorized"] is False
    packet_p0 = packet["simulation_prerequisite"]
    assert packet_p0["source"] == "validation/physical_v08/simulation_prerequisite.py"
    assert packet_p0["required_status"] == "PASS" and packet_p0["runtime_status"] == "RUNTIME_CHECK_REQUIRED"
    import hashlib
    assert packet_p0["source_sha256"] == hashlib.sha256((ROOT / packet_p0["source"]).read_bytes()).hexdigest()
    text = (ROOT / "exports/jigs/gate1/test_procedure_ko.md").read_text(encoding="utf-8")
    assert "legacy" in text and "K9DG60N2 + K9G75C" in text
    assert "software limit 8.0 N·m" in text
    plan = (ROOT / "release/build_final_documents.py").read_text(encoding="utf-8")
    for token in ("8.0 N·m", "8.8–9.3 N·m", "cold axial travel≥1.50 mm"):
        assert token in plan
    subprocess.run([sys.executable, str(BASE / "validate_fabrication_handoff.py")], check=True, cwd=ROOT)
    print(f"PHYSICAL_V08_READINESS_CONTRACT_OK gates={len(gate['gates'])} inventory={len(inv)} equipment={len(equipment)} sequence={len(seq)} stage_bom={len(stage_bom)}")

if __name__ == "__main__":
    main()
