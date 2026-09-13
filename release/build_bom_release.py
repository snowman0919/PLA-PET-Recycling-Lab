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
GGM_SUPERSEDED_DRIVE = {"CUT-07", "DRV-01", "DRV-02", "DRV-A42", "DRV-A60", "DRV-F01A", "DRV-F01B", "DRV-F01P"}
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
        ("PPR-C", "3D_PRINT"), ("DR-GGM", "DRIVE"), ("FR", "FRAME"), ("HP", "HOPPER"),
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
        "FR-01": "exports/final/frame_v08/FRAME_CUT_AND_TIE_KO.pdf",
        "FR-TIE-01": "exports/final/frame_v08/FR-TIE-01.svg",
        "EX-MT-01": "exports/final/manufacturing/hot_zone/ExtruderRearFixedDatum.svg",
        "EX-MT-02": "exports/final/manufacturing/hot_zone/ExtruderFrontSlidingGuide.svg",
        "EX-MT-03": "exports/final/manufacturing/hot_zone/ExtruderFixedCollar.svg",
        "EX-MT-04": "exports/final/manufacturing/hot_zone/ExtruderSupportRailRear.svg",
        "EX-MT-05": "exports/final/manufacturing/hot_zone/ExtruderRearRetainer.svg",
        "EX-MT-06": "exports/final/manufacturing/hot_zone/ExtruderRearRetainerSpacer318.svg",
        "DR-GGM-01": "exports/final/manufacturing/drive_ggm/PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf",
        "DR-GGM-02": "exports/final/manufacturing/drive_ggm/PPR_GGM_ASSEMBLY_INSPECTION_KO_r2.pdf",
        "DR-GGM-03": "exports/final/electrical/full_wiring_diagram.pdf",
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


def assembly_step_number(part_id: str) -> int:
    exact = {
        "PPR-C01": 9, "PPR-C02": 9, "PPR-C03": 10, "PPR-C04": 9,
        "PPR-C05": 14, "PPR-C06": 15, "PPR-C07": 16,
        "PPR-C08": 17, "PPR-C09": 17, "PPR-C10": 17,
        "PPR-C11": 22, "PPR-C12": 20,
        "PPR-FULL-ASM": 1, "PPR-FRAME-ASM": 2,
        "PPR-SHREDDER-ASM": 4, "PPR-FEEDER-ASM": 10,
        "PPR-EXTRUDER-ASM": 11, "PPR-FORMING-ASM": 14,
        "CUT-09": 4, "CUT-10": 5,
        "CUT-04": 9, "DRV-GD-01": 8, "FD-HOP-01": 9,
        "EX-CPN-BAR": 1, "EX-CPN-SCR": 1, "EX-SH-01": 13,
        "FM-GA-01": 17, "FM-GR-01": 17,
        "FM-GC-01": 17,
        "ExtruderSupportRailRear": 11, "ExtruderRearFixedDatum": 11,
        "ExtruderFrontSlidingGuide": 11, "ExtruderFixedCollar": 11,
        "ExtruderRearRetainer": 11, "ExtruderRearRetainerSpacer318": 11,
        "SH-06": 5,
        "GGM_ChainGuard": 8,
        "GGM_SH_CouplingGuard": 8,
        "DR-GGM-01": 7, "DR-GGM-02": 7, "DR-GGM-03": 19,
    }
    step = exact.get(part_id)
    if step is None:
        step = next((value for prefix, value in (
            ("FR-ANCHOR", 3), ("FR", 2), ("CUT-03", 4), ("CUT-08", 4),
            ("CUT-05", 5), ("CUT-01", 6), ("CUT-02", 6), ("CUT-06", 6),
            ("DRV", 7), ("SH", 8), ("HP", 9), ("IN-HOP", 9), ("FB", 9),
            ("FD", 10), ("FH", 10), ("EX-MT", 11), ("EX-THR", 12),
            ("EX-SCR", 12), ("EX-BAR", 12), ("EX-DIE", 13), ("TH", 13),
            ("EX", 12), ("CO", 14), ("DG", 15), ("PL", 16), ("FM", 16),
            ("GGM_EX", 12), ("GGM_SH", 7), ("GGM_Jack", 7),
            ("SP", 17), ("GD", 18), ("CT", 19), ("SF", 21), ("DR", 1),
        ) if part_id.startswith(prefix)), 1)
    return step


