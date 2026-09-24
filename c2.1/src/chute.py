"""VP1 Stage 1: real transfer chute from the S1 discharge opening to the
C2.1 S2 feed mouth, in absolute machine coordinates (new parts, group "feed").

Current interface datums (measured from the assembled geometry):
- S1 containment interior: x 83..237, y 162.4..324.6, bottom plane z=352.3
  (S1-WALL 160x5x92 at (80,157.4/324.6,352.3); S1-SIDE strips x 80..83 and
  237..240; shafts z=398.30275184708404, cutter sweep bottom z=358.3).
- S2 axis (308.56946468906176, z=280) via c2.1/design/machine_integration.json
  c2_subassembly_transform (180deg about Z + translation).
- S2 feed mouth: the only open arc of the chamber wall, global angles
  20.0..99.5 deg (measured by ray classification of the C2 STEP parts at
  r=64: shell-R2 covers 99.5..176, shell-R1+shear 176..220, screen
  220..320, shell-L 320..20). Chamber shells span y 255..295, r 62.8..65.8;
  outer apex z=345.8. End caps (r 65.6..76.5) occupy y 251..255 and
  295..299, so the chute throat must run inside y 255..295.
- The small S1-to-S2 elevation drop cannot supply a continuous passive
  gravity slide. The longitudinal auger delivers to a powered orthogonal
  cross-feed screw; its reduced-radius flight overlaps the S2 mouth axially
  without crossing the rotor coupling envelope. This is a geometric handoff
  opportunity, not proof of fragment transfer. S1 pickup also remains
  unverified.

Parts (group "feed"): CHUTE_BODY, CHUTE_TROUGH_FLOOR_E, the PDL worm drive,
AUG_SHAFT/BEARINGS/WHEEL, and CROSS_FEED_SHAFT/IDLER/gears/bearings/shell.
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

V = cq.Vector

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]

S1 = dict(x0=83.0, x1=237.0, y0=162.4, y1=324.6, bottom=352.3,
          wall_y0=157.4, wall_y1=329.6, strip_x0=80.0, strip_x1=240.0)
S2_AX, S2_AZ = 308.56946468906176, 280.0
SHELL_RO = 65.8            # chamber shell outer radius (apex z=345.8)
MOUTH_LO, MOUTH_HI = 20.0, 99.5   # open arc, global degrees
PAN_Z0, PAN_Z1 = 344.5, 348.0   # pan/trough-west floor: 4.3 mm entry under S1 bottom
TROUGH_Z0, TROUGH_Z1 = 347.5, 351.8   # trough-east floor (saddle recess datums)
TROUGH_Y0, TROUGH_Y1 = 255.0, 295.0   # chamber width band (end-cap faces)
WALL_TOP = 352.3                      # flush with the S1 bottom plane
SADDLE_STEP = "c2/cad/C2_THERMAL_SADDLE_R.step"

SLOPE_STEP_DZ = 1.5
SLOPE_MIN_DEG = 30.0

# Screw conveyor: four complete right-hand turns over the pickup-to-discharge
# span. The cross-section has a 3 mm axial face; the U shell follows the actual
# swept corner radius, not the nominal helix-center radius.
AUG_AX_Y, AUG_AX_Z = 232.0, 347.1
AUG_SHAFT_R = 3.0
AUG_FLIGHT_RO = 8.0
AUG_FLIGHT_PITCH = 28.5
AUG_FLIGHT_X0, AUG_FLIGHT_X1 = 237.0, 354.0
AUG_FLOOR_TOP, AUG_FLOOR_BASE = 335.6, 334.5
AUG_SEAT_TOP = 335.6
WORM_CX, WORM_CZ = 362.0, 374.5
WORM_SHAFT_X0, WORM_SHAFT_X1 = 208.0, 370.0
WORM_ROOT_R, WORM_PITCH_R, WORM_OD_R = 6.0, 6.75, 7.5
WORM_STARTS, WHEEL_TEETH = 2, 16
WHEEL_CD = WORM_CZ - AUG_AX_Z
WHEEL_R_P = WHEEL_CD - WORM_PITCH_R
WHEEL_R_WEB, WHEEL_R_ROOT, WHEEL_R_TIP = (
    WHEEL_R_P - 6.25, WHEEL_R_P - 1.75, WHEEL_R_P + 0.25)
WHEEL_WEB_R0 = 4.0
AUG_WHEEL_X0, AUG_WHEEL_X1 = 359.0, 365.0
WORM_LEAD = WORM_STARTS * 2.0 * math.pi * (30.0 - WORM_PITCH_R) / WHEEL_TEETH
WORM_LEAD_DEG = math.degrees(math.atan(WORM_LEAD / (2.0 * math.pi * WORM_PITCH_R)))
# At the rated 58 rpm M1 input: jackshaft 15/40, S2Ecc 24/12,
# then the 2-start/16T worm reduction. This is a reference speed, not a
# connected-flow guarantee or a motor torque rating.
AUG_RPM_ABS = 58.0 * (15.0 / 40.0) * (24.0 / 12.0) * WORM_STARTS / WHEEL_TEETH

# Orthogonal screw remains driven from the PDL shaft. Its 10 mm-radius
# receiving flight narrows before the swept S2 coupling web, then a 5 mm
# flight continues across the south mouth. The fixed cradle keeps only metal
# outside the rotor's radial envelope; neither a rotor contact nor an
# unpowered axial bridge is a substitute for the powered tail.
CROSS_X, CROSS_Z = 357.0, 328.0
CROSS_PIVOT_Y = 252.0
CROSS_SHAFT_Y0, CROSS_SHAFT_Y1 = 208.0, 261.0
CROSS_SHAFT_R, CROSS_FLIGHT_RO = 3.0, 10.0
CROSS_FLIGHT_Y0, CROSS_FLIGHT_Y1 = 226.0, 231.35
CROSS_TAIL_RO, CROSS_TAIL_Y1 = 5.0, 259.0
ROTOR_RADIAL_RELIEF_R = 63.5
CROSS_PITCH = 9.0
CROSS_GEAR_Y0, CROSS_GEAR_Y1 = 213.0, 219.0
# Equal 12T spur gears; the middle idler reverses twice in all, so the
# cross-feed screw turns at the PDL shaft's signed +Y rate, not its negative.
FEED_GEAR_TEETH = 12
FEED_GEAR_RP = FEED_GEAR_TEETH / math.cos(math.radians(15.0))
_gear_dx, _gear_dz = CROSS_X - WORM_CX, CROSS_Z - WORM_CZ
_gear_span = math.hypot(_gear_dx, _gear_dz)
_gear_offset = math.sqrt((2.0 * FEED_GEAR_RP)**2 - (_gear_span / 2.0)**2)
IDLER_X = (CROSS_X + WORM_CX) / 2.0 - _gear_dz / _gear_span * _gear_offset
IDLER_Z = (CROSS_Z + WORM_CZ) / 2.0 + _gear_dx / _gear_span * _gear_offset


# S1-wide pickup: a thin endless belt and two bearing-supported drums under
# the cutter envelope. S1B's extended rear shaft drives a 24T:12T #35
# chain at y402..407 behind the rear frame beam; the upper run travels
# +X at 2*|omega_S1B|*3.8 mm/s. Tread friction and ratings remain HOLD.
BELT_WEST_X, BELT_EAST_X, BELT_AX_Z = 80.0, 219.0, 335.2
BELT_EAST_Z = 332.9
BELT_INNER_R, BELT_OUTER_R = 3.8, 4.6

# The cross-screws engage flakes near the east side of the descending
# side treads. Their x200 flights end before the x208 auger-bearing bridge;
# gears remain keyed to the east-drum axle outside the pan rails. The north
# pair sits outboard of both the S1 bearing caps and S2 input support plate.
SWEEP_X, SWEEP_Z = 200.0, 344.7
SWEEP_SHAFT_R, SWEEP_FLIGHT_R, SWEEP_PITCH = 2.0, 6.7, 16.0
SWEEP_GEAR_Y = ((128.0, 134.0), (361.0, 367.0))
SWEEP_GEAR_SCALE = math.hypot(SWEEP_X-BELT_EAST_X,
                              SWEEP_Z-BELT_EAST_Z) / (2.0 * FEED_GEAR_RP)
BELT_Y0, BELT_Y1 = 163.5, 323.5

# The shared west axle is raised to the centre lane's east axis. Its
# Ø4.6 side treads descend 2.3 mm to x219, while the Ø3 central tread
# remains level at z338.2 instead of shedding fragments westward.
TRANSFER_WEST_X, TRANSFER_EAST_X = BELT_WEST_X, 270.0
TRANSFER_WEST_Z, TRANSFER_AX_Z = BELT_AX_Z, 335.2
TRANSFER_INNER_R, TRANSFER_OUTER_R = 2.3, 3.0
TRANSFER_Y0, TRANSFER_Y1 = 223.5, 240.5


def _c21_transform(shape):
    """Apply the frozen c2_subassembly_transform to a c2 local-frame part."""
    return (shape.rotate((0, 0, 0), (0, 0, 1), 180)
                 .translate((308.56946468906176, 299, 280)))


def _obstruction_solid():
    """Frozen S2 jacket solids that pierce the chute floor plane: the
    C2_THERMAL_SADDLE_R (body + six fins) and both C2_SADDLE_CAP_R end caps.
    The floor is cut with this compound so the frozen parts pass through by
    construction (zero-volume contact, collision-free)."""
    # c2_process_part imports with a local +4 y offset (process compartment
    # 4..44 -> global mouth band 255..295)
    s = cq.importers.importStep(str(REPO / SADDLE_STEP)).val().translate((0, 4, 0))
    out = _c21_transform(s)
    for y0 in (0.0, 44.0):
        cap = cq.importers.importStep(
            str(REPO / "c2/cad/C2_SADDLE_CAP_R.step")).val().translate((0, y0, 0))
        out = out.fuse(_c21_transform(cap))
    return out


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _prism_xz(points, y0, depth):
    wire = cq.Wire.makePolygon([V(x, y0, z) for x, z in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, depth, 0)).clean()

def _prism_yz(points, x0, width):
    wire = cq.Wire.makePolygon([V(x0, y, z) for y, z in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(width, 0, 0)).clean()


def _prism_xy(points, z0, height):
    wire = cq.Wire.makePolygon([V(x, y, z0) for x, y in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, 0, height)).clean()


def pan_floor():
    """S1 discharge basin with a recessed, supported belt pocket."""
    pts = [(S1["x0"], PAN_Z0), (245.5, PAN_Z0),
           (245.5, 344.5), (S1["x0"], PAN_Z1)]
    full = _prism_xz(pts, S1["wall_y0"] + 2.0,
                     326.5 - S1["wall_y0"] - 2.0)
    full = full.cut(_box(239.0, 245.5, 224.0, 240.0,
                         PAN_Z0 - 0.5, PAN_Z1 + 0.5))
    full = full.cut(_box(232.0, 246.0, 229.0, 235.0,
                         PAN_Z0 - 0.5, PAN_Z1 + 0.5))
    south = _box(244.0, 271.5, S1["wall_y0"] + 2.0, 201.0,
                 PAN_Z0, PAN_Z1)
    north_a = _box(244.0, 271.5, 213.0, 297.5, PAN_Z0, PAN_Z1)
    north_b = _box(244.0, 271.5, 307.5, 326.5, PAN_Z0, PAN_Z1)
    north_a = north_a.cut(_box(244.0, 271.5, 213.0, 248.5,
                               PAN_Z0 - 0.5, PAN_Z1 + 0.5))
    north_a = north_a.cut(_obstruction_solid())
    north_a = north_a.cut(_cyl(5.5, 16.0, 258.0, AUG_AX_Y,
                               AUG_AX_Z, axis=(1, 0, 0)))
    solids = [s for s in north_a.Solids() if s.Volume() > 10.0]
    if len(solids) not in (1, 2, 3):
        raise RuntimeError("pan floor north slab split: %d solids" % len(solids))
    full = full.fuse(south).fuse(*solids).fuse(north_b)
    # A recessed catch floor starts beyond the rounded side-belt tangency.
    # It must sit below the flake underside, not form a vertical stop at
    # the belt exit.
    full = full.cut(_box(75.3, 223.7, 163.4, 323.6, 320.0, 349.0))
    full = full.cut(_box(223.7, 237.0, 163.4, 323.6, 334.0, 349.0))
    full = full.cut(_box(237.0, 245.5, 222.0, 242.0, 334.0, 349.0))
    for y0, y1 in ((157.4, 163.4), (323.6, 329.6)):
        full = full.fuse(_box(74.0, 229.5, y0, y1, 320.0, 352.3))
    for x, z in ((BELT_WEST_X, BELT_AX_Z),
                 (BELT_EAST_X, BELT_EAST_Z)):
        for y0, y1 in ((157.4, 163.4), (323.6, 329.6)):
            full = full.cut(_cyl(5.15, y1-y0, x, y0, z))
    for y0, y1 in ((157.4, 163.4), (323.6, 329.6)):
        full = full.cut(_cyl(2.35, y1-y0, SWEEP_X, y0, SWEEP_Z))
    full = full.fuse(_box(76.0, 223.5, 163.4, 323.6, 321.0, 323.0))
    # The side tread falls from z339.8 at the west drum to about z337.8
    # beneath the x200 sweep. Its east landing remains 0.1 mm below the
    # z337.5 end tread and the central powered lane is relieved separately.
    full = full.fuse(_box(223.7, 237.0, 163.4, 323.6, 332.8, 337.4))
    # Curve the side-lane stop around the screw's swept circle. A straight
    # x207.5 gate left a Ø1.5 flake centre at x206.8,z338.2, 9.4 mm
    # from the x200,z344.7 axis and outside the 6.7-mm flight. At tread
    # height the stop now presents the flake to the flight; its upper edge
    # retreats with positive clearance from the rotating envelope.
    stop_profile = [(202.5, 338.1), (202.9, 338.2),
                    (204.2, 339.0), (205.4, 340.0),
                    (206.2, 341.0), (206.7, 342.0),
                    (207.0, 343.0), (207.3, 344.7),
                    (207.5, 352.0), (209.0, 352.0),
                    (209.0, 338.1)]
    for y0, y1 in ((163.3, 222.0), (242.0, 323.8)):
        full = full.fuse(_prism_xz(stop_profile, y0, y1-y0))
    # Preserve the rear support's metal volume below the south shelf.
    full = full.cut(_box(236.0, 237.0, 203.0, 211.0, 332.7, 334.1))
    # Keep side-lane flakes under the transverse flights until they reach
    # the central opening; otherwise the belt leaves them east of the screw.
    for y0, y1 in ((163.4, 220.5), (243.5, 323.6)):
        full = full.fuse(_box(235.3, 236.0, y0, y1, 334.0, 340.0))
    for y0, y1 in ((163.4, 222.0), (242.0, 323.6)):
        full = full.fuse(_box(236.0, 237.4, y0, y1,
                              334.0, WALL_TOP))
    # Keep these bearing-support cheeks below the underside of even a
    # Ø1.5 flake on the side drum; a z334.2 cheek trapped flakes at y243.
    # The x222.5 web below them still connects the metal support to the pan.
    full = full.cut(_box(222.5, 240.0, 223.2, 240.8, 328.5, 340.0))
    full = full.fuse(_box(224.0, 240.0, 221.0, 223.2, 327.0, 333.0))
    full = full.fuse(_box(224.0, 240.0, 240.8, 243.0, 327.0, 333.0))
    full = full.fuse(_box(224.0, 240.0, 223.2, 240.8, 326.0, 327.5))
    # Two narrow underside webs tie the lowered idler cheeks to the
    # existing full-width bottom plate without a wall above the treads.
    for y0, y1 in ((221.0, 223.2), (240.8, 243.0)):
        full = full.fuse(_box(222.5, 224.1, y0, y1, 322.0, 327.2))
    return full.clean()

def _wedge_rib(x, y0, y1, zbase=PAN_Z1, height=4.0, half=8.0):
    """Historical ratchet rib retained for inspection, not installed."""
    ztip = min(zbase + height, WALL_TOP - 0.5)
    return _prism_xz([(x - half, zbase - 2.0), (x, ztip),
                      (x, zbase - 2.0)], y0, y1 - y0).clean()


BAYS = [(250.5, 348.0), (265.5, 345.5), (280.0, 343.5),
        (295.0, 341.5), (310.0, 341.5), (325.0, 340.5),
        (340.0, 338.5), (350.0, 338.5)]


def transport_ribs():
    """No stationary ribs in the screw pickup or flight zone."""
    return None


def _transport_ribs_removed():
    """Historical pan-only ribs, superseded by the active transfer design."""
    ribs = None
    for x in (120.0, 150.0, 180.0, 210.0):
        zb = 348.0 - (x - S1["x0"]) * 3.5 / (245.5 - S1["x0"])
        rib = _wedge_rib(x, S1["wall_y0"] + 2.0, 326.5,
                         zbase=zb, height=4.0, half=8.0)
        ribs = rib if ribs is None else ribs.fuse(rib)
    return ribs.clean()


def bypass_channel_floor():
    """Longitudinal U cradle, opened locally into the powered cross pickup.

    The old x354..360.5 passive fallaway and y238..280 ramp are removed;
    they could not impart motion along +Y. The rotor-clearance cut continues
    into the last 9 mm of the auger cradle, where fragments change axes.
    """
    slab = _box(AUG_FLIGHT_X0, 354.0, 213.0, 251.0,
                AUG_FLOOR_BASE, AUG_FLOOR_TOP)
    shell = _box(AUG_FLIGHT_X0, 354.0, 223.3, 240.9,
                 AUG_FLOOR_TOP, AUG_AX_Z)
    inner = _cyl(9.5, AUG_FLIGHT_X1 - AUG_FLIGHT_X0,
                 AUG_FLIGHT_X0, AUG_AX_Y, AUG_AX_Z, axis=(1, 0, 0))
    shell = shell.cut(inner)
    cross_clearance = _cyl(10.55, 27.5, CROSS_X, 223.5, CROSS_Z)
    # The central tread continues into the first auger turn without entering
    # the S2 rotor's moving coupling-web envelope. Its exit recess begins
    # beyond the drum so fragments can enter the screw flight.
    entrance = _box(237.0, TRANSFER_EAST_X + TRANSFER_OUTER_R,
                    223.2, 240.8, 331.0, 351.0)
    exit_recess = _box(TRANSFER_EAST_X + TRANSFER_OUTER_R,
                       TRANSFER_EAST_X + TRANSFER_OUTER_R + 8.0,
                       223.2, 240.8, 337.5, 351.0)
    cradle = slab.fuse(shell).cut(cross_clearance).cut(entrance).cut(
        exit_recess)
    # Carry the tread's z338.2 landing onto a steel wear shelf at z337.7.
    # The previous z337.5 recess dropped small flakes below the auger's
    # lowest flight; the original slab beyond x281 was lower still (335.6).
    # Keep the shelf south of y235 where the S2 coupling web sweeps.
    cradle = cradle.fuse(_box(TRANSFER_EAST_X + TRANSFER_OUTER_R,
                              340.0, 223.2, 234.8,
                              AUG_FLOOR_BASE, 337.7))
    # Descend from the auger shelf into the orthogonal flight's receiving
    # quadrant. Cut the 10.55 mm swept envelope out of the fixed ramp.
    ramp = _prism_xz([(340.0, AUG_FLOOR_BASE), (340.0, 337.7),
                      (347.0, 333.0), (347.0, 331.0)],
                     223.2, 11.6).cut(cross_clearance)
    cradle = cradle.fuse(ramp)
    # The auger floor otherwise holds a flake at z339 beyond this ramp:
    # open the last seven millimetres above the powered receiving flight.
    # Retain the outer shell walls and the cross-feed's own U cradle.
    cradle = cradle.cut(_box(347.0, 354.0, 223.2, 240.9,
                             330.0, 341.0))
    x, z = TRANSFER_EAST_X, TRANSFER_AX_Z
    cradle = cradle.cut(_cyl(1.15, 36.0, x, 214.0, z))
    for y0, y1 in ((218.0, 223.2), (240.8, 246.0)):
        cradle = cradle.cut(_cyl(1.65, y1-y0, x, y0, z))
    return cradle.clean()

def bypass_wall_south():
    """South containment, relieved only at the low-y spur-gear face."""
    wall = _box(237.0, 360.0, 213.0, 223.3, AUG_FLOOR_BASE, 356.3)
    return wall.cut(_box(341.0, 384.0, 212.9, 219.2, 313.0, 390.0)).clean()


def bypass_wall_north_lower():
    """North containment ends before the orthogonal screw's west cheek."""
    return _box(237.0, 344.0, 240.9, 251.0, AUG_FLOOR_BASE, 353.5)




