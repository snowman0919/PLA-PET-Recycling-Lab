#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "v0.6.1-safety-orchestration-baseline"
FROZEN = [
    "cad/freecad/compact/geometry.py", "cad/freecad/compact/manufacturing.py",
    "cad/parameters/baseline.json", "exports/fusion_validation/geometry",
    "exports/fusion_validation/loads", "exports/fusion_validation/load_case_manifest.csv",
    "exports/fusion_validation/model_manifest.csv", "exports/fusion_validation/materials.csv",
    "exports/fusion_validation/contact_pairs.csv", "exports/fusion_validation/constraints.csv",
    "exports/fusion_validation/run_binding.json", "analysis/load_cases/openmodelica_dynamic_envelope.json",
    "analysis/structural/generated",
]
ALLOWED = {"FUSION_NEUTRAL", "FUSION_RESULT_CONSUMER"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE, "--", *FROZEN], cwd=ROOT,
        check=True, text=True, capture_output=True,
    ).stdout.splitlines()
    if changed:
        raise AssertionError("frozen Fusion baseline changed: " + ", ".join(changed))
    binding = json.loads((ROOT / "exports/fusion_validation/run_binding.json").read_text())
    expected = {
        "engineering_source_sha": "93db9533dcaf0655f9bde158d53e6f4df24ebb42",
        "load_case_manifest_sha256": "3a10603d30bbd177f6e2d065273afa8388c2c8a4a33378f6688dd68cb5b305a6",
        "model_manifest_sha256": "39d83ed1cbcf353909b28cda1e43e4268b131cdfee0201469795a3011c96c40c",
        "openmodelica_envelope_sha256": "4f9735292ab3046c40bc173c4e22611fc35ae475a6d087b674cd7882ea7aa1ed",
    }
    for key, value in expected.items():
        if binding.get(key) != value:
            raise AssertionError(f"run binding drift: {key}")
    if sha(ROOT / "exports/fusion_validation/load_case_manifest.csv") != expected["load_case_manifest_sha256"]:
        raise AssertionError("load case manifest hash drift")
    if sha(ROOT / "exports/fusion_validation/model_manifest.csv") != expected["model_manifest_sha256"]:
        raise AssertionError("model manifest hash drift")
    if sha(ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json") != expected["openmodelica_envelope_sha256"]:
        raise AssertionError("frozen dynamic envelope hash drift")
    path = ROOT / "analysis/fusion_delta_queue/change_classification.csv"
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"change_id", "path", "summary", "classification", "fusion_cases_affected",
                "reason", "applied_to_v062", "requires_fusion_rerun", "status"}
    if not rows or set(rows[0]) != required:
        raise AssertionError("delta classification schema drift")
    if any(row["classification"] not in ALLOWED or row["requires_fusion_rerun"] != "false" for row in rows):
        raise AssertionError("invalidating change was applied during frozen solve")
    payload = {
        "revision": "parallel-actuation-hardening-v0.6.2", "status": "PASS",
        "fusion_input_delta": "NONE", "frozen_paths_changed": [],
        "classification_count": len(rows), "binding": expected,
    }
    result = ROOT / "validation/results/fusion_delta_classification.json"
    result.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print("FUSION_DELTA_CLASSIFICATION_OK FUSION_INPUT_DELTA=NONE")


if __name__ == "__main__":
    main()
