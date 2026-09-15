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


RUN = load("analyze_material_run")
REL = load("validate_p11_stage_release")
TEST = load("test_p11_execution")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyzer_stub(record, stage, releases):
    return RUN.evaluate(record, stage, releases, checkers={"p10": TEST.p11_stub})


def make_release(run: Path):
    record, releases = TEST.make_p11(run)
    result = analyzer_stub(record, "P11", releases)
    result_path = run / "p11_result.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    p10 = releases["p10"]
    release = {
        "stage": "P11", "status": "PASS",
        "release_scope": "P11_PET_LOW_FEED_COMPLETE_P12_ENTRY_ONLY",
        "approved_by": "ENGINEER-A", "independent_reviewer": "REVIEWER-B",
        "reviewed_at": "2026-09-10T22:40:00+09:00",
        "p10_release": p10.name, "p10_release_sha256": sha(p10),
        "p11_record": record.name, "p11_record_sha256": sha(record),
        "p11_result": result_path.name, "p11_result_sha256": sha(result_path),
        "p12_entry_review": True,
        "material_feed_authorized": False, "continuing_power_authority": False,
        "machine_release": "HOLD",
    }
    path = run / "p11_stage_release.json"
    path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    return path, release


class P11StageReleaseTest(unittest.TestCase):
    def test_release_validates_but_only_unlocks_review(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, _ = make_release(Path(td))
            result = REL.validate(path, analyzer=analyzer_stub)
            self.assertEqual(result["status"], "P11_STAGE_RELEASE_VALIDATED")
            self.assertTrue(result["p12_entry_prerequisite"])
            self.assertFalse(result["material_feed_authorized"])
            self.assertFalse(result["continuing_power_authority"])
            self.assertEqual(result["machine_release"], "HOLD")

    def test_release_rejects_result_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["p11_result_sha256"] = "0" * 64
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "p11_result_sha256 mismatch"):
                REL.validate(path, analyzer=analyzer_stub)

    def test_release_rejects_feed_authority(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path, release = make_release(Path(td))
            release["material_feed_authorized"] = True
            path.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not authorize further material feed"):
                REL.validate(path, analyzer=analyzer_stub)


if __name__ == "__main__":
    unittest.main()
