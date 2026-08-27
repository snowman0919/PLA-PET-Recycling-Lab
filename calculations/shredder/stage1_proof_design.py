#!/usr/bin/env python3
"""Reproducible first-order Stage-1 shredder load and shaft sweep.

MIT licensed calculation code. Results are analytical screening values, not
physical validation. Cutter geometry hardware remains CERN-OHL-P-2.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt


@dataclass(frozen=True)
class CutScenario:
    name: str
    shear_mpa: float
    engaged_width_mm: float
    effective_thickness_mm: float
    shear_planes: int
    engagements: int
    factor: float
    note: str

    def force_n(self) -> float:
        area_m2 = self.engaged_width_mm * self.effective_thickness_mm * 1e-6
        return self.shear_mpa * 1e6 * area_m2 * self.shear_planes * self.engagements

    def torque_nm(self, effective_radius_mm: float) -> float:
        return self.force_n() * effective_radius_mm / 1000 * self.factor


def shaft_result(
    torque_nm: float,
    diameter_mm: float,
    bearing_span_mm: float,
    force_radius_mm: float,
    yield_mpa: float = 305.0,
    elastic_modulus_gpa: float = 200.0,
) -> dict[str, float]:
    d = diameter_mm / 1000
    span = bearing_span_mm / 1000
    radius = force_radius_mm / 1000
    force = torque_nm / radius
    bending_moment = force * span / 4
    bending_pa = 32 * bending_moment / (pi * d**3)
    torsion_pa = 16 * torque_nm / (pi * d**3)
    von_mises_pa = sqrt(bending_pa**2 + 3 * torsion_pa**2)
    inertia = pi * d**4 / 64
    deflection_m = force * span**3 / (48 * elastic_modulus_gpa * 1e9 * inertia)
    return {
        "force_n": force,
        "bending_mpa": bending_pa / 1e6,
        "torsion_mpa": torsion_pa / 1e6,
        "von_mises_mpa": von_mises_pa / 1e6,
        "safety_factor": yield_mpa * 1e6 / von_mises_pa,
        "deflection_mm": deflection_m * 1000,
    }


def required_ratio(output_torque_nm: float, motor_torque_nm: float, efficiency: float) -> float:
    return output_torque_nm / (motor_torque_nm * efficiency)


def main() -> None:
    radius_mm = 25.0
    scenarios = [
        CutScenario(
            "PET nominal tear",
            shear_mpa=30,
            engaged_width_mm=8,
            effective_thickness_mm=0.35,
            shear_planes=2,
            engagements=1,
            factor=1.5,
            note="notched thin wall; buckling usually reduces this full-shear bound",
        ),
        CutScenario(
            "PET folded/local double engagement",
            shear_mpa=35,
            engaged_width_mm=10,
            effective_thickness_mm=0.70,
            shear_planes=2,
            engagements=2,
            factor=1.5,
            note="folded wall or neck-adjacent local stack; feed limiter should avoid sustained case",
        ),
        CutScenario(
            "PLA printed shell nominal",
            shear_mpa=30,
            engaged_width_mm=6,
            effective_thickness_mm=2.0,
            shear_planes=2,
            engagements=1,
            factor=1.5,
            note="fracture/bending may occur before full shear; infill not treated as solid block",
        ),
        CutScenario(
            "PLA thick shell overload",
            shear_mpa=40,
            engaged_width_mm=6,
            effective_thickness_mm=3.0,
            shear_planes=2,
            engagements=1,
            factor=1.5,
            note="overload boundary, not a promise to process solid PLA",
        ),
    ]

    print("SCENARIO TORQUE SCREEN")
    for s in scenarios:
        print(f"{s.name:34s} force={s.force_n():7.1f} N torque={s.torque_nm(radius_mm):6.1f} N·m")

    print("\nSHAFT SCREEN AT 60 N·m STRUCTURAL PROOF LOAD")
    for diameter in (12.0, 15.0, 17.0, 20.0):
        r = shaft_result(60.0, diameter, bearing_span_mm=80.0, force_radius_mm=radius_mm)
        print(
            f"d={diameter:4.1f} mm vm={r['von_mises_mpa']:6.1f} MPa "
            f"SF={r['safety_factor']:4.2f} defl={r['deflection_mm']:6.3f} mm"
        )

    print("\nILLUSTRATIVE REDUCTION CHECK — REPLACE WITH DONOR DYNO DATA")
    for motor_torque in (0.20, 0.40, 0.80):
        ratio = required_ratio(20.0, motor_torque, efficiency=0.60)
        print(f"motor={motor_torque:.2f} N·m, eta=0.60 -> ratio for 20 N·m = {ratio:.1f}:1")


if __name__ == "__main__":
    main()
