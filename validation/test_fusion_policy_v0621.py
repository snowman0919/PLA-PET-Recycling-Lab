#!/usr/bin/env python3
"""Fusion tri-state 정책과 존재하는 잘못된 결과의 fail-closed 동작을 검사한다."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "validation/fusion_release_gate_v0621.py"
LC11_RESULT = ROOT / "exports/fusion_validation_v0621/results/fusion_results.csv"


def invoke(policy: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(suffix=".json") as output:
        return subprocess.run(
            [sys.executable, str(GATE), "--policy", policy, "--output", output.name],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    config = json.loads((ROOT / "validation/fusion_policy_v0.6.2.1.json").read_text())
    require(config["fusion_gate_policy"] == "DEFERRED", "configured policy")
    deferred = invoke("deferred")
    require(deferred.returncode == 0 and "V0621_FUSION_GATE_DEFERRED" in deferred.stdout,
            deferred.stdout + deferred.stderr)
    required = invoke("required")
    completed = invoke("completed")
    require(required.returncode != 0 and "CLI/config Fusion policy 불일치" in required.stdout,
            "required must not override configured policy")
    require(completed.returncode != 0 and "CLI/config Fusion policy 불일치" in completed.stdout,
            "completed must not override configured policy")

    require(not LC11_RESULT.exists(), "mutation fixture가 실제 LC11 결과를 덮어쓸 수 없음")
    try:
        LC11_RESULT.write_text("malformed,stale\n1,2\n")
        invalid = invoke("deferred")
        require(invalid.returncode != 0 and "V0621_FUSION_GATE_FAIL" in invalid.stdout,
                "DEFERRED가 malformed present result를 수락함")
    finally:
        LC11_RESULT.unlink(missing_ok=True)
    print("V0621_FUSION_POLICY_TEST_PASS deferred_not_pass=true malformed_present_rejected=true")


if __name__ == "__main__":
    main()
