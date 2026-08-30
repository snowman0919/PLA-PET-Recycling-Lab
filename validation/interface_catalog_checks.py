#!/usr/bin/env python3
"""Fail release on an incomplete or contradictory fabrication interface catalog."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "exports/fabrication/interface_catalog.csv"
REVISION = "coupled-digital-validation-v0.5"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    require(len(rows) >= 32, "interface catalog coverage is incomplete")
    require(len({row["interface_id"] for row in rows}) == len(rows), "duplicate interface id")
    required_columns = {
        "revision", "interface_id", "part_a", "part_b", "interface_type",
        "nominal_dimension_a", "nominal_dimension_b", "clearance_interference",
        "tolerance", "standard_reference", "assembly_method", "tool",
        "inspection_method", "status",
    }
    require(required_columns == set(rows[0]), "interface catalog schema mismatch")
    for row in rows:
        require(row["revision"] == REVISION, f"stale revision {row['interface_id']}")
        require(all(row[column].strip() for column in required_columns), f"blank field {row['interface_id']}")
        require("FAIL" not in row["status"] and "MISMATCH" not in row["status"], f"interface mismatch {row['interface_id']}")

    by_id = {row["interface_id"]: row for row in rows}
    require(by_id["IF-010"]["nominal_dimension_a"] == "Ø5 h6", "625 axle must be Ø5 h6")
    require("Ø16 H7" in by_id["IF-011"]["nominal_dimension_b"], "625 OD seat must be Ø16 H7")
    require("Ø5.2" in by_id["IF-012"]["nominal_dimension_b"], "PPR-C08 must locate the Ø5 axle")
    require("Ø34.0 custom" in by_id["IF-023"]["nominal_dimension_b"], "band heater ID mismatch")
    require("Ø6.20 H9" in by_id["IF-024"]["nominal_dimension_a"], "die heater bore mismatch")
    print(f"FABRICATION_INTERFACE_CATALOG_VALIDATED_OK rows={len(rows)}")


if __name__ == "__main__":
    main()
