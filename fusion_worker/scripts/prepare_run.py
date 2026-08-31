#!/usr/bin/env python3
"""검증된 Fusion 입력 패키지에서 hash-bound 실행 manifest를 만든다.

현재 checkout은 결박 commit 이후일 수 있다. 따라서 HEAD 문자열 일치가 아니라
engineering source commit의 존재/ancestor 관계와 그 commit 안의 STEP 바이트를 직접
검증한다. Solver 결과값은 생성하거나 추정하지 않는다.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_STUDIES = {
    "static_stress",
    "modal_frequencies",
    "thermal",
    "thermal_stress",
    "nonlinear_static",
    "event_simulation",
    "buckling",
    "linear_static",
}
CASE_STUDIES = {
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
    "LC11_FEEDER_ATTACHMENT": {"linear_static"},
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"필수 파일 없음: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def git(repo: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=not binary,
    )
    if result.returncode:
        stderr = result.stderr.decode(errors="replace") if binary else result.stderr
        raise ValueError(f"git {' '.join(args)} 실패: {stderr.strip()}")
    return result.stdout


def relative_to_repo(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"package가 저장소 밖에 있음: {path}") from error


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def find_load_spec(package: Path, case_id: str, case_row: dict[str, str]) -> tuple[Path, dict]:
    candidates: list[Path] = []
    if case_row.get("load_file"):
        candidates.append(package / "loads" / case_row["load_file"])
    candidates.extend(sorted((package / "loads").glob("*.json")))
    matched: list[tuple[Path, dict]] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        value = load_json(path)
        if value.get("case_id") == case_id:
            matched.append((path, value))
    if len(matched) != 1:
        raise ValueError(f"{case_id} load JSON은 정확히 하나여야 함: {len(matched)}")
    return matched[0]


def case_binding(package: Path, case_id: str, cases: dict[str, dict[str, str]],
                 models: dict[str, dict[str, str]]) -> dict:
    if case_id not in cases:
        raise ValueError(f"알 수 없는 case ID: {case_id}")
    case = cases[case_id]
    step_file = case.get("geometry", "")
    if not step_file or step_file not in models:
        raise ValueError(f"{case_id} geometry/model manifest 불일치: {step_file}")
    step_path = package / step_file
    if not step_path.is_file() and "/" not in step_file:
        step_path = package / "geometry" / step_file
    if not step_path.is_file():
        raise ValueError(f"STEP 파일 없음: {step_path}")
    expected_step_sha = case.get("geometry_sha256") or models[step_file].get("step_sha256")
    actual_step_sha = sha256(step_path)
    if not expected_step_sha or actual_step_sha != expected_step_sha:
        raise ValueError(f"{case_id} STEP hash 불일치")
    load_path, load_spec = find_load_spec(package, case_id, case)
    load_sha = sha256(load_path)
    if case.get("load_file_sha256") and load_sha != case["load_file_sha256"]:
        raise ValueError(f"{case_id} load JSON hash 불일치")
    return {
        "case_id": case_id,
        "step_file": step_file,
        "step_path": step_path,
        "step_sha256": actual_step_sha,
        "load_file": load_path.relative_to(package).as_posix(),
        "load_file_sha256": load_sha,
        "load_spec": load_spec,
    }


def build_manifest(repo: Path, package: Path, case_id: str, study_type: str,
                   solver_version: str, related_case_ids: list[str],
                   started_utc: str | None = None) -> dict:
    repo = repo.resolve()
    package = package.resolve()
    if study_type not in ALLOWED_STUDIES:
        raise ValueError(f"허용되지 않은 study type: {study_type}")
    if not solver_version.strip():
        raise ValueError("Fusion solver version이 비어 있음")

    binding_path = package / "run_binding.json"
    binding = load_json(binding_path)
    source_lock = load_json(package / "engineering_source_lock.json")
    source_sha = binding.get("engineering_source_sha") or binding.get("source_git_sha")
    if not isinstance(source_sha, str) or not SHA_RE.fullmatch(source_sha):
        raise ValueError("유효한 engineering source SHA 없음")
    if binding.get("source_git_sha") not in (None, source_sha):
        raise ValueError("source_git_sha와 engineering_source_sha 불일치")
    if source_lock.get("engineering_source_sha") != source_sha:
        raise ValueError("engineering source lock과 run binding 불일치")
    state_path = package / "package_state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if state.get("package_state") != "BOUND_TO_ENGINEERING_SOURCE":
            raise ValueError("package가 engineering source에 결박되지 않음")
        if state.get("fusion_execution_permitted") is not True:
            raise ValueError("package가 Fusion 실행을 허용하지 않음")

    git(repo, "cat-file", "-e", f"{source_sha}^{{commit}}")
    head_sha = str(git(repo, "rev-parse", "HEAD")).strip()
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", source_sha, head_sha]
    )
    if ancestor.returncode != 0:
        raise ValueError(f"engineering source {source_sha}가 현재 HEAD의 ancestor가 아님")

    model_path = package / "model_manifest.csv"
    load_manifest_path = package / "load_case_manifest.csv"
    if sha256(model_path) != binding.get("model_manifest_sha256"):
        raise ValueError("model manifest hash 불일치")
    if sha256(load_manifest_path) != binding.get("load_case_manifest_sha256"):
        raise ValueError("load-case manifest hash 불일치")
    models = {row["file"]: row for row in read_rows(model_path)}
    cases = {row["case_id"]: row for row in read_rows(load_manifest_path)}
    if study_type not in CASE_STUDIES.get(case_id, set()):
        raise ValueError(f"{case_id}에 허용되지 않은 study type: {study_type}")
    if case_id == "LC08" and study_type == "thermal_stress" and related_case_ids != ["LC06"]:
        raise ValueError("LC08 thermal_stress는 정확히 LC06 pressure 결박이 필요함")
    if related_case_ids and not (case_id == "LC08" and study_type == "thermal_stress"):
        raise ValueError("related case 결박은 LC08 thermal_stress + LC06에만 허용됨")
    if len(related_case_ids) != len(set(related_case_ids)):
        raise ValueError("related case ID 중복")
    primary = case_binding(package, case_id, cases, models)
    related = [case_binding(package, item, cases, models) for item in related_case_ids]

    package_rel = relative_to_repo(package, repo)
    step_rel = relative_to_repo(primary["step_path"], repo)
    source_step = git(repo, "show", f"{source_sha}:{step_rel}", binary=True)
    if sha256_bytes(source_step) != primary["step_sha256"]:
        raise ValueError("현재 package STEP과 engineering source Git object 불일치")
    for item in related:
        related_step_rel = relative_to_repo(item["step_path"], repo)
        related_source_step = git(repo, "show", f"{source_sha}:{related_step_rel}", binary=True)
        if sha256_bytes(related_source_step) != item["step_sha256"]:
            raise ValueError(f"{item['case_id']} STEP과 engineering source Git object 불일치")

    timestamp = started_utc or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("started_utc는 ISO-8601이어야 함") from error
    if parsed_time.tzinfo is None or parsed_time.utcoffset().total_seconds() != 0:
        raise ValueError("started_utc는 UTC timezone을 포함해야 함")
    safe_time = parsed_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    load_spec = primary.pop("load_spec")
    for item in related:
        item.pop("load_spec")
        item.pop("step_path")
    primary.pop("step_path")
    mesh_levels = load_spec.get("mesh_levels", ["coarse", "medium", "fine"])
    units = load_spec.get(
        "units",
        "explicit load-key suffixes: mm, N, N*mm, MPa, degC, s",
    )
    return {
        "schema_version": "1.1",
        "run_id": f"{case_id}-{study_type}-{safe_time}",
        "case_id": case_id,
        "study_type": study_type,
        "source_git_sha": source_sha,
        "engineering_source_sha": source_sha,
        "execution_checkout_sha": head_sha,
        "package_path": package_rel,
        "step_file": primary["step_file"],
        "step_sha256": primary["step_sha256"],
        "load_file": primary["load_file"],
        "load_file_sha256": primary["load_file_sha256"],
        "load_case_manifest_sha256": binding["load_case_manifest_sha256"],
        "model_manifest_sha256": binding["model_manifest_sha256"],
        "run_binding_sha256": sha256(binding_path),
        "related_case_bindings": related,
        "units": units,
        "mesh_levels": mesh_levels,
        "solver_name": "Autodesk Fusion",
        "solver_version": solver_version.strip(),
        "started_utc": timestamp,
        "completed_utc": None,
        "status": "PENDING",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--study-type", required=True)
    parser.add_argument("--solver-version", required=True)
    parser.add_argument("--related-case-id", action="append", default=[])
    parser.add_argument("--started-utc", help="결정론적 시험용 ISO-8601 UTC 시각")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    package = args.package_root
    if not package.is_absolute():
        package = args.repo_root / package
    try:
        manifest = build_manifest(
            args.repo_root,
            package,
            args.case_id,
            args.study_type,
            args.solver_version,
            args.related_case_id,
            args.started_utc,
        )
    except (ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"FUSION_RUN_PREP_FAIL {error}") from error
    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    output = args.output or package / "results" / f"{manifest['run_id']}.run.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit(f"FUSION_RUN_PREP_FAIL output already exists: {output}")
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FUSION_RUN_MANIFEST_OK path={output}")


if __name__ == "__main__":
    main()
