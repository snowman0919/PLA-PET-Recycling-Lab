#!/usr/bin/env python3
"""Fail-closed P2 cold-frame and fit evidence analyzer.

This analyzer evaluates authenticated physical records only. It never authorizes
cutting, fabrication, assembly progression, energization, or procurement.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_BINDINGS = (
    "docs/drawings/drawing_register.csv",
    "docs/final/assembly_steps.csv",
)

# FR-001 invokes ISO 2768-m for unspecified linear dimensions. 470 mm and
# 700 mm are both in the >400..1000 mm band: medium class = +/-0.8 mm.
NUMERIC = {
    "frame_base_x": ("range", (469.2, 470.8), "mm"),
    "frame_base_y": ("range", (699.2, 700.8), "mm"),
    "rail_squareness_700": ("max", 0.50, "mm"),
    "shredder_min_static_clearance": ("min", 1.90, "mm"),
    "shredder_hand_rotation_contacts": ("max", 0.0, "count"),
    "extruder_cold_axial_travel": ("min", 1.50, "mm"),
    "extruder_rear_retainer_endplay": ("range", (0.12, 0.28), "mm"),
    "frame_diagonal_a": ("positive", None, "mm"),
    "frame_diagonal_b": ("positive", None, "mm"),
}
BOOL_FALSE = {
    "frame_rocking",
    "guard_moving_envelope_intrusion",
    "guard_hot_envelope_intrusion",
}
REQUIRED = set(NUMERIC) | BOOL_FALSE


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def num(value: str, metric: str) -> float:
    if value is None or not str(value).strip():
        raise ValueError(f"{metric}: blank numeric field")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{metric}: non-finite value")
    return out


def verify_evidence(row: dict[str, str], root: Path, numeric: bool) -> None:
    metric = row.get("metric", "?")
    fields = ["operator", "reviewer", "measured_at", "evidence_path", "sha256"]
    if numeric:
        fields += ["instrument_id", "instrument_calibration_ref"]
    missing = [field for field in fields if not row.get(field, "").strip()]
    if missing:
        raise ValueError(f"{metric}: incomplete provenance: {','.join(missing)}")
    timestamp = datetime.datetime.fromisoformat(row["measured_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError(f"{metric}: measured_at must include timezone")
    path = (root / row["evidence_path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"{metric}: invalid evidence path")
    digest = row["sha256"].strip().lower()
    if len(digest) != 64 or sha(path) != digest:
        raise ValueError(f"{metric}: stale evidence hash")


def interval_pass(value: float, u95: float, mode: str, limit) -> bool:
    if u95 < 0:
        return False
    if mode == "max":
        return value + u95 <= float(limit)
    if mode == "min":
        return value - u95 >= float(limit)
    if mode == "range":
        lo, hi = limit
        return value - u95 >= lo and value + u95 <= hi
    if mode == "positive":
        return value - u95 > 0
    raise ValueError("unknown criterion mode")


def evaluate(rows: list[dict[str, str]], root: Path = ROOT) -> dict:
    by_metric = {}
    for row in rows:
        metric = row.get("metric", "").strip()
        if not metric:
            raise ValueError("blank metric")
        if metric in by_metric:
            raise ValueError(f"duplicate metric: {metric}")
        by_metric[metric] = row
    missing = sorted(REQUIRED - set(by_metric))
    extra = sorted(set(by_metric) - REQUIRED)
    if missing:
        raise ValueError("missing required metrics: " + ", ".join(missing))
    if extra:
        raise ValueError("unexpected metrics: " + ", ".join(extra))
    source_hashes = {}
    for name in SOURCE_BINDINGS:
        source = root / name
        if not source.is_file():
            raise ValueError("missing controlling source: " + name)
        source_hashes[name] = sha(source)

    out = {
        "status": "PASS",
        "record_check_only": True,
        "physical_evidence_evaluated": True,
        "fabrication_authorized": False,
        "stage_release_granted": False,
        "checks": {},
        "source_bindings_sha256": source_hashes,
    }
    values = {}
    uncertainties = {}
    for metric, (mode, limit, unit) in NUMERIC.items():
        row = by_metric[metric]
        verify_evidence(row, root, numeric=True)
        if row.get("unit", "").strip() != unit:
            raise ValueError(f"{metric}: unit must be {unit}")
        value = num(row["value"], metric)
        u95 = num(row["u95"], metric)
        if value < 0:
            raise ValueError(f"{metric}: physical value must be non-negative")
        if u95 < 0:
            raise ValueError(f"{metric}: U95 must be non-negative")
        if metric == "shredder_hand_rotation_contacts" and not value.is_integer():
            raise ValueError(f"{metric}: contact count must be a non-negative integer")
        ok = interval_pass(value, u95, mode, limit)
        values[metric] = value
        uncertainties[metric] = u95
        out["checks"][metric] = {
            "value": value,
            "u95": u95,
            "unit": unit,
            "criterion": mode,
            "limit": limit,
            "pass": ok,
        }
        if not ok:
            out["status"] = "FAIL"

    diagonal_difference = abs(values["frame_diagonal_a"] - values["frame_diagonal_b"])
    diagonal_bound = diagonal_difference + uncertainties["frame_diagonal_a"] + uncertainties["frame_diagonal_b"]
    diagonal_ok = diagonal_bound <= 1.0
    out["checks"]["frame_diagonal_difference"] = {
        "difference_mm": diagonal_difference,
        "u95_conservative_bound_mm": diagonal_bound,
        "limit_mm": 1.0,
        "pass": diagonal_ok,
    }
    if not diagonal_ok:
        out["status"] = "FAIL"

    for metric in sorted(BOOL_FALSE):
        row = by_metric[metric]
        verify_evidence(row, root, numeric=False)
        if row.get("unit", "").strip() != "boolean":
            raise ValueError(f"{metric}: unit must be boolean")
        token = row.get("value", "").strip().lower()
        if token not in {"false", "0", "no", "true", "1", "yes"}:
            raise ValueError(f"{metric}: invalid boolean")
        ok = token in {"false", "0", "no"}
        out["checks"][metric] = {"value": token, "pass": ok}
        if not ok:
            out["status"] = "FAIL"
    return out


def main(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        result = evaluate(list(csv.DictReader(fh)))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyze_p2_records.py p2_cold_fit.csv")
    raise SystemExit(main(Path(sys.argv[1])))
