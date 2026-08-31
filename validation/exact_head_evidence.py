#!/usr/bin/env python3
"""현재 체크아웃에서 생성된 검증 증거를 정확한 Git HEAD에 결속한다.

이 파일은 저장된 과거 PASS를 재사용하지 않는다. 호출 시점의 HEAD, 작업 트리,
필수 결과 파일을 다시 읽고 CI 런타임 증거를 ``validation/evidence``에 쓴다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "validation/evidence/exact_head_evidence.json"
REVISION = "parallel-actuation-hardening-v0.6.2"
BASELINE_REVISION = "safety-orchestration-closure-v0.6.1"
EXPECTED_MUTATIONS = {
    "residual_subsystem_latch": "IDLE_WITH_SUBSYSTEM_LATCH",
    "failed_start_in_shredding": "SHREDDING_WITH_FAILED_START",
    "pet_active_without_purge": "PENDING_MATERIAL_ACTIVE_WITHOUT_PURGE",
    "cooling_feedback_absent": "COOLING_FEEDBACK_LOSS_NOT_CONTAINED",
    "dancer_hard_limit_crossing": "NOMINAL_JAM_CROSSED_HARD_STOP",
    "invalid_strand_spool": "INELIGIBLE_STRAND_TO_PRODUCTION_SPOOL",
    "one_sample_recovery": "SPOOL_ELIGIBILITY_WITHOUT_REQUALIFICATION",
    "purge_over_500w": "PURGE_POWER_ENVELOPE_EXCEEDED",
    "estop_clear_implicit_restart": "ESTOP_CLEAR_IMPLICIT_RESTART",
    "stale_fusion_binding": "STALE_FUSION_BINDING_ACCEPTED",
    "stale_purge_feed_approval": "STALE_PURGE_FEED_APPROVAL_REUSE_ALLOWED",
    "startup_probe_heater_before_feedback_proof": "COOLING_STARTUP_HAZARDOUS_OUTPUT_BEFORE_PROOF",
    "purge_motion_before_waste_confirmation": "PURGE_MOTION_BEFORE_WASTE_CONFIRMATION",
    "production_invariant_false": "PRODUCTION_INVARIANT_FALSE",
}
EXPECTED_V062_MUTATIONS = {
    "puller_saturation_hardcoded_false", "fan2_channel_ignored",
    "purge_commanded_revolutions", "heater_feedback_removed",
    "spooler_fixed_pwm", "traverse_time_reversal", "fusion_binding_removed",
}
REQUIRED_RUNTIME_SCENARIOS = {
    "calibration_readiness_phase_gates", "purge_cooling_loss_containment",
    "preheat_cooling_loss_containment", "cooldown_cooling_loss_containment",
    "cooldown_to_idle_completion", "general_fault_valid_cooling",
    "stale_purge_feed_approval_rejected",
    "preheat_fan_first_startup_proof", "purge_fan_first_startup_proof",
    "startup_probe_feedback_absent_containment", "cooling_fault_clear_then_reprobe",
    "purge_cooling_fault_clear_then_reprobe", "cooldown_cooling_fault_clear_then_reprobe",
    "purge_ready_waits_ordered_confirmations", "phase_specific_readiness_ui",
    "purge_panel_abort_all_stages",
    "puller_tach_startup_grace_and_loss", "extrusion_quality_same_cycle_interlocks",
    "requalification_invalid_quality_resets_counter", "manual_rethread_fresh_invalid_rejected",
    "purge_completion_fresh_fault_preflight",
}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=check
    )


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise AssertionError(f"필수 런타임 증거 없음: {path.relative_to(ROOT)}")
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_current_hashes(label: str, hashes: dict[str, str]) -> None:
    if not hashes:
        raise AssertionError(f"{label} source hash 증거 없음")
    for relative, expected in hashes.items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"{label} 저장 증거가 현재 파일과 불일치: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("CI-LIGHT", "CI-FULL"), required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="개발 중 진단 전용. release exact-head 증거에는 사용 금지",
    )
    args = parser.parse_args()

    head = git("rev-parse", "HEAD").stdout.strip()
    branch = git("branch", "--show-current").stdout.strip()
    github_sha = os.environ.get("GITHUB_SHA", "")
    if github_sha and github_sha != head:
        raise AssertionError(f"GITHUB_SHA/HEAD 불일치: {github_sha} != {head}")

    status_lines = [
        line
        for line in git("status", "--porcelain=v1", "--untracked-files=all").stdout.splitlines()
        if " validation/evidence/exact_head_evidence.json" not in line
    ]
    if status_lines and not args.allow_dirty:
        raise AssertionError("exact-head 작업 트리가 깨끗하지 않음: " + ", ".join(status_lines[:20]))

    contract = load_json(ROOT / "control/process_contract.json")
    runtime = load_json(ROOT / "validation/results/runtime_supervisor.json")
    controller = load_json(ROOT / "validation/results/controller_contract.json")
    orchestration = load_json(ROOT / "validation/results/orchestration_contract.json")
    red_team = load_json(ROOT / "validation/results/red_team_orchestration.json")
    arduino = load_json(ROOT / "validation/results/arduino_mega_compile.json")
    actuation = load_json(ROOT / "validation/results/v062_actuation_contract.json")
    v062_mutation = load_json(ROOT / "validation/results/v062_mutation_tests.json")
    shadow = load_json(ROOT / "simulation/openmodelica/results_v0.6.2/summary.json")
    if contract.get("revision") != BASELINE_REVISION:
        raise AssertionError("process_contract가 동결 v0.6.1 계약이 아님")
    release = contract.get("release", {})
    if release.get("release_state") != "SAFETY_ORCHESTRATION_BASELINE":
        raise AssertionError("process_contract release state 불일치")
    for label, payload in {
        "runtime_supervisor": runtime, "arduino_mega_compile": arduino,
        "v062_actuation_contract": actuation, "v062_mutation_tests": v062_mutation,
        "v062_shadow": shadow,
    }.items():
        if payload.get("revision") != REVISION or payload.get("status") != "PASS":
            raise AssertionError(f"{label}가 현재 v0.6.2 PASS 증거가 아님")
    for label, payload in {
        "controller_contract": controller,
        "orchestration_contract": orchestration,
        "red_team_orchestration": red_team,
    }.items():
        if payload.get("revision") != BASELINE_REVISION or payload.get("status") != "PASS":
            raise AssertionError(f"{label}가 동결 v0.6.1 PASS 증거가 아님")

    require_current_hashes("runtime production", runtime.get("production_sources", {}))
    require_current_hashes("runtime headers", runtime.get("production_headers", {}))
    require_current_hashes("runtime validators", runtime.get("validator_sources", {}))
    require_current_hashes("controller validators", controller.get("validator_sources", {}))
    require_current_hashes("orchestration validators", orchestration.get("validator_sources", {}))
    require_current_hashes("orchestration production audit", orchestration.get("production_audit_sources", {}))
    require_current_hashes("red-team sources", red_team.get("source_hashes", {}))
    require_current_hashes("Arduino sources", arduino.get("source_hashes", {}))
    require_current_hashes("Arduino validator", arduino.get("validator_hashes", {}))
    harness = ROOT / "validation/runtime_supervisor_harness.cpp"
    if runtime.get("harness_sha256") != sha256(harness):
        raise AssertionError("runtime harness 저장 증거가 현재 파일과 불일치")
    trace_events = 0
    for scenario in runtime.get("scenarios", []):
        trace_path = ROOT / scenario.get("trace_file", "")
        if not trace_path.is_file() or scenario.get("sha256") != sha256(trace_path):
            raise AssertionError(f"runtime trace 저장 증거가 현재 파일과 불일치: {trace_path}")
        if scenario.get("status") != "PASS":
            raise AssertionError(f"runtime scenario PASS 아님: {scenario.get('name')}")
        trace_events += scenario.get("event_count", 0)
    scenario_names = {scenario.get("name") for scenario in runtime.get("scenarios", [])}
    if (
        len(runtime.get("scenarios", [])) != runtime.get("scenario_count")
        or trace_events != runtime.get("trace_count")
        or runtime.get("scenario_count", 0) < 43
        or runtime.get("trace_count", 0) < 100
        or runtime.get("invariant_failure_count") != 0
        or runtime.get("purge_revolution_evidence") != "ACTUAL_SCREW_TACH_MEASURED_REVOLUTIONS"
        or runtime.get("purge_operator_sequence") != "approvePurgeFeed_then_independent_waste_path_confirmation"
        or runtime.get("calibration_readiness", {}).get("status") != "PASS"
        or not REQUIRED_RUNTIME_SCENARIOS <= scenario_names
    ):
        raise AssertionError("runtime trace manifest/count/purge evidence 불일치")
    if red_team.get("mutation_count") != len(EXPECTED_MUTATIONS):
        raise AssertionError("red-team 필수 mutation count 불일치")
    if set(red_team.get("mutations", {})) != set(EXPECTED_MUTATIONS) or any(
        value != "FAIL_DETECTED" for value in red_team.get("mutations", {}).values()
    ):
        raise AssertionError("red-team 필수 mutation 결과 불일치")
    for mutation, expected_error in EXPECTED_MUTATIONS.items():
        errors = red_team.get("detected_errors", {}).get(mutation, [])
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"red-team expected error code 누락: {mutation}")
    v062_mutations = v062_mutation.get("mutations", [])
    if (v062_mutation.get("mutation_count") != len(EXPECTED_V062_MUTATIONS) or
            {row.get("mutation") for row in v062_mutations} != EXPECTED_V062_MUTATIONS or
            any(row.get("result") != "PASS" for row in v062_mutations)):
        raise AssertionError("v0.6.2 필수 mutation 결과 불일치")
    if (actuation.get("documented_high_signal_scenarios") != 22 or
            actuation.get("production_runtime_scenarios", 0) < 43 or
            actuation.get("shadow_scenario_count") != 24):
        raise AssertionError("v0.6.2 actuation/high-signal 증거 불일치")
    if arduino.get("fqbn") != "arduino:avr:mega" or arduino.get("target") != "firmware/arduino_mega/arduino_mega.ino":
        raise AssertionError("Arduino compile target/fqbn evidence 불일치")
    process_contract_path = ROOT / "control/process_contract.json"
    fault_contract_path = ROOT / "control/fault_response_contract.json"
    if orchestration.get("process_contract_sha256") != sha256(process_contract_path):
        raise AssertionError("orchestration 결과가 현재 process contract와 불일치")
    if orchestration.get("fault_response_contract_sha256") != sha256(fault_contract_path):
        raise AssertionError("orchestration 결과가 현재 fault contract와 불일치")
    if controller.get("contract_sha256") != sha256(process_contract_path):
        raise AssertionError("controller 결과가 현재 process contract와 불일치")

    manifest_path = ROOT / "artifacts/manifest.json"
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    reproducibility_path = ROOT / "validation/results/artifact_reproducibility.json"
    reproducibility = load_json(reproducibility_path) if reproducibility_path.is_file() else {}
    modelica_path = ROOT / "simulation/openmodelica/results/summary.json"
    modelica = load_json(modelica_path) if modelica_path.is_file() else {}

    if args.stage == "CI-FULL":
        if manifest.get("revision") != BASELINE_REVISION:
            raise AssertionError("CI-FULL frozen artifact manifest revision 불일치")
        if reproducibility.get("revision") != BASELINE_REVISION or reproducibility.get("status") != "PASS":
            raise AssertionError("CI-FULL artifact reproducibility PASS 증거 없음")
        if reproducibility.get("mismatches"):
            raise AssertionError("CI-FULL artifact mismatch가 0이 아님")
        if modelica.get("revision") != BASELINE_REVISION or modelica.get("status") != "PASS":
            raise AssertionError("CI-FULL OpenModelica frozen baseline PASS 증거 없음")
        if shadow.get("scenario_count") != 24 or shadow.get("pass_count") != 24:
            raise AssertionError("CI-FULL OpenModelica v0.6.2 shadow PASS 증거 없음")

    release_evidence = not status_lines
    evidence = {
        "revision": REVISION,
        "frozen_baseline_revision": BASELINE_REVISION,
        "status": "PASS" if release_evidence else "DIAGNOSTIC_DIRTY_NOT_RELEASE_EVIDENCE",
        "stage": args.stage,
        "exact_commit_sha": head,
        "branch": branch,
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID") or None,
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT") or None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_generator_sha256": sha256(Path(__file__).resolve()),
        "workflow_sha256": {
            stage: sha256(ROOT / f".github/workflows/{stage}.yml")
            for stage in ("ci-light", "ci-full")
        },
        "worktree_clean": not status_lines,
        "dirty_paths": status_lines,
        "runtime_trace_count": runtime.get("trace_count", 0),
        "runtime_invariant_failures": runtime.get("invariant_failure_count"),
        "artifact_count": manifest.get("artifact_count") if args.stage == "CI-FULL" else None,
        "artifact_mismatch_count": len(reproducibility.get("mismatches", [])) if args.stage == "CI-FULL" else None,
        "scenario_count": modelica.get("scenario_count") if args.stage == "CI-FULL" else None,
        "shadow_scenario_count": shadow.get("scenario_count") if args.stage == "CI-FULL" else None,
        "gates": {
            "ACTUATION_HARDENING_GATE": "PASS" if release_evidence else "NOT_EVALUATED_DIRTY_WORKTREE",
            "CROSS_SOLVER_GATE": "CROSS_SOLVER_VALIDATION_PENDING",
            "PROCUREMENT_APPROVAL_GATE": "USER_APPROVAL_REQUIRED",
            "COMMISSIONING_GATE": "USER_APPROVAL_REQUIRED",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(f"EXACT_HEAD_{args.stage.replace('-', '_')}_EVIDENCE_OK sha={head}")


if __name__ == "__main__":
    main()
