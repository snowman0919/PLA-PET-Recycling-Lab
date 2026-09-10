#!/usr/bin/env python3
"""Revalidate a reviewed P9 empty-hot-zone release before P10 entry review."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "validation/physical_v08/analyze_p9_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p9_stage_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P9 analyzer")
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
        raise ValueError("P9 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P9 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P9" or release.get("status") != "PASS":
        raise ValueError("P9 physical release is not PASS")
    if release.get("release_scope") != "P9_EMPTY_HOT_ZONE_COMPLETE_P10_ENTRY_ONLY":
        raise ValueError("P9 release scope invalid")
    if release.get("material_feed_authorized") is not False:
        raise ValueError("P9 release must not authorize material feed")
    if release.get("continuing_power_authority") is not False:
        raise ValueError("P9 release must not grant continuing power authority")
    if release.get("machine_release") != "HOLD":
        raise ValueError("P9 machine release must remain HOLD")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P9 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P9 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))

    p7 = repo_file(release.get("p7_release", ""), path, "P7 release")
    p8 = repo_file(release.get("p8_release", ""), path, "P8 release")
    receipt = repo_file(release.get("p9_receipt", ""), path, "P9 receipt")
    thermal = repo_file(release.get("p9_thermal_record", ""), path, "P9 thermal record")
    safety = repo_file(release.get("p9_safety_record", ""), path, "P9 safety record")
    result_path = repo_file(release.get("p9_result", ""), path, "P9 result")
    bindings = {
        "p7_release_sha256": p7,
        "p8_release_sha256": p8,
        "p9_receipt_sha256": receipt,
        "p9_thermal_record_sha256": thermal,
        "p9_safety_record_sha256": safety,
        "p9_result_sha256": result_path,
    }
    for field, target in bindings.items():
        if release.get(field) != sha(target):
            raise ValueError(field + " mismatch")

    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    fresh = authority(thermal, safety, p7, p8, receipt) if analyzer is not None else authority.evaluate(thermal, safety, p7, p8, receipt)
    if saved.get("status") != "P9_RECORD_CHECK_PASS" or fresh.get("status") != "P9_RECORD_CHECK_PASS":
        raise ValueError("P9 analyzer result is not PASS")
    for field, target in (("thermal_record_sha256", thermal), ("safety_record_sha256", safety)):
        if saved.get(field) != fresh.get(field) or fresh.get(field) != sha(target):
            raise ValueError("P9 record binding drift: " + field)
    if saved.get("source_bindings_sha256") != fresh.get("source_bindings_sha256"):
        raise ValueError("P9 source binding drift")
    if saved.get("prerequisites") != fresh.get("prerequisites"):
        raise ValueError("P9 prerequisite binding drift")
    for field in ("stage_p9_pass", "p10_entry_prerequisite", "material_feed_authorized", "continuing_power_authority"):
        if saved.get(field) is not False or fresh.get(field) is not False:
            raise ValueError("P9 analyzer authorization semantics drift: " + field)
    if saved.get("machine_release") != "HOLD" or fresh.get("machine_release") != "HOLD":
        raise ValueError("P9 analyzer machine-release state drift")
    return {
        "status": "P9_STAGE_RELEASE_VALIDATED",
        "stage": "P9",
        "p10_entry_prerequisite": True,
        "material_feed_authorized": False,
        "continuing_power_authority": False,
        "machine_release": "HOLD",
        "p7_release_sha256": sha(p7),
        "p8_release_sha256": sha(p8),
        "p9_receipt_sha256": sha(receipt),
        "p9_thermal_record_sha256": sha(thermal),
        "p9_safety_record_sha256": sha(safety),
        "p9_result_sha256": sha(result_path),
        "p9_analyzer_sha256": sha(ANALYZER),
        "approved_by": release["approved_by"],
        "independent_reviewer": release["independent_reviewer"],
        "reviewed_at": release["reviewed_at"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("release", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = validate(args.release)
        code = 0
    except (ValueError, KeyError, FileNotFoundError, json.JSONDecodeError) as exc:
        result = {
            "status": "NOT_RUN_OR_REJECTED",
            "p10_entry_prerequisite": False,
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
