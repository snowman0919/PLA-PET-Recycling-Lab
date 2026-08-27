#!/usr/bin/env python3
"""Stage-3 granulator load, shaft, screen-open-area and power screening."""

from __future__ import annotations

import json
from math import floor, pi, sqrt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def shaft(torque_nm: float, d_mm: float, span_mm: float, radius_mm: float) -> dict[str, float]:
    d = d_mm / 1000
    force = torque_nm / (radius_mm / 1000)
    moment = force * (span_mm / 1000) / 4
    bending = 32 * moment / (pi * d**3)
    torsion = 16 * torque_nm / (pi * d**3)
    vm = sqrt(bending**2 + 3 * torsion**2) / 1e6
    inertia = pi * d**4 / 64
    deflection = force * (span_mm / 1000) ** 3 / (48 * 200e9 * inertia) * 1000
    return {"force_n": force, "vm_mpa": vm, "sf_div_kt_1_6": 305 / vm / 1.6, "deflection_mm": deflection}


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["stage3"]
    radius = p["rotor_outer_diameter_mm"] / 2
    segment = p["active_width_mm"] / p["blade_axial_segments"]
    cases = (
        ("PET folded wall", 35, 0.7, 1),
        ("PLA 2 mm shell", 30, 2.0, 1),
        ("PLA two segments", 30, 2.0, 2),
    )
    print("STAGE3 CUT SCENARIOS")
    for name, shear, thickness, engagements in cases:
        force = shear * segment * thickness * 2 * engagements
        torque = force * radius / 1000 * 1.5
        print(f"{name:24s} force={force:6.1f} N torque={torque:5.1f} N·m")
    a = p["axial_layout"]
    span = a["right_bearing_z_mm"] - a["left_bearing_z_mm"]
    result = shaft(p["structural_proof_torque_nm"], p["shaft_diameter_mm"], span, radius)
    print(f"\nSHAFT span={span:.1f} mm proof={p['structural_proof_torque_nm']:.0f} N·m")
    print(f"force={result['force_n']:.0f} N vm={result['vm_mpa']:.1f} MPa SF/Kt1.6={result['sf_div_kt_1_6']:.2f} defl={result['deflection_mm']:.3f} mm")
    gross = (p["rotor_outer_diameter_mm"] + 10) * p["active_width_mm"]
    columns = floor(((p["rotor_outer_diameter_mm"] + 10) - 2 * p["screen_edge_margin_x_mm"]) / p["screen_pitch_mm"]) + 1
    rows = floor((p["active_width_mm"] - 2 * p["screen_edge_margin_z_mm"]) / p["screen_pitch_mm"]) + 1
    hole_count = columns * rows
    print("\nSCREEN GEOMETRIC OPEN AREA")
    for opening in p["screen_opening_candidates_mm"]:
        ratio = hole_count * pi * (opening / 2) ** 2 / gross
        print(f"opening={opening:.0f} mm ratio={ratio:.3f} pitch_web={p['screen_pitch_mm']-opening:.1f} mm")
    print("\nPOWER ENVELOPE")
    lo, hi = p["speed_range_rpm"]
    for rpm in (lo, (lo + hi) / 2, hi):
        for torque in p["continuous_torque_target_nm"]:
            print(f"rpm={rpm:3.0f} torque={torque:2.0f} N·m mechanical={torque*2*pi*rpm/60:5.0f} W")


if __name__ == "__main__":
    main()
