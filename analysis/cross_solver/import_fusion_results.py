#!/usr/bin/env python3
"""검증된 Fusion CSV를 frozen v0.6.1 package에 결박해 수신한다.

외부 solver 값은 이 도구가 생성하지 않는다. 모든 행이 source/STEP/load manifest,
case/study/unit 계약을 통과한 경우에만 correlation review 자료로 복사한다.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BINDING = ROOT / "exports/fusion_validation/run_binding.json"
MODELS = ROOT / "exports/fusion_validation/model_manifest.csv"
CASES = ROOT / "exports/fusion_validation/load_case_manifest.csv"

REQUIRED_COLUMNS = {
    "run_id", "case_id", "study_type", "source_git_sha", "step_file", "step_sha256",
    "load_case_manifest_sha256", "mesh_level", "element_count", "metric", "value", "unit",
    "solver_version", "completed_utc", "evidence_file", "evidence_sha256", "operator", "status",
}
ALLOWED_STUDIES = {
    "LC01": {"static_stress", "event_simulation"},
    "LC02": {"static_stress", "nonlinear_static"},
    "LC03": {"static_stress", "event_simulation"},
    "LC04": {"static_stress"},
    "LC05": {"static_stress"},
    "LC06": {"static_stress", "nonlinear_static"},
    "LC07": {"thermal", "thermal_stress"},
    "LC08": {"thermal", "thermal_stress"},
    "LC09": {"static_stress", "nonlinear_static"},
    "LC10": {"static_stress", "modal_frequencies", "buckling"},
}
STATE_ORDER = [
    "PENDING_EXTERNAL_EXECUTION", "RESULT_RECEIVED_UNVERIFIED", "INVALID_BINDING",
    "INPUT_REVIEW_REQUIRED", "MESH_NOT_CONVERGED", "CORRELATION_REVIEW",
    "CROSS_SOLVER_VALIDATED_FOR_DEFINED_CASES",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_unit(metric: str) -> set[str] | None:
    name = metric.lower().replace("_", " ")
    if "displacement" in name or "deflection" in name:
        return {"mm"}
    if "stress" in name or "pressure" in name:
        return {"MPa"}
    if "reaction" in name or "force" in name or "thrust" in name:
        return {"N"}
    if "torque" in name:
        return {"N*m"}
    if "frequency" in name or "mode" in name:
        return {"Hz"}
    if "temperature" in name or "thermal peak" in name:
        return {"degC"}
    if "participation" in name or "change" in name or "balance" in name:
        return {"percent"}
    if "factor" in name or "safety" in name:
        return {"dimensionless"}
    return None


def load_contract() -> tuple[dict, dict[str, dict], dict[str, dict]]:
    binding = json.loads(BINDING.read_text())
    assert sha256(CASES) == binding["load_case_manifest_sha256"], "local load manifest hash drift"
    assert sha256(MODELS) == binding["model_manifest_sha256"], "local model manifest hash drift"
    with MODELS.open(newline="") as handle:
        models = {row["file"]: row for row in csv.DictReader(handle)}
    with CASES.open(newline="") as handle:
        cases = {row["case_id"]: row for row in csv.DictReader(handle)}
    return binding, models, cases


def validate_rows(rows: list[dict[str, str]]) -> dict:
    binding, models, cases = load_contract()
    errors: list[str] = []
    accepted: list[dict] = []
    if not rows:
        return {"state": "PENDING_EXTERNAL_EXECUTION", "accepted_rows": [], "errors": []}
    for index, row in enumerate(rows, 2):
        prefix = f"row {index}"
        missing = REQUIRED_COLUMNS - set(row)
        if missing:
            errors.append(f"{prefix}: missing columns {sorted(missing)}")
            continue
        case_id = row["case_id"]
        model = models.get(row["step_file"])
        case = cases.get(case_id)
        if case is None:
            errors.append(f"{prefix}: unknown case_id {case_id}")
        if model is None:
            errors.append(f"{prefix}: unknown geometry filename {row['step_file']}")
        if case is not None and row["step_file"] != case["geometry"]:
            errors.append(f"{prefix}: geometry/case mismatch")
        if row["source_git_sha"] != binding["engineering_source_sha"]:
            errors.append(f"{prefix}: engineering source SHA mismatch")
        if row["load_case_manifest_sha256"] != binding["load_case_manifest_sha256"]:
            errors.append(f"{prefix}: load manifest SHA mismatch")
        if model is not None and row["step_sha256"] != model["step_sha256"]:
            errors.append(f"{prefix}: STEP SHA mismatch")
        study = row["study_type"].strip().lower().replace(" ", "_")
        if case_id in ALLOWED_STUDIES and study not in ALLOWED_STUDIES[case_id]:
            errors.append(f"{prefix}: study type {study} is invalid for {case_id}")
        units = expected_unit(row["metric"])
        if units is None:
            errors.append(f"{prefix}: metric unit contract is unknown; input review required")
        elif row["unit"] not in units:
            errors.append(f"{prefix}: unit {row['unit']} does not match {sorted(units)}")
        try:
            value = float(row["value"])
            elements = int(row["element_count"])
            if not math.isfinite(value) or elements <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"{prefix}: non-finite value or invalid element count")
        evidence = Path(row["evidence_file"])
        if not evidence.is_absolute():
            evidence = ROOT / evidence
        if not evidence.is_file() or sha256(evidence) != row["evidence_sha256"]:
            errors.append(f"{prefix}: evidence file/hash mismatch")
        accepted.append(row)
    state = "INVALID_BINDING" if errors else "CORRELATION_REVIEW"
    return {
        "revision": "parallel-actuation-hardening-v0.6.2",
        "state": state,
        "accepted_rows": accepted if not errors else [],
        "errors": errors,
        "binding": {
            "engineering_source_sha": binding["engineering_source_sha"],
            "load_case_manifest_sha256": binding["load_case_manifest_sha256"],
            "model_manifest_sha256": binding["model_manifest_sha256"],
        },
        "correlation_policy": {
            "reaction_balance_percent_max": 5,
            "global_displacement_percent_target": 15,
            "regional_stress_percent_target": 25,
            "medium_to_fine_change_percent_max": 5,
            "independent_safety_factor_min": 2.0,
            "modal_separation_percent_target": 20,
            "disagreement_classes": ["AGREE", "EXPLAINED_DIFFERENCE", "UNRESOLVED_DIFFERENCE",
                                     "INVALID_INPUT", "INSUFFICIENT_EVIDENCE"],
            "averaging_disagreeing_solvers_forbidden": True,
        },
    }


def import_results(source: Path, destination: Path) -> dict:
    with source.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = validate_rows(rows)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "analysis/cross_solver/fusion_import_review.json")
    args = parser.parse_args()
    result = import_results(args.csv, args.output)
    print(result["state"])
    if result["state"] == "INVALID_BINDING":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
