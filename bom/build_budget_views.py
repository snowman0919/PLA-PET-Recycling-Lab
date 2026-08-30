#!/usr/bin/env python3
"""Generate separate conditional and evidence-backed procurement budget states."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


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
    target=sum(int(r["planned_cash_krw"]) for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"})
    absolute=target+reserve
    target_row=next(r for r in rows if r["item_id"]=="TARGET_TOTAL")
    target_row["planned_cash_krw"]=str(target)
    target_row["status"]="CONDITIONAL_TARGET_PASS" if target<=180000 else "CONDITIONAL_TARGET_FAIL"
    absolute_row=next(r for r in rows if r["item_id"]=="ABSOLUTE_TOTAL_WITH_RESERVE")
    absolute_row["planned_cash_krw"]=str(absolute)
    absolute_row["status"]="CONDITIONAL_CAP_PASS" if absolute<=200000 else "CONDITIONAL_CAP_FAIL"
    absolute_row["evidence_or_blocker"]=f"200000 KRW 절대상한까지 {200000-absolute} KRW 여유"
    with cash_path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(rows)
    verified=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"} and r["status"] in {"RECEIPT_VERIFIED","QUOTE_VERIFIED"}]
    verified_subtotal=sum(int(r["planned_cash_krw"]) for r in verified)
    blocked=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"} and r["status"] not in {"RECEIPT_VERIFIED","QUOTE_VERIFIED"}]
    out=[
        ["METADATA","revision","","coupled-digital-validation-v0.5","generated from bom/cash_budget.csv"],
        ["CONDITIONAL_PLANNING_BUDGET","conditional_subtotal",target,"PASS_TARGET_LE_180000","target allowances; not quotes or receipts"],
        ["CONDITIONAL_PLANNING_BUDGET","print_material_including_support_and_12pct_reserve",print_cost,"PRUSASLICER_ESTIMATE","actual toolpath estimate, not purchase receipt"],
        ["CONDITIONAL_PLANNING_BUDGET","shipping_tax",0,"INCLUDED_ONLY_IN_CONTINGENCY","no supplier quote"],
        ["CONDITIONAL_PLANNING_BUDGET","contingency",reserve,"RESERVED","shipping machining variance failed prints fasteners consumables"],
        ["CONDITIONAL_PLANNING_BUDGET","absolute_total",absolute,"PASS_CAP_LE_200000","conditional subtotal plus contingency"],
        ["CONDITIONAL_PLANNING_BUDGET","remaining_margin",200000-absolute,"CONDITIONAL_ONLY","not verified purchasing headroom"],
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
    if not (target<=180000 and absolute<=200000 and verified_subtotal==0 and blocked):
        raise SystemExit("CONDITIONAL_AND_VERIFIED_BUDGET_FAIL")
    print(f"CONDITIONAL_AND_VERIFIED_BUDGET_OK conditional={target} absolute={absolute} verified_state=NOT_ESTABLISHED blocked={len(blocked)}")


if __name__=="__main__": main()
