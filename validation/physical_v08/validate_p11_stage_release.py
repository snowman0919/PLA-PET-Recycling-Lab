#!/usr/bin/env python3
"""Revalidate reviewed P11 PET low-feed evidence before P12 entry review."""
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
    spec = importlib.util.spec_from_file_location("ppr_p11_stage_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load material-run analyzer")
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
        raise ValueError("P11 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P11 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P11" or release.get("status") != "PASS":
        raise ValueError("P11 physical release is not PASS")
    if release.get("release_scope") != "P11_PET_LOW_FEED_COMPLETE_P12_ENTRY_ONLY":
        raise ValueError("P11 release scope invalid")
    if release.get("material_feed_authorized") is not False:
        raise ValueError("P11 release must not authorize further material feed")
    if release.get("continuing_power_authority") is not False or release.get("machine_release") != "HOLD":
        raise ValueError("P11 release safety state invalid")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P11 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P11 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))

    p10 = repo_file(release.get("p10_release", ""), path, "P10 release")
    record = repo_file(release.get("p11_record", ""), path, "P11 record")
    result_path = repo_file(release.get("p11_result", ""), path, "P11 result")
    for field, target in (("p10_release_sha256", p10), ("p11_record_sha256", record),
                          ("p11_result_sha256", result_path)):
        if release.get(field) != sha(target):
            raise ValueError(field + " mismatch")

    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    releases = {"p10": p10}
    fresh = authority(record, "P11", releases) if analyzer is not None else authority.evaluate(record, "P11", releases)
    if saved.get("status") != "MATERIAL_RUN_RECORD_CHECK_PASS" or fresh.get("status") != "MATERIAL_RUN_RECORD_CHECK_PASS":
        raise ValueError("P11 analyzer result is not PASS")
    if saved.get("stage") != "P11" or fresh.get("stage") != "P11":
        raise ValueError("P11 analyzer stage drift")
    if saved.get("material") != "PET" or fresh.get("material") != "PET":
        raise ValueError("P11 analyzer material drift")
    if saved.get("record_sha256") != fresh.get("record_sha256") or fresh.get("record_sha256") != sha(record):
        raise ValueError("P11 record binding drift")
    if saved.get("prerequisites") != fresh.get("prerequisites"):
        raise ValueError("P11 prerequisite binding drift")
    if saved.get("profile_source_sha256") != fresh.get("profile_source_sha256"):
        raise ValueError("P11 profile source binding drift")
    for field in ("stage_pass", "next_stage_entry_prerequisite", "material_feed_authorized", "continuing_power_authority"):
        if saved.get(field) is not False or fresh.get(field) is not False:
            raise ValueError("P11 analyzer authorization semantics drift: " + field)
    if saved.get("machine_release") != "HOLD" or fresh.get("machine_release") != "HOLD":
        raise ValueError("P11 analyzer machine-release state drift")
    return {
        "status": "P11_STAGE_RELEASE_VALIDATED",
        "stage": "P11",
        "p12_entry_prerequisite": True,
        "material_feed_authorized": False,
        "continuing_power_authority": False,
        "machine_release": "HOLD",
        "p10_release_sha256": sha(p10),
        "p11_record_sha256": sha(record),
        "p11_result_sha256": sha(result_path),
        "p11_analyzer_sha256": sha(ANALYZER),
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
        result = {"status": "NOT_RUN_OR_REJECTED", "p12_entry_prerequisite": False,
                  "material_feed_authorized": False, "continuing_power_authority": False,
                  "machine_release": "HOLD", "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
