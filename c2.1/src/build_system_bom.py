"""Build the active C2.1 system BOM without mutating the historical C1 BOM."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile

HERE = Path(__file__).resolve()
C21 = HERE.parents[1]
REPO = HERE.parents[2]
FIELDS = ["scope", "part_id", "description", "quantity", "material", "status",
          "source", "evidence", "landed_line_KRW", "cost_state", "notes"]


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def column_name(number):
    out = ""
    while number:
        number, remainder = divmod(number-1, 26)
        out = chr(65+remainder)+out
    return out


def write_xlsx(path, table):
    sheet_rows = []
    for row_number, row in enumerate([FIELDS]+[[str(item.get(key, "")) for key in FIELDS]
                                                for item in table], 1):
        cells = []
        for column_number, value in enumerate(row, 1):
            ref = f"{column_name(column_number)}{row_number}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="C2.1 system BOM" sheetId="1" r:id="rId1"/></sheets></workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>""",
        "xl/worksheets/sheet1.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>"""
        +"".join(sheet_rows)+"</sheetData></worksheet>"
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)


def main():
    master = json.loads((REPO/"design/assembly.json").read_text())
    integration = json.loads((C21/"results/machine_integration.json").read_text())
    # VP1 Stage 2: envelope instances replaced by real winder/puller/guard
    # geometry are excluded from the retained-quantity roll-up
    excluded = set(integration.get("vp1_stage1", {}).get(
        "excluded_legacy_instances", []))
    excluded.update(integration["vp1_stage1"]["deleted_drive_instances"])
    retained = Counter(item["part"] for item in master["instances"]
                       if item["group"] != "S2" and item["name"] not in excluded)
    # The added jackshaft chain-B driver uses a second physical 6x6x16 key,
    # not a second part ID or a zero-cost phantom.
    if not any(r.get("legacy") == "DRV-JACK_001"
               and r.get("kind") == "keyseat"
               for r in integration["vp1_stage1"]["vp1_stage3"]["relief_records"]):
        raise RuntimeError("BOM requires the second jackshaft keyseat")
    retained["KEY-6-16"] += 1
    removed = Counter(item["part"] for item in master["instances"]
                      if item["group"] == "S2" or item["name"] in excluded)
    groups = defaultdict(set)
    for item in master["instances"]:
        if item["group"] != "S2" and item["name"] not in excluded:
            groups[item["part"]].add(item["group"])
    costs = {item["item_id"]: item for item in rows(REPO/"c2/bom/cost_ledger.csv")}

    active = []
    for item in rows(REPO/"bom/BOM.csv"):
        part_id = item["part_id"]
        if part_id in master["parts"]:
            quantity = retained[part_id]
            if not quantity:
                continue
            scope = "legacy_interface:"+"+".join(sorted(groups[part_id]))
        else:
            quantity = item["quantity"]
            scope = "system_requirement"
        cost = costs.get(part_id, {})
        same_quantity = not cost or float(cost.get("quantity", quantity)) == float(quantity)
        landed = cost.get("landed_line_KRW", "") if same_quantity else ""
        cost_state = cost.get("quote_status", "UNKNOWN") if same_quantity else "REQUOTE_AFTER_QUANTITY_CHANGE"
        description, material, status = item["description"], item["material"], item["status"]
        notes = (item["notes"] + (" VP1 second jackshaft key cut to "
                 "14.8 mm before y388 bearing; fit/strength HOLD."
                 if part_id == "KEY-6-16" else ""))
        evidence = "C1_INTERFACE_BASELINE"
        if part_id == "SAFE-STOP":
            # The user reports one 2NC stop button, not the C1 handover
            # model. No part/rating identification or circuit qualification.
            description = "User-reported 2NC emergency stop button"
            status = "OWNED_REPORTED_RATING_HOLD"
            landed, cost_state = "", "OWNED_BUTTON_NO_NEW_PURCHASE_UNQUALIFIED"
            evidence = "USER_REPORTED_2NC_BUTTON_MODEL_UNVERIFIED"
            notes = (notes + " One 2NC button reported owned, with a reported "
                     "35x35 mm size (which face, body depth and panel cutout "
                     "unidentified); model, contact rating, positive opening, "
                     "wiring and hard-cut contactor unverified. No additional "
                     "button purchase assumed; full safety circuit unquoted.")
        elif part_id == "EL-PSU":
            # The donor rating and exterior size are user-reported, not a
            # nameplate, mount-hole, protection or power-circuit qualification.
            description = "User-reported Anycubic Chiron donor PSU, 24V 800W (label unverified)"
            material = "Donor PSU (unverified)"
            status = "OWNED_REPORTED_RATING_HOLD"
            landed, cost_state = "", "OWNED_DONOR_PSU_NO_NEW_PURCHASE_UNQUALIFIED"
            evidence = "USER_REPORTED_CHIRON_PSU_LABEL_UNVERIFIED"
            notes = (notes.replace("120x240x65 user measurement",
                                   "240x120x65 mm user-reported exterior")
                     .replace("model contains true body only",
                              "CAD box is an exterior envelope only")
                     + " Chiron donor PSU reported owned; 24V 800W is user-"
                     "reported. Label, mounting pattern, condition, protection "
                     "and 500W staged duty remain unverified; no replacement "
                     "PSU purchase assumed.")
        elif cost.get("owned_verified") == "True" or status.startswith("OWNED"):
            # Historical handover inventory is not current qualified stock.
            # Other donor subparts require an individual interface check.
            description = description.replace("Owned ", "").replace("Existing ", "")
            material = material.replace(" - existing", " candidate")
            status = ("DONOR_CUT_FIT_OR_PROCUREMENT_HOLD"
                      if part_id.startswith("FR-") else "PROCUREMENT_HOLD")
            landed, cost_state = "", "UNQUOTED_NOT_ZERO"
            evidence = "C1_GEOMETRY_REFERENCE_CURRENT_STOCK_UNCONFIRMED"
            notes = (notes.replace("120x240x65 user measurement",
                                   "120x240x65 historical reference envelope")
                     .replace("Existing BTS7960", "BTS7960 candidate")
                     + " Historical handover is not current qualified stock; "
                     "confirm donor part identity/interface or obtain landed quote.")
        elif part_id == "EL-DRV":
            notes = notes.replace("Existing BTS7960", "BTS7960 candidate")
        active.append({
            "scope": scope, "part_id": part_id, "description": description,
            "quantity": quantity, "material": material, "status": status,
            "source": item["source"], "evidence": evidence,
            "landed_line_KRW": landed, "cost_state": cost_state,
            "notes": notes,
        })

    for item in rows(C21/"bom/transmission_bom.csv"):
        active.append({
            "scope": "active_S2_C2.1", "part_id": item["item_id"],
            "description": item["description"], "quantity": item["qty"],
            "material": item["material_or_type"], "status": item["status"],
            "source": item["source"], "evidence": item["evidence"],
            "landed_line_KRW": item["landed_cost_KRW"],
            "cost_state": "KNOWN" if item["landed_cost_KRW"] else "UNKNOWN",
            "notes": item["notes"]
        })

    # VP1 Stage 1-3 delta rows: new parts, all costs explicitly UNQUOTED
    delta_fields = ["item_id", "description", "qty", "material_or_type",
                    "status", "source", "evidence", "landed_cost_KRW", "notes"]
    for item in rows(C21/"bom/vp1_bom_delta.csv"):
        landed = item["landed_cost_KRW"]
        if landed:
            raise RuntimeError("vp1 delta rows must not carry invented quotes: "
                               + item["item_id"])
        active.append({
            "scope": "vp1_stage1_3", "part_id": item["item_id"],
            "description": item["description"], "quantity": item["qty"],
            "material": item["material_or_type"], "status": item["status"],
            "source": item["source"], "evidence": item["evidence"],
            "landed_line_KRW": "",
            "cost_state": "UNQUOTED_NOT_ZERO",
            "notes": item["notes"]})

    ids = [item["part_id"] for item in active]
    if len(ids) != len(set(ids)):
        duplicates = sorted(part_id for part_id, count in Counter(ids).items() if count > 1)
        raise RuntimeError("Duplicate active BOM IDs: "+str(duplicates))
    active.sort(key=lambda item: (item["scope"], item["part_id"]))
    csv_path = C21/"bom/system_bom.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(active)
    xlsx_path = C21/"bom/system_bom.xlsx"
    write_xlsx(xlsx_path, active)

    cut_rows = rows(REPO/"bom/profile_cut_plan.csv")
    cut_ok = all(int(item["stock_mm"]) == int(item["cut_mm"])
                 + int(item["kerf_mm"])+int(item["remaining_mm"]) for item in cut_rows)
    scheduled_stock_mm = defaultdict(int)
    for item in cut_rows:
        scheduled_stock_mm[item["profile"]] += int(item["stock_mm"])
    known = [item for item in active if item["landed_line_KRW"] != ""]
    research = json.loads((REPO/"c2/results/continuation_research.json").read_text())
    motor_candidates = [item["known_motor_landed_floor_KRW"]
                        for item in research["procurement"]["candidates"]
                        if item.get("known_motor_landed_floor_KRW") is not None]
    cheapest_queried_motor = min(motor_candidates)
    summary = {
        "revision": "C2.1-P6+VP1-STAGE6",
        "active_rows": len(active),
        "unique_part_ids": len(set(ids)),
        "legacy_instances_removed": sum(removed.values()),
        "legacy_part_quantities_removed": dict(sorted(removed.items())),
        "adjusted_shared_quantities": {part_id: retained[part_id] for part_id in removed if retained[part_id]},
        "c21_rows_added": len(rows(C21/"bom/transmission_bom.csv")),
        "vp1_delta_rows": len(rows(C21/"bom/vp1_bom_delta.csv")),
        "vp1_delta_source": "c2.1/bom/vp1_bom_delta.csv",
        "known_cost_rows": len(known),
        "unknown_cost_rows": len(active)-len(known),
        "known_landed_total_KRW": (sum(float(item["landed_line_KRW"]) for item in known)
                                   if known else None),
        "queried_motor_candidate_price_plus_base_shipping_KRW": cheapest_queried_motor,
        "soft_total_budget_KRW": research["procurement"]["budget_soft_limit_KRW"],
        "current_inventory": {
            "status": "USER_REPORTED_2NC_BUTTON_AND_CHIRON_PSU_DONOR_UNQUALIFIED",
            "reported_owned_button_rows": sum(
                item["evidence"] == "USER_REPORTED_2NC_BUTTON_MODEL_UNVERIFIED"
                for item in active),
            "reported_owned_psu_rows": sum(
                item["evidence"] == "USER_REPORTED_CHIRON_PSU_LABEL_UNVERIFIED"
                for item in active),
            "qualified_stock_rows": 0,
            "historical_owned_rows_reclassified": sum(
                item["evidence"] == "C1_GEOMETRY_REFERENCE_CURRENT_STOCK_UNCONFIRMED"
                for item in active),
            "donor_printer": {
                "model": "Anycubic Chiron",
                "availability": "USER_REPORTED",
                "other_subparts": "UNALLOCATED_PENDING_LABEL_AND_DIMENSIONS",
                "profile_lengths": "UNMEASURED",
                "motor_driver_interfaces": "UNVERIFIED",
            },
            "feedstock": "NO_REFERENCE_PELLETS_REPORTED",
        },
        "candidate_motor_budget_gap_KRW": max(
            0, cheapest_queried_motor - research["procurement"]["budget_soft_limit_KRW"]),
        "minimum_functional_route": {
            "same_product": "reference_feed_same_extrusion_cooling_gauge_puller_winder",
            "staging": "upstream S1/S2 held during reference-feed qualification; not a substitute finished product",
            "cost_status": "UNPRICED_TWO_REPORTED_PARTS_UNQUALIFIED_NO_BUDGET_COMPLIANCE_PROVEN",
            "safety": "independent interlocks, fuses and lockout cannot be omitted",
        },
        "cost_conclusion": "BUTTON_AND_DONOR_PSU_REPORTED_OTHER_ACTIVE_ROWS_UNQUOTED_MOTOR_CANDIDATE_EXCEEDS_SOFT_BUDGET",
        "profile_cut_plan": {
            "rows": len(cut_rows), "stock_conservation_passed": cut_ok,
            "stock_available": None,
            "stock_confirmation_status": "DONOR_PROFILE_LENGTHS_UNMEASURED",
            "scheduled_stock_mm_by_profile": dict(sorted(scheduled_stock_mm.items())),
            "source_owned_flags": "HISTORICAL_C1_NOT_CURRENT_DONOR_STOCK",
            "basis": "cut layout conserves nominal stock; donor extrusion stock unmeasured",
            "source": "bom/profile_cut_plan.csv"},
        "csv": {"file": str(csv_path.relative_to(REPO)),
                "sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest()},
        "xlsx": {"file": str(xlsx_path.relative_to(REPO)),
                 "sha256": hashlib.sha256(xlsx_path.read_bytes()).hexdigest(),
                 "zip_test": zipfile.ZipFile(xlsx_path).testzip()},
        "procurement": "HOLD",
        "fabrication": "HOLD"
    }
    (C21/"results/system_bom_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))
    if not cut_ok or summary["xlsx"]["zip_test"] is not None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
