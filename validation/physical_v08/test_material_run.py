#!/usr/bin/env python3
import csv
import datetime
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RUN = load("analyze_material_run")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def p10_stubs():
    return {
        "p4": lambda _: {"status": "P4_STAGE_RELEASE_VALIDATED", "machine_release": "HOLD"},
        "p6": lambda _: {"status": "P6_STAGE_RELEASE_VALIDATED", "machine_release": "HOLD"},
        "p8": lambda _: {"status": "P8_STAGE_RELEASE_VALIDATED", "machine_release": "HOLD"},
        "p9": lambda _: {"status": "P9_STAGE_RELEASE_VALIDATED", "p10_entry_prerequisite": True,
                          "material_feed_authorized": False, "machine_release": "HOLD"},
    }


def make_p10(run: Path):
    evidence = run / "samples.log"
    drying = run / "drying.log"
    approval = run / "feed_approval.log"
    evidence.write_text("synthetic samples\n", encoding="utf-8")
    drying.write_text("synthetic dry PLA lot\n", encoding="utf-8")
    approval.write_text("synthetic bounded P10 approval\n", encoding="utf-8")
    releases = {}
    for key in ("p4", "p6", "p8", "p9"):
        path = run / f"{key}.json"; path.write_text(key + "\n", encoding="utf-8"); releases[key] = path
    with (HERE / "templates/p10_p11_material_run.csv").open(encoding="utf-8") as handle:
        fields = next(csv.reader(handle))
    targets = RUN.profile_targets()["PLA"]
    base = datetime.datetime(2026, 9, 10, 21, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
    rows = []
    for i in range(20):
        row = {field: "" for field in fields}
        row.update({
            "sample_id": f"S{i:02d}", "material": "PLA", "lot_id": "PLA-SYN-01",
            "drying_record": str(drying.relative_to(ROOT)), "drying_record_sha256": sha(drying),
            "material_feed_approval_path": str(approval.relative_to(ROOT)),
            "material_feed_approval_sha256": sha(approval),
            "material_feed_approval_scope": "P10_BOUNDED_PLA_RUN",
            "elapsed_s": str(i * 10), "measured_at": (base + datetime.timedelta(seconds=i * 10)).isoformat(),
            "stable_candidate": "YES", "screw_rpm": "9.0", "gearbox_torque_nm": "4.0",
            "gearbox_torque_u95_nm": "0.2", "motor_current_a": "3.0", "motor_current_u95_a": "0.1",
            "zone1_c": str(targets[0]), "zone2_c": str(targets[1]), "zone3_c": str(targets[2]),
            "die_c": str(targets[3]), "temperature_u95_c": "0.5", "diameter_x_mm": "1.75",
            "diameter_y_mm": "1.75", "diameter_u95_mm": "0.01", "puller_rpm": "20",
            "spool_rpm": "12", "cumulative_mass_g": str(i),
        })
        row.update({key: "NO" for key in ("leak", "pressure_symptom", "guard_contact", "torque_trip")})
        row.update({"logger_id": "LOG-1", "logger_calibration_ref": "CAL-T",
                    "diameter_gauge_id": "GAUGE-1", "diameter_calibration_ref": "CAL-D",
                    "torque_calibration_ref": "CAL-TQ", "current_calibration_ref": "CAL-I",
                    "operator": "TECH-A", "reviewer": "REVIEWER-B",
                    "raw_evidence_path": str(evidence.relative_to(ROOT)), "raw_evidence_sha256": sha(evidence)})
        rows.append(row)
    record = run / "p10.csv"
    write_csv(record, fields, rows)
    return record, releases


class MaterialRunTest(unittest.TestCase):
    def test_p10_pass_is_review_only(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p10(Path(td))
            result = RUN.evaluate(record, "P10", releases, checkers=p10_stubs())
            self.assertEqual(result["status"], "MATERIAL_RUN_RECORD_CHECK_PASS")
            self.assertEqual(result["stage"], "P10")
            self.assertFalse(result["stage_pass"])
            self.assertFalse(result["next_stage_entry_prerequisite"])
            self.assertFalse(result["material_feed_authorized"])
            self.assertLess(result["max_torque_plus_u95_nm"], 8.0)
            self.assertLessEqual(result["max_current_plus_u95_a"], 6.0)

    def test_p10_rejects_current_ceiling(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p10(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            rows[5]["motor_current_a"] = "6.0"; rows[5]["motor_current_u95_a"] = "0.1"
            write_csv(record, fields, rows)
            result = RUN.evaluate(record, "P10", releases, checkers=p10_stubs())
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("no 20-consecutive", result["reason"])

    def test_p10_rejects_torque_limit(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p10(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            rows[7]["gearbox_torque_nm"] = "7.9"; rows[7]["gearbox_torque_u95_nm"] = "0.2"
            write_csv(record, fields, rows)
            result = RUN.evaluate(record, "P10", releases, checkers=p10_stubs())
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("no 20-consecutive", result["reason"])

    def test_p10_rejects_drying_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p10(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            for row in rows: row["drying_record_sha256"] = "0" * 64
            write_csv(record, fields, rows)
            result = RUN.evaluate(record, "P10", releases, checkers=p10_stubs())
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("drying record hash mismatch", result["reason"])

    def test_p10_rejects_invalid_p9_release(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p10(Path(td)); stubs = p10_stubs()
            stubs["p9"] = lambda _: {"status": "NOT_RUN_OR_REJECTED", "machine_release": "HOLD"}
            result = RUN.evaluate(record, "P10", releases, checkers=stubs)
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("P9 stage release", result["reason"])


if __name__ == "__main__":
    unittest.main()
