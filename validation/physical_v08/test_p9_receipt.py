#!/usr/bin/env python3
import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


P9R = load("analyze_p9_receipt")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def make_record(run: Path):
    evidence = run / "p9_receipt_evidence.txt"
    evidence.write_text("synthetic hot-zone receipt evidence")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    relative = str(evidence.relative_to(ROOT))
    tape_contract = ROOT / "control/thermal_barrier_tape_contract.json"
    s4_result = run / "s4_result.json"
    s4_result.write_text(__import__("json").dumps({
        "status": "S4_THERMAL_BARRIER_TAPE_SMOKE_PASS",
        "p9_tape_smoke_prerequisite": True,
        "installation_authorized": False,
        "heater_energization_authorized": False,
        "machine_release": "HOLD",
        "contract_sha256": hashlib.sha256(tape_contract.read_bytes()).hexdigest(),
    }) + "\n", encoding="utf-8")
    s4_digest = hashlib.sha256(s4_result.read_bytes()).hexdigest()
    s4_relative = str(s4_result.relative_to(ROOT))
    with (HERE / "templates/p9_hot_zone_receipt.csv").open(encoding="utf-8") as handle:
        template = list(csv.DictReader(handle)); fields = list(template[0].keys())
    for row in template:
        metric = row["metric"]
        if metric in P9R.RANGES:
            lo, hi, _ = P9R.RANGES[metric]
            row["value"] = str((lo + hi) / 2); row["u95"] = "0.001"
            row["instrument_id"] = "SYN-METER"; row["calibration_ref"] = "SYN-CAL"
        elif metric in P9R.MAXIMUMS:
            limit, _ = P9R.MAXIMUMS[metric]
            row["value"] = str(limit * 0.5); row["u95"] = "0.01"
            row["instrument_id"] = "SYN-METER"; row["calibration_ref"] = "SYN-CAL"
        elif metric in P9R.MINIMUMS:
            limit, _ = P9R.MINIMUMS[metric]
            row["value"] = str(limit * 1.5); row["u95"] = "0.1"
            row["instrument_id"] = "SYN-METER"; row["calibration_ref"] = "SYN-CAL"
        elif metric in P9R.POSITIVE:
            defaults = {"tape_width": 25.0, "tape_thickness": 0.06, "tape_continuous_service_rating": 220.0}
            row["value"] = str(defaults[metric])
            row["u95"] = {"tape_continuous_service_rating": "0", "tape_width": "0.1", "tape_thickness": "0.005"}[metric]
            row["instrument_id"] = "SYN-METER"; row["calibration_ref"] = "SYN-CAL"
        else:
            row["value"] = "YES"; row["u95"] = ""
            row["instrument_id"] = "N/A"; row["calibration_ref"] = "N/A"
        row["measured_at"] = "2026-09-10T20:30:00+09:00"
        row["operator"] = "TECH-A"; row["reviewer"] = "REVIEWER-B"
        if metric == "tape_coupon_smoke_pass":
            row["evidence_path"] = s4_relative; row["sha256"] = s4_digest
        else:
            row["evidence_path"] = relative; row["sha256"] = digest
    path = run / "p9_hot_zone_receipt.csv"
    write_csv(path, fields, template)
    return path


class P9ReceiptTest(unittest.TestCase):
    def test_authenticated_receipt_passes_without_power_authority(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td)); result = P9R.evaluate(path)
            self.assertEqual(result["status"], "HOT_ZONE_RECEIPT_RECORD_CHECK_PASS")
            self.assertTrue(result["p9_receipt_prerequisite"])
            self.assertFalse(result["power_authorization"])
            self.assertEqual(result["machine_release"], "HOLD")

    def test_out_of_range_die_resistance_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            next(r for r in rows if r["metric"] == "die_cold_resistance")["value"] = "11.0"
            write_csv(path, fields, rows); result = P9R.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("die_cold_resistance", result["reason"])

    def test_spare_cannot_be_counted_as_installed(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            next(r for r in rows if r["metric"] == "tf_spare_not_installed")["value"] = "NO"
            write_csv(path, fields, rows); result = P9R.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("tf_spare_not_installed", result["reason"])

    def test_invalid_s4_result_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            row = next(r for r in rows if r["metric"] == "tape_coupon_smoke_pass")
            s4 = ROOT / row["evidence_path"]
            data = __import__("json").loads(s4.read_text()); data["status"] = "S4_NOT_RUN_OR_REJECTED"
            s4.write_text(__import__("json").dumps(data) + "\n")
            row["sha256"] = hashlib.sha256(s4.read_bytes()).hexdigest()
            write_csv(path, fields, rows); result = P9R.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("S4 result is not PASS", result["reason"])

    def test_rejects_280c_as_continuous_tape_rating(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            row = next(r for r in rows if r["metric"] == "tape_continuous_service_rating")
            row["value"] = "280"; row["u95"] = "0"
            write_csv(path, fields, rows); result = P9R.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("fixed 220 C", result["reason"])

    def test_legacy_z1_width_and_unapproved_revision_rejected(self):
        for metric, value in [('bh_z1_width', '45'),
                              ('bh_z1_revised_supplier_drawing_accepted', 'NO'),
                              ('tcr_fastener_stack_no_bottoming_verified', 'NO')]:
            with self.subTest(metric=metric), tempfile.TemporaryDirectory(dir=HERE) as td:
                path = make_record(Path(td))
                with path.open(encoding='utf-8') as handle:
                    rows = list(csv.DictReader(handle)); fields = list(rows[0])
                next(r for r in rows if r['metric'] == metric)['value'] = value
                write_csv(path, fields, rows)
                result = P9R.evaluate(path)
                self.assertEqual(result['status'], 'NOT_RUN_OR_REJECTED')
                self.assertIn(metric, result['reason'])

    def test_evidence_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            rows[0]["sha256"] = "0" * 64
            write_csv(path, fields, rows); result = P9R.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("evidence hash mismatch", result["reason"])


if __name__ == "__main__":
    unittest.main()
