#!/usr/bin/env python3
"""Validate all 40 mandated manual topics and their supporting evidence."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with (ROOT / "docs" / "manual_coverage.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["Number"]) for row in rows] == list(range(1, 41))
    assert all(row["Status"] == "INCLUDED" for row in rows)
    for row in rows:
        assert row["Required topic"] and row["Manual section"]
        assert (ROOT / row["Supporting file"]).is_file(), row
    source = (ROOT / "docs" / "build_manual_ko.typ").read_text()
    for required in (
        "항목 5 — 전체 BOM", "bom_rows = csv", "항목 9 — CNC 주문 방법",
        "항목 23 — Arduino Mega 핀맵", "항목 29 — PLA calibration",
        "항목 30 — PET calibration", "항목 40 — revision 및 변경 이력",
    ):
        assert required in source
    extracted = subprocess.run(
        ["pdftotext", "docs/build_manual_ko.pdf", "-"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout
    for row in rows:
        assert row["Required topic"] in extracted, row
    print("MANUAL_40_TOPIC_COVERAGE_OK")


if __name__ == "__main__":
    main()
