#!/usr/bin/env python3
"""Fail-closed P8 installed-motor dry-run evidence analyzer.

Consumes authenticated P3/P6/P7 releases and the firmware commissioning gate.
It validates already-recorded motor-run evidence and never energizes hardware.
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
P6_VALIDATOR = ROOT / "validation/physical_v08/validate_p6_stage_release.py"
P7_VALIDATOR = ROOT / "validation/physical_v08/validate_p7_stage_release.py"
FW_VALIDATOR = ROOT / "validation/physical_v08/validate_p8_firmware_commissioning.py"
SOURCE_FILES = (
    "control/ggm_drive_contract.json",
    "validation/physical_v08/physical_gate_contract.json",
    "validation/physical_v08/P8_INSTALLED_MOTOR_DRY_RUN_KO.md",
)
LIMITS = {
    "shredder_cutter_rpm": ("positive", None, "rpm"),
    "shredder_max_current": ("max", 6.0, "A"),
    "screw_start_rpm": ("max", 10.0, "rpm"),
    "screw_max_rpm": ("max", 20.0, "rpm"),
    "screw_max_current": ("max", 6.0, "A"),
}
BOOL_TRUE = {
    "p8_motor_power_approval_recorded", "heaters_isolated", "guards_closed",
    "one_motor_branch_at_a_time", "auxiliary_branches_direction_stop_checked",
    "shredder_speed_expectation_reviewed", "normal_stop_removes_command",
    "estop_removes_command", "tach_loss_removes_command",
}
BOOL_FALSE = {
    "screw_reverse_commanded", "abnormal_bearing_or_coupling_temp_trend",
    "abnormal_vibration_or_noise", "automatic_restart_after_recovery",
}
REQUIRED = set(LIMITS) | BOOL_TRUE | BOOL_FALSE


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric value")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + ": non-finite numeric value")
    return out


def boolean(value, field: str) -> bool:
    token = str(value).strip().upper()
    if token in {"TRUE", "YES", "PASS", "1"}:
        return True
    if token in {"FALSE", "NO", "NONE", "0"}:
        return False
    raise ValueError(field + ": invalid boolean")


def evidence(row: dict[str, str], numeric: bool) -> None:
    required = ["operator", "reviewer", "measured_at", "evidence_path", "sha256"]
    if numeric:
        required += ["instrument_id", "calibration_ref"]
    missing = [key for key in required if not str(row.get(key, "")).strip()]
    if missing:
        raise ValueError("missing evidence metadata: " + ",".join(missing))
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError("independent reviewer must differ from operator")
    stamp = datetime.datetime.fromisoformat(row["measured_at"].replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("measured_at must include timezone")
    path = (ROOT / row["evidence_path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("invalid evidence path: " + row["evidence_path"])
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError("evidence hash mismatch: " + row["evidence_path"])


def stage(path: Path, module_path: Path, expected: str, checker=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(expected + " input must be an existing repository file")
    if checker is not None:
        result = checker(path)
    else:
        result = load(module_path, "p8_" + expected.lower()).validate(path)
    if result.get("status") != expected:
        raise ValueError(expected + " prerequisite rejected")
    return result


def metric_ok(value: float, u95: float, mode: str, limit) -> bool:
    if value < 0 or u95 < 0:
        return False
    if mode == "positive":
        return value - u95 > 0
    return value + u95 <= float(limit)

def evaluate(record: Path, p3_release: Path, p6_release: Path, p7_release: Path,
             profile_dir: Path, tach_path: Path, install_path: Path, *,
             p3_checker=None, p6_checker=None, p7_checker=None, fw_checker=None) -> dict:
    out = {
        "status": "NOT_RUN_OR_REJECTED", "stage_p8_pass": False,
        "hardware_authorization": False, "heater_energization_authorized": False,
        "machine_release": "HOLD",
    }
    try:
        p3 = stage(p3_release, P3_VALIDATOR, "P3_STAGE_RELEASE_VALIDATED", p3_checker)
        p6 = stage(p6_release, P6_VALIDATOR, "P6_STAGE_RELEASE_VALIDATED", p6_checker)
        p7 = stage(p7_release, P7_VALIDATOR, "P7_STAGE_RELEASE_VALIDATED", p7_checker)
        if p6.get("p8_entry_prerequisite") is not True or p7.get("p8_entry_prerequisite") is not True:
            raise ValueError("P6/P7 do not permit P8 entry review")
        if p3.get("p4_energization_authorized") is not False:
            raise ValueError("P3 release safety semantics drift")
        if fw_checker is None:
            fw = load(FW_VALIDATOR, "p8_firmware_gate").validate(
                p3_release, profile_dir, tach_path, install_path)
        else:
            fw = fw_checker(p3_release, profile_dir, tach_path, install_path)
        if fw.get("status") != "FIRMWARE_COMMISSIONING_RECORD_CHECK_PASS" or fw.get("firmware_prerequisite_for_p8") is not True:
            raise ValueError("firmware commissioning prerequisite rejected")
        if fw.get("motor_energization_authorized") is not False or fw.get("heater_energization_authorized") is not False:
            raise ValueError("firmware commissioning safety semantics drift")

        record = record.resolve()
        if not record.is_relative_to(ROOT) or not record.is_file():
            raise ValueError("P8 record must be an existing repository file")
        rows = read_rows(record)
        by = {row.get("metric", "").strip(): row for row in rows}
        if len(rows) != len(REQUIRED) or set(by) != REQUIRED:
            raise ValueError("P8 metric set mismatch")
        checks = {}
        for metric, (mode, limit, unit) in LIMITS.items():
            row = by[metric]; evidence(row, numeric=True)
            if row.get("unit", "").strip() != unit:
                raise ValueError(metric + ": unit mismatch")
            value = number(row.get("value"), metric); u95 = number(row.get("u95"), metric + " U95")
            if not metric_ok(value, u95, mode, limit):
                raise ValueError(metric + ": outside U95-bounded acceptance")
            checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": True}
            if metric == "shredder_cutter_rpm":
                checks[metric]["design_expectation_rpm"] = 16.0
        for metric in sorted(BOOL_TRUE | BOOL_FALSE):
            row = by[metric]; evidence(row, numeric=False)
            expected = metric in BOOL_TRUE; actual = boolean(row.get("value"), metric)
            if actual is not expected:
                raise ValueError(metric + ": boolean acceptance failed")
            checks[metric] = {"value": actual, "pass": True}
        source_hashes = {}
        for name in SOURCE_FILES:
            path = ROOT / name
            if not path.is_file():
                raise ValueError("missing controlling source: " + name)
            source_hashes[name] = sha(path)
        out.update({
            "status": "NUMERIC_RECORD_CHECK_PASS", "checks": checks,
            "record_sha256": sha(record), "source_bindings_sha256": source_hashes,
            "input_motor_power_approval_recorded": True,
            "prerequisites": {
                "p3_release_sha256": sha(p3_release.resolve()),
                "p6_release_sha256": sha(p6_release.resolve()),
                "p7_release_sha256": sha(p7_release.resolve()),
                "firmware_commissioning": fw,
            },
            "note": "P8 recorded run evidence is coherent. This analyzer grants no continuing motor authority and no heater authority.",
        })
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        out["reason"] = str(exc)
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    ap.add_argument("--p3-release", type=Path, required=True)
    ap.add_argument("--p6-release", type=Path, required=True)
    ap.add_argument("--p7-release", type=Path, required=True)
    ap.add_argument("--profile-dir", type=Path, required=True)
    ap.add_argument("--tach-calibration", type=Path, required=True)
    ap.add_argument("--firmware-installation", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = evaluate(args.record, args.p3_release, args.p6_release, args.p7_release,
                      args.profile_dir, args.tach_calibration, args.firmware_installation)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "NUMERIC_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__":
    main()
