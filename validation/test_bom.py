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
    rollup = rows(ROOT / "bom" / "cost_rollup.csv")
    summary = json.loads((ROOT / "bom" / "cost_summary.json").read_text())

    ids = [row["Part ID"] for row in source]
    assert len(source) == 81 and len(ids) == len(set(ids))
    assert len(target) == len(recommended) == len(source)
    assert [row["Part ID"] for row in target] == ids
    assert [row["Part ID"] for row in recommended] == ids
    assert sum(row["Criticality"] == "CRITICAL" for row in source) == 56
    assert all(row["Status"] and row["Validation evidence"] for row in source)
    assert {row["Source type"] for row in source} <= {
        "BUY", "CNC", "FABRICATE", "PRINT", "PROJECT_LAB", "REUSE"
    }

    evidence_by_part = {row["Part ID"]: row for row in evidence}
    assert evidence_by_part["GAU-CAM-001"]["Planning floor KRW"] == "35000"
    assert evidence_by_part["SAF-REL-001"]["Planning floor KRW"] == "200200"
    assert all(row["Observed date"] == "2026-08-28" for row in evidence)
    assert all(row["Source URL"].startswith("https://") for row in evidence)
    assert summary["public_candidate_floor_krw"] == 235200
    assert summary["public_candidate_floor_over_cap_krw"] == 35200
    assert summary["target_budget_status"].startswith("CONDITIONAL_ONLY")
    assert "TBD" in summary["engineering_recommended_total_status"]
    rollup_by_name = {row["Rollup"]: row for row in rollup}
    assert set(rollup_by_name) == {
        "NEW_PURCHASE", "CNC_FABRICATION", "PRINT_FILAMENT",
        "PROJECT_LAB_REPLACEMENT", "DONOR_REPLACEMENT",
        "REQUIRED_BASELINE", "OPTIONAL_ADDONS",
    }
    assert rollup_by_name["NEW_PURCHASE"]["Known planning floor KRW"] == "235200"
    assert rollup_by_name["NEW_PURCHASE"]["TBD line count"] == "26"
    assert rollup_by_name["CNC_FABRICATION"]["TBD line count"] == "33"
    assert rollup_by_name["REQUIRED_BASELINE"]["BOM line count"] == "81"
    assert rollup_by_name["REQUIRED_BASELINE"]["TBD line count"] == "77"
    assert rollup_by_name["OPTIONAL_ADDONS"]["BOM line count"] == "0"

    critical_ids = {row["Part ID"] for row in source if row["Criticality"] == "CRITICAL"}
    target_by_id = {row["Part ID"]: row for row in target}
    for part_id in critical_ids - {"SYS-CTRL-001", "SYS-CTRL-002"}:
        assert target_by_id[part_id]["Planning floor KRW"] != "0", part_id
    print("BOM_VALIDATION_OK")


if __name__ == "__main__":
    main()
