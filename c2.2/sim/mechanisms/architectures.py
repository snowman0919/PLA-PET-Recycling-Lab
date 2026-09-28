"""I4 mechanism architecture library (Isaac-independent, numpy-free).

7 variants: S1-A/B/C primary shredders, S2-A/B/C/D secondary units.
S1-A inherits C1/C2 params (tip80/root46/shaft25/centers60 from
design/parameters.json). S2-A inherits C2.1 Transmission nominal
(q=8, e=7, +120/-15rpm, phi=-theta/q). S2-B conventional rotor-stator
granulator baseline MUST exist (comparison anchor).

No motor selection anywhere: drive envelope is a generic mechanical
torque/rpm cap (ASSUMPTION). Evidence UNCALIBRATED_DIGITAL_SENSITIVITY.

Envelope: whole-machine body 630x408x508 mm + S2 local frame
(Z-180deg, translate (308.569,299,280); process zone machine-Y 255..295).
Each variant declares a footprint that must fit the body; S2 variants
must additionally fit the S2 process bay (200 x 44 x 200 mm ASSUMPTION
derived from support-plate outline +/-85mm and 40mm process width + caps).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

EVIDENCE = "UNCALIBRATED_DIGITAL_SENSITIVITY"

BODY_MM = (630.0, 408.0, 508.0)
# S2 process bay: support plate outline x/z +/-85 (build_cad.support_plate),
# process width 40 + caps 0..48, coupling to 64, support from 68.
S2_BAY_MM = (200.0, 140.0, 200.0)

# Generic mechanical drive cap. ASSUMPTION for comparison only.
# NOT a motor rating, NOT a selection.
DRIVE_ENVELOPE = {
    "max_input_torque_Nm": 20.0,
    "max_input_rpm": 200.0,
    "max_input_power_W": 300.0,
    "status": "ASSUMPTION_NO_MOTOR_SELECTION",
}

# Common comparison contract: identical inputs per candidate slot.
COMPARISON_CONTRACT = {
    "seed_set": [7, 11, 23],
    "waste_classes": ["W1", "W2", "W3", "W4"],
    "specimen_mass_policy": "same waste_gen seed+class per slot",
    "duration_policy": "fixed event count per combo (single fracture event)",
    "gravity_m_s2": 9.81,
    "solver_settings": "BondManager fallback, scatter 0.02, SLIP 0.8mm",
    "friction_policy": "waste_gen sampled friction, shared per slot",
    "evidence_level": EVIDENCE,
}


class InvalidMechanism(ValueError):
    """Zero clearance, bad direction sign, missing baseline, bad envelope."""


@dataclass(frozen=True)
class Architecture:
    id: str
    stage: str  # "S1" or "S2"
    name: str
    params: dict
    ranges: dict  # sampleable ranges for screening
    footprint_mm: tuple[float, float, float]
    clearance_mm: float
    direction_sign: int  # rotor/output sense vs input: -1 reverse, +1 same
    baseline: bool = False
    notes: str = ""


def _s1a() -> Architecture:
    return Architecture(
        id="S1-A", stage="S1",
        name="twin-shaft hook shear (inherited)",
        params={"cutter_tip_mm": 80.0, "cutter_root_mm": 46.0,
                "cutter_thickness_mm": 6.0, "shaft_mm": 25.0,
                "shaft_center_mm": 60.0, "hooks": 7,
                "cutters_per_shaft": 13, "axial_phase_mm": 6.2,
                "end_gap_mm": 0.6, "rpm": 40.0,
                "source": "design/parameters.json S1 block"},
        ranges={"gap_mm": (0.4, 1.2), "rpm": (20.0, 60.0),
                "hooks": (5, 9)},
        footprint_mm=(220.0, 170.0, 120.0),
        clearance_mm=0.6, direction_sign=-1,
        notes="counter-rotating twin shafts; inherited C1/C2 geometry")


def _s1b() -> Architecture:
    return Architecture(
        id="S1-B", stage="S1",
        name="single toothed rotor + fixed breaker",
        params={"rotor_tip_mm": 80.0, "teeth": 12, "shaft_mm": 25.0,
                "breaker_gap_mm": 0.8, "rpm": 60.0},
        ranges={"gap_mm": (0.4, 1.2), "rpm": (30.0, 120.0),
                "teeth": (8, 18)},
        footprint_mm=(200.0, 160.0, 120.0),
        clearance_mm=0.8, direction_sign=+1,
        notes="one driven rotor against fixed breaker plate")


def _s1c() -> Architecture:
    return Architecture(
        id="S1-C", stage="S1",
        name="opposed compression/shear rollers",
        params={"roller_dia_mm": 70.0, "nip_gap_mm": 1.0,
                "rpm": 30.0, "surface": "toothed"},
        ranges={"gap_mm": (0.4, 1.2), "rpm": (15.0, 60.0),
                "roller_dia_mm": (50.0, 90.0)},
        footprint_mm=(200.0, 150.0, 110.0),
        clearance_mm=1.0, direction_sign=-1,
        notes="co-rotating pair with nip; fines crushing bias")


def _s2a() -> Architecture:
    return Architecture(
        id="S2-A", stage="S2",
        name="cycloidal fixed-ring (inherited C2.1)",
        params={"q": 8, "eccentric_mm": 7.0, "input_rpm": 120.0,
                "output_rpm": -15.0, "rotor_tip_mm": 110.0,
                "chamber_mm": 125.6, "process_width_mm": 40.0,
                "radial_gap_mm": 0.8, "screen_hole_mm": 4.0,
                "screen_thickness_mm": 2.0, "screen_arc_deg": 100.0,
                "law": "phi=-theta/q",
                "source": "c2.1/src/transmission.py Transmission"},
        ranges={"gap_mm": (0.4, 1.2), "screen_mm": (3.0, 5.5),
                "eccentric_mm": (5.0, 9.0), "q": (6, 12),
                "input_rpm": (60.0, 180.0)},
        footprint_mm=(190.0, 130.0, 190.0),
        clearance_mm=0.8, direction_sign=-1,
        notes="shared-M1 single DOF; output reverse -1/q")
def _s2b() -> Architecture:
    return Architecture(
        id="S2-B", stage="S2",
        name="conventional rotor-stator granulator (baseline)",
        params={"rotor_tip_mm": 100.0, "chamber_mm": 102.0,
                "radial_gap_mm": 1.0, "blades": 3,
                "screen_hole_mm": 4.0, "screen_thickness_mm": 2.0,
                "screen_arc_deg": 120.0, "rpm": 300.0},
        ranges={"gap_mm": (0.4, 1.2), "screen_mm": (3.0, 5.5),
                "rpm": (150.0, 500.0), "blades": (2, 5)},
        footprint_mm=(170.0, 120.0, 170.0),
        clearance_mm=1.0, direction_sign=+1,
        baseline=True,
        notes="industry-standard high-speed granulator; comparison anchor")

def _s2c() -> Architecture:
    return Architecture(
        id="S2-C", stage="S2",
        name="eccentric jaw/shear hybrid",
        params={"jaw_throw_mm": 6.0, "nip_gap_mm": 0.8,
                "strokes_per_min": 240.0, "screen_hole_mm": 4.0},
        ranges={"gap_mm": (0.4, 1.2), "screen_mm": (3.0, 5.5),
                "jaw_throw_mm": (3.0, 9.0),
                "strokes_per_min": (120.0, 360.0)},
        footprint_mm=(160.0, 120.0, 160.0),
        clearance_mm=0.8, direction_sign=+1,
        notes="low-speed high-force eccentric jaw with shear edge")


def _s2d() -> Architecture:
    return Architecture(
        id="S2-D", stage="S2",
        name="opposed disk differential shear",
        params={"disk_dia_mm": 120.0, "disk_gap_mm": 0.8,
                "rpm_a": 120.0, "rpm_b": -90.0,
                "screen_hole_mm": 4.0},
        ranges={"gap_mm": (0.4, 1.2), "screen_mm": (3.0, 5.5),
                "disk_dia_mm": (90.0, 150.0), "rpm_a": (60.0, 180.0)},
        footprint_mm=(170.0, 120.0, 170.0),
        clearance_mm=0.8, direction_sign=-1,
        notes="counter-rotating disks; differential shear in the gap")


ARCHITECTURES: dict[str, Architecture] = {
    a.id: a for a in (_s1a(), _s1b(), _s1c(), _s2a(), _s2b(), _s2c(), _s2d())
}


def get(arch_id: str) -> Architecture:
    try:
        return ARCHITECTURES[arch_id]
    except KeyError:
        raise InvalidMechanism(f"unknown architecture {arch_id!r}") from None


def s2a_direction_phi(theta: float, q: int = 8) -> float:
    """S2-A law: phi = -theta/q (reverse, sign -1)."""
    return -theta / q


def check_envelope(arch: Architecture) -> None:
    for got, lim, ax in zip(arch.footprint_mm, BODY_MM, "XYZ"):
        if got > lim:
            raise InvalidMechanism(
                f"{arch.id} footprint {arch.footprint_mm} exceeds body "
                f"{BODY_MM} on {ax}")
    if arch.stage == "S2":
        for got, lim, ax in zip(arch.footprint_mm, S2_BAY_MM, "XYZ"):
            if got > lim:
                raise InvalidMechanism(
                    f"{arch.id} footprint {arch.footprint_mm} exceeds S2 bay "
                    f"{S2_BAY_MM} on {ax}")


def check_clearance(arch: Architecture, gap_mm: float | None = None) -> None:
    g = arch.clearance_mm if gap_mm is None else gap_mm
    if not math.isfinite(g) or g <= 0:
        raise InvalidMechanism(f"{arch.id}: zero/non-finite clearance {g}")


def check_direction(arch: Architecture) -> None:
    if arch.id == "S2-A" and arch.direction_sign != -1:
        raise InvalidMechanism("S2-A must be reverse (phi=-theta/q, sign -1)")


def check_baseline_present() -> None:
    if "S2-B" not in ARCHITECTURES or not ARCHITECTURES["S2-B"].baseline:
        raise InvalidMechanism("S2-B conventional baseline missing")


def validate(arch: Architecture) -> None:
    check_envelope(arch)
    check_clearance(arch)
    check_direction(arch)


def validate_all() -> None:
    check_baseline_present()
    for a in ARCHITECTURES.values():
        validate(a)


def comparison_contract() -> dict:
    return dict(COMPARISON_CONTRACT)


def screen_open_area(screen_hole_mm: float, screen_thickness_mm: float = 2.0,
                     arc_deg: float = 100.0) -> float:
    """Open-area fraction proxy: hole pitch ~ 2x diameter triangular grid.

    Returns open fraction in [0,1]. Purely geometric; NOT a throughput claim.
    """
    if screen_hole_mm <= 0 or screen_thickness_mm <= 0:
        raise InvalidMechanism(f"bad screen dims {screen_hole_mm}")
    pitch = 2.0 * screen_hole_mm
    hole = math.pi * (screen_hole_mm / 2.0) ** 2
    cell = (math.sqrt(3) / 2.0) * pitch ** 2
    return (hole / cell) * (arc_deg / 360.0)
