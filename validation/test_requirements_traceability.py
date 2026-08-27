#!/usr/bin/env python3
"""Require complete one-to-one requirement traceability and real evidence paths."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    requirements_text = (ROOT / "requirements" / "system_requirements.md").read_text()
    declared = set(re.findall(r"\| (REQ-[A-Z]+-\d{3}) \|", requirements_text))
    with (ROOT / "requirements" / "compliance_matrix.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["Requirement ID"] for row in rows]
    assert len(declared) == len(rows) == 43
    assert len(ids) == len(set(ids))
    assert set(ids) == declared
    allowed = {"AUTOMATED_PASS", "DESIGN_EVIDENCE", "PHYSICAL_OPEN", "BLOCKED_EXTERNAL"}
    assert {row["Disposition"] for row in rows} <= allowed
    assert any(row["Disposition"] == "BLOCKED_EXTERNAL" for row in rows)
    assert any(row["Disposition"] == "PHYSICAL_OPEN" for row in rows)
    for row in rows:
        assert row["Open verification"] and row["Owner"]
        for field in ("Local evidence", "Automated evidence"):
            for relative in row[field].split(";"):
                assert relative and (ROOT / relative).is_file(), (
                    row["Requirement ID"], field, relative
                )
    generated = (ROOT / "requirements" / "compliance_matrix.md").read_text()
    assert all(requirement_id in generated for requirement_id in ids)
    print("REQUIREMENTS_TRACEABILITY_OK")


if __name__ == "__main__":
    main()
