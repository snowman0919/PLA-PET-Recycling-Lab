#!/usr/bin/env python3
"""Verify the v0.6.2 source freeze and pre-change Fusion evidence record."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "f9fde47359ef84744daf1a9279040c507ef60497"
MAIN = "e6eac810870feb02bf293f55cbdd915ef0c068eb"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def resolve(*refs: str) -> str:
    for ref in refs:
        result = git("rev-parse", "--verify", ref, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    raise AssertionError(f"missing source freeze ref: {refs}")


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def main() -> None:
    lock = json.loads((ROOT / "validation/source_lock_v0.6.2.1.json").read_text())
    assert lock["source_v0.6.2_sha"] == SOURCE
    assert lock["main_sha"] == MAIN
    assert lock["main_is_source_ancestor"] is True
    assert lock["main_merge_result"] == "NOT_REQUIRED_ALREADY_ANCESTOR"
    archive = resolve(
        "refs/heads/archive/parallel-actuation-hardening-v0.6.2",
        "refs/remotes/origin/archive/parallel-actuation-hardening-v0.6.2",
    )
    tag = resolve("refs/tags/parallel-actuation-hardening-v0.6.2^{}")
    assert archive == tag == SOURCE, (archive, tag, SOURCE)
    assert git("merge-base", "--is-ancestor", MAIN, SOURCE, check=False).returncode == 0
    before = {
        "run_binding_sha256": sha256("exports/fusion_validation/run_binding.json"),
        "load_case_manifest_sha256": sha256("exports/fusion_validation/load_case_manifest.csv"),
        "model_manifest_sha256": sha256("exports/fusion_validation/model_manifest.csv"),
        "openmodelica_envelope_sha256": sha256("analysis/load_cases/openmodelica_dynamic_envelope.json"),
    }
    for key, actual in before.items():
        assert lock[key] == actual, f"pre-change Fusion lock drift: {key}"
    binding = json.loads((ROOT / "exports/fusion_validation/run_binding.json").read_text())
    assert lock["fusion_engineering_source_sha"] == binding["engineering_source_sha"]
    assert lock["fusion_result_state_at_lock"] == "PENDING_EXTERNAL_EXECUTION"
    print(f"V0621_CONFIGURATION_CONTROL_OK source={SOURCE[:12]} main={MAIN[:12]}")


if __name__ == "__main__":
    main()
