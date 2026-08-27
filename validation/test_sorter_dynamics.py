#!/usr/bin/env python3
"""Regression checks for the vibratory sorter dynamic envelope."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calculations" / "vibration"))
from sorter_dynamics import build_report  # noqa: E402


def main() -> None:
    report = build_report()
    baseline = report["baseline"]
    assert 16.5 <= baseline["excitation_force_peak_n"] <= 17.5
    assert 0.30 <= baseline["amplitude_mm"] <= 0.40
    assert 1.1 <= baseline["acceleration_peak_g"] <= 1.4
    assert baseline["force_transmissibility"] <= 0.15
    assert 3.5 <= report["static_deflection_mm"] <= 4.2
    assert report["transport_velocity_mm_s_range"][0] >= 6.0
    assert report["active_deck_residence_s_range"][1] <= 50.0
    assert report["screen_nominal_open_area"]["top_6mm"] > report["screen_nominal_open_area"]["bottom_3mm"]
    path = ROOT / "simulation" / "vibration" / "vibratory_sorter_response.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["baseline"], indent=2))
    print("SORTER_DYNAMICS_OK")


if __name__ == "__main__":
    main()
