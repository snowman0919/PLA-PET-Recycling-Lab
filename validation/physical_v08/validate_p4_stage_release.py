#!/usr/bin/env python3
"""Validate a human-reviewed P4 result before remaining-cutter review may begin.

This validator records no fabrication or energization authority. It only proves
that the reviewed P4 result is still reproducible from the bound raw evidence.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P4_ANALYZER = ROOT / "validation/physical_v08/analyze_p4_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_p4():
    spec = importlib.util.spec_from_file_location("ppr_p4_stage_analyzer", P4_ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P4 analyzer")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def inside(value: str, release_path: Path, root: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def timestamp(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, root: Path = ROOT, p4_module=None, p3_checker=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("P4 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P4" or release.get("status") != "PASS":
        raise ValueError("P4 physical release is not PASS")
    if release.get("release_scope") != "P4_COMPLETE_REMAINING_CUTTER_REVIEW_ONLY":
        raise ValueError("P4 release scope invalid")
    if release.get("remaining_cut01_quantity") != 10:
        raise ValueError("P4 release must preserve exactly ten remaining CUT-01 parts")
    if release.get("remaining_cut01_fabrication_authorized") is not False:
        raise ValueError("P4 stage release must not authorize remaining-cutter fabrication")
    if release.get("downstream_energization_authorized") is not False or release.get("machine_release") != "HOLD":
        raise ValueError("P4 stage release has unsafe downstream semantics")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P4 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P4 release requires an independent reviewer")
    timestamp(release.get("reviewed_at"))

    result_path = inside(release.get("p4_result", ""), path, root, "P4 result")
    if release.get("p4_result_sha256") != sha(result_path):
        raise ValueError("P4 result hash mismatch")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    analyzer = p4_module or load_p4()
    verified = analyzer.validate_result(result, root, p3_checker=p3_checker)
    return {
        "status": "P4_STAGE_RELEASE_VALIDATED",
        "stage": "P4",
        "remaining_cut01_quantity": 10,
        "remaining_cut01_fabrication_review_allowed": True,
        "remaining_cut01_fabrication_authorized": False,
        "downstream_energization_authorized": False,
        "machine_release": "HOLD",
        "p4_result_sha256": sha(result_path),
        "p4_analyzer_sha256": sha(P4_ANALYZER),
        "p4_revalidation": verified,
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
        result = {"status": "NOT_RUN_OR_REJECTED", "remaining_cut01_fabrication_review_allowed": False,
                  "remaining_cut01_fabrication_authorized": False, "downstream_energization_authorized": False,
                  "machine_release": "HOLD", "reason": str(exc)}; code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output: args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)

if __name__ == "__main__": main()
