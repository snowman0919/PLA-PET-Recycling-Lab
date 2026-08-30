#!/usr/bin/env python3
"""Reject post-regeneration drift in every manifested artifact."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF_PATH = "validation/results/artifact_reproducibility.json"
sys.path.insert(0, str(ROOT / "artifacts"))
from manifest_lib import artifact_record, collect_paths  # noqa: E402


def comparable(record):
    return {key: record.get(key) for key in ("hash_mode", "normalized_bytes", "sha256")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="write the first deterministic result before rebuilding the manifest",
    )
    args = parser.parse_args()
    output = ROOT / "validation/results/artifact_reproducibility.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    # The result is itself manifested.  Seed only the first bootstrap so the
    # reported count already includes the gate record and remains a fixed point.
    if args.bootstrap and not output.exists():
        output.write_text("{}\n")
    current = {record["path"]: record for record in (artifact_record(path, ROOT) for path in collect_paths(ROOT))}
    mismatches = []
    if not args.bootstrap:
        baseline_path = ROOT / "artifacts/manifest.json"
        baseline = json.loads(baseline_path.read_text())
        expected = {record["path"]: record for record in baseline["artifacts"]}
        for path in sorted(set(expected) | set(current)):
            # The gate rewrites its own PASS/FAIL evidence.  Excluding only that
            # self-record from comparison lets a repaired tree recover after a
            # prior FAIL; test_release still requires the final PASS record and
            # exact manifest count.
            if path == SELF_PATH:
                continue
            if path not in expected:
                mismatches.append({"path": path, "reason": "UNMANIFESTED_CURRENT_FILE"})
            elif path not in current:
                mismatches.append({"path": path, "reason": "MISSING_CURRENT_FILE"})
            elif comparable(expected[path]) != comparable(current[path]):
                mismatches.append({
                    "path": path,
                    "reason": "NORMALIZED_CONTENT_DRIFT",
                    "expected": comparable(expected[path]),
                    "current": comparable(current[path]),
                })
    modes = Counter(record["hash_mode"] for record in current.values())
    result = {
        "revision": "coupled-digital-validation-v0.5",
        "gate": "CLEAN_CLONE_REPRODUCIBILITY",
        "scope": "all manifested decision-relevant artifacts after full regeneration",
        "normalization_policy": {
            "STEP_TEXT_NORMALIZED_V1": "timestamp and OpenCASCADE process-local translator sequence only",
            "FCSTD_DOCUMENT_BREP_V1": "all ZIP members except non-manufacturing *.Shape.Map.txt history map",
            "ZIP_MEMBER_CONTENT_V1": "sorted member names and exact contents; ZIP timestamps excluded",
            "RAW_SHA256_V1": "exact bytes",
        },
        "checked_count": len(current),
        "hash_mode_counts": dict(sorted(modes.items())),
        "mismatches": mismatches,
        "status": "PASS" if not mismatches else "FAIL",
        "physical_state": "PHYSICAL_VALIDATION_PENDING",
    }
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if mismatches:
        print(json.dumps(mismatches[:20], indent=2))
        raise SystemExit(f"CLEAN_CLONE_REPRODUCIBILITY_FAIL count={len(mismatches)}")
    print(f"CLEAN_CLONE_REPRODUCIBILITY_OK checked={len(current)}")


if __name__ == "__main__":
    main()
