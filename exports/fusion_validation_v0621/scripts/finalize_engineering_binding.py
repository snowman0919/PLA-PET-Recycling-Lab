#!/usr/bin/env python3
"""Bind LC11 package bytes to an existing immutable engineering source commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


SOURCE_PATHS = {
    "geometry/PF-04.step": "exports/process_v0621/parts/PF-04/PF-04.step",
    "geometry/PF-05.step": "exports/process_v0621/parts/PF-05/PF-05.step",
    "geometry/process_feed_assembly.step": "exports/process_v0621/process_feed_assembly.step",
}
SOURCE_MANIFEST = "exports/process_v0621/manifest.json"


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{path}"], cwd=repo, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode(errors="replace").strip()
        raise SystemExit(f"FUSION_V0621_BIND_FAIL cannot read {commit}:{path}: {detail}") from None


def atomic_json(path: Path, value: dict) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--engineering-source-sha", required=True)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    package = repo / "exports/fusion_validation_v0621"
    commit = args.engineering_source_sha.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("FUSION_V0621_BIND_FAIL engineering SHA must be 40 lowercase hex characters")
    resolved = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=repo, text=True
    ).strip()
    if resolved != commit:
        raise SystemExit("FUSION_V0621_BIND_FAIL SHA did not resolve to the exact commit")

    source_hashes: dict[str, dict[str, str]] = {}
    for packaged_path, source_path in SOURCE_PATHS.items():
        committed = git_blob(repo, commit, source_path)
        packaged = (package / packaged_path).read_bytes()
        if committed != packaged:
            raise SystemExit(
                f"FUSION_V0621_BIND_FAIL {packaged_path} differs from {commit}:{source_path}"
            )
        source_hashes[packaged_path] = {
            "source_path": source_path,
            "sha256": digest_bytes(committed),
        }

    committed_manifest = git_blob(repo, commit, SOURCE_MANIFEST)
    working_manifest = (repo / SOURCE_MANIFEST).read_bytes()
    if committed_manifest != working_manifest:
        raise SystemExit(
            "FUSION_V0621_BIND_FAIL working process manifest differs from the requested commit"
        )
    process_manifest_sha = digest_bytes(committed_manifest)
    aggregate = hashlib.sha256()
    for source_path in sorted([*SOURCE_PATHS.values(), SOURCE_MANIFEST]):
        aggregate.update(source_path.encode("utf-8") + b"\0")
        aggregate.update(git_blob(repo, commit, source_path))
        aggregate.update(b"\0")

    package_state = {
        "schema_version": "1.0",
        "package_id": "PPR-v0.6.2.1-LC11",
        "package_state": "BOUND_TO_ENGINEERING_SOURCE",
        "engineering_source_sha": commit,
        "fusion_execution_permitted": True,
        "reason": "package geometry and source manifest match immutable Git objects",
    }
    source_lock = {
        "schema_version": "1.0",
        "package_id": "PPR-v0.6.2.1-LC11",
        "package_state": "BOUND_TO_ENGINEERING_SOURCE",
        "engineering_source_sha": commit,
        "source_process_manifest": SOURCE_MANIFEST,
        "source_process_manifest_sha256": process_manifest_sha,
        "source_input_set_sha256": aggregate.hexdigest(),
        "geometry_sources": source_hashes,
        "binding_command": (
            "python3 exports/fusion_validation_v0621/scripts/"
            "finalize_engineering_binding.py --repo-root . "
            f"--engineering-source-sha {commit}"
        ),
    }
    run_binding = {
        "schema_version": "1.0",
        "package_id": "PPR-v0.6.2.1-LC11",
        "package_state": "BOUND_TO_ENGINEERING_SOURCE",
        "engineering_source_sha": commit,
        "source_git_sha": commit,
        "source_process_manifest_sha256": process_manifest_sha,
        "model_manifest_sha256": digest(package / "model_manifest.csv"),
        "load_case_manifest_sha256": digest(package / "load_case_manifest.csv"),
        "fusion_result_state": "PENDING_EXTERNAL_EXECUTION",
        "required_result_binding": [
            "engineering_source_sha",
            "step_sha256",
            "load_case_manifest_sha256",
        ],
    }
    atomic_json(package / "package_state.json", package_state)
    atomic_json(package / "engineering_source_lock.json", source_lock)
    atomic_json(package / "run_binding.json", run_binding)
    print(f"FUSION_V0621_BIND_OK engineering_source_sha={commit}")


if __name__ == "__main__":
    main()
