#!/usr/bin/env python3
"""비싼 위상 solver 증거는 실제 STEP 입력만 영구 의존성으로 남긴다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis/final_validation/results/v0.8"

for name in ("torsion_load_path_25_153.json", "torsion_load_path_25_105.json",
             "phase_gear_elastic_candidate.json", "phase_pair_backlash_candidate.json"):
    sources = json.loads((RESULTS / name).read_text())["source_sha256"]
    assert "analysis/final_validation/results/v0.8/phase_path_25_candidate.json" not in sources
    assert any(path.endswith(".step") for path in sources)
    assert all((ROOT / path).is_file() for path in sources)

for name in ("phase_path_25_153.step", "phase_path_25_105.step", "phase_path_25_solid_gear.step"):
    assert "'1970-01-01T00:00:00'" in (RESULTS / name).read_text(encoding="utf-8")

print("PHASE_SOLVER_DEPENDENCY_SCOPE_PASS")
