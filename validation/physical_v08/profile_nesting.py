#!/usr/bin/env python3
"""Fail-closed profile stock nesting from authenticated physical length records.

The solver consumes conservative usable length (measured value minus U95) and a
caller-supplied non-negative kerf budget plus 0.5 mm per-piece upper cut tolerance.
It never authorizes cutting.
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
CUTLIST = ROOT / "exports/fabrication/frame_cut_list.csv"
SELF = Path(__file__).resolve()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
REQUIRED_PROVENANCE = ("source_asset", "instrument_id", "instrument_calibration_ref", "measured_at", "operator", "reviewer", "evidence_path", "sha256")


def requirements(root=ROOT):
    from frame_release import validate
    validate(root)
    out = {}
    with (root / "exports/fabrication/frame_cut_list.csv").open(newline="", encoding="utf-8") as fh:
        source = list(csv.DictReader(fh))
    for row in source:
        typ = "2020" if row["stock"].startswith("20x20") else "2040" if row["stock"].startswith("20x40") else None
        if typ:
            out.setdefault(typ, []).extend([(row["part_id"], float(row["cut_length_mm"]) + 0.5)] * int(row["quantity"]))
    return out


def _evidence(row, root=ROOT):
    for field in REQUIRED_PROVENANCE:
        if not row.get(field, "").strip():
            raise ValueError(f"{row.get('record_id','?')}: missing {field}")
    timestamp = datetime.datetime.fromisoformat(row["measured_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None: raise ValueError("profile measured_at must include timezone")
    if row["operator"].strip().casefold() == row["reviewer"].strip().casefold():
        raise ValueError("profile independent reviewer required")
    path = (root / row["evidence_path"]).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"{row['record_id']}: invalid evidence path")
    digest = row["sha256"].lower()
    if len(digest) != 64 or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"{row['record_id']}: stale evidence hash")


def measured(path, root=ROOT):
    out = {"2020": [], "2040": []}
    seen = set()
    with path.open(newline="", encoding="utf-8") as fh:
        source = list(csv.DictReader(fh))
    for row in source:
        status = row.get("status", "").strip().upper()
        if status not in {"USABLE", "PASS"}:
            continue
        if row.get("condition_check") != "USABLE_REVIEWED" or row.get("inspection_power_state") != "NONE":
            raise ValueError("profile unpowered condition review missing")
        record_id = row.get("record_id", "").strip()
        if not record_id or record_id in seen:
            raise ValueError("blank or duplicate profile record_id")
        seen.add(record_id)
        typ = row.get("profile_type", "").strip().upper().replace("X", "")
        typ = {"2020": "2020", "2040": "2040"}.get(typ)
        if not typ:
            raise ValueError(f"{record_id}: invalid profile_type")
        if not row.get("straightness_note", "").strip() or not row.get("damage_note", "").strip():
            raise ValueError(f"{record_id}: missing condition notes")
        length = float(row["usable_length_mm"])
        u95 = float(row["u95_length_mm"])
        if not math.isfinite(length) or not math.isfinite(u95) or length <= 0 or u95 < 0 or length - u95 <= 0:
            raise ValueError(f"{record_id}: invalid usable length interval")
        _evidence(row, root)
        out[typ].append((record_id, length - u95))
    return out


def solve(cuts, bars, kerf):
    if isinstance(kerf, bool) or not math.isfinite(kerf) or kerf < 0:
        raise ValueError("kerf must be finite and non-negative")
    if any(not isinstance(name, str) or not name.strip() or isinstance(length, bool) or not math.isfinite(length) or length <= 0 for name, length in [*cuts, *bars]):
        raise ValueError("invalid cut/stock identity or length")
    if len({name for name, _ in bars}) != len(bars):
        raise ValueError("duplicate stock bar ID")
    if sum(length + kerf for _, length in cuts) > sum(length for _, length in bars) + 1e-9:
        return False, []
    cuts = sorted(cuts, key=lambda x: x[1], reverse=True)
    bars = sorted(bars, key=lambda x: x[1], reverse=True)
    rem = [bar[1] for bar in bars]
    plan = [[] for _ in bars]
    visited = 0
    def rec(i):
        nonlocal visited
        visited += 1
        if visited > 200000: raise ValueError("nesting search budget exhausted; no cutting authorization")
        if i == len(cuts):
            return True
        pid, length = cuts[i]
        need = length + kerf
        seen = set()
        for j, remaining in enumerate(rem):
            key = round(remaining, 6)
            if key in seen or remaining + 1e-9 < need:
                continue
            seen.add(key)
            rem[j] -= need
            plan[j].append((pid, length))
            if rec(i + 1):
                return True
            plan[j].pop()
            rem[j] += need
        return False
    ok = rec(0)
    return ok, [{"stock_id": bars[i][0], "conservative_stock_mm": bars[i][1], "cuts": plan[i], "leftover_mm": round(rem[i], 3)} for i in range(len(bars))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("measurements", type=Path)
    ap.add_argument("--kerf-mm", type=float, required=True, help="conservative per-cut kerf budget")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    if not math.isfinite(args.kerf_mm) or args.kerf_mm < 0:
        raise SystemExit("kerf must be finite and >=0")
    measurements = args.measurements.resolve()
    if not measurements.is_relative_to(ROOT) or not measurements.is_file():
        raise SystemExit("measurement record must be an existing repository file")
    req = requirements()
    try:
        stock = measured(measurements)
    except (KeyError, ValueError) as exc:
        raise SystemExit(f"profile evidence rejected: {exc}")
    result = {
        "status": "PASS", "cut_authorization": False, "kerf_budget_mm": args.kerf_mm,
        "stock_length_basis": "measured_minus_u95",
        "per_piece_upper_cut_allowance_mm": 0.5,
        "measurements_path": str(measurements.relative_to(ROOT)),
        "measurements_sha256": sha(measurements),
        "cutlist_path": str(CUTLIST.relative_to(ROOT)),
        "cutlist_sha256": sha(CUTLIST),
        "solver_source_sha256": sha(SELF),
        "profiles": {},
    }
    for typ in ("2020", "2040"):
        if not stock[typ]:
            result["profiles"][typ] = {"status": "NOT_RUN", "required_piece_count": len(req[typ])}
            result["status"] = "NOT_RUN"
            continue
        ok, plan = solve(req[typ], stock[typ], args.kerf_mm)
        result["profiles"][typ] = {
            "status": "PASS" if ok else "INSUFFICIENT_OR_UNNESTABLE",
            "required_piece_count": len(req[typ]),
            "required_raw_mm": sum(x[1] for x in req[typ]),
            "measured_conservative_usable_mm": sum(x[1] for x in stock[typ]),
            "plan": plan if ok else [],
        }
        if not ok:
            result["status"] = "FAIL"
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["status"] in {"PASS", "NOT_RUN"} else 2)


if __name__ == "__main__":
    main()
