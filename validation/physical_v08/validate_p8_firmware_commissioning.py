#!/usr/bin/env python3
"""Validate installed GGM calibration/firmware evidence before P8 motor-run review.

This tool is record-only. It never edits firmware, flashes hardware, writes EEPROM,
or grants motor/heater energization.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P3_VALIDATOR = ROOT / "validation/physical_v08/validate_p3_stage_release.py"
PROFILE_BUILDER = ROOT / "validation/physical_v08/build_p3_firmware_profile.py"
APPLIED_HEADER = ROOT / "firmware/ggm_drive_v08/ggm_commissioning.h"
VARIANT_MANIFEST = ROOT / "exports/final/drive_ggm_v08/firmware/manifest.json"
BUILD_MANIFEST = ROOT / "exports/final/firmware/build_manifest.json"
FINAL_HEX = ROOT / "exports/final/firmware/binaries/filament_recycler_atmega2560.hex"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(value: str, label: str) -> Path:
    path = (ROOT / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def timestamp(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing " + field)
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(field + " must include timezone")


def auth_file(path_value: str, digest: str, label: str) -> Path:
    path = repo_file(path_value, label)
    if len(str(digest).strip()) != 64 or sha(path) != str(digest).strip().lower():
        raise ValueError(label + " hash mismatch")
    return path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite(value, field: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + " must be finite")
    return out


def parse_report(path: Path) -> dict[str, str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("GGM_REPORT ")]
    if len(lines) != 1:
        raise ValueError("GGM report log must contain exactly one GGM_REPORT line")
    fields = {}
    for token in lines[0].split()[1:]:
        if "=" not in token:
            raise ValueError("malformed GGM_REPORT token")
        key, value = token.split("=", 1)
        if not key or key in fields:
            raise ValueError("duplicate/malformed GGM_REPORT field")
        fields[key] = value
    required = {
        "profile", "verified", "sh_zero", "sh_scale", "ex_zero", "ex_scale",
        "sh_nm_per_a", "ex_nm_per_a", "sh_idle_a", "ex_idle_a",
        "sh_tach_ppr", "ex_tach_ppr", "cal_record_valid",
    }
    if set(fields) != required:
        raise ValueError("GGM_REPORT field set mismatch")
    return fields


def tach_records(path: Path) -> dict[str, dict]:
    rows = read_csv(path)
    if len(rows) != 2 or {row.get("axis") for row in rows} != {"SH", "EX"}:
        raise ValueError("tach calibration requires exactly SH and EX rows")
    out = {}
    for row in rows:
        axis = row["axis"]
        for field in ("instrument_id", "calibration_ref", "measured_at", "operator", "reviewer", "evidence_path", "sha256"):
            if not str(row.get(field, "")).strip():
                raise ValueError(axis + " tach missing " + field)
        if row["operator"].strip() == row["reviewer"].strip():
            raise ValueError(axis + " tach requires independent reviewer")
        timestamp(row["measured_at"], axis + " tach measured_at")
        auth_file(row["evidence_path"], row["sha256"], axis + " tach evidence")
        revolutions = finite(row["manual_revolutions"], axis + " manual_revolutions")
        pulses = finite(row["observed_pulses"], axis + " observed_pulses")
        recorded = finite(row["calculated_ppr"], axis + " calculated_ppr")
        if revolutions < 10 or pulses <= 0 or not pulses.is_integer():
            raise ValueError(axis + " tach requires >=10 revolutions and integer pulse count")
        calculated = pulses / revolutions
        if abs(recorded - calculated) > 1e-9:
            raise ValueError(axis + " tach PPR arithmetic mismatch")
        nearest = round(calculated)
        if nearest <= 0 or abs(calculated - nearest) > 1e-6:
            raise ValueError(axis + " tach PPR must resolve to a positive integer")
        out[axis] = {"manual_revolutions": revolutions, "observed_pulses": int(pulses), "ppr": float(nearest)}
    return out


def installation(path: Path) -> dict:
    rows = read_csv(path)
    if len(rows) != 1 or rows[0].get("record_id") != "P8-FW-01":
        raise ValueError("firmware installation record must contain P8-FW-01 only")
    row = rows[0]
    for field in ("flashed_hex_readback_path", "flashed_hex_readback_sha256", "ggm_report_log_path",
                  "ggm_report_log_sha256", "measured_at", "operator", "reviewer"):
        if not str(row.get(field, "")).strip():
            raise ValueError("firmware installation missing " + field)
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError("firmware installation requires independent reviewer")
    timestamp(row["measured_at"], "firmware installation measured_at")
    flash = auth_file(row["flashed_hex_readback_path"], row["flashed_hex_readback_sha256"], "flash readback")
    log = auth_file(row["ggm_report_log_path"], row["ggm_report_log_sha256"], "GGM report log")
    return {"flash_path": flash, "report_path": log, "report": parse_report(log)}

def close(a, b, tol=1e-6) -> bool:
    return math.isclose(float(a), float(b), rel_tol=1e-7, abs_tol=tol)


def validate(p3_release: Path, profile_dir: Path, tach_path: Path, install_path: Path, *,
             applied_header: Path = APPLIED_HEADER, variant_manifest: Path = VARIANT_MANIFEST,
             build_manifest: Path = BUILD_MANIFEST, final_hex: Path = FINAL_HEX,
             p3_validator=None) -> dict:
    p3_release = p3_release.resolve(); profile_dir = profile_dir.resolve()
    if not p3_release.is_relative_to(ROOT) or not p3_release.is_file():
        raise ValueError("P3 release must be an existing repository file")
    if not profile_dir.is_relative_to(ROOT) or not profile_dir.is_dir():
        raise ValueError("P3 firmware profile directory must exist inside repository")
    authority = p3_validator or load(P3_VALIDATOR, "ppr_p8_p3_release")
    stage = authority.validate(p3_release) if p3_validator is None else authority(p3_release)
    if stage.get("status") != "P3_STAGE_RELEASE_VALIDATED":
        raise ValueError("P3 stage release is not validated")
    manifest_path = profile_dir / "manifest.json"
    candidate_header = profile_dir / "ggm_commissioning_generated.h"
    eeprom_command = profile_dir / "shredder_eeprom_command.txt"
    for path, label in ((manifest_path, "profile manifest"), (candidate_header, "candidate header"),
                        (eeprom_command, "EEPROM command"), (applied_header, "applied commissioning header"),
                        (variant_manifest, "variant manifest"), (build_manifest, "build manifest"),
                        (final_hex, "final HEX")):
        if not path.is_file():
            raise ValueError(label + " missing")
    profile = json.loads(manifest_path.read_text(encoding="utf-8"))
    if profile.get("status") != "REVIEW_CANDIDATE_ONLY" or profile.get("candidate_only") is not True:
        raise ValueError("P3 firmware profile is not a review candidate")
    for field in ("source_firmware_modified", "firmware_built", "hardware_flashed", "eeprom_command_applied", "p8_entry_prerequisite"):
        if profile.get(field) is not False:
            raise ValueError("P3 profile safety invariant drift: " + field)
    if profile.get("machine_release") != "HOLD":
        raise ValueError("P3 profile machine release must remain HOLD")
    if profile.get("p3_release_sha256") != sha(p3_release):
        raise ValueError("P3 profile release binding mismatch")
    if profile.get("profile_builder_sha256") != sha(PROFILE_BUILDER):
        raise ValueError("P3 firmware profile builder drift")
    outputs = profile.get("outputs", {})
    if outputs.get(candidate_header.name) != sha(candidate_header) or outputs.get(eeprom_command.name) != sha(eeprom_command):
        raise ValueError("P3 firmware profile output hash mismatch")
    if candidate_header.read_bytes() != applied_header.read_bytes():
        raise ValueError("applied commissioning header differs from reviewed P3 candidate")

    variant = json.loads(variant_manifest.read_text(encoding="utf-8"))
    build = json.loads(build_manifest.read_text(encoding="utf-8"))
    applied_sha = sha(applied_header)
    if variant.get("commissioning_header_sha256") != applied_sha:
        raise ValueError("variant manifest commissioning-header binding mismatch")
    if variant.get("source_payload", {}).get("src/ggm_commissioning.h") != applied_sha:
        raise ValueError("variant payload commissioning-header binding mismatch")
    if build.get("source_files", {}).get("src/ggm_commissioning.h") != applied_sha:
        raise ValueError("final build commissioning-header binding mismatch")
    if build.get("variant_manifest_sha256") != sha(variant_manifest):
        raise ValueError("final build variant-manifest binding mismatch")
    if build.get("variant_builder_sha256") != variant.get("builder_sha256"):
        raise ValueError("variant builder binding mismatch")
    clean = build.get("clean_rebuild", {})
    final_digest = sha(final_hex)
    if clean.get("status") != "PASS" or clean.get("original_source_hex_sha256") != final_digest or clean.get("released_source_hex_sha256") != final_digest:
        raise ValueError("final firmware clean rebuild is not bound to final HEX")
    if build.get("binary", {}).get("sha256") != final_digest or build.get("binary_sha256") != final_digest:
        raise ValueError("final firmware binary hash mismatch")

    tach = tach_records(tach_path.resolve())
    install = installation(install_path.resolve())
    if sha(install["flash_path"]) != final_digest:
        raise ValueError("installed flash readback differs from reviewed final HEX")
    report = install["report"]
    calibration = profile.get("calibration", {})
    if report["profile"] != profile.get("profile_id") or report["verified"] != "1" or report["cal_record_valid"] != "1":
        raise ValueError("GGM_REPORT profile/verification state mismatch")
    expected = {
        "sh_zero": calibration["SH"]["zero_adc"], "sh_scale": calibration["SH"]["amps_per_adc"],
        "ex_zero": calibration["EX"]["zero_adc"], "ex_scale": calibration["EX"]["amps_per_adc"],
        "sh_nm_per_a": calibration["SH"]["gearbox_nm_per_amp"], "ex_nm_per_a": calibration["EX"]["gearbox_nm_per_amp"],
        "sh_idle_a": calibration["SH"]["no_load_current_a"], "ex_idle_a": calibration["EX"]["no_load_current_a"],
    }
    for field, value in expected.items():
        if not close(report[field], value):
            raise ValueError("GGM_REPORT calibration mismatch: " + field)
    if not close(report["sh_tach_ppr"], tach["SH"]["ppr"]) or not close(report["ex_tach_ppr"], tach["EX"]["ppr"]):
        raise ValueError("GGM_REPORT tach PPR differs from manual pulse/revolution calibration")
    command = eeprom_command.read_text(encoding="utf-8").strip().split()
    if len(command) != 4 or command[:2] != ["CAL", "CURRENT"]:
        raise ValueError("reviewed shredder EEPROM command malformed")
    if not close(command[2], calibration["SH"]["zero_adc"]) or not close(command[3], calibration["SH"]["amps_per_adc"]):
        raise ValueError("reviewed shredder EEPROM command differs from P3 calibration")

    return {
        "status": "FIRMWARE_COMMISSIONING_RECORD_CHECK_PASS",
        "record_check_only": True,
        "firmware_prerequisite_for_p8": True,
        "motor_energization_authorized": False,
        "heater_energization_authorized": False,
        "machine_release": "HOLD",
        "p3_release_sha256": sha(p3_release),
        "profile_manifest_sha256": sha(manifest_path),
        "commissioning_header_sha256": applied_sha,
        "variant_manifest_sha256": sha(variant_manifest),
        "build_manifest_sha256": sha(build_manifest),
        "final_hex_sha256": final_digest,
        "flash_readback_sha256": sha(install["flash_path"]),
        "ggm_report_log_sha256": sha(install["report_path"]),
        "tach_calibration_sha256": sha(tach_path.resolve()),
        "profile_id": profile["profile_id"],
        "tach_ppr": {axis: tach[axis]["ppr"] for axis in ("SH", "EX")},
        "note": "Calibration/firmware installation evidence is coherent. P8 motor-power approval and P3/P6/P7 stage prerequisites remain separate.",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p3-release", type=Path, required=True)
    ap.add_argument("--profile-dir", type=Path, required=True)
    ap.add_argument("--tach-calibration", type=Path, required=True)
    ap.add_argument("--installation", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = validate(args.p3_release, args.profile_dir, args.tach_calibration, args.installation)
        code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {
            "status": "NOT_RUN_OR_REJECTED", "record_check_only": True,
            "firmware_prerequisite_for_p8": False, "motor_energization_authorized": False,
            "heater_energization_authorized": False, "machine_release": "HOLD",
            "reason": str(exc),
        }
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