def intake_lip():
    """45deg intake lip under the S1 -X side strip (the opening's west edge);
    all other opening edges seal flush under the S1 walls/strips."""
    pts = [(S1["strip_x0"], S1["bottom"]), (87.5, 344.8), (87.5, S1["bottom"])]
    return _prism_xz(pts, S1["wall_y0"] + 2.0, S1["wall_y1"] - S1["wall_y0"] - 4.0)


def _guide(p0, p1):
    """Stationary funnel wall clears the moving belt tread by 0.2 mm."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * 1.5, dx / L * 1.5
    pts = [p0, p1, (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)]
    return _prism_xy(pts, 336.2, WALL_TOP - 336.2)


def guide_left():
    """Central lane wall; transverse screw supplies lateral transport."""
    return _box(237.0, 245.0, 221.5, 223.5, 336.2, WALL_TOP)


def guide_right():
    return _box(237.0, 245.0, 240.9, 242.5, 336.2, WALL_TOP)

def belt_loop():
    """Two side loops leave a continuous, separately driven central lane."""
    dx = BELT_EAST_X - BELT_WEST_X
    dz = BELT_EAST_Z - BELT_AX_Z
    length = math.hypot(dx, dz)
    nx, nz = -dz / length, dx / length
    angle = math.atan2(nz, nx)

    def capsule(r, y0, y1):
        pts = [(BELT_WEST_X + r*nx, BELT_AX_Z + r*nz),
               (BELT_EAST_X + r*nx, BELT_EAST_Z + r*nz)]
        pts += [(BELT_EAST_X + r*math.cos(angle - math.pi*i/32),
                 BELT_EAST_Z + r*math.sin(angle - math.pi*i/32))
                for i in range(1, 33)]
        pts.append((BELT_WEST_X - r*nx, BELT_AX_Z - r*nz))
        pts += [(BELT_WEST_X + r*math.cos(angle - math.pi - math.pi*i/32),
                 BELT_AX_Z + r*math.sin(angle - math.pi - math.pi*i/32))
                for i in range(1, 33)]
        return _prism_xz(pts, y0, y1-y0)
    parts = []
    for y0, y1 in ((BELT_Y0, 223.2), (240.8, BELT_Y1)):
        parts.append(capsule(BELT_OUTER_R, y0, y1).cut(
            capsule(BELT_INNER_R + 0.03, y0, y1)).clean())
    return cq.Compound.makeCompound(parts)


def transfer_belt():
    """Level central lane on the common M1 drum, running beneath AUG."""
    dx = TRANSFER_EAST_X - TRANSFER_WEST_X
    dz = TRANSFER_AX_Z - TRANSFER_WEST_Z
    length = math.hypot(dx, dz)
    nx, nz = -dz/length, dx/length
    angle = math.atan2(nz, nx)

    def capsule(r):
        pts = [(TRANSFER_WEST_X + r*nx, TRANSFER_WEST_Z + r*nz),
               (TRANSFER_EAST_X + r*nx, TRANSFER_AX_Z + r*nz)]
        pts += [(TRANSFER_EAST_X + r*math.cos(angle - math.pi*i/32),
                 TRANSFER_AX_Z + r*math.sin(angle - math.pi*i/32))
                for i in range(1, 33)]
        pts.append((TRANSFER_WEST_X - r*nx, TRANSFER_WEST_Z - r*nz))
        pts += [(TRANSFER_WEST_X + r*math.cos(angle - math.pi - math.pi*i/32),
                 TRANSFER_WEST_Z + r*math.sin(angle - math.pi - math.pi*i/32))
                for i in range(1, 33)]
        return _prism_xz(pts, TRANSFER_Y0, TRANSFER_Y1 - TRANSFER_Y0)
    return capsule(TRANSFER_OUTER_R).cut(
        capsule(TRANSFER_INNER_R + 0.03)).clean()


def transfer_idler():
    """Captured east drum; the west driver is the waisted S1_BELT_DRIVE."""
    x, z = TRANSFER_EAST_X, TRANSFER_AX_Z
    drum = _cyl(TRANSFER_INNER_R, TRANSFER_Y1-TRANSFER_Y0,
                x, TRANSFER_Y0, z)
    return drum.fuse(_cyl(1.0, 36.0, x, 214.0, z)).clean()


def transfer_bearings():
    parts = []
    x, z = TRANSFER_EAST_X, TRANSFER_AX_Z
    for y0, y1 in ((218.0, 223.2), (240.8, 246.0)):
        ring = _cyl(1.55, y1-y0, x, y0, z)
        parts.append(ring.cut(_cyl(1.15, y1-y0+0.2, x, y0-0.1,
                                   z)))
    return cq.Compound.makeCompound(parts)

def belt_drum(x, driven=False):
    """Common waisted west driver; two independent east side followers."""
    if x == BELT_EAST_X:
        halves = []
        for (drum_y0, drum_y1), (shaft_y0, shaft_y1), gy in zip(
                ((BELT_Y0, 223.2), (240.8, BELT_Y1)),
                ((127.0, 223.2), (240.8, 369.0)), SWEEP_GEAR_Y):
            half = _cyl(BELT_INNER_R, drum_y1-drum_y0,
                        x, drum_y0, BELT_EAST_Z)
            half = half.fuse(_cyl(2.0, shaft_y1-shaft_y0, x,
                                  shaft_y0, BELT_EAST_Z))
            half = half.fuse(_box(x+1.9, x+2.45, gy[0], gy[1],
                                  BELT_EAST_Z-0.5, BELT_EAST_Z+0.5))
            halves.append(half.clean())
        return cq.Compound.makeCompound(halves)
    drum = _cyl(BELT_INNER_R, BELT_Y1-BELT_Y0, x, BELT_Y0, BELT_AX_Z)
    # The central 17 mm loop seats on a smaller common drive waist.
    drum = drum.cut(_cyl(BELT_INNER_R+0.1, 17.6, x, 223.2,
                         BELT_AX_Z))
    drum = drum.fuse(_cyl(TRANSFER_INNER_R, 17.6, x, 223.2,
                          BELT_AX_Z))
    drum = drum.fuse(_cyl(2.0, 359.0-127.0, x, 127.0, BELT_AX_Z))
    if driven:
        drum = drum.fuse(_cyl(6.0, 82.0, x, 331.0, BELT_AX_Z))
        drum = drum.fuse(_box(x+5.8, x+7.0, 401.0, 409.0,
                              BELT_AX_Z-1.0, BELT_AX_Z+1.0))
    return drum.clean()


def belt_bearings():
    """Four separable bearings seated in the pan's metal side rails."""
    parts = []
    for x, z in ((BELT_WEST_X, BELT_AX_Z),
                 (BELT_EAST_X, BELT_EAST_Z)):
        for y0, y1 in ((157.4, 163.4), (323.6, 329.6)):
            ring = _cyl(5.0, y1-y0, x, y0, z)
            parts.append(ring.cut(_cyl(2.2, y1-y0+0.2, x, y0-0.1,
                                       z)))
    return cq.Compound.makeCompound(parts)

