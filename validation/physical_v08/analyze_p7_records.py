#!/usr/bin/env python3
"""Fail-closed P7 electrical-safety and logic-only evidence checker.

Authenticates raw evidence and binds the reviewed record to the released electrical
schedules. It never authorizes motor/heater energization or machine release.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = (
    "exports/final/electrical/fuse_schedule.csv",
    "exports/final/electrical/pin_schedule.csv",
    "exports/final/electrical/wire_schedule.csv",
    "electronics/io_schedule.csv",
    "validation/physical_v08/physical_gate_contract.json",
    "control/thermal_cutoff_contract.json",
)
LIMITS = {
    "pe_bond_worst": ("max", 0.10, "ohm"),
    "insulation_resistance": ("min", 1.0, "Mohm"),
    "insulation_test_voltage": ("range", (500.0, 500.0), "VDC"),
    "logic_rail_voltage": ("range", (22.8, 25.2), "V"),
    "logic_startup_current": ("max", 0.5, "A"),
    "hazardous_enable_count_after_reset": ("max", 0.0, "count"),
}
BOOL = {
    "motor_branches_isolated": True,
    "heater_branches_isolated": True,
    "logic_power_approval_recorded": True,
    "electronics_disconnected_for_megger": True,
    "estop_k0_deenergized": True,
    "lid_k0_deenergized": True,
    "service_k0_deenergized": True,
    "tf_barrel_k0_deenergized": True,
    "tf_die_k0_deenergized": True,
    "motor_heater_permission_removed_on_open": True,
    "automatic_restart_after_power_restore": False,
    "fuse_ids_match_schedule": True,
    "point_to_point_wiring_match": True,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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

def authenticate(row: dict[str, str], numeric: bool) -> None:
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


def limit_ok(value: float, u95: float, mode: str, limit) -> bool:
    if value < 0 or u95 < 0:
        return False
    if mode == "max":
        return value + u95 <= float(limit)
    if mode == "min":
        return value - u95 >= float(limit)
    lo, hi = limit
    return value - u95 >= lo and value + u95 <= hi

def evaluate(path: Path, root: Path = ROOT) -> dict:
    out = {"status": "NOT_RUN_OR_REJECTED", "stage_p7_pass": False,
           "motor_energization_authorized": False, "heater_energization_authorized": False,
           "action_state": "HOLD", "machine_release": "HOLD"}
    try:
        path = path.resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("P7 record must be an existing repository file")
        rows = read_rows(path)
        by = {row.get("metric", "").strip(): row for row in rows}
        required = set(LIMITS) | set(BOOL)
        if len(rows) != len(required) or set(by) != required:
            raise ValueError("P7 metric set mismatch")
        source_hashes = {}
        for name in SOURCE_FILES:
            source = root / name
            if not source.is_file():
                raise ValueError("missing controlling source: " + name)
            source_hashes[name] = sha(source)
        checks = {}
        for metric, (mode, limit, unit) in LIMITS.items():
            row = by[metric]; authenticate(row, numeric=True)
            if row.get("unit", "").strip() != unit:
                raise ValueError(metric + ": unit mismatch")
            value = number(row.get("value"), metric)
            u95 = number(row.get("u95"), metric + " U95")
            ok = limit_ok(value, u95, mode, limit)
            checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": ok}
            if not ok:
                raise ValueError(metric + ": outside U95-bounded acceptance")
        for metric, expected in BOOL.items():
            row = by[metric]; authenticate(row, numeric=False)
            token = row.get("value", "").strip().upper()
            if token not in {"TRUE", "FALSE", "YES", "NO", "1", "0", "PASS"}:
                raise ValueError(metric + ": invalid boolean")
            actual = token in {"TRUE", "YES", "1", "PASS"}
            if actual is not expected:
                raise ValueError(metric + ": boolean acceptance failed")
            checks[metric] = {"value": actual, "pass": True}
        out.update({
            "status": "NUMERIC_RECORD_CHECK_PASS",
            "checks": checks,
            "record_sha256": sha(path),
            "source_bindings_sha256": source_hashes,
            "note": "P7 evidence passed authentication and logic-only checks. Motor/heater stages remain separately gated.",
        })
    except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
        out["reason"] = str(exc)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("record", type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args(); result = evaluate(args.record)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "NUMERIC_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__":
    main()
