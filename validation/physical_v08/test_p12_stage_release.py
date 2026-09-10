#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


P12 = load("analyze_p12_records")
REL = load("validate_p12_stage_release")
TEST = load("test_p12_execution")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyzer_stub(record, p11):
    return P12.evaluate(record, p11, p11_checker=TEST.p11_stub)


def make_release(run: Path):
    record, p11 = TEST.make_p12(run)
    result = analyzer_stub(record, p11)
    result_path = run / "p12_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    release = {
        "stage": "P12", "status": "PASS",
        "release_scope": "P12_PHYSICAL_VALIDATION_EVIDENCE_REVIEW_CANDIDATE_ONLY",
        "approved_by": "ENGINEER-A", "independent_reviewer": "REVIEWER-B",
        "reviewed_at": "2026-09-10T23:00:00+09:00",
        "p11_release": p11.name, "p11_release_sha256": sha(p11),
        "p12_record": record.name, "p12_record_sha256": sha(record),
        "p12_result": result_path.name, "p12_result_sha256": sha(result_path),
        "physical_validation_complete_candidate": True,
        "evidence_package_review_allowed": True,
        "continuing_power_authority": False, "production_authorized": False,
        "safety_certification": False, "machine_release": "HOLD",
    }
    path = run / "p12_stage_release.json"
    path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return path, release


class P12StageReleaseTest(unittest.TestCase):
    def test_release_marks_review_candidate_only(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, _ = make_release(Path(td))
            result = REL.validate(path, analyzer=analyzer_stub)
            self.assertEqual(result["status"], "P12_STAGE_RELEASE_VALIDATED")
            self.assertTrue(result["physical_validation_complete_candidate"])
            self.assertTrue(result["evidence_package_review_allowed"])
            self.assertFalse(result["continuing_power_authority"])
            self.assertFalse(result["production_authorized"])
            self.assertFalse(result["safety_certification"])
            self.assertEqual(result["machine_release"], "HOLD")

    def test_release_rejects_record_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["p12_record_sha256"] = "0" * 64
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "p12_record_sha256 mismatch"):
                REL.validate(path, analyzer=analyzer_stub)

    def test_release_rejects_production_authority(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["production_authorized"] = True
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "production_authorized false"):
                REL.validate(path, analyzer=analyzer_stub)


if __name__ == "__main__":
    unittest.main()
