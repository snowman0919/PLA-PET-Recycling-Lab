#!/usr/bin/env python3
"""Ø25 단일 기어 쌍의 냉간 CAD backlash 후보를 체적 접촉으로 묶는다."""
import hashlib
import json
import math
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "analysis/final_validation/results/v0.8"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    geometry_path = RESULTS / "phase_path_25_candidate.json"
    geometry = json.loads(geometry_path.read_text())
    assert all(sha(ROOT / path) == digest for path, digest in geometry["source_sha256"].items())
    step = ROOT / geometry["solid_gear_step"]
    assert sha(step) == geometry["solid_gear_step_sha256"]
    gear = Part.read(str(step))
    volumes = {}
    for offset in (-.16, -.15, 0, .15, .16):
        mate = gear.copy()
        mate.rotate(App.Vector(), App.Vector(0, 1, 0), 180 / 16 + offset)
        mate.translate(App.Vector(48, 0, 0))
        volumes[str(offset)] = gear.common(mate).Volume
    assert volumes["0"] < 1e-9
    assert volumes["-0.15"] < 1e-9 and volumes["0.15"] < 1e-9
    assert volumes["-0.16"] > 1e-8 and volumes["0.16"] > 1e-8
    free_rotation = [.30, .32]
    output = {
        "status": "HOLD", "physical_validation_state": "NOT_RUN",
        "centre_distance_mm": 48.0, "nominal_relative_phase_deg": 11.25,
        "sampled_common_volumes_mm3": volumes,
        "cad_pair_free_rotation_bound_deg": free_rotation,
        "cad_pair_backlash_bound_mm": [math.radians(angle) * 24 for angle in free_rotation],
        "scope": "Static BRep interference bracketing for the candidate pair only; no flank contact, runout, load, wear or manufacturing-error model.",
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in (Path(__file__).resolve(), step)},
    }
    (RESULTS / "phase_pair_backlash_candidate.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"PHASE_PAIR_BACKLASH_CANDIDATE_HOLD bound_mm={output['cad_pair_backlash_bound_mm']}")


if __name__ == "__main__":
    main()
