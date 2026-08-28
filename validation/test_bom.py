#!/usr/bin/env python3
"""Validate BOM identity, status, evidence and the two design variants."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    source = rows(ROOT / "bom" / "bom.csv")
    target = rows(ROOT / "bom" / "target_budget_design.csv")
    recommended = rows(ROOT / "bom" / "engineering_recommended_design.csv")
    evidence = rows(ROOT / "bom" / "cost_evidence.csv")
    routes = rows(ROOT / "bom" / "procurement_routes.csv")
    rollup = rows(ROOT / "bom" / "cost_rollup.csv")
    summary = json.loads((ROOT / "bom" / "cost_summary.json").read_text())

    ids = [row["Part ID"] for row in source]
    assert len(source) == 85 and len(ids) == len(set(ids))
    assert len(target) == len(recommended) == len(source)
    assert [row["Part ID"] for row in target] == ids
    assert [row["Part ID"] for row in recommended] == ids
    assert sum(row["Criticality"] == "CRITICAL" for row in source) == 59
    assert all(row["Status"] and row["Validation evidence"] for row in source)
    assert {row["Source type"] for row in source} <= {
        "BUY", "CNC", "FABRICATE", "PRINT", "PROJECT_LAB", "REUSE"
    }

    assert len(evidence) == 28
    assert len({row["Evidence ID"] for row in evidence}) == len(evidence)
    primary = {row["Part ID"]: row for row in evidence if row["Selection"] == "PRIMARY_CANDIDATE"}
    assert {part_id: row["Planning floor KRW"] for part_id, row in primary.items()} == {
        "ELE-BUCK-001": "42644",
        "GAU-CAM-001": "35000",
        "GRN-BRG-001": "5320",
        "SAF-EST-001": "143001",
        "SAF-REL-001": "200200",
    }
    assert all(row["Observed date"] == "2026-08-28" for row in evidence)
    assert all(row["Source URL"].startswith("https://") for row in evidence)
    assert all(row["Selection"] != "PRIMARY_CANDIDATE" for row in evidence if row["Distributor"] == "AliExpress")
    assert all(row["Marketplace safety class"] == "MARKETPLACE_SAMPLE_ONLY" for row in evidence if row["Distributor"] == "AliExpress")
    assert all(row["Acquisition method"] == "PLAYWRIGHT_SEARCH" for row in evidence if row["Distributor"] == "AliExpress")
    evidence_by_id = {row["Evidence ID"]: row for row in evidence}
    for evidence_id in {"PRICE-SIEVE6-AE-20260828", "PRICE-SIEVE3-AE-20260828", "PRICE-MIRROR-AE-20260828"}:
        assert evidence_by_id[evidence_id]["Selection"] == "SAMPLE_ONLY"
    assert evidence_by_id["PRICE-51102-DM-20260828"]["Selection"] == "PARTIAL_ASSEMBLY"
    assert evidence_by_id["PRICE-51102-DM-20260828"]["Stock observed"] == "0"
    rejected = {row["Evidence ID"]: row for row in evidence if row["Selection"] == "REJECTED"}
    assert rejected["REJECT-SSR-AC-DM-20260828"]["Status"] == "REJECTED_WRONG_OUTPUT_TYPE"
    assert summary["public_candidate_floor_krw"] == 426165
    assert summary["public_candidate_floor_over_cap_krw"] == 226165
    assert summary["engineering_candidate_floor_krw"] == 5240261
    assert summary["target_budget_status"].startswith("CONDITIONAL_ONLY")
    assert "TBD" in summary["engineering_recommended_total_status"]
    rollup_by_name = {row["Rollup"]: row for row in rollup}
    assert set(rollup_by_name) == {
        "NEW_PURCHASE", "ENGINEERING_CANDIDATE_SET", "CNC_FABRICATION", "PRINT_FILAMENT",
        "PROJECT_LAB_REPLACEMENT", "DONOR_REPLACEMENT",
        "REQUIRED_BASELINE", "OPTIONAL_ADDONS",
    }
    assert rollup_by_name["NEW_PURCHASE"]["Known planning floor KRW"] == "426165"
    assert rollup_by_name["NEW_PURCHASE"]["TBD line count"] == "27"
    assert rollup_by_name["ENGINEERING_CANDIDATE_SET"]["Known planning floor KRW"] == "5240261"
    assert rollup_by_name["CNC_FABRICATION"]["TBD line count"] == "33"
    assert rollup_by_name["REQUIRED_BASELINE"]["BOM line count"] == "85"
    assert rollup_by_name["REQUIRED_BASELINE"]["TBD line count"] == "78"
    assert rollup_by_name["OPTIONAL_ADDONS"]["BOM line count"] == "0"

    buy_ids = {row["Part ID"] for row in source if row["Source type"] == "BUY"}
    assert len(routes) == 32
    assert {row["Part ID"] for row in routes} == buy_ids
    route_by_id = {row["Part ID"]: row for row in routes}
    for part_id in {
        "DRY-PLA-HTR", "DRY-PET-HTR", "EXT-REL-001", "SAF-EST-001",
        "SAF-REL-001", "SAF-CON-001", "SAF-FUS-HLD", "SAF-FUS-001", "SAF-THM-001",
        "SAF-INT-001", "ELE-HTR-DRV", "ELE-HTR-HS", "ELE-BUCK-001", "CTL-ENC-001",
    }:
        assert route_by_id[part_id]["AliExpress policy"] == "FORBIDDEN"
    assert route_by_id["GRN-BRG-001"]["AliExpress policy"] == "SAMPLE_ONLY"
    assert route_by_id["SRT-ISO-001"]["Evidence state"] == "CANDIDATE_EVIDENCE_RECORDED"

    critical_ids = {row["Part ID"] for row in source if row["Criticality"] == "CRITICAL"}
    target_by_id = {row["Part ID"]: row for row in target}
    for part_id in critical_ids - {"SYS-CTRL-001", "SYS-CTRL-002"}:
        assert target_by_id[part_id]["Planning floor KRW"] != "0", part_id
    print("BOM_VALIDATION_OK")


if __name__ == "__main__":
    main()
