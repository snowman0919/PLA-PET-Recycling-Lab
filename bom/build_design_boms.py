#!/usr/bin/env python3
"""Validate the system BOM and generate honest budget/recommended variants."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOM = ROOT / "bom" / "bom.csv"
OUTPUT_FIELDS = [
    "Part ID",
    "Module",
    "Description",
    "Quantity",
    "Baseline status",
    "Source strategy",
    "Planning floor KRW",
    "Cost status",
    "Validation/approval gate",
]
COST_ROLLUP_FIELDS = [
    "Rollup",
    "Included source types",
    "BOM line count",
    "Known planning floor KRW",
    "TBD line count",
    "Total status",
    "Notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_variant(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_cost_rollup(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COST_ROLLUP_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    source = read_csv(BOM)
    evidence = read_csv(ROOT / "bom" / "cost_evidence.csv")
    assert source, "empty BOM"
    ids = [row["Part ID"] for row in source]
    assert len(ids) == len(set(ids)), "duplicate Part ID"
    assert all(len(row) == 19 for row in source), "BOM row width differs from header"
    assert all(row["Status"] for row in source), "missing status"
    assert all(row["Criticality"] for row in source), "missing criticality"

    primary_evidence = [row for row in evidence if row["Selection"] == "PRIMARY_CANDIDATE"]
    assert len({row["Part ID"] for row in primary_evidence}) == len(primary_evidence), (
        "more than one primary cost candidate for a BOM row"
    )
    public_floor = {
        row["Part ID"]: int(row["Planning floor KRW"])
        for row in primary_evidence
    }
    engineering_evidence = [
        row for row in evidence
        if row["Selection"] in {"PRIMARY_CANDIDATE", "QUALIFICATION_CANDIDATE", "SIZING_CANDIDATE"}
    ]
    assert len({row["Part ID"] for row in engineering_evidence}) == len(engineering_evidence), (
        "more than one active engineering cost candidate for a BOM row"
    )
    engineering_floor = {
        row["Part ID"]: int(row["Planning floor KRW"])
        for row in engineering_evidence
    }
    target: list[dict[str, str]] = []
    recommended: list[dict[str, str]] = []
    for row in source:
        part_id = row["Part ID"]
        available_reuse = row["Status"] == "AVAILABLE" and row["Source type"] == "REUSE"
        target_floor = public_floor.get(part_id, 0 if available_reuse else "TBD")
        if available_reuse:
            target_strategy = "VERIFIED_REUSE"
            target_cost_status = "KNOWN_ZERO_CASH_AFTER_INSPECTION"
        elif part_id in public_floor:
            target_strategy = "PROJECT_LAB_STOCK_REQUIRED"
            target_cost_status = "PUBLIC_NEW_PRICE_BREAKS_CAP_FLOOR"
        elif row["Criticality"] == "CRITICAL":
            target_strategy = "PROJECT_LAB_OR_DONOR_ONLY"
            target_cost_status = "BLOCKED_WITHOUT_VALIDATED_STOCK"
        else:
            target_strategy = "PROJECT_LAB_FIRST_BUY_SHORTAGE_ONLY"
            target_cost_status = "TBD_AFTER_INVENTORY"
        target.append(
            {
                "Part ID": part_id,
                "Module": row["Module"],
                "Description": row["Description"],
                "Quantity": row["Quantity"],
                "Baseline status": row["Status"],
                "Source strategy": target_strategy,
                "Planning floor KRW": target_floor,
                "Cost status": target_cost_status,
                "Validation/approval gate": row["Validation evidence"],
            }
        )

        if part_id in engineering_floor:
            recommended_strategy = f"BUY_CANDIDATE_{row['Vendor']}_{row['Part number']}"
            recommended_cost = engineering_floor[part_id]
            recommended_status = "PUBLIC_REFERENCE_QUALIFICATION_AND_LANDED_COST_OPEN"
        elif available_reuse:
            recommended_strategy = "REUSE_AFTER_INSPECTION"
            recommended_cost = 0
            recommended_status = "ZERO_CASH_ASSUMPTION"
        elif row["Source type"] == "CNC":
            recommended_strategy = "FABRICATION_QUOTE_REQUIRED"
            recommended_cost = "TBD"
            recommended_status = "NO_ORDER_WITHOUT_USER_APPROVAL"
        else:
            recommended_strategy = "SELECT_MPN_THEN_QUOTE"
            recommended_cost = "TBD"
            recommended_status = "NO_ORDER_WITHOUT_USER_APPROVAL"
        recommended.append(
            {
                "Part ID": part_id,
                "Module": row["Module"],
                "Description": row["Description"],
                "Quantity": row["Quantity"],
                "Baseline status": row["Status"],
                "Source strategy": recommended_strategy,
                "Planning floor KRW": recommended_cost,
                "Cost status": recommended_status,
                "Validation/approval gate": row["Validation evidence"],
            }
        )

    write_variant(ROOT / "bom" / "target_budget_design.csv", target)
    write_variant(ROOT / "bom" / "engineering_recommended_design.csv", recommended)
    public_floor_total = sum(public_floor.values())
    source_counts = Counter(row["Source type"] for row in source)
    known_zero_cash_ids = {
        row["Part ID"]
        for row in source
        if row["Status"] == "AVAILABLE" and row["Source type"] == "REUSE"
    }
    required_tbd_lines = len(source) - len(public_floor) - len(known_zero_cash_ids)
    rollup = [
        {
            "Rollup": "NEW_PURCHASE",
            "Included source types": "BUY",
            "BOM line count": source_counts["BUY"],
            "Known planning floor KRW": public_floor_total,
            "TBD line count": source_counts["BUY"] - len(public_floor),
            "Total status": "INCOMPLETE_LANDED_TOTAL",
            "Notes": f"{len(public_floor)} public primary candidates only; shipping tax customs and {source_counts['BUY'] - len(public_floor)} purchase lines remain TBD.",
        },
        {
            "Rollup": "ENGINEERING_CANDIDATE_SET",
            "Included source types": "BUY candidate rows only",
            "BOM line count": len(engineering_floor),
            "Known planning floor KRW": sum(engineering_floor.values()),
            "TBD line count": 0,
            "Total status": "INCOMPLETE_QUALIFICATION_AND_LANDED_COST_OPEN",
            "Notes": "Includes primary, qualification and sizing candidates; it is neither a complete system total nor purchase approval.",
        },
        {
            "Rollup": "CNC_FABRICATION",
            "Included source types": "CNC+FABRICATE",
            "BOM line count": source_counts["CNC"] + source_counts["FABRICATE"],
            "Known planning floor KRW": 0,
            "TBD line count": source_counts["CNC"] + source_counts["FABRICATE"],
            "Total status": "TBD_QUOTES_REQUIRED",
            "Notes": "No fabrication quote is represented as zero cost.",
        },
        {
            "Rollup": "PRINT_FILAMENT",
            "Included source types": "PRINT",
            "BOM line count": source_counts["PRINT"],
            "Known planning floor KRW": 0,
            "TBD line count": source_counts["PRINT"],
            "Total status": "TBD_SLICER_MASS_AND_MATERIAL_PRICE",
            "Notes": "Requires final orientation support and slicer mass for each print set.",
        },
        {
            "Rollup": "PROJECT_LAB_REPLACEMENT",
            "Included source types": "PROJECT_LAB",
            "BOM line count": source_counts["PROJECT_LAB"],
            "Known planning floor KRW": 0,
            "TBD line count": source_counts["PROJECT_LAB"],
            "Total status": "TBD_INVENTORY_AND_REPLACEMENT_VALUE",
            "Notes": "Project-lab availability is not a verified zero replacement value.",
        },
        {
            "Rollup": "DONOR_REPLACEMENT",
            "Included source types": "REUSE",
            "BOM line count": source_counts["REUSE"],
            "Known planning floor KRW": 0,
            "TBD line count": source_counts["REUSE"],
            "Total status": "TBD_AFTER_INSPECTION_AND_DYNO",
            "Notes": "Current cash may be zero for user-stated donor parts after inspection; all replacement values remain TBD.",
        },
        {
            "Rollup": "REQUIRED_BASELINE",
            "Included source types": "ALL",
            "BOM line count": len(source),
            "Known planning floor KRW": public_floor_total,
            "TBD line count": required_tbd_lines,
            "Total status": "INCOMPLETE_NOT_BUDGET_COMPLIANT",
            "Notes": f"All {len(source)} baseline rows are required; {len(public_floor)} primary public floors and {len(known_zero_cash_ids)} conditional on-hand zero-cash rows are the target-budget assumptions.",
        },
        {
            "Rollup": "OPTIONAL_ADDONS",
            "Included source types": "NONE",
            "BOM line count": 0,
            "Known planning floor KRW": 0,
            "TBD line count": 0,
            "Total status": "NO_OPTIONAL_ROWS_IN_BASELINE",
            "Notes": "No required item is reclassified as optional to make the cap appear achievable.",
        },
    ]
    write_cost_rollup(ROOT / "bom" / "cost_rollup.csv", rollup)
    summary = {
        "revision": "0.2.0-undergraduate-mvp",
        "generated_date": "2026-08-28",
        "bom_row_count": len(source),
        "critical_row_count": sum(row["Criticality"] == "CRITICAL" for row in source),
        "status_counts": dict(sorted(Counter(row["Status"] for row in source).items())),
        "target_budget_cap_krw": 200000,
        "public_candidate_floor_krw": public_floor_total,
        "public_candidate_floor_over_cap_krw": public_floor_total - 200000,
        "public_candidate_floor_includes": sorted(public_floor),
        "engineering_candidate_floor_krw": sum(engineering_floor.values()),
        "engineering_candidate_floor_includes": sorted(engineering_floor),
        "cost_rollup_file": "bom/cost_rollup.csv",
        "required_baseline_line_count": len(source),
        "optional_addon_line_count": 0,
        "required_baseline_tbd_line_count": required_tbd_lines,
        "target_budget_status": "CONDITIONAL_ONLY_IF_PRIMARY_CANDIDATES_ARE_VALIDATED_STOCK_OR_REUSE",
        "engineering_recommended_total_status": "TBD_PENDING_DONOR_INVENTORY_MPN_SELECTION_AND_CNC_QUOTES",
        "pricing_assumptions": [
            "Planning conversion uses 1 USD = 1400 KRW and is not a live FX quote.",
            "Public prices exclude unresolved shipping, tax, customs, incomplete assemblies and all unpriced rows; qualification candidates are not purchase approvals.",
            "Conditional zero current cash applies only to the user-stated on-hand Arduino Mega; PSU fitness and replacement remain TBD.",
        ],
    }
    (ROOT / "bom" / "cost_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    modules = Counter(row["Module"] for row in source)
    markdown = [
        "# 시스템 BOM 요약",
        "",
        f"총 {len(source)}개 line item, CRITICAL {summary['critical_row_count']}개다. 이 문서는 `build_design_boms.py`가 `bom.csv`에서 생성한 검사 요약이며 주문서가 아니다.",
        "",
        "## 모듈별 line item",
        "",
        "| 모듈 | 행 수 |",
        "|---|---:|",
    ]
    markdown.extend(f"| {module} | {count} |" for module, count in sorted(modules.items()))
    markdown.extend(
        [
            "",
            "## 비용 상태",
            "",
            f"공개 primary 후보 {len(public_floor)}개 품목의 planning floor는 {public_floor_total:,} KRW로 200,000 KRW cap을 {public_floor_total - 200000:,} KRW 초과한다. 나머지 부품·가공·미확정 배송·세금은 포함하지 않았다.",
            "",
            "- `target_budget_design.csv`: 검증된 project-lab/donor stock을 우선하며, critical stock이 없으면 BLOCKED다.",
            "- `engineering_recommended_design.csv`: 안전·압력·열 부품을 생략하지 않고 MPN 선정과 CNC quote를 요구한다.",
            "- `cost_evidence.csv`: 조회일·URL·계획 환율을 보존한다.",
            f"- `procurement_routes.csv`: {source_counts['BUY']}개 BUY 행의 권장 공급처·대체 공급처·AliExpress 허용 경계를 기록한다.",
            "- `cost_rollup.csv`: 신규 구매·CNC·print filament·project-lab replacement·donor replacement와 required/optional을 분리한다.",
            "",
            "주문·가공은 사용자 승인 전 진행하지 않는다.",
        ]
    )
    (ROOT / "bom" / "bom.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
