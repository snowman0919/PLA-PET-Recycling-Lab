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


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


V = load(HERE / "validate_p8_firmware_commissioning.py", "p8_fw_validator")
B = load(HERE / "build_p3_firmware_profile.py", "p8_profile_builder")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

def make_fixture(run: Path):
    p3_release = run / "p3_release.json"; p3_release.write_text('{"stage":"P3"}\n')
    profile_dir = run / "profile"; profile_dir.mkdir()
    values = {
        "SH": {"amps_per_adc": .01, "zero_adc": 100.0, "gearbox_nm_per_amp": 2.0,
               "no_load_current_a": .5, "holdout_error_bound_nm": .1},
        "EX": {"amps_per_adc": .02, "zero_adc": 200.0, "gearbox_nm_per_amp": 1.5,
               "no_load_current_a": .4, "holdout_error_bound_nm": .1},
    }
    profile_id = "GGM-P3-SYNTHETIC"
    header = profile_dir / "ggm_commissioning_generated.h"
    header.write_text(B.header_text(profile_id, values))
    command = profile_dir / "shredder_eeprom_command.txt"
    command.write_text("CAL CURRENT 100.000000000 0.010000000\n")
    profile = {
        "status": "REVIEW_CANDIDATE_ONLY", "candidate_only": True,
        "source_firmware_modified": False, "firmware_built": False,
        "hardware_flashed": False, "eeprom_command_applied": False,
        "p8_entry_prerequisite": False, "machine_release": "HOLD",
        "profile_id": profile_id, "p3_release_sha256": digest(p3_release),
        "profile_builder_sha256": digest(HERE / "build_p3_firmware_profile.py"),
        "calibration": values,
        "outputs": {header.name: digest(header), command.name: digest(command)},
    }
    (profile_dir / "manifest.json").write_text(json.dumps(profile, indent=2) + "\n")
    applied = run / "ggm_commissioning.h"; applied.write_bytes(header.read_bytes())
    variant_header = run / "variant_ggm_commissioning.h"; variant_header.write_bytes(header.read_bytes())
    released_header = run / "released_ggm_commissioning.h"; released_header.write_bytes(header.read_bytes())
    final_hex = run / "final.hex"; final_hex.write_text(":00000001FF\n")
    flash_readback = run / "flash_readback.hex"; flash_readback.write_bytes(final_hex.read_bytes())
    variant = {
        "commissioning_header_sha256": digest(applied),
        "source_payload": {"src/ggm_commissioning.h": digest(applied)},
        "builder_sha256": digest(V.VARIANT_BUILDER),
    }
    variant_path = run / "variant_manifest.json"; variant_path.write_text(json.dumps(variant, indent=2) + "\n")
    build = {
        "source_files": {"src/ggm_commissioning.h": digest(applied)},
        "variant_manifest_sha256": digest(variant_path), "variant_builder_sha256": digest(V.VARIANT_BUILDER),
        "clean_rebuild": {"status": "PASS", "original_source_hex_sha256": digest(final_hex),
                          "released_source_hex_sha256": digest(final_hex)},
        "binary": {"sha256": digest(final_hex)}, "binary_sha256": digest(final_hex),
    }
    build_path = run / "build_manifest.json"; build_path.write_text(json.dumps(build, indent=2) + "\n")
    tach_evidence = run / "tach_evidence.txt"; tach_evidence.write_text("synthetic manual rotation evidence")
    tach_rows = []
    for axis, revs, pulses in (("SH", 10, 60), ("EX", 10, 120)):
        tach_rows.append({"axis": axis, "manual_revolutions": revs, "observed_pulses": pulses,
                          "calculated_ppr": pulses / revs, "instrument_id": "SYN-COUNTER",
                          "calibration_ref": "SYN-CAL", "measured_at": "2026-09-10T18:40:00+09:00",
                          "operator": "TECH-A", "reviewer": "REVIEWER-B",
                          "evidence_path": str(tach_evidence.relative_to(ROOT)), "sha256": digest(tach_evidence), "notes": ""})
    tach_path = run / "p8_tach_calibration.csv"
    with (HERE / "templates/p8_tach_calibration.csv").open(encoding="utf-8") as handle:
        fields = list(csv.DictReader(handle).fieldnames)
    write_csv(tach_path, fields, tach_rows)
    report = run / "ggm_report.log"
    report.write_text(
        "GGM_REPORT profile=GGM-P3-SYNTHETIC verified=1 sh_zero=100.000000000 sh_scale=0.010000000 "
        "ex_zero=200.000000000 ex_scale=0.020000000 sh_nm_per_a=2.000000000 ex_nm_per_a=1.500000000 "
        "sh_idle_a=0.500000000 ex_idle_a=0.400000000 sh_tach_ppr=6.000000 ex_tach_ppr=12.000000 cal_record_valid=1\n"
    )
    install_path = run / "p8_firmware_installation.csv"
    with (HERE / "templates/p8_firmware_installation.csv").open(encoding="utf-8") as handle:
        install_fields = list(csv.DictReader(handle).fieldnames)
    install = [{
        "record_id": "P8-FW-01", "flashed_hex_readback_path": str(flash_readback.relative_to(ROOT)),
        "flashed_hex_readback_sha256": digest(flash_readback), "ggm_report_log_path": str(report.relative_to(ROOT)),
        "ggm_report_log_sha256": digest(report), "measured_at": "2026-09-10T18:45:00+09:00",
        "operator": "TECH-A", "reviewer": "REVIEWER-B", "notes": "synthetic only",
    }]
    write_csv(install_path, install_fields, install)
    return {
        "p3_release": p3_release, "profile_dir": profile_dir, "tach": tach_path, "install": install_path,
        "applied": applied, "variant_header": variant_header, "released_header": released_header,
        "variant": variant_path, "build": build_path, "hex": final_hex,
        "report": report, "flash": flash_readback,
    }


