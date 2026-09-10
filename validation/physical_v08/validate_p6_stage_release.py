#!/usr/bin/env python3
"""Revalidate a human-reviewed P6 cold-extruder release before P8 entry review."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "validation/physical_v08/analyze_p6_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p6_release_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P6 analyzer")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(value: str, release_path: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path

def require_time(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("P6 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P6 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P6" or release.get("status") != "PASS":
        raise ValueError("P6 physical release is not PASS")
    if release.get("release_scope") != "P6_COLD_EXTRUDER_COMPLETE_P8_ENTRY_ONLY":
        raise ValueError("P6 release scope invalid")
    if release.get("motor_energization_authorized") is not False or release.get("heater_energization_authorized") is not False:
        raise ValueError("P6 release must not authorize motor/heater energization")
    if release.get("machine_release") != "HOLD":
        raise ValueError("P6 machine release must remain HOLD")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P6 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P6 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))
    p5_path = repo_file(release.get("p5_release", ""), path, "P5 release")
    receipt_path = repo_file(release.get("production_receipt", ""), path, "production receipt")
    cold_path = repo_file(release.get("cold_record", ""), path, "P6 cold record")
    result_path = repo_file(release.get("p6_result", ""), path, "P6 result")
    for field, target in (("p5_release_sha256", p5_path), ("production_receipt_sha256", receipt_path),
                          ("cold_record_sha256", cold_path), ("p6_result_sha256", result_path)):
        if release.get(field) != sha(target):
            raise ValueError(field + " mismatch")
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    fresh = authority.evaluate(cold_path, p5_path, receipt_path)
    if saved.get("status") != "NUMERIC_RECORD_CHECK_PASS" or fresh.get("status") != "NUMERIC_RECORD_CHECK_PASS":
        raise ValueError("P6 analyzer result is not PASS")
    if saved.get("p5_release", {}).get("sha256") != fresh.get("p5_release", {}).get("sha256"):
        raise ValueError("P6 P5-release binding drift")
    if saved.get("production_receipt") != fresh.get("production_receipt"):
        raise ValueError("P6 production-receipt binding drift")
    if saved.get("cold_fit", {}).get("record_sha256") != fresh.get("cold_fit", {}).get("record_sha256"):
        raise ValueError("P6 cold-record binding drift")
    for key in ("stage_p6_pass", "hardware_authorization"):
        if saved.get(key) is not False or fresh.get(key) is not False:
            raise ValueError("P6 analyzer authorization semantics drift: " + key)
    if saved.get("action_state") != "HOLD" or fresh.get("action_state") != "HOLD":
        raise ValueError("P6 analyzer action state drift")
    return {
        "status": "P6_STAGE_RELEASE_VALIDATED", "stage": "P6", "p8_entry_prerequisite": True,
        "motor_energization_authorized": False, "heater_energization_authorized": False,
        "machine_release": "HOLD", "p5_release_sha256": sha(p5_path),
        "production_receipt_sha256": sha(receipt_path), "cold_record_sha256": sha(cold_path),        "p6_result_sha256": sha(result_path), "p6_analyzer_sha256": sha(ANALYZER),
        "approved_by": release["approved_by"], "independent_reviewer": release["independent_reviewer"],
        "reviewed_at": release["reviewed_at"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("release", type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = validate(args.release); code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {"status": "NOT_RUN_OR_REJECTED", "p8_entry_prerequisite": False,
                  "motor_energization_authorized": False, "heater_energization_authorized": False,
                  "machine_release": "HOLD", "reason": str(exc)}; code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
