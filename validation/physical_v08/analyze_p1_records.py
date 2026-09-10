#!/usr/bin/env python3
"""Fail-closed P1 inventory/receipt analyzer; never authorizes procurement or fabrication."""
from __future__ import annotations
import argparse, csv, datetime, hashlib, importlib.util, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTROL = HERE / "inventory_confirmation.csv"
GGM_INSPECTION = ROOT / "analysis/drive_acceptance_v08/manufacturing/inspection.py"
SURVEY_STATES = {
    "USER_REPORTED_AVAILABLE", "MEASURE_STOCK",
    "CHECK_PROJECT_LAB_FIRST", "CHECK_PROJECT_LAB_FIRST_THEN_BUY",
}
GGM_AXES = {"BUY-GGM-SH": ("SH", "K9G75C"), "BUY-GGM-EX": ("EX", "K9G150C")}
ALLOWED_RESULTS = {"PASS", "NOT_FOUND", "IDENTITY_PENDING", "SEEN_NOT_MEASURED", "NOT_RUN"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inspection():
    spec = importlib.util.spec_from_file_location("ppr_p1_ggm_inspection", GGM_INSPECTION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load GGM inspection authority")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def require_time(value: str, item_id: str) -> None:
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{item_id}: measured_at must include timezone")


def verify_evidence(row, root: Path):
    item = row["item_id"]
    required = ("observed_quantity", "dimension_or_rating_summary", "condition", "instrument_id",
                "instrument_calibration_ref", "measured_at", "operator", "reviewer", "evidence_path", "sha256")
    missing = [field for field in required if not row.get(field, "").strip()]
    if missing:
        raise ValueError(f"{item}: PASS missing " + ",".join(missing))
    if row["operator"].strip() == row["reviewer"].strip():
        raise ValueError(f"{item}: independent reviewer must differ from operator")
    require_time(row["measured_at"].strip(), item)
    rel = row["evidence_path"].strip(); digest = row["sha256"].strip().lower()
    if not SHA256_RE.fullmatch(digest):
        raise ValueError(f"{item}: PASS requires valid sha256")
    path = (root / rel).resolve(); resolved_root = root.resolve()
    if not path.is_relative_to(resolved_root) or not path.is_file():
        raise ValueError(f"{item}: invalid evidence {rel}")
    if sha(path) != digest:
        raise ValueError(f"{item}: evidence sha256 mismatch")


def expected_inventory() -> dict[str, dict[str, str]]:
    rows = read_csv(CONTROL)
    return {row["item_id"]: row for row in rows}


def validate_ggm_axis(packet: dict, axis: str, gear: str, inspection) -> dict:
    receipt = packet.get("receipt", {})
    if receipt.get("performed") is not True:
        raise ValueError(f"{axis}: GGM receipt packet is not performed")
    record = receipt.get("data", {}).get(axis)
    if not isinstance(record, dict):
        raise ValueError(f"{axis}: GGM receipt record missing")
    inspection.evidence(record)
    if record.get("motor_model") != "K9DG60N2" or record.get("gear_model") != gear:
        raise ValueError(f"{axis}: wrong GGM motor/gear identity")
    for name, limits in inspection.RECEIPT.items():
        inspection.interval(record["readings"][name], *limits)
    return {"axis": axis, "motor_model": record["motor_model"], "gear_model": gear,
            "part_serial": record["part_serial"], "receipt_check_count": len(inspection.RECEIPT)}


def evaluate(rows, evidence_root: Path, ggm_packet: dict | None = None):
    expected = expected_inventory()
    by_id = {r.get("item_id", "").strip(): r for r in rows}
    if len(by_id) != len(rows) or "" in by_id:
        raise ValueError("blank or duplicate item_id")
    if set(by_id) != set(expected):
        missing = sorted(set(expected) - set(by_id)); extra = sorted(set(by_id) - set(expected))
        raise ValueError(f"P1 inventory coverage mismatch missing={missing} extra={extra}")
    for item, control in expected.items():
        row = by_id[item]
        if row.get("planned_state", "").strip() != control["current_state"].strip():
            raise ValueError(f"{item}: planned_state differs from inventory_confirmation.csv")
        if row.get("required", "").strip() != control["required_quantity_or_capacity"].strip():
            raise ValueError(f"{item}: required quantity/capacity drift")

    unresolved=[]; failures=[]; passed=[]; verified_ggm={}
    ggm_pass_ids=[]
    for item, row in by_id.items():
        result=row.get("result", "").strip().upper()
        if result not in ALLOWED_RESULTS:
            raise ValueError(f"{item}: invalid result {result!r}")
        if result == "PASS":
            verify_evidence(row, evidence_root); passed.append(item)
            if item in GGM_AXES: ggm_pass_ids.append(item)
        elif result in {"NOT_FOUND", "IDENTITY_PENDING", "SEEN_NOT_MEASURED"}:
            failures.append(item)
        if row.get("planned_state", "").strip() in SURVEY_STATES and result == "NOT_RUN":
            unresolved.append(item)

    if ggm_pass_ids:
        if not isinstance(ggm_packet, dict):
            raise ValueError("GGM PASS rows require --ggm-packet physical receipt evidence")
        inspection = load_inspection()
        seen_serials=set()
        for item in sorted(ggm_pass_ids):
            axis, gear = GGM_AXES[item]
            checked = validate_ggm_axis(ggm_packet, axis, gear, inspection)
            if checked["part_serial"] in seen_serials:
                raise ValueError("duplicate GGM part identity")
            seen_serials.add(checked["part_serial"]); verified_ggm[axis]=checked

    missing_ggm=sorted(item for item in GGM_AXES if by_id[item].get("result", "").strip().upper() != "PASS")
    if failures: status="P1_REJECTED"
    elif unresolved: status="P1_SURVEY_INCOMPLETE"
    elif missing_ggm: status="P1_STOCK_SURVEY_PASS_GGM_PENDING"
    else: status="P1_RECORD_CHECK_PASS"
    return {
        "status":status, "stage_p1_pass":status=="P1_RECORD_CHECK_PASS",
        "hardware_authorization":False, "procurement_authorization":False,
        "inventory_control_sha256":sha(CONTROL), "required_item_count":len(expected),
        "passed_count":len(passed), "survey_unresolved":sorted(unresolved),
        "nonconforming_or_missing":sorted(failures), "ggm_receipt_pending":missing_ggm,
        "ggm_receipt_verified":verified_ggm,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("inventory", type=Path)
    ap.add_argument("--ggm-packet", type=Path); ap.add_argument("--output", type=Path)
    args=ap.parse_args()
    packet=json.loads(args.ggm_packet.read_text(encoding="utf-8")) if args.ggm_packet else None
    try:
        result=evaluate(read_csv(args.inventory), ROOT, packet); code=0 if result["status"] in {"P1_STOCK_SURVEY_PASS_GGM_PENDING", "P1_RECORD_CHECK_PASS"} else 2
    except (ValueError, KeyError, TypeError, FileNotFoundError, json.JSONDecodeError) as exc:
        result={"status":"P1_REJECTED", "stage_p1_pass":False, "hardware_authorization":False,
                "procurement_authorization":False, "reason":str(exc)}; code=2
    text=json.dumps(result, ensure_ascii=False, indent=2)+"\n"
    if args.output: args.output.write_text(text, encoding="utf-8")
    print(text, end=""); raise SystemExit(code)


if __name__ == "__main__": main()
