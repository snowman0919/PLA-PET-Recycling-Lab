#!/usr/bin/env python3
"""Decision-relevant compact v0.3 release checks."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REV = "compact-single-path-v0.3"


def require(condition, message):
    if not condition: raise AssertionError(message)


def test_revision_and_stale():
    params = json.loads((ROOT/"cad/parameters/baseline.json").read_text())
    require(params["revision"] == REV, "baseline revision mismatch")
    for rel in ("README.md", "requirements/system_requirements.md", "requirements/architecture_contract.md", "bom/bom.csv", "docs/build_manual_ko.typ", "docs/design_report_ko.typ", "validation/release_checklist.md"):
        require(REV in (ROOT/rel).read_text(), f"revision missing: {rel}")
    stale = ["2250 x 500 x 1100", "2510 x 600 x 1350", "two-tower", "Tower A", "Tower B", "6-color classifier", "3-stage release", "external 700 mm rail", "0.1.0-preflight", "0.2.0-undergraduate-mvp"]
    files = [ROOT/"README.md", ROOT/"CHANGELOG.md"]
    for pattern in ("requirements/*", "cad/parameters/*", "cad/freecad/compact/*.py", "bom/*", "calculations/**/*.md", "firmware/**/*", "electronics/*", "validation/*.py", "validation/**/*.md", "artifacts/*.py", "docs/*"):
        files.extend(p for p in ROOT.glob(pattern) if p.is_file() and p.name not in {"archive_index.md", "test_release.py"} and p.suffix.lower() not in {".pdf", ".fcstd", ".png", ".stl", ".step", ".3mf"})
    hits=[]
    for path in sorted(set(files)):
        text=path.read_text(errors="ignore")
        for token in stale:
            if token in text: hits.append(f"{path.relative_to(ROOT)}:{token}")
    require(not hits, "stale architecture: " + ", ".join(hits))


def test_envelope():
    p=json.loads((ROOT/"cad/parameters/baseline.json").read_text())
    meta=json.loads((ROOT/"cad/generation/assembly_metadata.json").read_text())
    bb=meta["bounding_box_mm"]
    require(all(a <= b for a,b in zip(bb,p["limits"]["hard_envelope_mm"])), f"hard envelope exceeded: {bb}")
    require(all(a <= b for a,b in zip(bb,p["limits"]["target_envelope_mm"])), f"target envelope exceeded: {bb}")
    require(meta["minimum_mm"] == [0.0,0.0,0.0], f"unexpected negative envelope {meta}")
    require(meta["maximum_mm"] == [470.0,700.0,930.0], f"operation envelope incomplete {meta}")


def test_budget():
    rows=list(csv.DictReader((ROOT/"bom/cash_budget.csv").open()))
    items=[r for r in rows if r["category"] != "TOTAL"]
    total=sum(int(r["planned_cash_krw"]) for r in items)
    declared=int(next(r for r in rows if r["category"]=="TOTAL")["planned_cash_krw"])
    require(total==declared==189500, f"cash rollup mismatch {total}/{declared}")
    require(total <= 200000, "cash cap exceeded")
    cnc=list(csv.DictReader((ROOT/"bom/cnc_quote_package.csv").open()))
    require(len({r["family_id"] for r in cnc}) <= 8, "unique CNC family cap")
    reuse=list(csv.DictReader((ROOT/"bom/reuse_inventory.csv").open()))
    require(all(r["claimed_zero_cash"] == "false" for r in reuse), "unverified reuse claimed at zero cash")


def test_print_package():
    rows=list(csv.DictReader((ROOT/"exports/print/print_manifest.csv").open()))
    require(len(rows)==12, f"print family count {len(rows)}")
    total=0.0
    for r in rows:
        require(max(float(r[k]) for k in ("x_mm","y_mm","z_mm")) <= 210.0, f"print oversize {r['part_id']}")
        total += float(r["mass_total_g"])
        folder=ROOT/"exports/print"/r["part_id"]
        for ext in ("FCStd","step","stl","3mf"):
            path=folder/f"{r['part_id']}.{ext}"; require(path.exists() and path.stat().st_size>100, f"missing {path}")
        require((folder/"print_notes.md").exists(), f"notes missing {r['part_id']}")
    require(total <= 1500.0, f"print target exceeded {total}")
    plates=sorted((ROOT/"exports/print/plate_layouts").glob("*.3mf")); require(len(plates)>=4,"plate layouts missing")
    for path in plates:
        require(zipfile.is_zipfile(path), f"invalid 3MF container {path}")


def test_calculations_and_profiles():
    s=json.loads((ROOT/"simulation/engineering_summary.json").read_text())
    selected=[r for r in s["screw_sweep"] if r["selected"]]
    require(len(selected)==1 and selected[0]["diameter_mm"]==16.0 and selected[0]["active_length_mm"]==256.0,"screw selection")
    require(s["power"]["calculated_concurrent_peak_w"] <= s["power"]["psu_rating_w"],"power budget")
    require(s["cutter"]["yield_safety_factor_at_145mpa_shear"] >= 2.0,"shaft torsion screen")
    header=(ROOT/"firmware/arduino_mega/src/material_profile.h").read_text()
    for field in ("shredder_rpm","shredder_trip_amp","predry_minutes","feeder_rpm","screw_rpm","zone_c","die_c","fan_percent","puller_feedforward_mm_s","diameter_kp","purge_grams"):
        require(field in header, f"profile field missing {field}")


def test_artifacts_and_docs():
    required=[
        "renders/assembly/compact_full_assembly_isometric.png", "renders/review/compact_exploded.png", "renders/review/compact_section.png",
        "renders/review/shredder_fastener_tool_access.png", "renders/review/print_orientation.png", "renders/review/support_contact.png",
        "docs/build_manual_ko.pdf", "docs/design_report_ko.pdf", "cad/generation/fcstd/compact_full_assembly.FCStd", "exports/step/compact_full_assembly.step"
    ]
    for rel in required: require((ROOT/rel).exists() and (ROOT/rel).stat().st_size>1000, f"artifact missing {rel}")
    for pdf in ("docs/build_manual_ko.pdf","docs/design_report_ko.pdf"):
        text=subprocess.run(["pdftotext",str(ROOT/pdf),"-"],text=True,capture_output=True,check=True).stdout
        require(REV in text, f"PDF revision mismatch {pdf}")
    manifest=json.loads((ROOT/"artifacts/manifest.json").read_text())
    require(manifest["revision"]==REV and manifest["artifact_count"]>=50,"manifest incomplete")


def main():
    test_revision_and_stale(); print("PASS REVISION_STALE")
    test_envelope(); print("PASS FULL_ENVELOPE")
    test_budget(); print("PASS CASH_CNC_BUDGET")
    test_print_package(); print("PASS PRINT_PACKAGE")
    test_calculations_and_profiles(); print("PASS ENGINEERING_PROFILES")
    test_artifacts_and_docs(); print("PASS ARTIFACTS_DOCS")
    print("COMPACT_RELEASE_VALIDATION_OK")


if __name__ == "__main__": main()
