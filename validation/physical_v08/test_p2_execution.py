#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from p1_test_fixtures import fill_semantics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


P1 = load("analyze_p1_records")
P2 = load("analyze_p2_records")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def receipt(axis, gear, evidence_rel, evidence_sha, offset=18.0):
    return {
        "kind": "PHYSICAL_MEASUREMENT", "performed": True, "operator": "TECH-A",
        "part_serial": "SER-" + axis, "instrument_id": "MEAS-P1",
        "instrument_calibration_ref": "CAL-P1", "measured_at": "2026-09-10T23:40:00+09:00",
        "raw_files": {evidence_rel: evidence_sha}, "motor_model": "K9DG60N2", "gear_model": gear,
        "readings": {
            "voltage_v": {"value": 24.0, "u95": 0.0, "unit": "V"},
            "shaft_diameter": {"value": 11.99, "u95": 0.002, "unit": "mm"},
            "shaft_projection": {"value": 32.0, "u95": 0.05, "unit": "mm"},
            "bolt_pcd": {"value": 104.0, "u95": 0.01, "unit": "mm"},
            "output_offset": {"value": offset, "u95": 0.01, "unit": "mm"},
            "case_width": {"value": 90.0, "u95": 0.1, "unit": "mm"},
            "rear_length": {"value": 209.0, "u95": 0.1, "unit": "mm"},
        },
    }


def make_fixture(run: Path):
    evidence = run / "p2_evidence.txt"; evidence.write_text("synthetic P2 evidence\n", encoding="utf-8")
    digest = sha(evidence); rel = str(evidence.relative_to(ROOT))

    template = P1.read_csv(HERE / "templates/p1_inventory_record.csv")
    inv_rows = []
    for source in template:
        row = dict(source)
        if row["planned_state"] in P1.SURVEY_STATES or row["item_id"] in P1.GGM_AXES:
            marking = "MODEL"
            if row["item_id"] in P1.GGM_AXES:
                marking = "K9DG60N2 " + P1.GGM_AXES[row["item_id"]][1]
            row.update({
                "observed_quantity": "1", "manufacturer_model_marking": marking,
                "dimension_or_rating_summary": "checked", "condition": "GOOD",
                "instrument_id": "MEAS-P1", "instrument_calibration_ref": "CAL-P1",
                "measured_at": "2026-09-10T23:40:00+09:00", "operator": "TECH-A",
                "reviewer": "REVIEWER-B", "evidence_path": rel, "sha256": digest, "result": "PASS",
            })
        inv_rows.append(row)
    fill_semantics(inv_rows, ROOT, run)
    inventory = run / "p1_inventory.csv"
    write_csv(inventory, list(inv_rows[0]), inv_rows)

    bindings = {name: sha(ROOT / name) for name in (
        "control/ggm_drive_contract.json", "analysis/drive_acceptance_v08/manufacturing/drawing_contract.json")}
    packet_data = {
        "all_physical_actions_authorized": False,
        "design_sha256": bindings,
        "receipt": {"performed": True, "data": {
            "SH": receipt("SH", "K9G75C", rel, digest),
            "EX": receipt("EX", "K9G150C", rel, digest),
        }},
        "alignment": {"performed": False, "data": {}},
        "protection_pin": {"performed": False, "data": {}},
        "current_calibration": {"performed": False, "data": {}},
    }
    packet = run / "ggm_packet.json"; packet.write_text(json.dumps(packet_data, indent=2) + "\n", encoding="utf-8")

    with (HERE / "templates/profile_stock_measurement.csv").open(encoding="utf-8") as handle:
        stock_fields = next(csv.reader(handle))
    common = {
        "condition_check": "USABLE_REVIEWED", "inspection_power_state": "NONE",
        "source_asset": "LAB", "u95_length_mm": "1.0", "straightness_note": "OK",
        "damage_note": "NONE", "instrument_id": "MEAS-16", "instrument_calibration_ref": "CAL-LONG",
        "measured_at": "2026-09-10T23:42:00+09:00", "operator": "TECH-A", "reviewer": "REVIEWER-B",
        "evidence_path": rel, "sha256": digest, "status": "USABLE", "notes": "synthetic",
    }
    stock_rows = []
    for item, typ in (("ASSET-2020", "2020"), ("ASSET-2040", "2040")):
        detail=json.loads((ROOT/next(r for r in inv_rows if r["item_id"]==item)["detail_path"]).read_text())
        for entry in detail['entries']:
            stock_rows.append({**common,"record_id":entry['id'],"profile_type":typ,
                               "usable_length_mm":str(entry['quantity']),"u95_length_mm":str(entry['u95'])})
    stock = run / "profile_stock.csv"; write_csv(stock, stock_fields, stock_rows)

    approval_data = {
        "stage": "P2", "status": "APPROVED", "scope": P2.APPROVAL_SCOPE,
        "approved_by": "USER-A", "approved_at": "2026-09-10T23:45:00+09:00",
        "p1_inventory_sha256": sha(inventory), "ggm_packet_sha256": sha(packet),
        "profile_stock_sha256": sha(stock), "frame_cut_list_sha256": sha(P2.FRAME_CUTLIST),
        "frame_release_sha256": sha(ROOT/"exports/final/frame_v08/frame_release.json"),
        "kerf_budget_mm": 2.0, "procurement_authorized": False,
        "energization_authorized": False, "machine_release": "HOLD",
    }
    approval = run / "p2_approval.json"; approval.write_text(json.dumps(approval_data, indent=2) + "\n", encoding="utf-8")

    with (HERE / "templates/p2_cold_fit.csv").open(encoding="utf-8") as handle:
        template_rows = list(csv.DictReader(handle)); p2_fields = list(template_rows[0])
    numeric = {
        "frame_base_x": (470.0, 0.1), "frame_base_y": (700.0, 0.1),
        "frame_diagonal_a": (843.0, 0.1), "frame_diagonal_b": (843.2, 0.1),
        "rail_squareness_700": (0.30, 0.05), "shredder_min_static_clearance": (2.10, 0.05),
        "shredder_hand_rotation_contacts": (0.0, 0.0), "extruder_cold_axial_travel": (1.70, 0.05),
        "extruder_rear_retainer_endplay": (0.20, 0.02),
    }
    p2_rows = []
    for row in template_rows:
        metric = row["metric"]
        if metric in numeric:
            row["value"], row["u95"] = map(str, numeric[metric]); row["instrument_id"] = "MEAS-P2"; row["instrument_calibration_ref"] = "CAL-P2"
        else:
            row["value"] = "false"; row["u95"] = ""; row["instrument_id"] = ""; row["instrument_calibration_ref"] = ""
        row["operator"] = "TECH-A"; row["reviewer"] = "REVIEWER-B"; row["measured_at"] = "2026-09-10T23:55:00+09:00"
        row["evidence_path"] = rel; row["sha256"] = digest; p2_rows.append(row)
    record = run / "p2_cold_fit.csv"; write_csv(record, p2_fields, p2_rows)
    return record, inventory, packet, stock, approval


