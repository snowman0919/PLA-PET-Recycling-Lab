#!/usr/bin/env python3
"""Build revision-locked SHA-256 manifest for the v0.4 digital baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = (
    "cad/parameters/*.json", "cad/freecad/**/*.py", "cad/generation/*.py", "cad/generation/*.csv", "cad/generation/*.json",
    "cad/generation/fcstd/*.FCStd",
    "cad/generation/assembly_metadata.json",
    "exports/step/*.step",
    "exports/cnc/**/*.FCStd", "exports/cnc/**/*.step", "exports/cnc/**/*.dxf", "exports/cnc/**/*.md", "exports/cnc/**/*.pdf", "exports/cnc/*.csv",
    "exports/drive_interface/**/*", "exports/jigs/**/*",
    "exports/print/**/*.FCStd", "exports/print/**/*.step", "exports/print/**/*.stl", "exports/print/**/*.3mf",
    "exports/print/**/*.md", "exports/print/**/*.py", "exports/print/**/*.svg", "exports/print/**/*.csv", "exports/print/*.csv",
    "exports/print/slicer_profiles/*",
    "renders/**/*.png", "docs/*.pdf", "docs/*.md",
    "bom/*.csv", "calculations/*.md", "calculations/economics/*.md",
    "simulation/*.json", "simulation/openmodelica/**/*.mo", "simulation/openmodelica/**/*.mos",
    "simulation/openmodelica/**/*.json", "simulation/openmodelica/**/*.md", "simulation/openmodelica/results/plots/*.svg",
    "analysis/**/*.py", "analysis/**/*.json", "analysis/**/*.md", "analysis/structural/generated/*.inp",
    "requirements/*.md", "validation/*.py", "validation/release_checklist.md", "validation/completion_audit_v0.4.md", "validation/physical_gate_status.json", "validation/results/*.json",
)


def main():
    paths = sorted({
        p for pattern in PATTERNS for p in ROOT.glob(pattern)
        if p.is_file() and "simulation/openmodelica/results/raw" not in p.as_posix()
        and "exports/print/slicing_previews" not in p.as_posix()
    })
    artifacts = []
    for path in paths:
        data = path.read_bytes()
        artifacts.append({"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    result = {
        "revision": "solid-manifold-openmodelica-v0.4",
        "release_state": "DIGITAL_FABRICATION_BASELINE",
        "physical_state": "PHYSICAL_NOT_RUN",
        "regeneration_commands": [
            "FreeCADCmd cad/generation/generate_all.py via validation/run_all.py",
            "PrusaSlicer 2.9.6 via validation/slice_prints.py",
            "OpenModelica 1.27.0 / MSL 4.0.0 via simulation/openmodelica/scripts/run_all.mos",
            "CalculiX 2.23 via analysis/structural/run_load_checks.py",
        ],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    out = ROOT / "artifacts/manifest.json"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"ARTIFACT_MANIFEST_OK count={len(artifacts)}")


if __name__ == "__main__": main()
