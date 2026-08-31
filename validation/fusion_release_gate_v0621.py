#!/usr/bin/env python3
"""v0.6.2.1 Fusion 증거와 교차-solver 판정을 fail-closed로 검증한다."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis/cross_solver"))
import import_fusion_results as legacy_importer  # noqa: E402

MANDATORY_LEGACY_CASES = {"LC02", "LC04", "LC05", "LC07", "LC08", "LC10"}
MESH_LEVELS = {"coarse", "medium", "fine"}
FINAL_CLASSES = {"AGREE", "EXPLAINED_DIFFERENCE"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise AssertionError(f"필수 Fusion 증거 없음: {path.relative_to(ROOT)}")
    return json.loads(path.read_text())


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


def validate_release() -> dict:
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "validation/results/fusion_release_gate_v0.6.2.1.json",
    )
    args = parser.parse_args()
    try:
        result = validate_release()
    except (AssertionError, FileNotFoundError, ValueError, KeyError) as error:
        external_path = ROOT / "validation/fusion_external_blocker_v0.6.2.1.json"
        external = json.loads(external_path.read_text()) if external_path.is_file() else None
        result = {
            "revision": "technical-blocker-closure-v0.6.2.1",
            "status": "PENDING_EXTERNAL_FUSION",
            "exact_external_blocker": str(error),
            "worker_observation": external,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"V0621_FUSION_EXTERNAL_BLOCKER {error}")
        if args.allow_pending:
            return
        raise SystemExit(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("V0621_FUSION_CROSS_SOLVER_GATE_PASS")


if __name__ == "__main__":
    main()