def refresh_approval(approval: Path, inventory: Path, packet: Path, stock: Path):
    data = json.loads(approval.read_text(encoding="utf-8"))
    data["p1_inventory_sha256"] = sha(inventory); data["ggm_packet_sha256"] = sha(packet); data["profile_stock_sha256"] = sha(stock)
    approval.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class P2ExecutionTest(unittest.TestCase):
    def test_p2_bound_prerequisites_pass_review_only(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            args = make_fixture(Path(td)); result = P2.evaluate(*args[:4], 2.0, args[4])
            self.assertEqual(result["status"], "P2_RECORD_CHECK_PASS")
            self.assertTrue(result["physical_evidence_evaluated"])
            self.assertFalse(result["fabrication_authorized"]); self.assertFalse(result["energization_authorized"])
            self.assertFalse(result["stage_release_granted"]); self.assertEqual(result["machine_release"], "HOLD")
            self.assertEqual(result["prerequisites"]["p1_status"], "P1_RECORD_CHECK_PASS")
            self.assertEqual(result["prerequisites"]["mount_status"], "AS_DRAWN_COMPATIBLE_NOT_AUTHORIZED")

    def test_p2_rejects_approval_binding_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, inventory, packet, stock, approval = make_fixture(Path(td))
            data=json.loads(approval.read_text()); data["profile_stock_sha256"]="0"*64; approval.write_text(json.dumps(data)+"\n")
            result=P2.evaluate(record,inventory,packet,stock,2.0,approval)
            self.assertEqual(result["status"],"NOT_RUN_OR_REJECTED"); self.assertIn("profile_stock_sha256",result["reason"])

    def test_p2_rejects_stale_mount_design_binding(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, inventory, packet, stock, approval = make_fixture(Path(td))
            data=json.loads(packet.read_text()); data["design_sha256"]["control/ggm_drive_contract.json"]="0"*64
            packet.write_text(json.dumps(data,indent=2)+"\n"); refresh_approval(approval,inventory,packet,stock)
            result=P2.evaluate(record,inventory,packet,stock,2.0,approval)
            self.assertEqual(result["status"],"NOT_RUN_OR_REJECTED"); self.assertIn("GGM mount",result["reason"])

    def test_p2_rejects_unnestable_profile_stock(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, inventory, packet, stock, approval = make_fixture(Path(td))
            with stock.open(encoding="utf-8") as handle: rows=list(csv.DictReader(handle)); fields=list(rows[0])
            next(row for row in rows if row["profile_type"]=="2040")["usable_length_mm"]="1000"
            write_csv(stock,fields,rows); refresh_approval(approval,inventory,packet,stock)
            result=P2.evaluate(record,inventory,packet,stock,2.0,approval)
            self.assertEqual(result["status"],"NOT_RUN_OR_REJECTED"); self.assertIn("2040 profile stock",result["reason"])

    def test_p2_rejects_incomplete_p1_survey(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, inventory, packet, stock, approval = make_fixture(Path(td))
            with inventory.open(encoding="utf-8") as handle: rows=list(csv.DictReader(handle)); fields=list(rows[0])
            next(row for row in rows if row["item_id"]=="ASSET-PSU")["result"]="NOT_RUN"
            write_csv(inventory,fields,rows); refresh_approval(approval,inventory,packet,stock)
            result=P2.evaluate(record,inventory,packet,stock,2.0,approval)
            self.assertEqual(result["status"],"NOT_RUN_OR_REJECTED"); self.assertIn("P1 full inventory",result["reason"])


if __name__ == "__main__":
    unittest.main()
