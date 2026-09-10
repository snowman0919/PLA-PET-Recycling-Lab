#!/usr/bin/env python3
"""Revalidate a human-reviewed P7 logic-safety release for P8/P9 entry review."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "validation/physical_v08/analyze_p7_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p7_release_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P7 analyzer")
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
        raise ValueError("P7 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P7 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P7" or release.get("status") != "PASS":
        raise ValueError("P7 physical release is not PASS")
    if release.get("release_scope") != "P7_LOGIC_SAFETY_COMPLETE_P8_P9_ENTRY_ONLY":
        raise ValueError("P7 release scope invalid")
    if release.get("motor_energization_authorized") is not False or release.get("heater_energization_authorized") is not False:
        raise ValueError("P7 release must not authorize motor/heater energization")
    if release.get("machine_release") != "HOLD":
        raise ValueError("P7 machine release must remain HOLD")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P7 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P7 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))
    record_path = repo_file(release.get("p7_record", ""), path, "P7 record")
    result_path = repo_file(release.get("p7_result", ""), path, "P7 result")
    if release.get("p7_record_sha256") != sha(record_path):
        raise ValueError("P7 record hash mismatch")
    if release.get("p7_result_sha256") != sha(result_path):
        raise ValueError("P7 result hash mismatch")
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    fresh = authority.evaluate(record_path)
    if saved.get("status") != "NUMERIC_RECORD_CHECK_PASS" or fresh.get("status") != "NUMERIC_RECORD_CHECK_PASS":
        raise ValueError("P7 analyzer result is not PASS")
    if saved.get("record_sha256") != fresh.get("record_sha256") or fresh.get("record_sha256") != sha(record_path):
        raise ValueError("P7 record binding drift")
    if saved.get("source_bindings_sha256") != fresh.get("source_bindings_sha256"):
        raise ValueError("P7 electrical source binding drift")
    for key in ("stage_p7_pass", "motor_energization_authorized", "heater_energization_authorized"):
        if saved.get(key) is not False or fresh.get(key) is not False:
            raise ValueError("P7 analyzer authorization semantics drift: " + key)
    if saved.get("action_state") != "HOLD" or fresh.get("action_state") != "HOLD":
        raise ValueError("P7 analyzer action state drift")
    return {
        "status": "P7_STAGE_RELEASE_VALIDATED",
        "stage": "P7",
        "p8_entry_prerequisite": True,
        "p9_entry_prerequisite": True,
        "motor_energization_authorized": False,
        "heater_energization_authorized": False,
        "machine_release": "HOLD",
        "p7_record_sha256": sha(record_path),        "p7_result_sha256": sha(result_path),
        "p7_analyzer_sha256": sha(ANALYZER),
        "source_bindings_sha256": fresh["source_bindings_sha256"],
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
        result = {"status": "NOT_RUN_OR_REJECTED", "p8_entry_prerequisite": False,
                  "p9_entry_prerequisite": False, "motor_energization_authorized": False,
                  "heater_energization_authorized": False, "machine_release": "HOLD", "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