def run_validate(fx):
    return V.validate(
        fx["p3_release"], fx["profile_dir"], fx["tach"], fx["install"],
        applied_header=fx["applied"], variant_header=fx["variant_header"],
        released_header=fx["released_header"], variant_builder=V.VARIANT_BUILDER,
        variant_manifest=fx["variant"], build_manifest=fx["build"], final_hex=fx["hex"],
        p3_validator=lambda _: {"status": "P3_STAGE_RELEASE_VALIDATED"},
    )


class P8FirmwareCommissioningTest(unittest.TestCase):
    def test_coherent_installation_passes_but_does_not_authorize_motor(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            fx = make_fixture(Path(td)); result = run_validate(fx)
            self.assertEqual(result["status"], "FIRMWARE_COMMISSIONING_RECORD_CHECK_PASS")
            self.assertTrue(result["firmware_prerequisite_for_p8"])
            self.assertFalse(result["motor_energization_authorized"])
            self.assertFalse(result["heater_energization_authorized"])
            self.assertEqual(result["tach_ppr"], {"SH": 6.0, "EX": 12.0})

    def test_candidate_header_drift_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            fx = make_fixture(Path(td)); fx["applied"].write_text(fx["applied"].read_text() + "// drift\n")
            with self.assertRaisesRegex(ValueError, "applied commissioning header differs"):
                run_validate(fx)

    def test_flash_readback_drift_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            fx = make_fixture(Path(td)); fx["flash"].write_text(":0100000000FF\n")
            rows = V.read_csv(fx["install"]); rows[0]["flashed_hex_readback_sha256"] = digest(fx["flash"])
            write_csv(fx["install"], rows[0].keys(), rows)
            with self.assertRaisesRegex(ValueError, "installed flash readback differs"):
                run_validate(fx)

    def test_tach_readback_mismatch_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            fx = make_fixture(Path(td)); fx["report"].write_text(fx["report"].read_text().replace("sh_tach_ppr=6.000000", "sh_tach_ppr=7.000000"))
            rows = V.read_csv(fx["install"]); rows[0]["ggm_report_log_sha256"] = digest(fx["report"])
            write_csv(fx["install"], rows[0].keys(), rows)
            with self.assertRaisesRegex(ValueError, "tach PPR differs"):
                run_validate(fx)


if __name__ == "__main__":
    unittest.main()
