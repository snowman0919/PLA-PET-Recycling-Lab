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
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


RUN = load("analyze_material_run")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def p11_stub(_):
    return {"status": "P10_STAGE_RELEASE_VALIDATED", "p11_entry_prerequisite": True,
            "material_feed_authorized": False, "machine_release": "HOLD"}


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def make_p11(run: Path):
    evidence = run / "pet_samples.log"; evidence.write_text("synthetic PET samples\n", encoding="utf-8")
    drying = run / "pet_drying.log"; drying.write_text("synthetic dry PET lot\n", encoding="utf-8")
    approval = run / "pet_feed_approval.log"; approval.write_text("synthetic bounded P11 approval\n", encoding="utf-8")
    p10 = run / "p10_release.json"; p10.write_text("synthetic P10 release\n", encoding="utf-8")
    with (HERE / "templates/p10_p11_material_run.csv").open(encoding="utf-8") as handle:
        fields = next(csv.reader(handle))
    targets = RUN.profile_targets()["PET"]
    base = datetime.datetime(2026, 9, 10, 22, 35, tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
    rows = []
    for i in range(20):
        row = {field: "" for field in fields}
        row.update({"sample_id": f"PET{i:02d}", "material": "PET", "lot_id": "PET-SYN-01",
                    "drying_record": str(drying.relative_to(ROOT)), "drying_record_sha256": sha(drying),
                    "material_feed_approval_path": str(approval.relative_to(ROOT)),
                    "material_feed_approval_sha256": sha(approval),
                    "material_feed_approval_scope": "P11_BOUNDED_PET_RUN"})
        row.update({"elapsed_s": str(i * 10),
                    "measured_at": (base + datetime.timedelta(seconds=i * 10)).isoformat(),
                    "stable_candidate": "YES", "screw_rpm": "9.0",
                    "gearbox_torque_nm": "4.5", "gearbox_torque_u95_nm": "0.2",
                    "motor_current_a": "3.4", "motor_current_u95_a": "0.1",
                    "zone1_c": str(targets[0]), "zone2_c": str(targets[1]),
                    "zone3_c": str(targets[2]), "die_c": str(targets[3]),
                    "temperature_u95_c": "0.5", "diameter_x_mm": "1.75",
                    "diameter_y_mm": "1.75", "diameter_u95_mm": "0.01",
                    "puller_rpm": "20", "spool_rpm": "12", "cumulative_mass_g": str(i)})
        row.update({key: "NO" for key in ("leak", "pressure_symptom", "guard_contact", "torque_trip")})
        row.update({"logger_id": "LOG-1", "logger_calibration_ref": "CAL-T",
                    "diameter_gauge_id": "GAUGE-1", "diameter_calibration_ref": "CAL-D",
                    "torque_calibration_ref": "CAL-TQ", "current_calibration_ref": "CAL-I",
                    "operator": "TECH-A", "reviewer": "REVIEWER-B",
                    "raw_evidence_path": str(evidence.relative_to(ROOT)),
                    "raw_evidence_sha256": sha(evidence)})
        rows.append(row)
    record = run / "p11.csv"; write_csv(record, fields, rows)
    return record, {"p10": p10}


class P11ExecutionTest(unittest.TestCase):
    def test_p11_pet_pass_is_review_only(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p11(Path(td))
            result = RUN.evaluate(record, "P11", releases, checkers={"p10": p11_stub})
            self.assertEqual(result["status"], "MATERIAL_RUN_RECORD_CHECK_PASS")
            self.assertEqual(result["stage"], "P11")
            self.assertEqual(result["material"], "PET")
            self.assertFalse(result["next_stage_entry_prerequisite"])
            self.assertFalse(result["material_feed_authorized"])

    def test_p11_rejects_pla_material(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p11(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            for row in rows: row["material"] = "PLA"
            write_csv(record, fields, rows)
            result = RUN.evaluate(record, "P11", releases, checkers={"p10": p11_stub})
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("material does not match", result["reason"])

    def test_p11_rejects_missing_p10_release(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, _ = make_p11(Path(td))
            result = RUN.evaluate(record, "P11", {"p10": None}, checkers={"p10": p11_stub})
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("P10 stage release", result["reason"])

    def test_p11_rejects_wrong_approval_scope(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            record, releases = make_p11(Path(td))
            with record.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0])
            for row in rows: row["material_feed_approval_scope"] = "P10_BOUNDED_PLA_RUN"
            write_csv(record, fields, rows)
            result = RUN.evaluate(record, "P11", releases, checkers={"p10": p11_stub})
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("approval scope mismatch", result["reason"])


if __name__ == "__main__":
    unittest.main()
