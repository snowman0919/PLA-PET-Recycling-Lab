#!/usr/bin/env python3
"""v0.8 two-cutter physical Gate P4 readiness audit; executes no hardware."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "exports/jigs/gate1"
PHYS = ROOT / "validation/physical_v08"

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def rows(name):
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def main():
    prereq = json.loads((PHYS / "simulation_prerequisite.json").read_text(encoding="utf-8"))
    stages = json.loads((PHYS / "stage_status.json").read_text(encoding="utf-8"))
    contract = json.loads((PHYS / "physical_gate_contract.json").read_text(encoding="utf-8"))
    require(prereq["status"] == "PASS" and prereq["required_technical_gate_count"] == 23,
            "23-gate technical prerequisite is not PASS")
    require(stages["physical_action_authorized"] is False and stages["stages"]["P4"] == "NOT_RUN",
            "template must not imply physical execution")
    require(next(g for g in contract["gates"] if g["id"] == "P3")["name"] == "GGM_DRIVE_BENCH",
            "P3 GGM bench contract missing")
    require(next(g for g in contract["gates"] if g["id"] == "P4")["name"] == "SHREDDER_COUPON",
            "P4 shredder contract missing")

    expected_counts = {
        "preflight_inspection_template.csv": 14,
        "calibration_log_template.csv": 4,
        "drive_calibration_template.csv": 9,
        "gate1_results_template.csv": 25,
        "jam_recovery_results_template.csv": 6,
        "chip_size_results_template.csv": 2,
        "evidence_manifest_template.csv": 8,
    }
    for name, expected in expected_counts.items():
        require((BASE / name).is_file() and len(rows(name)) == expected,
                f"missing/unexpected Gate-1 template {name}")

    bom = {row["item_id"]: row for row in rows("bom.csv")}
    require(bom["CUT-01"]["qty"] == "2" and "remaining 10" in bom["CUT-01"]["notes"],
            "P4 must fabricate exactly two CUT-01 coupons first")
    for item_id in ("CUT-01", "CUT-03", "CUT-04", "CUT-05", "CUT-05R", "CUT-08", "CUT-10", "DRV-03", "DRV-03R"):
        require("GATE1_RFQ_ALLOWED" in bom[item_id]["status"], f"coupon fabrication lock broken: {item_id}")
    require(bom["DRV-01/Axx"]["status"] == "LEGACY_NOT_FOR_GGM_DO_NOT_FABRICATE",
            "legacy donor adapter was reactivated")
    require(bom["G1J-11"]["status"] == "LEGACY_NOT_FOR_GGM_DO_NOT_FABRICATE",
            "legacy motor foot was reactivated")
    require(bom["GGM-SH-PATH"]["status"] == "P3_GGM_BENCH_PASS_REQUIRED_BEFORE_P4",
            "current GGM powered path not bound to P3")

    drive = rows("drive_calibration_template.csv")
    require(sum(r["calibration_type"] == "GGM_GEARBOX_TORQUE_CURRENT_REFERENCE" for r in drive) == 5,
            "GGM torque/current reference coverage")
    require(sum(r["calibration_type"] == "GGM_MECH_PROTECTION_REFERENCE" for r in drive) == 3,
            "GGM mechanical protection repeats")
    require(all(not r["cutter_torque_Nm"] for r in drive if r["calibration_type"].startswith("GGM_")),
            "legacy cutter torque preset leaked into GGM calibration template")
    jam = rows("jam_recovery_results_template.csv")
    require(all(r["command_rpm"] == "16" and not r["trip_cutter_torque_Nm"] for r in jam),
            "legacy jam command/torque preset remains")

    text = (BASE / "test_procedure_ko.md").read_text(encoding="utf-8")
    assembly = (BASE / "assembly_ko.md").read_text(encoding="utf-8")
    for token in ("K9DG60N2 + K9G75C", "software limit 8.0 N·m", "8.8–9.3 N·m"):
        require(token in text, f"current GGM criterion missing: {token}")
    require("legacy `gate1_powered_assembly.step`" in text and "legacy `gate1_powered_assembly.step`" in assembly,
            "legacy powered STEP not clearly deprecated")
    require((ROOT / "exports/final/manufacturing/drive_ggm/manifest.csv").is_file(),
            "final GGM drive manufacturing manifest missing")
    require((ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json").is_file(),
            "GGM physical inspection packet missing")

    result = {
        "revision": "physical-readiness-v0.8",
        "gate": "P4_SHREDDER_COUPON_READINESS",
        "readiness": "READY_AFTER_P3_PASS_AND_EXPLICIT_USER_APPROVAL",
        "physical_result": "NOT_RUN",
        "technical_prerequisite": "PASS_23_OF_23",
        "legacy_powered_path": "DISABLED_NOT_FOR_GGM",
        "minimum_cutter_coupon_count": 2,
        "remaining_cutter_count_locked": 10,
        "price_state": "INFORMATIONAL_NON_BLOCKING",
        "purchase_authorized": False,
        "fabrication_authorized": False,
        "energization_authorized": False,
        "status": "PASS",
    }
    out = ROOT / "validation/results/gate1_readiness.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P4_SHREDDER_COUPON_READINESS_OK current=GGM coupons=2 physical=NOT_RUN")

if __name__ == "__main__":
    main()
