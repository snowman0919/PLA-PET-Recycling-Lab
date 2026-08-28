"""Actual compact v0.3 FreeCAD geometry and print-part definitions."""

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
    return outer.cut(inner)


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


def hook_disc(od=58.0, root=36.0, thickness=6.0, hooks=7, capture_samples=18, relief_samples=8):
    """Asymmetric cycloidal-derived hook disc.

    A long 76 % capture flank follows a cycloidal radial rise.  A short nose
    and 24 % relief flank create the hook asymmetry.  This is a manufacturable
    2-D laser/waterjet profile, not a generic saw-tooth placeholder.
    """
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


def cutter_shaft(length=220.0):
    shaft = Part.makeCylinder(10, length, App.Vector(0, 0, 0), App.Vector(0, 1, 0))
    for y, key_length in ((0.0, 30.0), (45.0, 100.0), (180.0, 40.0)):
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
    plate = Part.makeBox(125, 110, 6)
    for x in (25, 98.5):
        for y in (30, 50):
            plate = plate.cut(Part.makeBox(9, 24, 6, App.Vector(x - 4.5, y - 12, 0)))
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
        dict(id="CUT-05", name="20 mm keyed cutter shaft", shape=shaft, qty=2, material="S45C", process="turn + keyway", critical="diameter 20 h6 at two 6004 journals per shaft; overall 220.0 +/-0.10; TIR <=0.05; 6 mm keyways at y=0-30, 45-145 and 180-220 from motor end; keyway depth 3.5; use standard metal clamp collars for axial retention"),
        dict(id="CUT-06", name="Phase gear axial spacer", shape=Part.makeCylinder(15, 4).cut(Part.makeCylinder(10.1, 4)), qty=2, material="steel", process="simple turning", critical="OD 30.0; bore 20.2 +0.10/0; length 4.00 +/-0.03; faces parallel within 0.03"),
        dict(id="CUT-07", name="MY1016Z slotted motor plate", shape=motor_mount, qty=1, material="6 mm steel", process="laser cut + deburr; separate standard angle brackets", critical="125 x 110 x 6; 9 x 24 slots cover measured 20/73.5 mm patterns; slot-center families x=25.0/98.5 and y=30/50; final bracket drilling is HOLD until received motor pilot, bolt pattern, shaft height and rotation envelope are measured"),
        dict(id="CUT-08", name="Dual 6004 bearing retainer", shape=bearing_retainer, qty=2, material="2 mm steel", process="laser cut + deburr", critical="figure-eight OD lobes 60; two relief bores diameter 34; center distance 48.00 +/-0.05; six M4 clearance holes diameter 4.5 at drawing coordinates; CUT-03 matching holes are included and may be match-reamed after bearing-seat finish"),
    ]