def sweep_shaft(south):
    """Split shaft with a swept, opposite-hand screw and keyed spur."""
    y0, y1 = (127.0, 228.5) if south else (235.5, 369.0)
    flight0, flight1 = (164.5, 226.0) if south else (236.0, 321.5)
    shaft = _cyl(SWEEP_SHAFT_R, y1-y0, SWEEP_X, y0, SWEEP_Z)
    gy0, gy1 = SWEEP_GEAR_Y[0 if south else 1]
    shaft = shaft.fuse(_box(SWEEP_X+1.9, SWEEP_X+2.45,
                            gy0, gy1, SWEEP_Z-0.5, SWEEP_Z+0.5))
    # East drum rotates +Y to convey +X; an external gear reverses the
    # feeder. RH under -Y advances +Y, LH advances -Y.
    path = _helix_z((SWEEP_SHAFT_R+SWEEP_FLIGHT_R)/2,
                    SWEEP_PITCH, flight1-flight0,
                    (0, 0, flight0), lefthand=not south)
    path = path.rotate(V(0, 0, 0), V(1, 0, 0), -90).translate(
        V(SWEEP_X, 0, SWEEP_Z))
    p0, tangent = _path_frame(path)
    radial = V(p0.x-SWEEP_X, 0, p0.z-SWEEP_Z).normalized()
    axial = tangent.cross(radial).normalized()
    if axial.dot(V(0, 1, 0)) < 0:
        axial *= -1
    half_rad = (SWEEP_FLIGHT_R-SWEEP_SHAFT_R)/2
    profile = [p0+radial*-half_rad+axial*-0.8,
               p0+radial*half_rad+axial*-0.8,
               p0+radial*half_rad+axial*0.8,
               p0+radial*-half_rad+axial*0.8]
    return shaft.fuse(_sweep_profile(path, profile)).clean()


