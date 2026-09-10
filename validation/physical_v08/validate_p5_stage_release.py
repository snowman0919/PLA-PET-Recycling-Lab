#!/usr/bin/env python3
"""Validate a reviewed P5 coupon result before P6 entry review.

This validator replays the current P5 analyzer against the exact bound records.
It never grants machining, purchase, energization, or machine release.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P5_ANALYZER = ROOT / "validation/physical_v08/analyze_p5_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_p5():
    spec = importlib.util.spec_from_file_location("ppr_p5_stage_analyzer", P5_ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P5 analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def repo_file(value: str, release_path: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def repo_dir(value: str, release_path: Path) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_dir():
        raise ValueError("P5 records_dir must resolve to a repository directory")
    return path


def require_time(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("P5 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P5 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P5" or release.get("status") != "PASS":
        raise ValueError("P5 physical release is not PASS")
    if release.get("release_scope") != "P5_COUPON_COMPLETE_P6_REVIEW_ONLY":
        raise ValueError("P5 release scope invalid")
    if release.get("action_state") != "HOLD" or release.get("machine_release") != "HOLD":
        raise ValueError("P5 release safety state invalid")
    for field in ("approved_by", "independent_reviewer", "qualified_supplier", "qualified_route_id", "screw_heat_reservation_ref", "barrel_heat_reservation_ref"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P5 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P5 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))

    records = repo_dir(release.get("records_dir", ""), path)
    result_path = repo_file(release.get("p5_result", ""), path, "P5 result")
    if release.get("p5_result_sha256") != sha(result_path):
        raise ValueError("P5 result hash mismatch")
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_p5()
    fresh = authority.evaluate(records)
    if saved.get("status") != "NUMERIC_RECORD_CHECK_PASS" or fresh.get("status") != "NUMERIC_RECORD_CHECK_PASS":
        raise ValueError("P5 analyzer result is not PASS")
    if saved.get("stage_p5_pass") is not False or saved.get("full_part_order_authorized") is not False:
        raise ValueError("saved P5 result has unsafe release semantics")
    if fresh.get("stage_p5_pass") is not False or fresh.get("full_part_order_authorized") is not False:
        raise ValueError("current P5 analyzer safety semantics drift")
    for key, digest in fresh.get("record_files_sha256", {}).items():
        if saved.get("record_files_sha256", {}).get(key) != digest:
            raise ValueError("P5 saved result record binding drift: " + key)
    for key, digest in fresh.get("source_bindings_sha256", {}).items():
        if saved.get("source_bindings_sha256", {}).get(key) != digest:
            raise ValueError("P5 saved result source binding drift: " + key)
    return {
        "status": "P5_STAGE_RELEASE_VALIDATED",
        "stage": "P5",
        "p6_entry_prerequisite": True,
        "p6_entry_review": True,
        "action_state": "HOLD",
        "machine_release": "HOLD",
        "p5_result_sha256": sha(result_path),
        "p5_analyzer_sha256": sha(P5_ANALYZER),
        "record_files_sha256": fresh["record_files_sha256"],
        "qualified_supplier": release["qualified_supplier"],
        "qualified_route_id": release["qualified_route_id"],
        "screw_heat_reservation_ref": release["screw_heat_reservation_ref"],
        "barrel_heat_reservation_ref": release["barrel_heat_reservation_ref"],
        "approved_by": release["approved_by"],
        "independent_reviewer": release["independent_reviewer"],
        "reviewed_at": release["reviewed_at"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("release", type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = validate(args.release); code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {"status": "NOT_RUN_OR_REJECTED", "p6_entry_prerequisite": False,
                  "p6_entry_review": False, "action_state": "HOLD", "machine_release": "HOLD", "reason": str(exc)}; code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output: args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__": main()
