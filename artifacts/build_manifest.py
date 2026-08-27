#!/usr/bin/env python3
"""Generate revision, size, and SHA-256 metadata for release artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    "cad/generation/fcstd/*.FCStd",
    "exports/step/*.step",
    "exports/stl/*.stl",
    "exports/dxf/*.dxf",
    "renders/assembly/*.png",
    "renders/modules/*.png",
)


def main() -> None:
    parameters = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())
    paths = sorted({path for pattern in PATTERNS for path in ROOT.glob(pattern)})
    artifacts = []
    for path in paths:
        data = path.read_bytes()
        artifacts.append(
            {
                "path": str(path.relative_to(ROOT)),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {
        "project": "filament-recycler",
        "revision": parameters["revision"],
        "generated_utc": "2026-08-27T19:34:56Z",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    (ROOT / "artifacts" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"manifest artifacts={len(artifacts)}")


if __name__ == "__main__":
    main()
