"""Resolve local Git identity or export metadata; external package verification authenticates bytes."""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess


def source_identity(root: Path) -> tuple[str, str]:
    root = root.resolve()
    if (root/".git").exists():
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
        return head, branch
    marker = root/"SOURCE_SNAPSHOT.json"
    if not marker.is_file():
        raise RuntimeError("No local Git identity or exported SOURCE_SNAPSHOT.json; do not inherit a parent repository")
    data = json.loads(marker.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not re.fullmatch(r"[0-9a-f]{40}", str(data.get("source_commit", ""))):
        raise ValueError("Malformed source snapshot identity")
    if data.get("physical_validation_state") != "NOT_RUN" or data.get("energization_authorized") is not False:
        raise ValueError("Snapshot must not claim physical release")
    return data["source_commit"], "EXPORTED_SNAPSHOT"
