#!/usr/bin/env python3
"""Create a review-only GGM commissioning profile from an authenticated P3 release.

The output is never flashed and this tool never edits firmware sources. A later
review/application gate must bind the approved profile to a rebuilt HEX and EEPROM readback.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P3_VALIDATOR = ROOT / "validation/physical_v08/validate_p3_stage_release.py"
INSPECTION = ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def resolve_from_release(value: str, release_path: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path

def header_text(profile_id: str, values: dict) -> str:
    sh, ex = values["SH"], values["EX"]
    return f'''#pragma once
// REVIEW CANDIDATE generated from authenticated P3 evidence. Do not copy blindly.
namespace GgmCommissioning {{
constexpr const char* PROFILE = "{profile_id}";
constexpr bool RECEIPT_LIMITER_CURRENT_AND_WIRING_VERIFIED = true;
constexpr float SH_GEARBOX_NM_PER_AMP = {sh['gearbox_nm_per_amp']:.9f}f;
constexpr float EX_GEARBOX_NM_PER_AMP = {ex['gearbox_nm_per_amp']:.9f}f;
constexpr float SH_NO_LOAD_CURRENT_A = {sh['no_load_current_a']:.9f}f;
constexpr float EX_NO_LOAD_CURRENT_A = {ex['no_load_current_a']:.9f}f;
constexpr float EX_CURRENT_ZERO_ADC = {ex['zero_adc']:.9f}f;
constexpr float EX_CURRENT_AMPS_PER_COUNT = {ex['amps_per_adc']:.9f}f;
}}
'''


def generate(release_path: Path, output_dir: Path) -> dict:
    release_path = release_path.resolve(); output_dir = output_dir.resolve()
    if not release_path.is_relative_to(ROOT) or not release_path.is_file():
        raise ValueError("P3 release must be an existing repository file")
    if not output_dir.is_relative_to(ROOT):
        raise ValueError("output directory must stay inside repository")
    validated = load(P3_VALIDATOR, "ppr_profile_p3_release").validate(release_path)
    if validated.get("status") != "P3_STAGE_RELEASE_VALIDATED":
        raise ValueError("P3 stage release is not validated")
    release = json.loads(release_path.read_text(encoding="utf-8"))
    packet_path = resolve_from_release(release["inspection_packet"], release_path, "P3 inspection packet")
    report_path = resolve_from_release(release["inspection_report"], release_path, "P3 inspection report")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    inspector = load(INSPECTION, "ppr_profile_inspection")
    values = inspector.currents(packet["current_calibration"]["data"])
    for axis in ("SH", "EX"):
        row = values[axis]
        if row.get("write_firmware") is not False or row.get("profile_enabled") is not False:
            raise ValueError(axis + ": authoritative inspector unexpectedly self-enabled firmware")
        if not (0 < row["amps_per_adc"] < 0.1 and 0 <= row["no_load_current_a"] < 4.6):
            raise ValueError(axis + ": calibration outside commissioning envelope")
        if not (0 < row["gearbox_nm_per_amp"] < 10 and row["holdout_error_bound_nm"] <= 0.40):
            raise ValueError(axis + ": torque calibration outside commissioning envelope")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("output directory must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    release_digest = sha(release_path)
    profile_id = "GGM-P3-" + release_digest[:12]
    header = output_dir / "ggm_commissioning_generated.h"
    command = output_dir / "shredder_eeprom_command.txt"
    header.write_text(header_text(profile_id, values), encoding="utf-8")
    sh = values["SH"]
    command.write_text(
        f"CAL CURRENT {sh['zero_adc']:.9f} {sh['amps_per_adc']:.9f}\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "status": "REVIEW_CANDIDATE_ONLY",
        "profile_id": profile_id,
        "candidate_only": True,
        "source_firmware_modified": False,
        "firmware_built": False,
        "hardware_flashed": False,
        "eeprom_command_applied": False,
        "p8_entry_prerequisite": False,
        "machine_release": "HOLD",
        "p3_release": str(release_path.relative_to(ROOT)),
        "p3_release_sha256": release_digest,
        "inspection_packet_sha256": sha(packet_path),
        "inspection_report_sha256": sha(report_path),
        "p3_stage_validator_sha256": sha(P3_VALIDATOR),
        "inspection_engine_sha256": sha(INSPECTION),
        "calibration": {
            axis: {
                "amps_per_adc": values[axis]["amps_per_adc"],
                "zero_adc": values[axis]["zero_adc"],
                "gearbox_nm_per_amp": values[axis]["gearbox_nm_per_amp"],
                "no_load_current_a": values[axis]["no_load_current_a"],
                "holdout_error_bound_nm": values[axis]["holdout_error_bound_nm"],
            }
            for axis in ("SH", "EX")
        },
        "outputs": {
            header.name: sha(header),
            command.name: sha(command),
        },
        "application_policy": "Human review is required before copying the header, rebuilding firmware, applying EEPROM calibration, or entering P8.",
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p3-release", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = generate(args.p3_release, args.output_dir); code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {"status": "NOT_RUN_OR_REJECTED", "candidate_only": True,
                  "firmware_built": False, "hardware_flashed": False,
                  "eeprom_command_applied": False, "p8_entry_prerequisite": False,
                  "machine_release": "HOLD", "reason": str(exc)}; code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
