#!/usr/bin/env python3
"""Revalidate reviewed P10 PLA low-feed evidence before P11 entry review."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "validation/physical_v08/analyze_material_run.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p10_stage_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load material-run analyzer")
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


def require_time(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("P10 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P10 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P10" or release.get("status") != "PASS":
        raise ValueError("P10 physical release is not PASS")
    if release.get("release_scope") != "P10_PLA_LOW_FEED_COMPLETE_P11_ENTRY_ONLY":
        raise ValueError("P10 release scope invalid")
    if release.get("material_feed_authorized") is not False:
        raise ValueError("P10 release must not authorize further material feed")
    if release.get("continuing_power_authority") is not False or release.get("machine_release") != "HOLD":
        raise ValueError("P10 release safety state invalid")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P10 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P10 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))

    p4 = repo_file(release.get("p4_release", ""), path, "P4 release")
    p6 = repo_file(release.get("p6_release", ""), path, "P6 release")
    p8 = repo_file(release.get("p8_release", ""), path, "P8 release")
    p9 = repo_file(release.get("p9_release", ""), path, "P9 release")
    record = repo_file(release.get("p10_record", ""), path, "P10 record")
    result_path = repo_file(release.get("p10_result", ""), path, "P10 result")
    bindings = {
        "p4_release_sha256": p4,
        "p6_release_sha256": p6,
        "p8_release_sha256": p8,
        "p9_release_sha256": p9,
        "p10_record_sha256": record,
        "p10_result_sha256": result_path,
    }
    for field, target in bindings.items():
        if release.get(field) != sha(target):
            raise ValueError(field + " mismatch")

    releases = {"p4": p4, "p6": p6, "p8": p8, "p9": p9, "p10": None}
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    fresh = authority(record, "P10", releases) if analyzer is not None else authority.evaluate(record, "P10", releases)
    if saved.get("status") != "MATERIAL_RUN_RECORD_CHECK_PASS" or fresh.get("status") != "MATERIAL_RUN_RECORD_CHECK_PASS":
        raise ValueError("P10 analyzer result is not PASS")
    if saved.get("stage") != "P10" or fresh.get("stage") != "P10":
        raise ValueError("P10 analyzer stage drift")
    if saved.get("record_sha256") != fresh.get("record_sha256") or fresh.get("record_sha256") != sha(record):
        raise ValueError("P10 record binding drift")
    if saved.get("prerequisites") != fresh.get("prerequisites"):
        raise ValueError("P10 prerequisite binding drift")
    if saved.get("profile_source_sha256") != fresh.get("profile_source_sha256"):
        raise ValueError("P10 profile source binding drift")
    for field in ("stage_pass", "next_stage_entry_prerequisite", "material_feed_authorized", "continuing_power_authority"):
        if saved.get(field) is not False or fresh.get(field) is not False:
            raise ValueError("P10 analyzer authorization semantics drift: " + field)
    if saved.get("machine_release") != "HOLD" or fresh.get("machine_release") != "HOLD":
        raise ValueError("P10 analyzer machine-release state drift")
    return {
        "status": "P10_STAGE_RELEASE_VALIDATED",
        "stage": "P10",
        "p11_entry_prerequisite": True,
        "material_feed_authorized": False,
        "continuing_power_authority": False,
        "machine_release": "HOLD",
        "p4_release_sha256": sha(p4),
        "p6_release_sha256": sha(p6),
        "p8_release_sha256": sha(p8),
        "p9_release_sha256": sha(p9),
        "p10_record_sha256": sha(record),
        "p10_result_sha256": sha(result_path),
        "p10_analyzer_sha256": sha(ANALYZER),
        "approved_by": release["approved_by"],
        "independent_reviewer": release["independent_reviewer"],
        "reviewed_at": release["reviewed_at"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("release", type=Path); ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = validate(args.release); code = 0
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {
            "status": "NOT_RUN_OR_REJECTED",
            "p11_entry_prerequisite": False,
            "material_feed_authorized": False,
            "continuing_power_authority": False,
            "machine_release": "HOLD",
            "reason": str(exc),
        }
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
