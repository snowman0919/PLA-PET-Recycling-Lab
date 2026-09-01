#!/usr/bin/env python3
"""Generate and audit the fabrication interface catalog for v0.5."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "exports/fabrication/interface_catalog.csv"
BASELINE_REVISION = "safety-orchestration-closure-v0.6.1"
PROCESS_FEED_REVISION = "technical-blocker-closure-v0.6.2.1"
PROCESS_FEED_INTERFACE_IDS = {"IF-021", "IF-022", "IF-031"}

FIELDS = (
    "interface_id",
    "part_a",
    "part_b",
    "interface_type",
    "nominal_dimension_a",
    "nominal_dimension_b",
    "clearance_interference",
    "tolerance",
    "standard_reference",
    "assembly_method",
    "tool",
    "inspection_method",
    "status",
)


def row(interface_id, part_a, part_b, interface_type, a, b, fit, tolerance,
        standard, assembly, tool, inspection, status="PASS_DIGITAL"):
    return dict(zip(FIELDS, (
        interface_id, part_a, part_b, interface_type, a, b, fit, tolerance,
        standard, assembly, tool, inspection, status,
    )))


def catalog_rows():
    """Controlling mechanical and thermal interfaces in the active assembly."""
    return [
        row("IF-001", "CUT-05 shaft journals", "6004-2RS x4", "bearing inner-ring fit", "Ø20 h6", "ID Ø20", "transition/slip per received bearing", "shaft 0/-0.013 mm", "ISO 286-2; bearing maker data", "press inner ring only; metal collars", "micrometer + bearing heater/press", "measure four journals and received bearing IDs"),
        row("IF-002", "6004-2RS x4", "CUT-03 matched side plates", "bearing outer-ring seat", "OD Ø42", "Ø42 H7", "0/+0.025 mm nominal bore allowance", "seat +0/+0.025 mm", "ISO 286-2", "press outer ring only", "bore gauge + arbor press", "report both seats/plate and centre distance"),
        row("IF-003", "6004-2RS", "CUT-03/CUT-08", "bearing axial retention", "width 12", "plate 12 + retainer 2", "outer ring positively retained without seal contact", "axial endplay 0.05–0.20 mm", "6004 20×42×12", "M4 retainer plate", "feeler gauge + torque wrench", "rotate freely after retainer torque"),
        row("IF-004", "CUT-05", "CUT-02 spacers/CUT-01 discs", "cutter stack bore", "Ø20 h6", "Ø20.2", "0.20–0.23 mm diametral clearance", "bore +0.05/0", "internal project fit", "keyed stack + metal shims/collars", "micrometer + plug gauge", "dry-stack hand slide and phase mark"),
        row("IF-005", "CUT-05", "DRV-02 cutter hub", "keyed shaft hub", "Ø20 h6 + 6 mm key", "Ø20 H7 + 6 P9 keyway", "transition fit; no phase slip", "hub bore H7", "KS B 1311 / DIN 6885", "clamping hub + key", "micrometer + bore gauge", "blue-check contact and witness-mark torque test"),
        row("IF-006", "DRV-02", "#35 driven sprocket", "bolt-on sprocket", "PCD36 holes", "matching PCD36 holes", "face contact", "PCD ±0.05 mm", "ANSI B29.1 #35", "bolted hub with prevailing nuts", "caliper + torque wrench", "radial runout ≤0.20 mm"),
        row("IF-007", "#35 chain", "12T/30T or 36T sprockets", "roller chain mesh", "pitch 9.525 mm", "pitch 9.525 mm", "2–3% midspan slack", "shaft parallelism ≤0.20/150", "ANSI B29.1 #35", "slotted DRV-01 tension adjustment", "straightedge + ruler", "hand-turn full revolution under guard-off lockout"),
        row("IF-008", "42GP-775 reference shaft", "DRV-A42 adapter", "motor shaft adapter", "Ø10 class keyed/D-flat; verify variant", "donor-specific measured bore", "clamping fit; no set-screw-only torque path", "adapter released after shaft measurement", "supplier drawing controls", "split-clamp adapter", "micrometer + torque wrench", "measure shaft diameter/flat/key and proof against adapter drawing", "REFERENCE_VARIANT_VERIFY"),
        row("IF-009", "DRV-03 keyed phase gear pair", "CUT-05 shafts", "phase synchronization and torque path", "M3 Z16 20° face≥18; Ø20.2 + 6.2 keyway", "Ø20 h6 shaft + common 6×6 key; centre distance 48.00", "keyed torque path; backlash 0.15–0.35 mm target", "centre distance ±0.03 mm; keyway width +0.10/0", "ISO 54 involute module; DIN 6885/KS B 1311 key", "common key + 2xM4 PCD30 clamp + Ø3 h6 dowel per gear", "feeler/indicator + blue check", "seven-hook phase sweep, key contact and witness marks"),
        row("IF-010", "FM-GA-01 fixed axle", "625-2RS x2", "guide bearing inner-ring fit", "Ø5 h6", "ID Ø5", "transition/slip per received bearing", "shaft 0/-0.008 mm", "625-2RS 5×16×5", "inner rings located by metal collars", "micrometer", "free rotation without axial preload"),
        row("IF-011", "625-2RS x2", "FM-GR-01 guide roller", "guide bearing outer seats", "OD Ø16", "2× Ø16 H7 ×5.1 deep", "0/+0.018 mm bore allowance", "seat +0/+0.018 mm", "ISO 286-2", "press outer ring only into turned roller", "small arbor press + bore gauge", "seat depth and shoulder squareness"),
        row("IF-012", "FM-GA-01", "PPR-C08 x2", "fixed axle support", "Ø5 h6", "Ø5.2 printed/reamed", "0.20–0.41 mm diametral clearance", "bore +0.20/0 after coupon", "project printed clearance", "axle collars outside brackets", "Ø5.2 reamer + hex key", "axle passes both brackets without bending"),
        row("IF-013", "FM-AX-01", "FM-RL-01/FM-PL-01", "puller spindle", "Ø8 h6", "Ø8.2 bores", "0.20–0.42 mm diametral clearance", "matched plate axes ±0.05 mm", "internal project fit", "metal collars; donor drive one spindle", "micrometer + pin gauge", "roller TIR ≤0.05 mm"),
        row("IF-014", "SP-AX-01", "SP-DA-01/SP-RL-01", "dancer pivot/roller axle", "Ø8 h6", "Ø8.2", "0.20–0.42 mm diametral clearance", "bore +0.05/0", "internal project fit", "metal collars", "micrometer + pin gauge", "full -25…+25° sweep free"),
        row("IF-015", "donor traverse rods", "PPR-C10", "linear slide", "Ø8 measured", "Ø8.4 printed/reamed", "0.40 mm nominal diametral clearance", "selected by PPR-TC01 coupon", "donor measurement", "parallel rods + GT2 belt clamp", "caliper + straightedge", "80 mm stroke without bind"),
        row("IF-016", "SP-SH-01", "6001-2RS x2", "spool bearing inner fit", "Ø12 h6", "ID Ø12", "transition/slip per received bearing", "shaft 0/-0.011 mm", "6001-2RS 12×28×8", "inner-ring collars", "micrometer", "full-spool runout check"),
        row("IF-017", "6001-2RS", "SP-BP-01", "spool bearing outer support", "OD Ø28", "Ø28.2 through + metal retainer", "0.20 mm diametral service clearance", "bore +0.05/0", "6001-2RS", "metal washer/clip captures outer ring", "bore gauge + torque wrench", "outer ring cannot escape; rotates freely"),
        row("IF-018", "PPR-C09", "SP-SH-01", "spool cone", "Ø12.2 printed bore", "Ø12 h6 spindle", "0.20–0.41 mm diametral clearance", "coupon-selected", "project printed clearance", "M6 cross clamp; metal collar bears axial load", "reamer + hex key", "adapter slides and clamps without split"),
        row("IF-019", "EX-SCR-01 flight OD", "EX-BAR-01 bore", "screw radial clearance", "Ø15.92 -0.02/0", "Ø16.20 +0.02/0", "0.14–0.16 mm radial", "matched three-station report", "RFQ drawing", "matched supplier pair", "micrometer + three-point bore gauge", "B+20/B+140/B+260 clearance report"),
        row("IF-020", "EX-SCR-01 journals", "thrust/drive bearings", "screw support", "Ø12 h6 / Ø15 h6", "received bearing IDs", "matched transition fit", "TIR ≤0.03 mm", "RFQ drawing + bearing data", "metal thrust stack", "micrometer + dial indicator", "hand rotation and axial endplay Gate-3"),
        row("IF-021", "PF-04 auger flight", "PF-05 housing bore", "positive-metering running clearance", "OD24.0 nominal", "ID27.0 nominal", "1.50 mm radial nominal", "final metal process tolerance and flake coupon pending", "internal project clearance", "removable auger with metal thrust retention", "micrometer + bore gauge", "hand rotation plus PLA/PET feed coupon without rub", "PHYSICAL_COUPON_PENDING"),
        row("IF-022", "PF-03 agitator shaft", "hopper-side support and donor drive", "agitator shaft support", "Ø8 nominal", "received bushing/bearing and donor coupling", "donor-specific fit not yet released", "measure donor shaft bearing and coupling before drawing release", "supplier data plus measured donor", "metal bearing/coupling path; printed wall is not sole support", "micrometer + dial indicator", "free bounded rotation without hopper-wall contact", "DONOR_MEASUREMENT_REQUIRED"),
        row("IF-023", "EX-BAR-01", "HT-BAND-01 x3", "band heater clamp", "OD Ø34.00 ±0.05", "ID Ø34.0 custom", "zero-gap clamp contact", "heater maker clamp range must include 33.95–34.05", "custom mica band supplier drawing", "split band clamp; no 35 mm substitution", "micrometer + feeler", "360° contact and cold insulation resistance"),
        row("IF-024", "EX-DIE-01", "HT-CART-01", "cartridge heater bore", "Ø6.05 H7 reamed through", "heater Ø6.00 -0.02/-0.06", "0.070–0.122 mm diametral clearance", "bore +0/+0.012 mm", "supplier fit guidance + received heater measurement", "thin anti-seize film + positive axial clamp", "pin gauge + micrometer + megohmmeter", "full insertion without force; no loose lead loading"),
        row("IF-025", "EX-BAR zones 1–3", "TEMP-01..03", "barrel thermocouple", "Ø3.2 +0.05/0 blind5.5 bore", "Ø3 ungrounded mineral-insulated K probe", "0.20–0.25 mm diametral clearance", "3.35–3.40 mm nominal melt-bore ligament", "IEC 60584 K-type", "compression screw/washer", "depth gauge + insulation/continuity meter", "probe reads barrel metal; ungrounded junction required for MAX6675 architecture"),
        row("IF-026", "EX-DIE-01", "TEMP-04", "die thermocouple", "Ø3.2 blind bore", "Ø3 K probe", "0.2 mm diametral clearance", "tip 2.0–3.0 mm from melt channel", "IEC 60584 K-type", "compression screw/washer", "depth gauge + continuity meter", "no intersection with Ø8 melt/heater channels"),
        row("IF-027", "FD-HOP-01 wall", "HT-PTC-01 spreader", "hopper maintenance heater", "2 mm stainless wall", "aluminum spreader + insulated PTC", "full thermal-pad contact", "electrically isolated; no polymer contact", "supplier PTC data pending", "clamped metal sandwich", "megohmmeter + feeler", "measure one PTC power and equilibrium temperature before fixing quantity", "REFERENCE_POWER_MEASUREMENT_REQUIRED"),
        row("IF-028", "M3 heat-set insert", "PPR-C06/C11", "printed insert bore", "insert lot OD4.2/4.6", "matching blind bore", "coupon-selected interference", "PPR-TC01 controls", "insert supplier data", "temperature-controlled press", "coupon + pullout fixture", "print and pull-test PPR-TC01 with actual insert lot", "PHYSICAL_COUPON_PENDING"),
        row("IF-029", "M4 heat-set insert", "PPR-C01/PPR-C10", "printed insert bore", "insert lot OD4.6/5.6", "matching blind bore", "coupon-selected interference", "PPR-TC01 controls", "insert supplier data", "temperature-controlled press", "coupon + pullout fixture", "print and pull-test PPR-TC01 with actual insert lot", "PHYSICAL_COUPON_PENDING"),
        row("IF-030", "M4/M5/M6 fasteners", "printed/metal clearance holes", "bolt clearance", "actual fastener shank", "Ø4.5/5.5/6.6", "ISO normal clearance", "drawing-specific", "ISO 273", "washer + metal nut/T-nut/rivnut", "pin gauge + torque wrench", "all bolts insert and reach full thread"),
        row("IF-031", "PF-01 hopper throat", "PF-05 auger housing flange", "sealed positive-feed interface", "44x44 mm hopper outlet", "Ø48 flange and Ø27 bore", "continuous gasketed transition without ledge/dead pocket", "final bolt pattern and gasket compression coupon pending", "project removable sanitary joint", "metal adapter and captive fasteners under service lockout", "caliper + feeler + visual", "dry-flake leak cleanability and no-retention coupon", "PHYSICAL_COUPON_PENDING"),
        row("IF-032", "PPR-C03 x4", "FD-BIN-01 sheet", "flake-bin corner channel", "1.4 mm printed slot", "1.0 mm sheet", "0.4 mm nominal slot clearance", "printed ±0.30 mm", "project printed sheet joint", "M3 fasteners + welded/folded sheet", "feeler + visual", "no inward dead pocket or burr"),
    ]


def validate(rows):
    if len({r["interface_id"] for r in rows}) != len(rows):
        raise AssertionError("duplicate interface_id")
    for r in rows:
        missing = [field for field in FIELDS if not str(r[field]).strip()]
        if missing:
            raise AssertionError(f"{r['interface_id']} missing fields: {missing}")
        if "FAIL" in r["status"] or "MISMATCH" in r["status"]:
            raise AssertionError(f"interface mismatch: {r['interface_id']}")
    required = {"6004", "625", "6001", "EX-SCR", "HT-BAND", "HT-CART", "TEMP-01", "PPR-C08"}
    corpus = "\n".join(" ".join(r.values()) for r in rows)
    missing_tokens = sorted(token for token in required if token not in corpus)
    if missing_tokens:
        raise AssertionError(f"interface families missing: {missing_tokens}")


def main():
    rows = catalog_rows()
    validate(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("revision",) + FIELDS, lineterminator="\n")
        writer.writeheader()
        for item in rows:
            revision = (
                PROCESS_FEED_REVISION
                if item["interface_id"] in PROCESS_FEED_INTERFACE_IDS
                else BASELINE_REVISION
            )
            writer.writerow({"revision": revision, **item})
    print(f"FABRICATION_INTERFACE_CATALOG_OK rows={len(rows)}")


if __name__ == "__main__":
    main()
