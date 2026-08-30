"""Closed-solid source geometry for the compact v0.5 machine.

Review keep-outs are emitted by :func:`review_keepout_objects` and are never
part of the fabrication assembly or printable exports.
"""

from __future__ import annotations

import math
from pathlib import Path

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[3]


def box(x, y, z, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, App.Vector(x, y, z))


def cyl(radius, length, x, y, z, axis=(0, 0, 1)):
    return Part.makeCylinder(radius, length, App.Vector(x, y, z), App.Vector(*axis))


def shell_box(dx, dy, dz, wall=3.0, bottom=True):
    outer = Part.makeBox(dx, dy, dz)
    inner_z = wall if bottom else 0
    inner = Part.makeBox(dx - 2 * wall, dy - 2 * wall, dz, App.Vector(wall, wall, inner_z))
    return outer.cut(inner).removeSplitter()


def joined(*shapes):
    """Boolean-union overlapping bodies and remove internal splitters."""
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    result = result.removeSplitter()
    return result.Solids[0] if len(result.Solids) == 1 else result


def one_solid(shape):
    """Normalize a one-solid boolean compound to an explicit TopoDS_Solid."""
    refined = shape.removeSplitter()
    return refined.Solids[0] if len(refined.Solids) == 1 else refined


def open_front_sheet_shell(dx, dy, dz, wall=2.0):
    """Five-sided sheet enclosure, open on local Y=0 service/front face."""
    outer = Part.makeBox(dx, dy, dz)
    inner = Part.makeBox(dx - 2 * wall, dy - wall, dz - 2 * wall, App.Vector(wall, 0, wall))
    return one_solid(outer.cut(inner))


def three_panel_tunnel(dx, dy, dz, wall=2.0):
    """Open-ended, open-bottom sheet tunnel joined at its two upper seams."""
    return one_solid(joined(
        Part.makeBox(dx, wall, dz),
        Part.makeBox(dx, wall, dz, App.Vector(0, dy - wall, 0)),
        Part.makeBox(dx, dy, wall, App.Vector(0, 0, dz - wall)),
    ))


