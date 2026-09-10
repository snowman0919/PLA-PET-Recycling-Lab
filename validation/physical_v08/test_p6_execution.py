#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


P5 = load("analyze_p5_records")
P5REL = load("validate_p5_stage_release")
P6 = load("analyze_p6_records")
T5 = load("test_p5_execution")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        w = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(rows)

def make_p5_release(run: Path) -> Path:
    T5.synthetic_packet(run, False)
    result = P5.evaluate(run)
    assert result["status"] == "NUMERIC_RECORD_CHECK_PASS"
    result_path = run / "p5_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n")
    release = {
        "stage": "P5", "status": "PASS", "release_scope": "P5_COUPON_COMPLETE_P6_REVIEW_ONLY",
        "approved_by": "ENGINEER-A", "independent_reviewer": "REVIEWER-B",
        "reviewed_at": "2026-09-10T17:45:00+09:00", "records_dir": str(run.relative_to(ROOT)),
        "p5_result": result_path.name, "p5_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "qualified_supplier": "SYN-SUPPLIER", "qualified_route_id": "SYN-ROUTE-01",
        "screw_heat_reservation_ref": "SYN-SCR-HEAT", "barrel_heat_reservation_ref": "SYN-BAR-HEAT",
        "p6_entry_review": True, "action_state": "HOLD", "machine_release": "HOLD",
    }
    path = run / "p5_stage_release.json"; path.write_text(json.dumps(release, indent=2) + "\n")
    assert P5REL.validate(path)["status"] == "P5_STAGE_RELEASE_VALIDATED"
    return path


def make_p6_records(run: Path, route: str = "SYN-ROUTE-01"):
    evidence = run / "p6_evidence.txt"; evidence.write_text("synthetic P6 evidence")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest(); rel = str(evidence.relative_to(ROOT))
    with (HERE / "templates/p6_production_receipt.csv").open(encoding="utf-8") as handle:
        receipt_fields = list(csv.DictReader(handle).fieldnames)
    receipt_rows = []
    for part, serial, reservation in (("EX-SCR-01", "SCR-SYN-01", "SYN-SCR-HEAT"), ("EX-BAR-01", "BAR-SYN-01", "SYN-BAR-HEAT")):
        receipt_rows.append({
            "part_id": part, "part_serial": serial, "supplier_id": "SYN-SUPPLIER",
            "qualified_route_id": route, "heat_reservation_ref": reservation,
            "material_grade": "SCM440 JIS G4105", "heat_lot_id": "SYN-HEAT-PROD",
            "material_certificate_id": "MTC-SYN", "process_certificate_id": "PROC-SYN",
            "final_finish_report_id": "FIN-SYN", "received_at": "2026-09-10T17:50:00+09:00",
            "operator": "RECEIVER-A", "reviewer": "REVIEWER-B", "evidence_path": rel,
            "sha256": digest, "disposition": "PASS", "notes": "synthetic only",
        })
    write_csv(run / "p6_production_receipt.csv", receipt_fields, receipt_rows)

    with (HERE / "templates/p6_cold_extruder.csv").open(encoding="utf-8") as handle:
        cold_fields = list(csv.DictReader(handle).fieldnames)
    numeric = {
        "screw_barrel_clearance_min": (0.295, 0.005, "mm"),
        "screw_barrel_clearance_max": (0.305, 0.005, "mm"),
        "bearing_pocket_diametral_clearance": (0.325, 0.005, "mm"),
        "thrust_loaded_endplay": (0.10, 0.01, "mm"),
        "hand_rotation_contacts": (0.0, 0.0, "count"),
        "drive_coaxiality": (0.03, 0.005, "mm"),
        "front_guide_cold_axial_travel": (1.65, 0.05, "mm"),
        "rear_retainer_cold_endplay": (0.20, 0.02, "mm"),
    }
    cold_rows = []
    for metric, (value, u95, unit) in numeric.items():
        cold_rows.append({
            "metric": metric, "value": str(value), "u95": str(u95), "unit": unit,
            "acceptance": "synthetic", "instrument_id": "SYN-MET", "calibration_ref": "SYN-CAL",
            "measured_at": "2026-09-10T18:00:00+09:00", "operator": "ASSEMBLER-A",
            "reviewer": "REVIEWER-B", "evidence_path": rel, "sha256": digest, "notes": "synthetic only",
        })
    for metric, value in (("thrust_washer_orientation_ok", "YES"), ("printed_shim_used", "NO")):
        cold_rows.append({
            "metric": metric, "value": value, "u95": "", "unit": "boolean",
            "acceptance": "synthetic", "instrument_id": "N/A", "calibration_ref": "N/A",
            "measured_at": "2026-09-10T18:00:00+09:00", "operator": "ASSEMBLER-A",
            "reviewer": "REVIEWER-B", "evidence_path": rel, "sha256": digest, "notes": "synthetic only",
        })
    write_csv(run / "p6_cold_extruder.csv", cold_fields, cold_rows)
    return run / "p6_production_receipt.csv", run / "p6_cold_extruder.csv"


class P6ExecutionTest(unittest.TestCase):
    def test_p6_binds_p5_route_and_evidence(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); p5_release = make_p5_release(run)
            receipt, cold = make_p6_records(run)
            result = P6.evaluate(cold, p5_release, receipt)
            self.assertEqual(result["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertFalse(result["stage_p6_pass"]); self.assertEqual(result["action_state"], "HOLD")
            self.assertEqual(result["production_receipt"]["route"], "SYN-ROUTE-01")

    def test_p6_rejects_route_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); p5_release = make_p5_release(run)
            receipt, cold = make_p6_records(run, route="OTHER-ROUTE")
            result = P6.evaluate(cold, p5_release, receipt)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("supplier/process route differs", result["reason"])

    def test_p6_rejects_stale_cold_evidence(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); p5_release = make_p5_release(run)
            receipt, cold = make_p6_records(run)
            with cold.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            rows[0]["sha256"] = "0" * 64
            write_csv(cold, rows[0].keys(), rows)
            result = P6.evaluate(cold, p5_release, receipt)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("evidence hash mismatch", result["reason"])

    def test_p6_rejects_invalid_p5_release(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); p5_release = make_p5_release(run)
            receipt, cold = make_p6_records(run)
            release = json.loads(p5_release.read_text())
            release["qualified_route_id"] = "TAMPERED"
            p5_release.write_text(json.dumps(release, indent=2) + "\n")
            result = P6.evaluate(cold, p5_release, receipt)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("P5", result["reason"])


if __name__ == "__main__":
    unittest.main()
