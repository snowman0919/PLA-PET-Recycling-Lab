#!/usr/bin/env python3
"""v0.6.2.1 기술 release와 명시적 Fusion tri-state policy gate."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], token: str) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or token not in output:
        print(output, end="")
        raise SystemExit(f"V0621_GATE_FAIL expected={token} command={' '.join(command)}")
    print(f"PASS {token}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fusion-policy", choices=("required", "deferred", "completed"), required=True,
        help="validation/fusion_policy_v0.6.2.1.json과 일치해야 하는 명시적 정책",
    )
    args = parser.parse_args()
    py = sys.executable
    checks = [
        ([py, "validation/configuration_control_v0.6.2.1.py"], "V0621_CONFIGURATION_CONTROL_OK"),
        ([py, "validation/run_v062.py"], "V062_CI_LIGHT_OK"),
        ([py, "control/generate_tach_contract.py", "--check"], "TACH_CONTRACT_SYNC_OK"),
        ([py, "validation/hardware_adapter_v0621.py"], "HOST_HARDWARE_ADAPTER_SIMULATION_PASS"),
        ([py, "validation/hardware_adapter_e2e_v0621.py"], "HARDWARE_ADAPTER_E2E_V0621_PASS"),
        ([py, "validation/test_budget_policy_v0.6.2.1.py"], "V0621_PRICE_INFORMATIONAL_MUTATION_PASS"),
        ([py, "analysis/process_feed/verify_process_lane.py"], "PROCESS_MECHANICAL_LANE_PASS"),
        ([py, "analysis/process_risk/cooling_degradation_v0.6.2.1.py"], "COOLING_DEGRADATION_V0621_PASS"),
        ([py, "simulation/openmodelica/postprocess/validate_v0621_shadow.py", "--evidence-only"],
         "V0621_SHADOW_COMPACT_EVIDENCE_PASS"),
        ([py, "validation/fusion_worker_handoff_v0621.py"],
         "FUSION_WORKER_HANDOFF_V0621_PASS"),
        ([py, "-m", "unittest", "analysis/cross_solver/test_import_fusion_results.py"],
         "OK"),
        ([py, "validation/test_fusion_policy_v0621.py"],
         "V0621_FUSION_POLICY_TEST_PASS"),
        ([py, "validation/v0621_mutation_tests.py"], "V0621_MUTATION_GATE_PASS"),
    ]
    for command, token in checks:
        run(command, token)

    fusion_command = [py, "validation/fusion_release_gate_v0621.py", "--policy", args.fusion_policy]
    fusion_token = (
        "V0621_FUSION_GATE_DEFERRED"
        if args.fusion_policy == "deferred"
        else "V0621_FUSION_CROSS_SOLVER_GATE_PASS"
    )
    result = subprocess.run(fusion_command, cwd=ROOT, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode or fusion_token not in output:
        print(output, end="")
        raise SystemExit(f"V0621_GATE_FAIL expected={fusion_token} command={' '.join(fusion_command)}")
    if args.fusion_policy == "deferred":
        print("DEFERRED V0621_FUSION_GATE_DEFERRED solver_pass=false")
    else:
        print(f"PASS {fusion_token}")
    run([py, "validation/build_release_metadata_v0621.py"], "V0621_RELEASE_METADATA_OK")
    print(f"V0621_TECHNICAL_CLOSURE_GATE_PASS fusion_policy={args.fusion_policy.upper()}")


if __name__ == "__main__":
    main()
