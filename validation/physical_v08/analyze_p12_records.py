#!/usr/bin/env python3
"""Fail-closed P12 full forming/spool evidence checker."""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P11_VALIDATOR = ROOT / "validation/physical_v08/validate_p11_stage_release.py"
PROFILE_SOURCE = ROOT / "firmware/arduino_mega/src/generated_profiles.h"
FORMING_SOURCE = ROOT / "firmware/arduino_mega/src/machine_supervisor.cpp"
GATE_SOURCE = ROOT / "validation/physical_v08/physical_gate_contract.json"

BOOL_TRUE = {
    "p12_full_path_approval_recorded", "gauge_xy_calibration_verified",
    "puller_speed_reference_verified", "dancer_calibration_verified",
    "traverse_home_limits_verified", "full_1kg_nominal_winding_path_completed",
    "stable_strand_used_for_final_pass",
}
BOOL_FALSE = {
    "traverse_end_collision", "dancer_hard_stop_contact", "spool_spill",
    "guard_contact", "traverse_jam", "leak", "pressure_symptom",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load " + str(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(value, label: str) -> Path:
    if value is None or not str(value).strip():
        raise ValueError(label + " missing")
    path = Path(value); path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def member_file(value, release: Path, label: str) -> Path:
    if value is None or not str(value).strip():
        raise ValueError(label + " missing")
    path = Path(value); path = path if path.is_absolute() else release.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric value")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(field + ": non-finite numeric value")
    return result


def stamp(value: str) -> None:
    parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("measured_at must include timezone")


def authenticate(row: dict[str, str], numeric: bool) -> None:
    required = ["source_lot_id", "measured_at", "operator", "reviewer", "evidence_path", "sha256"]
    if numeric:
        required += ["instrument_id", "calibration_ref"]
    missing = [field for field in required if not str(row.get(field, "")).strip()]
    if missing:
        raise ValueError("missing evidence metadata: " + ",".join(missing))
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError("independent reviewer must differ from operator")
    stamp(row["measured_at"])
    evidence = repo_file(row["evidence_path"], "P12 evidence")
    if row["sha256"].strip().lower() != sha(evidence):
        raise ValueError("P12 evidence hash mismatch: " + row["evidence_path"])


def bool_value(row: dict[str, str], metric: str) -> bool:
    token = row.get("value", "").strip().upper()
    if token not in {"TRUE", "FALSE", "YES", "NO", "1", "0", "PASS"}:
        raise ValueError(metric + ": invalid boolean")
    return token in {"TRUE", "YES", "1", "PASS"}


def design_limits() -> dict[str, tuple[str, float, str]]:
    profile = PROFILE_SOURCE.read_text(encoding="utf-8")
    forming = FORMING_SOURCE.read_text(encoding="utf-8")
    controlled = re.search(r"DANCER_CONTROLLED_STOP_RAD\s*=\s*([0-9.]+)f?;", profile)
    hard = re.search(r"DANCER_MECHANICAL_HARD_STOP_RAD\s*=\s*([0-9.]+)f?;", profile)
    width = re.search(r"spooler\.spool_width_mm\s*=\s*([0-9.]+)f?;", forming)
    if not (controlled and hard and width):
        raise ValueError("forming design limits missing from firmware sources")
    return {
        "puller_slip": ("max", 1.0, "percent"),
        "traverse_usable_width": ("min", float(width.group(1)), "mm"),
        "dancer_control_stop_angle": ("strict_max", float(controlled.group(1)), "rad"),
        "dancer_peak_angle": ("strict_max", float(hard.group(1)), "rad"),
        "spool_test_load_mass": ("min", 1.0, "kg"),
        "diameter_mean_error": ("max", 0.05, "mm"),
        "diameter_max_ovality": ("max", 0.05, "mm"),
        "diameter_max_u95": ("max", 0.03, "mm"),
        "gearbox_torque_peak": ("strict_max", 8.0, "N.m"),
        "motor_current_peak": ("max", 6.0, "A"),
    }


def within(value: float, u95: float, mode: str, limit: float) -> bool:
    if value < 0 or u95 < 0:
        return False
    if mode == "min":
        return value - u95 >= limit
    if mode == "strict_max":
        return value + u95 < limit
    return value + u95 <= limit


def validate_p11(release_path: Path, checker=None) -> tuple[dict, str]:
    result = checker(release_path) if checker else load(P11_VALIDATOR, "ppr_p12_p11").validate(release_path)
    if result.get("status") != "P11_STAGE_RELEASE_VALIDATED" or result.get("p12_entry_prerequisite") is not True:
        raise ValueError("P11 stage release is not a valid P12 prerequisite")
    if result.get("material_feed_authorized") is not False or result.get("continuing_power_authority") is not False:
        raise ValueError("P11 release authorization semantics drift")
    if result.get("machine_release") != "HOLD":
        raise ValueError("P11 release machine state drift")
    release = json.loads(release_path.read_text(encoding="utf-8"))
    p11_result = member_file(release.get("p11_result"), release_path, "P11 result")
    if release.get("p11_result_sha256") != sha(p11_result):
        raise ValueError("P11 result binding drift")
    saved = json.loads(p11_result.read_text(encoding="utf-8"))
    if saved.get("status") != "MATERIAL_RUN_RECORD_CHECK_PASS" or saved.get("material") != "PET":
        raise ValueError("P11 result is not a released PET material run")
    lot_id = str(saved.get("context", {}).get("lot_id", "")).strip()
    if not lot_id:
        raise ValueError("P11 released PET lot ID missing")
    return result, lot_id


def evaluate(record: Path, p11_release: Path, p11_checker=None) -> dict:
    out = {"status": "NOT_RUN_OR_REJECTED", "stage_p12_pass": False,
           "physical_validation_complete_candidate": False,
           "continuing_power_authority": False, "production_authorized": False,
           "safety_certification": False, "machine_release": "HOLD"}
    try:
        record = repo_file(record, "P12 forming/spool record")
        p11_release = repo_file(p11_release, "P11 stage release")
        p11_result, released_lot = validate_p11(p11_release, checker=p11_checker)
        data = rows(record)
        by = {row.get("metric", "").strip(): row for row in data}
        limits = design_limits()
        required = set(limits) | BOOL_TRUE | BOOL_FALSE
        if len(data) != len(required) or set(by) != required:
            raise ValueError("P12 metric set mismatch")
        lot_ids = {row.get("source_lot_id", "").strip() for row in data}
        if lot_ids != {released_lot}:
            raise ValueError("P12 source_lot_id must match the released P11 PET lot")
        checks = {}
        for metric, (mode, limit, unit) in limits.items():
            row = by[metric]; authenticate(row, numeric=True)
            if row.get("unit", "").strip() != unit:
                raise ValueError(metric + ": unit mismatch")
            value = number(row.get("value"), metric)
            u95 = number(row.get("u95"), metric + " U95")
            if not within(value, u95, mode, limit):
                raise ValueError(metric + ": outside U95-bounded acceptance")
            checks[metric] = {"value": value, "u95": u95, "unit": unit, "limit": limit, "pass": True}
        for metric, expected in [(x, True) for x in BOOL_TRUE] + [(x, False) for x in BOOL_FALSE]:
            row = by[metric]; authenticate(row, numeric=False)
            actual = bool_value(row, metric)
            if actual is not expected:
                raise ValueError(metric + ": boolean acceptance failed")
            if metric == "p12_full_path_approval_recorded" and row.get("approval_scope", "").strip() != "P12_FULL_PATH_RUN":
                raise ValueError("P12 full-path approval scope mismatch")
            checks[metric] = {"value": actual, "pass": True}
        source_hashes = {str(path.relative_to(ROOT)): sha(path) for path in (PROFILE_SOURCE, FORMING_SOURCE, GATE_SOURCE)}
        out.update({
            "status": "P12_RECORD_CHECK_PASS",
            "stage_p12_pass": False,
            "physical_validation_complete_candidate": False,
            "source_lot_id": released_lot,
            "checks": checks,
            "p11_release_sha256": sha(p11_release),
            "p11_revalidation": p11_result,
            "record_sha256": sha(record),
            "source_bindings_sha256": source_hashes,
            "continuing_power_authority": False,
            "production_authorized": False,
            "safety_certification": False,
            "machine_release": "HOLD",
            "note": "Authenticated P12 evidence passed; separate reviewed P12 stage release is required for a physical-validation completion candidate.",
        })
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        out["reason"] = str(exc)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("record", type=Path)
    ap.add_argument("--p11-release", required=True, type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args(); result = evaluate(args.record, args.p11_release)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "P12_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__":
    main()
