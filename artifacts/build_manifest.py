#!/usr/bin/env python3
"""Build revision-locked SHA-256 manifest for compact release artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    "cad/generation/fcstd/*.FCStd",
    "cad/generation/assembly_metadata.json",
    "exports/step/*.step",
    "exports/print/**/*.FCStd", "exports/print/**/*.step", "exports/print/**/*.stl", "exports/print/**/*.3mf",
    "exports/print/**/*.md", "exports/print/*.csv",
    "renders/**/*.png", "docs/*.pdf",
    "bom/*.csv", "calculations/*.md", "calculations/economics/*.md",
    "simulation/*.json", "requirements/*.md", "validation/release_checklist.md",
)


def main():
    paths = sorted({p for pattern in PATTERNS for p in ROOT.glob(pattern) if p.is_file()})
    artifacts = []
    for path in paths:
        data = path.read_bytes()
        artifacts.append({"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    result = {"revision": "compact-single-path-v0.3", "artifact_count": len(artifacts), "artifacts": artifacts}
    out = ROOT / "artifacts/manifest.json"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"ARTIFACT_MANIFEST_OK count={len(artifacts)}")


if __name__ == "__main__": main()
