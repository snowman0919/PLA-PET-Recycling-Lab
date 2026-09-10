#!/usr/bin/env python3
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
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P9REL = load("validate_p9_stage_release")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stub_analyzer(thermal, safety, p7, p8, receipt):
    return {
        "status": "P9_RECORD_CHECK_PASS",
        "stage_p9_pass": False,
        "p10_entry_prerequisite": False,
        "material_feed_authorized": False,
        "continuing_power_authority": False,
        "machine_release": "HOLD",
        "thermal_record_sha256": sha(thermal),
        "safety_record_sha256": sha(safety),
        "source_bindings_sha256": {"synthetic": "1" * 64},
        "prerequisites": {
            "p7_release_sha256": sha(p7),
            "p8_release_sha256": sha(p8),
            "p9_receipt_sha256": sha(receipt),
            "topology_status": "THERMAL_CUTOFF_TOPOLOGY_PASS",
        },
    }


def make_release(run: Path):
    p7 = run / "p7.json"
    p8 = run / "p8.json"
    receipt = run / "receipt.csv"
    thermal = run / "thermal.csv"
    safety = run / "safety.csv"
    for path, text in ((p7, "p7"), (p8, "p8"), (receipt, "receipt"), (thermal, "thermal"), (safety, "safety")):
        path.write_text(text + "\n", encoding="utf-8")
    result = stub_analyzer(thermal, safety, p7, p8, receipt)
    result_path = run / "p9_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    release = {
        "stage": "P9",
        "status": "PASS",
        "release_scope": "P9_EMPTY_HOT_ZONE_COMPLETE_P10_ENTRY_ONLY",
        "approved_by": "ENGINEER-A",
        "independent_reviewer": "REVIEWER-B",
        "reviewed_at": "2026-09-10T21:10:00+09:00",
        "p7_release": p7.name,
        "p7_release_sha256": sha(p7),
        "p8_release": p8.name,
        "p8_release_sha256": sha(p8),
        "p9_receipt": receipt.name,
        "p9_receipt_sha256": sha(receipt),
        "p9_thermal_record": thermal.name,
        "p9_thermal_record_sha256": sha(thermal),
        "p9_safety_record": safety.name,
        "p9_safety_record_sha256": sha(safety),
        "p9_result": result_path.name,
        "p9_result_sha256": sha(result_path),
        "p10_entry_review": True,
        "material_feed_authorized": False,
        "continuing_power_authority": False,
        "machine_release": "HOLD",
    }
    release_path = run / "p9_stage_release.json"
    release_path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return release_path, release


class P9StageReleaseTest(unittest.TestCase):
    def test_valid_release_revalidates_and_stays_hold(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, _ = make_release(Path(td))
            checked = P9REL.validate(path, analyzer=stub_analyzer)
            self.assertEqual(checked["status"], "P9_STAGE_RELEASE_VALIDATED")
            self.assertTrue(checked["p10_entry_prerequisite"])
            self.assertFalse(checked["material_feed_authorized"])
            self.assertFalse(checked["continuing_power_authority"])
            self.assertEqual(checked["machine_release"], "HOLD")

    def test_rejects_result_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["p9_result_sha256"] = "0" * 64
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "p9_result_sha256 mismatch"):
                P9REL.validate(path, analyzer=stub_analyzer)

    def test_rejects_same_reviewer(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["independent_reviewer"] = release["approved_by"]
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "independent reviewer"):
                P9REL.validate(path, analyzer=stub_analyzer)


if __name__ == "__main__":
    unittest.main()
