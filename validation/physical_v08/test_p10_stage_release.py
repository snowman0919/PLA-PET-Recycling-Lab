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
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


RUN = load("analyze_material_run")
REL = load("validate_p10_stage_release")
TEST_RUN = load("test_material_run")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyzer_stub(record, stage, releases):
    return RUN.evaluate(record, stage, releases, checkers=TEST_RUN.p10_stubs())


def make_release(run: Path):
    record, releases = TEST_RUN.make_p10(run)
    result = analyzer_stub(record, "P10", {**releases, "p10": None})
    result_path = run / "p10_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    release = {
        "stage": "P10", "status": "PASS",
        "release_scope": "P10_PLA_LOW_FEED_COMPLETE_P11_ENTRY_ONLY",
        "approved_by": "ENGINEER-A", "independent_reviewer": "REVIEWER-B",
        "reviewed_at": "2026-09-10T22:30:00+09:00",
        "material_feed_authorized": False, "continuing_power_authority": False,
        "machine_release": "HOLD",
    }
    for key in ("p4", "p6", "p8", "p9"):
        release[f"{key}_release"] = releases[key].name
        release[f"{key}_release_sha256"] = sha(releases[key])
    release.update({
        "p10_record": record.name, "p10_record_sha256": sha(record),
        "p10_result": result_path.name, "p10_result_sha256": sha(result_path),
        "p11_entry_review": True,
    })
    path = run / "p10_stage_release.json"
    path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return path, release


class P10StageReleaseTest(unittest.TestCase):
    def test_release_validates_but_does_not_authorize_feed(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, _ = make_release(Path(td))
            result = REL.validate(path, analyzer=analyzer_stub)
            self.assertEqual(result["status"], "P10_STAGE_RELEASE_VALIDATED")
            self.assertTrue(result["p11_entry_prerequisite"])
            self.assertFalse(result["material_feed_authorized"])
            self.assertFalse(result["continuing_power_authority"])
            self.assertEqual(result["machine_release"], "HOLD")

    def test_release_rejects_record_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["p10_record_sha256"] = "0" * 64
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "p10_record_sha256 mismatch"):
                REL.validate(path, analyzer=analyzer_stub)

    def test_release_rejects_authorization_escalation(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["material_feed_authorized"] = True
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not authorize further material feed"):
                REL.validate(path, analyzer=analyzer_stub)


if __name__ == "__main__":
    unittest.main()