def sweep_gear(south, on_drum):
    """One small-module 12T spur keyed to the east drum or feeder axle."""
    import drive_teeth as dt
    y0, y1 = SWEEP_GEAR_Y[0 if south else 1]
    cx, cz = ((BELT_EAST_X, BELT_EAST_Z) if on_drum
              else (SWEEP_X, SWEEP_Z))
    mesh_angle = math.degrees(math.atan2(SWEEP_Z-BELT_EAST_Z,
                                          SWEEP_X-BELT_EAST_X))
    phase = (mesh_angle + (0.0 if on_drum else 15.0)) % 30.0
    pts = [(cx + x*SWEEP_GEAR_SCALE, cz + z*SWEEP_GEAR_SCALE)
           for x, z in dt._gear_profile_xy(12, phase_deg=phase)]
    face = _prism_xz(pts, y0, y1-y0)
    bore = 2.0
    gear = face.cut(_cyl(bore, y1-y0+0.2, cx, y0-0.1, cz))
    return gear.cut(_box(cx+1.9, cx+2.55, y0-0.1, y1+0.1,
                         cz-0.55, cz+0.55)).clean()


def sweep_bearings():
    rings = []
    for y0, y1 in ((157.4, 163.4), (323.6, 329.6)):
        ring = _cyl(2.35, y1-y0, SWEEP_X, y0, SWEEP_Z)
        rings.append(ring.cut(_cyl(2.15, y1-y0+0.2,
                                   SWEEP_X, y0-0.1, SWEEP_Z)))
    return cq.Compound.makeCompound(rings)


