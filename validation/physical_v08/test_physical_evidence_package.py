#!/usr/bin/env python3
import csv
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


BUILD = load("build_physical_evidence_package")
CHECK = load("validate_physical_evidence_package")


def fake_validation():
    return {
        "status": "P12_STAGE_RELEASE_VALIDATED",
        "physical_validation_complete_candidate": True,
        "evidence_package_review_allowed": True,
        "continuing_power_authority": False,
        "production_authorized": False,
        "safety_certification": False,
        "machine_release": "HOLD",
    }


def make_graph(run: Path):
    raw = run / "raw.log"; raw.write_text("synthetic evidence\n", encoding="utf-8")
    p12_record = run / "p12.csv"
    with p12_record.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "evidence_path"])
        writer.writeheader(); writer.writerow({"metric": "x", "evidence_path": str(raw.relative_to(ROOT))})
    p11_result = run / "p11_result.json"
    p11_result.write_text(json.dumps({"status": "MATERIAL_RUN_RECORD_CHECK_PASS", "context": {"lot_id": "PET-SYN"}}) + "\n")
    p11_release = run / "p11_stage_release.json"
    p11_release.write_text(json.dumps({"p11_result": p11_result.name}) + "\n")
    p12_result = run / "p12_result.json"
    p12_result.write_text(json.dumps({"status": "P12_RECORD_CHECK_PASS", "p11_release": p11_release.name}) + "\n")
    p12_release = run / "p12_stage_release.json"
    p12_release.write_text(json.dumps({
        "stage": "P12", "status": "PASS", "p11_release": p11_release.name,
        "p12_record": p12_record.name, "p12_result": p12_result.name,
    }) + "\n")
    return p12_release, raw, p12_record, p11_release, p11_result, p12_result


class EvidencePackageTest(unittest.TestCase):
    def setUp(self):
        self.original_load = BUILD.load
        class Validator:
            @staticmethod
            def validate(_): return fake_validation()
        BUILD.load = lambda *_: Validator

    def tearDown(self):
        BUILD.load = self.original_load

    def test_recursive_evidence_bundle_validates(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); root, raw, record, p11, p11_result, p12_result = make_graph(run)
            output = run / "evidence.zip"; built = BUILD.build(root, output)
            checked = CHECK.validate(output)
            self.assertEqual(checked["status"], "PHYSICAL_EVIDENCE_PACKAGE_PASS")
            self.assertFalse(built["production_authorized"])
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                for path in (root, raw, record, p11, p11_result, p12_result):
                    self.assertIn("01_EVIDENCE/" + path.relative_to(ROOT).as_posix(), names)

    def test_manifest_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            run = Path(td); root, *_ = make_graph(run)
            output = run / "evidence.zip"; BUILD.build(root, output)
            tampered = run / "tampered.zip"
            with zipfile.ZipFile(output) as src, zipfile.ZipFile(tampered, "w") as dst:
                for name in src.namelist():
                    data = src.read(name)
                    if name.endswith("raw.log"):
                        data += b"tamper"
                    dst.writestr(name, data)
            with self.assertRaises(ValueError):
                CHECK.validate(tampered)


if __name__ == "__main__":
    unittest.main()