def assembly_step(part_id: str) -> str:
    return f"docs/final/complete_build_manual_ko.pdf step {assembly_step_number(part_id)}; docs/final/assembly_steps.csv"


def critical(part_id: str, detail: str = "") -> str:
    base = next((text for prefix, text in (
        ("DR-GGM", "selected GGM drive mounting, bearing support, coupling protection and current feedback"),
        ("FR", "profile joint squareness and table load path"),
        ("SH", "guarded cutter torque path and service lockout"),
        ("CUT", "shaft/bearing fit; cutter shim clearance; phase registration"),
        ("DRV", "keyed phase/sprocket interface; chain alignment; GGM protection coupling governs mechanical release"),
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
    if part_id.startswith(("DR-GGM", "SH", "DRV", "FH-03", "EX-03", "EX-04", "EX-05", "EX-06", "EX-07", "EX-08", "TH", "CO-02", "DG", "PL", "SP", "CT")):
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
        if pid == "DR-GGM-01":
            make = "MAKE_TO_DRAWING"
            donor = "NOT_APPLICABLE—project-lab fabrication from released stock/drawings"
            supplier = "DIGITAL_DRAWING_PASS—FABRICATION_USER_APPROVAL_REQUIRED"
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
        if pid in GGM_SUPERSEDED_DRIVE:
            return
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
        if row["part_id"] in GGM_SUPERSEDED_DRIVE:
            continue
        add(row["part_id"], row["name"], row["quantity"], row["material"], row["process"], row["release_state"],
            "exports/drive_interface/manifest.csv", f"exports/drive_interface/parts/{row['part_id']}/drawing_notes.md")
    return rows


def ggm_sprocket_rows(existing: set[str]) -> list[dict[str, str]]:
    contract = json.loads((ROOT / "control/ggm_drive_contract.json").read_text(encoding="utf-8"))["shredder"]["chain_drive"]
    register = {row["part_id"]: row for row in read_csv("analysis/drive_acceptance_v08/drive_component_register.csv")}
    result = []
    for role in ("input_sprocket", "output_sprocket"):
        spec = contract[role]; pid = spec["part_id"]
        if pid in existing:
            continue
        reg = register[pid]
        if reg["classification"] != "purchased_reference_envelope":
            raise ValueError(pid + " must remain a purchased reference envelope")
        result.append({
            "part_id": pid, "description": spec["type"], "revision": REV, "category": "DRIVE",
            "quantity": reg["quantity"], "required_or_optional": "REQUIRED", "make_or_buy": "BUY_TO_SPEC",
            "material/specification": reg["material_note"] + "; " + spec["shaft_interface"] + "; " + spec["key"],
            "critical interface": f"keyed torque path; radial TIR <= {spec['radial_tir_mm_max']:.2f} mm; assembled axial shift+U95 <= {contract['assembled_axial_shift_u95_mm_max']:.2f} mm; chain alignment <= {contract['chain_plane_alignment_mm_per_150_max']:.2f}/150 mm; received maker axial retention required",
            "approved MPN": "NONE_APPROVED—received keyed #35 sprocket must pass P1/P4 fit and retention evidence",
            "approved alternative": "NONE_APPROVED—failed bore/key/retention/TIR requires an engineering adapter revision",
            "donor status": "NOT_APPLICABLE",
            "supplier status": "CHECK_EXISTING_STOCK_FIRST—PURCHASE_USER_APPROVAL_REQUIRED—PHYSICAL_RECEIPT_HOLD",
            "drawing": "docs/drawings/v0.8/SH-004_chain_phase_gear.svg",
            "assembly step": assembly_step(pid),
            "firmware dependency": "GGM torque/current protection calibration; sprocket retention is mechanical",
            "notes": "CURRENT GGM PURCHASED SPROCKET SOURCE: control/ggm_drive_contract.json + analysis/drive_acceptance_v08/drive_component_register.csv; key carries torque; maker retention hardware is axial-only; DRV-02 is superseded",
        })
    return result


def active_reference_rows(existing: set[str]) -> list[dict[str, str]]:
    aliases = {
        "ExtruderSupportRailRear": ("EX-MT-04", "exports/final/manufacturing/hot_zone/ExtruderSupportRailRear.svg"),
        "ExtruderRearFixedDatum": ("EX-MT-01", "exports/final/manufacturing/hot_zone/ExtruderRearFixedDatum.svg"),
        "ExtruderFrontSlidingGuide": ("EX-MT-02", "exports/final/manufacturing/hot_zone/ExtruderFrontSlidingGuide.svg"),
        "ExtruderFixedCollar": ("EX-MT-03", "exports/final/manufacturing/hot_zone/ExtruderFixedCollar.svg"),
        "ExtruderRearRetainer": ("EX-MT-05", "exports/final/manufacturing/hot_zone/ExtruderRearRetainer.svg"),
        "ExtruderRearRetainerSpacer318": ("EX-MT-06", "exports/final/manufacturing/hot_zone/ExtruderRearRetainerSpacer318.svg"),
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
            "drawing": draw, "assembly step": assembly_step(pid),
            "firmware dependency": "NONE", "notes": f"active_part_set reference; canonical={canonical}; exclude from procurement roll-up",
        })
    return result


def ggm_manufacturing_rows(existing: set[str]) -> list[dict[str, str]]:
    manifest = ROOT / "exports/final/manufacturing/drive_ggm/manifest.csv"
    if not manifest.is_file(): return []
    result=[]
    for item in read_csv("exports/final/manufacturing/drive_ggm/manifest.csv"):
        pid=item["part_id"]
        if pid in existing: continue
        result.append({
            "part_id":pid,"description":f"GGM drive manufactured part: {pid}","revision":REV,
            "category":"DRIVE","quantity":item["quantity"],"required_or_optional":"REQUIRED","make_or_buy":"MAKE",
            "material/specification":f"{item['material']}; process={item['process']}",
            "critical interface":item["critical_tolerance"],"approved MPN":"NOT_APPLICABLE_CUSTOM",
            "approved alternative":"NONE_APPROVED—deviation requires drive-interface review",
            "donor status":"NOT_APPLICABLE","supplier status":"DIGITAL_DRAWING_PASS; PHYSICAL_NOT_RUN",
            "drawing":"exports/final/manufacturing/drive_ggm/PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf",
            "assembly step":assembly_step(pid),"firmware dependency":"GGM/BTS7960 released profile; commissioning calibration remains NOT_RUN",
            "notes":"authoritative sub-manifest: exports/final/manufacturing/drive_ggm/manifest.csv"})
    return result


def enrich_ggm_existing(bom: list[dict[str,str]]) -> int:
    manifest=ROOT/"exports/final/manufacturing/drive_ggm/manifest.csv"
    if not manifest.is_file(): return 0
    by={r["part_id"]:r for r in bom}
    count=0
    for item in read_csv("exports/final/manufacturing/drive_ggm/manifest.csv"):
        if item["part_id"] not in by: continue
        row=by[item["part_id"]]; count+=1
        row["drawing"] += "; exports/final/manufacturing/drive_ggm/PPR_GGM_MANUFACTURING_DRAWINGS_r2.pdf"
        row["critical interface"] += "; GGM delta: "+item["critical_tolerance"]
        row["notes"] += "; GGM drive delta drawing bound by drive_ggm manifest"
    return count


def enrich_final_manufacturing(bom: list[dict[str, str]]) -> int:
    """최종 RFQ manifest가 있으면 같은 Part ID의 제작 도면/공차를 우선한다."""
    manifest = ROOT / "exports/final/manufacturing/RFQ/manifest.csv"
    if not manifest.is_file():
        return 0
    by_id = {row["part_id"]: row for row in bom}
    rows = read_csv("exports/final/manufacturing/RFQ/manifest.csv")
    rows = [item for item in rows if item["part_id"] not in GGM_SUPERSEDED_DRIVE]
    for item in rows:
        row = by_id[item["part_id"]]
        assert float(row["quantity"]) == float(item["quantity"]), f"manufacturing quantity mismatch: {item['part_id']}"
        drawing_pdf = f"exports/final/manufacturing/RFQ/{item['drawing_pdf']}"
        assert (ROOT / drawing_pdf).is_file(), f"missing final manufacturing drawing: {drawing_pdf}"
        row["drawing"] = drawing_pdf
        row["material/specification"] = f"{item['material']}; process={item['process']}"
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
            torque = part["tightening_torque"].replace(" N.m", "")
            if ";" in torque:
                thread = re.search(r"\bM\d+", match.group(2))
                assert thread, f"missing thread for torque selection: {spec}"
                torque = dict(value.strip().split(" ", 1) for value in torque.split(";"))[thread[0]]
            rows.append(dict(zip(fields, (
                f"PR-{part['part_id']}-{index}", f"{part['part_id']} / {part['mating_part']}", match.group(2).strip(),
                int(match.group(1)) * int(part["quantity"]), torque,
                part["insert_or_nut"], "hex/driver sized to received fastener",
                f"{part['interfaces']}; witness mark and no crack", "exports/print/print_manifest.csv", "RELEASED_DIGITAL"))))
    manual = [
        ("SYS-01", "frame profile joints", "BASE FRAME ALLOWANCE ONLY: M5x12 + washer + T-nut 56 kits; not final GGM joint count; FR-TIE-01 needs four separate M5x10 kits", 56, "5.0", "prevailing T-nut", "4 mm hex + square", "P2 member-by-member connection review; final GGM bracket/T-nut allocation and tie thread engagement required; frame diagonal <=1.0 mm", "HOLD_GGM_MEMBER_CONNECTION_RECEIPT_REVIEW"),
        ("SYS-02", "PE-01..04 bonds", "M4x10 + two tooth washers + all-metal nut per bond", 4, "3.0", "tooth washer + all-metal nut", "3 mm hex + DMM", "four PE bonds pass continuity and have witness marks", "RELEASED_DIGITAL"),
        ("SYS-03", "EX-THR-01 / barrel", "M6x20 class 8.8", 8, "9", "prevailing metal nut", "5 mm hex/10 mm spanner", "metal thrust path; witness mark", "RELEASED_DIGITAL"),
        ("SYS-04", "EX-DIE-01 / EX-BAR-01", "M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1", 4, "1.5", "dry thread; no threadlocker; witness mark", "3 mm hex; micrometer/depth gauge", "digital load-path PASS: engagement6.82-7.40 and thread-bottom clearance0.60-1.18 from die grip34.95-35.05, compressed gasket0.25-0.53 and barrel full thread8.00; 6 MPa retained-clamp separation SF2.14; physical receipt/leak/first thermal-cycle check NOT_RUN", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-05", "EX-DIE-04 / EX-DIE-01", "M4 retainer screw", 2, "1.2", "all-metal lock", "3 mm hex", "retainer captures insert", "RELEASED_DIGITAL"),
        ("SYS-06", "CUT-08 / CUT-03", "M4x12 class 8.8 SHCS", 12, "3", "all-metal locknut", "3 mm hex + 7 mm spanner", "bearing seal untouched; free rotation", "RELEASED_DIGITAL"),
        ("SYS-07", "hot-zone datum/guide / rear rail", "M5 profile fastener", 4, "2.5", "prevailing T-nut", "4 mm hex", "rear datum fixed; front axial slide free", "RELEASED_DIGITAL"),
        ("SYS-08", "DRV-03 / DRV-03R phase gears", "M4x22 class 10.9 SHCS", 4, "3", "all-metal locknut + dowel", "3 mm hex + 7 mm spanner", "2 bolts/gear; clocking dowel seated; matched keys blue-checked", "RELEASED_DIGITAL"),
        ("SYS-09", "GGM_SH_12T / GGM_SH_30T axial retention", "received sprocket maker axial-retention hardware; 4x4/6x6 keys carry torque", 2, "HOLD", "maker locking/retention feature; axial retention only", "tool and torque per accepted received hardware", "blue-check key flank; no friction-only/set-screw-only torque path; each sprocket radial TIR <=0.10 mm; total axial shift+U95 <=0.20 mm; chain alignment <=0.20/150 mm", "HOLD_SPROCKET_RECEIPT_AXIAL_RETENTION_NOT_RUN"),
        ("SYS-10", "ExtruderRearRetainer / ExtruderRearFixedDatum", "M4x25 class 8.8 SHCS", 2, "2.9", "dry thread; witness mark", "3 mm hex", "full thread engagement >=8.0 mm; cold endplay 0.12-0.28 mm", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-11", "FM-EB-01 / FM-PL-01", "M3x10 class 8.8 SHCS", 4, "1.2", "witness mark; clean dry thread", "2.5 mm hex", "paired bush index within0.5 deg; full-rotation roller gap1.60-1.90 mm", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-12", "FD-HOP-01 / FD-GSK-01 / FD-MET-01", "M4x16 A2-70 SHCS + washer + all-metal prevailing nut", 4, "HOLD", "all-metal prevailing nut", "3 mm hex; 7 mm spanner; feeler/depth gauge", "register clearance0.10-0.16; tighten crosswise only until gasket thickness0.35-0.40; dry-flake leak/retention test required", "HOLD_GASKET_COMPRESSION_PHYSICAL_NOT_RUN"),
        ("SYS-13", "SP-BR-01 / SP-BP-01", "M5x20 A2-70 SHCS + washer + all-metal prevailing nut", 8, "2.5", "all-metal prevailing nut", "4 mm hex + 8 mm spanner", "four bolts per bearing; cross-tighten; blue-check outer-ring edge only; free rotation and axial capture", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-14", "FM-GC-01 / FM-GR-01", "M3x25 A2-70 SHCS + washers + all-metal prevailing nuts", 3, "0.35", "all-metal prevailing nut", "2.5 mm hex + 5.5 mm spanner", "three balanced through-bolts; caps flush; blue-check outer-ring edge only; free rotation and no cap rub", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-15", "FD-MET-02 / FD-MET-03 / FD-CP-01", "420 stainless slotted spring pins: Ø3x12 lower + Ø3x18 upper", 2, "N/A", "matched Ø3.00-3.05 cross-holes; replace after removal", "3 mm pin punch", "both pins flush; 10 hand turns without housing/coupling rub; inspect for looseness", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-16", "TH-DIE-01 / EX-DIE-01", "2x M3x8 A4-80 SHCS + Schnorr washer", 2, "1.0", "high-temperature serrated conical washer; no threadlocker", "2.5 mm hex", "flange seated; heater cannot back out; leads unloaded; cold witness-mark and recheck after first thermal cycle", "RELEASED_DIGITAL_PHYSICAL_NOT_RUN"),
        ("SYS-17", "TH-TCR-01 / EX-BAR-01 / EX-DIE-01", "M3x6 A4-80 SHCS + Schnorr washer; M3x8 prohibited in 4 mm blind threads", 8, "0.5", "high-temperature serrated conical washer; no threadlocker", "2.5 mm hex", "confirm actual washer/collar/bridge stack, useful thread engagement and positive bottom clearance before torque; nominal M3x6 clears whereas M3x8 bottoms; four stop collars captured; 20 N pull causes <=0.10 mm motion cold and after thermal cycle", "HOLD_RECEIVED_RETAINER_STACK_AND_PULL_TEST"),
    ]
    for values in manual:
        rows.append(dict(zip(fields, (*values[:8], "release/build_bom_release.py::fasteners; final manual generated from this schedule", values[8]))))
    return rows


def fastener_step_number(joint: dict[str, object]) -> int:
    if str(joint["joint_id"]).startswith("PR-"):
        return assembly_step_number(str(joint["part_ids"]).split(" / ")[0])
    return {"SYS-01": 2, "SYS-02": 19, "SYS-03": 12, "SYS-04": 13,
            "SYS-05": 13, "SYS-06": 4, "SYS-07": 11, "SYS-08": 7,
            "SYS-09": 7, "SYS-10": 11, "SYS-11": 16, "SYS-12": 10, "SYS-13": 17, "SYS-14": 17,
            "SYS-15": 10, "SYS-16": 13, "SYS-17": 13}[str(joint["joint_id"])]


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
        dict(zip(consumable_fields, ("CON-SHEARPIN", "GGM mechanical-protection calibration pin coupons", "9", "each", "lot-controlled brass blank per GGM_SH/EX_FusePinBlank; final neck is determined only by measured release", "P3 GGM bench: 3 SH-F + 3 SH-R + 3 EX-F", "replace after every actuation; accept final geometry only when U95-bounded release is 8.8-9.3 N.m and post-release drive is free/undamaged", "USER_APPROVAL_AND_P3_REQUIRED"))),
    ]
    tool_fields = ["tool_id", "tool", "minimum_capability", "used_for", "calibration_or_inspection", "required_or_optional"]
    tools = [
        ("TL-01", "torque wrench/driver set", "0.5–20 N·m covering M3–M8; anchor value provisional pending table/anchor verification", "all controlled fasteners", "current calibration certificate or check", "REQUIRED"),
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
        ("SH-03", "GGM K9DG60N2 + K9G75C selected drive", "none until an exact shaft/mount/ratio/current/torque equivalent is documented", "PURCHASE_AND_RECEIPT_HOLD", "PCD/output-offset mount compatibility, ratio/speed, 0-6 A current map, gearbox torque map and 8.8-9.3 N.m mechanical protection", "vendor/received label + authenticated receipt packet + mount-compatibility PASS + P3 bench evidence"),
        ("CUT-03", "12 mm steel", "15 mm 6061-T6", "CONDITIONAL_AFTER_GATE1", "bearing-seat, plate deflection/stress and fastener bearing", "material certificate + rerun LC04/related plate case + Gate-1"),
        ("FD-BIN-01", "1 mm PP sheet", "1 mm 304 stainless sheet", "LISTED_DESIGN_OPTION", "mass/service handling check; no firmware recalibration", "slot fit, edge/burr and cleanability inspection"),
        ("FD-MET-02", "304 stainless auger/agitator per final RFQ", "none; legacy POM-C pocket rotor is not the active geometry", "NO_APPROVED_ALTERNATIVE", "any new material/geometry requires feeder clearance, torque/inertia, current-window and thermal review", "new drawing revision and dry-feed coupon"),
        ("FH-03", "17E1K-07 + EG17-G10 + CL42T-V41 digital reference", "none until an exact replacement is documented", "PURCHASE_AND_RECEIPT_HOLD", "FD-DA-01/FD-CP-01 fit, output torque, STEP rate, current/fuse, ALM and tach", "datasheet + received shaft/pilot/pattern/current + 2.2 N.m torque-arm + tach-loss test"),
        ("EX-THR-01", "S45C", "SS400", "LISTED_DESIGN_OPTION", "thrust plate stress/deflection if thickness or geometry changes", "material certificate, seat dimensions and LC05 boundary match"),
        ("FM-GR-01", "POM-C", "6061-T6", "LISTED_DESIGN_OPTION", "roller inertia and puller/dancer control verification", "bearing fit, runout and strand surface inspection"),
        ("EX-SCR-01/EX-BAR-01", "SCM440 KS D3867/JIS G4105", "chemically/mechanically equivalent SCM440 designation", "CERTIFICATE_REVIEW_REQUIRED", "thermal growth and strength if properties differ", "certificate, QT/nitride hardness/depth, Ra, TIR and matched clearance report"),
        ("TH-BH-01", "custom ID34 24 V 100 W band", "none; Ø35 stock substitution prohibited", "NO_APPROVED_ALTERNATIVE", "power/current/fuse/PID and thermal model for any design change", "new engineering release and receipt thermal test"),
        ("TH-DIE-01", "Tempco custom Hi-Density metric Ø6.50 CG x39.50 with HTL leads and MFR flange", "none; stock 3D-printer cartridge substitution prohibited", "CUSTOM_QUOTE_AND_DRAWING_REQUIRED", "fit, watt density, lead temperature, power/current/fuse/PID and flange retention", "accepted vendor drawing + OD/camber/resistance/insulation report + full hand insertion"),
        ("TH-TC-01", "Tempco MTA1 K/2/M/A/Q/U custom probe with welded stop collar", "none until the same OD, stop, insulation and response contract is documented", "CUSTOM_QUOTE_AND_DRAWING_REQUIRED", "probe fit, junction isolation, insertion stop, transition temperature and control response", "accepted vendor drawing + dimensional/insulation certificate + cold/hot pull and coupon response tests"),
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
    candidates = [shutil.which("typst"), *sorted(Path("/nix/store").glob("*-typst-*/bin/typst"))]
    typst = next((str(candidate) for candidate in candidates if candidate and subprocess.run([str(candidate), "--version"], capture_output=True).returncode == 0), None)
    if not typst:
        raise RuntimeError("typst not found in PATH or /nix/store")
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

== 미검증 체결품 — 체결/조립 진행 보류

{table(["joint_id", "specification", "torque_Nm", "inspection"], [r for r in aux["fastener_schedule"][1] if str(r["verification_state"]).startswith("HOLD")], ["20mm", "60mm", "25mm", "170mm"], ["Joint", "후보 규격", "토크 상태", "해소 필요 조건"])}

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
    assert not (GGM_SUPERSEDED_DRIVE & set(ids)), "superseded generic drive item reactivated"
    assert {"GGM_SH_12T", "GGM_SH_30T"} <= set(ids), "direct-keyed GGM sprockets missing from final BOM"
    active = json.loads((ROOT / "release/active_part_set.json").read_text(encoding="utf-8"))["parts"]
    by_id = {row["part_id"]: row for row in bom}
    assert all(item["part_id"] in by_id and float(by_id[item["part_id"]]["quantity"]) == item["quantity"] for item in active), "active quantity mismatch"
    checked_drawings = set()
    steps = {int(row["step_number"]): row for row in read_csv("docs/final/assembly_steps.csv")}
    for row in bom:
        for item in row["drawing"].split(";"):
            file = item.strip().split(" §", 1)[0]
            assert (ROOT / file).is_file(), f"missing drawing: {row['part_id']} {file}"
            checked_drawings.add(file)
        link = re.fullmatch(r"(docs/final/complete_build_manual_ko\.pdf) step (\d+); (docs/final/assembly_steps\.csv)", row["assembly step"])
        assert link and int(link[2]) in steps, f"invalid final manual step: {row['part_id']}"
        assert (ROOT / link[1]).is_file() and (ROOT / link[3]).is_file(), f"missing final manual: {row['part_id']}"
    for item in active:
        step = steps[assembly_step_number(item["part_id"])]
        assert f"{item['part_id']} ×{item['quantity']}" in step["part_ids_quantity"].split("; "), f"active manual quantity mismatch: {item['part_id']}"
    for joint in aux["fastener_schedule"][1]:
        step = steps[fastener_step_number(joint)]
        assert f"{joint['joint_id']}: {joint['specification']} ×{joint['quantity']}; " in step["fasteners"] + "; ", f"manual fastener mismatch: {joint['joint_id']}"
        assert f"{joint['joint_id']}: {joint['torque_Nm']} N·m; " in step["torque"] + "; ", f"manual torque mismatch: {joint['joint_id']}"
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
        "active_manual_quantity_match": True, "final_manual_steps_checked": len(steps),
        "fastener_manual_quantity_torque_match": True, "fastener_joints_checked": len(aux["fastener_schedule"][1]),
        "duplicate_part_revision": False, "required_fields_complete": True,
        "donor_zero_cost_or_false_approval": False,
        "approved_mpn_pending_rows": sum("NONE_APPROVED" in r["approved MPN"] for r in bom),
        "blocking_source_gaps": [f"{joint}: exact piece count is absent from authoritative design source" for joint in kitting_holds]
            + [f"manual step {step}: {row['clearance_tolerance']}" for step, row in steps.items() if "joint definition (HOLD)" in row["clearance_tolerance"]],
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
    for row in ggm_manufacturing_rows(seen):
        if row["part_id"] in seen: raise ValueError(f"duplicate GGM part_id: {row['part_id']}")
        seen.add(row["part_id"]); bom.append(row)
    for row in ggm_sprocket_rows(seen):
        if row["part_id"] in seen: raise ValueError(f"duplicate GGM sprocket part_id: {row['part_id']}")
        seen.add(row["part_id"]); bom.append(row)
    bom.extend(active_reference_rows(seen))
    bom.sort(key=lambda row: row["part_id"])
    manufacturing_count = enrich_final_manufacturing(bom) + enrich_ggm_existing(bom)
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
