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


def overhung_timing_sensitivity(
    torque_nm: float,
    diameter_mm: float,
    bearing_span_mm: float,
    force_radius_mm: float,
    timing_pitch_radius_mm: float,
    gear_overhang_mm: float,
    transferred_torque_fraction: float = 0.5,
    yield_mpa: float = 305.0,
) -> dict[str, float]:
    """Conservative superposition for an unsupported timing gear.

    The cutting-force bending model already places the full shaft torque at the
    active-span centre.  This sensitivity adds a same-plane gear moment from the
    stated fraction of torque; it is not a detailed shaft FEA.
    """

    d = diameter_mm / 1000
    cut_force_n = torque_nm / (force_radius_mm / 1000)
    cut_moment_nm = cut_force_n * (bearing_span_mm / 1000) / 4
    gear_torque_nm = torque_nm * transferred_torque_fraction
    gear_force_n = gear_torque_nm / (timing_pitch_radius_mm / 1000)
    gear_moment_nm = gear_force_n * (gear_overhang_mm / 1000)
    combined_moment_nm = cut_moment_nm + gear_moment_nm
    bending_pa = 32 * combined_moment_nm / (pi * d**3)
    torsion_pa = 16 * torque_nm / (pi * d**3)
    von_mises_pa = sqrt(bending_pa**2 + 3 * torsion_pa**2)
    return {
        "gear_force_n": gear_force_n,
        "cut_moment_nm": cut_moment_nm,
        "gear_moment_nm": gear_moment_nm,
        "combined_von_mises_mpa": von_mises_pa / 1e6,
        "safety_factor_div_kt_1_6": yield_mpa * 1e6 / von_mises_pa / 1.6,
    }


def required_ratio(output_torque_nm: float, motor_torque_nm: float, efficiency: float) -> float:
    return output_torque_nm / (motor_torque_nm * efficiency)


def key_result(torque_nm: float, shaft_mm: float, key_width_mm: float, key_height_mm: float, length_mm: float) -> dict[str, float]:
    d, width, height, length = (value / 1000 for value in (shaft_mm, key_width_mm, key_height_mm, length_mm))
    return {
        "shear_mpa": 2 * torque_nm / (d * width * length) / 1e6,
        "bearing_mpa": 4 * torque_nm / (d * height * length) / 1e6,
    }


def bearing_result(
    torque_nm: float,
    force_radius_mm: float,
    dynamic_rating_n: float,
    static_rating_n: float,
    cutter_rpm: float,
) -> dict[str, float]:
    reaction_n = torque_nm / (force_radius_mm / 1000) / 2
    l10_million_revolutions = (dynamic_rating_n / reaction_n) ** 3
    return {
        "reaction_n": reaction_n,
        "static_safety_factor": static_rating_n / reaction_n,
        "l10_hours_ideal": l10_million_revolutions * 1e6 / (60 * cutter_rpm),
    }


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

    bearing_span_mm = 81.0
    print(f"\nSHAFT SCREEN AT 60 N·m STRUCTURAL PROOF LOAD, span={bearing_span_mm:.1f} mm")
    for diameter in (12.0, 15.0, 17.0, 20.0):
        r = shaft_result(60.0, diameter, bearing_span_mm=bearing_span_mm, force_radius_mm=radius_mm)
        print(
            f"d={diameter:4.1f} mm vm={r['von_mises_mpa']:6.1f} MPa "
            f"SF={r['safety_factor']:4.2f} SF/Kt1.6={r['safety_factor']/1.6:4.2f} "
            f"defl={r['deflection_mm']:6.3f} mm"
        )

    print("\nKEY AND 6004 BEARING SCREEN")
    key = key_result(60.0, shaft_mm=20.0, key_width_mm=6.0, key_height_mm=6.0, length_mm=50.0)
    bearing = bearing_result(60.0, radius_mm, dynamic_rating_n=9950.0, static_rating_n=5000.0, cutter_rpm=30.0)
    print(f"6x6 key L=50 mm: shear={key['shear_mpa']:.1f} MPa bearing={key['bearing_mpa']:.1f} MPa")
    print(
        f"6004 candidate: reaction={bearing['reaction_n']:.0f} N static_SF={bearing['static_safety_factor']:.2f} "
        f"ideal_L10={bearing['l10_hours_ideal']:.0f} h"
    )
    print("L10 excludes shock spectrum, contamination, misalignment, fit and lubrication effects.")

    print("\nUNSUPPORTED TIMING-GEAR SENSITIVITY — OMITTED BY RECOMMENDED STRADDLE SUPPORT")
    for torque in (50.0, 60.0):
        timing = overhung_timing_sensitivity(
            torque,
            diameter_mm=20.0,
            bearing_span_mm=bearing_span_mm,
            force_radius_mm=radius_mm,
            timing_pitch_radius_mm=25.0,
            gear_overhang_mm=16.0,
        )
        print(
            f"T={torque:.0f} N·m gear_force={timing['gear_force_n']:.0f} N "
            f"Mgear={timing['gear_moment_nm']:.1f} N·m vm={timing['combined_von_mises_mpa']:.1f} MPa "
            f"SF/Kt1.6={timing['safety_factor_div_kt_1_6']:.2f}"
        )
    print("Assumes half of total torque is transferred at 25 mm pitch radius and 16 mm overhang.")

    print("\nILLUSTRATIVE REDUCTION CHECK — REPLACE WITH DONOR DYNO DATA")
    for motor_torque in (0.20, 0.40, 0.80):
        ratio = required_ratio(20.0, motor_torque, efficiency=0.60)
        print(f"motor={motor_torque:.2f} N·m, eta=0.60 -> ratio for 20 N·m = {ratio:.1f}:1")


if __name__ == "__main__":
    main()
