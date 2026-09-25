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

# Sprocket placement datums (XZ). ADR-002 rev B (VP1 Stage 4 layout fix):
# chain B is driven from the JACKSHAFT 24T (new instance DRV-SP24-B20_002 at
# jack y373..381, XZ datum 136.94018992255457/65) instead of the input-shaft
# sprocket, so the strand no longer crosses the jackshaft core; the S2 12T
# sprocket sits at (308.569..., 280) in the same y-plane (376..381 band).
# Chain B doubles the already-reduced jackshaft speed (58 -> 21.75 -> 43.5 rpm);
# 76 links = 723.9 mm nominal.
CHAIN_A = dict(p1=(136.94018992255457, 65.0), p2=(130.0, 398.30275184708404),
               z1=24, z2=24, links=94, y0=354.0)
CHAIN_B = dict(p1=(136.94018992255457, 65.0), p2=(308.56946468906176, 280.0),
               z1=24, z2=12, links=76, y0=374.0)
# The PDL transfer chain drives the WORM SHAFT at x362,z374.5 from the S2
# 12T sprocket, 1:1 12T/12T. A 34-link chain is 8.884 mm shorter than this
# centre path and cannot assemble; 35 links require an offset link and leave
# ~0.64 mm length surplus. Offset-link strength and tension are UNRATED/HOLD.
# Power path: M1 -> 15T/40T -> jackshaft -> chain B -> S2Ecc 12T ->
# chain P -> worm shaft 12T -> RH 2-start worm -> AUG_WHEEL 16T -> AUG_SHAFT.
# Rotation signs: one external helical mesh reverses the M1 input, while
# open chains preserve it. At the 58 rpm reference, the S2 eccentric and
# worm shaft run at -43.5 rpm; the 8:1 worm/wheel drives the RH auger at
# -5.4375 rpm about +X, conveying +x.
CHAIN_P = dict(p1=(308.56946468906176, 280.0), p2=(362.0, 374.5),
               z1=12, z2=12, links=35, y0=381.0)
WORM_WHEEL_RATIO = WORM_STARTS_RATIO = 2.0 / 16.0   # worm starts / wheel teeth
AUGER_REDUCED_RPM = -58.0 * (15.0 / 40.0) * (24.0 / 12.0) * WORM_WHEEL_RATIO


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
    """Kinematic chain from the VP1 Stage 4 layout (teeth counts only).
    M1 -> DRV-CPL12 (1:1) -> 15T/40T helical mesh -> jackshaft; chain A 24/24
    -> S1 shaft A; S1-SYNC 30T/30T external mesh -> shaft B counter-rotates;
    jackshaft 24T -> chain B -> 12T -> S2 input; S2 cycloid q=8 -> phi=-theta/8."""
    gear_ratio = 15.0 / 40.0
    chain_a = 24.0 / 24.0
    chain_b = 24.0 / 12.0
    jack = -input_rpm * gear_ratio
    s1a = jack * chain_a
    s2_ecc = jack * chain_b
    auger = s2_ecc * WORM_WHEEL_RATIO
    return {
        "input_rpm": input_rpm,
        "jackshaft_rpm": jack,
        "s1_shaft_A_rpm": s1a,
        "s1_shaft_B_rpm": -s1a,
        "s2_input_rpm": s2_ecc,
        "s2_output_rpm": -s2_ecc / 8.0,
        "s2_ecc_rpm": s2_ecc,
        "worm_shaft_rpm": s2_ecc,
        "auger_rpm": auger,
        "auger_conveying_pitch_mm": 28.5,
    }
