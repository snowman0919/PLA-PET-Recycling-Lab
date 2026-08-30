#!/usr/bin/env python3
"""Refresh only lightweight generated metadata when the frozen geometry is unchanged."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OLD = "implementation-crosssolver-v0.6"
NEW = "safety-orchestration-closure-v0.6.1"
TEXT_SUFFIXES = {".csv", ".json", ".md", ".svg", ".txt"}
ROOTS = (
    ROOT / "cad/generation",
    ROOT / "cad/review_keepouts",
    ROOT / "exports/cnc/extruder",
    ROOT / "exports/drive_interface",
    ROOT / "exports/fabrication",
    ROOT / "exports/jigs/gate1",
    ROOT / "exports/print",
    ROOT / "exports/thermal",
)
EXTRA_FILES = (ROOT / "simulation/cad_clearance.json",)


def main() -> None:
    changed: list[str] = []
    candidates = [path for base in ROOTS for path in base.rglob("*")]
    candidates.extend(EXTRA_FILES)
    for path in sorted(candidates):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(errors="strict")
        if OLD not in text:
            continue
        path.write_text(text.replace(OLD, NEW))
        changed.append(path.relative_to(ROOT).as_posix())
    print(f"FROZEN_GEOMETRY_METADATA_REFRESH_OK files={len(changed)}")


if __name__ == "__main__":
    main()
