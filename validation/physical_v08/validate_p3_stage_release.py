#!/usr/bin/env python3
"""Validate a human-reviewed P3 stage-release record before P4 may consume it.

This validator does not create, sign, or approve a release. It verifies that a
manually completed release is bound to exact P3 packet/report files and that the
current authoritative inspector still accepts the underlying P3 evidence.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSPECTION = ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py"
REQUIRED_DOMAINS = ("receipt", "current_calibration", "protection_pin")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inspection():
    spec = importlib.util.spec_from_file_location("ppr_p3_stage_inspection", INSPECTION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load authoritative GGM inspector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inside(path_value: str, release_path: Path, root: Path, label: str) -> Path:
    path = Path(path_value)
    path = path if path.is_absolute() else (release_path.parent / path)
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(label + " must resolve to an existing repository file")
    return path


def timestamp(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("missing " + field)
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(field + " must include timezone")


def validate(path: Path, root: Path = ROOT, inspector=None) -> dict:
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("P3 stage release must be an existing repository file")
    release = json.loads(path.read_text(encoding="utf-8"))
    if release.get("stage") != "P3" or release.get("status") != "PASS":
        raise ValueError("P3 physical release is not PASS")
    if release.get("release_scope") != "P3_COMPLETE_P4_ENTRY_ONLY":
        raise ValueError("P3 release scope invalid")
    if release.get("p4_energization_authorized") is not False or release.get("machine_release") != "HOLD":
        raise ValueError("P3 stage release must not authorize P4 energization or machine release")
    for field in ("approved_by", "independent_reviewer"):
        if not isinstance(release.get(field), str) or not release[field].strip():
            raise ValueError("P3 release missing " + field)
    if release["approved_by"].strip() == release["independent_reviewer"].strip():
        raise ValueError("P3 release requires an independent reviewer")
    timestamp(release.get("reviewed_at"), "reviewed_at")

    packet_path = inside(release.get("inspection_packet", ""), path, root, "inspection packet")
    report_path = inside(release.get("inspection_report", ""), path, root, "inspection report")
    if release.get("inspection_packet_sha256") != sha(packet_path):
        raise ValueError("P3 inspection packet hash mismatch")
    if release.get("inspection_report_sha256") != sha(report_path):
        raise ValueError("P3 inspection report hash mismatch")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    packet_canonical_sha = hashlib.sha256(json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    current_engine_sha = sha(INSPECTION)
    if packet.get("record_status") != "P3_RECORDS_COMPILED_NOT_STAGE_RELEASE":
        raise ValueError("P3 packet was not built by the field-record compiler")
    if packet.get("p3_preflight", {}).get("status") != "PREPOWER_RECORD_CHECK_PASS":
        raise ValueError("P3 packet lacks bound preflight PASS")
    if saved.get("physical_test_executed_by_this_tool") is not False or saved.get("hardware_authorization") != "NOT_GRANTED" or saved.get("machine_release") != "HOLD":
        raise ValueError("saved P3 inspection report has invalid safety semantics")
    if saved.get("input_physical_authorization_present") is not True:
        raise ValueError("saved P3 inspection report was not evaluated under the recorded physical-action authorization")
    if saved.get("input_packet_canonical_sha256") != packet_canonical_sha:
        raise ValueError("saved P3 inspection report is not bound to the exact inspection packet")
    if saved.get("inspection_engine_sha256") != current_engine_sha:
        raise ValueError("saved P3 inspection report was produced by a different inspector revision")
    if saved.get("p3_preflight", {}).get("status") != "NUMERIC_RECORD_CHECK_PASS":
        raise ValueError("saved P3 inspection report preflight is not PASS")
    for domain in REQUIRED_DOMAINS:
        if saved.get("domains", {}).get(domain, {}).get("status") != "NUMERIC_RECORD_CHECK_PASS":
            raise ValueError("saved P3 inspection domain is not PASS: " + domain)

    authority = inspector or load_inspection()
    fresh = authority.inspect(packet)
    if fresh.get("p3_preflight", {}).get("status") != "NUMERIC_RECORD_CHECK_PASS":
        raise ValueError("current inspector rejects P3 preflight")
    for domain in REQUIRED_DOMAINS:
        if fresh.get("domains", {}).get(domain, {}).get("status") != "NUMERIC_RECORD_CHECK_PASS":
            raise ValueError("current inspector rejects P3 domain: " + domain)
    if fresh.get("machine_release") != "HOLD" or fresh.get("hardware_authorization") != "NOT_GRANTED":
        raise ValueError("current inspector safety semantics drift")
    if fresh.get("input_packet_canonical_sha256") != packet_canonical_sha or fresh.get("inspection_engine_sha256") != current_engine_sha:
        raise ValueError("current inspector provenance binding drift")
    if fresh.get("input_physical_authorization_present") is not True:
        raise ValueError("current inspector no longer sees the physical-action authorization used for P3")

    return {
        "status": "P3_STAGE_RELEASE_VALIDATED",
        "stage": "P3",
        "p4_entry_prerequisite": True,
        "p4_energization_authorized": False,
        "machine_release": "HOLD",
        "inspection_packet_sha256": sha(packet_path),
        "inspection_packet_canonical_sha256": packet_canonical_sha,
        "inspection_report_sha256": sha(report_path),
        "inspection_engine_sha256": current_engine_sha,
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
        result = {"status": "NOT_RUN_OR_REJECTED", "p4_entry_prerequisite": False,
                  "p4_energization_authorized": False, "machine_release": "HOLD", "reason": str(exc)}
        code = 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
