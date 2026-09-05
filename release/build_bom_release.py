#!/usr/bin/env python3
"""v0.8 시스템 BOM을 제조 릴리스용 BOM과 일정표로 변환한다.

`bom/bom.csv`가 설계 항목의 authoritative source다. 제조/출력 manifest는
그 항목을 실제 제작 단위로 펼치는 subordinate source일 뿐이다.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports/final/bom"
REV = "final-design-fabrication-closure-v0.8"
FIELDS = [
    "part_id", "description", "revision", "category", "quantity",
    "required_or_optional", "make_or_buy", "material/specification",
    "critical interface", "approved MPN", "approved alternative",
    "donor status", "supplier status", "drawing", "assembly step",
    "firmware dependency", "notes",
]


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def category(part_id: str) -> str:
    return next((name for prefix, name in (
        ("PPR-C", "3D_PRINT"), ("FR", "FRAME"), ("HP", "HOPPER"),
        ("IN-HOP", "HOPPER"), ("FB", "FLAKE_HANDLING"), ("FD", "FEEDER"),
        ("FH", "FEEDER"), ("SH", "SHREDDER"), ("CUT", "SHREDDER"),
        ("DRV", "DRIVE"), ("EX", "EXTRUDER"), ("TH", "THERMAL"),
        ("CO", "COOLING"), ("DG", "GAUGE"), ("PL", "PULLER"),
        ("FM", "FORMING"), ("SP", "SPOOLER"), ("CT", "CONTROL"),
        ("SF", "SAFETY"), ("GD", "GUARD"), ("DR", "EXTERNAL_PROCESS"),
    ) if part_id.startswith(prefix)), "SYSTEM")


def drawing(part_id: str) -> str:
    if part_id.startswith("PPR-C"):
        return f"exports/print/{part_id}/dimension_sheet.svg"
    special = {
        "EX-MT-01": "exports/final/manufacturing/hot_zone/ExtruderRearFixedDatum.svg",
        "EX-MT-02": "exports/final/manufacturing/hot_zone/ExtruderFrontSlidingGuide.svg",
        "EX-MT-03": "exports/final/manufacturing/hot_zone/ExtruderFixedCollar.svg",
        "EX-MT-04": "exports/final/manufacturing/hot_zone/ExtruderSupportRailRear.svg",
    }
    if part_id in special:
        return special[part_id]
    name = next((name for prefix, name in (
        ("FR", "FR-001_frame.svg"), ("SH", "SH-001_shredder_assembly.svg"),
        ("CUT", "SH-002_cutter_stack.svg"), ("DRV", "SH-004_chain_phase_gear.svg"),
        ("HP", "FD-001_hopper.svg"), ("IN-HOP", "FD-001_hopper.svg"),
        ("FB", "FD-002_recirculation_screen.svg"), ("FD", "FD-003_positive_feeder.svg"),
        ("FH", "FD-003_positive_feeder.svg"), ("EX", "EX-002_screw_barrel_die.svg"),
        ("TH", "EX-003_heater_thermocouple.svg"), ("CO", "FM-001_cooling_strand_path.svg"),
        ("DG", "FM-002_gauge_puller.svg"), ("PL", "FM-002_gauge_puller.svg"),
        ("FM", "FM-002_gauge_puller.svg"), ("SP", "SP-001_spooler_traverse.svg"),
        ("CT", "EL-001_electrical_enclosure.svg"), ("SF", "EL-001_electrical_enclosure.svg"),
        ("GD", "GD-001_guards_panels.svg"), ("DR", "GA-001_general_arrangement.svg"),
    ) if part_id.startswith(prefix)), "GA-001_general_arrangement.svg")
    return f"docs/drawings/v0.8/{name}"


def assembly_step(part_id: str) -> str:
    label = next((label for prefix, label in (
        ("FR", "Frame과 module 배치"), ("SH", "Hopper와 cutter"),
        ("CUT", "Hopper와 cutter"), ("DRV", "Hopper와 cutter"),
        ("HP", "Hopper와 cutter"), ("IN-HOP", "Hopper와 cutter"),
        ("FB", "Hopper와 cutter"), ("FD", "Dry feed와 extruder"),
        ("FH", "Dry feed와 extruder"), ("EX", "Dry feed와 extruder"),
        ("TH", "Dry feed와 extruder"), ("CO", "Cooling, gauge, puller"),
        ("DG", "Cooling, gauge, puller"), ("PL", "Cooling, gauge, puller"),
        ("FM", "Cooling, gauge, puller"), ("SP", "Guide, dancer, traverse, spool"),
        ("CT", "Control과 UI"), ("SF", "Control과 UI"),
        ("GD", "조립·체결 schedule"), ("PPR-C", "Print package"),
        ("DR", "작업 전 확인"),
    ) if part_id.startswith(prefix)), "Frame과 module 배치")
    return f"docs/build_manual_ko.typ §{label}"


def critical(part_id: str, detail: str = "") -> str:
    base = next((text for prefix, text in (
        ("FR", "profile joint squareness and table load path"),
        ("SH", "guarded cutter torque path and service lockout"),
        ("CUT", "shaft/bearing fit; cutter shim clearance; phase registration"),
        ("DRV", "donor shaft interface; chain alignment; replaceable shear element"),
        ("HP", "anti-reach opening and removable hopper interface"),
        ("IN-HOP", "anti-reach opening and removable hopper interface"),
        ("FB", "screen/bin clearance and service withdrawal"),
        ("FD", "sealed flake path; feeder-to-barrel interface"),
        ("FH", "sealed flake path; feeder feedback and cleanability"),
        ("EX-MT", "rear axial datum/front sliding thermal expansion path"),
        ("EX", "screw/barrel cold clearance; die seal; metal thrust path"),
        ("TH", "heater fit, insulation, branch fuse and independent thermal cutoff"),
        ("CO", "hot-shield clearance and verified airflow feedback"),
        ("DG", "orthogonal gauge alignment and calibration"),
        ("PL", "roller alignment, pinch guard and tach calibration"),
        ("FM", "strand alignment and bearing/shaft fit"),
        ("SP", "spindle/bearing fit; dancer/traverse envelope"),
        ("CT", "PE bond, segregated routing and pin-map consistency"),
        ("SF", "hardwired E-stop/interlock/thermal chain independent of firmware"),
        ("GD", "moving/hot hazard reach protection and service interlock"),
        ("PPR-C", "printed interface per dimension sheet; no structural hot/high-load path"),
        ("DR", "external dryer qualification and material moisture evidence"),
    ) if part_id.startswith(prefix)), "assembly interface per released drawing")
    return f"{base}; {detail}" if detail else base


def firmware_dependency(part_id: str) -> str:
    if part_id.startswith(("SF", "GD")):
        return "hardware safety function; firmware monitoring only; never sole protection"
    if part_id.startswith(("SH", "DRV", "FH-03", "EX-03", "EX-04", "EX-05", "EX-06", "TH", "CO-02", "DG", "PL", "SP", "CT")):
        return "firmware/arduino_mega/src + released pin map/calibration; physical calibration required"
    return "NONE"


def normalize_quantity(value: str) -> str:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(.*)", value)
    if not match or float(match.group(1)) <= 0:
        raise ValueError(f"invalid quantity: {value!r}")
    return match.group(1)


def root_rows() -> list[dict[str, str]]:
    result = []
    for src in read_csv("bom/bom.csv"):
        pid, source = src["part_id"], src["source"].lower()
        make = next((value for token, value in (
            ("cnc", "MAKE_CNC"), ("custom rfq", "BUY_CUSTOM"),
            ("stock/buy", "BUY"), ("project lab", "VERIFY_REUSE_OR_BUY"),
            ("external", "USER_SUPPLIED_EXTERNAL"), ("mixed", "MIXED"),
            ("buy", "BUY"),
        ) if token in source), "MIXED")
        supplier = next((value for token, value in (
            ("CNC", "RFQ_NOT_SENT—USER_APPROVAL_REQUIRED"),
            ("RECEIPT", "CANDIDATE_SELECTED—RECEIPT_TEST_REQUIRED"),
            ("USER_APPROVAL", "USER_SELECTION_OR_APPROVAL_REQUIRED"),
            ("UNVERIFIED", "USER_INVENTORY_VERIFICATION_REQUIRED"),
            ("DONOR", "DONOR_IDENTIFICATION_REQUIRED"),
            ("RFQ", "RFQ_NOT_SENT—USER_APPROVAL_REQUIRED"),
            ("DESIGNED", "SPECIFICATION_RELEASED—PROCUREMENT_NOT_APPROVED"),
            ("EXCLUDED", "NOT_APPLICABLE—EXTERNAL_USER_EQUIPMENT"),
        ) if token in src["status"]), "SUPPLIER_OR_INVENTORY_VERIFICATION_REQUIRED")
        donor = "UNVERIFIED—label, rating, shaft, condition and functional test required" if any(
            token in (source + " " + src["status"].lower()) for token in ("donor", "reuse", "project lab", "unverified")
        ) else "NOT_APPLICABLE"
        mpn = "NONE_APPROVED—exact make/model and receipt evidence pending" if make in {"BUY", "BUY_CUSTOM", "MIXED", "VERIFY_REUSE_OR_BUY"} else "NOT_APPLICABLE—build to released specification"
        qty_note = src["quantity"].strip()[len(normalize_quantity(src["quantity"])):].strip()
        result.append({
            "part_id": pid, "description": src["description"], "revision": REV,
            "category": category(pid), "quantity": normalize_quantity(src["quantity"]),
            "required_or_optional": "OPTIONAL_EXTERNAL" if pid == "DR-EXT" else "REQUIRED",
            "make_or_buy": make, "material/specification": src["material_or_model"],
            "critical interface": critical(pid), "approved MPN": mpn,
            "approved alternative": "NONE_APPROVED—deviation requires interface review and affected recalculation/calibration",
            "donor status": donor, "supplier status": supplier, "drawing": drawing(pid),
            "assembly step": assembly_step(pid), "firmware dependency": firmware_dependency(pid),
            "notes": f"AUTHORITATIVE DESIGN SOURCE: bom/bom.csv; source={src['source']}; cash_class={src['cash_class']}; status={src['status']}; quantity_unit={qty_note or 'each'}; {src['notes']}",
        })
    return result


def expanded_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(pid: str, desc: str, qty: str, material: str, process: str, state: str,
            source: str, draw: str | None = None, detail: str = "") -> None:
        manufacture = pid.startswith("PPR-C") or any(token in process.lower() for token in ("print", "laser", "waterjet", "turn", "mill", "drill", "cut", "weld", "brake", "ream", "hone", "edm"))
        rows.append({
            "part_id": pid, "description": desc, "revision": REV, "category": category(pid),
            "quantity": normalize_quantity(qty), "required_or_optional": "REQUIRED",
            "make_or_buy": "MAKE_3D_PRINT" if pid.startswith("PPR-C") else ("MAKE_TO_DRAWING" if manufacture else "BUY_TO_SPEC"),
            "material/specification": f"{material}; process={process}",
            "critical interface": critical(pid, detail),
            "approved MPN": "NOT_APPLICABLE—make from released file" if manufacture else "NONE_APPROVED—exact make/model and receipt evidence pending",
            "approved alternative": "NONE_APPROVED—deviation requires interface review and affected recalculation/calibration",
            "donor status": "NOT_APPLICABLE", "supplier status": state,
            "drawing": draw or drawing(pid), "assembly step": assembly_step(pid),
            "firmware dependency": firmware_dependency(pid),
            "notes": f"SUBORDINATE DETAIL SOURCE: {source}; parent design authority remains bom/bom.csv; procurement/fabrication requires user approval",
        })

    for row in read_csv("exports/print/print_manifest.csv"):
        add(row["part_id"], row["name"], row["quantity"], row["material"],
            f"FDM; {row['nozzle_mm']} mm nozzle; {row['layer_height']}; {row['walls']} walls; {row['infill']} infill",
            f"PRINT_PACKAGE_{row['slicer_status']}", "exports/print/print_manifest.csv",
            detail=f"mating={row['mating_part']}; tolerance={row['tolerance']}")
    for row in read_csv("exports/fabrication/machine_manifest.csv"):
        add(row["part_id"], row["name"], row["quantity"], row["material"], row["process"], row["release_state"],
            "exports/fabrication/machine_manifest.csv", f"exports/fabrication/parts/{row['part_id']}/drawing_notes.md")
    for row in read_csv("exports/cnc/shredder_manifest.csv"):
        add(row["part_id"], row["name"], row["quantity"], row["material"], row["process"], row["release_state"],
            "exports/cnc/shredder_manifest.csv", f"exports/cnc/{row['part_id']}/drawing_notes.md")
    for row in read_csv("exports/cnc/extruder/rfq_manifest.csv"):
        add(row["part_id"], row["name"], row["qty"], row["material"], row["process"], row["release"],
            "exports/cnc/extruder/rfq_manifest.csv", f"exports/cnc/extruder/{row['drawing']}")
    for row in read_csv("exports/thermal/manifest.csv"):
        add(row["part_id"], row["name"], row["quantity"], row["material"], "buy/custom fabricate to thermal drawing note",
            row["release_state"], "exports/thermal/manifest.csv", f"exports/thermal/parts/{row['part_id']}/drawing_notes.md")
    for row in read_csv("exports/drive_interface/manifest.csv"):
        add(row["part_id"], row["name"], row["quantity"], row["material"], row["process"], row["release_state"],
            "exports/drive_interface/manifest.csv", f"exports/drive_interface/parts/{row['part_id']}/drawing_notes.md")
    return rows


def active_reference_rows(existing: set[str]) -> list[dict[str, str]]:
    aliases = {
        "ExtruderSupportRailRear": ("EX-MT-04", "exports/final/manufacturing/hot_zone/ExtruderSupportRailRear.svg"),
        "ExtruderRearFixedDatum": ("EX-MT-01", "exports/final/manufacturing/hot_zone/ExtruderRearFixedDatum.svg"),
        "ExtruderFrontSlidingGuide": ("EX-MT-02", "exports/final/manufacturing/hot_zone/ExtruderFrontSlidingGuide.svg"),
        "ExtruderFixedCollar": ("EX-MT-03", "exports/final/manufacturing/hot_zone/ExtruderFixedCollar.svg"),
    }
    assembly_drawings = {
        "PPR-FULL-ASM": "docs/drawings/v0.8/ASM-001_full_assembly.svg",
        "PPR-SHREDDER-ASM": "docs/drawings/v0.8/SH-001_shredder_assembly.svg",
        "PPR-FEEDER-ASM": "docs/drawings/v0.8/FD-003_positive_feeder.svg",
        "PPR-EXTRUDER-ASM": "docs/drawings/v0.8/EX-001_extruder_assembly.svg",
        "PPR-FORMING-ASM": "docs/drawings/v0.8/FM-001_cooling_strand_path.svg",
        "PPR-FRAME-ASM": "docs/drawings/v0.8/FR-001_frame.svg",
    }
    result = []
    active = json.loads((ROOT / "release/active_part_set.json").read_text(encoding="utf-8"))["parts"]
    for item in active:
        pid = item["part_id"]
        if pid in existing:
            continue
        canonical, draw = aliases.get(pid, (pid, assembly_drawings.get(pid, drawing(pid))))
        result.append({
            "part_id": pid, "description": f"reference alias: {canonical}", "revision": REV,
            "category": "CAD_REFERENCE", "quantity": str(item["quantity"]), "required_or_optional": "REQUIRED",
            "make_or_buy": "REFERENCE_ONLY", "material/specification": "not separately procured; canonical BOM item or assembly",
            "critical interface": "reference identity must resolve to canonical BOM/drawing",
            "approved MPN": "NOT_APPLICABLE", "approved alternative": "NOT_APPLICABLE",
            "donor status": "NOT_APPLICABLE", "supplier status": "NOT_APPLICABLE_REFERENCE",
            "drawing": draw, "assembly step": "docs/build_manual_ko.typ §조립·체결 schedule",
            "firmware dependency": "NONE", "notes": f"active_part_set reference; canonical={canonical}; exclude from procurement roll-up",
        })
    return result


def enrich_final_manufacturing(bom: list[dict[str, str]]) -> int:
    """최종 RFQ manifest가 있으면 같은 Part ID의 제작 도면/공차를 우선한다."""
    manifest = ROOT / "exports/final/manufacturing/RFQ/manifest.csv"
    if not manifest.is_file():
        return 0
    by_id = {row["part_id"]: row for row in bom}
    rows = read_csv("exports/final/manufacturing/RFQ/manifest.csv")
    for item in rows:
        row = by_id[item["part_id"]]
        assert float(row["quantity"]) == float(item["quantity"]), f"manufacturing quantity mismatch: {item['part_id']}"
        drawing_pdf = f"exports/final/manufacturing/RFQ/{item['drawing_pdf']}"
        assert (ROOT / drawing_pdf).is_file(), f"missing final manufacturing drawing: {drawing_pdf}"
        row["drawing"] = drawing_pdf
        row["critical interface"] = f"{row['critical interface']}; drawing tolerance={item['critical_tolerance']}; datum={item['datum_scheme']}"
        row["supplier status"] = f"DIGITAL_DRAWING_PASS; PART_GATE={item['status']}; PROCUREMENT_USER_APPROVAL_REQUIRED"
        row["notes"] += "; FINAL MANUFACTURING DETAIL: exports/final/manufacturing/RFQ/manifest.csv"
    return len(rows)


def fasteners() -> list[dict[str, object]]:
    fields = ["joint_id", "part_ids", "specification", "quantity", "torque_Nm", "locking", "tool", "inspection", "source", "verification_state"]
    rows: list[dict[str, object]] = []
    for part in read_csv("exports/print/print_manifest.csv"):
        for index, spec in enumerate(part["fastener"].split(";"), 1):
            match = re.match(r"\s*(\d+)x\s*(.*)", spec)
            if not match:
                raise ValueError(f"fastener quantity missing: {part['part_id']} {spec}")
            rows.append(dict(zip(fields, (
                f"PR-{part['part_id']}-{index}", f"{part['part_id']} / {part['mating_part']}", match.group(2).strip(),
                int(match.group(1)) * int(part["quantity"]), part["tightening_torque"].replace(" N.m", ""),
                part["insert_or_nut"], "hex/driver sized to received fastener",
                f"{part['interfaces']}; witness mark and no crack", "exports/print/print_manifest.csv", "RELEASED_DIGITAL"))))
    manual = [
        ("SYS-01", "frame profile joints", "M5x12 SHCS + washer + prevailing T-nut; 56 kits paired across 28 two-fastener corner brackets", 56, "5.0", "prevailing T-nut", "4 mm hex + square", "all 56 witness marks present; frame diagonal <=1.0 mm", "RELEASED_DIGITAL"),
        ("SYS-02", "PE-01..04 bonds", "M4x10 + two tooth washers + all-metal nut per bond", 4, "3.0", "tooth washer + all-metal nut", "3 mm hex + DMM", "four PE bonds pass continuity and have witness marks", "RELEASED_DIGITAL"),
        ("SYS-03", "EX-THR-01 / barrel", "M6x20 class 8.8", 8, "9", "prevailing metal nut", "5 mm hex/10 mm spanner", "metal thrust path; witness mark", "RELEASED_DIGITAL"),
        ("SYS-04", "EX-DIE-01 / EX-BAR-01", "M4x45 class 10.9", 4, "3.0", "all-metal lock", "3 mm hex/7 mm spanner", "cross torque; new EX-DIE-05 gasket", "RELEASED_DIGITAL"),
        ("SYS-05", "EX-DIE-04 / EX-DIE-01", "M4 retainer screw", 2, "1.2", "all-metal lock", "3 mm hex", "retainer captures insert", "RELEASED_DIGITAL"),
        ("SYS-06", "CUT-08 / CUT-03", "M4x12 class 8.8 SHCS", 12, "3", "all-metal locknut", "3 mm hex + 7 mm spanner", "bearing seal untouched; free rotation", "RELEASED_DIGITAL"),
        ("SYS-07", "hot-zone datum/guide / rear rail", "M5 profile fastener", 4, "2.5", "prevailing T-nut", "4 mm hex", "rear datum fixed; front axial slide free", "RELEASED_DIGITAL"),
        ("SYS-08", "DRV-03 phase gears", "M4x22 class 10.9 SHCS", 4, "3", "all-metal locknut + dowel", "3 mm hex + 7 mm spanner", "2 bolts/gear; registration dowel seated", "RELEASED_DIGITAL"),
        ("SYS-09", "DRV-02 / #35 sprocket", "M6 class 10.9", 4, "10", "all-metal locknut", "5 mm hex + 10 mm spanner", "chain alignment <=0.20/150 mm", "RELEASED_DIGITAL"),
    ]
    for values in manual:
        rows.append(dict(zip(fields, (*values[:8], "docs/final/assembly_steps.csv", values[8]))))
    return rows


def auxiliary(bom: list[dict[str, str]]) -> dict[str, tuple[list[str], list[dict[str, object]]]]:
    print_mass = Counter()
    for row in read_csv("exports/print/print_manifest.csv"):
        print_mass[row["material"]] += float(row["slicer_mass_total_g"])
    consumable_fields = ["item_id", "description", "quantity", "unit", "specification", "used_at", "replacement_rule", "status"]
    consumables = [
        dict(zip(consumable_fields, ("CON-PLA", "PLA print material including 12% process reserve", f"{print_mass['PLA'] * 1.12 / 1000:.3f}", "kg", "dry filament matching released slicer profile", "PPR-C01/02/03/04/08/09/10/11/12", "replace failed print only after root-cause check", "PLANNING_QUANTITY"))),
        dict(zip(consumable_fields, ("CON-ABS", "ABS print material including 12% process reserve", f"{print_mass['ABS'] * 1.12 / 1000:.3f}", "kg", "dry ABS matching released slicer profile", "PPR-C05/06/07", "replace failed print only after root-cause check", "PLANNING_QUANTITY"))),
        dict(zip(consumable_fields, ("CON-GASKET", "die face gasket", "2", "each", "EX-DIE-05 C110 annealed copper t0.5", "EX-DIE-01 to EX-BAR-01", "fit a new gasket after each opened hot-path joint", "REQUIRED; procurement approval pending"))),
        dict(zip(consumable_fields, ("CON-SHIM", "ground metal shim assortment", "1", "set", "0.05/0.10/0.25 mm metal; never printed", "cutter stack and aligned interfaces", "replace if creased, burred or thickness out of tolerance", "REQUIRED; final stack selection by measurement"))),
        dict(zip(consumable_fields, ("CON-SHEARPIN", "replaceable motor-side shear pin coupons", "6", "each", "DRV-F01P C360/CuZn39Pb3 per released drawing", "shredder drive", "replace after actuation; recalibrate by selected ratio", "USER_APPROVAL_AND_GATE1_REQUIRED"))),
    ]
    tool_fields = ["tool_id", "tool", "minimum_capability", "used_for", "calibration_or_inspection", "required_or_optional"]
    tools = [
        ("TL-01", "torque wrench/driver set", "0.5–18 N·m covering M3–M8", "all controlled fasteners", "current calibration certificate or check", "REQUIRED"),
        ("TL-02", "hex/socket/spanner set", "2.5/3/4/5 mm hex; 7/8/10/13 mm", "assembly and service", "inspect for wear", "REQUIRED"),
        ("TL-03", "DMM and proven 0 V tester", "DC voltage/resistance/continuity; rated for installed source", "polarity, PE, lockout verification", "prove tester before/after; calibration current", "REQUIRED"),
        ("TL-04", "insulation resistance tester", "test voltage suitable for disconnected equipment", "heater/sensor/PE inspection", "calibration current; isolate electronics", "REQUIRED"),
        ("TL-05", "square, straightedge and tape", "1 mm frame diagonal resolution", "frame/module alignment", "check against known standard", "REQUIRED"),
        ("TL-06", "caliper and micrometers", "0.01 mm; ranges through 60 mm", "received dimensions and shaft seats", "traceable calibration", "REQUIRED"),
        ("TL-07", "three-point bore gauge", "Ø12–35 mm, 0.01 mm", "barrel/bearing/heater bores", "traceable calibration", "REQUIRED"),
        ("TL-08", "dial indicator and magnetic stand", "0.01 mm or better", "shaft/screw/spool TIR", "traceable calibration", "REQUIRED"),
        ("TL-09", "feeler and metal shim gauges", "0.05–1.0 mm", "cutter, shield and assembly clearances", "clean/undamaged leaves", "REQUIRED"),
        ("TL-10", "pin gauges/depth gauge", "drawing limits for Ø3–8 and depth", "holes, thermocouple and die inspection", "traceable calibration", "REQUIRED"),
        ("TL-11", "arbor press and bearing sleeves", "load only intended bearing ring", "bearing installation", "square ram and undamaged sleeves", "REQUIRED"),
        ("TL-12", "borescope", "view intersecting Ø8 die channel", "die burr/step inspection", "clean lens; scale reference", "REQUIRED"),
        ("TL-13", "ferrule crimper and pull-test fixture", "matches released terminals/wire", "electrical assembly", "sample crimp pull check", "REQUIRED"),
    ]
    alt_fields = ["part_id", "baseline", "approved_alternative", "approval_state", "required_recalculation_or_recalibration", "evidence_before_use"]
    alternatives = [
        ("SH-03", "GMP60-60127 ratio47 digital reference", "18–30 V donor geared DC candidate", "NOT_APPROVED_UNTIL_MEASURED", "chain ratio, current-trip, torque/RPM calibration and adapter geometry", "label/photos/shaft/current/RPM/backlash/30 min temperature + Gate-1"),
        ("CUT-03", "12 mm steel", "15 mm 6061-T6", "CONDITIONAL_AFTER_GATE1", "bearing-seat, plate deflection/stress and fastener bearing", "material certificate + rerun LC04/related plate case + Gate-1"),
        ("FD-BIN-01", "1 mm PP sheet", "1 mm 304 stainless sheet", "LISTED_DESIGN_OPTION", "mass/service handling check; no firmware recalibration", "slot fit, edge/burr and cleanability inspection"),
        ("FD-MET-02", "POM-C", "304 stainless", "LISTED_DESIGN_OPTION", "drive current window and inertia check", "pocket dimensions, runout and dry-feed coupon"),
        ("EX-THR-01", "S45C", "SS400", "LISTED_DESIGN_OPTION", "thrust plate stress/deflection if thickness or geometry changes", "material certificate, seat dimensions and LC05 boundary match"),
        ("FM-GR-01", "POM-C", "6061-T6", "LISTED_DESIGN_OPTION", "roller inertia and puller/dancer control verification", "bearing fit, runout and strand surface inspection"),
        ("EX-SCR-01/EX-BAR-01", "SCM440 KS D3867/JIS G4105", "chemically/mechanically equivalent SCM440 designation", "CERTIFICATE_REVIEW_REQUIRED", "thermal growth and strength if properties differ", "certificate, QT/nitride hardness/depth, Ra, TIR and matched clearance report"),
        ("TH-BH-01", "custom ID34 24 V 100 W band", "none; Ø35 stock substitution prohibited", "NO_APPROVED_ALTERNATIVE", "power/current/fuse/PID and thermal model for any design change", "new engineering release and receipt thermal test"),
        ("PPR-C01..12", "material in print manifest", "none", "NO_APPROVED_ALTERNATIVE", "re-slice, fit coupon, temperature/strength review", "new print manifest and interface validation"),
    ]
    make_fields = ["part_id", "description", "quantity", "decision", "source_of_truth", "release_or_procurement_gate", "rationale"]
    matrix = [{
        "part_id": r["part_id"], "description": r["description"], "quantity": r["quantity"], "decision": r["make_or_buy"],
        "source_of_truth": "bom/bom.csv" if "AUTHORITATIVE" in r["notes"] else r["notes"].split(";", 1)[0],
        "release_or_procurement_gate": r["supplier status"],
        "rationale": "reference only; exclude from order" if r["make_or_buy"] == "REFERENCE_ONLY" else r["material/specification"],
    } for r in bom]
    return {
        "fastener_schedule": (["joint_id", "part_ids", "specification", "quantity", "torque_Nm", "locking", "tool", "inspection", "source", "verification_state"], fasteners()),
        "consumables": (consumable_fields, consumables),
        "tools_required": (tool_fields, [dict(zip(tool_fields, row)) for row in tools]),
        "approved_alternatives": (alt_fields, [dict(zip(alt_fields, row)) for row in alternatives]),
        "make_buy_matrix": (make_fields, matrix),
    }


def xlsx(path: Path, sheets: list[tuple[str, list[str], list[dict[str, object]]]]) -> None:
    def tag(name: str, body: str, attrs: str = "") -> str:
        return f"<{name}{(' ' + attrs) if attrs else ''}>{body}</{name}>"
    def cell(col: int, row: int, value: object, header: bool = False) -> str:
        letters, n = "", col
        while n:
            n, rem = divmod(n - 1, 26); letters = chr(65 + rem) + letters
        ref = f"{letters}{row}"; value = str(value)
        return f'<c r="{ref}" t="inlineStr" s="{1 if header else 0}"><is><t xml:space="preserve">{html.escape(value)}</t></is></c>'
    files: dict[str, bytes] = {}
    sheet_refs = []
    rels = []
    for index, (name, fields, rows) in enumerate(sheets, 1):
        sheet_refs.append(f'<sheet name="{html.escape(name)}" sheetId="{index}" r:id="rId{index}"/>')
        rels.append(f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>')
        xml_rows = [tag("row", "".join(cell(i, 1, f, True) for i, f in enumerate(fields, 1)), 'r="1"')]
        for rnum, item in enumerate(rows, 2):
            xml_rows.append(tag("row", "".join(cell(i, rnum, item[f]) for i, f in enumerate(fields, 1)), f'r="{rnum}"'))
        width = max(12, min(60, max(len(str(x.get(f, ""))) for x in rows for f in fields) // max(1, len(fields)) + 12))
        sheet_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            f'<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
            f'<cols><col min="1" max="{len(fields)}" width="{width}" customWidth="1"/></cols><sheetData>{"".join(xml_rows)}</sheetData>'
            f'<autoFilter ref="A1:{chr(64 + min(len(fields), 26))}{len(rows) + 1}"/></worksheet>')
        files[f"xl/worksheets/sheet{index}.xml"] = sheet_xml.encode()
    files["[Content_Types].xml"] = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' +
        ''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets) + 1)) + '</Types>').encode()
    files["_rels/.rels"] = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>').encode()
    files["xl/workbook.xml"] = ('<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets>{"".join(sheet_refs)}</sheets></workbook>').encode()
    files["xl/_rels/workbook.xml.rels"] = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + ''.join(rels) +
        f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>').encode()
    files["xl/styles.xml"] = ('<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="10"/><name val="Noto Sans CJK KR"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Noto Sans CJK KR"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF235A70"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="2"><xf fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf></cellXfs></styleSheet>').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            zf.writestr(info, files[name])


def typst_text(value: object) -> str:
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", "\u200b", str(value))
    value = re.sub(r"([_;/—-])", lambda match: match.group(1) + "\u200b", value)
    return f"#text({json.dumps(value, ensure_ascii=False)})"


def pdf(path: Path, bom: list[dict[str, str]], aux: dict[str, tuple[list[str], list[dict[str, object]]]]) -> None:
    typst = shutil.which("typst")
    if not typst:
        raise RuntimeError("typst not found; run with: nix develop --command python3 release/build_bom_release.py")
    def table(fields: list[str], rows: list[dict[str, object]], widths: list[str], labels: list[str]) -> str:
        cells = ",\n".join("[" + typst_text(row[field]) + "]" for row in rows for field in fields)
        heads = ", ".join(f"[*{label}*]" for label in labels)
        return f'#table(columns: ({", ".join(widths)}), inset: 2pt, stroke: 0.35pt + rgb("b9c4c9"), table.header({heads}), {cells})'
    status_counts = Counter(r["supplier status"] for r in bom)
    procurement = table(
        ["part_id", "description", "quantity", "make_or_buy", "material/specification", "approved MPN", "supplier status"], bom,
        ["18mm", "44mm", "10mm", "25mm", "70mm", "54mm", "54mm"],
        ["Part ID", "설명", "수량", "Make/Buy", "재료/사양", "승인 MPN", "공급 상태"])
    integration = table(
        ["part_id", "critical interface", "drawing", "assembly step", "firmware dependency", "notes"], bom,
        ["18mm", "62mm", "55mm", "48mm", "55mm", "85mm"],
        ["Part ID", "핵심 인터페이스", "도면", "조립 단계", "펌웨어 의존", "비고"])
    counts = ", ".join(f"{k}: {v}" for k, v in sorted(status_counts.items()))
    source_hash = hashlib.sha256((ROOT / "bom/bom.csv").read_bytes()).hexdigest()
    body = f'''#set page(paper: "a3", flipped: true, margin: 12mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 6.2pt, lang: "ko")
#set heading(numbering: "1.1")
#align(center)[#text(size: 20pt, weight: "bold", fill: rgb("235a70"))[PLA/PET Recycling Lab v0.8 — 최종 BOM]]
#align(center)[Revision {REV} · 디지털 제조 후보]

#block(fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt)[
*구매·가공·통전 승인 문서가 아니다.* donor와 supplier가 미확정인 항목을 0원 또는 승인품으로 간주하지 않는다. 실제 라벨·치수·정격·수령검사와 사용자 승인이 필요하다.
]

= 구성관리 기준

- Authoritative design source: `bom/bom.csv` (SHA-256 `{source_hash}`)
- Subordinate detail sources: print, machine, shredder, extruder, thermal, drive manifests
- BOM rows: {len(bom)} / source design rows: {len(read_csv("bom/bom.csv"))}
- 공급 상태 집계: {counts}
- Price는 정보이며 설계 release gate가 아니다. 미확정 MPN/공급사는 주문 전에 닫는다.
- CSV의 17개 필드가 전체 release record이며 이 PDF는 사람이 검토하는 vector view다.

= 조달·제작 보기

{procurement}

#pagebreak()
= 인터페이스·도면·조립 교차참조

{integration}

#pagebreak()
= 일정표 요약

Fastener {len(aux["fastener_schedule"][1])}행 · Consumables {len(aux["consumables"][1])}행 · Tools {len(aux["tools_required"][1])}행 · Alternatives {len(aux["approved_alternatives"][1])}행.

세부값은 동봉 CSV와 BOM.xlsx의 동일 이름 sheet가 지배한다. `USER_APPROVAL_REQUIRED`, `RECEIPT_TEST_REQUIRED`, `NOT_APPROVED`는 누락이 아니라 의도적인 물리/조달 gate이며 승인으로 승격하지 않는다.
'''
    tmp = OUT / ".BOM_KO.typ"
    tmp.write_text(body, encoding="utf-8")
    try:
        env = os.environ.copy(); env["SOURCE_DATE_EPOCH"] = "946684800"
        subprocess.run([typst, "compile", "--root", str(ROOT), str(tmp), str(path)], check=True, cwd=ROOT, env=env)
    finally:
        tmp.unlink(missing_ok=True)


def validate(bom: list[dict[str, str]], aux: dict[str, tuple[list[str], list[dict[str, object]]]], manufacturing_count: int) -> dict[str, object]:
    assert bom and list(bom[0]) == FIELDS
    ids = [row["part_id"] for row in bom]
    assert len(ids) == len(set(ids)), "duplicate part revision"
    assert all(all(str(row[field]).strip() for field in FIELDS) for row in bom), "empty required field"
    assert all(float(row["quantity"]) > 0 for row in bom)
    source_ids = {r["part_id"] for r in read_csv("bom/bom.csv")}
    assert source_ids <= set(ids), "authoritative source row lost"
    active = json.loads((ROOT / "release/active_part_set.json").read_text(encoding="utf-8"))["parts"]
    by_id = {row["part_id"]: row for row in bom}
    assert all(item["part_id"] in by_id and float(by_id[item["part_id"]]["quantity"]) == item["quantity"] for item in active), "active quantity mismatch"
    checked_drawings = set()
    for row in bom:
        for item in row["drawing"].split(";"):
            file = item.strip().split(" §", 1)[0]
            assert (ROOT / file).is_file(), f"missing drawing: {row['part_id']} {file}"
            checked_drawings.add(file)
        manual = row["assembly step"].split(" §", 1)[0]
        assert (ROOT / manual).is_file(), f"missing manual: {row['part_id']} {manual}"
    unsafe = [r["part_id"] for r in bom if r["donor status"].startswith("UNVERIFIED") and "approved" in r["supplier status"].lower()]
    assert not unsafe, f"unverified donor marked approved: {unsafe}"
    assert not any("0원" in json.dumps(row, ensure_ascii=False) or "zero-cost" in json.dumps(row).lower() for row in bom)
    assert all(rows and fields and all(all(str(row[field]).strip() for field in fields) for row in rows) for fields, rows in aux.values())
    kitting_holds = [r["joint_id"] for r in aux["fastener_schedule"][1] if "kitting count required" in str(r["verification_state"])]
    return {
        "status": "PASS_WITH_DOCUMENTED_SOURCE_HOLDS", "digital_integrity_status": "PASS",
        "fabrication_procurement_readiness": "HOLD", "revision": REV, "authoritative_source": "bom/bom.csv",
        "authoritative_source_sha256": hashlib.sha256((ROOT / "bom/bom.csv").read_bytes()).hexdigest(),
        "bom_rows": len(bom), "active_parts_checked": len(active), "active_quantity_match": True,
        "final_manufacturing_parts_checked": manufacturing_count,
        "drawings_checked": len(checked_drawings), "manual_cross_reference": True,
        "duplicate_part_revision": False, "required_fields_complete": True,
        "donor_zero_cost_or_false_approval": False,
        "approved_mpn_pending_rows": sum("NONE_APPROVED" in r["approved MPN"] for r in bom),
        "blocking_source_gaps": [f"{joint}: exact piece count is absent from authoritative design source" for joint in kitting_holds],
        "note": "digital BOM integrity only; supplier receipt, procurement, physical assembly and commissioning remain user approval gates",
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bom = root_rows()
    seen = {r["part_id"] for r in bom}
    for row in expanded_rows():
        if row["part_id"] in seen:
            raise ValueError(f"duplicate detail part_id: {row['part_id']}")
        seen.add(row["part_id"]); bom.append(row)
    bom.extend(active_reference_rows(seen))
    bom.sort(key=lambda row: row["part_id"])
    manufacturing_count = enrich_final_manufacturing(bom)
    aux = auxiliary(bom)
    report = validate(bom, aux, manufacturing_count)
    write_csv(OUT / "BOM.csv", FIELDS, bom)
    for name, (fields, rows) in aux.items():
        write_csv(OUT / f"{name}.csv", fields, rows)
    sheets = [("BOM", FIELDS, bom)] + [(name[:31], fields, rows) for name, (fields, rows) in aux.items()]
    xlsx(OUT / "BOM.xlsx", sheets)
    pdf(OUT / "BOM_KO.pdf", bom, aux)
    (OUT / "bom_verification.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    expected = {"BOM.csv", "BOM.xlsx", "BOM_KO.pdf", "fastener_schedule.csv", "consumables.csv", "tools_required.csv", "approved_alternatives.csv", "make_buy_matrix.csv", "bom_verification.json"}
    assert expected <= {p.name for p in OUT.iterdir() if p.is_file()}
    print(f"V08_BOM_RELEASE_OK rows={len(bom)} active={report['active_parts_checked']} drawings={report['drawings_checked']}")


if __name__ == "__main__":
    main()