def print_parts():
    lid = Part.makeBox(195, 195, 2).fuse(Part.makeBox(195, 4, 6)).fuse(Part.makeBox(195, 4, 6, App.Vector(0, 191, 0)))
    chute = shell_box(190, 150, 90, 2).fuse(Part.makeBox(170, 2, 28, App.Vector(10, 45, 28))).fuse(Part.makeBox(170, 2, 28, App.Vector(10, 102, 28)))
    # Four small corner extrusions capture 1 mm PP/ABS sheet panels; the large
    # bin faces are deliberately not printed.
    flake_bin = Part.makeBox(25, 3, 120).fuse(Part.makeBox(3, 25, 120)).fuse(Part.makeBox(25, 25, 3))
    handle = Part.makeBox(120, 25, 20).cut(Part.makeBox(88, 25, 10, App.Vector(16, 0, 5)))
    duct = shell_box(80, 75, 135, 2, bottom=False)
    gauge = shell_box(95, 70, 28, 2).cut(Part.makeBox(8, 70, 10, App.Vector(43.5, 0, 9)))
    guard = shell_box(150, 100, 65, 2).cut(Part.makeBox(100, 100, 32, App.Vector(25, 0, 16)))
    bracket = Part.makeBox(60, 5, 70).fuse(Part.makeBox(60, 45, 5)).cut(cyl(4.2, 5, 30, 0, 50, (0, 1, 0)))
    adapter = Part.makeCone(18, 35, 35).cut(Part.makeCone(14, 31, 33, App.Vector(0, 0, 2))).cut(cyl(6.1, 35, 0, 0, 0))
    carriage = Part.makeBox(90, 55, 8).fuse(Part.makeBox(90, 6, 16, App.Vector(0, 0, 8))).fuse(Part.makeBox(90, 6, 16, App.Vector(0, 49, 8))).cut(cyl(4.2, 90, 0, 15, 4, (1, 0, 0))).cut(cyl(4.2, 90, 0, 40, 4, (1, 0, 0)))
    bezel = Part.makeBox(180, 120, 5).cut(Part.makeBox(145, 82, 5, App.Vector(17.5, 19, 0)))
    clip = Part.makeBox(24, 18, 18).cut(Part.makeBox(14, 18, 13, App.Vector(5, 0, 5))).cut(Part.makeBox(6, 18, 8, App.Vector(9, 0, 10)))
    return [
        dict(id="PPR-C01", name="Sliding hopper lid", shape=lid, qty=1, material="PLA", orientation="flat", layer="0.24 mm", walls=4, infill="20%", support="no", fastener="M4 captured nut", tolerance="0.35 mm slide", mating="metal hopper rails", order=3),
        dict(id="PPR-C02", name="Anti-reach baffle chute", shape=chute, qty=1, material="PLA", orientation="outlet down", layer="0.24 mm", walls=5, infill="25%", support="baffle edges only", fastener="M4x12 + captured nut", tolerance="0.40 mm flake path", mating="hopper and metal cutter chamber", order=4),
        dict(id="PPR-C03", name="Flake bin sheet corner", shape=flake_bin, qty=4, material="PLA", orientation="end down", layer="0.28 mm", walls=4, infill="25%", support="no", fastener="M3x8 captured nut", tolerance="0.30 mm sheet slot", mating="1 mm sheet bin and screen rails", order=7),
        dict(id="PPR-C04", name="Screen drawer handle", shape=handle, qty=1, material="PLA", orientation="back flat", layer="0.24 mm", walls=5, infill="35%", support="no", fastener="M5x16 + washer", tolerance="0.25 mm", mating="metal screen", order=6),
        dict(id="PPR-C05", name="Cooling duct segment", shape=duct, qty=2, material="ABS", orientation="end face down", layer="0.24 mm", walls=4, infill="15%", support="no", fastener="M4x12", tolerance="0.30 mm tongue", mating="80 mm fan and next duct", order=13),
        dict(id="PPR-C06", name="Gauge enclosure half", shape=gauge, qty=2, material="ABS", orientation="outer face down", layer="0.20 mm", walls=4, infill="25%", support="slot bridge only", fastener="M3x12 + heat-set insert", tolerance="0.20 mm optical slit", mating="LED/photodiode cross frame", order=14),
        dict(id="PPR-C07", name="Puller pinch guard", shape=guard, qty=1, material="ABS", orientation="outer face down", layer="0.24 mm", walls=5, infill="20%", support="window bridge only", fastener="M4 captive screw", tolerance="0.40 mm guard gap", mating="metal puller plate", order=15),
        dict(id="PPR-C08", name="Solid-strand guide bracket", shape=bracket, qty=2, material="PLA", orientation="L side", layer="0.20 mm", walls=5, infill="40%", support="yes under bore", fastener="M5x16", tolerance="0.25 mm bearing fit", mating="625 bearing and profile", order=16),
        dict(id="PPR-C09", name="Spool cone adapter", shape=adapter, qty=2, material="PLA", orientation="large face down", layer="0.20 mm", walls=5, infill="35%", support="no", fastener="M6 metal clamp", tolerance="0.30 mm spool core", mating="12 mm metal spindle", order=18),
        dict(id="PPR-C10", name="Traverse carriage", shape=carriage, qty=1, material="PLA", orientation="flat", layer="0.20 mm", walls=5, infill="40%", support="rod bores only", fastener="M4 belt clamp", tolerance="0.20 mm after ream", mating="donor rods and GT2 belt", order=19),
        dict(id="PPR-C11", name="Control panel bezel", shape=bezel, qty=1, material="PLA", orientation="front face down", layer="0.20 mm", walls=4, infill="20%", support="no", fastener="M3x10 + heat-set insert", tolerance="0.25 mm TFT", mating="metal control panel", order=21),
        dict(id="PPR-C12", name="Cable duct clip", shape=clip, qty=8, material="PLA", orientation="side down", layer="0.20 mm", walls=4, infill="50%", support="no", fastener="M4x10", tolerance="0.30 mm snap", mating="20 mm profile", order=22),
    ]


