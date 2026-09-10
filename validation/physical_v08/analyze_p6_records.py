#!/usr/bin/env python3
"""Fail-closed P6 cold-extruder evidence checker.

Requires a validated P5 release, authenticated production receipt, and cold-fit
measurements. It never grants machining, energization, or machine release.
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
P5_VALIDATOR = ROOT / "validation/physical_v08/validate_p5_stage_release.py"
LIMITS = {
    "screw_barrel_clearance_min": ("min", 0.28, "mm"),
    "screw_barrel_clearance_max": ("max", 0.32, "mm"),
    "bearing_pocket_diametral_clearance": ("range", (0.30, 0.35), "mm"),
    "thrust_loaded_endplay": ("range", (0.05, 0.15), "mm"),
    "hand_rotation_contacts": ("max", 0.0, "count"),
    "drive_coaxiality": ("max", 0.05, "mm"),
    "front_guide_cold_axial_travel": ("min", 1.50, "mm"),
    "rear_retainer_cold_endplay": ("range", (0.12, 0.28), "mm"),
}
BOOL = {"thrust_washer_orientation_ok": True, "printed_shim_used": False}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value, field: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(field + ": blank numeric value")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(field + ": non-finite numeric value")
    return out


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_p5_validator():
    spec = importlib.util.spec_from_file_location("ppr_p6_p5_validator", P5_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P5 stage validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authenticate(row: dict[str, str], field: str = "measured_at") -> None:
    for key in ("operator", "reviewer", field, "evidence_path", "sha256"):
        if not str(row.get(key, "")).strip():
            raise ValueError("missing evidence metadata: " + key)
    stamp = datetime.datetime.fromisoformat(str(row[field]).replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError(field + " must include timezone")
    path = (ROOT / row["evidence_path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("invalid evidence path: " + row["evidence_path"])
    digest = str(row["sha256"]).strip().lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError("evidence hash mismatch: " + row["evidence_path"])


def check_receipt(path: Path, p5: dict) -> dict:
    rows = read_rows(path)
    if {r.get("part_id") for r in rows} != {"EX-SCR-01", "EX-BAR-01"} or len(rows) != 2:
        raise ValueError("production receipt must contain exactly EX-SCR-01 and EX-BAR-01")
    serials = set()
    by = {r["part_id"]: r for r in rows}
    for part, reservation_key in (("EX-SCR-01", "screw_heat_reservation_ref"), ("EX-BAR-01", "barrel_heat_reservation_ref")):
        row = by[part]; authenticate(row, "received_at")
        for key in ("part_serial", "supplier_id", "qualified_route_id", "heat_reservation_ref", "heat_lot_id",
                    "material_certificate_id", "process_certificate_id", "final_finish_report_id"):
            if not str(row.get(key, "")).strip():
                raise ValueError(part + ": missing " + key)
        if row["part_serial"] in serials:
            raise ValueError("duplicate production part serial")
        serials.add(row["part_serial"])
        grade = row.get("material_grade", "").upper().replace(" ", "")
        if "SCM440" not in grade or "G4105" not in grade:
            raise ValueError(part + ": material grade mismatch")
        if row["supplier_id"] != p5["qualified_supplier"] or row["qualified_route_id"] != p5["qualified_route_id"]:
            raise ValueError(part + ": supplier/process route differs from P5 release")
        if row["heat_reservation_ref"] != p5[reservation_key]:
            raise ValueError(part + ": heat reservation differs from P5 release")
        if row.get("disposition", "").strip().upper() != "PASS":
            raise ValueError(part + ": receipt disposition is not PASS")
    return {"parts": 2, "supplier": p5["qualified_supplier"], "route": p5["qualified_route_id"],
            "serials": {part: by[part]["part_serial"] for part in by}}

def limit_ok(value: float, u95: float, mode: str, limit) -> bool:
    if u95 < 0:
        return False
    if mode == "min": return value - u95 >= float(limit)
    if mode == "max": return value + u95 <= float(limit)
    lo, hi = limit
    return value - u95 >= lo and value + u95 <= hi


def check_cold(path: Path) -> dict:
    rows = read_rows(path)
    by = {r.get("metric", "").strip(): r for r in rows}
    required = set(LIMITS) | set(BOOL)
    if set(by) != required or len(rows) != len(required):
        raise ValueError("P6 cold-fit metric set mismatch")
    checks = {}
    for metric, (mode, limit, unit) in LIMITS.items():
        row = by[metric]; authenticate(row)
        if row.get("unit", "").strip() != unit:
            raise ValueError(metric + ": unit mismatch")
        if not str(row.get("instrument_id", "")).strip() or not str(row.get("calibration_ref", "")).strip():
            raise ValueError(metric + ": instrument/calibration metadata missing")
        value = number(row.get("value"), metric); u95 = number(row.get("u95"), metric + " U95")
        if value < 0 or u95 < 0:
            raise ValueError(metric + ": negative physical value/U95")
        ok = limit_ok(value, u95, mode, limit)
        checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": ok}
        if not ok:
            raise ValueError(metric + ": outside U95-bounded acceptance")
    for metric, expected in BOOL.items():
        row = by[metric]; authenticate(row)
        token = row.get("value", "").strip().upper()
        if token not in {"TRUE", "FALSE", "YES", "NO", "1", "0", "PASS"}:
            raise ValueError(metric + ": invalid boolean")
        actual = token in {"TRUE", "YES", "1", "PASS"}
        if actual is not expected:
            raise ValueError(metric + ": boolean acceptance failed")
        checks[metric] = {"value": actual, "pass": True}
    return {"checks": checks, "rows": len(rows), "record_sha256": sha(path)}

def evaluate(cold_path: Path, p5_release: Path, receipt_path: Path) -> dict:
    out = {"status": "NOT_RUN_OR_REJECTED", "stage_p6_pass": False,
           "hardware_authorization": False, "action_state": "HOLD", "machine_release": "HOLD"}
    try:
        p5 = load_p5_validator().validate(p5_release)
        if p5.get("status") != "P5_STAGE_RELEASE_VALIDATED" or p5.get("p6_entry_prerequisite") is not True:
            raise ValueError("P5 stage release prerequisite is not valid")
        out.update({"status": "NUMERIC_RECORD_CHECK_PASS",
                    "p5_release": {"sha256": sha(p5_release), "validated": p5},
                    "production_receipt": check_receipt(receipt_path, p5),
                    "cold_fit": check_cold(cold_path),
                    "note": "P6 records passed authentication and arithmetic only; downstream electrical/heater stages remain separately gated."})
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        out["reason"] = str(exc)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cold_record", type=Path)
    ap.add_argument("--p5-release", type=Path, required=True)
    ap.add_argument("--production-receipt", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = evaluate(args.cold_record, args.p5_release, args.production_receipt)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output: args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "NUMERIC_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__": main()
