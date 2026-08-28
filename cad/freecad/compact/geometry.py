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


def hook_disc(od=58.0, root=36.0, thickness=6.0, hooks=7):
    pts = []
    for i in range(hooks):
        a = 2 * math.pi * i / hooks
        for offset, radius in ((0.0, root / 2), (0.16, od / 2), (0.56, od / 2 - 2), (0.86, root / 2)):
            t = a + offset * (2 * math.pi / hooks)
            pts.append(App.Vector(radius * math.cos(t), 0, radius * math.sin(t)))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    disc = face.extrude(App.Vector(0, thickness, 0))
    return disc.cut(cyl(10.1, thickness, 0, 0, 0, (0, 1, 0)))


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
    def cutter_plate(y):
        plate = box(55, y, 535, 150, 12, 125)
        for cx in (105, 153): plate = plate.cut(cyl(21.2, 12, cx, y, 590, (0, 1, 0)))
        for x in (70, 190):
            for z in (550, 645): plate = plate.cut(cyl(3.3, 12, x, y, z, (0, 1, 0)))
        return plate
    add("CutterPlateFront", cutter_plate(315), steel, "shredder", "steel")
    add("CutterPlateRear", cutter_plate(455), steel, "shredder", "steel")
    for cx in (105, 153):
        add(f"Shaft{cx}", cyl(10, 152, cx, 315, 590, (0, 1, 0)), steel, "shredder", "steel")
        for i in range(6):
            d = hook_disc()
            axial_offset = 0.0 if cx == 105 else 6.5
            if cx == 153: d.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 25.714)
            d.translate(App.Vector(cx, 339 + axial_offset + i * 13, 590))
            add(f"Hook{cx}_{i}", d, orange, "shredder", "tool steel")
        for y in (315, 455):
            bearing = cyl(21, 12, cx, y, 590, (0, 1, 0)).cut(cyl(10.1, 12, cx, y, 590, (0, 1, 0)))
            add(f"Bearing{cx}_{y}", bearing, purple, "shredder", "6004")
    for x in (70, 190):
        for z in (550, 645): add(f"M6Fastener{x}_{z}", cyl(3, 164, x, 307, z, (0, 1, 0)), orange, "shredder", "M6 steel")
    add("Screen", box(60, 330, 556, 135, 120, 3), green, "shredder", "stainless")
    add("ShredderMotor", box(205, 380, 555, 85, 90, 80), red, "shredder", "donor/verify")
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
