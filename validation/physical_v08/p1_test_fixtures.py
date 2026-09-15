"""Synthetic declarations for tests only; never generate physical receipt evidence."""
import csv
import hashlib
import json
from pathlib import Path
import p1_semantics as semantics


def fill_semantics(rows, root: Path, folder: Path):
    control = root / "validation/physical_v08/inventory_confirmation.csv"
    for row in rows:
        if row.get("result") != "PASS": continue
        item = row["item_id"]
        row.update(identity_check="MATCHED_TO_REQUIREMENT", inspection_power_state="NONE")
        required = row["required"].strip()
        count = int(required) if required.isdecimal() else 2 if item == "MAT-CUT" else None
        if count is not None:
            row.update(observed_quantity=str(count), quantity_unit="count")
            continue
        entry = {"id": "SYNTHETIC-STOCK-" + item, "marking": "SYNTHETIC TEST ONLY", "condition": "GOOD", "quantity": 1, "unit": "count", "dimensions_or_spec": "synthetic dimension fixture"}
        entries = [entry]
        unit = "lot"; quantity = 1
        extra = {}
        if item in semantics.PROFILES:
            with (root / "exports/fabrication/frame_cut_list.csv").open(newline="") as f:
                length = sum(float(r["cut_length_mm"]) * int(r["quantity"]) for r in csv.DictReader(f) if r["stock"].startswith(semantics.PROFILES[item])) + 1000
            unit = "mm"; quantity = length
            entry.update(quantity=length, unit="mm", u95=1.0, profile_type="2020" if item=="ASSET-2020" else "2040")
            extra = {"frame_cut_list_sha256": hashlib.sha256((root/"exports/fabrication/frame_cut_list.csv").read_bytes()).hexdigest()}
        elif item in semantics.MASS:
            unit = "kg"; quantity = 10.0 if item == "ASSET-PLA" else .5
            entry.update(quantity=quantity, unit="kg", u95=.001)
        elif item in semantics.SETS:
            unit = "set"
            entries = [{**entry, "id": key, "quantity": value} for key, value in semantics.required_set(item, root).items()]
        elif item == "ASSET-TH-INS":
            unit = "roll"; entry.update(unit="roll")
            extra = {"label_width_mm": 25, "label_length_m": 30}
        elif item in semantics.BULK:
            extra = {"requirements_review": "ITEMIZED_STOCK_REVIEWED_NOT_FINAL_KITTING"}
        row.update(observed_quantity=str(quantity), quantity_unit=unit)
        data = {"schema_version": 1, "kind": "P1_INVENTORY_DETAIL", "item_id": item,
                "synthetic_fixture_only": True,
                "inventory_control_sha256": hashlib.sha256(control.read_bytes()).hexdigest(),
                "content_review": "ACCEPTED_FOR_UNPOWERED_INVENTORY_ONLY",
                "physical_action_authorized": False,
                "raw_files": {row["evidence_path"]: row["sha256"]}, "entries": entries, **extra}
        for key in ("manufacturer_model_marking", "condition", "quantity_unit", "operator", "reviewer", "measured_at"):
            data[key] = row[key]
        path = folder / (item + "-synthetic-detail.json")
        path.write_text(json.dumps(data, indent=2) + "\n")
        row["detail_path"] = path.relative_to(root).as_posix()
        row["detail_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rows
