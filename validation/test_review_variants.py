#!/usr/bin/env python3
"""Validate required CAD review variants and their explicit limitations."""

from __future__ import annotations

import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "renders" / "review"
EXPECTED = {
    "control_enclosure_proof_cable_routing.png",
    "control_enclosure_proof_transparent.png",
    "dryer_feeder_proof_exploded.png",
    "dryer_feeder_proof_section.png",
    "dryer_feeder_proof_transparent.png",
    "extruder_proof_exploded.png",
    "extruder_proof_section.png",
    "extruder_proof_tool_access.png",
    "extruder_proof_transparent.png",
    "full_assembly_skeleton_cable_routing.png",
    "full_assembly_skeleton_exploded.png",
    "full_assembly_skeleton_section.png",
    "full_assembly_skeleton_tool_access.png",
    "input_classifier_proof_section.png",
    "input_classifier_proof_transparent.png",
    "spooler_proof_exploded.png",
    "spooler_proof_tool_access.png",
    "stage1_shredder_proof_exploded.png",
    "stage1_shredder_proof_section.png",
    "stage2_shredder_proof_section.png",
    "stage3_granulator_proof_section.png",
    "tolerance_coupon_slicing_preview.png",
}


def main() -> None:
    found = {path.name for path in REVIEW.glob("*.png")}
    assert found == EXPECTED
    for filename in EXPECTED:
        path = REVIEW / filename
        assert path.stat().st_size > 25_000, path
        data = path.read_bytes()[:32]
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", data[16:24])
        assert (width, height) == (1600, 1200)
    source = (ROOT / "cad" / "generation" / "render_views.py").read_text()
    for phrase in (
        "centroid-clipped review scene; no section cap",
        "hidden-line removal disabled",
        "machine-specific G-code",
        "physical reach test remains open",
        "schematic paths; verify harness lengths and bend radii",
    ):
        assert phrase in source
    print("CAD_REVIEW_VARIANTS_OK")


if __name__ == "__main__":
    main()
