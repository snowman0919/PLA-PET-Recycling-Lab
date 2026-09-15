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
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P9 = load("analyze_p9_records")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prerequisite_stubs():
    return (
        lambda _: {"status": "P7_STAGE_RELEASE_VALIDATED", "p9_entry_prerequisite": True,
                   "heater_energization_authorized": False, "machine_release": "HOLD"},
        lambda _: {"status": "P8_STAGE_RELEASE_VALIDATED", "p9_entry_prerequisite": True,
                   "heater_energization_authorized": False, "machine_release": "HOLD"},
        lambda _: {"status": "HOT_ZONE_RECEIPT_RECORD_CHECK_PASS", "p9_receipt_prerequisite": True,
                   "power_authorization": False, "machine_release": "HOLD",
                   "checks": {"tape_continuous_service_rating": {"value": 300.0, "pass": True}}},
        lambda: {"status": "THERMAL_CUTOFF_TOPOLOGY_PASS", "machine_release": "HOLD"},
    )


def make_inputs(run: Path):
    evidence = run / "p9_evidence.txt"
    evidence.write_text("synthetic P9 evidence", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    evidence_rel = str(evidence.relative_to(ROOT))
    targets, _ = P9.profile_contract()

    with (HERE / "templates/p9_thermal_profile.csv").open(encoding="utf-8") as handle:
        thermal_rows = list(csv.DictReader(handle))
        thermal_fields = list(thermal_rows[0].keys())
    for row in thermal_rows:
        target = targets[(row["profile"], row["zone"])]
        row["target_c"] = str(target)
        row["measured_mean_c"] = str(target)
        row["u95_c"] = "0.5"
        row["run_peak_c"] = str(target + 2.0)
        row["run_peak_u95_c"] = "0.5"
        row["logger_id"] = "SYN-LOGGER"
        row["calibration_ref"] = "SYN-CAL"
        row["measured_at"] = "2026-09-10T20:50:00+09:00"
        row["operator"] = "TECH-A"
        row["reviewer"] = "REVIEWER-B"
        row["evidence_path"] = evidence_rel
        row["sha256"] = digest
    thermal = run / "p9_thermal.csv"
    write_csv(thermal, thermal_fields, thermal_rows)

    with (HERE / "templates/p9_hot_safety.csv").open(encoding="utf-8") as handle:
        safety_rows = list(csv.DictReader(handle))
        safety_fields = list(safety_rows[0].keys())
    numeric = {
        "cold_axial_travel_reference": (1.8, 0.05),
        "die_fastener_length_min": (42.5, 0.02),
        "die_fastener_length_max": (42.5, 0.02),
        "tcr_hot_cycle_pull_motion_max": (0.05, 0.01),
        "post_cycle_pe_bond_worst": (0.05, 0.005),
        "post_cycle_insulation_resistance": (20.0, 0.5),
        "post_cycle_insulation_test_voltage": (500.0, 0.0),
        "thermal_barrier_tape_edge_lift_max": (0.5, 0.05),
        "thermal_barrier_tape_interface_peak": (120.0, 1.0),
        "thermal_barrier_tape_outer_surface_peak": (70.0, 1.0),
    }
    false_metrics = set(P9.BOOL_FALSE)
    for row in safety_rows:
        metric = row["metric"]
        if metric in numeric:
            row["value"], row["u95"] = map(str, numeric[metric])
            row["instrument_id"] = "SYN-INST"
            row["calibration_ref"] = "SYN-CAL"
        else:
            row["value"] = "NO" if metric in false_metrics else "YES"
            row["instrument_id"] = "N/A"
            row["calibration_ref"] = "N/A"
        row["measured_at"] = "2026-09-10T21:00:00+09:00"
        row["operator"] = "TECH-A"
        row["reviewer"] = "REVIEWER-B"
        row["evidence_path"] = evidence_rel
        row["sha256"] = digest
    safety = run / "p9_safety.csv"
    write_csv(safety, safety_fields, safety_rows)
    p7 = run / "p7_release.json"
    p8 = run / "p8_release.json"
    receipt = run / "p9_receipt.csv"
    p7.write_text("{}\n", encoding="utf-8")
    p8.write_text("{}\n", encoding="utf-8")
    receipt.write_text("placeholder\n", encoding="utf-8")
    return thermal, safety, p7, p8, receipt


def evaluate_with_stubs(inputs, stubs=None):
    p7, p8, receipt, topology = stubs or prerequisite_stubs()
    thermal, safety, p7_file, p8_file, receipt_file = inputs
    return P9.evaluate(
        thermal, safety, p7_file, p8_file, receipt_file,
        p7_checker=p7, p8_checker=p8, receipt_checker=receipt,
        topology_checker=topology,
    )


class P9ExecutionTest(unittest.TestCase):
    def test_valid_record_passes_but_stays_hold(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            result = evaluate_with_stubs(make_inputs(Path(td)))
            self.assertEqual(result["status"], "P9_RECORD_CHECK_PASS")
            self.assertFalse(result["stage_p9_pass"])
            self.assertFalse(result["p10_entry_prerequisite"])
            self.assertFalse(result["material_feed_authorized"])
            self.assertFalse(result["continuing_power_authority"])
            self.assertEqual(result["machine_release"], "HOLD")

    def test_rejects_invalid_p7_prerequisite(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            inputs = make_inputs(Path(td))
            stubs = list(prerequisite_stubs())
            stubs[0] = lambda _: {"status": "NOT_RUN_OR_REJECTED", "p9_entry_prerequisite": False,
                                  "heater_energization_authorized": False, "machine_release": "HOLD"}
            result = evaluate_with_stubs(inputs, tuple(stubs))
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("P7 stage release", result["reason"])

    def test_rejects_peak_overtemperature(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            inputs = list(make_inputs(Path(td)))
            thermal = inputs[0]
            with thermal.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            rows[-1]["run_peak_c"] = "285.0"
            rows[-1]["run_peak_u95_c"] = "0.5"
            write_csv(thermal, fields, rows)
            result = evaluate_with_stubs(tuple(inputs))
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("peak temperature", result["reason"])
    def test_rejects_single_cutoff_failure(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            inputs = list(make_inputs(Path(td)))
            safety = inputs[1]
            with safety.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            by = {row["metric"]: row for row in rows}
            by["tf_die_open_removes_k0_heater_energy"]["value"] = "NO"
            write_csv(safety, fields, rows)
            result = evaluate_with_stubs(tuple(inputs))
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("tf_die_open_removes_k0_heater_energy", result["reason"])

    def test_rejects_thermal_tape_temperature_margin_failure(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            inputs = list(make_inputs(Path(td)))
            safety = inputs[1]
            with safety.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            next(r for r in rows if r["metric"] == "thermal_barrier_tape_interface_peak")["value"] = "275.0"
            write_csv(safety, fields, rows)
            result = evaluate_with_stubs(tuple(inputs))
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("temperature margin", result["reason"])

    def test_rejects_stale_raw_evidence(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            inputs = list(make_inputs(Path(td)))
            thermal = inputs[0]
            with thermal.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle)); fields = list(rows[0].keys())
            rows[0]["sha256"] = "0" * 64
            write_csv(thermal, fields, rows)
            result = evaluate_with_stubs(tuple(inputs))
            self.assertEqual(result["status"], "NOT_RUN_OR_REJECTED")
            self.assertIn("evidence hash mismatch", result["reason"])


if __name__ == "__main__":
    unittest.main()
