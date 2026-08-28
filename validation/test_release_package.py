#!/usr/bin/env python3
"""Validate final documents, renders and SHA-256 artifact manifest."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_pdf(relative: str, expected_pages: int) -> None:
    data = (ROOT / relative).read_bytes()
    assert len(data) > 100_000, f"small PDF: {relative}"
    assert data.startswith(b"%PDF-") and data.rstrip().endswith(b"%%EOF"), relative
    assert len(re.findall(rb"/Type\s*/Page\b", data)) == expected_pages, relative


def main() -> None:
    check_pdf("docs/build_manual_ko.pdf", 28)
    check_pdf("docs/design_report_ko.pdf", 14)

    stems = (
        "tolerance_coupon", "input_classifier_proof", "classification_storage_proof",
        "stage1_cutter_stack", "stage1_shredder_proof", "stage2_shredder_proof",
        "stage3_granulator_proof", "vibratory_sorter_proof", "dryer_feeder_proof",
        "extruder_screw", "extruder_proof", "forming_line_proof",
        "diameter_gauge_optical_proof", "spooler_proof", "control_enclosure_proof",
    )
    views = ("front", "rear", "left", "right", "top", "bottom", "isometric")
    for stem in stems:
        for view in views:
            path = ROOT / "renders" / "modules" / f"{stem}_{view}.png"
            assert path.stat().st_size > 5_000, path
    for view in views:
        path = ROOT / "renders" / "assembly" / f"full_assembly_skeleton_{view}.png"
        assert path.stat().st_size > 5_000, path

    report_paths = sorted((ROOT / "validation" / "fabrication_review").glob("*.json"))
    report_paths.append(ROOT / "validation" / "visual_review" / "full_assembly_skeleton.json")
    for path in report_paths:
        text = path.read_text(encoding="utf-8")
        assert str(ROOT) not in text and '": "/' not in text, f"absolute path leaked into {path}"

    for path in sorted((ROOT / "exports" / "step").glob("*.step")):
        header = path.read_text(encoding="ascii")[:1_500]
        assert "'2000-01-01T00:00:00'" in header, f"non-reproducible STEP header: {path}"
        assert "Open CASCADE STEP translator 7.9 0" in header, f"non-reproducible STEP product ID: {path}"

    manifest = json.loads((ROOT / "artifacts" / "manifest.json").read_text())
    artifacts = manifest["artifacts"]
    assert manifest["artifact_count"] == len(artifacts) == 355
    assert len({entry["path"] for entry in artifacts}) == len(artifacts)
    for entry in artifacts:
        path = ROOT / entry["path"]
        data = path.read_bytes()
        assert len(data) == entry["bytes"], entry["path"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
    print("RELEASE_PACKAGE_OK")


if __name__ == "__main__":
    main()
