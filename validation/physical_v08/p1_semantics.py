"""Typed inventory declarations; hashes do not establish physical truth."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import re
from pathlib import Path

GOOD = {"GOOD", "USABLE", "NEW", "USED_SERVICEABLE"}
PLACEHOLDERS = {"", "UNKNOWN", "UNSELECTED", "N/A", "NA", "NONE", "NULL", "TBD", "PENDING", "미확인"}
BULK = {"ASSET-HW", "MAT-SHAFT", "MAT-PLATE", "MAT-GASKET"}
SETS = {"STOCK-K0", "STOCK-CHAIN", "STOCK-FUSE", "MAT-HOT"}
MASS = {"ASSET-PLA", "ASSET-ABS"}
PROFILES = {"ASSET-2020": "20x20", "ASSET-2040": "20x40"}


def number(value, label: str, *, positive: bool = True) -> float:
    if isinstance(value, bool) or value is None or not str(value).strip():
        raise ValueError(label + ": blank/bool numeric value")
    try:
        n = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(label + ": invalid numeric value") from exc
    if not math.isfinite(n) or (n <= 0 if positive else n < 0):
        raise ValueError(label + ": non-finite/nonpositive value")
    return n


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_file(root: Path, rel, expected_hash) -> Path:
    if not isinstance(rel, str) or not rel.strip():
        raise ValueError("missing structured evidence path")
    path = root / rel
    if Path(rel).is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("unsafe structured evidence path")
    if not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}", str(expected_hash)) or digest(path) != expected_hash:
        raise ValueError("structured evidence missing or hash mismatch")
    return path


def detail(row, root: Path, control: Path) -> dict:
    data = json.loads(checked_file(root, row.get("detail_path"), row.get("detail_sha256")).read_text())
    if data.get("schema_version") != 1 or data.get("kind") != "P1_INVENTORY_DETAIL":
        raise ValueError("invalid P1 structured evidence schema")
    if data.get("item_id") != row["item_id"] or data.get("inventory_control_sha256") != digest(control):
        raise ValueError("structured evidence item/requirement binding mismatch")
    for key in ("manufacturer_model_marking", "condition", "quantity_unit", "operator", "reviewer", "measured_at"):
        if data.get(key) != row.get(key):
            raise ValueError("structured evidence declaration mismatch: " + key)
    if data.get("content_review") != "ACCEPTED_FOR_UNPOWERED_INVENTORY_ONLY" or data.get("physical_action_authorized") is not False:
        raise ValueError("missing limited-scope content review")
    raw = data.get("raw_files", {})
    if not isinstance(raw, dict) or raw.get(row["evidence_path"]) != row["sha256"]:
        raise ValueError("structured evidence must bind the row's raw evidence")
    for rel, value in raw.items():
        checked_file(root, rel, value)
    return data


def required_set(item: str, root: Path) -> dict[str, int]:
    if item == "STOCK-K0": return {"K0_CONTACTOR": 1, "AUX_FEEDBACK": 1}
    if item == "STOCK-CHAIN": return {"CHAIN_35": 1, "SPROCKET_12T": 1, "SPROCKET_30T": 1}
    if item == "MAT-HOT": return {"EX-CPN-SCR": 1, "EX-CPN-BAR": 1}
    with (root / "exports/final/electrical/fuse_schedule.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    key = "fuse_id" if rows and "fuse_id" in rows[0] else "id"
    return {**{r[key]: 1 for r in rows}, "TF-BARREL": 1, "TF-DIE": 1, "TF-SPARE": 1}


def validate_row(row: dict, root: Path, control_path: Path) -> dict:
    item = row["item_id"]
    marking = row.get("manufacturer_model_marking", "").strip()
    if marking.upper() in PLACEHOLDERS or row.get("identity_check") != "MATCHED_TO_REQUIREMENT":
        raise ValueError(item + ": mandatory identity/marking check missing")
    if row.get("condition", "").strip().upper() not in GOOD:
        raise ValueError(item + ": nonconforming or unreviewed condition")
    if row.get("inspection_power_state") != "NONE":
        raise ValueError(item + ": inventory survey requires power NONE")
    n = number(row.get("observed_quantity"), item + " observed_quantity")
    numeric_required = row["required"].strip()
    count = int(numeric_required) if numeric_required.isdecimal() else 2 if item == "MAT-CUT" else None
    if count is not None:
        if row.get("quantity_unit") != "count" or not n.is_integer() or n != count:
            raise ValueError(item + ": exact allocated quantity mismatch")
        return {"kind": "exact_count", "observed": n, "required": count}
    data = detail(row, root, control_path)
    entries = data.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise ValueError(item + ": structured entries required")
    ids = set()
    for entry in entries:
        key = entry.get("id")
        if not isinstance(key, str) or not key.strip() or key in ids:
            raise ValueError(item + ": blank/duplicate entry identity")
        ids.add(key)
        if str(entry.get("marking", "")).strip().upper() in PLACEHOLDERS:
            raise ValueError(item + ": entry marking absent")
        if entry.get("condition") not in GOOD:
            raise ValueError(item + ": entry condition rejected")
        number(entry.get("quantity"), item + " entry quantity")
    if item in PROFILES:
        if row.get("quantity_unit") != "mm": raise ValueError(item + ": unit must be mm")
        if any(e.get("unit") != "mm" for e in entries): raise ValueError("profile entry unit")
        total = sum(number(e["quantity"], "length") for e in entries)
        lower = sum(number(e["quantity"], "length") - number(e.get("u95"), "length U95", positive=False) for e in entries)
        if any(number(e["quantity"], "length") <= number(e.get("u95"), "length U95", positive=False) for e in entries):
            raise ValueError("invalid conservative bar length")
        with (root / "exports/fabrication/frame_cut_list.csv").open(newline="") as f:
            minimum = sum(float(r["cut_length_mm"]) * int(r["quantity"]) for r in csv.DictReader(f) if r["stock"].startswith(PROFILES[item]))
        if minimum <= 0 or lower < minimum or not math.isclose(total, n, abs_tol=1e-6, rel_tol=0):
            raise ValueError(item + ": profile length short or entry total mismatch")
        return {"kind": "stock_length", "measured_mm": total, "conservative_mm": lower, "nominal_cut_mm": minimum, "nesting_required_at_p2": True}
    if item in MASS:
        if row.get("quantity_unit") != "kg" or any(e.get("unit") != "kg" for e in entries):
            raise ValueError(item + ": mass unit must be kg")
        lower = sum(number(e["quantity"], "mass") - number(e.get("u95"), "mass U95", positive=False) for e in entries)
        if any(number(e["quantity"], "mass") <= number(e.get("u95"), "mass U95", positive=False) for e in entries):
            raise ValueError(item + ": invalid individual mass interval")
        if lower <= 0 or not math.isclose(sum(float(e["quantity"]) for e in entries), n, abs_tol=1e-6, rel_tol=0):
            raise ValueError(item + ": invalid mass interval/total")
        return {"kind": "measured_mass_inventory", "kg": n, "production_capacity_verified": False}
    if item in SETS:
        if row.get("quantity_unit") != "set" or n != 1:
            raise ValueError(item + ": exactly one allocated set required")
        required = required_set(item, root)
        actual = {e["id"]: e["quantity"] for e in entries}
        if actual != required or any(e.get("unit") != "count" for e in entries):
            raise ValueError(item + ": set composition mismatch")
        return {"kind": "enumerated_set", "positions": sorted(required)}
    if item == "ASSET-TH-INS":
        if row.get("quantity_unit") != "roll" or n != 1 or len(entries) != 1 or entries[0].get("unit") != "roll" or entries[0]["quantity"] != 1:
            raise ValueError(item + ": exactly one identified roll required")
        if data.get("label_width_mm") != 25 or data.get("label_length_m") != 30:
            raise ValueError(item + ": received tape label differs from 25 mm x 30 m")
        return {"kind": "identified_roll", "thermal_qualification": "NOT_RUN"}
    if item in BULK:
        if row.get("quantity_unit") != "lot" or n != 1 or data.get("requirements_review") != "ITEMIZED_STOCK_REVIEWED_NOT_FINAL_KITTING":
            raise ValueError(item + ": itemized stock review required")
        for e in entries:
            if e.get("unit") not in {"count", "mm", "kg"} or not str(e.get("dimensions_or_spec", "")).strip():
                raise ValueError(item + ": stock unit/dimensions required")
        return {"kind": "itemized_stock", "entries": len(entries), "final_kitting_verified": False}
    raise ValueError(item + ": no approved quantity semantics")
