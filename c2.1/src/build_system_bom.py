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
        active.append({
            "scope": scope, "part_id": part_id, "description": item["description"],
            "quantity": quantity, "material": item["material"], "status": item["status"],
            "source": item["source"], "evidence": "C1_INTERFACE_BASELINE",
            "landed_line_KRW": landed, "cost_state": cost_state,
            "notes": (item["notes"] + (" VP1 second jackshaft key cut to "
                      "14.8 mm before y388 bearing; fit/strength HOLD."
                      if part_id == "KEY-6-16" else "")),
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
    known = [item for item in active if item["landed_line_KRW"] != ""]
    research = json.loads((REPO/"c2/results/continuation_research.json").read_text())
    motor_floors = [item["known_motor_landed_floor_KRW"]
                    for item in research["procurement"]["candidates"]
                    if item.get("known_motor_landed_floor_KRW") is not None]
    summary = {
        "revision": "C2.1-P6+VP1-STAGE5",
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
        "known_landed_total_KRW": sum(float(item["landed_line_KRW"]) for item in known),
        "unselected_motor_landed_floor_KRW": min(motor_floors),
        "soft_total_budget_KRW": research["procurement"]["budget_soft_limit_KRW"],
        "cost_conclusion": "INCOMPLETE_AND_KNOWN_MOTOR_FLOOR_EXCEEDS_TOTAL_SOFT_BUDGET",
        "profile_cut_plan": {"rows": len(cut_rows), "stock_conservation_passed": cut_ok,
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
