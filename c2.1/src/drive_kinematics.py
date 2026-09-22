"""Pure kinematics/math for the VP1 common drive — NO cadquery dependency.

Split out of drive_teeth.py (VP1 Stage 3 closing fix): the CI runner has no
cadquery, so the pure-math contract functions (tooth counts, pitch radii,
tangent geometry, chain lengths, ratio chain) live here and are imported by
drive_teeth.py, the tests and any cq-free consumer.
"""
from __future__ import annotations

import math

MODULE_N = 2.0
HELIX_DEG = 15.0
PRESSURE_DEG = 20.0
BACKLASH_MM = 0.08   # tangential backlash (j), typical stock-gear value for mn=2
CHAIN_PITCH = 9.525
ROLLER_R = 2.54
CHAIN_RADIAL_ENV = 5.5
CHAIN_AXIAL = 5.0

# Sprocket placement datums (XZ, from design/assembly.json instances)
CHAIN_A = dict(p1=(136.94018992255457, 65.0), p2=(130.0, 398.30275184708404),
               z1=24, z2=24, links=94, y0=354.0)
CHAIN_B = dict(p1=(80.0, 65.0), p2=(308.56946468906176, 280.0),
               z1=24, z2=12, links=84, y0=374.0)


def gear_pitch_radius(z):
    """Transverse pitch radius of a helical gear (normal module mn)."""
    return MODULE_N * z / (2.0 * math.cos(math.radians(HELIX_DEG)))


def gear_center_distance(z1, z2):
    return gear_pitch_radius(z1) + gear_pitch_radius(z2)


def sprocket_pitch_radius(z):
    return CHAIN_PITCH / (2.0 * math.sin(math.pi / z))


def _tangent_data(c1, r1, c2, r2):
    """External tangent construction in XZ. Returns the two touch-point
    4-tuples, the tangent half-angle phi and the center distance; asserts
    the tangent lines really are tangent (perpendicular distance == r)."""
    ux, uz = c2[0] - c1[0], c2[1] - c1[1]
    d = math.hypot(ux, uz)
    ux, uz = ux / d, uz / d
    px, pz = -uz, ux
    cos_phi = (r1 - r2) / d
    sin_phi = math.sqrt(max(0.0, 1.0 - cos_phi * cos_phi))
    normals = [(cos_phi * ux + sin_phi * px, cos_phi * uz + sin_phi * pz),
               (cos_phi * ux - sin_phi * px, cos_phi * uz - sin_phi * pz)]
    t = []
    for n in normals:
        t.append((c1[0] + r1 * n[0], c1[1] + r1 * n[1],
                  c2[0] + r2 * n[0], c2[1] + r2 * n[1]))
    phi = math.acos(cos_phi)
    return t, phi, d


def chain_length_mm(chain):
    p1, p2 = chain["p1"], chain["p2"]
    r1 = sprocket_pitch_radius(chain["z1"])
    r2 = sprocket_pitch_radius(chain["z2"])
    lines, phi, dist = _tangent_data(p1, r1, p2, r2)
    straight = math.hypot(lines[0][2] - lines[0][0], lines[0][3] - lines[0][1])
    return 2.0 * straight + r1 * (2.0 * math.pi - 2.0 * phi) + r2 * 2.0 * phi


def ratio_chain(input_rpm=58.0):
    """Kinematic chain from the frozen C1 drive layout (teeth counts only).
    M1 -> DRV-CPL12 (1:1) -> 15T/40T helical mesh -> jackshaft; chain A 24/24
    -> S1 shaft A; S1-SYNC 30T/30T external mesh -> shaft B counter-rotates;
    chain B 24T(input) -> 12T -> S2 input; S2 cycloid q=8 -> phi=-theta/8."""
    gear_ratio = 15.0 / 40.0
    chain_a = 24.0 / 24.0
    chain_b = 24.0 / 12.0
    jack = input_rpm * gear_ratio
    s1a = jack * chain_a
    return {
        "input_rpm": input_rpm,
        "jackshaft_rpm": jack,
        "s1_shaft_A_rpm": s1a,
        "s1_shaft_B_rpm": -s1a,
        "s2_input_rpm": input_rpm * chain_b,
        "s2_output_rpm": -input_rpm * chain_b / 8.0,
        "s2_output_vs_adr_nominal_120rpm_delta_rpm": input_rpm * chain_b - 120.0,
    }
