#!/usr/bin/env python3
"""Authenticate hot-zone receipt evidence before any P9 heater energization."""
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
    "control/thermal_cutoff_contract.json",
    "exports/thermal/manifest.csv",
    "exports/thermal/channel_schedule.csv",
    "exports/thermal/thermal_cutoff_topology.json",
    "exports/thermal/parts/TH-BH-01/drawing_notes.md",
    "exports/thermal/parts/TH-DIE-01/drawing_notes.md",
    "exports/thermal/parts/TH-TC-01/drawing_notes.md",
    "docs/final/thermocouple_selection_basis_ko.md",
    "docs/final/die_heater_selection_basis_ko.md",
)

RANGES = {
    **{f"bh_z{i}_cold_resistance": (5.184, 6.336, "ohm") for i in range(1, 4)},
    **{f"bh_z{i}_width": (44.5, 45.5, "mm") for i in range(1, 4)},
    "die_cold_resistance": (9.12, 10.56, "ohm"),
    "die_od": (6.487, 6.513, "mm"),
    "die_insertion_length": (39.30, 39.70, "mm"),
    **{f"tc_t{i}_od": (2.97, 3.03, "mm") for i in range(1, 6)},
    **{f"tc_t{i}_stop": (5.15, 5.25, "mm") for i in range(1, 4)},
    "tc_t4_stop": (9.95, 10.05, "mm"),
    "tc_t5_stop": (3.95, 4.05, "mm"),
}
MAXIMUMS = {
    "tc_reference_bias_max": (2.0, "C"),
    "tc_t90_max": (30.0, "s"),
}
MINIMUMS = {"tc_min_insulation": (100.0, "Mohm")}
BOOL_TRUE = {
    "bh_all_pe_bond_verified", "die_positive_retention_verified",
    "tcr_cold_pull_20n_motion_le_0p10", "tf_barrel_datasheet_rating_accepted",
    "tf_die_datasheet_rating_accepted", "tf_barrel_continuity_verified",
    "tf_die_continuity_verified", "tf_barrel_installed_k0_chain",
    "tf_die_installed_k0_chain", "tf_spare_same_spec", "tf_spare_not_installed",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def number(value: str, field: str) -> float:
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
    evidence = (ROOT / row["evidence_path"]).resolve()
    if not evidence.is_relative_to(ROOT) or not evidence.is_file():
        raise ValueError("invalid evidence path: " + row["evidence_path"])
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(evidence) != digest:
        raise ValueError("evidence hash mismatch: " + row["evidence_path"])

def bool_value(row: dict[str, str], metric: str) -> bool:
    token = row.get("value", "").strip().upper()
    if token not in {"TRUE", "FALSE", "YES", "NO", "1", "0", "PASS"}:
        raise ValueError(metric + ": invalid boolean")
    return token in {"TRUE", "YES", "1", "PASS"}


def evaluate(path: Path) -> dict:
    out = {
        "status": "NOT_RUN_OR_REJECTED",
        "p9_receipt_prerequisite": False,
        "power_authorization": False,
        "machine_release": "HOLD",
    }
    try:
        path = path.resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("P9 receipt record must be an existing repository file")
        data = read_rows(path)
        by = {row.get("metric", "").strip(): row for row in data}
        required = set(RANGES) | set(MAXIMUMS) | set(MINIMUMS) | BOOL_TRUE
        if len(data) != len(required) or set(by) != required:
            raise ValueError("P9 hot-zone receipt metric set mismatch")
        source_hashes = {}
        for relative in SOURCE_FILES:
            source = ROOT / relative
            if not source.is_file():
                raise ValueError("missing controlling source: " + relative)
            source_hashes[relative] = sha(source)
        checks = {}
        for metric, (lo, hi, unit) in RANGES.items():
            row = by[metric]; authenticate(row, numeric=True)
            if row.get("unit", "").strip() != unit:
                raise ValueError(metric + ": unit mismatch")
            value = number(row.get("value"), metric)
            u95 = number(row.get("u95"), metric + " U95")
            if u95 < 0 or value - u95 < lo or value + u95 > hi:
                raise ValueError(metric + ": outside U95-bounded acceptance")
            checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": True}
        for metric, (limit, unit) in MAXIMUMS.items():
            row = by[metric]; authenticate(row, numeric=True)
            value = number(row.get("value"), metric); u95 = number(row.get("u95"), metric + " U95")
            if row.get("unit", "").strip() != unit or u95 < 0 or value + u95 > limit:
                raise ValueError(metric + ": maximum acceptance failed")
            checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": True}
        for metric, (limit, unit) in MINIMUMS.items():
            row = by[metric]; authenticate(row, numeric=True)
            value = number(row.get("value"), metric); u95 = number(row.get("u95"), metric + " U95")
            if row.get("unit", "").strip() != unit or u95 < 0 or value - u95 < limit:
                raise ValueError(metric + ": minimum acceptance failed")
            checks[metric] = {"value": value, "u95": u95, "unit": unit, "pass": True}
        for metric in BOOL_TRUE:
            row = by[metric]; authenticate(row, numeric=False)
            if not bool_value(row, metric):
                raise ValueError(metric + ": required true evidence missing")
            checks[metric] = {"value": True, "pass": True}
        out.update({
            "status": "HOT_ZONE_RECEIPT_RECORD_CHECK_PASS",
            "p9_receipt_prerequisite": True,
            "record_sha256": sha(path),
            "source_bindings_sha256": source_hashes,
            "checks": checks,
            "note": "Receipt evidence is coherent; this does not authorize heater power.",
        })
    except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
        out["reason"] = str(exc)
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("record", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = evaluate(args.record)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["status"] == "HOT_ZONE_RECEIPT_RECORD_CHECK_PASS" else 2)


if __name__ == "__main__":
    main()