def assembly_objects(exploded=False):
    objects = []
    def add(name, shape, color, group, material="mixed"):
        if exploded:
            offsets = {"input": (-35, 0, 35), "shredder": (-20, 0, 10), "feed": (25, 0, 25), "extruder": (0, -40, 0), "forming": (-25, -20, -25), "spooler": (35, 35, -10), "control": (30, -35, 10), "frame": (0, 0, 0)}
            dx, dy, dz = offsets.get(group, (0, 0, 0))
            shape = shape.copy(); shape.translate(App.Vector(dx, dy, dz))
        objects.append(dict(name=name, shape=shape, color=color, group=group, material=material))

    steel = (88, 101, 112); aluminum = (165, 177, 184); orange = (225, 116, 55)
    blue = (47, 122, 163); green = (69, 151, 97); purple = (119, 89, 145); red = (185, 54, 54)
    # Frame: four columns, top/bottom rectangles and mid rails.
    for x in (0, 450):
        for y in (0, 680): add(f"FrameColumn{x}_{y}", box(x, y, 0, 20, 20, 930), aluminum, "frame", "Al profile")
    for z in (0, 910):
        for y in (0, 680): add(f"FrameX{z}_{y}", box(0, y, z, 470, 20, 20), aluminum, "frame", "Al profile")
        for x in (0, 450): add(f"FrameY{z}_{x}", box(x, 0, z, 20, 700, 20), aluminum, "frame", "Al profile")
    for z in (320, 500):
        add(f"MidRail{z}", box(0, 290, z, 470, 20, 20), aluminum, "frame", "Al profile")

    hopper = cylindrical_hopper(100, 150, 60, 20); hopper.translate(App.Vector(125, 395, 750))
    add("MetalHopper", hopper, aluminum, "input", "2 mm sheet metal")
    add("SlidingLid", box(30, 290, 900, 195, 195, 8), blue, "input", "PLA")
    add("AntiReach", box(35, 305, 620, 190, 150, 70), blue, "input", "PLA")

    # Shredder metal load path.
    def placed_cutter_plate(y_max):
        plate = bearing_side_plate()
        plate.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
        plate.translate(App.Vector(55, y_max, 535))
        return plate
    add("CutterPlateFront", placed_cutter_plate(327), steel, "shredder", "CUT-03 steel")
    add("CutterPlateRear", placed_cutter_plate(467), steel, "shredder", "CUT-03 steel")
    for cx in (105, 153):
        shaft = cutter_shaft(); shaft.translate(App.Vector(cx, 285, 590))
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

    # One 24 V brushed geared-DC motor directly drives the right cutter shaft
    # through a KTR ROTEX 19 coupling.  A purchased, hardened M3 Z16 pair
    # fixes counter-rotation and phase at the 48 mm shaft centers.  Motor envelope is deliberately conservative
    # until the incoming MY1016Z-24V-250W-75RPM unit passes dimensional receipt.
    drive_gear = spur_phase_gear(module=3.0, teeth=16, thickness=30.0, bore=20.2)
    for cx in (105, 153):
        gear = drive_gear.copy()
        if cx == 153:
            gear.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 180.0 / 16.0)
        gear.translate(App.Vector(cx, 471, 590))
        add(f"PhaseGear{cx}", gear, purple, "shredder", "KHK SS3-16H, bore/key finish to 20 mm")
    add("ROTEX19Coupling", cyl(20.5, 66, 153, 244, 590, (0, 1, 0)), steel, "shredder", "KTR ROTEX 19 98ShA, bore 17/20")
    add("DriveGuard", box(70, 260, 525, 155, 48, 142), blue, "shredder", "1 mm grounded sheet + standoffs")
    add("MY1016ZGearbox", box(108, 225, 545, 90, 45, 90), red, "shredder", "MY1016Z secondary gearbox")
    add("MY1016ZMotor", cyl(50, 130, 153, 95, 590, (0, 1, 0)), red, "shredder", "MY1016Z-24V-250W-75RPM")
    motor_plate = motor_mount_plate()
    motor_plate.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90)
    motor_plate.translate(App.Vector(90, 231, 545))
    add("MotorMountPlate", motor_plate, steel, "shredder", "CUT-07 6 mm steel + standard metal angles")
    retainer = bearing_retainer_plate()
    front_retainer = retainer.copy(); front_retainer.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90); front_retainer.translate(App.Vector(55, 315, 535))
    rear_retainer = retainer.copy(); rear_retainer.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 90); rear_retainer.translate(App.Vector(55, 469, 535))
    add("BearingRetainerFront", front_retainer, steel, "shredder", "CUT-08 2 mm steel")
    add("BearingRetainerRear", rear_retainer, steel, "shredder", "CUT-08 2 mm steel")
    flake = shell_box(185, 175, 115, 2); flake.translate(App.Vector(45, 300, 410))
    add("FlakeBin", flake, blue, "feed", "thin PP sheet + printed corners")
    feed = cylindrical_hopper(78, 145, 55, 16); feed.translate(App.Vector(350, 420, 555))
    add("SealedFeedHopper", feed, aluminum, "feed", "2 mm sheet metal")
    add("Feeder", cyl(18, 105, 315, 345, 485, (0, 0, -1)), steel, "feed", "metal")

    # Horizontal extruder and 90-degree metal down die.
    add("ThrustPlate", box(380, 300, 330, 12, 95, 105), steel, "extruder", "steel")
    add("Barrel", cyl(17, 280, 95, 347, 382, (1, 0, 0)), steel, "extruder", "steel")
    shield = shell_box(300, 75, 85, 2, bottom=False); shield.translate(App.Vector(85, 310, 340))
    add("HotShield", shield, aluminum, "extruder", "grounded sheet")
    add("ExtruderDrive", box(390, 310, 340, 55, 75, 85), red, "extruder", "donor/verify")
    add("DownDie", cyl(12, 55, 95, 347, 365, (0, 0, -1)), orange, "extruder", "stainless")
    add("DieOrifice", cyl(1.5, 260, 95, 347, 310, (0, 0, -1)), (235, 205, 79), "forming", "filament")

    cooling = shell_box(80, 75, 190, 2, bottom=False); cooling.translate(App.Vector(55, 310, 120))
    add("CoolingDuct", cooling, blue, "forming", "ABS")
    gauge = shell_box(90, 85, 35, 2, bottom=False); gauge.translate(App.Vector(50, 305, 95))
    add("Gauge", gauge, purple, "forming", "ABS/optics")
    add("PullerPlate", box(45, 300, 55, 100, 95, 40), steel, "forming", "metal")
    for x in (75, 115): add(f"PullerRoll{x}", cyl(20, 25, x, 335, 75, (0, 1, 0)), green, "forming", "roller")

    # Solid guide, dancer/traverse and maximum spool motion.
    add("GuideRoller", cyl(18, 20, 175, 375, 90, (0, 1, 0)), green, "spooler", "bearing")
    add("DancerArm", box(180, 445, 110, 15, 105, 12), aluminum, "spooler", "metal")
    add("DancerSweep", cyl(65, 8, 188, 452, 115, (0, 1, 0)), (176, 220, 235), "spooler", "motion keepout")
    add("Spool", cyl(100, 73, 335, 500, 175, (0, 1, 0)), (223, 187, 104), "spooler", "1 kg spool")
    add("SpoolCore", cyl(26, 73, 335, 500, 175, (0, 1, 0)), steel, "spooler", "spindle")
    add("TraverseRail", box(245, 445, 280, 160, 12, 12), aluminum, "spooler", "donor rod")
    add("TraverseMotion", box(270, 438, 265, 80, 40, 35), purple, "spooler", "motion keepout")

    add("ControlPanel", box(255, 35, 330, 190, 35, 190), blue, "control", "metal/bezel")
    add("PSU", box(275, 80, 200, 160, 180, 90), red, "control", "24 V 600 W")
    add("CableDuct", box(425, 650, 80, 18, 18, 750), purple, "control", "fixed vertical duct")
    return objects
