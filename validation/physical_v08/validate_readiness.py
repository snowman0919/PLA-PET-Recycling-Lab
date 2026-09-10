#!/usr/bin/env python3
"""Cross-check physical-readiness documents against current v0.8 design evidence."""
from __future__ import annotations
import csv, json, math
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

    assert sim["status"] == "PASS" and sim["required_technical_gate_count"] == 23
    assert sim["failed_technical_gates"] == []
    assert set(sim["excluded_release_only_gates"]) == {"20_release_package", "21_release_policy"}
    assert all(v is False for v in gate["global_state"].values() if isinstance(v, bool))
    assert [row["id"] for row in gate["gates"]] == [f"P{i}" for i in range(13)]

    assert ggm["selected"]["shredder"] == "GGM K9DG60N2 + K9G75C"
    assert ggm["selected"]["screw"] == "GGM K9DG60N2 + K9G150C"
    assert close(ggm["protection"]["command_limit_gearbox_nm"], 8.0)
    assert ggm["protection"]["mechanical_release_acceptance_nm"] == [8.8, 9.3]
    assert close(ggm["screw"]["hard_speed_limit_rpm"], 20)

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
    by_stage_id = {(r["gate"], r["item_id"]): r for r in stage_bom}
    assert len(stage_bom) == 28 and by_stage_id[("P4", "CUT-01")]["quantity"] == "2"
    assert by_stage_id[("P3", "PIN-COUPON")]["quantity"] == "9"
    assert by_stage_id[("P3", "GGM-SH")]["item"] == "GGM K9DG60N2 + K9G75C"
    assert by_stage_id[("P3", "GGM-EX")]["item"] == "GGM K9DG60N2 + K9G150C"
    assert by_stage_id[("P5", "EX-CPN-SCR")]["quantity"] == "1" and by_stage_id[("P5", "EX-CPN-BAR")]["quantity"] == "1"

    assert packet["all_physical_actions_authorized"] is False
    assert packet["simulation_prerequisite"]["current_status"] == "PASS"
    assert packet["simulation_prerequisite"]["technical_gate_count"] == 23
    import hashlib
    assert packet["simulation_prerequisite"]["current_sha256"] == hashlib.sha256((ROOT / "validation/physical_v08/simulation_prerequisite.json").read_bytes()).hexdigest()
    text = (ROOT / "exports/jigs/gate1/test_procedure_ko.md").read_text(encoding="utf-8")
    assert "legacy" in text and "K9DG60N2 + K9G75C" in text
    assert "software limit 8.0 N·m" in text
    plan = (ROOT / "release/build_final_documents.py").read_text(encoding="utf-8")
    for token in ("8.0 N·m", "8.8–9.3 N·m", "cold axial travel≥1.50 mm"):
        assert token in plan
    print(f"PHYSICAL_V08_READINESS_CONTRACT_OK gates={len(gate['gates'])} inventory={len(inv)} equipment={len(equipment)} sequence={len(seq)} stage_bom={len(stage_bom)}")

if __name__ == "__main__":
    main()
