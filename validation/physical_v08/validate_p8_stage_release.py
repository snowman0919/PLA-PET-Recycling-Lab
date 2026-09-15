#!/usr/bin/env python3
"""Revalidate a human-reviewed P8 dry-run release before P9 entry review."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "validation/physical_v08/analyze_p8_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p8_stage_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P8 analyzer")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(value: str, release_path: Path, label: str) -> Path:
    path = Path(value); path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path

def repo_dir(value: str, release_path: Path) -> Path:
    path = Path(value); path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_dir():
        raise ValueError("profile_dir must resolve to a repository directory")
    return path


def require_time(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("P8 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P8 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P8" or release.get("status") != "PASS":
        raise ValueError("P8 physical release is not PASS")
    if release.get("release_scope") != "P8_DRY_RUN_COMPLETE_P9_ENTRY_ONLY":
        raise ValueError("P8 release scope invalid")
    if release.get("heater_energization_authorized") is not False or release.get("machine_release") != "HOLD":
        raise ValueError("P8 release safety state invalid")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P8 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P8 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))

    p3 = repo_file(release.get("p3_release", ""), path, "P3 release")
    p6 = repo_file(release.get("p6_release", ""), path, "P6 release")
    p7 = repo_file(release.get("p7_release", ""), path, "P7 release")
    tach = repo_file(release.get("tach_calibration", ""), path, "tach calibration")
    install = repo_file(release.get("firmware_installation", ""), path, "firmware installation")
    record = repo_file(release.get("p8_record", ""), path, "P8 record")
    result_path = repo_file(release.get("p8_result", ""), path, "P8 result")
    profile = repo_dir(release.get("profile_dir", ""), path)
    manifest = profile / "manifest.json"
    if not manifest.is_file():
        raise ValueError("P8 profile manifest missing")
    bindings = {
        "p3_release_sha256": p3, "p6_release_sha256": p6, "p7_release_sha256": p7,
        "tach_calibration_sha256": tach, "firmware_installation_sha256": install,
        "p8_record_sha256": record, "p8_result_sha256": result_path,
        "profile_manifest_sha256": manifest,
    }
    for field, target in bindings.items():
        if release.get(field) != sha(target):
            raise ValueError(field + " mismatch")

    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    fresh = authority(record, p3, p6, p7, profile, tach, install) if analyzer is not None else authority.evaluate(record, p3, p6, p7, profile, tach, install)
    if saved.get("status") != "NUMERIC_RECORD_CHECK_PASS" or fresh.get("status") != "NUMERIC_RECORD_CHECK_PASS":
        raise ValueError("P8 analyzer result is not PASS")
    if saved.get("record_sha256") != fresh.get("record_sha256") or fresh.get("record_sha256") != sha(record):
        raise ValueError("P8 record binding drift")
    if saved.get("source_bindings_sha256") != fresh.get("source_bindings_sha256"):
        raise ValueError("P8 source binding drift")
    if saved.get("prerequisites") != fresh.get("prerequisites"):
        raise ValueError("P8 prerequisite binding drift")
    for key in ("stage_p8_pass", "hardware_authorization", "heater_energization_authorized"):
        if saved.get(key) is not False or fresh.get(key) is not False:
            raise ValueError("P8 analyzer authorization semantics drift: " + key)
    if saved.get("machine_release") != "HOLD" or fresh.get("machine_release") != "HOLD":
        raise ValueError("P8 analyzer machine-release state drift")
    return {
        "status": "P8_STAGE_RELEASE_VALIDATED", "stage": "P8", "p9_entry_prerequisite": True,
        "heater_energization_authorized": False, "machine_release": "HOLD",
        "p3_release_sha256": sha(p3), "p6_release_sha256": sha(p6), "p7_release_sha256": sha(p7),
        "profile_manifest_sha256": sha(manifest), "tach_calibration_sha256": sha(tach),
        "firmware_installation_sha256": sha(install), "p8_record_sha256": sha(record),
        "p8_result_sha256": sha(result_path), "p8_analyzer_sha256": sha(ANALYZER),
        "approved_by": release["approved_by"], "independent_reviewer": release["independent_reviewer"],
        "reviewed_at": release["reviewed_at"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("release", type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = validate(args.release); code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {"status": "NOT_RUN_OR_REJECTED", "p9_entry_prerequisite": False,
                  "heater_energization_authorized": False, "machine_release": "HOLD", "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
