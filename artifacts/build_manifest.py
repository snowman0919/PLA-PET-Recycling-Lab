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
    "docs/*.pdf",
    "bom/bom.md",
    "bom/target_budget_design.csv",
    "bom/engineering_recommended_design.csv",
    "bom/cost_summary.json",
    "bom/cost_rollup.csv",
    "requirements/compliance_matrix.csv",
    "requirements/compliance_matrix.md",
    "requirements/architecture_contract.md",
    "exports/cnc_quote_packages/README.md",
    "exports/cnc_quote_packages/*_package.csv",
    "calculations/structural/beam_fea.md",
    "simulation/structural/beam_crosscheck.json",
    "calculations/thermal/hot_zone_guard.md",
    "simulation/thermal/hot_zone_guard.json",
    "simulation/architecture/two_tower_contract.json",
    "simulation/architecture/two_tower_geometry.json",
    "simulation/gpu/README.md",
    "simulation/gpu/*.cu",
    "simulation/gpu/*_gpu.json",
    "renders/review/*.png",
    "docs/manual_coverage.csv",
    "electronics/pcb/interface_board/*_evidence.json",
    "electronics/pcb/interface_board/*.kicad_pro",
    "electronics/pcb/interface_board/*.kicad_sch",
    "electronics/pcb/interface_board/*.kicad_pcb",
    "electronics/pcb/interface_board/*.kicad_dru",
    "electronics/pcb/interface_board/*_bom.csv",
    "electronics/pcb/interface_board/*.rpt",
    "electronics/pcb/interface_board/analysis/*.json",
    "electronics/pcb/interface_board/fabrication/*",
    "electronics/pcb/interface_board/review/*",
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
        "generated_utc": "2026-08-27T20:15:00Z",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    (ROOT / "artifacts" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"manifest artifacts={len(artifacts)}")


if __name__ == "__main__":
    main()
