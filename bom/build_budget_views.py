#!/usr/bin/env python3
"""Generate separate conditional and evidence-backed procurement budget states."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

PRICE_STATUS = "INFORMATIONAL"
PRICE_RELEASE_BLOCKING = False
PROCUREMENT_APPROVAL_GATE = "USER_APPROVAL_REQUIRED"


def price_policy(absolute_total_krw: int) -> dict[str, object]:
    """Return price reporting state without changing the technical gate.

    The former 200,000 KRW cap remains visible as planning context.  It is not
    a safety, physics, fabrication, or release acceptance criterion in v0.6.2.1.
    """
    return {
        "price_status": PRICE_STATUS,
        "price_release_blocking": PRICE_RELEASE_BLOCKING,
        "procurement_approval_gate": PROCUREMENT_APPROVAL_GATE,
        "former_target_krw": 200000,
        "absolute_total_krw": absolute_total_krw,
        "delta_to_former_target_krw": absolute_total_krw - 200000,
        "technical_release_blocked": False,
    }


def main():
    cash_path=ROOT/"bom/cash_budget.csv"
    rows=list(csv.DictReader(cash_path.open()))
    slicing=json.loads((ROOT/"validation/results/slicer_results.json").read_text())
    print_path=ROOT/"bom/printed_material_cost.csv"
    print_rows=list(csv.DictReader(print_path.open()))
    fieldnames=list(print_rows[0].keys())
    mass_field="slicer_mass_total_g" if "slicer_mass_total_g" in fieldnames else "estimated_mass_g"
    print_rows=[r for r in print_rows if r["part_id"] not in {"TOTAL_NOMINAL","FAILED_PRINT_RESERVE_12_PERCENT","TOTAL_SLICED","TOTAL_PLANNING"}]
    cost_per_kg=18000
    sliced_cost=round(float(slicing["total_mass_g"])*cost_per_kg/1000)
    print_cost=round(float(slicing["planning_mass_g"])*cost_per_kg/1000)
    def total_row(part_id, mass, cost, status):
        row={name:"" for name in fieldnames}
        row.update({"part_id":part_id,"quantity":"1","material":"PLA/ABS",mass_field:f"{mass:.2f}","cost_krw_per_kg":str(cost_per_kg),"estimated_cost_krw":str(cost),"status":status})
        return row
    print_rows.extend([
        total_row("TOTAL_SLICED",float(slicing["total_mass_g"]),sliced_cost,"PRUSASLICER_ESTIMATE"),
        total_row("TOTAL_PLANNING",float(slicing["planning_mass_g"]),print_cost,"PRUSASLICER_PLUS_12_PERCENT_RESERVE"),
    ])
    with print_path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames,lineterminator="\n"); w.writeheader(); w.writerows(print_rows)
    print_row=next(r for r in rows if r["item_id"]=="PRINT-ALLOW")
    print_row["planned_cash_krw"]=str(print_cost)
    print_row["description"]=f"PrusaSlicer 2.9.6 nominal {slicing['total_mass_g']:.2f} g plus 12 percent reserve"
    print_row["evidence_or_blocker"]=f"planning mass {slicing['planning_mass_g']:.2f} g at 18000 KRW/kg"
    reserve=int(next(r for r in rows if r["item_id"]=="ABSOLUTE_CAP_RESERVE")["planned_cash_krw"])
    machine_rows=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY","OPTIONAL_EMPIRICAL"}]
    target=sum(int(r["planned_cash_krw"]) for r in machine_rows)
    optional_empirical=sum(int(r["planned_cash_krw"]) for r in rows if r["category"]=="OPTIONAL_EMPIRICAL")
    absolute=target+reserve
    target_row=next(r for r in rows if r["item_id"]=="TARGET_TOTAL")
    target_row["planned_cash_krw"]=str(target)
    target_row["status"]="INFORMATIONAL_AT_OR_BELOW_FORMER_TARGET" if target<=180000 else "INFORMATIONAL_ABOVE_FORMER_TARGET"
    absolute_row=next(r for r in rows if r["item_id"]=="ABSOLUTE_TOTAL_WITH_RESERVE")
    absolute_row["planned_cash_krw"]=str(absolute)
    absolute_row["status"]="INFORMATIONAL_AT_OR_BELOW_FORMER_TARGET" if absolute<=200000 else "INFORMATIONAL_ABOVE_FORMER_TARGET"
    absolute_row["evidence_or_blocker"]=f"이전 200000 KRW 목표 대비 {absolute-200000:+d} KRW; 기술 릴리스 비차단"
    with cash_path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(rows)
    verified=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"} and r["status"] in {"RECEIPT_VERIFIED","QUOTE_VERIFIED"}]
    verified_subtotal=sum(int(r["planned_cash_krw"]) for r in verified)
    blocked=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"} and r["status"] not in {"RECEIPT_VERIFIED","QUOTE_VERIFIED"}]
    out=[
        ["METADATA","revision","","technical-blocker-closure-v0.6.2.1","generated from bom/cash_budget.csv"],
        ["METADATA","PRICE_STATUS","",PRICE_STATUS,"price is reported but does not gate technical release"],
        ["METADATA","PRICE_RELEASE_BLOCKING","",str(PRICE_RELEASE_BLOCKING).lower(),"technical release conjunction excludes price"],
        ["METADATA","PROCUREMENT_APPROVAL_GATE","",PROCUREMENT_APPROVAL_GATE,"no purchase or payment without user approval"],
        ["CONDITIONAL_PLANNING_BUDGET","conditional_subtotal",target,"INFORMATIONAL","target allowances; not quotes or receipts"],
        ["CONDITIONAL_PLANNING_BUDGET","print_material_including_support_and_12pct_reserve",print_cost,"PRUSASLICER_ESTIMATE","actual toolpath estimate, not purchase receipt"],
        ["CONDITIONAL_PLANNING_BUDGET","shipping_tax",0,"INCLUDED_ONLY_IN_CONTINGENCY","no supplier quote"],
        ["CONDITIONAL_PLANNING_BUDGET","contingency",reserve,"RESERVED","shipping machining variance failed prints fasteners consumables"],
        ["CONDITIONAL_PLANNING_BUDGET","absolute_total",absolute,"INFORMATIONAL","conditional subtotal plus contingency; no technical release effect"],
        ["CONDITIONAL_PLANNING_BUDGET","delta_to_former_target",absolute-200000,"INFORMATIONAL_ONLY","not verified purchasing headroom and not a technical gate"],
        ["OPTIONAL_EMPIRICAL_VALIDATION","gate1_optional_cost",optional_empirical,"EXCLUDED_FROM_DESIGN_RELEASE_MACHINE_TOTAL","requires separate user approval if performed"],
        ["VERIFIED_PROCUREMENT_BUDGET","verified_quoted_or_receipted_subtotal",verified_subtotal,"NOT_ESTABLISHED" if blocked else "PASS","zero means no item is yet evidence-qualified, not a zero-cost machine"],
        ["VERIFIED_PROCUREMENT_BUDGET","shipping_tax","","UNKNOWN","supplier destinations and quotes absent"],
        ["VERIFIED_PROCUREMENT_BUDGET","print_material_including_support","","UNKNOWN","filament lot/receipt absent"],
        ["VERIFIED_PROCUREMENT_BUDGET","contingency",reserve,"RESERVED_NOT_SPENT","cannot be used to hide blocked base cost"],
        ["VERIFIED_PROCUREMENT_BUDGET","remaining_margin","","UNKNOWN","cannot calculate until every blocked item has quote/receipt or verified donor evidence"],
    ]
    for row in blocked:
        out.append(["BLOCKED_ITEM",row["item_id"],row["planned_cash_krw"],row["status"],row["evidence_or_blocker"]])
    path=ROOT/"bom/verified_budget.csv"
    with path.open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["budget_state","field_or_item","amount_krw","status","evidence_or_blocker"]); w.writerows(out)
    policy = price_policy(absolute)
    (ROOT / "bom" / "budget_policy.json").write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n"
    )
    if not (verified_subtotal == 0 and blocked):
        raise SystemExit("BUDGET_EVIDENCE_CLASSIFICATION_FAIL")
    print(
        "CONDITIONAL_AND_VERIFIED_BUDGET_OK "
        f"conditional={target} absolute={absolute} price_status={PRICE_STATUS} "
        f"technical_release_blocked=false verified_state=NOT_ESTABLISHED blocked={len(blocked)}"
    )


if __name__=="__main__": main()
