#!/usr/bin/env python3
"""Verify immutable archive refs and active revision configuration locks."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "virtual-physics-closure-v0.5.1"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()


def resolve_any(*refs: str) -> str:
    for ref in refs:
        result = subprocess.run(["git", "rev-parse", "--verify", ref], cwd=ROOT, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout.strip()
    raise AssertionError(f"missing ref: {refs}")


def main() -> None:
    params = json.loads((ROOT / "cad/parameters/baseline.json").read_text())
    expected = params["archive_sha"]
    assert params["revision"] == REV
    tag_commit = git("rev-parse", "coupled-digital-validation-v0.5^{}")
    # A --single-branch clean clone intentionally omits unrelated remote branch
    # refs while still fetching annotated release tags.  Prefer the archive
    # branch when present, then use the immutable tag's peeled commit as the
    # local reproducibility witness.
    branch_commit = resolve_any(
        "refs/heads/archive/coupled-digital-validation-v0.5",
        "refs/remotes/origin/archive/coupled-digital-validation-v0.5",
        "coupled-digital-validation-v0.5^{}",
    )
    assert tag_commit == branch_commit == expected, (tag_commit, branch_commit, expected)
    assert git("cat-file", "-t", "coupled-digital-validation-v0.5") == "tag", "tag must remain annotated"

    compact_expected = "d0d7f5cfe866c433bc85ca928d12583a57155c99"
    compact_tag = git("rev-parse", "compact-v0.3-surface-proof^{}")
    compact_branch = resolve_any(
        "refs/heads/archive/compact-v0.3-surface-proof",
        "refs/remotes/origin/archive/compact-v0.3-surface-proof",
        "compact-v0.3-surface-proof^{}",
    )
    assert compact_tag == compact_branch == compact_expected, (compact_tag, compact_branch)

    old_expected = "5d83e165466c6a8a1f4c159d198baaa1c2768e59"
    old_tag = git("rev-parse", "research-v0.2-two-tower^{}")
    old_branch = resolve_any(
        "refs/heads/archive/research-v0.2-two-tower",
        "refs/remotes/origin/archive/research-v0.2-two-tower",
        "research-v0.2-two-tower^{}",
    )
    assert old_tag == old_branch == old_expected, (old_tag, old_branch)

    archive_text = (ROOT / "docs/archive_index.md").read_text()
    for token in (expected, "coupled-digital-validation-v0.5", REV, compact_expected, "compact-v0.3-surface-proof", old_expected, "research-v0.2-two-tower"):
        assert token in archive_text, f"archive index missing {token}"
    print(f"CONFIGURATION_CONTROL_OK v05={expected[:12]} compact={compact_expected[:12]} legacy={old_expected[:12]}")


if __name__ == "__main__":
    main()
