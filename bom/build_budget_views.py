#!/usr/bin/env python3
"""Generate separate conditional and evidence-backed procurement budget states."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    rows=list(csv.DictReader((ROOT/"bom/cash_budget.csv").open()))
    target=int(next(r for r in rows if r["item_id"]=="TARGET_TOTAL")["planned_cash_krw"])
    reserve=int(next(r for r in rows if r["item_id"]=="ABSOLUTE_CAP_RESERVE")["planned_cash_krw"])
    absolute=int(next(r for r in rows if r["item_id"]=="ABSOLUTE_TOTAL_WITH_RESERVE")["planned_cash_krw"])
    print_cost=int(next(r for r in rows if r["item_id"]=="PRINT-ALLOW")["planned_cash_krw"])
    verified=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"} and r["status"] in {"RECEIPT_VERIFIED","QUOTE_VERIFIED"}]
    verified_subtotal=sum(int(r["planned_cash_krw"]) for r in verified)
    blocked=[r for r in rows if r["category"] not in {"TOTAL","CONTINGENCY"} and r["status"] not in {"RECEIPT_VERIFIED","QUOTE_VERIFIED"}]
    out=[
        ["METADATA","revision","","solid-manifold-openmodelica-v0.4","generated from bom/cash_budget.csv"],
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
