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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_variant(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    source = read_csv(BOM)
    assert source, "empty BOM"
    ids = [row["Part ID"] for row in source]
    assert len(ids) == len(set(ids)), "duplicate Part ID"
    assert all(len(row) == 19 for row in source), "BOM row width differs from header"
    assert all(row["Status"] for row in source), "missing status"
    assert all(row["Criticality"] for row in source), "missing criticality"

    public_floor = {"GAU-CAM-001": 35000, "SAF-REL-001": 200200}
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

        if part_id in public_floor:
            recommended_strategy = f"BUY_CANDIDATE_{row['Vendor']}_{row['Part number']}"
            recommended_cost = public_floor[part_id]
            recommended_status = "PUBLIC_REFERENCE_NOT_LANDED_QUOTE"
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
    summary = {
        "revision": "0.1.0-preflight",
        "generated_date": "2026-08-28",
        "bom_row_count": len(source),
        "critical_row_count": sum(row["Criticality"] == "CRITICAL" for row in source),
        "status_counts": dict(sorted(Counter(row["Status"] for row in source).items())),
        "target_budget_cap_krw": 200000,
        "public_candidate_floor_krw": public_floor_total,
        "public_candidate_floor_over_cap_krw": public_floor_total - 200000,
        "public_candidate_floor_includes": sorted(public_floor),
        "target_budget_status": "CONDITIONAL_ONLY_IF_SAFETY_RELAY_AND_CAMERA_ARE_VALIDATED_STOCK",
        "engineering_recommended_total_status": "TBD_PENDING_DONOR_INVENTORY_MPN_SELECTION_AND_CNC_QUOTES",
        "pricing_assumptions": [
            "Planning conversion uses 1 USD = 1400 KRW and is not a live FX quote.",
            "Public prices exclude shipping, tax, customs, E-stop actuator, contactor and all unpriced rows.",
            "Zero cash applies only to user-stated on-hand Pi, Mega and PSU after inspection.",
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
            f"공개 후보 두 품목의 planning floor는 {public_floor_total:,} KRW로 200,000 KRW cap을 {public_floor_total - 200000:,} KRW 초과한다. 나머지 부품·가공·배송·세금은 포함하지 않았다.",
            "",
            "- `target_budget_design.csv`: 검증된 project-lab/donor stock을 우선하며, critical stock이 없으면 BLOCKED다.",
            "- `engineering_recommended_design.csv`: 안전·압력·열 부품을 생략하지 않고 MPN 선정과 CNC quote를 요구한다.",
            "- `cost_evidence.csv`: 조회일·URL·계획 환율을 보존한다.",
            "",
            "주문·가공은 사용자 승인 전 진행하지 않는다.",
        ]
    )
    (ROOT / "bom" / "bom.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
