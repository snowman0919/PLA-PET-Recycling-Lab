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


P12 = load("analyze_p12_records")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def p11_stub(_):
    return {"status": "P11_STAGE_RELEASE_VALIDATED", "p12_entry_prerequisite": True,
            "material_feed_authorized": False, "continuing_power_authority": False,
            "machine_release": "HOLD"}


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def make_p12(run: Path):
    evidence = run / "forming.log"; evidence.write_text("synthetic forming evidence\n", encoding="utf-8")
    result_path = run / "p11_result.json"
    result_path.write_text(json.dumps({"status": "MATERIAL_RUN_RECORD_CHECK_PASS", "material": "PET",
                                      "context": {"lot_id": "PET-SYN-01"}}, indent=2) + "\n", encoding="utf-8")
    p11_release = run / "p11_release.json"
    p11_release.write_text(json.dumps({"p11_result": result_path.name,
                                       "p11_result_sha256": sha(result_path)}, indent=2) + "\n", encoding="utf-8")
    with (HERE / "templates/p12_forming_spool.csv").open(encoding="utf-8") as handle:
        template = list(csv.DictReader(handle)); fields = list(template[0])
    numeric = {
        "puller_slip": (0.5, 0.1), "traverse_usable_width": (68.5, 0.1),
        "dancer_control_stop_angle": (0.34, 0.005), "dancer_peak_angle": (0.40, 0.005),
        "spool_test_load_mass": (1.10, 0.02), "diameter_mean_error": (0.02, 0.005),
        "diameter_max_ovality": (0.02, 0.005), "diameter_max_u95": (0.02, 0.0),
        "gearbox_torque_peak": (5.0, 0.2), "motor_current_peak": (4.0, 0.1),
    }
    true_metrics = P12.BOOL_TRUE
    false_metrics = P12.BOOL_FALSE
    rows = []
    for row in template:
        metric = row["metric"]
        row["source_lot_id"] = "PET-SYN-01"
        row["measured_at"] = "2026-09-10T22:50:00+09:00"
        row["operator"] = "TECH-A"; row["reviewer"] = "REVIEWER-B"
        row["evidence_path"] = str(evidence.relative_to(ROOT)); row["sha256"] = sha(evidence)
        if metric in numeric:
            row["value"], row["u95"] = map(str, numeric[metric])
            row["instrument_id"] = "SYN-MEAS"; row["calibration_ref"] = "SYN-CAL"
        elif metric in true_metrics:
            row["value"] = "YES"; row["u95"] = ""; row["instrument_id"] = "N/A"; row["calibration_ref"] = "N/A"
        elif metric in false_metrics:
            row["value"] = "NO"; row["u95"] = ""; row["instrument_id"] = "N/A"; row["calibration_ref"] = "N/A"
        rows.append(row)
    record = run / "p12.csv"; write_csv(record, fields, rows)
    return record, p11_release


class P12ExecutionTest(unittest.TestCase):
    def test_p12_pass_remains_review_only(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, p11 = make_p12(Path(td))
            result = P12.evaluate(record, p11, p11_checker=p11_stub)
            self.assertEqual(result["status"], "P12_RECORD_CHECK_PASS")
            self.assertEqual(result["source_lot_id"], "PET-SYN-01")
            self.assertFalse(result["stage_p12_pass"])
            self.assertFalse(result["physical_validation_complete_candidate"])
            self.assertFalse(result["production_authorized"])
            self.assertFalse(result["safety_certification"])

    def test_p12_rejects_lot_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, p11 = make_p12(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            for row in rows: row["source_lot_id"] = "PET-OTHER"
            write_csv(record, fields, rows)
            result = P12.evaluate(record, p11, p11_checker=p11_stub)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("source_lot_id", result["reason"])

    def test_p12_rejects_dancer_limit(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, p11 = make_p12(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            by = {row["metric"]: row for row in rows}
            by["dancer_control_stop_angle"]["value"] = "0.358"
            by["dancer_control_stop_angle"]["u95"] = "0.005"
            write_csv(record, fields, rows)
            result = P12.evaluate(record, p11, p11_checker=p11_stub)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("dancer_control_stop_angle", result["reason"])

    def test_p12_rejects_evidence_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, p11 = make_p12(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            rows[0]["sha256"] = "0" * 64; write_csv(record, fields, rows)
            result = P12.evaluate(record, p11, p11_checker=p11_stub)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("evidence hash mismatch", result["reason"])

    def test_p12_rejects_invalid_p11_release(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, p11 = make_p12(Path(td))
            bad = lambda _: {"status": "NOT_RUN_OR_REJECTED", "machine_release": "HOLD"}
            result = P12.evaluate(record, p11, p11_checker=bad)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("P11 stage release", result["reason"])


if __name__ == "__main__":
    unittest.main()
