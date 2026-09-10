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


P7 = load("analyze_p7_records")
P7REL = load("validate_p7_stage_release")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def make_record(run: Path):
    evidence = run / "p7_evidence.txt"; evidence.write_text("synthetic P7 evidence")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest(); rel = str(evidence.relative_to(ROOT))
    with (HERE / "templates/p7_electrical_safety.csv").open(encoding="utf-8") as handle:
        template = list(csv.DictReader(handle)); fields = list(template[0].keys())
    numeric = {
        "pe_bond_worst": (0.05, 0.005),
        "insulation_resistance": (20.0, 0.5),
        "insulation_test_voltage": (500.0, 0.0),
        "logic_rail_voltage": (24.0, 0.05),
        "logic_startup_current": (0.30, 0.01),
        "hazardous_enable_count_after_reset": (0.0, 0.0),
    }
    bools = {
        "motor_branches_isolated": "YES", "heater_branches_isolated": "YES",
        "logic_power_approval_recorded": "YES", "electronics_disconnected_for_megger": "YES",
        "estop_k0_deenergized": "YES", "lid_k0_deenergized": "YES",
        "service_k0_deenergized": "YES", "thermal_k0_deenergized": "YES",
        "motor_heater_permission_removed_on_open": "YES",
        "automatic_restart_after_power_restore": "NO",
        "fuse_ids_match_schedule": "YES", "point_to_point_wiring_match": "YES",
    }
    rows = []
    for row in template:
        metric = row["metric"]
        if metric in numeric:
            row["value"], row["u95"] = map(str, numeric[metric])
            row["instrument_id"] = "SYN-DMM"; row["calibration_ref"] = "SYN-CAL"
        else:
            row["value"] = bools[metric]; row["u95"] = ""
            row["instrument_id"] = "N/A"; row["calibration_ref"] = "N/A"
        row["measured_at"] = "2026-09-10T18:15:00+09:00"; row["operator"] = "TECH-A"
        row["reviewer"] = "REVIEWER-B"; row["evidence_path"] = rel; row["sha256"] = digest
        rows.append(row)
    path = run / "p7_electrical_safety.csv"; write_csv(path, fields, rows)
    return path


class P7ExecutionTest(unittest.TestCase):
    def test_p7_authenticated_pass_stays_hold(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td)); result = P7.evaluate(path)
            self.assertEqual(result["status"], "NUMERIC_RECORD_CHECK_PASS")
            self.assertFalse(result["stage_p7_pass"])
            self.assertFalse(result["motor_energization_authorized"])
            self.assertFalse(result["heater_energization_authorized"])
            self.assertEqual(set(result["source_bindings_sha256"]), set(P7.SOURCE_FILES))

    def test_p7_rejects_stale_evidence(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            rows[0]["sha256"] = "0" * 64; write_csv(path, fields, rows)
            result = P7.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("evidence hash mismatch", result["reason"])

    def test_p7_rejects_unisolated_motor_branch(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            by = {row["metric"]: row for row in rows}; by["motor_branches_isolated"]["value"] = "NO"
            write_csv(path, fields, rows); result = P7.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("motor_branches_isolated", result["reason"])

    def test_p7_requires_independent_reviewer(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path = make_record(Path(td))
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            rows[0]["reviewer"] = rows[0]["operator"]; write_csv(path, fields, rows)
            result = P7.evaluate(path)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("independent reviewer", result["reason"])

    def test_p7_stage_release_revalidates_record(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); record = make_record(run); result = P7.evaluate(record)
            result_path = run / "p7_result.json"; result_path.write_text(json.dumps(result, indent=2) + "\n")
            release = {
                "stage": "P7", "status": "PASS", "release_scope": "P7_LOGIC_SAFETY_COMPLETE_P8_P9_ENTRY_ONLY",
                "approved_by": "ENGINEER-A", "independent_reviewer": "REVIEWER-B",
                "reviewed_at": "2026-09-10T18:20:00+09:00", "p7_record": record.name,
                "p7_record_sha256": hashlib.sha256(record.read_bytes()).hexdigest(), "p7_result": result_path.name,
                "p7_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
                "p8_motor_entry_review": True, "p9_heater_entry_review": True,
                "motor_energization_authorized": False, "heater_energization_authorized": False, "machine_release": "HOLD",
            }
            release_path = run / "p7_stage_release.json"; release_path.write_text(json.dumps(release, indent=2) + "\n")
            checked = P7REL.validate(release_path)
            self.assertEqual(checked["status"], "P7_STAGE_RELEASE_VALIDATED")
            self.assertTrue(checked["p8_entry_prerequisite"]); self.assertTrue(checked["p9_entry_prerequisite"])
            release["p7_record_sha256"] = "0" * 64; release_path.write_text(json.dumps(release, indent=2) + "\n")
            with self.assertRaises(ValueError): P7REL.validate(release_path)


if __name__ == "__main__":
    unittest.main()
