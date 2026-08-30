#!/usr/bin/env python3
"""정상·purge·rundown·hold·requalification phase의 독립 component 합산 검증."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from run_engineering import REV, phase_power_budget

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = phase_power_budget()
    if result["status"] != "PASS":
        raise SystemExit("ORCHESTRATION_POWER_FAIL " + json.dumps(result["states"], ensure_ascii=False))
    path = ROOT / "calculations/orchestration_power.csv"
    rows = result["states"]
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "calculations/orchestration_power.json").write_text(json.dumps({"revision": REV, **result}, ensure_ascii=False, indent=2) + "\n")
    maximum = max(row["computed_peak_w"] for row in rows)
    reserve = min(row["remaining_w_to_psu"] for row in rows)
    print(f"ORCHESTRATION_POWER_OK phases={len(rows)} peak={maximum:.1f}W reserve={reserve:.1f}W")


if __name__ == "__main__":
    main()