def belt_follower_sprocket():
    import drive_teeth as dt
    return dt._sprocket_local_solid("DRV-SP12-B12", hub_len=1.0).translate(
        (BELT_WEST_X, 401.0, BELT_AX_Z)).clean()


def belt_chain():
    import drive_teeth as dt
    return dt._chain_loop(dict(p1=(190.0, 398.30275184708404),
                               p2=(BELT_WEST_X, BELT_AX_Z),
                               z1=24, z2=12, y0=402.0))


def wall_front():
    """Sealed under the S1 front wall bottom face (y 157.4..162.4)."""
    return _box(S1["x0"], 248.0, S1["wall_y0"], S1["wall_y0"] + 5.0,
                PAN_Z0, WALL_TOP)


def wall_rear():
    """Sealed under the S1 rear wall bottom face (y 324.6..329.6)."""
    return _box(S1["x0"], 248.0, S1["wall_y1"] - 5.0, S1["wall_y1"],
                PAN_Z0, WALL_TOP)


def trough_floor():
    """Landing ledge over the mouth (x 278.5..310, y 255..295); cut where the
    frozen C2_THERMAL_SADDLE_R body pierces the slab.  Its top stays 0.6 mm
    below the ledge surface, so the jacket forms a smooth local recess."""
    slab = _box(278.5, 310.0, TROUGH_Y0, TROUGH_Y1, TROUGH_Z0, TROUGH_Z1)
    cut = slab.cut(_obstruction_solid())
    solids = [x for x in cut.Solids() if x.Volume() > 10.0]
    if len(solids) != 1:
        raise RuntimeError("trough_floor split: %d solids" % len(solids))
    return solids[0].clean()


def _cyl(r, h, x, y, z, axis=(0, 1, 0)):
    return cq.Solid.makeCylinder(r, h, V(x, y, z), V(*axis))


def _helix_z(radius, pitch, length, center, lefthand=False):
    return cq.Wire.makeHelix(pitch, length, radius, V(*center),
                             V(0, 0, 1), 360.0, lefthand)


def _path_frame(path):
    """Point and unit tangent at the initial vertex of a swept helix."""
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    adaptor = BRepAdaptor_Curve(path.Edges()[0].wrapped)
    first = adaptor.FirstParameter()
    p = adaptor.Value(first)
    tangent = adaptor.DN(first, 1)
    return V(p.X(), p.Y(), p.Z()), V(
        tangent.X(), tangent.Y(), tangent.Z()).normalized()


def _sweep_profile(path, pts3):
    profile = cq.Wire.makePolygon(pts3, close=True)
    face = cq.Face.makeFromWires(profile)
    return (cq.Workplane("XY").newObject([face])
            .sweep(cq.Workplane("XY").newObject([path]),
                   isFrenet=False).val())


def _helix_about_y(radius, lead, y0, y1, cx, cz, y_bottom_phase=None):
    """Right-hand helix advancing along +Y with a specified bottom phase."""
    if y_bottom_phase is not None:
        y0 = y_bottom_phase - lead / 4.0
    helix = cq.Wire.makeHelix(lead, y1 - y0, radius,
                              V(cx, -cz, y0), V(0, 0, 1), 360.0, False)
    return helix.rotate(V(0, 0, 0), V(1, 0, 0), -90)


def worm_shaft():
    """One shaft: worm, cross-drive key, and keyed 12 mm chain shoulder."""
    shaft = _cyl(5.0, 188.0, WORM_CX, 204.0, WORM_CZ)
    feed_key = _box(WORM_CX + 4.8, WORM_CX + 6.0,
                    CROSS_GEAR_Y0, CROSS_GEAR_Y1,
                    WORM_CZ - 1.0, WORM_CZ + 1.0)
    shoulder = _cyl(6.0, 16.0, WORM_CX, 376.0, WORM_CZ)
    chain_key = _box(WORM_CX + 5.8, WORM_CX + 7.0,
                     376.0, 390.0, WORM_CZ - 0.9, WORM_CZ + 0.9)
    worm_key = _box(WORM_CX + 4.8, WORM_CX + 6.0,
                    220.0, 240.0, WORM_CZ - 0.9, WORM_CZ + 0.9)
    return shaft.fuse(feed_key).fuse(worm_key).fuse(shoulder).fuse(chain_key).clean()


def worm_bearings():
    """Two separated supports on the C2.1 support-plate bosses."""
    south = _box(353.0, 365.0, 204.0, 210.0, 365.0, 388.0)
    south = south.cut(_cyl(6.2, 10.0, WORM_CX, 203.0, WORM_CZ)).clean()
    north = _box(353.0, 365.0, 352.0, 358.0, 365.0, 388.0)
    north = north.cut(_cyl(6.2, 10.0, WORM_CX, 351.0, WORM_CZ)).clean()
    return cq.Compound.makeCompound([south, north]).clean()


def worm_sleeve():
    """PDL_WORM: right-hand two-start swept threads keyed to the shaft."""
    blank = _cyl(WORM_ROOT_R, 20.0, WORM_CX, 220.0, WORM_CZ)
    for phase in (232.0 - WORM_LEAD / 4.0,
                  232.0 + WORM_LEAD / 4.0):
        helix = _helix_about_y(WORM_PITCH_R, WORM_LEAD, 220.0, 240.0,
                               WORM_CX, WORM_CZ, y_bottom_phase=phase)
        p0, direction = _path_frame(helix)
        ref = V(1, 0, 0) if abs(direction.dot(V(1, 0, 0))) < 0.9 else V(0, 0, 1)
        u = direction.cross(ref).normalized()
        v = direction.cross(u).normalized()
        radial = V(p0.x - WORM_CX, 0, p0.z - WORM_CZ).normalized()
        if u.dot(radial) < 0:
            u, v = u * -1.0, v * -1.0
        root = p0 + u * -(WORM_PITCH_R - WORM_ROOT_R)
        tip = p0 + u * (WORM_OD_R - WORM_PITCH_R)
        ridge = _sweep_profile(helix, [root + v * -2.5,
                                       root + v * 2.5,
                                       tip + v * 1.1,
                                       tip + v * -1.1])
        blank = blank.fuse(ridge)
    blank = blank.cut(_cyl(5.0, 24.0, WORM_CX, 219.0, WORM_CZ))
    return blank.cut(_box(WORM_CX + 4.8, WORM_CX + 6.1,
                          219.9, 240.1, WORM_CZ - 1.0,
                          WORM_CZ + 1.0)).clean()


