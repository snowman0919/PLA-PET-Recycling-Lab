#!/usr/bin/env python3
"""First-order Stage-2 rotor, shaft, bed-knife and speed screening."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import pi, sqrt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Scenario:
    name: str
    shear_mpa: float
    width_mm: float
    thickness_mm: float
    planes: int
    engagements: int
    factor: float

    def result(self, radius_mm: float) -> tuple[float, float]:
        force_n = self.shear_mpa * self.width_mm * self.thickness_mm * self.planes * self.engagements
        return force_n, force_n * radius_mm / 1000 * self.factor


def shaft_screen(torque_nm: float, diameter_mm: float, span_mm: float, radius_mm: float) -> dict[str, float]:
    d = diameter_mm / 1000
    force_n = torque_nm / (radius_mm / 1000)
    moment_nm = force_n * (span_mm / 1000) / 4
    bending_pa = 32 * moment_nm / (pi * d**3)
    torsion_pa = 16 * torque_nm / (pi * d**3)
    vm_mpa = sqrt(bending_pa**2 + 3 * torsion_pa**2) / 1e6
    inertia = pi * d**4 / 64
    deflection_mm = force_n * (span_mm / 1000) ** 3 / (48 * 200e9 * inertia) * 1000
    return {"force_n": force_n, "vm_mpa": vm_mpa, "sf_div_kt_1_6": 305 / vm_mpa / 1.6, "deflection_mm": deflection_mm}


def main() -> None:
    params = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["stage2"]
    radius_mm = params["rotor_outer_diameter_mm"] / 2
    segment_width_mm = params["active_width_mm"] / params["blade_axial_segments"]
    scenarios = (
        Scenario("PET folded wall", 35, segment_width_mm, 0.70, 2, 1, 1.5),
        Scenario("PLA 2 mm shell", 30, segment_width_mm, 2.0, 2, 1, 1.5),
        Scenario("PLA two local engagements", 30, segment_width_mm, 2.0, 2, 2, 1.5),
    )
    print("STAGE2 CUT SCENARIOS")
    for scenario in scenarios:
        force, torque = scenario.result(radius_mm)
        print(f"{scenario.name:28s} force={force:7.1f} N torque={torque:5.1f} N·m")

    axial = params["axial_layout"]
    span_mm = axial["right_bearing_z_mm"] - axial["left_bearing_z_mm"]
    proof_nm = params["structural_proof_torque_nm"]
    print(f"\n{params['shaft_diameter_mm']:.0f} MM SHAFT AT {proof_nm:.0f} N·m PROOF, span={span_mm:.1f} mm")
    shaft = shaft_screen(proof_nm, params["shaft_diameter_mm"], span_mm=span_mm, radius_mm=radius_mm)
    print(
        f"force={shaft['force_n']:.0f} N vm={shaft['vm_mpa']:.1f} MPa "
        f"SF/Kt1.6={shaft['sf_div_kt_1_6']:.2f} defl={shaft['deflection_mm']:.3f} mm"
    )

    print("\nSPEED/POWER ENVELOPE")
    blades = 3
    speed_low, speed_high = params["speed_range_rpm"]
    for rpm in (speed_low, (speed_low + speed_high) / 2, speed_high):
        pass_hz = blades * rpm / 60
        for torque in params["continuous_torque_target_nm"]:
            power_w = torque * 2 * pi * rpm / 60
            print(f"rpm={rpm:3.0f} torque={torque:2.0f} N·m blade_pass={pass_hz:4.1f} Hz mechanical={power_w:5.0f} W")
    print("Output size and feed speed require physical coupons; blade-pass frequency alone is not a size guarantee.")


if __name__ == "__main__":
    main()
