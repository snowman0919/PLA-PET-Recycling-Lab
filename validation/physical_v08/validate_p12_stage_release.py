#!/usr/bin/env python3
"""Revalidate reviewed P12 evidence as a physical-validation review candidate."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYZER = ROOT / "validation/physical_v08/analyze_p12_records.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_analyzer():
    spec = importlib.util.spec_from_file_location("ppr_p12_stage_analyzer", ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load P12 analyzer")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def repo_file(value: str, release_path: Path, label: str) -> Path:
    path = Path(value); path = path if path.is_absolute() else release_path.parent / path
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def require_time(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("P12 release missing reviewed_at")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("reviewed_at must include timezone")


def validate(path: Path, analyzer=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("P12 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P12" or release.get("status") != "PASS":
        raise ValueError("P12 physical release is not PASS")
    if release.get("release_scope") != "P12_PHYSICAL_VALIDATION_EVIDENCE_REVIEW_CANDIDATE_ONLY":
        raise ValueError("P12 release scope invalid")
    for field in ("continuing_power_authority", "production_authorized", "safety_certification"):
        if release.get(field) is not False:
            raise ValueError("P12 release must keep " + field + " false")
    if release.get("machine_release") != "HOLD":
        raise ValueError("P12 machine release must remain HOLD")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P12 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P12 release requires an independent reviewer")
    require_time(release.get("reviewed_at"))

    p11 = repo_file(release.get("p11_release", ""), path, "P11 release")
    record = repo_file(release.get("p12_record", ""), path, "P12 record")
    result_path = repo_file(release.get("p12_result", ""), path, "P12 result")
    for field, target in (("p11_release_sha256", p11), ("p12_record_sha256", record),
                          ("p12_result_sha256", result_path)):
        if release.get(field) != sha(target):
            raise ValueError(field + " mismatch")

    saved = json.loads(result_path.read_text(encoding="utf-8"))
    authority = analyzer or load_analyzer()
    fresh = authority(record, p11) if analyzer is not None else authority.evaluate(record, p11)
    if saved.get("status") != "P12_RECORD_CHECK_PASS" or fresh.get("status") != "P12_RECORD_CHECK_PASS":
        raise ValueError("P12 analyzer result is not PASS")
    if saved.get("record_sha256") != fresh.get("record_sha256") or fresh.get("record_sha256") != sha(record):
        raise ValueError("P12 record binding drift")
    if saved.get("p11_release_sha256") != fresh.get("p11_release_sha256") or fresh.get("p11_release_sha256") != sha(p11):
        raise ValueError("P12 P11-release binding drift")
    if saved.get("source_lot_id") != fresh.get("source_lot_id"):
        raise ValueError("P12 source-lot binding drift")
    if saved.get("source_bindings_sha256") != fresh.get("source_bindings_sha256"):
        raise ValueError("P12 design-source binding drift")
    for field in ("stage_p12_pass", "physical_validation_complete_candidate", "continuing_power_authority",
                  "production_authorized", "safety_certification"):
        if saved.get(field) is not False or fresh.get(field) is not False:
            raise ValueError("P12 analyzer authorization semantics drift: " + field)
    if saved.get("machine_release") != "HOLD" or fresh.get("machine_release") != "HOLD":
        raise ValueError("P12 analyzer machine-release state drift")
    return {
        "status": "P12_STAGE_RELEASE_VALIDATED",
        "stage": "P12",
        "physical_validation_complete_candidate": True,
        "evidence_package_review_allowed": True,
        "continuing_power_authority": False,
        "production_authorized": False,
        "safety_certification": False,
        "machine_release": "HOLD",
        "source_lot_id": fresh["source_lot_id"],
        "p11_release_sha256": sha(p11),
        "p12_record_sha256": sha(record),
        "p12_result_sha256": sha(result_path),
        "p12_analyzer_sha256": sha(ANALYZER),
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
        result = {"status": "NOT_RUN_OR_REJECTED", "physical_validation_complete_candidate": False,
                  "evidence_package_review_allowed": False, "continuing_power_authority": False,
                  "production_authorized": False, "safety_certification": False,
                  "machine_release": "HOLD", "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"; print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