def worm_sprocket():
    """12T sprocket keyed onto the shaft's 12 mm shoulder, not a loose bore."""
    import drive_teeth as dt
    sprocket = dt._sprocket_local_solid("DRV-SP12-B12", hub_len=7.0)
    return sprocket.translate((WORM_CX, 376.0, WORM_CZ)).clean()


def worm_chain():
    import drive_teeth as dt
    return dt._chain_loop(dt.CHAIN_P)


def auger_shaft():
    """Single right-hand helicoid with a 3 mm swept flight face."""
    shaft = _cyl(AUG_SHAFT_R, WORM_SHAFT_X1 - WORM_SHAFT_X0,
                 WORM_SHAFT_X0, AUG_AX_Y, AUG_AX_Z, axis=(1, 0, 0))
    # The 114 mm helix has exactly four 28.5 mm turns. Axial half-width
    # extends the swept flight into the x237..354 envelope.
    x0, x1 = AUG_FLIGHT_X0 + 1.5, AUG_FLIGHT_X1 - 1.5
    helix = _helix_z((AUG_SHAFT_R + AUG_FLIGHT_RO) / 2.0,
                     AUG_FLIGHT_PITCH, x1 - x0, (0, 0, 0))
    helix = helix.rotate(V(0, 0, 0), V(0, 1, 0), 90).translate(
        V(x0, AUG_AX_Y, AUG_AX_Z))
    p0, tangent = _path_frame(helix)
    radial = V(0, p0.y - AUG_AX_Y, p0.z - AUG_AX_Z).normalized()
    axial = tangent.cross(radial).normalized()
    if axial.dot(V(1, 0, 0)) < 0:
        axial *= -1.0
    half_web = 1.5
    half_rad = (AUG_FLIGHT_RO - AUG_SHAFT_R) / 2.0
    profile = [p0 + radial * -half_rad + axial * -half_web,
               p0 + radial * half_rad + axial * -half_web,
               p0 + radial * half_rad + axial * half_web,
               p0 + radial * -half_rad + axial * half_web]
    wheel_key = _box(AUG_WHEEL_X0 - 1.0, AUG_WHEEL_X0 + 3.0,
                     AUG_AX_Y - 0.9, AUG_AX_Y + 0.9,
                     AUG_AX_Z + 2.8, AUG_AX_Z + 4.0)
    return shaft.fuse(_sweep_profile(helix, profile)).fuse(wheel_key).clean()


def auger_bearings():
    """West journal hangs above the belt, leaving its +X discharge open."""
    west_ring = _cyl(5.2, 6.0, 208.0, AUG_AX_Y, AUG_AX_Z,
                     axis=(1, 0, 0))
    west_ring = west_ring.cut(_cyl(3.5, 6.2, 207.9, AUG_AX_Y,
                                   AUG_AX_Z, axis=(1, 0, 0))).clean()
    # Two overhead steel arms tie the ring into both S1 metal side rails;
    # their z355.3 top stays below the cutter sweep bottom z357.3.
    bridge_s = _box(208.0, 214.0, 162.4, 226.8, 352.1, 355.3)
    bridge_n = _box(208.0, 214.0, 237.2, 324.6, 352.1, 355.3)
    post_s = _box(208.0, 214.0, 225.5, 228.5, 350.7, 353.0)
    post_n = _box(208.0, 214.0, 235.5, 238.5, 350.7, 353.0)
    west = west_ring.fuse(bridge_s).fuse(bridge_n).fuse(post_s).fuse(post_n).clean()
    east = _box(366.0, 369.0, 226.0, 238.0,
                AUG_FLOOR_TOP, AUG_AX_Z + AUG_SHAFT_R)
    east = east.cut(_cyl(3.7, 8.0, 364.0, AUG_AX_Y,
                          AUG_AX_Z, axis=(1, 0, 0))).clean()
    return cq.Compound.makeCompound([west, east]).clean()


def auger_wheel():
    """Sector gear at the auger end, generated against the actual worm.

    The swept worm is indexed through the 16:2 reduction and subtracted
    from the annular blank, rather than replacing the mating tooth faces
    with nominal blocks.
    """
    angle = math.radians(25.0)
    wedge_pts = [(AUG_AX_Y + 40.0 * math.sin(angle),
                  AUG_AX_Z + 40.0 * math.cos(angle)),
                 (AUG_AX_Y, AUG_AX_Z),
                 (AUG_AX_Y - 40.0 * math.sin(angle),
                  AUG_AX_Z + 40.0 * math.cos(angle))]
    wedge_wire = cq.Wire.makePolygon(
        [V(AUG_WHEEL_X0 - 1.0, y, z) for y, z in wedge_pts],
        close=True)
    wedge = cq.Solid.extrudeLinear(wedge_wire, [], V(8.0, 0, 0)).clean()
    outer = _cyl(WHEEL_R_TIP, 8.0, AUG_WHEEL_X0 - 1.0,
                 AUG_AX_Y, AUG_AX_Z, axis=(1, 0, 0))
    inner = _cyl(WHEEL_R_ROOT, 10.0, AUG_WHEEL_X0 - 1.0,
                 AUG_AX_Y, AUG_AX_Z, axis=(1, 0, 0))
    web_outer = _cyl(WHEEL_R_ROOT, 4.0, AUG_WHEEL_X0 - 1.0,
                     AUG_AX_Y, AUG_AX_Z, axis=(1, 0, 0))
    web_inner = _cyl(AUG_SHAFT_R, 6.0, AUG_WHEEL_X0 - 1.0,
                     AUG_AX_Y, AUG_AX_Z, axis=(1, 0, 0))
    pieces = []
    for ring in (outer.cut(inner), web_outer.cut(web_inner)):
        for solid in ring.intersect(wedge).Solids():
            bb = solid.BoundingBox()
            if bb.zmax > AUG_AX_Z + 3.0 and solid.Volume() > 1.0:
                pieces.append(solid)
    body = pieces[0]
    for solid in pieces[1:]:
        body = body.fuse(solid)
    worm = worm_sleeve()
    cutters = None
    for i in range(-12, 13):
        beta = 2.0 * i
        cutter = worm.rotate(V(WORM_CX, 0, WORM_CZ),
                             V(0, 1, 0), 8.0 * beta)
        cutter = cutter.rotate(V(0, AUG_AX_Y, AUG_AX_Z),
                                V(1, 0, 0), -beta)
        cutters = cutter if cutters is None else cutters.fuse(cutter)
    return body.cut(cutters).cut(_box(
        AUG_WHEEL_X0 - 1.1, AUG_WHEEL_X0 + 3.1,
        AUG_AX_Y - 1.0, AUG_AX_Y + 1.0,
        AUG_AX_Z + 2.8, AUG_AX_Z + 4.1)).clean()


