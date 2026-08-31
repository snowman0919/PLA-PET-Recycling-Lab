#!/usr/bin/env python3
"""v0.6.2.1 기술 preflight 및 Fusion 의존 release gate."""

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
    parser.add_argument("--allow-fusion-pending", action="store_true",
                        help="A-K 기술 preflight만 판정하고 외부 Fusion pending을 허용")
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
        ([py, "validation/v0621_mutation_tests.py"], "V0621_MUTATION_GATE_PASS"),
    ]
    for command, token in checks:
        run(command, token)

    fusion_command = [py, "validation/fusion_release_gate_v0621.py"]
    fusion_token = "V0621_FUSION_CROSS_SOLVER_GATE_PASS"
    if args.allow_fusion_pending:
        fusion_command.append("--allow-pending")
        fusion_token = "V0621_FUSION_EXTERNAL_BLOCKER"
    run(fusion_command, fusion_token)
    if args.allow_fusion_pending:
        print("V0621_TECHNICAL_PREFLIGHT_PASS_RELEASE_UNMET")
        return
    print("V0621_RELEASE_GATE_PASS")


if __name__ == "__main__":
    main()
