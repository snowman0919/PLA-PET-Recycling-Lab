#!/usr/bin/env python3
"""Reject incomplete or unbound Fusion result rows; never synthesise solver values."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: validate_fusion_results.py PACKAGE_ROOT RESULT_CSV")
    package = Path(sys.argv[1]).resolve()
    result_csv = Path(sys.argv[2]).resolve()
    binding = json.loads((package / "run_binding.json").read_text())
    models = {row["file"]: row for row in csv.DictReader((package / "model_manifest.csv").open())}
    rows = list(csv.DictReader(result_csv.open()))
    if not rows:
        raise SystemExit("FUSION_RESULT_FAIL empty result table")
    required = {"run_id", "case_id", "study_type", "source_git_sha", "step_file", "step_sha256", "load_case_manifest_sha256", "metric", "value", "unit", "evidence_file", "evidence_sha256", "status"}
    for index, row in enumerate(rows, start=2):
        missing = sorted(key for key in required if not row.get(key))
        if missing:
            raise SystemExit(f"FUSION_RESULT_FAIL row={index} missing={missing}")
        if row["source_git_sha"] != binding["source_git_sha"] or row["load_case_manifest_sha256"] != binding["load_case_manifest_sha256"]:
            raise SystemExit(f"FUSION_RESULT_FAIL row={index} binding mismatch")
        if row["step_file"] not in models or row["step_sha256"] != models[row["step_file"]]["step_sha256"]:
            raise SystemExit(f"FUSION_RESULT_FAIL row={index} STEP mismatch")
        value = float(row["value"])
        if not math.isfinite(value):
            raise SystemExit(f"FUSION_RESULT_FAIL row={index} non-finite value")
        evidence = result_csv.parent / row["evidence_file"]
        if not evidence.is_file() or digest(evidence) != row["evidence_sha256"]:
            raise SystemExit(f"FUSION_RESULT_FAIL row={index} evidence mismatch")
        if row["status"] not in {"PASS", "FAIL"}:
            raise SystemExit(f"FUSION_RESULT_FAIL row={index} invalid status")
    print(f"FUSION_RESULT_OK rows={len(rows)}")


if __name__ == "__main__":
    main()
