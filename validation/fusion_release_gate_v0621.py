#!/usr/bin/env python3
"""v0.6.2.1 Fusion tri-state 정책과 결과/패키지를 fail-closed로 검증한다."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/cross_solver"))
import import_fusion_results as legacy_importer  # noqa: E402

MANDATORY_LEGACY_CASES = {"LC02", "LC04", "LC05", "LC07", "LC08", "LC10"}
MESH_LEVELS = {"coarse", "medium", "fine"}
FINAL_CLASSES = {"AGREE", "EXPLAINED_DIFFERENCE"}
POLICIES = {"REQUIRED", "DEFERRED", "COMPLETED"}
POLICY_PATH = ROOT / "validation/fusion_policy_v0.6.2.1.json"
LEGACY_RESULTS = ROOT / "exports/fusion_validation/results/fusion_results.csv"
LC11_RESULTS = ROOT / "exports/fusion_validation_v0621/results/fusion_results.csv"
FINAL_HANDOFF_LOCK = ROOT / "exports/fusion_handoff_lock_v0.6.2.1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise AssertionError(f"필수 Fusion 증거 없음: {path.relative_to(ROOT)}")
    return json.loads(path.read_text())


def validate_policy(selected: str) -> dict:
    policy = load_json(POLICY_PATH)
    configured = policy.get("fusion_gate_policy")
    if configured not in POLICIES or sorted(policy.get("allowed_policies", [])) != sorted(POLICIES):
        raise AssertionError("Fusion tri-state policy contract 불일치")
    if selected != configured:
        raise AssertionError(f"CLI/config Fusion policy 불일치: cli={selected} config={configured}")
    if policy.get("package_integrity_required") is not True:
        raise AssertionError("Fusion package integrity gate 비활성화 금지")
    if policy.get("present_result_validation_required") is not True:
        raise AssertionError("존재하는 Fusion 결과 fail-closed 검증 비활성화 금지")
    if configured == "DEFERRED" and policy.get("deferred_is_solver_pass") is not False:
        raise AssertionError("DEFERRED를 solver PASS로 해석할 수 없음")
    return policy


def validate_package_integrity() -> dict:
    command = [
        sys.executable,
        "fusion_worker/result_validation/validate_fusion_v0621_package.py",
        "exports/fusion_validation_v0621",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode or "FUSION_V0621_PACKAGE_OK" not in result.stdout + result.stderr:
        raise AssertionError("LC11 package integrity 실패: " + (result.stdout + result.stderr).strip())
    binding, models, cases = legacy_importer.load_contract()
    source_lock = load_json(ROOT / "exports/fusion_validation/engineering_source_lock.json")
    result_manifest = load_json(ROOT / "exports/fusion_validation/results/fusion_result_manifest.json")
    if source_lock.get("engineering_source_sha") != binding.get("engineering_source_sha"):
        raise AssertionError("legacy Fusion engineering source lock 불일치")
    if result_manifest.get("source_git_sha") != binding.get("source_git_sha"):
        raise AssertionError("legacy Fusion result manifest source binding 불일치")
    if result_manifest.get("load_case_manifest_sha256") != binding.get("load_case_manifest_sha256"):
        raise AssertionError("legacy Fusion result manifest load binding 불일치")
    if result_manifest.get("model_manifest_sha256") != binding.get("model_manifest_sha256"):
        raise AssertionError("legacy Fusion result manifest model binding 불일치")
    final_lock = load_json(FINAL_HANDOFF_LOCK)
    final_source = final_lock.get("engineering_source_sha")
    if (
        final_lock.get("state") != "IMMUTABLE_HANDOFF_BOUND"
        or final_lock.get("fusion_gate_policy") != "DEFERRED"
        or final_lock.get("fusion_solver_pass") is not False
        or not isinstance(final_source, str)
    ):
        raise AssertionError("최종 Fusion handoff lock 상태 불일치")
    tree = subprocess.run(
        ["git", "rev-parse", f"{final_source}^{{tree}}"], cwd=ROOT,
        text=True, capture_output=True,
    )
    if tree.returncode or tree.stdout.strip() != final_lock.get("source_tree_hash"):
        raise AssertionError("최종 Fusion handoff source tree hash 불일치")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", final_source, "HEAD"], cwd=ROOT
    ).returncode:
        raise AssertionError("현재 checkout이 최종 Fusion handoff source보다 이전임")
    locked_files: dict[str, str] = dict(final_lock.get("worker_contract_sha256", {}))
    for package in final_lock.get("packages", {}).values():
        locked_files.update(package.get("files", {}))
    if not locked_files:
        raise AssertionError("최종 Fusion handoff 파일 hash 없음")
    for relative, expected in locked_files.items():
        path = ROOT / relative
        if not path.is_file() or sha256(path) != expected:
            raise AssertionError(f"최종 Fusion handoff hash drift: {relative}")
        try:
            committed = subprocess.check_output(
                ["git", "show", f"{final_source}:{relative}"], cwd=ROOT,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as error:
            raise AssertionError(f"최종 Fusion source Git object 없음: {relative}") from error
        if hashlib.sha256(committed).hexdigest() != expected:
            raise AssertionError(f"최종 Fusion source Git object drift: {relative}")
    return {
        "status": "PASS",
        "legacy_model_count": len(models),
        "legacy_case_count": len(cases),
        "legacy_engineering_source_sha": binding["engineering_source_sha"],
        "lc11_engineering_source_sha": load_json(
            ROOT / "exports/fusion_validation_v0621/run_binding.json"
        )["engineering_source_sha"],
        "final_handoff_state": final_lock["state"],
        "final_handoff_engineering_source_sha": final_source,
        "final_handoff_source_tree_hash": final_lock["source_tree_hash"],
        "final_handoff_input_set_sha256": final_lock["handoff_input_set_sha256"],
    }


def inspect_present_results() -> dict:
    review = load_json(ROOT / "analysis/cross_solver/fusion_import_review.json")
    legacy_manifest = load_json(ROOT / "exports/fusion_validation/results/fusion_result_manifest.json")
    legacy_rows: list[dict[str, str]] = []
    lc11_rows: list[dict[str, str]] = []
    if LEGACY_RESULTS.is_file():
        with LEGACY_RESULTS.open(newline="") as handle:
            legacy_rows = list(csv.DictReader(handle))
        live = legacy_importer.validate_rows(legacy_rows)
        if live.get("state") == "INVALID_BINDING" or live.get("errors"):
            raise AssertionError("존재하는 legacy Fusion 결과가 malformed/stale: " + "; ".join(live.get("errors", [])))
        if review.get("state") != live.get("state") or review.get("accepted_rows") != live.get("accepted_rows") or review.get("errors") != live.get("errors"):
            raise AssertionError("legacy Fusion import review가 현재 결과 CSV와 불일치")
        if not legacy_manifest.get("runs"):
            raise AssertionError("legacy Fusion 결과 CSV에 hash-bound run manifest 없음")
    elif review.get("accepted_rows") or review.get("errors") or review.get("state") != "PENDING_EXTERNAL_EXECUTION":
        raise AssertionError("legacy Fusion 결과 CSV 없이 stale import review 존재")
    elif legacy_manifest.get("runs"):
        raise AssertionError("legacy Fusion 결과 CSV 없이 run manifest 존재")

    if LC11_RESULTS.is_file():
        lc11_rows = validate_lc11_rows(LC11_RESULTS)

    return {
        "legacy_result_file_present": LEGACY_RESULTS.is_file(),
        "legacy_result_rows": len(legacy_rows),
        "lc11_result_file_present": LC11_RESULTS.is_file(),
        "lc11_result_rows": len(lc11_rows),
        "presence": "PRESENT" if legacy_rows or lc11_rows else "ABSENT",
        "validation": "VALID" if legacy_rows or lc11_rows else "NOT_APPLICABLE",
    }


def validate_lc11_rows(path: Path) -> list[dict[str, str]]:
    binding = load_json(ROOT / "exports/fusion_validation_v0621/run_binding.json")
    if binding.get("package_state") != "BOUND_TO_ENGINEERING_SOURCE":
        raise AssertionError("LC11 engineering source binding 미완료")
    if sha256(ROOT / "exports/fusion_validation_v0621/load_case_manifest.csv") != binding.get(
        "load_case_manifest_sha256"
    ):
        raise AssertionError("LC11 load-case manifest hash drift")
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise AssertionError("LC11 Fusion 결과 행 없음")
    expected_step = sha256(ROOT / "exports/fusion_validation_v0621/geometry/PF-05.step")
    for row in rows:
        if row.get("case_id") != "LC11_FEEDER_ATTACHMENT":
            raise AssertionError("LC11 결과에 다른 case 혼입")
        if row.get("engineering_source_sha") != binding.get("engineering_source_sha"):
            raise AssertionError("LC11 engineering source SHA 불일치")
        if row.get("step_file") != "geometry/PF-05.step" or row.get("step_sha256") != expected_step:
            raise AssertionError("LC11 STEP binding 불일치")
        if row.get("load_case_manifest_sha256") != binding.get("load_case_manifest_sha256"):
            raise AssertionError("LC11 load-case binding 불일치")
        if row.get("mesh_level") not in MESH_LEVELS or int(row.get("element_count", "0")) <= 0:
            raise AssertionError("LC11 mesh 증거 불완전")
        if row.get("solver_name") != "Autodesk Fusion" or not row.get("solver_version"):
            raise AssertionError("LC11 실제 Fusion/version 증거 없음")
        evidence = ROOT / row.get("evidence_file", "")
        if not evidence.is_file() or sha256(evidence) != row.get("evidence_sha256"):
            raise AssertionError("LC11 evidence file/hash 불일치")
        if row.get("status") != "PASS":
            raise AssertionError("LC11 Fusion study PASS 아님")
    if {row["mesh_level"] for row in rows} != MESH_LEVELS:
        raise AssertionError("LC11 coarse/medium/fine mesh 증거 미완료")
    return rows


def validate_completed_results() -> dict:
    review = load_json(ROOT / "analysis/cross_solver/fusion_import_review.json")
    rows = review.get("accepted_rows", [])
    live = legacy_importer.validate_rows(rows)
    if live.get("state") != "CORRELATION_REVIEW" or review.get("errors"):
        raise AssertionError("LC02/04/05/07/08/10 Fusion binding 검증 미완료")
    by_case: dict[str, set[str]] = {}
    for row in rows:
        if row.get("status") != "COMPLETE" or not row.get("solver_version"):
            raise AssertionError("legacy Fusion run 완료/version 증거 불완전")
        by_case.setdefault(row["case_id"], set()).add(row["mesh_level"])
    missing = sorted(case for case in MANDATORY_LEGACY_CASES if by_case.get(case) != MESH_LEVELS)
    if missing:
        raise AssertionError("mandatory Fusion coarse/medium/fine case 미완료: " + ",".join(missing))
    lc08_combined = [
        row for row in rows
        if row["case_id"] == "LC08" and row["study_type"].strip().lower().replace(" ", "_") == "thermal_stress"
    ]
    if not lc08_combined:
        raise AssertionError("LC08+LC06 thermal-stress/pressure combination 증거 없음")
    lc11_rows = validate_lc11_rows(ROOT / "exports/fusion_validation_v0621/results/fusion_results.csv")

    with (ROOT / "analysis/cross_solver/correlation_matrix.csv").open(newline="") as handle:
        correlations = list(csv.DictReader(handle))
    required_ids = {f"C{i:02d}" for i in range(1, 12)}
    by_id = {row["correlation_id"]: row for row in correlations}
    if not required_ids <= set(by_id):
        raise AssertionError("교차-solver 필수 correlation 행 누락")
    invalid = [key for key in sorted(required_ids) if by_id[key].get("status") not in FINAL_CLASSES]
    if invalid:
        raise AssertionError("교차-solver 미해결 판정: " + ",".join(invalid))
    return {
        "revision": "technical-blocker-closure-v0.6.2.1",
        "status": "CROSS_SOLVER_VALIDATED",
        "legacy_mandatory_cases": sorted(MANDATORY_LEGACY_CASES),
        "legacy_result_rows": len(rows),
        "lc11_result_rows": len(lc11_rows),
        "correlation_classes": {key: by_id[key]["status"] for key in sorted(required_ids)},
    }


def evaluate(policy_name: str) -> dict:
    policy = validate_policy(policy_name)
    package = validate_package_integrity()
    present = inspect_present_results()
    completed = None
    if policy_name in {"REQUIRED", "COMPLETED"}:
        completed = validate_completed_results()
    elif present["presence"] == "PRESENT":
        try:
            completed = validate_completed_results()
        except (AssertionError, FileNotFoundError, ValueError, KeyError):
            completed = None
    if policy_name == "DEFERRED":
        return {
            "revision": "technical-blocker-closure-v0.6.2.1",
            "status": "FUSION_GATE_DEFERRED",
            "gate_outcome": "DEFERRED",
            "fusion_gate_policy": policy_name,
            "fusion_state": "DEFERRED_TO_POST_V0.6.2.1_MACBOOK_STAGE",
            "cross_solver_state": "CROSS_SOLVER_VALIDATION_DEFERRED",
            "release_blocking": False,
            "deferred_is_solver_pass": False,
            "package_integrity": package,
            "present_results": present,
            "completed_result_summary": completed,
            "forbidden_claims": policy["forbidden_claims"],
        }
    assert completed is not None
    completed.update({
        "gate_outcome": "COMPLETED",
        "fusion_gate_policy": policy_name,
        "fusion_state": "COMPLETED",
        "cross_solver_state": "CROSS_SOLVER_VALIDATED_FOR_DEFINED_CASES",
        "release_blocking": False,
        "deferred_is_solver_pass": False,
        "package_integrity": package,
        "present_results": present,
    })
    return completed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", choices=("required", "deferred", "completed"), required=True)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "validation/results/fusion_release_gate_v0.6.2.1.json",
    )
    args = parser.parse_args()
    try:
        result = evaluate(args.policy.upper())
    except (AssertionError, FileNotFoundError, ValueError, KeyError) as error:
        result = {
            "revision": "technical-blocker-closure-v0.6.2.1",
            "status": "FUSION_GATE_INVALID_OR_UNMET",
            "gate_outcome": "FAIL",
            "fusion_gate_policy": args.policy.upper(),
            "exact_failure": str(error),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"V0621_FUSION_GATE_FAIL {error}")
        raise SystemExit(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if result["status"] == "FUSION_GATE_DEFERRED":
        print("V0621_FUSION_GATE_DEFERRED package_integrity=PASS solver_pass=false")
    else:
        print("V0621_FUSION_CROSS_SOLVER_GATE_PASS")


if __name__ == "__main__":
    main()