def _cross_feed_flight(y0, y1, outer_radius, phase_deg=0.0):
    helix = _helix_z((CROSS_SHAFT_R + outer_radius) / 2.0,
                     CROSS_PITCH, y1 - y0, (0, 0, y0), lefthand=False)
    helix = helix.rotate(V(0, 0, 0), V(1, 0, 0), -90).translate(
        V(CROSS_X, 0, CROSS_Z))
    p0, tangent = _path_frame(helix)
    radial = V(p0.x - CROSS_X, 0, p0.z - CROSS_Z).normalized()
    axial = tangent.cross(radial).normalized()
    if axial.dot(V(0, 1, 0)) < 0:
        axial *= -1.0
    half_rad = (outer_radius - CROSS_SHAFT_R) / 2.0
    half_web = 1.25
    profile = [p0 + radial * -half_rad + axial * -half_web,
               p0 + radial * half_rad + axial * -half_web,
               p0 + radial * half_rad + axial * half_web,
               p0 + radial * -half_rad + axial * half_web]
    return _sweep_profile(helix, profile).rotate(
        V(CROSS_X, 0, CROSS_Z), V(CROSS_X, 1, CROSS_Z), phase_deg)

def cross_feed_shaft():
    """RH receiving flight and rotor-clear powered tail advance material +Y."""
    shaft = _cyl(CROSS_SHAFT_R, CROSS_SHAFT_Y1 - CROSS_SHAFT_Y0,
                 CROSS_X, CROSS_SHAFT_Y0, CROSS_Z)
    key = _box(CROSS_X + 2.8, CROSS_X + 4.0,
               CROSS_GEAR_Y0, CROSS_GEAR_Y1,
               CROSS_Z - 1.0, CROSS_Z + 1.0)
    return (shaft.fuse(key)
            .fuse(_cross_feed_flight(CROSS_FLIGHT_Y0, CROSS_FLIGHT_Y1,
                                     CROSS_FLIGHT_RO))
            .fuse(_cross_feed_flight(
                CROSS_FLIGHT_Y1, CROSS_TAIL_Y1, CROSS_TAIL_RO,
                phase_deg=360.0 * (CROSS_FLIGHT_Y1 - CROSS_FLIGHT_Y0) /
                CROSS_PITCH)).clean())


def _feed_gear(cx, cz, bore, phase=0.0):
    """Six-mm, 12T involute spur face, keyed on its +X bore flank."""
    import drive_teeth as dt
    tooth = dt._gear_profile_xy(FEED_GEAR_TEETH, phase_deg=phase)
    gear = _prism_xz([(cx + x, cz + z) for x, z in tooth],
                     CROSS_GEAR_Y0, CROSS_GEAR_Y1 - CROSS_GEAR_Y0)
    gear = gear.cut(_cyl(bore, 6.2, cx, CROSS_GEAR_Y0 - 0.1, cz))
    return gear.cut(_box(cx + bore - 0.2, cx + bore + 1.1,
                         CROSS_GEAR_Y0 - 0.1, CROSS_GEAR_Y1 + 0.1,
                         cz - 1.1, cz + 1.1)).clean()


def pdl_feed_gear():
    """12T keyed output gear sharing the existing PDL shaft."""
    angle = math.degrees(math.atan2(IDLER_Z - WORM_CZ, IDLER_X - WORM_CX))
    return _feed_gear(WORM_CX, WORM_CZ, 5.0, phase=angle % 30.0)


def cross_feed_idler():
    """12T integral intermediate wheel on its own two supported journals."""
    toward_pdl = math.degrees(math.atan2(WORM_CZ - IDLER_Z,
                                          WORM_CX - IDLER_X))
    wheel = _feed_gear(IDLER_X, IDLER_Z, 3.0,
                       phase=(toward_pdl - 15.0) % 30.0)
    # The one-piece axle overlaps the gear bore by 0.05 mm in its CAD
    # union; the bearing bore is still 0.20 mm larger than the journal.
    core = _cyl(3.05, 17.0, IDLER_X, 207.0, IDLER_Z)
    key = _box(IDLER_X + 2.8, IDLER_X + 4.0, 213.0, 219.0,
               IDLER_Z - 1.0, IDLER_Z + 1.0)
    return core.fuse(key).fuse(wheel).clean()


def cross_feed_gear():
    """Equal 12T keyed output wheel; two external meshes restore PDL sign."""
    toward_idler = math.degrees(math.atan2(IDLER_Z - CROSS_Z,
                                            IDLER_X - CROSS_X))
    idler_toward_cross = math.degrees(math.atan2(CROSS_Z - IDLER_Z,
                                                 CROSS_X - IDLER_X))
    idler_toward_pdl = math.degrees(math.atan2(WORM_CZ - IDLER_Z,
                                               WORM_CX - IDLER_X))
    idler_phase = (idler_toward_pdl - 15.0) % 30.0
    # Index a tooth into the idler's nearest gap at this second mesh.
    idler_offset = (idler_toward_cross - idler_phase) % 30.0
    phase = (toward_idler + idler_offset - 15.0) % 30.0
    return _feed_gear(CROSS_X, CROSS_Z, CROSS_SHAFT_R, phase=phase)


def cross_feed_shell():
    """U cradle relieved for the swept S2 rotor, with an open inner outlet."""
    cradle = _box(345.8, 368.2, 223.5, 250.8, 315.8, CROSS_Z)
    bore = _cyl(10.65, 28.0, CROSS_X, 223.3, CROSS_Z)
    cradle = cradle.cut(bore)
    east = _box(368.2, 369.2, 223.5, 260.0, 320.0, 334.5)
    east = east.fuse(_box(368.2, 369.2, 238.1, 250.8, 334.5, 342.5))
    west = _box(344.3, 345.8, 240.9, 250.8, 326.0, 342.5)
    roof = _box(345.0, 369.2, 240.9, 250.8, 341.0, 342.5)
    outlet = _box(350.0, 359.7, 250.3, 258.0, 311.8, 317.3)
    lip_w = _box(349.0, 350.0, 250.3, 258.0, 315.8, 322.0)
    lip_e = _box(359.7, 360.1, 250.3, 258.0, 315.8, 319.0)
    # A 3.4 mm metal shelf is integral with the outer cheek. It supports
    # the narrow flight through the mouth while the inner side stays open
    # to the S2 rotor; the former inner bridge struck the moving hooks.
    shelf = _box(359.0, 369.0, 235.0, 260.0, 317.8, 321.2)
    shell = (cradle.fuse(east).fuse(west).fuse(roof)
             .fuse(outlet).fuse(lip_w).fuse(lip_e).fuse(shelf))
    # The former under-shaft bridge occupied the rotor's swept volume.
    # Remove only the inner sector; the remaining outer U wall and mounting
    # cheek stay one solid while the powered flight reaches past y255.
    rotor_clearance = _cyl(ROTOR_RADIAL_RELIEF_R, 26.0,
                           S2_AX, 234.0, S2_AZ)
    shell = shell.cut(rotor_clearance).clean()
    if len(shell.Solids()) != 1:
        raise RuntimeError("cross-feed shell rotor relief split its support")
    return shell


