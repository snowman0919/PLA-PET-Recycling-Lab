#!/usr/bin/env python3
"""Build revision-locked SHA-256 manifest for the v0.6.1 safety baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "artifacts"))
from manifest_lib import artifact_record, collect_paths  # noqa: E402


def main():
    artifacts = [artifact_record(path, ROOT) for path in collect_paths(ROOT)]
    result = {
        "revision": "safety-orchestration-closure-v0.6.1",
        "release_state": "SAFETY_ORCHESTRATION_BASELINE",
        "implementation_state": "IMPLEMENTATION_BASELINE",
        "geometry_validation": "PASS",
        "fabrication_validation": "PASS",
        "virtual_physics_validation": "PASS",
        "virtual_physics_state": "VIRTUAL_PHYSICS_VALIDATED",
        "empirical_validation": "OPTIONAL_NOT_RUN",
        "empirical_state": "EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN",
        "cross_solver_state": "CROSS_SOLVER_VALIDATION_PENDING",
        "regeneration_commands": [
            "FreeCADCmd console-stream runpy cad/generation/generate_all.py via validation/run_all.py",
            "PrusaSlicer 2.9.6 via validation/slice_prints.py",
            "OpenModelica 1.27.0 / MSL 4.0.0 via simulation/openmodelica/scripts/run_all.mos",
            "CalculiX 2.23 via analysis/structural/run_load_checks.py",
            "FreeCAD STEP/LC01-LC10 Fusion neutral handoff via cad/freecad/compact/generate_fusion_validation.py",
            "Arduino Mega compile via validation/arduino_compile.py and host tests via firmware Makefile",
            "Normalized artifact equality via validation/artifact_reproducibility.py",
        ],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    out = ROOT / "artifacts/manifest.json"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(f"ARTIFACT_MANIFEST_OK count={len(artifacts)}")


if __name__ == "__main__": main()
