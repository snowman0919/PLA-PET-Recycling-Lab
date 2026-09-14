"""Closed-solid source geometry for the compact v0.5 machine.

Review keep-outs are emitted by :func:`review_keepout_objects` and are never
part of the fabrication assembly or printable exports.
"""

from __future__ import annotations

import math
import json
from pathlib import Path

import FreeCAD as App
import Part
from traverse_revision import SPEC as TRAVERSE, carriage_shape, end_plate_shape, rotated_at
from shaft_retention import traverse_collar_rows


ROOT = Path(__file__).resolve().parents[3]
LID = json.loads((ROOT / "cad/parameters/baseline.json").read_text())["input_lid"]


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
    """100 x 40 x10 plate: one fixed axle and one eccentric-bush seat."""
    plate = Part.makeBox(100, 10, 40)
    plate = plate.cut(Part.makeCylinder(4.1, 10, App.Vector(29.1, 0, 20), App.Vector(0, 1, 0)))
    plate = plate.cut(Part.makeCylinder(8, 10, App.Vector(69.9, 0, 20), App.Vector(0, 1, 0)))
    for z in (11, 29):
        plate = plate.cut(Part.makeCylinder(1.25, 8, App.Vector(69.9, 0, z), App.Vector(0, 1, 0)))
    for x in (10, 90):
        for z in (7, 33):
            plate = plate.cut(Part.makeCylinder(2.25, 10, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def puller_roller_shape():
    """Ø40 x60 roller with Ø8.2 through bore for a metal spindle."""
    return one_solid(Part.makeCylinder(20, 60).cut(Part.makeCylinder(4.1, 60)))


def puller_eccentric_bushing_shape():
    """Flanged metal bush; straight flange slots permit ±30° pressure trim."""
    axis = App.Vector(0, 1, 0)
    bush = Part.makeCylinder(8, 10, App.Vector(0, 0, 0), axis).fuse(
        Part.makeCylinder(12, 3, App.Vector(0, -3, 0), axis))
    bush = bush.cut(Part.makeCylinder(4.1, 13, App.Vector(1, -3, 0), axis))
    for z in (-9, 9):
        slot = Part.makeBox(6.6, 3, 3.4, App.Vector(-3.3, -3, z - 1.7))
        for x in (-3.3, 3.3):
            slot = slot.fuse(Part.makeCylinder(1.7, 3, App.Vector(x, -3, z), axis))
        bush = bush.cut(slot)
    return one_solid(bush)


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
    plate = plate.cut(Part.makeCylinder(16.0375, 6, App.Vector(40, 40, 0)))
    for angle in (45, 135, 225, 315):
        a = math.radians(angle)
        plate = plate.cut(Part.makeCylinder(2.75, 6, App.Vector(40 + 22.5 * math.cos(a), 40 + 22.5 * math.sin(a), 0)))
    for x in (8, 72):
        plate = plate.cut(Part.makeBox(6.6, 18, 6, App.Vector(x - 3.3, 31, 0)))
    return one_solid(plate)


def mica_band_heater_shape(inner_diameter=34.15, width=45.0, radial_thickness=2.0, closure_gap=4.0):
    """24 V/100 W custom split mica band in its free state, local barrel axis +Z."""
    inner_radius = inner_diameter / 2.0
    band = Part.makeCylinder(inner_radius + radial_thickness, width).cut(
        Part.makeCylinder(inner_radius, width)
    )
    # The displayed split is an installation envelope; the RFQ controls its
    # usable closure travel and the installed sector-contact acceptance.
    split = Part.makeBox(
        radial_thickness + 2.0,
        closure_gap,
        width,
        App.Vector(inner_radius - 1.0, -closure_gap / 2.0, 0),
    )
    return one_solid(band.cut(split))


def k_type_probe_shape(diameter=3.0, insertion_length=6.0, sheath_length=25.4, lead_length=45.0):
    """Tempco MTA1 custom MI probe envelope; tip is +Z and stop is at Z=0."""
    external = sheath_length - insertion_length
    assert external > 0
    sheath = Part.makeCylinder(diameter / 2.0, sheath_length, App.Vector(0, 0, -external))
    stop = Part.makeCylinder(3.0, 0.8, App.Vector(0, 0, -0.8))
    lead = Part.makeCylinder(1.0, lead_length, App.Vector(0, 0, -external - lead_length))
    return one_solid(joined(sheath, stop, lead))


def thermocouple_retainer_shape():
    """TH-TCR-01 bridge retaining the supplier-welded probe stop collar."""
    axis = App.Vector(0, 1, 0)
    bridge = Part.makeBox(12, 1.5, 16, App.Vector(-6, 0, -8))
    bridge = bridge.cut(Part.makeCylinder(1.7, 1.5, App.Vector(0, 0, 0), axis))
    for z in (-5, 5):
        bridge = bridge.cut(Part.makeCylinder(1.7, 1.5, App.Vector(0, 0, z), axis))
    return one_solid(bridge)


def die_cartridge_heater_shape():
    """TH-DIE-01 Ø6.5 x39.5 cartridge with captive flange; axis +Y."""
    heater = Part.makeCylinder(3.25, 39.5, App.Vector(0, -19.0, 0), App.Vector(0, 1, 0))
    flange = Part.makeBox(20, 1.5, 12, App.Vector(-10, 20, -6))
    for x in (-7, 7):
        flange = flange.cut(Part.makeCylinder(1.7, 1.5, App.Vector(x, 20, 0), App.Vector(0, 1, 0)))
    return one_solid(heater.fuse(flange))


def feeder_housing_shape():
    """Vertical metering-auger housing with a registered upper gasket spigot."""
    tube = Part.makeCylinder(14.5, 106.2).cut(Part.makeCylinder(12.5, 106.2))
    # The 1.2 mm projection above the upper flange is finish-turned to Ø28.80.
    tube = tube.cut(
        Part.makeCylinder(14.5, 1.2, App.Vector(0, 0, 105)).cut(
            Part.makeCylinder(14.4, 1.2, App.Vector(0, 0, 105))
        )
    )
    lower = Part.makeCylinder(22, 3).cut(Part.makeCylinder(12.5, 3))
    upper = Part.makeCylinder(22, 3, App.Vector(0, 0, 102)).cut(
        Part.makeCylinder(12.5, 3, App.Vector(0, 0, 102))
    )
    housing = joined(tube, lower, upper)
    for z in (0, 102):
        for angle in (0, 90, 180, 270):
            a = math.radians(angle)
            housing = housing.cut(
                Part.makeCylinder(2.25, 3, App.Vector(18 * math.cos(a), 18 * math.sin(a), z))
            )
    return one_solid(housing)


def sealed_feed_hopper_shape():
    """Sealed hopper with a direct registered flange for FD-MET-01."""
    hopper = cylindrical_hopper(78, 145, 55, 14.45)
    flange = Part.makeCylinder(22, 3, App.Vector(0, 0, -55)).cut(
        Part.makeCylinder(12.45, 3, App.Vector(0, 0, -55))
    )
    hopper = joined(hopper, flange)
    # Ø28.90 socket, 1.40 deep, leaves axial clearance over the 1.2 mm spigot.
    hopper = hopper.cut(Part.makeCylinder(14.45, 1.4, App.Vector(0, 0, -55)))
    for angle in (0, 90, 180, 270):
        a = math.radians(angle)
        hopper = hopper.cut(Part.makeCylinder(2.3, 3, App.Vector(18 * math.cos(a), 18 * math.sin(a), -55)))
    return one_solid(hopper)


def feed_hopper_gasket_shape():
    gasket = Part.makeCylinder(22, 0.5).cut(Part.makeCylinder(14.6, 0.5))
    for angle in (0, 90, 180, 270):
        a = math.radians(angle)
        gasket = gasket.cut(Part.makeCylinder(2.3, 0.5, App.Vector(18 * math.cos(a), 18 * math.sin(a), 0)))
    return one_solid(gasket)


def feeder_auger_shape():
    """Ø24.60 x105 removable positive-displacement auger on an Ø8 shaft."""
    root_r, outer_r, length, pitch = 5.0, 12.3, 105.0, 18.0
    root = Part.makeCylinder(root_r, length).cut(Part.makeCylinder(4.1, length))
    # Local Ø12 boss gives the removable Ø3 spring pin enough bearing
    # length without changing the metering root along the rest of the auger.
    root = joined(root, Part.makeCylinder(6.0, 8.0, App.Vector(0, 0, 4.0)).cut(
        Part.makeCylinder(4.1, 8.0, App.Vector(0, 0, 4.0))))
    segments_per_turn = 24
    dz = pitch / segments_per_turn
    blade_width = 3.4
    blade_tip_x = math.sqrt(outer_r**2 - (blade_width / 2)**2)
    segments = []
    for index in range(int(math.ceil(length / dz))):
        z = index * dz
        segment = Part.makeBox(blade_tip_x - root_r + 0.35, blade_width, min(2.0, length - z), App.Vector(root_r - 0.35, -blade_width / 2, z))
        segment.rotate(App.Vector(0, 0, z), App.Vector(0, 0, 1), index * 360.0 / segments_per_turn)
        segments.append(segment)
    auger = one_solid(root.multiFuse(segments))
    return one_solid(auger.cut(Part.makeCylinder(1.5, 14.0, App.Vector(-7, 0, 8), App.Vector(1, 0, 0))))


def feeder_agitator_shaft_shape():
    """Common Ø8 drive shaft with hopper anti-bridge paddles above the auger."""
    shaft = Part.makeCylinder(4, 300)
    for z, radius, angle in ((183, 25, 0), (228, 50, 90), (273, 60, 0)):
        arm = Part.makeCylinder(2, 2 * radius, App.Vector(-radius, 0, z), App.Vector(1, 0, 0))
        arm.rotate(App.Vector(0, 0, z), App.Vector(0, 0, 1), angle)
        shaft = shaft.fuse(arm)
    shaft = shaft.cut(Part.makeCylinder(1.5, 8.0, App.Vector(-4, 0, 11), App.Vector(1, 0, 0)))
    return one_solid(shaft.cut(Part.makeCylinder(1.5, 8.0, App.Vector(-4, 0, 292), App.Vector(1, 0, 0))))


def feeder_drive_mount_shape():
    """Welded steel shelf transferring the feeder drive load to the rear frame post."""
    shelf = Part.makeBox(126, 70, 8)
    shelf = shelf.cut(Part.makeCylinder(13, 8, App.Vector(30, 35, 0)))
    for x in (14.5, 45.5):
        for y in (19.5, 50.5):
            shelf = shelf.cut(Part.makeCylinder(2.25, 8, App.Vector(x, y, 0)))
    flange = Part.makeBox(8, 70, 70, App.Vector(118, 0, 0))
    for y in (15, 55):
        flange = flange.cut(Part.makeCylinder(3.3, 8, App.Vector(118, y, 35), App.Vector(1, 0, 0)))
    return one_solid(joined(shelf, flange))


def feeder_drive_coupling_shape():
    """Keyed Ø8 gearbox-to-cross-pinned Ø8 feeder-shaft coupling."""
    coupling = Part.makeCylinder(9, 24).cut(Part.makeCylinder(4.025, 24))
    coupling = coupling.cut(Part.makeBox(3.1, 2.2, 12, App.Vector(-1.55, 3.8, 12)))
    coupling = coupling.cut(Part.makeCylinder(1.5, 18, App.Vector(-9, 0, 6), App.Vector(1, 0, 0)))
    return one_solid(coupling)


def feeder_reference_drive_shape():
    """17E1K-07 motor plus EG17-G10 installation envelope, output along -Z."""
    gearbox = Part.makeBox(42, 42, 55, App.Vector(-21, -21, 0))
    motor = Part.makeBox(42, 42, 80, App.Vector(-21, -21, 55))
    output = Part.makeCylinder(4, 21.5, App.Vector(0, 0, 0), App.Vector(0, 0, -1))
    return one_solid(joined(gearbox, motor, output))


def thrust_plate_shape():
    """12 mm thrust plate with a 51102 housing-washer pocket and four M6 mounts."""
    plate = Part.makeBox(12, 95, 105)
    plate = plate.cut(Part.makeCylinder(8.6, 12, App.Vector(0, 47.5, 52.5), App.Vector(1, 0, 0)))
    plate = plate.cut(Part.makeCylinder(14.15, 9.15, App.Vector(0, 47.5, 52.5), App.Vector(1, 0, 0)))
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
    roller = Part.makeCylinder(18, 20).cut(Part.makeCylinder(6.0, 20))
    # Flush metal retainers sit in Ø32 x1.05 end recesses; the bearing seats
    # start at their inner faces and leave 0.10–0.22 mm axial freedom.
    for z in (0, 18.95):
        roller = roller.cut(Part.makeCylinder(16.0, 1.05, App.Vector(0, 0, z)))
    for z in (1.05, 13.85):
        roller = roller.cut(Part.makeCylinder(8.0, 5.1, App.Vector(0, 0, z)))
    for angle in (0, 120, 240):
        x, y = 13 * math.cos(math.radians(angle)), 13 * math.sin(math.radians(angle))
        roller = roller.cut(Part.makeCylinder(1.7, 20, App.Vector(x, y, 0)))
    return one_solid(roller)


def guide_roller_retainer_shape():
    """Flush 304 SS cap retaining the 625 outer ring without seal contact."""
    cap = Part.makeCylinder(16, 1).cut(Part.makeCylinder(7.5, 1))
    for angle in (0, 120, 240):
        x, y = 13 * math.cos(math.radians(angle)), 13 * math.sin(math.radians(angle))
        cap = cap.cut(Part.makeCylinder(1.7, 1, App.Vector(x, y, 0)))
    return one_solid(cap)


def spool_bearing_plate_shape():
    """10 mm plate with an 8.05 mm-deep Ø28 H7 bearing pocket."""
    plate = Part.makeBox(105, 10, 60)
    plate = plate.cut(Part.makeCylinder(13.0, 10, App.Vector(30, 0, 30), App.Vector(0, 1, 0)))
    plate = plate.cut(Part.makeCylinder(14.005, 8.05, App.Vector(30, 0, 30), App.Vector(0, 1, 0)))
    for x in (8, 52):
        for z in (8, 52):
            plate = plate.cut(Part.makeCylinder(2.75, 10, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    for z in (10, 50):
        plate = plate.cut(Part.makeCylinder(2.75, 10, App.Vector(97, 0, z), App.Vector(0, 1, 0)))
    return one_solid(plate)


def spool_bearing_retainer_shape():
    """Four-bolt metal cover contacting only the 6001 outer-ring edge."""
    retainer = Part.makeBox(54, 2, 54, App.Vector(3, 0, 3))
    retainer = retainer.cut(Part.makeCylinder(13.0, 2, App.Vector(30, 0, 30), App.Vector(0, 1, 0)))
    for x in (8, 52):
        for z in (8, 52):
            retainer = retainer.cut(Part.makeCylinder(2.75, 2, App.Vector(x, 0, z), App.Vector(0, 1, 0)))
    return one_solid(retainer)


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
    return one_solid(end_plate_shape())


def dancer_support_plate_shape():
    plate = Part.makeBox(36, 8, 80)
    plate = plate.cut(Part.makeCylinder(4.1, 8, App.Vector(18, 0, 45), App.Vector(0, 1, 0)))
    for x in (8, 28):
        plate = plate.cut(Part.makeCylinder(2.75, 8, App.Vector(x, 0, 10), App.Vector(0, 1, 0)))
    return one_solid(plate)


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
    for y in (-13.0, 13.0):
        body = body.cut(Part.makeCylinder(1.5, 6, App.Vector(34, y, 0), App.Vector(1, 0, 0)))
    # Two M4 retainer threads, one heater bore with two M3 flange threads,
    # and one blind sensor bore.
    for x in (8, 32):
        body = body.cut(Part.makeCylinder(1.65, 10, App.Vector(x, 0, -24)))
    body = body.cut(Part.makeCylinder(3.275, 40, App.Vector(20, -20, 18), App.Vector(0, 1, 0)))
    for x in (13, 27):
        body = body.cut(Part.makeCylinder(1.25, 6, App.Vector(x, 14, 18), App.Vector(0, 1, 0)))
    body = body.cut(Part.makeCylinder(1.60, 12, App.Vector(8, -20, 15), App.Vector(0, 1, 0)))
    for z in (10, 20):
        body = body.cut(Part.makeCylinder(1.25, 4, App.Vector(8, -20, z), App.Vector(0, 1, 0)))
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
    for y in (-13.0, 13.0):
        gasket = gasket.cut(Part.makeCylinder(1.6, 0.5, App.Vector(40, y, 0), App.Vector(1, 0, 0)))
    return one_solid(gasket)


def cylindrical_hopper(radius, straight_height, cone_height, outlet_radius, wall=2.0):
    straight = Part.makeCylinder(radius, straight_height).cut(
        Part.makeCylinder(radius-wall, straight_height)
    )
    outer_cone = Part.makeCone(outlet_radius, radius, cone_height, App.Vector(0, 0, -cone_height))
    inner_cone = Part.makeCone(outlet_radius-wall, radius-wall, cone_height, App.Vector(0, 0, -cone_height))
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


def hook_disc(od=58.0, root=36.0, thickness=6.0, hooks=7, capture_samples=18, relief_samples=8,
              bore=25.01, key_width=6.0075):
    """Asymmetric cycloidal-derived hook disc.

    A long 76 % capture flank follows a cycloidal radial rise.  A short nose
    and 24 % relief flank create the hook asymmetry.  This is a manufacturable
    2-D laser/waterjet profile, not a generic saw-tooth placeholder.
    """
    pts = cycloidal_hook_profile_points(od, root, hooks, capture_samples, relief_samples)
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    disc = face.extrude(App.Vector(0, thickness, 0))
    bore_void = cyl(bore / 2, thickness, 0, 0, 0, (0, 1, 0))
    # Internal keyway only: the previous long radial cut could open through a
    # tooth.  A 6 mm radial depth from z=7 accepts the protruding half of a
    # standard 6 x 6 key while remaining blind inside the hub/root section.
    keyway = Part.makeBox(key_width, thickness, 6.0, App.Vector(-key_width / 2, 0, 9.0))
    return disc.cut(bore_void.fuse(keyway))


def spur_phase_gear(module=2.0, teeth=24, thickness=8.0, bore=20.2, pair_backlash_mm=0.0):
    """Ideal 20 degree involute envelope for a purchased steel phase gear.

    Root trochoid and hub/set-screw details remain supplier geometry; this
    model is not released as a cut-gear DXF.
    """
    pressure_angle = math.radians(20.0)
    pitch_radius = module * teeth / 2.0
    base_radius = pitch_radius * math.cos(pressure_angle)
    root_radius = pitch_radius - 1.25 * module
    tip_radius = pitch_radius + module
    if not 0 <= pair_backlash_mm < math.pi * pitch_radius / teeth:
        raise ValueError("pair backlash must be nonnegative and smaller than circular tooth pitch")
    # Equal thinning on both gears: pair backlash = 4*r*half-flank angular reduction.
    half_tooth = math.pi / (2.0 * teeth) - pair_backlash_mm / (4.0 * pitch_radius)
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


def cutter_shaft(length=240.0, key_phase_deg=0.0, shaft_id="105"):
    """Separate keyseat stations preserve the complete bearing-seat envelopes."""
    if str(shaft_id) not in {"105", "153"}:
        raise ValueError("shaft_id must identify the released left/right shaft")
    if length < 240.0:
        raise ValueError("released keyseat schedule requires at least 240 mm")
    shaft = Part.makeCylinder(12.5, length, App.Vector(0, 0, 0), App.Vector(0, 1, 0))
    seats = ((0.0, 35.0, 6.0, 3.5), (55.0, 105.0, 6.0, 3.5), (195.0, 45.0, 8.0, 4.0))
    if str(shaft_id) == "153":
        # Driven shaft starts at machine Y258 instead of Y278. Its bearing
        # envelopes are local Y57..69 and197..209; no slot may cross them.
        seats = ((0.0, 35.0, 6.0, 3.5), (85.0, 80.0, 6.0, 3.5), (212.0, 28.0, 8.0, 4.0))
    for y, key_length, width, depth in seats:
        keyway = Part.makeBox(width, key_length, depth, App.Vector(-width / 2, y, 12.5 - depth))
        keyway.rotate(App.Vector(), App.Vector(0, 1, 0), key_phase_deg)
        shaft = shaft.cut(keyway)
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
    shaft_right = cutter_shaft(key_phase_deg=25.714, shaft_id="153")
    motor_mount = motor_mount_plate()
    bearing_retainer = bearing_retainer_plate()
    chamber_sleeve = Part.makeCylinder(5, 128).cut(Part.makeCylinder(3.3, 128))
    return [
        dict(id="CUT-01", name="Cycloidal hook cutter disc", shape=hook_disc(), qty=12, material="6 mm AISI D2 tool steel (JIS SKD11 equivalent)", process="rough waterjet, vacuum harden/double temper 58-60 HRC, finish profile/faces grind", critical="OD 58.0; root circle R18.0 with smooth DXF transition; bore 25.01 +0.01/0; matched keyway width 6.005-6.010; final profile ±0.10 and taper <=0.05 through thickness after CAM kerf compensation; t6.00 ±0.03; flatness/parallelism 0.03; tooth side deburr C0.15 max; axial working gap 0.25-0.50 mm by metal shim; selected 5.995-6.000 key plus engraved index line registers stack; replace on crack, chip >0.5 mm, edge recession >0.30 mm or lost shim gap"),
        dict(id="CUT-02", name="Cutter spacer", shape=Part.makeCylinder(17, 7).cut(Part.makeCylinder(12.55, 7)), qty=10, material="S45C normalized steel", process="turn, then match-grind/lap as one numbered two-shaft stack", critical="OD34.0; bore25.10 +0.05/0; nominal length7.00; faces parallel within0.01; engrave shaft/position; with CUT-01 and 0.05/0.10/0.25 metal shims, every one of 11 opposing axial gaps shall measure0.25-0.50 over one full hand rotation; supply only as the accepted matched set"),
        dict(id="CUT-03", name="Bearing side plate", shape=plate, qty=2, material="12 mm S275JR steel", process="laser + bearing-seat finish", critical="two SKF 61905-2RS1 seats diameter 42 H7; center distance 48.00 +/-0.03; match-machine both plates; seat-axis parallelism 0.05/140; four frame holes diameter 6.6; identify front fixed and rear floating sides; after CUT-10 retention and metal shimming, each complete shaft axial float shall be0.05-0.20 over one full hand rotation"),
        dict(id="CUT-04", name="5 mm aperture screen", shape=screen_plate(), qty=2, material="3 mm 304 stainless", process="laser cut + deburr", critical="135 x 120 x 3; apertures diameter 5.0 on 9.0 pitch; all strand-side edges R0.3; verify minimum 1.9 mm rotating clearance with shims before powered test"),
        dict(id="CUT-05", name="25 mm keyed cutter shaft left", shape=shaft, qty=1, material="S45C QT steel", process="turn + indexed keyway; black oxide with bearing seats masked", critical="continuous Ø25 h6 =24.987-25.000 across 61905 journals, cutter land and gear/hub land; overall240.0 +/-0.10; TIR<=0.05; 6.005-6.010 keyways at y=0-35 and55-160 with selected key5.995-6.000; 8.005-8.010 keyway at195-240 with selected key7.995-8.000; datum clock0 deg; install slave shaft at Y278"),
        dict(id="CUT-05R", name="25 mm keyed cutter shaft right", shape=shaft_right, qty=1, material="S45C QT steel", process="turn + indexed keyway; black oxide with bearing seats masked", critical="continuous Ø25 h6 =24.987-25.000 across 61905 journals, cutter land and gear/hub land; overall240.0 +/-0.10; TIR<=0.05; all keyway centreplanes clocked25.714 +/-0.02 deg; 6.005-6.010 keyways at y=0-35 and85-165 with selected key5.995-6.000; 8.005-8.010 keyway at212-240 with selected key7.995-8.000; install driven shaft at Y258"),
        dict(id="CUT-06", name="Phase gear axial spacer", shape=Part.makeCylinder(17, 4).cut(Part.makeCylinder(12.55, 4)), qty=2, material="S45C normalized steel", process="simple turning", critical="OD 34.0; bore 25.10 +0.05/0; length 4.00 +/-0.03; faces parallel within 0.03"),
        dict(id="CUT-07", name="DRV-01 universal donor motor plate", shape=motor_mount, qty=1, material="6 mm steel", process="laser cut + deburr; standard metal angles", critical="180 x 140 x 6; three 9 x 70 motor-angle slots and two 55 x 9 tension slots; donor-specific angle/hub drilling is HOLD until exact model, shaft height and rotation envelope are measured"),
        dict(id="CUT-08", name="Dual 61905 bearing retainer", shape=bearing_retainer, qty=2, material="2 mm steel", process="laser cut + deburr", critical="figure-eight OD lobes 60; two relief bores diameter 34; center distance 48.00 +/-0.05; six M4 clearance holes diameter 4.5 at drawing coordinates; CUT-03 matching holes are included and may be match-reamed after bearing-seat finish"),
        dict(id="CUT-09", name="Shredder chamber distance sleeve", shape=chamber_sleeve, qty=4, material="S275JR steel", process="turn, drill/ream and match-face as a set", critical="OD10.00 +/-0.05; ID6.60 +0.10/0; length128.00 +/-0.03; four-piece matched length spread <=0.03; face parallelism <=0.03; deburr C0.2 max"),
        dict(id="CUT-10", name="61905 bearing seat ring", shape=Part.makeCylinder(21, 3).cut(Part.makeCylinder(12.75, 3)), qty=4, material="S45C normalized steel", process="turn and match-face", critical="OD42 g6; ID25.50 +0.10/0; width3.00 +/-0.02; faces parallel0.01; bears on outer ring only; engrave front-fixed/rear-floating and shaft ID; set rear outer-ring endplay using0.05/0.10/0.20 ground metal shims; complete-shaft axial float acceptance0.05-0.20 mm"),
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
        Part.makeBox(LID["width_mm"], LID["length_mm"], 2),
        Part.makeBox(LID["width_mm"], 4, 6),
        Part.makeBox(LID["width_mm"], 4, 6, App.Vector(0, LID["length_mm"]-4, 0)),
        Part.makeCylinder(7, 8, App.Vector(LID["latch_x_mm"], 12, 0)),
    ).cut(Part.makeCylinder(2.25, 8, App.Vector(LID["latch_x_mm"], 12, 0))).cut(
        Part.makeCone(4.2, 2.25, 2.0, App.Vector(LID["latch_x_mm"], 12, 0))
    )

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
    # Chamber upper steel sleeves pass through clearance holes in both walls;
    # the M6 tie bolts run inside the sleeves and close these paths in service.
    for x in (35, 155):
        chute = chute.cut(Part.makeCylinder(5.25, 120, App.Vector(x, 0, 25), App.Vector(0, 1, 0)))

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
        gauge = gauge.cut(Part.makeCylinder(1.7, 8, App.Vector(x, y, 0)))

    guard = shell_box(110, 100, 65, 2).cut(Part.makeBox(80, 100, 32, App.Vector(15, 0, 16)))
    guard = joined(guard, *(Part.makeCylinder(7, 8, App.Vector(x, y, 0)) for x, y in ((8, 8), (102, 8), (8, 92), (102, 92))))
    for x, y in ((8, 8), (102, 8), (8, 92), (102, 92)):
        guard = guard.cut(Part.makeCylinder(2.25, 8, App.Vector(x, y, 0)))

    bracket = Part.makeBox(60, 5, 70).fuse(Part.makeBox(60, 45, 5)).cut(cyl(2.6, 5, 30, 0, 50, (0, 1, 0)))
    for x in (15, 45):
        bracket = bracket.cut(Part.makeCylinder(2.75, 5, App.Vector(x, 30, 0)))
    adapter = Part.makeCone(18, 35, 35).cut(Part.makeCone(14, 31, 33, App.Vector(0, 0, 2))).cut(cyl(6.1, 35, 0, 0, 0))
    adapter = adapter.cut(Part.makeCylinder(3.3, 60, App.Vector(-30, 0, 10), App.Vector(1, 0, 0)))
    carriage = one_solid(carriage_shape())
    bezel = Part.makeBox(180, 120, 5).cut(Part.makeBox(145, 82, 5, App.Vector(17.5, 19, 0)))
    bezel = joined(bezel, *(Part.makeCylinder(6, 8, App.Vector(x, y, 0)) for x, y in ((8, 8), (172, 8), (8, 112), (172, 112))))
    for x, y in ((8, 8), (172, 8), (8, 112), (172, 112)):
        bezel = bezel.cut(Part.makeCylinder(1.7, 8, App.Vector(x, y, 0)))
    # Rectangular clamp around the 18 x 18 purchased duct.  Its 18.6 mm
    # cavity gives 0.30 mm clearance per side; the side tab mounts to profile.
    clip = Part.makeBox(26, 26, 8).cut(Part.makeBox(18.6, 18.6, 8, App.Vector(3.7, 3.7, 0)))
    clip = joined(clip, Part.makeBox(12, 26, 8, App.Vector(-12, 0, 0)))
    clip = clip.cut(Part.makeCylinder(2.25, 8, App.Vector(-6, 13, 0)))
    specs = [
        dict(id="PPR-C01", name="Sliding hopper lid", shape=lid, qty=1, material="PLA", orientation="flat", layer="0.24 mm", walls=4, infill="20%", support="no", support_contact="none", support_removal="ream latch hole to Ø4.50–4.70 and deburr underside countersink", fastener="1x M4x16 90° flat-head latch flag screw + washer + nyloc", insert="none", tightening="1.2 N.m", tolerance="finished latch hole Ø4.50–4.70; screw head flush or recessed≤0.05; rail slide gap0.35", mating="metal hopper rails and lid-interlock flag", order=3, edge_distance="15 mm boss centre to edge", interfaces="M4 through bore Ø4.50–4.70 with Ø8.4×2 90° underside countersink; rail slide gap0.35"),
        dict(id="PPR-C02", name="Anti-reach baffle chute", shape=chute, qty=1, material="PLA", orientation="outlet down", layer="0.24 mm", walls=5, infill="25%", support="ledge undersides only", support_contact="two staggered ledge undersides", support_removal="needle-nose pliers through 100x50 outlet", fastener="4x M4x12 + washer; 2x chamber M6 tie bolts inside steel sleeves", insert="4x M4 nyloc nuts on metal side", tightening="M4 1.2 N.m; M6 6 N.m", tolerance="0.40 mm flake path", mating="hopper and metal cutter chamber", order=4, edge_distance="8 mm boss centre; Ø14 boss", interfaces="4x Ø4.5 mount; 2x Ø10.5 steel-sleeve clearance; 100x50 outlet; staggered 72 mm ledges"),
        dict(id="PPR-C03", name="Flake bin sheet corner", shape=flake_bin, qty=4, material="PLA", orientation="end down", layer="0.28 mm", walls=4, infill="25%", support="no", support_contact="none", support_removal="none", fastener="2x M3x8 + washer + nyloc", insert="none", tightening="0.5 N.m", tolerance="sheet slot 1.40 ±0.30 mm", mating="1.00 ±0.05 mm sheet bin and screen rails", order=7, edge_distance="12 mm hole centre", interfaces="2x Ø3.4 through on orthogonal legs"),
        dict(id="PPR-C04", name="Screen drawer handle", shape=handle, qty=1, material="PLA", orientation="back flat", layer="0.24 mm", walls=5, infill="35%", support="no", support_contact="none", support_removal="none", fastener="2x M5x16 + large washer + nyloc", insert="none", tightening="2.0 N.m", tolerance="0.25 mm", mating="metal screen", order=6, edge_distance="8 mm hole centre", interfaces="2x Ø5.5 through at 84 mm spacing"),
        dict(id="PPR-C05", name="Cooling duct segment", shape=duct, qty=2, material="ABS", orientation="end face down", layer="0.24 mm", walls=4, infill="15%", support="no", support_contact="none", support_removal="none", fastener="8x M4x12 + washer + nyloc", insert="none", tightening="1.2 N.m", tolerance="0.30 mm flange registration", mating="80 mm fan and next duct", order=13, edge_distance="5 mm hole centre", interfaces="8x Ø4.5 flange holes; 60x55 clear air opening"),
        dict(id="PPR-C06", name="Gauge enclosure", shape=gauge, qty=2, material="ABS", orientation="outer face down", layer="0.20 mm", walls=4, infill="25%", support="slot bridge only", support_contact="8x70 optical slot roof", support_removal="break bridge strands from open housing side; ream fastener holes to Ø3.40–3.50", fastener="4x M3x12 + washers + all-metal nuts", insert="none", tightening="0.5 N.m", tolerance="finished holes Ø3.40–3.50; 0.20 mm optical slit; install X/Y pair on one straight Ø1.75 calibration wire, match-drill mounting datum, scan both axes and accept optical centreline offset <=0.10 mm", mating="LED/photodiode cross frame", order=14, edge_distance="7 mm boss centre; Ø12 boss", interfaces="4x Ø3.40–3.50 through bores; 8 mm optical slot; complete-pair functional alignment"),
        dict(id="PPR-C07", name="Puller pinch guard", shape=guard, qty=1, material="ABS", orientation="outer face down", layer="0.24 mm", walls=5, infill="20%", support="window bridge only", support_contact="80x32 inspection-window upper edge", support_removal="deburr from open guard interior", fastener="4x M4 captive screws", insert="4x M4 rivnuts in metal puller plate", tightening="1.2 N.m", tolerance="0.40 mm guard gap", mating="metal puller plate", order=15, edge_distance="8 mm boss centre; Ø14 boss", interfaces="4x Ø4.5 through; 80x32 guarded window"),
        dict(id="PPR-C08", name="Solid-strand guide axle bracket", shape=bracket, qty=2, material="PLA", orientation="L side", layer="0.20 mm", walls=5, infill="40%", support="yes under axle bore", support_contact="Ø5.2 axle-bore lower semicircle", support_removal="ream both bores to Ø5.20–5.40 after support removal", fastener="2x M5x16 + washer + T-nut", insert="none", tightening="2.0 N.m", tolerance="finished bore Ø5.20–5.40; align both loose T-slot brackets on the same axle before 2.0 N.m torque; axle shall pass by hand without visible bending", mating="FM-GA-01 fixed Ø5 axle and profile; 625 bearings are seated in FM-GR-01", order=16, edge_distance="15 mm hole centre", interfaces="2x Ø5.5 base holes; Ø5.20–5.40 fixed-axle bore; complete-pair hand-pass alignment"),
        dict(id="PPR-C09", name="Spool cone adapter", shape=adapter, qty=2, material="PLA", orientation="large face down", layer="0.20 mm", walls=5, infill="35%", support="no", support_contact="none", support_removal="ream spindle bore to Ø12.20–12.40", fastener="1x M6x30 through clamp + washer + nyloc", insert="none; metal shaft collar carries axial load", tightening="2.5 N.m", tolerance="finished spindle bore Ø12.20–12.40; diametral clearance0.20–0.411 to Ø12 h6; cone-to-received-spool contact is separately selected", mating="12 mm metal spindle, metal collar, and received spool", order=18, edge_distance="radial cross-hole at z=10", interfaces="Ø12.20–12.40 axial bore; Ø6.6 radial through clamp; metal collar carries axial load"),
        dict(id="PPR-C10", name="Traverse carriage", shape=carriage, qty=1, material="PLA", orientation="flat", layer="0.20 mm", walls=5, infill="40%", support="rod bores only", support_contact="two Ø8.4 rod-bores", support_removal="ream rod bores to Ø8.40–8.50 and belt-clamp holes to Ø4.50–4.70", fastener="2x M4x25 belt-clamp screws + washers + nyloc", insert="none", tightening="1.2 N.m", tolerance="finished rod bores Ø8.40–8.50; finished clamp holes Ø4.50–4.70; use two Ø8 h6=7.991–8.000 ground steel rods", mating="specified Ø8 h6 rods and GT2 belt", order=19, edge_distance="8 mm from belt-pad edge", interfaces="40x55 carriage; rod bores8.40-8.50; clamp holes4.50-4.70 at local X13/27 Y27.5; Y travel80 parallel to spindle"),
        dict(id="PPR-C11", name="Control panel bezel", shape=bezel, qty=1, material="PLA", orientation="front face down", layer="0.20 mm", walls=4, infill="20%", support="no", support_contact="none", support_removal="ream fastener holes to Ø3.40–3.50", fastener="4x M3x16 + washers + all-metal nuts", insert="none", tightening="0.5 N.m", tolerance="finished holes Ø3.40–3.50; 0.25 mm TFT", mating="metal control panel", order=21, edge_distance="8 mm boss centre; Ø12 boss", interfaces="4x Ø3.40–3.50 through bores; 145x82 display opening"),
        dict(id="PPR-C12", name="Cable duct clamp", shape=clip, qty=8, material="PLA", orientation="flat", layer="0.20 mm", walls=4, infill="50%", support="no", support_contact="none", support_removal="none", fastener="1x M4x10 + profile T-nut", insert="none", tightening="1.0 N.m", tolerance="18.6 mm cavity; 0.30 mm/side", mating="20 mm profile and fixed 18x18 cable duct", order=22, edge_distance="6 mm hole centre on 12 mm side tab", interfaces="1x Ø4.5 through tab; 18.6x18.6 duct cavity"),
    ]
    # axis, start xyz, radius, length.  validation/print_interface_checks.py
    # probes these actual voids and a surrounding annulus in the final B-Rep.
    interface_bores = {
        "PPR-C01": [("z", (LID["latch_x_mm"], 12, 0), 2.25, 8)],
        "PPR-C02": (
            [("z", (x, y, 0), 2.25, 8) for x, y in ((8, 8), (182, 8), (8, 112), (182, 112))]
            + [("y", (x, 0, 25), 5.25, 120) for x in (35, 155)]
        ),
        "PPR-C03": [("x", (0, 12, 90), 1.7, 3), ("y", (12, 0, 60), 1.7, 3)],
        "PPR-C04": [("z", (x, 12.5, 0), 2.75, 20) for x in (8, 92)],
        "PPR-C05": [("z", (x, y, z), 2.25, 4) for z in (0, 96) for x, y in ((5, 5), (75, 5), (5, 70), (75, 70))],
        "PPR-C06": [("z", (x, y, 0), 1.7, 8) for x, y in ((7, 7), (88, 7), (7, 63), (88, 63))],
        "PPR-C07": [("z", (x, y, 0), 2.25, 8) for x, y in ((8, 8), (102, 8), (8, 92), (102, 92))],
        "PPR-C08": [("z", (x, 30, 0), 2.75, 5) for x in (15, 45)],
        "PPR-C09": [("x", (-30, 0, 10), 3.3, 60)],
        "PPR-C10": [("z", (x, 27.5, 0), 2.25, 14) for x in TRAVERSE["clamp_hole_x_mm"]],
        "PPR-C11": [("z", (x, y, 0), 1.7, 8) for x, y in ((8, 8), (172, 8), (8, 112), (172, 112))],
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
            Part.makeCylinder(16, 4, App.Vector(x, 45, 55), App.Vector(0, 1, 0))
        )
    return one_solid(guard)


def hot_shield_shape():
    shield = three_panel_tunnel(335, 75, 85, 2)
    return one_solid(shield.cut(Part.makeCylinder(25, 2, App.Vector(314, 37, 83))))


def machine_fabrication_parts():
    """Non-shredder machine parts that require stock cutting or fabrication."""
    printed = {item["id"]: item["shape"] for item in print_parts()}
    return [
        dict(id="IN-HOP-01", name="Refillable input hopper", shape=cylindrical_hopper(100, 150, 60, 20), qty=1, material="2 mm 5052-H32 aluminum", process="roll cone/cylinder + TIG weld + deburr", critical="OD200 x straight150 + cone60; outlet Ø40; wall 2.0; lid rail datum flatness 0.5; leak-free dry-flake seams"),
        dict(id="FD-BIN-01", name="Removable flake bin", shape=flake_bin_sheet_shape(printed["PPR-C03"]), qty=1, material="1.00 ±0.05 mm 304 stainless sheet", process="laser cut, fold and rivet/TIG seam", critical="185 x175 x115 outside; sheet1.00 ±0.05; PPR-C03 slot1.40 ±0.30 gives clearance0.05–0.75; corner reliefs control; no inward burr/dead pocket; removable without cutter disassembly"),
        dict(id="FD-HOP-01", name="Sealed feed hopper", shape=sealed_feed_hopper_shape(), qty=1, material="2 mm 304 stainless", process="roll cone/cylinder + TIG flange + gasketed lid", critical="OD156 x straight145 + cone55; outlet ID24.90–25.00; lower flange OD44 x3, 4xØ4.60 +0.10/0 PCD36±0.05; register ID28.90 +0.03/0 x1.40±0.05; leak test"),
        dict(id="FD-GSK-01", name="Feed-hopper flange gasket", shape=feed_hopper_gasket_shape(), qty=2, material="food-contact platinum silicone 0.50±0.05 mm", process="die cut", critical="OD44; ID29.20 +0.20/0; 4xØ4.60 +0.10/0 PCD36±0.10; compress to0.35–0.40; one installed plus one replacement"),
        dict(id="FD-MET-01", name="Metering auger housing", shape=feeder_housing_shape(), qty=1, material="304 stainless", process="turn tube/flanges + drill", critical="OD29/ID25.00 +0.05/0 x105 flange face plus upper spigot OD28.77–28.80 x1.20±0.05; flanges Ø44 x3; 4xØ4.60 +0.10/0 PCD36±0.05; auger radial clearance 0.20–0.25"),
        dict(id="FD-MET-02", name="Positive-displacement metering auger", shape=feeder_auger_shape(), qty=1, material="304 stainless", process="turn root/bore + mill or weld continuous flight", critical="OD24.60 -0.05/0 x105; root Ø10 with local Ø12 x8 pin boss at Z4–12; bore Ø8.20 +0.10/0; Ø3.00 +0.05/0 cross-hole at Z8; pitch18; deburr/polish Ra≤3.2; Gate-2 sets mass/rev"),
        dict(id="FD-MET-03", name="Common auger and anti-bridge agitator shaft", shape=feeder_agitator_shaft_shape(), qty=1, material="304 shaft", process="turn Ø8 shaft + cross-drill + weld/pin Ø4 paddles", critical="Ø8 h8=7.978–8.000 x300; Ø3.00 +0.05/0 cross-holes at Z11 and Z292; lower hole matched with FD-MET-02, upper with FD-CP-01; paddle sweep Ø50/100/120 at Z183/228/273; straightness0.10; 2.2 N·m design torque SF≥2"),
        dict(id="FD-DA-01", name="Feeder reference-drive frame mount", shape=feeder_drive_mount_shape(), qty=1, material="8 mm S275 steel", process="laser/waterjet + bore finish + weld flange", critical="126x70x70 welded shelf; gearbox pilot Ø26 clearance; 4xØ4.5 at31 mm square; 2xØ6.6 frame holes at40 pitch; mount centre30/35; weld continuous both sides; gearbox axis position0.10 to frame datum"),
        dict(id="FD-CP-01", name="Feeder positive drive coupling", shape=feeder_drive_coupling_shape(), qty=1, material="S45C normalized steel", process="turn + broach 3 mm keyway + cross-drill", critical="OD18 x24; both bores Ø8.05 +0.03/0; gearbox half 3.10 +0.05/0 keyway x12; feeder half Ø3.00 +0.05/0 cross-hole at Z6 matched to FD-MET-03; new Ø3x18 spring pin; no set-screw-only torque path"),
        dict(id="EX-THR-01", name="Extruder thrust plate", shape=thrust_plate_shape(), qty=1, material="12 mm S45C normalized steel", process="laser rough + bore/seat finish", critical="12 x95 x105; passage Ø17.2; 51102 pocket Ø28.30 +0.05/0 x9.10 +0.05/0 from marked front face; 4xØ6.6; pocket shoulder square0.05 to bore; NSK general-purpose housing radial clearance >0.25; metal-to-profile load path"),
        dict(id="EX-SH-01", name="Three-panel hot-zone shield", shape=hot_shield_shape(), qty=1, material="2 mm 5052 aluminum", process="laser + two 90deg bends; bond PE", critical="335 x75 x85; open bottom/ends; feeder opening Ø50 at X314/Y37; >=10 mm ABS-duct gap; edge hem/deburr"),
        dict(id="DRV-GD-01", name="Interlocked drive guard", shape=drive_guard_shape(), qty=1, material="1 mm galvanized steel", process="laser + brake + service-cover hardware", critical="165 x48 x190; two Ø32 shaft clearances at X20/68,Z55; installed annular opening≤6; open service face; positive-opening interlock flag; PE bond"),
        dict(id="FM-PL-01", name="Puller side plate", shape=puller_plate_shape(), qty=2, material="10 mm 6061-T6", process="waterjet + ream/tap", critical="100 x10 x40; fixed axle Ø8.2 at X29.10/Z20; adjustable bush seat Ø16 H7 at X69.90/Z20; 2xM3-6H blind7 at X69.90/Z11/29 from marked outer face; installed axes X29.10/X70.90 give gap1.80 and nip X50.00 local; 4xØ4.5 guard mounts; matched pair axis position ±0.05"),
        dict(id="FM-RL-01", name="Puller roller", shape=puller_roller_shape(), qty=2, material="6061-T6 hub + replaceable Shore A 50-70 silicone sleeve", process="turn + bore", critical="finished OD40.00 ±0.025 x60; bore Ø8.2; TIR <=0.05; Shore A 50-70 sleeve; matched OD within 0.05"),
        dict(id="FM-EB-01", name="Puller eccentric pressure bushing", shape=puller_eccentric_bushing_shape(), qty=2, material="S45C normalized steel", process="turn eccentric bore + mill flange slots", critical="OD16 g6 x10; flange Ø24 x3; bore Ø8.20 +0.05/0 offset1.00 ±0.02; 2x3.4x10 flange slots at radius9; install paired bushes at equal index within0.5°; set full-rotation unloaded roller gap1.60-1.90 then clamp 2xM3 per bush"),
        dict(id="FM-AX-01", name="Puller roller spindle", shape=Part.makeCylinder(4, 80), qty=2, material="Ø8 h6 stainless shaft", process="cut/face + collar flats", critical="Ø8 h6 x80; TIR0.03; two metal collars; driven spindle interface remains donor-specific"),
        dict(id="FM-GR-01", name="Solid-strand guide roller", shape=guide_roller_shape(), qty=1, material="POM-C", process="turn + bearing-seat bore", critical="OD36 x20; 2x Ø32 x1.05 cap recesses; 2x Ø16 H7 x5.10 bearing pockets from cap inner faces; Ø12 through relief; 3xØ3.4 PCD26 through; seat shoulders square0.05; polished Ra<=1.6"),
        dict(id="FM-GC-01", name="Guide roller 625 outer-ring retainer", shape=guide_roller_retainer_shape(), qty=2, material="1 mm 304 stainless sheet", process="laser cut + deburr", critical="Ø32 x1; bore Ø15.00 +0.10/0 gives outer-ring radial overlap0.446-0.500; 3xØ3.4 PCD26; flatness0.05; bearing face burr-free; install flush in FM-GR-01 recess"),
        dict(id="FM-GA-01", name="Guide roller fixed axle", shape=Part.makeCylinder(2.5, 30), qty=1, material="Ø5 h6 stainless shaft", process="cut/face + E-clip grooves or collars", critical="Ø5 h6=4.992-5.000 x30; SKF625-2Z bore4.992-5.000; two E-clips/collars outside PPR-C08; bearing inner-ring clamp must not preload outer rings; no printed axle"),
        dict(id="SP-DA-01", name="Dancer arm", shape=dancer_arm_shape(0, (0, 0, 0)), qty=1, material="8 mm 6061-T6", process="waterjet + ream", critical="100 mm pivot centres; 12 mm arm; 2xØ8.20 +0.05/0; edge R2; full -25..+25deg motion"),
        dict(id="SP-AX-01", name="Dancer pivot/roller axles", shape=Part.makeCylinder(4, 28), qty=2, material="Ø8 h6 stainless shaft", process="cut/face + collars", critical="Ø8 h6 =7.991-8.000 x28; metal collars; one pivot and one end roller axle"),
        dict(id="SP-RL-01", name="Dancer end roller", shape=Part.makeCylinder(10, 20).cut(Part.makeCylinder(4.1, 20)), qty=1, material="POM-C", process="turn + bore", critical="OD20 x20; bore Ø8.20 +0.05/0; diametral axle clearance0.20-0.259; free rotation under 0.2-1.0 N filament tension"),
        dict(id="SP-SH-01", name="Spool spindle", shape=Part.makeCylinder(6, 143), qty=1, material="Ø12 h6 S45C", process="cut/turn faces + collar flats", critical="Ø12 h6=11.989-12.000 x143; straightness0.05; two SKF6001-2RSH bore11.992-12.000; axial collars carry spool load"),
        dict(id="SP-BP-01", name="Spool 6001 bearing pocket plate", shape=spool_bearing_plate_shape(), qty=2, material="10 mm 6061-T6", process="waterjet rough + pocket bore finish", critical="105 x10 x60; bearing centre X30/Z30; Ø28.000–28.021 H7 x8.05–8.10 pocket from marked inner face; Ø26 through relief leaves 1.95–2.00 shoulder; 4xØ5.5 retainer + 2xØ5.5 profile tab; matched axis position ±0.05"),
        dict(id="SP-BR-01", name="Spool 6001 outer-ring retainer", shape=spool_bearing_retainer_shape(), qty=2, material="2 mm 304 stainless sheet", process="laser cut + deburr", critical="54 x2 x54; Ø26.0 +0.10/0 relief gives 0.95–1.00 radial outer-ring overlap; 4xØ5.5 at 44 mm square; flatness0.10; burr away from bearing; use 4x M5 with SP-BP-01"),
        dict(id="SP-MM-01", name="Universal NEMA17-class spool motor plate", shape=spool_motor_mount_shape(), qty=1, material="6 mm 6061-T6", process="laser/waterjet + drill", critical="101 x6 x52; motor centre X26, Ø24; 4xØ4.5 at 31 mm square; 2xØ5.5 profile tab; actual donor shaft and body measurement required before coupling release"),
        dict(id="SP-TG-01", name="Traverse guide rod", shape=Part.makeCylinder(4,TRAVERSE["rod_length_mm"]), qty=2, material="8 h6 ground steel shaft", process="cut/face/deburr; collar witness marks outside carriage stroke", critical="8 h6 x196; nominal end margin2 beyond each8 mm collar; keep set-screw contact outside carriage path; actual collar torque and shaft retention test HOLD"),
        dict(id="SP-TR-01", name="Y-axis traverse stepped support", shape=traverse_end_plate_shape(), qty=2, material="8 mm 6061-T6", process="waterjet + ream", critical="8x60x132; stem14x84; rod bores8.20-8.30 at local Y10/35 Z114; M5 holes5.5 at Y7 Z8/32; two SP-TG-01 rods8 h6 x196; four SP-SC-08 collars outside support plates; parallelism<=0.10 over support spacing; spindle-parallel Y axis; four M5x16 plus received washer/T-nut; received collar torque/anti-slip test and bracket/joint proof HOLD"),
        dict(id="SP-DS-01", name="Dancer pivot support plate", shape=dancer_support_plate_shape(), qty=1, material="8 mm 6061-T6", process="waterjet + ream", critical="36 x8 x80; pivot Ø8.20 +0.05/0 at X18/Z45; 2xØ5.5 foot mounts; metal support carries spring/tension load"),
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
    add("FrameTraversePostLeft", box(*TRAVERSE["post_origins_mm"][0],20,20,280), aluminum, "frame", "20x20 profile L280")
    add("FrameTraversePostRight", box(*TRAVERSE["post_origins_mm"][1],20,20,280), aluminum, "frame", "20x20 profile L280")

    hopper = cylindrical_hopper(100, 150, 60, 20); hopper.translate(App.Vector(125, 395, 750))
    add("MetalHopper", hopper, aluminum, "input", "2 mm sheet metal")
    add("PPR-C01_SlidingLid", printed_at("PPR-C01",LID["origin_mm"]), blue, "input", "PLA")
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
        shaft = cutter_shaft(key_phase_deg=25.714 if cx == 153 else 0, shaft_id=str(cx)); shaft.translate(App.Vector(cx, shaft_y, 590))
        add(f"Shaft{cx}", shaft, steel, "shredder", "S45C QT, indexed 6/8 mm keyway zones")
        for i in range(6):
            # Assembly LOD preserves the cycloidal equation and envelope while
            # CUT-01 fabrication export retains the dense 18/8 sampling.
            d = hook_disc(capture_samples=6, relief_samples=3)
            axial_offset = 0.0 if cx == 105 else 6.5
            if cx == 153: d.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 25.714)
            d.translate(App.Vector(cx, 339 + axial_offset + i * 13, 590))
            add(f"Hook{cx}_{i}", d, orange, "shredder", "tool steel")
        for y in (315, 455):
            bearing = cyl(21, 12, cx, y, 590, (0, 1, 0)).cut(cyl(12.5, 12, cx, y, 590, (0, 1, 0)))
            add(f"Bearing{cx}_{y}", bearing, purple, "shredder", "SKF 61905-2RS1 + CUT-10 outer-ring seat ring")
    for x in (70, 190):
        for z in (550, 645):
            add(f"CUT09Sleeve{x}_{z}", cyl(5, 128, x, 327, z, (0, 1, 0)).cut(cyl(3.3, 128, x, 327, z, (0, 1, 0))), steel, "shredder", "CUT-09 S275JR steel")
            add(f"M6Fastener{x}_{z}", cyl(3, 170, x, 307, z, (0, 1, 0)), orange, "shredder", "M6x170 class 10.9 + hardened washers + all-metal locknut; 7 N.m")
    # Assembly LOD uses the perforated plate envelope; CUT-04 export contains
    # every 5 mm aperture and is the fabrication source of truth.
    add("Screen", box(60, 330, 555, 135, 120, 3), green, "shredder", "CUT-04 3 mm 304 stainless, 5 mm holes")
    add("PPR-C04_ScreenHandle",printed_at("PPR-C04",(78,288,545)),blue,"shredder","PLA")

    # Interchangeable geared-DC interface: a generic #35 chain ratio drives the
    # right shaft; a functional-spec M3 Z16 pair fixes counter-rotation/phase.
    drive_gear = spur_phase_gear(module=3.0, teeth=16, thickness=18.0, bore=25.01, pair_backlash_mm=.125)
    for cx in (105, 153):
        gear = drive_gear.copy()
        if cx == 153:
            gear.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 180.0 / 16.0)
        gear.translate(App.Vector(cx, 471, 590))
        add(f"PhaseGear{cx}", gear, purple, "shredder", "generic M3 Z16 20deg face18 steel or DRV-03 laminate")
    cutter_sprocket = chain_sprocket_shape(30, 25.01, 12); cutter_sprocket.rotate(App.Vector(),App.Vector(1,0,0),-90); cutter_sprocket.translate(App.Vector(153,258,590))
    motor_sprocket = chain_sprocket_shape(12, 12.2, 10); motor_sprocket.rotate(App.Vector(),App.Vector(1,0,0),-90); motor_sprocket.translate(App.Vector(153,258,680))
    add("CutterSprocket30T", cutter_sprocket, purple, "shredder", "#35 30T face>=6, match-drilled 4xØ6.6 PCD36 to DRV-02; tooth-root TIR<=0.10")
    add("MotorSprocket12T", motor_sprocket, purple, "shredder", "#35 12T on DRV-F01 outer hub")
    add("ChainTightSide",box(121,260,590,4,8,90),orange,"shredder","#35 pitch9.525, 40-pitch endless loop; C target86.167, slack2-3%", "purchased_reference_lod")
    add("ChainSlackSide",box(181,260,590,4,8,90),orange,"shredder","#35 pitch9.525, 40-pitch endless loop; C target86.167, slack2-3%", "purchased_reference_lod")
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
    add("DriveAdapterGMP60", adapter60, steel, "shredder", "DRV-A60 6 mm steel, Ø32.05–32.10 pilot bore, 4xM5 PCD45; chain-centre slot range C81-99")
    motor_plate = motor_mount_plate()
    motor_plate.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
    motor_plate.translate(App.Vector(65, 257, 590))
    add("MotorMountPlate", motor_plate, steel, "shredder", "CUT-07/DRV-01 6 mm steel; DRV-A60 bears directly on its front face")
    retainer = bearing_retainer_plate()
    front_retainer = retainer.copy(); front_retainer.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90); front_retainer.translate(App.Vector(55, 315, 535))
    rear_retainer = retainer.copy(); rear_retainer.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90); rear_retainer.translate(App.Vector(55, 469, 535))
    add("BearingRetainerFront", front_retainer, steel, "shredder", "CUT-08 2 mm steel")
    add("BearingRetainerRear", rear_retainer, steel, "shredder", "CUT-08 2 mm steel")
    # Conservative installation envelopes close the routing/clearance model;
    # exact sensor bodies and connectors remain receipt-inspection gates.
    add("ShredderRPMSensorEnvelope", box(90,268,604,12,8,20), purple, "shredder", "6 PPR Hall sensor maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="electronics/io_schedule.csv SHREDDER_SHAFT_RPM; receipt dimensions and air gap required")
    add("ShredderCableRouteEnvelope", box(195,238,570,12,12,125), purple, "shredder", "segregated motor/sensor cable service envelope", "purchased_reference_envelope")
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
    feed = sealed_feed_hopper_shape(); feed.translate(App.Vector(354, 347, 559.5))
    feed = one_solid(feed.cut(cyl(1.6,5.0,354,268,675,(0,1,0))))
    add("SealedFeedHopper", feed, aluminum, "feed", "2 mm sheet metal")
    feed_gasket = feed_hopper_gasket_shape(); feed_gasket.translate(App.Vector(354, 347, 504))
    add("FeedHopperGasket", feed_gasket, orange, "feed", "FD-GSK-01 food-contact silicone gasket")
    hopper_probe=k_type_probe_shape(insertion_length=4.0); hopper_probe.rotate(App.Vector(),App.Vector(1,0,0),-90); hopper_probe.translate(App.Vector(354,268,675))
    add("TemperatureProbeT5",hopper_probe,purple,"feed","T5 ungrounded K-type probe; MAX6675 T- common reference at receiver only")
    # Coaxial auger and anti-bridge paddles use one bounded drive. Gate-2 sets
    # mass/revolution; the lower auger remains removable under lockout.
    feeder_housing = feeder_housing_shape(); feeder_housing.translate(App.Vector(354, 347, 399))
    feeder_auger = feeder_auger_shape(); feeder_auger.translate(App.Vector(354, 347, 399))
    feeder_shaft = feeder_agitator_shaft_shape(); feeder_shaft.translate(App.Vector(354, 347, 396))
    add("FeederHousing", feeder_housing, steel, "feed", "FD-MET-01 304 OD29/ID25 housing")
    add("FeederAuger", feeder_auger, orange, "feed", "FD-MET-02 304 positive-displacement auger OD24.60 pitch18")
    add("FeederAgitatorDriveShaft", feeder_shaft, steel, "feed", "FD-MET-03 coaxial auger/anti-bridge shaft Ø8 h8; 2.2 N·m envelope")
    add("FeederAugerSpringPin", Part.makeCylinder(1.5,12,App.Vector(348,347,407),App.Vector(1,0,0)), steel, "feed", "SYS-15 Ø3x12 420 stainless spring pin")
    mount = feeder_drive_mount_shape(); mount.translate(App.Vector(324,312,716))
    coupling = feeder_drive_coupling_shape(); coupling.translate(App.Vector(354,347,686))
    drive = feeder_reference_drive_shape(); drive.translate(App.Vector(354,347,724))
    add("FeederDriveMount", mount, steel, "feed", "FD-DA-01 welded steel mount to frame post")
    add("FeederDriveCoupling", coupling, steel, "feed", "FD-CP-01 keyed and cross-pinned positive coupling")
    add("FeederDriveReference", drive, red, "feed", "StepperOnline 17E1K-07 + EG17-G10 digital reference envelope", "purchased_reference_envelope", evidence="purchase and received dimensions remain USER_APPROVAL_REQUIRED")
    add("FeederCableRouteEnvelope", box(432,320,580,12,12,130), purple, "feed", "segregated feeder/sensor cable service envelope; turn outside FD-DA-01 above Z710", "purchased_reference_envelope")

    # Horizontal extruder and fully connected 90-degree metal down-die.
    # The RFQ screw/barrel solids are also the assembly solids.  Local Z runs
    # from rear to die; rotate it to global -X so the 24 mm tip setback is real.
    from manufacturing import extruder_barrel, extruder_screw
    screw = extruder_screw(); screw.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -90); screw.translate(App.Vector(435, 347, 382))
    barrel = one_solid(extruder_barrel()); barrel.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -90); barrel.translate(App.Vector(375, 347, 382))
    thrust = thrust_plate_shape(); thrust.translate(App.Vector(389, 347-47.5, 382-52.5))
    add("ThrustPlate", thrust, steel, "extruder", "EX-THR-01 12 mm steel")
    thrust_bearing = Part.makeCylinder(14,9,App.Vector(389,347,382),App.Vector(1,0,0)).cut(
        Part.makeCylinder(7.5,9,App.Vector(389,347,382),App.Vector(1,0,0)))
    add("ScrewThrustBearing",one_solid(thrust_bearing),purple,"extruder","NSK 51102 15x28x9 reference envelope","purchased_reference_envelope")
    add("Screw", screw, orange, "extruder", "EX-SCR-01 SCM440 QT + gas nitride")
    add("Barrel", barrel, steel, "extruder", "EX-BAR-01 SCM440 QT + gas nitride")
    thermal = json.loads((ROOT/"cad/parameters/baseline.json").read_text())["extruder"]
    ranges = thermal["heater_zone_axial_ranges_from_barrel_rear_mm"]
    for zone, ((z0, z1), sensor_z) in enumerate(zip(ranges, thermal["barrel_sensor_bores_mm"]), start=1):
        band=mica_band_heater_shape(width=z1-z0); band.translate(App.Vector(0,0,z0)); band.rotate(App.Vector(),App.Vector(0,1,0),-90); band.translate(App.Vector(375,347,382))
        add(f"BarrelBandHeaterZ{zone}",band,orange,"extruder",f"24 V 100 W custom mica band ID34.00 W{z1-z0:g} zone {zone}","purchased_reference_envelope")
        probe=k_type_probe_shape(insertion_length=5.20); probe.rotate(App.Vector(),App.Vector(1,0,0),90); probe.translate(App.Vector(375-sensor_z,364,382))
        add(f"TemperatureProbeT{zone}",probe,purple,"extruder",f"T{zone} Tempco MTA1 custom K/U/Q probe; Ø3.00±0.03, 5.20±0.05 stop collar")
        retainer=thermocouple_retainer_shape(); retainer.rotate(App.Vector(),App.Vector(0,1,0),90); retainer.translate(App.Vector(375-sensor_z,364.8,382))
        add(f"TemperatureProbeRetainerT{zone}",retainer,steel,"extruder","TH-TCR-01 304SS stop-collar bridge; 2xM3")
    add("BarrelThermalFuse",box(263,343,401.5,22,8,12),red,"extruder","independent 300 C one-shot fuse on metal clamp in inter-zone gap")
    shield = hot_shield_shape(); shield.translate(App.Vector(40, 310, 340))
    for x,z,radius in ((315,382,3.0),(240,382,3.0),(165,382,3.0),(280,382,2.0),(205,382,2.0),(130,382,2.0),(62.5,397,2.0)):
        shield=shield.cut(cyl(radius,75,x,310,z,(0,1,0)))
    add("HotShield", shield, aluminum, "extruder", "grounded sheet")
    drive = box(401, 310, 340, 55, 75, 85).cut(
        Part.makeCylinder(18, 55, App.Vector(401, 347, 382), App.Vector(1, 0, 0))
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
    add("DieCartridgeHeater",die_heater,red,"extruder","TH-DIE-01 custom 24 V 60 W Ø6.50 CG x39.50 with MFR flange in Ø6.55 H7 bore","purchased_reference_envelope")
    die_probe=k_type_probe_shape(insertion_length=10.0); die_probe.rotate(App.Vector(),App.Vector(1,0,0),-90); die_probe.translate(App.Vector(62.5,327,397))
    add("TemperatureProbeT4",die_probe,purple,"extruder","T4 Tempco MTA1 custom K/U/Q probe; Ø3.00±0.03, 10.00±0.05 stop collar")
    die_probe_retainer=thermocouple_retainer_shape(); die_probe_retainer.translate(App.Vector(62.5,324.7,397))
    add("TemperatureProbeRetainerT4",die_probe_retainer,steel,"extruder","TH-TCR-01 304SS stop-collar bridge; 2xM3")
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
    add("PPR-C05_CoolingDuctLower",printed_at("PPR-C05",(34.5,309.5,128)),blue,"forming","ABS")
    add("PPR-C05_CoolingDuctUpper",printed_at("PPR-C05",(34.5,309.5,228)),blue,"forming","ABS")
    add("PPR-C06_GaugeX",printed_at("PPR-C06",(27.0,312.0,96)),purple,"forming","ABS/optics")
    gauge_y=printed["PPR-C06"].copy(); gauge_y.rotate(App.Vector(0,0,0),App.Vector(0,0,1),90); gauge_y.translate(App.Vector(109.5,299.5,68))
    add("PPR-C06_GaugeY",gauge_y,purple,"forming","ABS/optics")
    front_plate = puller_plate_shape(); front_plate.translate(App.Vector(24.5, 310, 15))
    rear_plate = puller_plate_shape().mirror(App.Vector(), App.Vector(0, 1, 0)); rear_plate.translate(App.Vector(24.5, 390, 15))
    add("PullerPlateFront", front_plate, steel, "forming", "PL-01 10 mm metal")
    add("PullerPlateRear", rear_plate, steel, "forming", "PL-01 10 mm metal")
    for x in (53.6, 95.4):
        roller = puller_roller_shape(); roller.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90); roller.translate(App.Vector(x, 320, 35))
        add(f"PullerRoll{x}", roller, green, "forming", "PL-02 Ø40 x60 roller, Ø8.2 bore")
        add(f"PullerSpindle{x}", cyl(4,80,x,310,35,(0,1,0)), steel, "forming", "FM-AX-01 Ø8 h6 x80 metal spindle")
    front_bush = puller_eccentric_bushing_shape(); front_bush.translate(App.Vector(94.4, 310, 35))
    rear_bush = puller_eccentric_bushing_shape().mirror(App.Vector(), App.Vector(0, 1, 0)); rear_bush.translate(App.Vector(94.4, 390, 35))
    add("PullerEccentricBushFront", front_bush, steel, "forming", "FM-EB-01 S45C eccentric pressure bushing")
    add("PullerEccentricBushRear", rear_bush, steel, "forming", "FM-EB-01 S45C eccentric pressure bushing")
    add("FormingCableRouteEnvelope", box(20,286,52,125,12,12), purple, "forming", "gauge/puller sensor cable service envelope", "purchased_reference_envelope")
    add("PPR-C07_PullerGuard",printed_at("PPR-C07",(20,300,0)),blue,"forming","ABS")

    # Solid guide, dancer/traverse and maximum spool motion.
    guide = guide_roller_shape(); guide.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), -90); guide.translate(App.Vector(175, 375, 90))
    add("GuideRoller", guide, green, "spooler", "FM-GR-01 Ø36 x20 roller, two retained Ø16 H7 bearing seats")
    add("GuideRollerAxle", cyl(2.5,30,175,370,90,(0,1,0)), steel, "spooler", "FM-GA-01 Ø5 h6 x30 fixed metal axle")
    add("GuideBearingFront", cyl(8,5,175,376.05,90,(0,1,0)).cut(cyl(2.5,5,175,376.05,90,(0,1,0))), purple, "spooler", "SKF 625-2Z 5x16x5")
    add("GuideBearingRear", cyl(8,5,175,388.95,90,(0,1,0)).cut(cyl(2.5,5,175,388.95,90,(0,1,0))), purple, "spooler", "SKF 625-2Z 5x16x5")
    front_cap = guide_roller_retainer_shape(); front_cap.rotate(App.Vector(), App.Vector(1,0,0), -90); front_cap.translate(App.Vector(175,375.05,90))
    rear_cap = guide_roller_retainer_shape(); rear_cap.rotate(App.Vector(), App.Vector(1,0,0), -90); rear_cap.translate(App.Vector(175,393.95,90))
    add("GuideBearingRetainerFront", front_cap, steel, "spooler", "FM-GC-01 flush metal retainer")
    add("GuideBearingRetainerRear", rear_cap, steel, "spooler", "FM-GC-01 flush metal retainer")
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
    front_bearing_plate = spool_bearing_plate_shape().mirror(App.Vector(), App.Vector(0,1,0)); front_bearing_plate.translate(App.Vector(305,492,145))
    rear_bearing_plate = spool_bearing_plate_shape(); rear_bearing_plate.translate(App.Vector(305,588,145))
    add("SpoolBearingPlateFront", front_bearing_plate, aluminum, "spooler", "SP-BP-01 10 mm pocket plate")
    add("SpoolBearingPlateRear", rear_bearing_plate, aluminum, "spooler", "SP-BP-01 10 mm pocket plate")
    front_retainer = spool_bearing_retainer_shape(); front_retainer.translate(App.Vector(305,492,145))
    rear_retainer = spool_bearing_retainer_shape().mirror(App.Vector(), App.Vector(0,1,0)); rear_retainer.translate(App.Vector(305,588,145))
    add("SpoolBearingRetainerFront", front_retainer, steel, "spooler", "SP-BR-01 2 mm metal retainer")
    add("SpoolBearingRetainerRear", rear_retainer, steel, "spooler", "SP-BR-01 2 mm metal retainer")
    add("SpoolBearingFront", cyl(14,8,335,484,175,(0,1,0)).cut(cyl(6.1,8,335,484,175,(0,1,0))), purple, "spooler", "6001-2RSH bearing")
    add("SpoolBearingRear", cyl(14,8,335,588,175,(0,1,0)).cut(cyl(6.1,8,335,588,175,(0,1,0))), purple, "spooler", "6001-2RSH bearing")
    add("PPR-C09_SpoolAdapterFront",printed_at("PPR-C09",(335,500,175),((1,0,0),-90)),blue,"spooler","PLA")
    add("PPR-C09_SpoolAdapterRear",printed_at("PPR-C09",(335,573,175),((1,0,0),90)),blue,"spooler","PLA")
    add("TraverseRodA", cyl(4, TRAVERSE["rod_length_mm"], *TRAVERSE["rod_origins_mm"][0], TRAVERSE["axis"]), steel, "spooler", "Ø8 h6 ground steel rod")
    add("TraverseRodB", cyl(4, TRAVERSE["rod_length_mm"], *TRAVERSE["rod_origins_mm"][1], TRAVERSE["axis"]), steel, "spooler", "Ø8 h6 ground steel rod")
    for collar in traverse_collar_rows(TRAVERSE):
        add(collar["name"], collar["shape"], steel, collar["group"], collar["material"],
            collar["classification"], evidence=collar["evidence"])
    left_traverse_plate = rotated_at(traverse_end_plate_shape(), TRAVERSE["plate_origins_mm"][0])
    right_traverse_plate = rotated_at(traverse_end_plate_shape(), TRAVERSE["plate_origins_mm"][1])
    add("TraverseEndPlateLeft", left_traverse_plate, aluminum, "spooler", "SP-TR-01 8 mm stepped metal bracket")
    add("TraverseEndPlateRight", right_traverse_plate, aluminum, "spooler", "SP-TR-01 8 mm stepped metal bracket")
    add("PPR-C10_TraverseCarriage",rotated_at(printed["PPR-C10"], TRAVERSE["carriage_origin_mm"]),blue,"spooler","PLA")
    add("DancerSensorEnvelope", box(158,426,105,12,12,22), purple, "spooler", "dancer analog sensor maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="electronics/io_schedule.csv DANCER; receipt dimensions and calibration required")
    add("TraverseLeftLimitEnvelope", box(*TRAVERSE["limit_origins_mm"][0],12,10,18), purple, "spooler", "positive-action left limit maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="electronics/io_schedule.csv TRAVERSE_LEFT_RIGHT_LIMIT; receipt dimensions required")
    add("TraverseRightLimitEnvelope", box(*TRAVERSE["limit_origins_mm"][1],12,10,18), purple, "spooler", "positive-action right limit maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="electronics/io_schedule.csv TRAVERSE_LEFT_RIGHT_LIMIT; receipt dimensions required")
    add("SpoolerTachSensorEnvelope", box(350,472,188,14,10,18), purple, "spooler", "20 PPR Hall sensor maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="electronics/io_schedule.csv SPOOLER_PWM_DIR_TACH; receipt dimensions and air gap required")
    add("SpoolerCableRouteEnvelope", box(150,405,300,270,12,12), purple, "spooler", "dancer/traverse/spooler cable service envelope", "purchased_reference_envelope")

    spool_motor_plate = spool_motor_mount_shape(); spool_motor_plate.translate(App.Vector(309,602,149))
    add("SpoolMotorMount", spool_motor_plate, aluminum, "spooler", "SP-MM-01 universal metal plate")
    add("SpoolMotorEnvelope", box(314,612,154,42,48,42), red, "spooler", "unverified donor NEMA17-class envelope", "unverified_donor_envelope", evidence="label, body, shaft, current and mounting measurement required before coupling release")

    panel = open_front_sheet_shell(190, 35, 190, 2); panel.translate(App.Vector(255, 35, 330))
    for x,z,radius in ((330,505,9.5),*[(x,z,1.7) for x in (268,432) for z in (373,477)]):
        panel = panel.cut(cyl(radius,8,x,33,z,(0,1,0)))
    panel = panel.cut(cyl(20.5,6,253,52,480,(1,0,0)))
    add("ControlPanel", panel, blue, "control", "CT-01 2 mm sheet enclosure")
    add("PPR-C11_ControlBezel",printed_at("PPR-C11",(260,43,365),((1,0,0),90)),blue,"control","PLA")
    add("ControlEmergencyStopEnvelope", cyl(20,30,227,52,480,(1,0,0)), red, "control", "SF-01 latching E-stop maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="BOM SF-01; positive-opening contact and receipt dimensions required")
    add("ControlEncoderEnvelope", cyl(9,22,330,31,505,(0,1,0)), purple, "control", "UI encoder maximum envelope; exact model unverified", "unverified_donor_envelope", evidence="CT-01 UI contract; receipt shaft/body dimensions required")
    add("ControlSafetyInputEnvelope", box(270,70,440,70,24,35), purple, "control", "hardwired safety relay/input terminal envelope", "unverified_donor_envelope", evidence="BOM SF-01/SF-02; exact relay and terminals require approval")
    for index,(x,z) in enumerate(((268,373),(432,373),(268,477),(432,477)),start=1):
        add(f"ControlBezelM3Fastener{index}", cyl(1.5,12,x,33,z,(0,1,0)), orange, "control", "PPR-C11 M3 bezel fastener")
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