def puller_plate_shape():
    """100 x 40 x10 metal plate with two roller bores and four guard mounts."""
    plate = Part.makeBox(100, 10, 40)
    for x in (30, 70):
        plate = plate.cut(Part.makeCylinder(4.1, 10, App.Vector(x, 0, 20), App.Vector(0, 1, 0)))
    for x in (10, 90):
        for z in (7, 33):
            plate = plate.cut(Part.makeCylinder(2.25, 10, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def puller_roller_shape():
    """Ø40 x60 roller with Ø8.2 through bore for a metal spindle."""
    return one_solid(Part.makeCylinder(20, 60).cut(Part.makeCylinder(4.1, 60)))


def chain_sprocket_shape(teeth, bore, thickness=10.0, pitch=9.525):
    """Manufacturable #35 sprocket LOD with explicit teeth and shaft bore."""
    pitch_radius = pitch / (2.0 * math.sin(math.pi / teeth))
    outer_radius = 0.5 * pitch * (0.6 + 1.0 / math.tan(math.pi / teeth))
    root_radius = pitch_radius - 2.8
    sprocket = Part.makeCylinder(root_radius, thickness)
    tooth_length = outer_radius - root_radius + 0.5
    tooth_width = max(3.0, pitch * 0.38)
    for index in range(teeth):
        tooth = Part.makeBox(
            tooth_length,
            tooth_width,
            thickness,
            App.Vector(root_radius - 0.25, -tooth_width / 2.0, 0),
        )
        tooth.rotate(App.Vector(), App.Vector(0, 0, 1), index * 360.0 / teeth)
        sprocket = sprocket.fuse(tooth)
    return one_solid(sprocket.removeSplitter().cut(Part.makeCylinder(bore / 2.0, thickness)))


def gmp60_60127_reference_shape():
    """TT Motor GMP60-60127-2460 with ratio-47 gearbox, shaft on +Z."""
    motor = Part.makeCylinder(30.25, 127.0)
    gearbox = Part.makeCylinder(30.0, 59.0, App.Vector(0, 0, 127.0))
    # Official side view: Ø32 pilot projects 4.85 mm; the Ø12 shaft extends
    # 25.8 mm from the gearbox mounting face and has a 13 mm D-flat length.
    front_boss = Part.makeCylinder(16.0, 4.85, App.Vector(0, 0, 186.0))
    shaft = Part.makeCylinder(6.0, 25.8, App.Vector(0, 0, 186.0))
    return one_solid(joined(motor, gearbox, front_boss, shaft))


def motor_adapter_42gp775_shape():
    """DRV-A42 plate for the requested 42GP/GMP42 family reference."""
    plate = Part.makeBox(70, 70, 6)
    plate = plate.cut(Part.makeCylinder(13.0, 6, App.Vector(35, 35, 0)))
    for angle in (45, 135, 225, 315):
        a = math.radians(angle)
        plate = plate.cut(Part.makeCylinder(2.25, 6, App.Vector(35 + 17.5 * math.cos(a), 35 + 17.5 * math.sin(a), 0)))
    for x in (8, 62):
        plate = plate.cut(Part.makeBox(6.6, 16, 6, App.Vector(x - 3.3, 27, 0)))
    return one_solid(plate)


def motor_adapter_gmp60_shape():
    """DRV-A60 plate for the selected GMP60-60127 reference motor."""
    plate = Part.makeBox(80, 80, 6)
    plate = plate.cut(Part.makeCylinder(16.1, 6, App.Vector(40, 40, 0)))
    for angle in (45, 135, 225, 315):
        a = math.radians(angle)
        plate = plate.cut(Part.makeCylinder(2.75, 6, App.Vector(40 + 22.5 * math.cos(a), 40 + 22.5 * math.sin(a), 0)))
    for x in (8, 72):
        plate = plate.cut(Part.makeBox(6.6, 18, 6, App.Vector(x - 3.3, 31, 0)))
    return one_solid(plate)


def mica_band_heater_shape(inner_diameter=34.0, width=45.0, radial_thickness=2.0, closure_gap=4.0):
    """24 V/100 W custom split mica band, local barrel axis +Z."""
    inner_radius = inner_diameter / 2.0
    band = Part.makeCylinder(inner_radius + radial_thickness, width).cut(
        Part.makeCylinder(inner_radius, width)
    )
    # A real split is required for clamp installation; the RFQ controls the
    # closure hardware and as-clamped ID, not this display gap.
    split = Part.makeBox(
        radial_thickness + 2.0,
        closure_gap,
        width,
        App.Vector(inner_radius - 1.0, -closure_gap / 2.0, 0),
    )
    return one_solid(band.cut(split))


def k_type_probe_shape(diameter=3.0, insertion_length=6.0, lead_length=45.0):
    """Grounded mineral-insulated K-probe LOD with a flexible lead."""
    probe = Part.makeCylinder(diameter / 2.0, insertion_length)
    lead = Part.makeCylinder(1.0, lead_length, App.Vector(0, 0, -lead_length))
    return one_solid(joined(probe, lead))


def die_cartridge_heater_shape():
    """24 V/60 W Ø6 x38 cartridge; local axis +Y."""
    return Part.makeCylinder(3.0, 38.0, App.Vector(0, -19.0, 0), App.Vector(0, 1, 0))


def hopper_ptc_spreader_shape():
    """Aluminum maintenance-heat spreader, never a primary PET dryer."""
    plate = Part.makeBox(120, 3, 55)
    for x in (8, 112):
        for z in (8, 47):
            plate = plate.cut(Part.makeCylinder(2.25, 3, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def hopper_ptc_clamp_shape():
    """Metal keeper plate for four 35 x21 x5 PTC elements."""
    plate = Part.makeBox(120, 2, 55)
    for x in (8, 112):
        for z in (8, 47):
            plate = plate.cut(Part.makeCylinder(2.25, 2, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def feeder_housing_shape():
    """Compact vertical metering housing: Ø36/Ø32 x105 with bolted end flanges."""
    tube = Part.makeCylinder(18, 105).cut(Part.makeCylinder(16, 105))
    lower = Part.makeCylinder(24, 3).cut(Part.makeCylinder(16, 3))
    upper = Part.makeCylinder(24, 3, App.Vector(0, 0, 102)).cut(
        Part.makeCylinder(16, 3, App.Vector(0, 0, 102))
    )
    housing = joined(tube, lower, upper)
    for z in (0, 102):
        for angle in (0, 90, 180, 270):
            a = math.radians(angle)
            housing = housing.cut(
                Part.makeCylinder(2.25, 3, App.Vector(20 * math.cos(a), 20 * math.sin(a), z))
            )
    return one_solid(housing)


def feeder_metering_rotor_shape():
    """Six-pocket removable metering disc; physical feed coupon sets RPM/capacity."""
    rotor = Part.makeCylinder(15.8, 8).cut(Part.makeCylinder(2.6, 8))
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        rotor = rotor.cut(Part.makeCylinder(4.0, 8, App.Vector(10 * math.cos(a), 10 * math.sin(a), 0)))
    return one_solid(rotor)


def thrust_plate_shape():
    """12 mm thrust plate with Ø17.2 passage, Ø30.2 seat and four M6 mounts."""
    plate = Part.makeBox(12, 95, 105)
    plate = plate.cut(Part.makeCylinder(8.6, 12, App.Vector(0, 47.5, 52.5), App.Vector(1, 0, 0)))
    plate = plate.cut(Part.makeCylinder(15.1, 5, App.Vector(0, 47.5, 52.5), App.Vector(1, 0, 0)))
    for y in (12, 83):
        for z in (15, 90):
            plate = plate.cut(Part.makeCylinder(3.3, 12, App.Vector(0, y, z), App.Vector(1, 0, 0)))
    return one_solid(plate)


def guide_roller_shape():
    """Ø36 guide roller with two real 625-2RS bearing seats.

    The former Ø8.2 through-bore was incorrectly described as a 625 bearing
    interface even though a 625 bearing has a 16 mm OD.  The corrected roller
    carries one 625 bearing in each end; the fixed Ø5 axle passes through the
    bearing IDs and the printed PPR-C08 brackets only locate that axle.
    """
    roller = Part.makeCylinder(18, 20)
    roller = roller.cut(Part.makeCylinder(6.0, 20))
    roller = roller.cut(Part.makeCylinder(8.0, 5.1))
    roller = roller.cut(Part.makeCylinder(8.0, 5.1, App.Vector(0, 0, 14.9)))
    return one_solid(roller)


def spool_bearing_plate_shape():
    plate = Part.makeBox(105, 5, 60)
    plate = plate.cut(Part.makeCylinder(14.1, 5, App.Vector(30, 0, 30), App.Vector(0, 1, 0)))
    for x in (8, 52):
        for z in (8, 52):
            plate = plate.cut(Part.makeCylinder(2.75, 5, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    for z in (10, 50):
        plate = plate.cut(Part.makeCylinder(2.75, 5, App.Vector(97, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def spool_motor_mount_shape():
    plate = Part.makeBox(101, 6, 52).cut(
        Part.makeCylinder(12, 6, App.Vector(26, 0, 26), App.Vector(0, 1, 0))
    )
    for x in (10.5, 41.5):
        for z in (10.5, 41.5):
            plate = plate.cut(Part.makeCylinder(2.25, 6, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    for z in (10, 42):
        plate = plate.cut(Part.makeCylinder(2.75, 6, App.Vector(93, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def traverse_end_plate_shape():
    plate = Part.makeBox(5, 50, 40)
    for y in (10, 35):
        plate = plate.cut(Part.makeCylinder(4.1, 5, App.Vector(0, y, 20), App.Vector(1, 0, 0)))
    for y in (6, 44):
        plate = plate.cut(Part.makeCylinder(2.75, 5, App.Vector(0, y, 6), App.Vector(1, 0, 0)))
    return one_solid(plate)


def dancer_support_plate_shape():
    plate = Part.makeBox(36, 8, 80)
    plate = plate.cut(Part.makeCylinder(4.1, 8, App.Vector(18, 0, 45), App.Vector(0, 1, 0)))
    for x in (8, 28):
        plate = plate.cut(Part.makeCylinder(2.75, 8, App.Vector(x, 0, 10), App.Vector(0, 1, 0)))
    return one_solid(plate)


def hollow_tube_between(start, end, outer_radius, wall):
    """Straight sealed transfer tube between two 3-D points."""
    p0 = App.Vector(*start); p1 = App.Vector(*end); direction = p1.sub(p0)
    length = direction.Length
    axis = direction.normalize()
    outer = Part.makeCylinder(outer_radius, length, p0, axis)
    inner = Part.makeCylinder(outer_radius - wall, length, p0, axis)
    return one_solid(outer.cut(inner))


def down_die_body():
    """Machinable 90 degree open-die body, local barrel face at X=40.

    The local outlet axis is X=20/Y=0.  The body is bolted to the barrel
    front face through a replaceable copper gasket; no printed part carries
    melt pressure or heater load.
    """
    body = Part.makeBox(40, 40, 48, App.Vector(0, -20, -24))
    # Ø8 horizontal-to-vertical melt turn and Ø16.2 breaker-plate seat.
    body = body.cut(Part.makeCylinder(4, 21, App.Vector(19, 0, 0), App.Vector(1, 0, 0)))
    body = body.cut(Part.makeCylinder(4, 28, App.Vector(20, 0, -24)))
    body = body.cut(Part.makeCylinder(8.10, 3, App.Vector(37, 0, 0), App.Vector(1, 0, 0)))
    # Replaceable Ø11.9 x14 die insert seat.
    body = body.cut(Part.makeCylinder(6.0, 14, App.Vector(20, 0, -24)))
    # Four M4 barrel bolts on PCD26; heads are accessible from local X=0.
    for angle in (45, 135, 225, 315):
        a = math.radians(angle)
        y, z = 13 * math.cos(a), 13 * math.sin(a)
        body = body.cut(Part.makeCylinder(2.25, 40, App.Vector(0, y, z), App.Vector(1, 0, 0)))
        body = body.cut(Part.makeCylinder(4.0, 5, App.Vector(0, y, z), App.Vector(1, 0, 0)))
    # Two M4 retainer threads, one heater bore and one blind sensor bore.
    for x in (8, 32):
        body = body.cut(Part.makeCylinder(1.65, 10, App.Vector(x, 0, -24)))
    body = body.cut(Part.makeCylinder(3.025, 40, App.Vector(20, -20, 18), App.Vector(0, 1, 0)))
    body = body.cut(Part.makeCylinder(1.60, 12, App.Vector(8, -20, 15), App.Vector(0, 1, 0)))
    return one_solid(body)


def down_die_breaker_plate():
    """Ø15.9 x2 304 breaker plate with seven Ø2 flow holes."""
    plate = Part.makeCylinder(7.95, 2, App.Vector(37, 0, 0), App.Vector(1, 0, 0))
    holes = [Part.makeCylinder(1, 2, App.Vector(37, 0, 0), App.Vector(1, 0, 0))]
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        holes.append(Part.makeCylinder(1, 2, App.Vector(37, 5 * math.cos(a), 5 * math.sin(a)), App.Vector(1, 0, 0)))
    return one_solid(plate.cut(Part.makeCompound(holes)))


def down_die_insert():
    """Replaceable Ø11.9 x14 die insert: Ø3 x10 land plus 4 mm cone."""
    insert = Part.makeCylinder(5.95, 14, App.Vector(20, 0, -24))
    insert = insert.cut(Part.makeCylinder(1.5, 10, App.Vector(20, 0, -24)))
    insert = insert.cut(Part.makeCone(1.5, 4.0, 4, App.Vector(20, 0, -14)))
    return one_solid(insert)


def down_die_relief_retainer():
    """Coupon-calibrated 304 stainless sacrificial retainer, t=1.5."""
    plate = Part.makeBox(32, 20, 1.5, App.Vector(4, -10, -25.5))
    # Two 10 wide x2.5 long bending webs between bolt pads and insert pad.
    for x in (12, 25.5):
        plate = plate.cut(Part.makeBox(2.5, 5, 1.5, App.Vector(x, -10, -25.5)))
        plate = plate.cut(Part.makeBox(2.5, 5, 1.5, App.Vector(x, 5, -25.5)))
    for x in (8, 32):
        plate = plate.cut(Part.makeCylinder(2.25, 1.5, App.Vector(x, 0, -25.5)))
    plate = plate.cut(Part.makeCylinder(2.0, 1.5, App.Vector(20, 0, -25.5)))
    return one_solid(plate)


def down_die_copper_gasket():
    """Annealed copper face gasket, t=0.5, matching barrel M4 PCD26."""
    gasket = Part.makeCylinder(17, 0.5, App.Vector(40, 0, 0), App.Vector(1, 0, 0))
    gasket = gasket.cut(Part.makeCylinder(8.1, 0.5, App.Vector(40, 0, 0), App.Vector(1, 0, 0)))
    for angle in (45, 135, 225, 315):
        a = math.radians(angle)
        gasket = gasket.cut(Part.makeCylinder(2.25, 0.5, App.Vector(40, 13 * math.cos(a), 13 * math.sin(a),), App.Vector(1, 0, 0)))
    return one_solid(gasket)


def cylindrical_hopper(radius, straight_height, cone_height, outlet_radius, wall=2.0):
    straight = Part.makeCylinder(radius, straight_height).cut(
        Part.makeCylinder(radius-wall, straight_height, App.Vector(0, 0, wall))
    )
    outer_cone = Part.makeCone(outlet_radius, radius, cone_height, App.Vector(0, 0, -cone_height))
    inner_cone = Part.makeCone(outlet_radius-wall, radius-wall, cone_height, App.Vector(0, 0, -cone_height+wall))
    return straight.fuse(outer_cone.cut(inner_cone))


def _cycloidal_ease(u):
    """Unit cycloid displacement, with zero slope at both ends."""
    return u - math.sin(2.0 * math.pi * u) / (2.0 * math.pi)


def cycloidal_hook_profile_points(od=58.0, root=36.0, hooks=7, capture_samples=18, relief_samples=8):
    """Return the controlling asymmetric 7-hook profile points."""
    pts = []
    pitch = 2.0 * math.pi / hooks
    r_root = root / 2.0
    r_tip = od / 2.0
    capture_fraction = 0.76
    for i in range(hooks):
        a = pitch * i
        for j in range(capture_samples):
            u = j / capture_samples
            s = _cycloidal_ease(u)
            angle = a + capture_fraction * pitch * u
            radius = r_root + (r_tip - r_root) * s
            pts.append(App.Vector(radius * math.cos(angle), 0, radius * math.sin(angle)))
        # Rounded overhung nose.  The slightly enlarged middle point survives
        # deburr while retaining a visible capture lip.
        for phase, radius in ((0.76, r_tip), (0.80, r_tip + 0.55), (0.84, r_tip - 0.5)):
            angle = a + phase * pitch
            pts.append(App.Vector(radius * math.cos(angle), 0, radius * math.sin(angle)))
        for j in range(1, relief_samples + 1):
            u = j / relief_samples
            # Fast cubic relief produces the undercut-looking hook back while
            # remaining a single closed 2-D profile suitable for waterjet.
            s = 1.0 - (1.0 - u) ** 3
            angle = a + (0.84 + 0.16 * u) * pitch
            radius = (r_tip - 0.5) - ((r_tip - 0.5) - r_root) * s
            pts.append(App.Vector(radius * math.cos(angle), 0, radius * math.sin(angle)))
    pts.append(pts[0])
    return pts


def hook_disc(od=58.0, root=36.0, thickness=6.0, hooks=7, capture_samples=18, relief_samples=8):
    """Asymmetric cycloidal-derived hook disc.

    A long 76 % capture flank follows a cycloidal radial rise.  A short nose
    and 24 % relief flank create the hook asymmetry.  This is a manufacturable
    2-D laser/waterjet profile, not a generic saw-tooth placeholder.
    """
    pts = cycloidal_hook_profile_points(od, root, hooks, capture_samples, relief_samples)
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    disc = face.extrude(App.Vector(0, thickness, 0))
    bore = cyl(10.1, thickness, 0, 0, 0, (0, 1, 0))
    # Internal keyway only: the previous long radial cut could open through a
    # tooth.  A 6 mm radial depth from z=7 accepts the protruding half of a
    # standard 6 x 6 key while remaining blind inside the hub/root section.
    keyway = Part.makeBox(6.2, thickness, 6.0, App.Vector(-3.1, 0, 7.0))
    return disc.cut(bore.fuse(keyway))


def spur_phase_gear(module=2.0, teeth=24, thickness=8.0, bore=20.2):
    """Ideal 20 degree involute envelope for a purchased steel phase gear.

    Root trochoid and hub/set-screw details remain supplier geometry; this
    model is not released as a cut-gear DXF.
    """
    pressure_angle = math.radians(20.0)
    pitch_radius = module * teeth / 2.0
    base_radius = pitch_radius * math.cos(pressure_angle)
    root_radius = pitch_radius - 1.25 * module
    tip_radius = pitch_radius + module
    half_tooth = math.pi / (2.0 * teeth)
    pitch_involute = math.tan(pressure_angle) - pressure_angle

    def theta_at(radius):
        t = math.sqrt(max(0.0, (radius / base_radius) ** 2 - 1.0))
        return half_tooth + pitch_involute - (t - math.atan(t))

    pts = []
    for i in range(teeth):
        a = 2.0 * math.pi * i / teeth
        theta_base = theta_at(base_radius)
        # Left root and involute flank.
        pts.append(App.Vector(root_radius * math.cos(a - theta_base), 0, root_radius * math.sin(a - theta_base)))
        for j in range(7):
            radius = base_radius + (tip_radius - base_radius) * j / 6.0
            angle = a - theta_at(radius)
            pts.append(App.Vector(radius * math.cos(angle), 0, radius * math.sin(angle)))
        theta_tip = theta_at(tip_radius)
        for j in range(1, 4):
            angle = a - theta_tip + 2.0 * theta_tip * j / 3.0
            pts.append(App.Vector(tip_radius * math.cos(angle), 0, tip_radius * math.sin(angle)))
        for j in range(5, -1, -1):
            radius = base_radius + (tip_radius - base_radius) * j / 6.0
            angle = a + theta_at(radius)
            pts.append(App.Vector(radius * math.cos(angle), 0, radius * math.sin(angle)))
        pts.append(App.Vector(root_radius * math.cos(a + theta_base), 0, root_radius * math.sin(a + theta_base)))
        next_root = a + 2.0 * math.pi / teeth - theta_base
        for j in range(1, 4):
            angle = a + theta_base + (next_root - (a + theta_base)) * j / 3.0
            pts.append(App.Vector(root_radius * math.cos(angle), 0, root_radius * math.sin(angle)))
    pts.append(pts[0])
    gear = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, thickness, 0))
    return gear.cut(cyl(bore / 2.0, thickness, 0, 0, 0, (0, 1, 0)))


def screen_plate(width=135.0, depth=120.0, thickness=3.0, opening=5.0, pitch=9.0):
    plate = Part.makeBox(width, depth, thickness)
    holes = []
    x = 9.0
    while x <= width - 9.0:
        y = 9.0
        while y <= depth - 9.0:
            holes.append(Part.makeCylinder(opening / 2.0, thickness, App.Vector(x, y, 0)))
            y += pitch
        x += pitch
    return plate.cut(Part.makeCompound(holes))


def cutter_shaft(length=240.0):
    shaft = Part.makeCylinder(10, length, App.Vector(0, 0, 0), App.Vector(0, 1, 0))
    # One common shaft drawing serves both rotors.  The slave shaft is shifted
    # 20 mm rearward in assembly so the Ø~100 driven sprocket cannot intersect
    # it; the long common cutter and rear keyseats tolerate either position.
    for y, key_length in ((0.0, 35.0), (55.0, 105.0), (195.0, 45.0)):
        shaft = shaft.cut(Part.makeBox(6.0, key_length, 3.5, App.Vector(-3.0, y, 6.5)))
    return shaft


def bearing_side_plate():
    plate = Part.makeBox(150, 125, 12)
    for cx in (50, 98):
        plate = plate.cut(Part.makeCylinder(21.0, 12, App.Vector(cx, 55, 0)))
    for x, y in ((50, 81), (24, 55), (50, 29), (98, 81), (124, 55), (98, 29)):
        plate = plate.cut(Part.makeCylinder(2.25, 12, App.Vector(x, y, 0)))
    for x in (15, 135):
        for y in (15, 110):
            plate = plate.cut(Part.makeCylinder(3.3, 12, App.Vector(x, y, 0)))
    return plate


def motor_mount_plate():
    """DRV-01/CUT-07 universal donor plate; donor-specific angles bolt on."""
    plate = Part.makeBox(180, 140, 6)
    for x in (12,168):
        for y in (12,128):
            plate=plate.cut(Part.makeCylinder(3.3,6,App.Vector(x,y,0)))
    for x in (45,90,135):
        plate=plate.cut(Part.makeBox(9,70,6,App.Vector(x-4.5,35,0)))
    for y in (28,112):
        plate=plate.cut(Part.makeBox(55,9,6,App.Vector(62.5,y-4.5,0)))
    # Common output-shaft pass-through.  Donor face patterns remain solely on
    # DRV-Axx, so changing a motor never requires modifying this load plate.
    # Ø65 common gearbox clearance lets the donor-specific DRV-Axx carry the
    # face pattern without forcing a 60 mm gearcase through a Ø24 opening.
    plate = plate.cut(Part.makeCylinder(32.5, 6, App.Vector(90, 70, 0)))
    # Top-open output/coupling clearance.  The donor-specific adapter bridges
    # this notch; no proprietary face pattern is built into DRV-01.
    plate = plate.cut(Part.makeBox(26, 12, 6, App.Vector(75, 128, 0)))
    return plate


def bearing_retainer_plate():
    retainer = Part.makeCylinder(30, 2, App.Vector(50, 55, 0)).fuse(
        Part.makeCylinder(30, 2, App.Vector(98, 55, 0))
    )
    for cx in (50, 98):
        retainer = retainer.cut(Part.makeCylinder(17, 2, App.Vector(cx, 55, 0)))
    for x, y in ((50, 81), (24, 55), (50, 29), (98, 81), (124, 55), (98, 29)):
        retainer = retainer.cut(Part.makeCylinder(2.25, 2, App.Vector(x, y, 0)))
    return retainer


def shredder_metal_parts():
    """Orderable metal part geometry exported by generate.py."""
    plate = bearing_side_plate()
    shaft = cutter_shaft()
    motor_mount = motor_mount_plate()
    bearing_retainer = bearing_retainer_plate()
    return [
        dict(id="CUT-01", name="Cycloidal hook cutter disc", shape=hook_disc(), qty=12, material="6 mm D2/SKD11 candidate", process="waterjet or laser + finish grind", critical="OD 58.0; root 36.0; bore 20.2 +0.10/0; keyway width 6.2 +0.10/0; flatness 0.10; tooth side deburr C0.15 max; axial working gap is set by 0.25-0.50 mm metal shim, never by printed tolerance"),
        dict(id="CUT-02", name="Cutter spacer", shape=Part.makeCylinder(14, 7).cut(Part.makeCylinder(10.1, 7)), qty=10, material="steel", process="simple turning", critical="OD 28.0; bore 20.2 +0.10/0; length 7.00 +/-0.03; faces parallel within 0.03"),
        dict(id="CUT-03", name="Bearing side plate", shape=plate, qty=2, material="12 mm steel or 15 mm 6061 after Gate 1", process="laser + bearing-seat finish", critical="two 6004 seats diameter 42 H7; center distance 48.00 +/-0.03; match-machine both plates; seat-axis parallelism 0.05/140; four frame holes diameter 6.6"),
        dict(id="CUT-04", name="5 mm aperture screen", shape=screen_plate(), qty=2, material="3 mm 304 stainless", process="laser cut + deburr", critical="135 x 120 x 3; apertures diameter 5.0 on 9.0 pitch; all strand-side edges R0.3; verify minimum 1.9 mm rotating clearance with shims before powered test"),
        dict(id="CUT-05", name="20 mm keyed cutter shaft", shape=shaft, qty=2, material="S45C", process="turn + keyway", critical="diameter 20 h6 at two 6004 journals per shaft; overall 240.0 +/-0.10; TIR <=0.05; 6 mm keyways at y=0-35, 55-160 and 195-240 from datum end; keyway depth 3.5; install driven shaft at Y258 and slave shaft at Y278 to preserve 20 mm front sprocket clearance; use standard metal clamp collars for axial retention"),
        dict(id="CUT-06", name="Phase gear axial spacer", shape=Part.makeCylinder(15, 4).cut(Part.makeCylinder(10.1, 4)), qty=2, material="steel", process="simple turning", critical="OD 30.0; bore 20.2 +0.10/0; length 4.00 +/-0.03; faces parallel within 0.03"),
        dict(id="CUT-07", name="DRV-01 universal donor motor plate", shape=motor_mount, qty=1, material="6 mm steel", process="laser cut + deburr; standard metal angles", critical="180 x 140 x 6; three 9 x 70 motor-angle slots and two 55 x 9 tension slots; donor-specific angle/hub drilling is HOLD until exact model, shaft height and rotation envelope are measured"),
        dict(id="CUT-08", name="Dual 6004 bearing retainer", shape=bearing_retainer, qty=2, material="2 mm steel", process="laser cut + deburr", critical="figure-eight OD lobes 60; two relief bores diameter 34; center distance 48.00 +/-0.05; six M4 clearance holes diameter 4.5 at drawing coordinates; CUT-03 matching holes are included and may be match-reamed after bearing-seat finish"),
    ]


def tolerance_coupon():
    """PPR-TC01 fit coupon; excluded from released machine print mass."""
    coupon=Part.makeBox(120,80,6)
    # Three-point diameter ladders for M3, M4 insert pilots and M5 clearance.
    for y,diameters in ((15,(3.2,3.4,3.6)),(35,(4.2,4.4,4.6)),(55,(5.3,5.5,5.7))):
        for index,diameter in enumerate(diameters):
            coupon=coupon.cut(Part.makeCylinder(diameter/2,6,App.Vector(12+index*16,y,0)))
    # Captured-square-nut pockets open from the top, with a central clearance.
    for y,sizes,clearance in ((70,(5.6,5.8,6.0),3.4),(70,(7.0,7.2,7.4),4.5)):
        x0=62 if clearance<4 else 88
        for index,size in enumerate(sizes):
            x=x0+index*10
            coupon=coupon.cut(Part.makeBox(size,size,3.2,App.Vector(x-size/2,y-size/2,2.8)))
            coupon=coupon.cut(Part.makeCylinder(clearance/2,6,App.Vector(x,y,0)))
    # Rod/shaft male gauges share the base and therefore remain one solid.
    for y,diameters in ((18,(7.8,8.0,8.2)),(43,(11.8,12.0,12.2))):
        for index,diameter in enumerate(diameters):
            coupon=coupon.fuse(Part.makeCylinder(diameter/2,12,App.Vector(72+index*18,y,6)))
    return one_solid(coupon)


def dancer_arm_shape(angle_deg=0.0, pivot=(188.0,452.0,115.0)):
    """Metal dancer arm at an angle about its physical Y-axis pivot."""
    arm=joined(
        Part.makeBox(105,8,12,App.Vector(0,-4,-6)),
        Part.makeCylinder(10,8,App.Vector(0,-4,0),App.Vector(0,1,0)),
        Part.makeCylinder(12,8,App.Vector(100,-4,0),App.Vector(0,1,0)),
    )
    arm=arm.cut(Part.makeCylinder(4.1,8,App.Vector(0,-4,0),App.Vector(0,1,0)))
    arm=arm.cut(Part.makeCylinder(4.1,8,App.Vector(100,-4,0),App.Vector(0,1,0)))
    arm.rotate(App.Vector(0,0,0),App.Vector(0,1,0),angle_deg)
    arm.translate(App.Vector(*pivot))
    return one_solid(arm)


def print_parts():
    # Every fastener named in the print notes is represented by an actual
    # clearance/insert bore in the released solid.  Bosses overlap the parent
    # wall or plate; no floating cylinders are used.
    lid = joined(
        Part.makeBox(195, 195, 2),
        Part.makeBox(195, 4, 6),
        Part.makeBox(195, 4, 6, App.Vector(0, 191, 0)),
        Part.makeCylinder(7, 8, App.Vector(180, 12, 0)),
    ).cut(Part.makeCylinder(2.3, 5, App.Vector(180, 12, 3)))

    # Two staggered horizontal ledges form a real zig-zag anti-reach path.
    # The 100 x 60 bottom outlet prevents the old closed-bottom dead end.
    chute = shell_box(190, 120, 90, 2).cut(Part.makeBox(100, 50, 2, App.Vector(45, 35, 0)))
    chute = joined(
        chute,
        Part.makeBox(186, 72, 2, App.Vector(2, 2, 58)),
        Part.makeBox(186, 72, 2, App.Vector(2, 46, 30)),
        *(Part.makeCylinder(7, 8, App.Vector(x, y, 0)) for x, y in ((8, 8), (182, 8), (8, 112), (182, 112))),
    )
    for x, y in ((8, 8), (182, 8), (8, 112), (182, 112)):
        chute = chute.cut(Part.makeCylinder(2.25, 8, App.Vector(x, y, 0)))
    # Chamber upper tie bolts pass through sealed clearance holes in both
    # walls.  The installed M6 bolts close these paths in service.
    for x in (35, 155):
        chute = chute.cut(Part.makeCylinder(3.3, 120, App.Vector(x, 0, 25), App.Vector(0, 1, 0)))

    # Orthogonal U-channels capture 1 mm PP/ABS panels in 1.4 mm slots.  This
    # is a real clamp geometry, not a solid L-bracket occupying sheet volume.
    flake_bin = joined(
        Part.makeBox(25, 2, 100),
        Part.makeBox(2, 25, 100),
        # The two inner channel walls overlap 1 mm at the corner.  An exact
        # edge-only meeting creates a four-face non-manifold STL edge.
        Part.makeBox(20.6, 2, 94.2, App.Vector(4.4, 3.4, 4)),
        Part.makeBox(2, 20.6, 94.2, App.Vector(3.4, 4.4, 4)),
        Part.makeBox(25, 25, 2, App.Vector(0, 0, 98)),
    )
    flake_bin = flake_bin.cut(Part.makeCylinder(1.7, 3, App.Vector(0, 12, 90), App.Vector(1, 0, 0)))
    flake_bin = flake_bin.cut(Part.makeCylinder(1.7, 3, App.Vector(12, 0, 60), App.Vector(0, 1, 0)))
    handle = Part.makeBox(100, 25, 20).cut(Part.makeBox(68, 25, 10, App.Vector(16, 0, 5)))
    for x in (8, 92):
        handle = handle.cut(Part.makeCylinder(2.75, 20, App.Vector(x, 12.5, 0)))

    duct_height = 100
    duct = joined(
        shell_box(80, 75, duct_height, 2, bottom=False),
        Part.makeBox(80, 75, 4).cut(Part.makeBox(60, 55, 4, App.Vector(10, 10, 0))),
        Part.makeBox(80, 75, 4, App.Vector(0, 0, duct_height - 4)).cut(Part.makeBox(60, 55, 4, App.Vector(10, 10, duct_height - 4))),
    )
    for z in (0, duct_height - 4):
        for x, y in ((5, 5), (75, 5), (5, 70), (75, 70)):
            duct = duct.cut(Part.makeCylinder(2.25, 4, App.Vector(x, y, z)))

    gauge = shell_box(95, 70, 28, 2).cut(Part.makeBox(8, 70, 10, App.Vector(43.5, 0, 9)))
    gauge = joined(gauge, *(Part.makeCylinder(6, 8, App.Vector(x, y, 0)) for x, y in ((7, 7), (88, 7), (7, 63), (88, 63))))
    for x, y in ((7, 7), (88, 7), (7, 63), (88, 63)):
        gauge = gauge.cut(Part.makeCylinder(2.3, 5, App.Vector(x, y, 3)))

    guard = shell_box(110, 100, 65, 2).cut(Part.makeBox(80, 100, 32, App.Vector(15, 0, 16)))
    guard = joined(guard, *(Part.makeCylinder(7, 8, App.Vector(x, y, 0)) for x, y in ((8, 8), (102, 8), (8, 92), (102, 92))))
    for x, y in ((8, 8), (102, 8), (8, 92), (102, 92)):
        guard = guard.cut(Part.makeCylinder(2.25, 8, App.Vector(x, y, 0)))

    bracket = Part.makeBox(60, 5, 70).fuse(Part.makeBox(60, 45, 5)).cut(cyl(2.6, 5, 30, 0, 50, (0, 1, 0)))
    for x in (15, 45):
        bracket = bracket.cut(Part.makeCylinder(2.75, 5, App.Vector(x, 30, 0)))
    adapter = Part.makeCone(18, 35, 35).cut(Part.makeCone(14, 31, 33, App.Vector(0, 0, 2))).cut(cyl(6.1, 35, 0, 0, 0))
    adapter = adapter.cut(Part.makeCylinder(3.3, 60, App.Vector(-30, 0, 10), App.Vector(1, 0, 0)))
    carriage = joined(
        Part.makeBox(90, 55, 8),
        Part.makeBox(90, 6, 18, App.Vector(0, 0, 6)),
        Part.makeBox(90, 6, 18, App.Vector(0, 49, 6)),
        cyl(7.0, 90, 0, 15, 12, (1, 0, 0)),
        cyl(7.0, 90, 0, 40, 12, (1, 0, 0)),
        Part.makeBox(30, 20, 8, App.Vector(30, 17.5, 6)),
    )
    carriage = one_solid(carriage.cut(cyl(4.2, 90, 0, 15, 12, (1, 0, 0))).cut(cyl(4.2, 90, 0, 40, 12, (1, 0, 0))))
    for x in (38, 52):
        carriage = carriage.cut(Part.makeCylinder(2.25, 14, App.Vector(x, 27.5, 0)))
    bezel = Part.makeBox(180, 120, 5).cut(Part.makeBox(145, 82, 5, App.Vector(17.5, 19, 0)))
    bezel = joined(bezel, *(Part.makeCylinder(6, 8, App.Vector(x, y, 0)) for x, y in ((8, 8), (172, 8), (8, 112), (172, 112))))
    for x, y in ((8, 8), (172, 8), (8, 112), (172, 112)):
        bezel = bezel.cut(Part.makeCylinder(2.1, 5, App.Vector(x, y, 3)))
    # Rectangular clamp around the 18 x 18 purchased duct.  Its 18.6 mm
    # cavity gives 0.30 mm clearance per side; the side tab mounts to profile.
    clip = Part.makeBox(26, 26, 8).cut(Part.makeBox(18.6, 18.6, 8, App.Vector(3.7, 3.7, 0)))
    clip = joined(clip, Part.makeBox(12, 26, 8, App.Vector(-12, 0, 0)))
    clip = clip.cut(Part.makeCylinder(2.25, 8, App.Vector(-6, 13, 0)))
    specs = [
        dict(id="PPR-C01", name="Sliding hopper lid", shape=lid, qty=1, material="PLA", orientation="flat", layer="0.24 mm", walls=4, infill="20%", support="no", support_contact="none", support_removal="none", fastener="1x M4x10 latch flag screw", insert="1x M4 heat-set insert OD4.6 x L5", tightening="1.2 N.m", tolerance="0.35 mm slide", mating="metal hopper rails and lid-interlock flag", order=3, edge_distance="15 mm boss centre to edge", interfaces="M4 insert bore Ø4.6 x5 blind; rail slide gap 0.35"),
        dict(id="PPR-C02", name="Anti-reach baffle chute", shape=chute, qty=1, material="PLA", orientation="outlet down", layer="0.24 mm", walls=5, infill="25%", support="ledge undersides only", support_contact="two staggered ledge undersides", support_removal="needle-nose pliers through 100x50 outlet", fastener="4x M4x12 + washer; 2x chamber M6 tie bolts through clearance holes", insert="4x M4 nyloc nuts on metal side", tightening="M4 1.2 N.m; M6 6 N.m", tolerance="0.40 mm flake path", mating="hopper and metal cutter chamber", order=4, edge_distance="8 mm boss centre; Ø14 boss", interfaces="4x Ø4.5 mount; 2x Ø6.6 tie-bolt; 100x50 outlet; staggered 72 mm ledges"),
        dict(id="PPR-C03", name="Flake bin sheet corner", shape=flake_bin, qty=4, material="PLA", orientation="end down", layer="0.28 mm", walls=4, infill="25%", support="no", support_contact="none", support_removal="none", fastener="2x M3x8 + washer + nyloc", insert="none", tightening="0.5 N.m", tolerance="0.30 mm sheet slot", mating="1 mm sheet bin and screen rails", order=7, edge_distance="12 mm hole centre", interfaces="2x Ø3.4 through on orthogonal legs"),
        dict(id="PPR-C04", name="Screen drawer handle", shape=handle, qty=1, material="PLA", orientation="back flat", layer="0.24 mm", walls=5, infill="35%", support="no", support_contact="none", support_removal="none", fastener="2x M5x16 + large washer + nyloc", insert="none", tightening="2.0 N.m", tolerance="0.25 mm", mating="metal screen", order=6, edge_distance="8 mm hole centre", interfaces="2x Ø5.5 through at 84 mm spacing"),
        dict(id="PPR-C05", name="Cooling duct segment", shape=duct, qty=2, material="ABS", orientation="end face down", layer="0.24 mm", walls=4, infill="15%", support="no", support_contact="none", support_removal="none", fastener="8x M4x12 + washer + nyloc", insert="none", tightening="1.2 N.m", tolerance="0.30 mm flange registration", mating="80 mm fan and next duct", order=13, edge_distance="5 mm hole centre", interfaces="8x Ø4.5 flange holes; 60x55 clear air opening"),
        dict(id="PPR-C06", name="Gauge enclosure half", shape=gauge, qty=2, material="ABS", orientation="outer face down", layer="0.20 mm", walls=4, infill="25%", support="slot bridge only", support_contact="8x70 optical slot roof", support_removal="break bridge strands from open housing side", fastener="4x M3x12", insert="4x M3 heat-set insert OD4.6 x L5", tightening="0.5 N.m", tolerance="0.20 mm optical slit", mating="LED/photodiode cross frame and opposite half", order=14, edge_distance="7 mm boss centre; Ø12 boss", interfaces="4x Ø4.6 x5 blind insert bores; 8 mm optical slot"),
        dict(id="PPR-C07", name="Puller pinch guard", shape=guard, qty=1, material="ABS", orientation="outer face down", layer="0.24 mm", walls=5, infill="20%", support="window bridge only", support_contact="80x32 inspection-window upper edge", support_removal="deburr from open guard interior", fastener="4x M4 captive screws", insert="4x M4 rivnuts in metal puller plate", tightening="1.2 N.m", tolerance="0.40 mm guard gap", mating="metal puller plate", order=15, edge_distance="8 mm boss centre; Ø14 boss", interfaces="4x Ø4.5 through; 80x32 guarded window"),
        dict(id="PPR-C08", name="Solid-strand guide axle bracket", shape=bracket, qty=2, material="PLA", orientation="L side", layer="0.20 mm", walls=5, infill="40%", support="yes under axle bore", support_contact="Ø5.2 axle-bore lower semicircle", support_removal="ream Ø5.2 after support removal", fastener="2x M5x16 + washer + T-nut", insert="none", tightening="2.0 N.m", tolerance="Ø5.2 +0.20/0 printed/reamed axle clearance", mating="FM-GA-01 fixed Ø5 axle and profile; 625 bearings are seated in FM-GR-01", order=16, edge_distance="15 mm hole centre", interfaces="2x Ø5.5 base holes; Ø5.2 fixed-axle bore"),
        dict(id="PPR-C09", name="Spool cone adapter", shape=adapter, qty=2, material="PLA", orientation="large face down", layer="0.20 mm", walls=5, infill="35%", support="no", support_contact="none", support_removal="ream Ø12.2 spindle bore", fastener="1x M6x30 through clamp + washer + nyloc", insert="none; metal shaft collar carries axial load", tightening="2.5 N.m", tolerance="0.30 mm spool core", mating="12 mm metal spindle and metal collar", order=18, edge_distance="radial cross-hole at z=10", interfaces="Ø12.2 axial bore; Ø6.6 radial through hole"),
        dict(id="PPR-C10", name="Traverse carriage", shape=carriage, qty=1, material="PLA", orientation="flat", layer="0.20 mm", walls=5, infill="40%", support="rod bores only", support_contact="two Ø8.4 rod-bores", support_removal="ream both bores from either x face", fastener="2x M4x16 belt-clamp screws", insert="2x M4 heat-set insert OD5.6 x L6 or through nyloc", tightening="1.2 N.m", tolerance="0.20 mm after ream", mating="donor rods and GT2 belt", order=19, edge_distance="8 mm from belt-pad edge", interfaces="2x Ø8.4 rod bores; 2x Ø4.5 clamp bores"),
        dict(id="PPR-C11", name="Control panel bezel", shape=bezel, qty=1, material="PLA", orientation="front face down", layer="0.20 mm", walls=4, infill="20%", support="no", support_contact="none", support_removal="none", fastener="4x M3x10", insert="4x M3 heat-set insert OD4.2 x L5", tightening="0.5 N.m", tolerance="0.25 mm TFT", mating="metal control panel", order=21, edge_distance="8 mm boss centre; Ø12 boss", interfaces="4x Ø4.2 x5 blind insert bores; 145x82 display opening"),
        dict(id="PPR-C12", name="Cable duct clamp", shape=clip, qty=8, material="PLA", orientation="flat", layer="0.20 mm", walls=4, infill="50%", support="no", support_contact="none", support_removal="none", fastener="1x M4x10 + profile T-nut", insert="none", tightening="1.0 N.m", tolerance="18.6 mm cavity; 0.30 mm/side", mating="20 mm profile and fixed 18x18 cable duct", order=22, edge_distance="6 mm hole centre on 12 mm side tab", interfaces="1x Ø4.5 through tab; 18.6x18.6 duct cavity"),
    ]
    # axis, start xyz, radius, length.  validation/print_interface_checks.py
    # probes these actual voids and a surrounding annulus in the final B-Rep.
    interface_bores = {
        "PPR-C01": [("z", (180, 12, 3), 2.3, 5)],
        "PPR-C02": (
            [("z", (x, y, 0), 2.25, 8) for x, y in ((8, 8), (182, 8), (8, 112), (182, 112))]
            + [("y", (x, 0, 25), 3.3, 120) for x in (35, 155)]
        ),
        "PPR-C03": [("x", (0, 12, 90), 1.7, 3), ("y", (12, 0, 60), 1.7, 3)],
        "PPR-C04": [("z", (x, 12.5, 0), 2.75, 20) for x in (8, 92)],
        "PPR-C05": [("z", (x, y, z), 2.25, 4) for z in (0, 96) for x, y in ((5, 5), (75, 5), (5, 70), (75, 70))],
        "PPR-C06": [("z", (x, y, 3), 2.3, 5) for x, y in ((7, 7), (88, 7), (7, 63), (88, 63))],
        "PPR-C07": [("z", (x, y, 0), 2.25, 8) for x, y in ((8, 8), (102, 8), (8, 92), (102, 92))],
        "PPR-C08": [("z", (x, 30, 0), 2.75, 5) for x in (15, 45)],
        "PPR-C09": [("x", (-30, 0, 10), 3.3, 60)],
        "PPR-C10": [("z", (x, 27.5, 0), 2.25, 14) for x in (38, 52)],
        "PPR-C11": [("z", (x, y, 3), 2.1, 5) for x, y in ((8, 8), (172, 8), (8, 112), (172, 112))],
        "PPR-C12": [("z", (-6, 13, 0), 2.25, 8)],
    }
    wall_probes = {
        "PPR-C01": ((100, 100, -1), (0, 0, 1), 5),
        "PPR-C02": ((-1, 75, 45), (1, 0, 0), 5),
        "PPR-C03": ((-1, 12, 30), (1, 0, 0), 3),
        "PPR-C04": ((-1, 12.5, 2), (1, 0, 0), 20),
        "PPR-C05": ((-1, 37.5, 50), (1, 0, 0), 5),
        "PPR-C06": ((-1, 35, 15), (1, 0, 0), 5),
        "PPR-C07": ((-1, 50, 50), (1, 0, 0), 5),
        "PPR-C08": ((30, 30, -1), (0, 0, 1), 8),
        "PPR-C09": ((-40, 0, 17.5), (1, 0, 0), 80),
        "PPR-C10": ((10, 27.5, -1), (0, 0, 1), 12),
        "PPR-C11": ((30, 10, -1), (0, 0, 1), 9),
        "PPR-C12": ((-13, 13, 4), (1, 0, 0), 5),
    }
    for spec in specs:
        spec["shape"] = one_solid(spec["shape"])
        spec["expected_solids"] = 1
        spec["nozzle_mm"] = 0.4
        spec["top_bottom_layers"] = 5 if spec["walls"] >= 5 else 4
        spec["brim"] = "5 mm" if spec["orientation"] in ("end down", "end face down", "L side") else "none"
        spec["minimum_wall_mm"] = 1.6 if spec["walls"] == 4 else 2.0
        spec["interface_bores"] = interface_bores[spec["id"]]
        spec["wall_probe"] = wall_probes[spec["id"]]
    return specs


def flake_bin_sheet_shape(corner_shape):
    """1 mm removable bin with reliefs matching the four PPR-C03 bridges."""
    shell = shell_box(185, 175, 115, 1)
    poses = (
        ((-2.0, -2.0, -3.0), 0),
        ((187.0, -2.0, -3.0), 90),
        ((-2.0, 177.4, -3.0), -90),
        ((187.0, 177.4, -3.0), 180),
    )
    for location, angle in poses:
        corner = corner_shape.copy()
        corner.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)
        corner.translate(App.Vector(*location))
        shell = shell.cut(corner)
    return one_solid(shell)


def drive_guard_shape():
    guard = open_front_sheet_shell(165, 48, 190, 1.0)
    for x in (20, 68):
        guard = guard.cut(
            Part.makeCylinder(13, 4, App.Vector(x, 45, 55), App.Vector(0, 1, 0))
        )
    return one_solid(guard)


def hot_shield_shape():
    shield = three_panel_tunnel(335, 75, 85, 2)
    return one_solid(shield.cut(Part.makeCylinder(25, 2, App.Vector(314, 37, 83))))


def machine_fabrication_parts():
    """Non-shredder machine parts that require stock cutting or fabrication."""
    printed = {item["id"]: item["shape"] for item in print_parts()}
    transfer_length = (4.0 ** 2 + 73.0 ** 2 + 76.0 ** 2) ** 0.5
    return [
        dict(id="IN-HOP-01", name="Refillable input hopper", shape=cylindrical_hopper(100, 150, 60, 20), qty=1, material="2 mm 5052-H32 aluminum", process="roll cone/cylinder + TIG weld + deburr", critical="OD200 x straight150 + cone60; outlet Ø40; wall 2.0; lid rail datum flatness 0.5; leak-free dry-flake seams"),
        dict(id="FD-BIN-01", name="Removable flake bin", shape=flake_bin_sheet_shape(printed["PPR-C03"]), qty=1, material="1 mm PP or 304 sheet", process="laser/knife cut panels + thermal weld or fold/rivet", critical="185 x175 x115 outside; PPR-C03 corner reliefs control; no inward burr/dead pocket; removable without cutter disassembly"),
        dict(id="FD-HOP-01", name="Sealed feed hopper", shape=cylindrical_hopper(78, 145, 55, 16), qty=1, material="2 mm 304 stainless", process="roll cone/cylinder + TIG weld + gasketed lid", critical="OD156 x straight145 + cone55; outlet Ø32; wall2.0; leak test; lid gasket limits moisture ingress"),
        dict(id="FD-TRN-01", name="Sealed transfer tube", shape=Part.makeCylinder(16, transfer_length).cut(Part.makeCylinder(14, transfer_length)), qty=1, material="304 tube OD32 x2", process="tube cut + socket fit + TIG tack/weld", critical=f"centreline length {transfer_length:.2f}; OD32, ID28; clock after dry assembly; both sockets >=8 engagement"),
        dict(id="FD-MET-01", name="Metering feeder housing", shape=feeder_housing_shape(), qty=1, material="304 stainless", process="turn tube/flanges + drill", critical="Ø36/Ø32 x105; flanges Ø48 x3; 4xØ4.5 PCD40 each end; rotor radial clearance 0.20 nominal"),
        dict(id="FD-MET-02", name="Six-pocket metering rotor", shape=feeder_metering_rotor_shape(), qty=1, material="POM-C or 304", process="turn + 3-axis mill six pockets", critical="OD31.60 -0.05/0 x8; bore Ø5.2; 6xØ8 pockets PCD20; balance and deburr; Gate-2 sets volumetric coefficient"),
        dict(id="FD-MET-03", name="Metering feeder shaft", shape=Part.makeCylinder(2.5, 110), qty=1, material="304 shaft", process="cut/face Ø5 stock", critical="Ø5 h8 x110; straightness 0.10; retain rotor with removable cross pin or two collars after donor motor measurement"),
        dict(id="EX-THR-01", name="Extruder thrust plate", shape=thrust_plate_shape(), qty=1, material="12 mm S45C or SS400", process="laser rough + bore/seat finish", critical="12 x95 x105; passage Ø17.2; thrust seat Ø30.2 x5; 4xØ6.6; seat axis square 0.05; metal-to-profile load path"),
        dict(id="EX-SH-01", name="Three-panel hot-zone shield", shape=hot_shield_shape(), qty=1, material="2 mm 5052 aluminum", process="laser + two 90deg bends; bond PE", critical="335 x75 x85; open bottom/ends; feeder opening Ø50 at X314/Y37; >=10 mm ABS-duct gap; edge hem/deburr"),
        dict(id="DRV-GD-01", name="Interlocked drive guard", shape=drive_guard_shape(), qty=1, material="1 mm galvanized steel", process="laser + brake + service-cover hardware", critical="165 x48 x190; two Ø26 shaft clearances at X20/68,Z55; open service face; positive-opening interlock flag; PE bond"),
        dict(id="FM-PL-01", name="Puller side plate", shape=puller_plate_shape(), qty=2, material="10 mm 6061-T6", process="waterjet + ream", critical="100 x10 x40; 2xØ8.2 roller axes 40.00 apart; 4xØ4.5 guard mounts; matched pair axis position ±0.05"),
        dict(id="FM-RL-01", name="Puller roller", shape=puller_roller_shape(), qty=2, material="aluminum hub + replaceable silicone sleeve", process="turn + bore", critical="finished OD40 x60; bore Ø8.2; TIR <=0.05; Shore A 50-70 sleeve; matched OD within 0.05"),
        dict(id="FM-AX-01", name="Puller roller spindle", shape=Part.makeCylinder(4, 80), qty=2, material="Ø8 h6 stainless shaft", process="cut/face + collar flats", critical="Ø8 h6 x80; TIR0.03; two metal collars; driven spindle interface remains donor-specific"),
        dict(id="FM-GR-01", name="Solid-strand guide roller", shape=guide_roller_shape(), qty=1, material="POM-C or 6061", process="turn + bearing-seat bore", critical="OD36 x20; 2x Ø16 H7 x5.1-deep 625 seats; Ø12 through relief; seat shoulders square 0.05; groove-free polished surface Ra<=1.6; roller only after puller"),
        dict(id="FM-GA-01", name="Guide roller fixed axle", shape=Part.makeCylinder(2.5, 30), qty=1, material="Ø5 h6 stainless shaft", process="cut/face + E-clip grooves or collars", critical="Ø5 h6 x30; two E-clips/collars outside PPR-C08; bearing inner-ring clamp must not preload outer rings; no printed axle"),
        dict(id="SP-DA-01", name="Dancer arm", shape=dancer_arm_shape(0, (0, 0, 0)), qty=1, material="8 mm 6061-T6", process="waterjet + ream", critical="100 mm pivot centres; 12 mm arm; 2xØ8.2; edge R2; full -25..+25deg motion"),
        dict(id="SP-AX-01", name="Dancer pivot/roller axles", shape=Part.makeCylinder(4, 28), qty=2, material="Ø8 h6 stainless shaft", process="cut/face + collars", critical="Ø8 h6 x28; metal collars; one pivot and one end roller axle"),
        dict(id="SP-RL-01", name="Dancer end roller", shape=Part.makeCylinder(10, 20).cut(Part.makeCylinder(4.1, 20)), qty=1, material="POM-C", process="turn + bore", critical="OD20 x20; bore Ø8.2; free rotation under 0.2-1.0 N filament tension"),
        dict(id="SP-SH-01", name="Spool spindle", shape=Part.makeCylinder(6, 143), qty=1, material="Ø12 h6 S45C", process="cut/turn faces + collar flats", critical="Ø12 h6 x143; straightness0.05; two 6001 bearings; axial collars carry spool load"),
        dict(id="SP-BP-01", name="Spool 6001 bearing plate", shape=spool_bearing_plate_shape(), qty=2, material="5 mm 6061-T6", process="waterjet + bearing-seat finish", critical="105 x5 x60; bearing centre X30, Ø28.2; 4xØ5.5 bearing block + 2xØ5.5 profile tab; matched axis position ±0.05; bearing outer ring retained by metal washer/clip"),
        dict(id="SP-MM-01", name="Universal NEMA17-class spool motor plate", shape=spool_motor_mount_shape(), qty=1, material="6 mm 6061-T6", process="laser/waterjet + drill", critical="101 x6 x52; motor centre X26, Ø24; 4xØ4.5 at 31 mm square; 2xØ5.5 profile tab; actual donor shaft and body measurement required before coupling release"),
        dict(id="SP-TR-01", name="Traverse rod end plate", shape=traverse_end_plate_shape(), qty=2, material="5 mm 6061-T6", process="waterjet + ream", critical="5 x50 x40; two Ø8.2 at 25 mm spacing; 2xØ5.5 mount; matched pair and rod parallelism <=0.10/160"),
        dict(id="SP-DS-01", name="Dancer pivot support plate", shape=dancer_support_plate_shape(), qty=1, material="8 mm 6061-T6", process="waterjet + ream", critical="36 x8 x80; pivot Ø8.2 at X18/Z45; 2xØ5.5 foot mounts; metal support carries spring/tension load"),
        dict(id="CT-ENC-01", name="Control-panel sheet enclosure", shape=open_front_sheet_shell(190, 35, 190, 2), qty=1, material="2 mm 5052 aluminum", process="laser + brake + PE stud", critical="190 x35 x190; service-open face; PPR-C11 bezel datum; M4 profile mounts; segregate heater/motor and signal wiring"),
    ]


def assembly_objects(exploded=False):
    objects = []
    def add(name, shape, color, group, material="mixed", classification="manufactured_or_stock", mass_override_kg=None, evidence=""):
        if exploded:
            offsets = {"input": (-35, 0, 35), "shredder": (-20, 0, 10), "feed": (25, 0, 25), "extruder": (0, -40, 0), "forming": (-25, -20, -25), "spooler": (35, 35, -10), "control": (30, -35, 10), "frame": (0, 0, 0)}
            dx, dy, dz = offsets.get(group, (0, 0, 0))
            shape = shape.copy(); shape.translate(App.Vector(dx, dy, dz))
        objects.append(dict(name=name, shape=shape, color=color, group=group, material=material, classification=classification,mass_override_kg=mass_override_kg,evidence=evidence))

    steel = (88, 101, 112); aluminum = (165, 177, 184); orange = (225, 116, 55)
    blue = (47, 122, 163); green = (69, 151, 97); purple = (119, 89, 145); red = (185, 54, 54)
    printed={item["id"]:item["shape"] for item in print_parts()}

    def printed_at(part_id,location,rotation=None):
        shape=printed[part_id].copy()
        if rotation:
            axis,angle=rotation; shape.rotate(App.Vector(0,0,0),App.Vector(*axis),angle)
        shape.translate(App.Vector(*location)); return shape
    # Frame: butt-jointed 20-series members.  No two profile solids occupy the
    # same volume; columns sit between bottom/top rectangles, and each tier is
    # closed by side Y rails so the centre crossrail is not floating.
    for x in (0, 450):
        for y in (0, 680): add(f"FrameColumn{x}_{y}", box(x, y, 20, 20, 20, 890), aluminum, "frame", "20x20 profile L890")
    for z in (0, 910):
        for y in (0, 680): add(f"FrameX{z}_{y}", box(20, y, z, 430, 20, 20), aluminum, "frame", "20x20 profile L430")
        for x in (0, 450): add(f"FrameY{z}_{x}", box(x, 20, z, 20, 660, 20), aluminum, "frame", "20x20 profile L660")
    for z in (320, 500):
        for x in (0, 450):
            if z == 500:
                add(f"FrameTierY{z}_{x}", box(x, 20, z, 20, 660, 40), aluminum, "frame", "20x40 profile L660; 40 mm vertical")
            else:
                add(f"FrameTierY{z}_{x}", box(x, 20, z, 20, 660, 20), aluminum, "frame", "20x20 profile L660")
        add(f"MidRail{z}", box(20, 270, z, 430, 20, 20), aluminum, "frame", "20x20 profile L430")
    # The puller guard occupies y=300..400 at the base.  The adjacent rails
    # stop 5 mm short of the guard instead of passing through its shell.
    for y in (275, 405, 440, 608):
        add(f"FrameBottomCross{y}", box(20, y, 0, 430, 20, 20), aluminum, "frame", "20x20 profile L430")
    add("FrameSpoolColumnFront", box(410,480,20,20,20,300), aluminum, "frame", "20x20 profile L300")
    add("FrameSpoolColumnRear", box(410,588,20,20,20,300), aluminum, "frame", "20x20 profile L300")
    add("FrameSpoolTopRail", box(410,290,320,20,318,20), aluminum, "frame", "20x20 profile L318")
    add("FrameTraversePostLeft", box(220,405,20,20,20,280), aluminum, "frame", "20x20 profile L280")
    add("FrameTraversePostRight", box(410,405,20,20,20,280), aluminum, "frame", "20x20 profile L280")

    hopper = cylindrical_hopper(100, 150, 60, 20); hopper.translate(App.Vector(125, 395, 750))
    add("MetalHopper", hopper, aluminum, "input", "2 mm sheet metal")
    add("PPR-C01_SlidingLid", printed_at("PPR-C01",(30,290,900)), blue, "input", "PLA")
    add("PPR-C02_AntiReach", printed_at("PPR-C02",(35,331,620)), blue, "input", "PLA")

    # Shredder metal load path.
    def placed_cutter_plate(y_max):
        plate = bearing_side_plate()
        plate.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
        plate.translate(App.Vector(55, y_max, 535))
        return plate
    add("CutterPlateFront", placed_cutter_plate(327), steel, "shredder", "CUT-03 steel")
    add("CutterPlateRear", placed_cutter_plate(467), steel, "shredder", "CUT-03 steel")
    for cx in (105, 153):
        shaft_y = 278 if cx == 105 else 258
        shaft = cutter_shaft(); shaft.translate(App.Vector(cx, shaft_y, 590))
        add(f"Shaft{cx}", shaft, steel, "shredder", "S45C, three 6 mm keyway zones")
        for i in range(6):
            # Assembly LOD preserves the cycloidal equation and envelope while
            # CUT-01 fabrication export retains the dense 18/8 sampling.
            d = hook_disc(capture_samples=6, relief_samples=3)
            axial_offset = 0.0 if cx == 105 else 6.5
            if cx == 153: d.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 25.714)
            d.translate(App.Vector(cx, 339 + axial_offset + i * 13, 590))
            add(f"Hook{cx}_{i}", d, orange, "shredder", "tool steel")
        for y in (315, 455):
            bearing = cyl(21, 12, cx, y, 590, (0, 1, 0)).cut(cyl(10.1, 12, cx, y, 590, (0, 1, 0)))
            add(f"Bearing{cx}_{y}", bearing, purple, "shredder", "6004")
    for x in (70, 190):
        for z in (550, 645): add(f"M6Fastener{x}_{z}", cyl(3, 164, x, 307, z, (0, 1, 0)), orange, "shredder", "M6 steel")
    # Assembly LOD uses the perforated plate envelope; CUT-04 export contains
    # every 5 mm aperture and is the fabrication source of truth.
    add("Screen", box(60, 330, 555, 135, 120, 3), green, "shredder", "CUT-04 3 mm 304 stainless, 5 mm holes")
    add("PPR-C04_ScreenHandle",printed_at("PPR-C04",(78,288,545)),blue,"shredder","PLA")

    # Interchangeable geared-DC interface: a generic #35 chain ratio drives the
    # right shaft; a functional-spec M3 Z16 pair fixes counter-rotation/phase.
    drive_gear = spur_phase_gear(module=3.0, teeth=16, thickness=18.0, bore=20.2)
    for cx in (105, 153):
        gear = drive_gear.copy()
        if cx == 153:
            gear.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 180.0 / 16.0)
        gear.translate(App.Vector(cx, 471, 590))
        add(f"PhaseGear{cx}", gear, purple, "shredder", "generic M3 Z16 20deg face18 steel or DRV-03 laminate")
    cutter_sprocket = chain_sprocket_shape(30, 20.2, 12); cutter_sprocket.rotate(App.Vector(),App.Vector(1,0,0),-90); cutter_sprocket.translate(App.Vector(153,258,590))
    motor_sprocket = chain_sprocket_shape(12, 12.2, 10); motor_sprocket.rotate(App.Vector(),App.Vector(1,0,0),-90); motor_sprocket.translate(App.Vector(153,258,680))
    add("CutterSprocket30T", cutter_sprocket, purple, "shredder", "#35 30T selected, DRV-02 bolt-on hub")
    add("MotorSprocket12T", motor_sprocket, purple, "shredder", "#35 12T on DRV-F01 outer hub")
    add("ChainTightSide",box(121,260,590,4,8,90),orange,"shredder","#35 chain conservative solid LOD", "purchased_reference_lod")
    add("ChainSlackSide",box(181,260,590,4,8,90),orange,"shredder","#35 chain conservative solid LOD", "purchased_reference_lod")
    drive_guard = drive_guard_shape()
    drive_guard.translate(App.Vector(85, 240, 535))
    # The universal metal motor plate forms the closure at this bulkhead.  A
    # clearance slit prevents impossible coincident sheet/plate volume while
    # the bolted hem maintains anti-reach protection in the real assembly.
    drive_guard = drive_guard.cut(box(64,250,589,182,8,142))
    add("DriveGuard", drive_guard, blue, "shredder", "1 mm grounded sheet + interlocked service cover")
    # Exact reference geometry: GMP60-60127-2460 with 47:1 gearbox.  The
    # requested 42GP-775 adapter remains orderable, but its official rated
    # torque fails the continuous cutter target and is not the selected drive.
    reference_motor = gmp60_60127_reference_shape(); reference_motor.rotate(App.Vector(),App.Vector(1,0,0),-90); reference_motor.translate(App.Vector(153,59,680))
    add("DriveMotorGMP60Reference", reference_motor, red, "shredder", "TT Motor GMP60-60127-2460, ratio47, 24V", "purchased_reference_envelope", evidence="official GMP60-6097/60127 drawing: motor127 + gearbox59 + shaft25.8, pilot Ø32x4.85, Ø60 body")
    adapter60=motor_adapter_gmp60_shape(); adapter60.rotate(App.Vector(),App.Vector(1,0,0),90); adapter60.translate(App.Vector(113,251,640))
    add("DriveAdapterGMP60", adapter60, steel, "shredder", "DRV-A60 6 mm steel, Ø32.2 boss and 4xM5 PCD45")
    motor_plate = motor_mount_plate()
    motor_plate.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
    motor_plate.translate(App.Vector(65, 257, 590))
    add("MotorMountPlate", motor_plate, steel, "shredder", "CUT-07/DRV-01 6 mm steel; DRV-A60 bears directly on its front face")
    retainer = bearing_retainer_plate()
    front_retainer = retainer.copy(); front_retainer.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90); front_retainer.translate(App.Vector(55, 315, 535))
    rear_retainer = retainer.copy(); rear_retainer.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90); rear_retainer.translate(App.Vector(55, 469, 535))
    add("BearingRetainerFront", front_retainer, steel, "shredder", "CUT-08 2 mm steel")
    add("BearingRetainerRear", rear_retainer, steel, "shredder", "CUT-08 2 mm steel")
    corner_poses = (
        ((33.0, 298.0, 427.0), 0),
        ((222.0, 298.0, 427.0), 90),
        ((33.0, 477.4, 427.0), -90),
        ((222.0, 477.4, 427.0), 180),
    )
    corner_shapes = [printed_at("PPR-C03", location, ((0, 0, 1), angle)) for location, angle in corner_poses]
    flake = flake_bin_sheet_shape(printed["PPR-C03"]); flake.translate(App.Vector(35, 300, 430))
    add("FlakeBin", flake, blue, "feed", "1 mm PP sheet with PPR-C03 top corner reliefs")
    for index,corner in enumerate(corner_shapes):
        add(f"PPR-C03_FlakeCorner{index}",corner,blue,"feed","PLA")
    feed = cylindrical_hopper(78, 145, 55, 16); feed.translate(App.Vector(350, 420, 635))
    feed = one_solid(feed.cut(cyl(1.6,5.0,350,341,748,(0,1,0))))
    add("SealedFeedHopper", feed, aluminum, "feed", "2 mm sheet metal")
    ptc_spreader=hopper_ptc_spreader_shape(); ptc_spreader.translate(App.Vector(290,338,690))
    add("HopperPTCSpreader",ptc_spreader,aluminum,"feed","TH-PTC-01 3 mm aluminum spreader")
    for index,(x,z) in enumerate(((298,696),(337,696),(298,721),(337,721)),start=1):
        add(f"HopperPTC{index}",box(x,333,z,35,5,21),orange,"feed","24 V 35x21x5 self-regulating PTC; power receipt-test required","purchased_reference_envelope")
    ptc_clamp=hopper_ptc_clamp_shape(); ptc_clamp.translate(App.Vector(290,331,690))
    add("HopperPTCClamp",ptc_clamp,steel,"feed","TH-PTC-02 2 mm grounded metal keeper")
    hopper_probe=k_type_probe_shape(insertion_length=4.0); hopper_probe.rotate(App.Vector(),App.Vector(1,0,0),-90); hopper_probe.translate(App.Vector(350,341,748))
    add("TemperatureProbeT5",hopper_probe,purple,"feed","T5 ungrounded K-type probe; MAX6675 T- common reference at receiver only")
    add("HopperThermalFuse",box(410,331,705,20,6,8),red,"feed","independent one-shot thermal fuse clamped at spreader edge")
    transfer = hollow_tube_between((354, 347, 504), (350, 420, 580), 16, 2)
    add("FeedTransferChute", transfer, aluminum, "feed", "2 mm sealed 304 transfer tube")
    # Vertical six-pocket metering disc feeder.  Gate-2 determines its RPM and
    # volumetric coefficient; the housing/rotor are real removable solids.
    feeder_housing = feeder_housing_shape(); feeder_housing.translate(App.Vector(354, 347, 399))
    feeder_rotor = feeder_metering_rotor_shape(); feeder_rotor.translate(App.Vector(354, 347, 402))
    feeder_shaft = Part.makeCylinder(2.5, 110, App.Vector(354, 347, 402))
    add("FeederHousing", feeder_housing, steel, "feed", "304 stainless Ø36/Ø32 housing")
    add("FeederRotor", feeder_rotor, orange, "feed", "POM or 304 six-pocket metering disc")
    add("FeederShaft", feeder_shaft, steel, "feed", "Ø5 stainless shaft; NEMA17 donor drive")

    # Horizontal extruder and fully connected 90-degree metal down-die.
    # The RFQ screw/barrel solids are also the assembly solids.  Local Z runs
    # from rear to die; rotate it to global -X so the 24 mm tip setback is real.
    from manufacturing import extruder_barrel, extruder_screw
    screw = extruder_screw(); screw.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -90); screw.translate(App.Vector(435, 347, 382))
    barrel = one_solid(extruder_barrel()); barrel.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -90); barrel.translate(App.Vector(375, 347, 382))
    thrust = thrust_plate_shape(); thrust.translate(App.Vector(380, 300, 330))
    add("ThrustPlate", thrust, steel, "extruder", "EX-THR-01 12 mm steel")
    add("Screw", screw, orange, "extruder", "EX-SCR-01 SCM440 QT + gas nitride")
    add("Barrel", barrel, steel, "extruder", "EX-BAR-01 SCM440 QT + gas nitride")
    for zone,(z0,sensor_z) in enumerate(((45.0,95.0),(115.0,170.0),(190.0,245.0)),start=1):
        band=mica_band_heater_shape(); band.translate(App.Vector(0,0,z0)); band.rotate(App.Vector(),App.Vector(0,1,0),-90); band.translate(App.Vector(375,347,382))
        add(f"BarrelBandHeaterZ{zone}",band,orange,"extruder",f"24 V 100 W custom mica band ID34.00 W45 zone {zone}","purchased_reference_envelope")
        probe=k_type_probe_shape(); probe.rotate(App.Vector(),App.Vector(1,0,0),90); probe.translate(App.Vector(375-sensor_z,364,382))
        add(f"TemperatureProbeT{zone}",probe,purple,"extruder",f"T{zone} ungrounded K-type Ø3 probe in EX-BAR-01 blind bore B+{sensor_z:.0f}; MAX6675 T- common reference")
    add("BarrelThermalFuse",box(263,343,401.5,22,8,12),red,"extruder","independent 300 C one-shot fuse on metal clamp in inter-zone gap")
    shield = hot_shield_shape(); shield.translate(App.Vector(40, 310, 340))
    for x,z,radius in ((315,382,3.0),(240,382,3.0),(165,382,3.0),(280,382,2.0),(205,382,2.0),(130,382,2.0),(62.5,397,2.0)):
        shield=shield.cut(cyl(radius,75,x,310,z,(0,1,0)))
    add("HotShield", shield, aluminum, "extruder", "grounded sheet")
    drive = box(392, 310, 340, 55, 75, 85).cut(
        Part.makeCylinder(18, 55, App.Vector(392, 347, 382), App.Vector(1, 0, 0))
    )
    add("ExtruderDrive", one_solid(drive), red, "extruder", "donor maximum housing envelope with output-axis clearance; exact adapter pending", "unverified_donor_envelope", evidence="label/shaft/mount measurement required before adapter release")
    die_shift = App.Vector(54.5, 347, 382)
    for name, shape, material in (
        ("DownDieBody", down_die_body(), "SCM440 QT + gas nitride"),
        ("DownDieBreaker", down_die_breaker_plate(), "304 stainless"),
        ("DownDieInsert", down_die_insert(), "17-4PH H900 stainless"),
        ("DownDieRelief", down_die_relief_retainer(), "304 stainless t1.5 sacrificial"),
        ("DownDieGasket", down_die_copper_gasket(), "annealed copper t0.5"),
    ):
        shape = shape.copy(); shape.translate(die_shift)
        add(name, shape, orange, "extruder", material)
    die_heater=die_cartridge_heater_shape(); die_heater.translate(App.Vector(74.5,347,400))
    add("DieCartridgeHeater",die_heater,red,"extruder","24 V 60 W Ø6 x38 cartridge in Ø6.05 H7 reamed through bore","purchased_reference_envelope")
    die_probe=k_type_probe_shape(insertion_length=10.0); die_probe.rotate(App.Vector(),App.Vector(1,0,0),-90); die_probe.translate(App.Vector(62.5,328,397))
    add("TemperatureProbeT4",die_probe,purple,"extruder","T4 ungrounded K-type Ø3 probe in EX-DIE-01 Ø3.20 blind12 bore; MAX6675 T- common reference")
    add("DieThermalFuse",box(72,345,407,18,7,10),red,"extruder","independent die thermal fuse on metal clamp above die body")
    # High-temperature leads enter a fixed metal duct; flexible sections stay
    # outside the band clamp screws and the screw-withdrawal axis.
    for index,x in enumerate((315,240,165),start=1):
        add(f"HeaterLeadZ{index}",cyl(2,55,x,368,382,(0,1,0)),purple,"extruder","fiberglass/silicone high-temperature paired lead")
    cable_duct=open_front_sheet_shell(250,18,18,1); cable_duct.translate(App.Vector(120,418,374))
    add("HeaterCableDuct",cable_duct,aluminum,"extruder","grounded 18x18 metal duct; heater/sensor separation partition")
    cable_bridge_x=open_front_sheet_shell(64,18,18,1); cable_bridge_x.translate(App.Vector(370,418,374))
    add("HeaterCableDuctBridgeX",cable_bridge_x,aluminum,"extruder","grounded 18x18 metal duct; fixed X bridge")
    cable_bridge_y=open_front_sheet_shell(232,18,18,1); cable_bridge_y.rotate(App.Vector(),App.Vector(0,0,1),90); cable_bridge_y.translate(App.Vector(443,418,374))
    add("HeaterCableDuctBridgeY",cable_bridge_y,aluminum,"extruder","grounded 18x18 metal duct; fixed Y bridge to vertical service duct")

    # One shared straight soft-strand path.  Direction changes only after the
    # puller; the X and Y shadow modules are sequential and orthogonal.
    add("PPR-C05_CoolingDuctLower",printed_at("PPR-C05",(34.5,309.5,130)),blue,"forming","ABS")
    add("PPR-C05_CoolingDuctUpper",printed_at("PPR-C05",(34.5,309.5,230)),blue,"forming","ABS")
    add("PPR-C06_GaugeX",printed_at("PPR-C06",(27.0,312.0,96)),purple,"forming","ABS/optics")
    gauge_y=printed["PPR-C06"].copy(); gauge_y.rotate(App.Vector(0,0,0),App.Vector(0,0,1),90); gauge_y.translate(App.Vector(109.5,299.5,68))
    add("PPR-C06_GaugeY",gauge_y,purple,"forming","ABS/optics")
    front_plate = puller_plate_shape(); front_plate.translate(App.Vector(24.5, 310, 15))
    rear_plate = puller_plate_shape(); rear_plate.translate(App.Vector(24.5, 380, 15))
    add("PullerPlateFront", front_plate, steel, "forming", "PL-01 10 mm metal")
    add("PullerPlateRear", rear_plate, steel, "forming", "PL-01 10 mm metal")
    for x in (54.5, 94.5):
        roller = puller_roller_shape(); roller.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90); roller.translate(App.Vector(x, 320, 35))
        add(f"PullerRoll{x}", roller, green, "forming", "PL-02 Ø40 x60 roller, Ø8.2 bore")
        add(f"PullerSpindle{x}", cyl(4,80,x,310,35,(0,1,0)), steel, "forming", "FM-AX-01 Ø8 h6 x80 metal spindle")
    add("PPR-C07_PullerGuard",printed_at("PPR-C07",(20,300,0)),blue,"forming","ABS")

    # Solid guide, dancer/traverse and maximum spool motion.
    guide = guide_roller_shape(); guide.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90); guide.translate(App.Vector(175, 375, 90))
    add("GuideRoller", guide, green, "spooler", "FM-GR-01 Ø36 x20 roller, two Ø16 H7 bearing seats")
    add("GuideRollerAxle", cyl(2.5,30,175,370,90,(0,1,0)), steel, "spooler", "FM-GA-01 Ø5 h6 x30 fixed metal axle")
    add("GuideBearingFront", cyl(8,5,175,375,90,(0,1,0)).cut(cyl(2.5,5,175,375,90,(0,1,0))), purple, "spooler", "625-2RS 5x16x5")
    add("GuideBearingRear", cyl(8,5,175,390,90,(0,1,0)).cut(cyl(2.5,5,175,390,90,(0,1,0))), purple, "spooler", "625-2RS 5x16x5")
    front_bracket = printed["PPR-C08"].copy().mirror(App.Vector(0,0,0), App.Vector(0,1,0)); front_bracket.translate(App.Vector(145,375,40))
    add("PPR-C08_GuideBracketFront",front_bracket,blue,"spooler","PLA")
    add("PPR-C08_GuideBracketRear",printed_at("PPR-C08",(145,395,40)),blue,"spooler","PLA")
    add("DancerArm", dancer_arm_shape(0), aluminum, "spooler", "metal")
    dancer_support = dancer_support_plate_shape(); dancer_support.translate(App.Vector(170,440,70))
    add("DancerSupportPlate", dancer_support, aluminum, "spooler", "SP-DS-01 8 mm metal")
    add("DancerSupportPost", box(170,440,20,20,20,50), aluminum, "spooler", "SP-DP-01 20x20 metal support")
    add("DancerPivotAxle", cyl(4,16,188,444,115,(0,1,0)), steel, "spooler", "SP-AX-01 Ø8 h6 metal axle")
    dancer_roller = Part.makeCylinder(10,20,App.Vector(288,428,115),App.Vector(0,1,0)).cut(Part.makeCylinder(4.1,20,App.Vector(288,428,115),App.Vector(0,1,0)))
    add("DancerEndRoller", dancer_roller, green, "spooler", "SP-RL-01 POM roller")
    add("DancerEndAxle", cyl(4,36,288,424,115,(0,1,0)), steel, "spooler", "SP-AX-01 Ø8 h6 metal axle")
    add("Spool", cyl(100, 73, 335, 500, 175, (0, 1, 0)), (223, 187, 104), "spooler", "1 kg spool full envelope", "purchased_reference_envelope", evidence="generic 1 kg spool maximum envelope; actual spool must fit PPR-C09")
    add("SpoolCore", cyl(26, 73, 335, 500, 175, (0, 1, 0)), steel, "spooler", "spool core reference", "purchased_reference_lod")
    add("SpoolSpindle", cyl(6, 143, 335, 465, 175, (0, 1, 0)), steel, "spooler", "SP-01 Ø12 metal spindle")
    front_bearing_plate = spool_bearing_plate_shape(); front_bearing_plate.translate(App.Vector(305,487,145))
    rear_bearing_plate = spool_bearing_plate_shape(); rear_bearing_plate.translate(App.Vector(305,588,145))
    add("SpoolBearingPlateFront", front_bearing_plate, aluminum, "spooler", "SP-BP-01 5 mm metal")
    add("SpoolBearingPlateRear", rear_bearing_plate, aluminum, "spooler", "SP-BP-01 5 mm metal")
    add("SpoolBearingFront", cyl(14,8,335,492,175,(0,1,0)).cut(cyl(6.1,8,335,492,175,(0,1,0))), purple, "spooler", "6001-2RS bearing")
    add("SpoolBearingRear", cyl(14,8,335,580,175,(0,1,0)).cut(cyl(6.1,8,335,580,175,(0,1,0))), purple, "spooler", "6001-2RS bearing")
    add("PPR-C09_SpoolAdapterFront",printed_at("PPR-C09",(335,500,175),((1,0,0),-90)),blue,"spooler","PLA")
    add("PPR-C09_SpoolAdapterRear",printed_at("PPR-C09",(335,573,175),((1,0,0),90)),blue,"spooler","PLA")
    add("TraverseRodA", cyl(4, 160, 245, 435, 280, (1, 0, 0)), aluminum, "spooler", "donor Ø8 rod")
    add("TraverseRodB", cyl(4, 160, 245, 460, 280, (1, 0, 0)), aluminum, "spooler", "donor Ø8 rod")
    left_traverse_plate = traverse_end_plate_shape(); left_traverse_plate.translate(App.Vector(240,425,260))
    right_traverse_plate = traverse_end_plate_shape(); right_traverse_plate.translate(App.Vector(405,425,260))
    add("TraverseEndPlateLeft", left_traverse_plate, aluminum, "spooler", "SP-TR-01 5 mm metal")
    add("TraverseEndPlateRight", right_traverse_plate, aluminum, "spooler", "SP-TR-01 5 mm metal")
    add("PPR-C10_TraverseCarriage",printed_at("PPR-C10",(270,420,268)),blue,"spooler","PLA")

    spool_motor_plate = spool_motor_mount_shape(); spool_motor_plate.translate(App.Vector(309,602,149))
    add("SpoolMotorMount", spool_motor_plate, aluminum, "spooler", "SP-MM-01 universal metal plate")
    add("SpoolMotorEnvelope", box(314,612,154,42,48,42), red, "spooler", "unverified donor NEMA17-class envelope", "unverified_donor_envelope", evidence="label, body, shaft, current and mounting measurement required before coupling release")

    panel = open_front_sheet_shell(190, 35, 190, 2); panel.translate(App.Vector(255, 35, 330))
    add("ControlPanel", panel, blue, "control", "CT-01 2 mm sheet enclosure")
    add("PPR-C11_ControlBezel",printed_at("PPR-C11",(260,43,365),((1,0,0),90)),blue,"control","PLA")
    add("PSU", box(275, 80, 200, 160, 180, 90), red, "control", "24 V 600 W unverified maximum envelope", "unverified_donor_envelope", evidence="label and measured L/W/H required before bracket release")
    add("CableDuct", box(425, 650, 80, 18, 18, 750), purple, "control", "18 x18 fixed vertical purchased duct envelope", "purchased_reference_envelope")
    for index,z in enumerate(range(100,821,100)):
        # Cavity x/y = 3.7..22.3, centered around the fixed duct envelope.
        add(f"PPR-C12_CableClip{index}",printed_at("PPR-C12",(421.3,646.3,z)),blue,"control","PLA")
    return objects


def review_keepout_objects():
    """Non-manufacturing motion/service volumes, quarantined from exports."""
    return [
        dict(name="KO_ChainMotion", shape=box(120, 255, 555, 66, 18, 160), purpose="chain sweep and guard clearance"),
        dict(name="KO_DancerSweep", shape=cyl(115, 12, 188, 446, 115, (0, 1, 0)), purpose="full dancer arm radius including end roller, -25 to +25 degrees"),
        dict(name="KO_TraverseMotion", shape=box(270, 420, 268, 170, 55, 24), purpose="90 mm carriage over full 80 mm traverse stroke"),
        dict(name="KO_ScrewService", shape=box(70, 300, 330, 310, 95, 105), purpose="removable screw withdrawal path"),
    ]
