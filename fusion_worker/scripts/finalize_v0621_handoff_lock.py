#!/usr/bin/env python3
"""최종 v0.6.2.1 engineering source에 두 Fusion handoff 패키지를 결박한다.

이 도구는 solver 결과를 만들지 않는다. 지정 commit의 Git object와 현재 패키지
바이트가 같은지 확인한 뒤, 이후 MacBook stage가 검증할 immutable lock만 쓴다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


PACKAGE_PATTERNS = {
    "exports/fusion_validation": [
        "geometry/*.step",
        "loads/*.json",
        "loads/load_case_manifest.csv",
        "fusion_studies/*.md",
        "constraints.csv",
        "contact_pairs.csv",
        "coordinate_system.md",
        "engineering_source_lock.json",
        "expected_metrics.csv",
        "load_case_manifest.csv",
        "materials.csv",
        "model_manifest.csv",
        "rerun_delta_report.csv",
        "results/fusion_result_template.csv",
        "run_binding.json",
        "units_contract.md",
    ],
    "exports/fusion_validation_v0621": [
        "geometry/*.step",
        "loads/*.json",
        "constraints.csv",
        "contact_pairs.csv",
        "coordinate_system.md",
        "engineering_source_lock.json",
        "expected_metrics.csv",
        "legacy_package_reference.json",
        "load_case_manifest.csv",
        "materials.csv",
        "mesh_plan.csv",
        "model_manifest.csv",
        "package_state.json",
        "results/fusion_result_template.csv",
        "results/result_schema.json",
        "run_binding.json",
    ],
}
WORKER_FILES = [
    "fusion_worker/README.md",
    "fusion_worker/cua_playbooks/fusion_execution.md",
    "fusion_worker/run_manifest.schema.json",
    "fusion_worker/scripts/prepare_run.py",
    "fusion_worker/result_validation/validate_fusion_results.py",
    "fusion_worker/result_validation/validate_fusion_v0621_package.py",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(repo: Path, *args: str, binary: bool = False) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=not binary
    )
    if result.returncode:
        detail = result.stderr.decode(errors="replace") if binary else result.stderr
        raise ValueError(f"git {' '.join(args)} 실패: {detail.strip()}")
    return result.stdout


def committed_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return git(repo, "show", f"{commit}:{relative}", binary=True)  # type: ignore[return-value]


def expand_files(repo: Path, package: str, patterns: list[str]) -> list[str]:
    base = repo / package
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(base.glob(pattern))
    relative = sorted(path.relative_to(repo).as_posix() for path in paths if path.is_file())
    if not relative:
        raise ValueError(f"handoff package 파일 없음: {package}")
    return relative


def bind_file(repo: Path, commit: str, relative: str) -> str:
    path = repo / relative
    if not path.is_file():
        raise ValueError(f"현재 handoff 파일 없음: {relative}")
    committed = committed_bytes(repo, commit, relative)
    current = path.read_bytes()
    if current != committed:
        raise ValueError(f"현재 파일이 engineering source commit과 다름: {relative}")
    return sha256_bytes(committed)


def atomic_json(path: Path, value: dict) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--engineering-source-sha", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports/fusion_handoff_lock_v0.6.2.1.json"),
    )
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    commit = args.engineering_source_sha.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("FUSION_HANDOFF_LOCK_FAIL engineering SHA must be 40 lowercase hex")
    try:
        resolved = str(git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")).strip()
        if resolved != commit:
            raise ValueError("engineering SHA가 정확한 commit으로 resolve되지 않음")
        source_tree_hash = str(git(repo, "rev-parse", f"{commit}^{{tree}}")).strip()
        object_format = str(git(repo, "rev-parse", "--show-object-format")).strip()
        packages: dict[str, dict] = {}
        aggregate = hashlib.sha256()
        for package, patterns in PACKAGE_PATTERNS.items():
            files = {
                relative: bind_file(repo, commit, relative)
                for relative in expand_files(repo, package, patterns)
            }
            binding = json.loads((repo / package / "run_binding.json").read_text())
            step_hashes = {
                relative: digest for relative, digest in files.items() if relative.endswith(".step")
            }
            contract_hashes = {
                relative: digest
                for relative, digest in files.items()
                if Path(relative).name in {
                    "load_case_manifest.csv", "materials.csv", "contact_pairs.csv",
                    "constraints.csv", "model_manifest.csv", "mesh_plan.csv",
                    "result_schema.json", "fusion_result_template.csv",
                }
            }
            packages[package] = {
                "provenance_engineering_source_sha": binding.get("engineering_source_sha"),
                "step_sha256": step_hashes,
                "contract_sha256": contract_hashes,
                "files": files,
            }
            for relative, digest in sorted(files.items()):
                aggregate.update(relative.encode() + b"\0" + digest.encode() + b"\0")
        worker_hashes = {relative: bind_file(repo, commit, relative) for relative in WORKER_FILES}
        for relative, digest in sorted(worker_hashes.items()):
            aggregate.update(relative.encode() + b"\0" + digest.encode() + b"\0")
        payload = {
            "schema_version": "1.0",
            "revision": "technical-blocker-closure-v0.6.2.1",
            "state": "IMMUTABLE_HANDOFF_BOUND",
            "engineering_source_sha": commit,
            "source_tree_hash": source_tree_hash,
            "source_tree_hash_algorithm": object_format,
            "handoff_input_set_sha256": aggregate.hexdigest(),
            "fusion_gate_policy": "DEFERRED",
            "fusion_execution_state": "DEFERRED_TO_POST_V0.6.2.1_MACBOOK_STAGE",
            "fusion_solver_pass": False,
            "external_execution_must_use_descendant_of": commit,
            "recommended_tag": "technical-closure-v0.6.2.1",
            "recommended_archive_branch": "archive/technical-blocker-closure-v0.6.2.1",
            "packages": packages,
            "worker_contract_sha256": worker_hashes,
        }
        output = args.output if args.output.is_absolute() else repo / args.output
        atomic_json(output, payload)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"FUSION_HANDOFF_LOCK_FAIL {error}") from error
    print(
        "FUSION_HANDOFF_LOCK_OK "
        f"engineering_source_sha={commit} packages={len(packages)} solver_pass=false"
    )


if __name__ == "__main__":
    main()
