#!/usr/bin/env python3
"""Validate CNC/RFQ package coverage without overstating fabrication readiness."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "exports" / "cnc_quote_packages"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    bom = read(ROOT / "bom" / "bom.csv")
    expected_primary = {
        row["Part ID"] for row in bom if row["Source type"] in {"CNC", "FABRICATE"}
    }
    package_rows = []
    for filename, expected_count in (
        ("shredder_package.csv", 18),
        ("extruder_package.csv", 5),
        ("sheet_metal_package.csv", 11),
    ):
        rows = read(PACKAGE_DIR / filename)
        assert len(rows) == expected_count
        package_rows.extend(rows)
    ids = [row["Part ID"] for row in package_rows]
    assert len(ids) == len(set(ids)) == 34
    assert expected_primary <= set(ids)
    assert set(ids) - expected_primary == {"EXT-THR-001"}
    for row in package_rows:
        assert row["RFQ status"] == "RFQ_PRECHECK_ONLY_NOT_FABRICATION_RELEASE"
        assert "final material/tolerance/heat-treatment/DFM approval" in row["Open release gates"]
        assert (ROOT / row["Model STEP"]).is_file()
        assert (ROOT / row["Drawing notes"]).is_file()
        if not row["Profile DXF"].startswith("NOT_PROVIDED"):
            assert (ROOT / row["Profile DXF"]).is_file()
    readme = (PACKAGE_DIR / "README.md").read_text()
    assert "NOT_FABRICATION_RELEASED" in readme and "NO_ORDER_AUTHORIZED" in readme
    print("CNC_QUOTE_PACKAGES_OK")


if __name__ == "__main__":
    main()