def cross_feed_bearings():
    """Paired cantilever journals on the cross shaft and intermediate idler."""
    pieces = []
    for x, z, intervals in ((CROSS_X, CROSS_Z, ((208.0, 211.0), (220.0, 223.0))),
                             (IDLER_X, IDLER_Z, ((207.0, 211.0), (220.0, 224.0)))):
        for y0, y1 in intervals:
            ring = _cyl(5.2, y1 - y0, x, y0, z)
            pieces.append(ring.cut(_cyl(3.25, y1 - y0 + 0.2,
                                        x, y0 - 0.1, z)))
    # External rails avoid the 12T tooth swept annuli at y213..219 and
    # connect the journals to the U shell near its east structural cheek.
    for y0, y1 in ((208.0, 211.0), (220.0, 223.0)):
        pieces.append(_box(361.0, 373.0, y0, y1, 321.0, 325.0))
    pieces.append(_box(371.7, 373.0, 208.0, 224.0, 320.5, 324.0))
    pieces.append(_box(369.2, 373.0, 223.0, 227.0, 318.0, 321.5))
    for y0, y1 in ((207.0, 211.0), (220.0, 224.0)):
        pieces.append(_box(IDLER_X + 4.0, 383.5, y0, y1,
                           IDLER_Z - 2.0, IDLER_Z + 2.0))
    pieces.append(_box(383.0, 384.5, 207.0, 224.0, 322.0, IDLER_Z + 2.0))
    pieces.append(_box(369.2, 384.5, 223.0, 227.0, 319.0, 325.0))
    return cq.Compound.makeCompound(pieces).clean()


def components():
    """S1 basin, auger, orthogonal screw and separately supported 1:1 drive."""
    parts = [pan_floor(), bypass_channel_floor(), intake_lip(),
             wall_front(), wall_rear(), guide_left(), guide_right(),
             bypass_wall_south(), bypass_wall_north_lower()]
    body = parts[0]
    for s in parts[1:]:
        body = body.fuse(s)
    body = body.cut(_obstruction_solid())
    # The S1 east liner remains in place; notch only chute wall upper lips.
    body = body.cut(_box(237.0, 240.05, S1["y0"], S1["y1"],
                         S1["bottom"], 356.4))
    # Re-bore the side-wall union after fusing front/rear walls and rails.
    # Bearings seat at this cylindrical interface and retain a 0.15 mm
    # radial journal clearance.
    for y0, y1 in ((157.4, 163.4), (323.6, 329.6)):
        body = body.cut(_cyl(2.35, y1-y0, SWEEP_X, y0, SWEEP_Z))
    body = body.cut(_cyl(1.15, 36.0, TRANSFER_EAST_X, 214.0,
                         TRANSFER_AX_Z))
    for y0, y1 in ((218.0, 223.2), (240.8, 246.0)):
        body = body.cut(_cyl(1.65, y1-y0, TRANSFER_EAST_X, y0,
                             TRANSFER_AX_Z))
    # The original north lip and slab must not obstruct the new U cradle's
    # fixed west guard over y241..251.
    body = body.cut(_box(344.0, 355.0, 240.9, 251.01, 334.0, 353.6))
    # The spur train sits below the AUG shaft in the south wall's original
    # footprint; remove the floor patch there as well as its wall relief.
    body = body.cut(_box(341.0, 355.0, 212.9, 219.2, 313.0, 390.0))
    solids = [x for x in body.Solids() if x.Volume() > 10.0]
    if len(solids) != 1:
        raise RuntimeError("CHUTE_BODY split: %d solids" % len(solids))
    driven = [("PDL_SHAFT", worm_shaft(), "feed"),
              ("PDL_BEARINGS", worm_bearings(), "feed"),
              ("PDL_SPROCKET", worm_sprocket(), "feed"),
              ("PDL_CHAIN", worm_chain(), "feed"),
              ("PDL_WORM", worm_sleeve(), "feed"),
              ("AUG_SHAFT", auger_shaft(), "feed"),
              ("AUG_BEARINGS", auger_bearings(), "feed"),
              ("AUG_WHEEL", auger_wheel(), "feed"),
              ("PDL_FEED_GEAR", pdl_feed_gear(), "feed"),
              ("CROSS_FEED_IDLER", cross_feed_idler(), "feed"),
              ("CROSS_FEED_GEAR", cross_feed_gear(), "feed"),
              ("CROSS_FEED_SHAFT", cross_feed_shaft(), "feed"),
              ("CROSS_FEED_BEARINGS", cross_feed_bearings(), "feed"),
              ("CROSS_FEED_SHELL", cross_feed_shell(), "feed"),
              ("S1_BELT", belt_loop(), "feed"),
              ("S1_BELT_DRIVE", belt_drum(BELT_WEST_X, driven=True), "feed"),
              ("S1_BELT_IDLER", belt_drum(BELT_EAST_X), "feed"),
              ("S1_BELT_BEARINGS", belt_bearings(), "feed"),
              ("S1_BELT_FOLLOWER", belt_follower_sprocket(), "feed"),
              ("S1_BELT_CHAIN", belt_chain(), "feed")]
    driven += [("S1_SWEEP_SOUTH", sweep_shaft(True), "feed"),
               ("S1_SWEEP_NORTH", sweep_shaft(False), "feed"),
               ("S1_SWEEP_GEAR_DRUM_S", sweep_gear(True, True), "feed"),
               ("S1_SWEEP_GEAR_S", sweep_gear(True, False), "feed"),
               ("S1_SWEEP_GEAR_DRUM_N", sweep_gear(False, True), "feed"),
               ("S1_SWEEP_GEAR_N", sweep_gear(False, False), "feed"),
               ("S1_SWEEP_BEARINGS", sweep_bearings(), "feed")]
    driven += [("S1_TRANSFER_BELT", transfer_belt(), "feed"),
               ("S1_TRANSFER_IDLER", transfer_idler(), "feed"),
               ("S1_TRANSFER_BEARINGS", transfer_bearings(), "feed")]
    return [("CHUTE_BODY", solids[0].clean(), "feed"),
            ("CHUTE_TROUGH_FLOOR_E", trough_floor(), "feed")] + driven


def cutter_sweep_solids():
    """Conservative S1 cutter sweep envelopes for clearance checks."""
    out = []
    for x in (130.0, 190.0):
        out.append(cq.Solid.makeCylinder(41.0, 160.0, V(x, 160.0, 398.30275184708404),
                                         V(0, 1, 0)))
    return out


if __name__ == "__main__":
    import json
    from build_machine_integration import bounds
    parts = components()
    recs = []
    fails = []
    separated = {"PDL_BEARINGS": 2, "AUG_BEARINGS": 2,
                 "CROSS_FEED_BEARINGS": 12,
                 "S1_BELT": 2, "S1_BELT_IDLER": 2,
                 "S1_BELT_BEARINGS": 4,
                 "S1_SWEEP_BEARINGS": 2,
                 "S1_TRANSFER_BEARINGS": 2}
    for name, solid, group in parts:
        ok = solid.isValid() and len(solid.Solids()) == separated.get(name, 1)
        recs.append({"name": name, "solids": len(solid.Solids()),
                     "valid": solid.isValid(), "bounds": bounds(solid)})
        if not ok:
            fails.append(name)
    sweeps = cutter_sweep_solids()
    clearance = []
    for name, solid, group in parts:
        for i, sw in enumerate(sweeps, 1):
            b1, b2 = solid.BoundingBox(), sw.BoundingBox()
            overlap = all(min(getattr(b1, a + "max"), getattr(b2, a + "max"))
                          - max(getattr(b1, a + "min"), getattr(b2, a + "min")) > 0
                          for a in "xyz")
            if overlap:
                v = solid.intersect(sw).Volume()
                if v > 1e-6:
                    clearance.append({"part": name, "sweep": "S%d" % i,
                                      "volume_mm3": v})
    result = {"parts": recs, "cutter_sweep_intersections": clearance,
              "passed": not fails and not clearance}
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for name, solid, group in parts:
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    result["exported_step"] = exported
    (ROOT / "results" / "chute_geometry.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails or clearance:
        raise SystemExit(1)
