#!/usr/bin/env python3
"""Optional empirical Gate-1 package readiness and procurement-lock audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "exports/jigs/gate1"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def rows(name):
    with (BASE / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def require_columns(name, required):
    with (BASE / name).open(newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames is not None, f"missing header {name}")
        missing = set(required) - set(reader.fieldnames)
        require(not missing, f"missing columns {name}: {sorted(missing)}")


def main():
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
        require((BASE / name).exists(), f"missing Gate-1 template {name}")
        require(len(rows(name)) == expected, f"unexpected row count {name}")

    require_columns("preflight_inspection_template.csv", {"item_id", "acceptance", "measured", "evidence_path", "operator", "reviewer", "pass_fail"})
    require_columns("drive_calibration_template.csv", {"donor_id", "calibration_type", "motor_current_A", "cutter_torque_Nm", "cutter_torque_per_amp_Nm_A", "derived_efficiency", "relief_released", "pass_fail"})
    require_columns("gate1_results_template.csv", {"material", "specimen_id", "peak_N", "radius_m", "calculated_peak_Nm", "failure_mode", "permanent_damage", "pass_fail"})
    require_columns("jam_recovery_results_template.csv", {"material", "trial", "trip_cutter_torque_Nm", "rpm_drop_percent", "reverse_duration_ms", "retry_count", "latched_fault_after_third_failure", "pass_fail"})
    require_columns("chip_size_results_template.csv", {"material", "input_mass_g", "mass_3_6_g", "mass_gt20_g", "fines_lt3_g", "recovery_percent", "pass_fail"})
    require_columns("evidence_manifest_template.csv", {"evidence_id", "relative_path", "sha256", "operator", "reviewer"})

    torque = rows("gate1_results_template.csv")
    require({row["material"] for row in torque} == {"PLA", "PET"}, "torque material coverage")
    require(all(row["pass_fail"] == "" for row in torque), "template must not contain physical PASS")
    jam = rows("jam_recovery_results_template.csv")
    require(sum(row["material"] == "PLA" for row in jam) == 3 and sum(row["material"] == "PET" for row in jam) == 3, "jam replicate coverage")
    chips = rows("chip_size_results_template.csv")
    require({row["material"] for row in chips} == {"PLA", "PET"}, "chip material coverage")
    drive = rows("drive_calibration_template.csv")
    require(sum(row["calibration_type"] == "TORQUE_CURRENT" for row in drive) == 5, "drive torque/current points")
    require(sum(row["calibration_type"] == "MECH_RELIEF" for row in drive) == 3, "mechanical relief repeats")

    for name in ("gate1_assembly.FCStd","gate1_assembly.step","gate1_assembly.stl",
                 "gate1_powered_assembly.FCStd","gate1_powered_assembly.step","gate1_powered_assembly.stl"):
        require((BASE/name).exists() and (BASE/name).stat().st_size > 100, f"missing controlling Gate-1 assembly {name}")
    bom=rows("bom.csv")
    by_id={row["item_id"]:row for row in bom}
    require(by_id["CUT-01"]["qty"] == "2" and "remaining 10" in by_id["CUT-01"]["notes"], "Gate-1 must release exactly two CUT-01 coupons")
    for item_id in ("CUT-01","CUT-03","CUT-04","CUT-05","CUT-08","DRV-03"):
        require("GATE1_RFQ_ALLOWED" in by_id[item_id]["status"], f"circular Gate-1 fabrication lock: {item_id}")
    require("AFTER_DONOR_MEASUREMENT" in by_id["DRV-01/Axx"]["status"], "donor adapter must remain measurement-locked")
    caps={row["item_id"]:int(row["planned_cash_krw"]) for row in csv.DictReader((ROOT/"bom/cash_budget.csv").open())
          if row["item_id"] not in {"TARGET_TOTAL","ABSOLUTE_CAP_RESERVE","ABSOLUTE_TOTAL_WITH_RESERVE"}}
    allocated={}
    for row in bom:
        bucket=row["budget_bucket"]
        allocated[bucket]=allocated.get(bucket,0)+int(row["planning_cash_krw"])
    for bucket,amount in allocated.items():
        require(bucket in caps, f"Gate-1 BOM references unknown budget bucket {bucket}")
        require(amount <= caps[bucket], f"Gate-1 allocation {bucket}={amount} exceeds cash budget {caps[bucket]}")

    physical = json.loads((ROOT / "validation/physical_gate_status.json").read_text())
    require(physical["optional_gate1_result"] == "NOT_RUN", "unreviewed optional empirical Gate-1 state")
    require(not physical["full_cutter_order_release"], "full cutter order accidentally released")
    require(not physical["full_screw_barrel_order_release"], "full screw/barrel order accidentally released")
    require(physical["main_promotion_allowed"] and physical["design_release_gate"] == "PASS", "digital design release incorrectly blocked")
    require(physical["procurement_approval_gate"] == "USER_APPROVAL_REQUIRED", "procurement approval bypassed")
    release = (BASE / "gate1_release_record_ko.md").read_text()
    require("현재 상태: `NOT_RUN`" in release and "결론: `NOT_RUN | FAIL | PASS`" in release, "Gate-1 release template state")

    result = {
        "revision": "implementation-crosssolver-v0.6",
        "gate": "OPTIONAL_EMPIRICAL_VALIDATION_GATE1_READINESS",
        "readiness": "OPTIONAL_EMPIRICAL_VALIDATION_READY_AFTER_USER_APPROVAL_AND_INVENTORY_VERIFICATION",
        "empirical_result": "OPTIONAL_NOT_RUN",
        "template_rows": expected_counts,
        "coverage": {
            "quasi_static_torque_specimens": 25,
            "jam_trials": {"PLA": 3, "PET": 3},
            "chip_batches": {"PLA": 1, "PET": 1},
            "drive_torque_current_points": 5,
            "mechanical_relief_repeats": 3,
            "preflight_checks": 14,
            "gate1_budget_allocation_krw": allocated,
            "evidence_hash_slots": 8,
        },
        "procurement_locks": {
            "full_cutter_order_release": False,
            "full_screw_barrel_order_release": False,
            "heater_purchase_release": False,
        },
        "design_release_gate": "PASS",
        "main_promotion_allowed": True,
        "remaining_external_inputs": [
            "exact donor identity and received inspection",
            "traceable instrument calibration",
            "user approval before purchase/CNC",
            "signed physical CSV and photo/video hashes",
        ],
        "status": "PASS",
    }
    output = ROOT / "validation/results/gate1_readiness.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("OPTIONAL_EMPIRICAL_GATE1_READINESS_OK torque=25 jam=6 chip=2")


if __name__ == "__main__":
    main()
