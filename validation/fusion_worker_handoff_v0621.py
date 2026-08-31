#!/usr/bin/env python3
"""Legacy mandatory cases와 LC11 Fusion worker handoff를 실제 입력으로 검증한다."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "fusion_worker/scripts/prepare_run.py"
START = "2026-08-31T00:00:00Z"
SOLVER = "2704.1.53"


def prepare(package: str, case_id: str, study: str, related: str | None = None) -> dict:
    command = [
        sys.executable,
        str(TOOL),
        "--repo-root", str(ROOT),
        "--package-root", package,
        "--case-id", case_id,
        "--study-type", study,
        "--solver-version", SOLVER,
        "--started-utc", START,
        "--dry-run",
    ]
    if related:
        command.extend(["--related-case-id", related])
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def reject(package: str, case_id: str, study: str, expected: str) -> None:
    command = [
        sys.executable,
        str(TOOL),
        "--repo-root", str(ROOT),
        "--package-root", package,
        "--case-id", case_id,
        "--study-type", study,
        "--solver-version", SOLVER,
        "--started-utc", START,
        "--dry-run",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    require(result.returncode != 0 and expected in result.stdout + result.stderr,
            f"invalid handoff accepted: {case_id}/{study}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_schema(manifest: dict) -> None:
    schema = json.loads((ROOT / "fusion_worker/run_manifest.schema.json").read_text())
    required = set(schema["required"])
    require(required <= set(manifest), f"run manifest required fields: {sorted(required - set(manifest))}")
    properties = schema["properties"]
    for field in ("case_id", "source_git_sha", "step_file", "step_sha256",
                  "load_case_manifest_sha256", "model_manifest_sha256", "run_binding_sha256"):
        pattern = properties[field].get("pattern")
        if pattern:
            require(re.fullmatch(pattern, manifest[field]) is not None, f"schema pattern: {field}")
    require(manifest["study_type"] in properties["study_type"]["enum"], "schema study type")
    require(manifest["status"] in properties["status"]["enum"], "schema status")
    require(len(manifest["mesh_levels"]) == len(set(manifest["mesh_levels"])), "unique mesh levels")


def main() -> None:
    mandatory = {
        "LC02": "static_stress",
        "LC04": "static_stress",
        "LC05": "static_stress",
        "LC07": "thermal",
        "LC08": "thermal",
        "LC10": "modal_frequencies",
    }
    legacy_runs = {
        case_id: prepare("exports/fusion_validation", case_id, study)
        for case_id, study in mandatory.items()
    }
    legacy = legacy_runs["LC02"]
    combined = prepare("exports/fusion_validation", "LC08", "thermal_stress", "LC06")
    lc11 = prepare("exports/fusion_validation_v0621", "LC11_FEEDER_ATTACHMENT", "linear_static")
    require(legacy["source_git_sha"] == "93db9533dcaf0655f9bde158d53e6f4df24ebb42", "legacy source SHA")
    require(legacy["step_file"] == "cutter_shaft.step", "legacy STEP")
    require(legacy["mesh_levels"] == ["coarse", "medium", "fine"], "legacy mesh plan")
    require(combined["related_case_bindings"][0]["case_id"] == "LC06", "combined LC08+LC06")
    require(lc11["source_git_sha"] == "e86e436861fd28f4055af1a1b9387bb764a7179b", "LC11 source SHA")
    require(lc11["step_file"] == "geometry/PF-05.step", "LC11 STEP")
    require(lc11["mesh_levels"] == ["coarse", "medium", "fine"], "LC11 mesh plan")
    require(lc11["status"] == "PENDING", "tool must not synthesize solver PASS")
    require(set(legacy_runs) == set(mandatory), "mandatory legacy set")
    for manifest in [*legacy_runs.values(), combined, lc11]:
        validate_schema(manifest)
    reject("exports/fusion_validation", "LC10", "modal", "허용되지 않은 study type")
    reject("exports/fusion_validation", "LC08", "thermal_stress", "LC06 pressure 결박")
    print("FUSION_WORKER_HANDOFF_V0621_PASS cases=LC02,LC04,LC05,LC07,LC08,LC08+LC06,LC10,LC11")


if __name__ == "__main__":
    main()
