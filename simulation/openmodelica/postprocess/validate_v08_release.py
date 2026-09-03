#!/usr/bin/env python3
"""v0.8 OpenModelica hot-mount/LC09 scope 결과를 검증한다."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "simulation" / "openmodelica" / "results_v0.8" / "raw"
OUT = RAW.parent


def read(name: str) -> list[dict[str, float]]:
    with (RAW / f"{name}_res.csv").open(newline="") as stream:
        return [{key.strip('"'): float(value) for key, value in row.items()} for row in csv.DictReader(stream)]


def main() -> None:
    hot = read("HotZoneControlledExpansion")
    spool = read("LC09SpoolScope")
    hot_final, spool_final = hot[-1], spool[-1]
    checks = {
        "hot_zone_travel_margin_nonnegative": hot_final["travelMarginMm"] >= 0,
        "hot_zone_regional_sf_ge_2": hot_final["safetyFactor"] >= 2,
        "lc09_scope_contract": spool_final["scopePass"] == 1,
        "lc09_force_balance": abs(spool_final["forceResidualN"]) < 1e-8,
        "lc09_moment_balance": abs(spool_final["momentResidualNmm"]) < 1e-8,
    }
    result = {
        "revision": "final-design-fabrication-closure-v0.8",
        "solver": "OpenModelica 1.27.0 DASSL",
        "model_sha256": hashlib.sha256((ROOT / "simulation/openmodelica/v0.8/V08ReleaseScenarios.mo").read_bytes()).hexdigest(),
        "hot_zone": {key: hot_final[key] for key in ("temperatureC", "axialGrowthMm", "travelMarginMm", "safetyFactor", "pass")},
        "LC09": {
            "spindle_length_mm": 143.0,
            "bearing_spacing_mm": 88.0,
            "load_position_from_front_mm": 40.5,
            "spool_mass_kg": 1.35,
            "line_tension_n": 8.0,
            **{key: spool_final[key] for key in ("radialLoadN", "frontReactionN", "rearReactionN", "forceResidualN", "momentResidualNmm", "scopePass")},
        },
        "checks": checks,
        "physical_validation_state": "NOT_RUN",
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if result["status"] != "PASS":
        raise SystemExit("V08_OPENMODELICA_VALIDATION_FAIL")
    print(f"V08_OPENMODELICA_VALIDATION_OK growth_mm={hot_final['axialGrowthMm']:.4f} lc09_load_n={spool_final['radialLoadN']:.4f}")


if __name__ == "__main__":
    main()
