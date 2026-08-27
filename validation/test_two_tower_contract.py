#!/usr/bin/env python3
"""Protect the quantified two-tower release scope and stability decisions."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "calculations" / "architecture"))
from two_tower_contract import build_report  # noqa: E402


def main() -> None:
    report = build_report()
    release = report["requirement_resolution"]["release_configuration"]
    assert release["shredding"] == "THREE_STAGE_REQUIRED"
    assert "SIX_COLOR_AND_REJECT" in release["classification"]

    a = report["tower_a"]
    b = report["tower_b"]
    assert a["rack_envelope_mm"] == {"width": 600.0, "depth": 600.0, "height": 1350.0}
    assert a["maximum_input_lip_height_from_floor_mm"] <= 1350.0
    assert b["cooling_length_mm"] == 440.0
    assert b["die_to_gauge_center_mm"] == 470.0
    assert b["straight_service_rail_extension_from_die_mm"] >= 760.0

    batch = report["batch_interface"]
    assert batch["nominal_flake_capacity_kg"] >= 1.5
    assert batch["maximum_handled_mass_kg"] == 2.0
    assert "manual" in batch["transfer"]

    a_stability = a["stability_screen"]
    b_stability = b["stability_screen"]
    assert a_stability["anchor_required"]
    assert a_stability["anchor_candidate_safety_factor"] >= 4.0
    assert b_stability["unanchored_tip_acceleration_g"] >= 0.5
    assert len(report["mandatory_physical_gates"]) >= 5
    print("TWO_TOWER_ARCHITECTURE_VALIDATION_OK")


if __name__ == "__main__":
    main()
