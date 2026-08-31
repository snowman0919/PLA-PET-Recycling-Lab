#!/usr/bin/env python3
"""v0.6.2.1 검증 결과를 정확한 현재 Git HEAD와 fail-closed로 결속한다."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "validation/evidence/exact_head_evidence_v0.6.2.1.json"
REVISION = "technical-blocker-closure-v0.6.2.1"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(relative: str) -> dict:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"필수 증거 없음: {relative}")
    return json.loads(path.read_text())


def require_hashes(base: Path, hashes: dict[str, str], label: str) -> None:
    if not hashes:
        raise AssertionError(f"{label} source hash 없음")
    for relative, expected in hashes.items():
        path = base / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"{label} hash drift: {relative}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("CI-LIGHT", "CI-FULL"), required=True)
    parser.add_argument("--allow-dirty", action="store_true", help="개발 진단 전용")
    parser.add_argument("--allow-fusion-pending", action="store_true", help="release 증거가 아닌 진단 전용")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    head = git("rev-parse", "HEAD")
    github_sha = os.environ.get("GITHUB_SHA", "")
    if github_sha and github_sha != head:
        raise AssertionError(f"GITHUB_SHA/HEAD 불일치: {github_sha} != {head}")
    excluded = {
        "validation/evidence/exact_head_evidence_v0.6.2.1.json",
        "validation/results/fusion_release_gate_v0.6.2.1.json",
    }
    dirty = []
    for line in git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        path = line[3:]
        if path not in excluded:
            dirty.append(line)
    if dirty and not args.allow_dirty:
        raise AssertionError("exact-head 작업 트리가 깨끗하지 않음: " + ", ".join(dirty[:20]))

    source_lock = load_json("validation/source_lock_v0.6.2.1.json")
    if source_lock.get("source_v0.6.2_sha") != "f9fde47359ef84744daf1a9279040c507ef60497":
        raise AssertionError("v0.6.2 source lock 불일치")
    if source_lock.get("main_merge_result") != "NOT_REQUIRED_ALREADY_ANCESTOR":
        raise AssertionError("main merge 판정 불일치")

    adapter = load_json("validation/results/hardware_adapter_e2e/summary.json")
    if (
        adapter.get("status") != "HOST_SIMULATION_PASS"
        or adapter.get("physical_test_status") != "NOT_RUN"
        or adapter.get("scenario_count") != 37
        or not adapter.get("all_scenarios_passed")
        or not adapter.get("all_scenarios_unique")
    ):
        raise AssertionError("P0-J hardware adapter E2E 증거 불일치")
    trace = ROOT / adapter["trace"]
    if sha256(trace) != adapter.get("trace_sha256"):
        raise AssertionError("P0-J trace hash drift")
    require_hashes(ROOT / "firmware/arduino_mega", adapter.get("source_sha256", {}), "P0-J")

    tach = load_json("validation/results/hardware_adapter_tach/summary.json")
    if tach.get("status") != "HOST_HARDWARE_ADAPTER_SIMULATION_PASS":
        raise AssertionError("P0-A tach adapter PASS 없음")
    if any(
        not row.get("rollover_safe") or row.get("maximum_nominal_relative_error", 1.0) > 0.03
        for row in tach.get("per_channel", {}).values()
    ):
        raise AssertionError("P0-A tach accuracy/rollover 불합격")

    mutation = load_json("validation/results/v0621_mutation_tests.json")
    if (
        mutation.get("status") != "PASS"
        or mutation.get("mutation_count", 0) < 18
        or mutation.get("rejected_mutation_count") != mutation.get("mutation_count")
    ):
        raise AssertionError("v0.6.2.1 mutation 증거 불합격")

    feed = load_json("analysis/process_feed/feed_validation.json")
    recirculation = load_json("analysis/shredder_recirculation/recirculation_validation.json")
    if feed.get("status") != "PASS" or not feed.get("nominal_all_pass"):
        raise AssertionError("P0-H feed virtual validation 불합격")
    if recirculation.get("status") != "PASS":
        raise AssertionError("P0-G recirculation virtual validation 불합격")

    shadow = load_json("simulation/openmodelica/results_v0.6.2.1/summary.json")
    solver = load_json("simulation/openmodelica/results_v0.6.2.1/solver_execution.json")
    if (
        shadow.get("revision") != REVISION
        or shadow.get("status") != "PASS"
        or shadow.get("scenario_count") != 24
        or shadow.get("pass_count") != 24
        or solver.get("validation_status") != "PASS"
        or solver.get("result_file_count") != 24
        or len(solver.get("result_sha256", {})) != 24
    ):
        raise AssertionError("P0-K OpenModelica 실행 증거 불합격")

    budget = load_json("bom/budget_policy.json")
    if (
        budget.get("price_status") != "INFORMATIONAL"
        or budget.get("price_release_blocking") is not False
        or budget.get("technical_release_blocked") is not False
        or budget.get("procurement_approval_gate") != "USER_APPROVAL_REQUIRED"
    ):
        raise AssertionError("가격 비차단 정책 불일치")

    with (ROOT / "validation/blocker_closure_matrix.csv").open(newline="") as handle:
        blockers = {row["blocker_id"]: row for row in csv.DictReader(handle)}
    if set(blockers) != {f"P0-{letter}" for letter in "ABCDEFGHIJKL"}:
        raise AssertionError("blocker matrix ID 불완전")
    not_closed = [key for key in sorted(blockers) if key != "P0-L" and not blockers[key]["status"].startswith("PASS")]
    if not_closed:
        raise AssertionError("P0-A~K 미종결: " + ",".join(not_closed))

    fusion = load_json("validation/results/fusion_release_gate_v0.6.2.1.json")
    fusion_pass = fusion.get("status") == "CROSS_SOLVER_VALIDATED"
    if not fusion_pass and not args.allow_fusion_pending:
        raise AssertionError("P0-L actual Fusion/correlation 미완료: " + fusion.get("exact_external_blocker", "unknown"))
    if fusion_pass and blockers["P0-L"]["status"] != "PASS":
        raise AssertionError("Fusion PASS와 blocker matrix 상태 불일치")

    manifest = load_json("artifacts/manifest_v0.6.2.1.json")
    for artifact in manifest.get("artifacts", []):
        path = ROOT / artifact["path"]
        if not path.is_file() or sha256(path) != artifact["sha256"]:
            raise AssertionError(f"artifact manifest hash drift: {artifact['path']}")

    release_evidence = not dirty and fusion_pass and args.stage in {"CI-LIGHT", "CI-FULL"}
    evidence = {
        "revision": REVISION,
        "status": "PASS" if release_evidence else "DIAGNOSTIC_NOT_RELEASE_EVIDENCE",
        "stage": args.stage,
        "exact_commit_sha": head,
        "branch": git("branch", "--show-current"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID") or None,
        "worktree_clean": not dirty,
        "dirty_paths": dirty,
        "fusion_status": fusion.get("status"),
        "hardware_adapter_scenarios": adapter.get("scenario_count"),
        "mutation_count": mutation.get("mutation_count"),
        "openmodelica_scenarios": shadow.get("scenario_count"),
        "artifact_count": manifest.get("artifact_count"),
        "physical_test_performed": False,
        "gates": {
            "HARDWARE_ADAPTER_VALIDATION": "PASS",
            "ACTUATION_CONTROL_VALIDATION": "PASS",
            "PROCESS_FEED_VIRTUAL_VALIDATION": "PASS",
            "VIRTUAL_PHYSICS_VALIDATION": "PASS",
            "CROSS_SOLVER_VALIDATION": "PASS" if fusion_pass else "PENDING_EXTERNAL_FUSION",
            "EXACT_HEAD_REPRODUCIBILITY": "PASS" if release_evidence else "NOT_RELEASE_EVIDENCE",
            "PRICE_STATUS": "INFORMATIONAL_NON_BLOCKING",
            "PROCUREMENT_APPROVAL_GATE": "USER_APPROVAL_REQUIRED",
            "COMMISSIONING_GATE": "USER_APPROVAL_REQUIRED",
        },
        "generator_sha256": sha256(Path(__file__).resolve()),
        "workflow_sha256": {
            "CI-LIGHT": sha256(ROOT / ".github/workflows/ci-light.yml"),
            "CI-FULL": sha256(ROOT / ".github/workflows/ci-full.yml"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(f"V0621_EXACT_HEAD_{args.stage.replace('-', '_')}_{evidence['status']}")


if __name__ == "__main__":
    main()
