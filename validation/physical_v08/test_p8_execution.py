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


P8 = load("analyze_p8_records")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def fixture(run: Path):
    evidence = run / "p8_evidence.txt"; evidence.write_text("synthetic P8 motor-run evidence")
    ev_rel = str(evidence.relative_to(ROOT)); ev_sha = digest(evidence)
    with (HERE / "templates/p8_motor_dry_run.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
    numeric = {
        "shredder_cutter_rpm": (16.0, .1), "shredder_max_current": (3.0, .1),
        "screw_start_rpm": (8.0, .1), "screw_max_rpm": (15.0, .1), "screw_max_current": (3.0, .1),
    }
    true_metrics = P8.BOOL_TRUE
    for row in rows:
        metric = row["metric"]
        if metric in numeric:
            row["value"], row["u95"] = map(str, numeric[metric])
            row["instrument_id"] = "SYN-METER"; row["calibration_ref"] = "SYN-CAL"
        else:
            row["value"] = "YES" if metric in true_metrics else "NO"; row["u95"] = ""
            row["instrument_id"] = "N/A"; row["calibration_ref"] = "N/A"
        row["measured_at"] = "2026-09-10T19:00:00+09:00"
        row["operator"] = "TECH-A"; row["reviewer"] = "REVIEWER-B"
        row["evidence_path"] = ev_rel; row["sha256"] = ev_sha
    record = run / "p8_motor_dry_run.csv"; write_csv(record, fields, rows)
    releases = {}
    for stage in ("p3", "p6", "p7"):
        path = run / f"{stage}_release.json"; path.write_text("{}\n"); releases[stage] = path
    profile = run / "profile"; profile.mkdir()
    tach = run / "tach.csv"; tach.write_text("synthetic\n")
    install = run / "install.csv"; install.write_text("synthetic\n")
    return record, releases, profile, tach, install

def run_eval(record, releases, profile, tach, install, *, p6_ok=True):
    return P8.evaluate(
        record, releases["p3"], releases["p6"], releases["p7"], profile, tach, install,
        p3_checker=lambda _: {"status": "P3_STAGE_RELEASE_VALIDATED", "p4_energization_authorized": False},
        p6_checker=lambda _: {"status": "P6_STAGE_RELEASE_VALIDATED" if p6_ok else "REJECTED", "p8_entry_prerequisite": p6_ok},
        p7_checker=lambda _: {"status": "P7_STAGE_RELEASE_VALIDATED", "p8_entry_prerequisite": True},
        fw_checker=lambda *_: {"status": "FIRMWARE_COMMISSIONING_RECORD_CHECK_PASS",
                               "firmware_prerequisite_for_p8": True,
                               "motor_energization_authorized": False,
                               "heater_energization_authorized": False},
    )


class P8ExecutionTest(unittest.TestCase):
    def test_authenticated_motor_record_passes_without_continuing_authority(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            fx = fixture(Path(td)); result = run_eval(*fx)
            self.assertEqual(result["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertTrue(result["input_motor_power_approval_recorded"])
            self.assertFalse(result["stage_p8_pass"]); self.assertFalse(result["hardware_authorization"])
            self.assertFalse(result["heater_energization_authorized"]); self.assertEqual(result["machine_release"], "HOLD")

    def test_motor_approval_record_is_mandatory(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases, profile, tach, install = fixture(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            next(row for row in rows if row["metric"] == "p8_motor_power_approval_recorded")["value"] = "NO"
            write_csv(record, fields, rows)
            result = run_eval(record, releases, profile, tach, install)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("p8_motor_power_approval_recorded", result["reason"])
    def test_current_ceiling_includes_u95(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases, profile, tach, install = fixture(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            current = next(row for row in rows if row["metric"] == "screw_max_current")
            current["value"] = "5.95"; current["u95"] = "0.10"
            write_csv(record, fields, rows)
            result = run_eval(record, releases, profile, tach, install)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("screw_max_current", result["reason"])

    def test_stale_raw_evidence_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases, profile, tach, install = fixture(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            rows[0]["sha256"] = "0" * 64; write_csv(record, fields, rows)
            result = run_eval(record, releases, profile, tach, install)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("evidence hash mismatch", result["reason"])

    def test_rejected_stage_prerequisite_blocks_p8(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            fx = fixture(Path(td)); result = run_eval(*fx, p6_ok=False)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("P6_STAGE_RELEASE_VALIDATED prerequisite rejected", result["reason"])


if __name__ == "__main__":
    unittest.main()
