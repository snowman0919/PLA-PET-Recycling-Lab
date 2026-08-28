"""Manufacturing geometry for compact v0.3 VE drive, Gate-1 jig and extruder RFQ.

All dimensions are millimetres.  Shapes in this module are fabrication/review
geometry; physical Gate-1 and Gate-3 remain release locks.
"""

from __future__ import annotations

import math

import FreeCAD as App
import Part

from geometry import (
    bearing_retainer_plate,
    bearing_side_plate,
    cutter_shaft,
    hook_disc,
    screen_plate,
    spur_phase_gear,
)


def universal_motor_plate():
    """6 mm metal plate accepting donor gearmotor brackets, not one MPN."""
    plate = Part.makeBox(180, 140, 6)
    # Frame/angle attachment.
    for x in (12, 168):
        for y in (12, 128):
            plate = plate.cut(Part.makeCylinder(3.3, 6, App.Vector(x, y, 0)))
    # Four long slots accept a separate motor-specific angle or saddle.
    for x in (45, 90, 135):
        slot = Part.makeBox(9, 70, 6, App.Vector(x - 4.5, 35, 0))
        plate = plate.cut(slot)
    # Chain tension adjustment slots at the driven-side frame interface.
    for y in (28, 112):
        plate = plate.cut(Part.makeBox(55, 9, 6, App.Vector(62.5, y - 4.5, 0)))
    return plate


def bolt_on_sprocket_hub(bore=20.2):
    """Common hub: shaft/key on one side, any qualified sprocket blank on PCD36."""
    hub = Part.makeCylinder(25, 20).cut(Part.makeCylinder(bore / 2, 20))
    hub = hub.cut(Part.makeBox(6.2, 20, 6, App.Vector(-3.1, 0, 7.0)))
    for angle in (0, 90, 180, 270):
        a = math.radians(angle)
        hub = hub.cut(Part.makeCylinder(3.3, 20, App.Vector(18 * math.cos(a), 18 * math.sin(a), 0)))
    return hub


def generic_phase_gear_lamination():
    """One of three 6 mm steel laminations per phase gear, M3 Z16 20 degree."""
    return spur_phase_gear(module=3.0, teeth=16, thickness=6.0, bore=20.2)


def gate1_base_plate():
    plate = Part.makeBox(320, 240, 8)
    for x in (20, 300):
        for y in (20, 220):
            plate = plate.cut(Part.makeCylinder(4.5, 8, App.Vector(x, y, 0)))
    # Two side-plate foot patterns.  Slots permit shim alignment.
    for y in (58, 198):
        for x in (95, 245):
            plate = plate.cut(Part.makeBox(18, 7, 8, App.Vector(x - 9, y - 3.5, 0)))
    return plate


def gate1_torque_arm():
    arm = Part.makeBox(300, 25, 6)
    arm = arm.cut(Part.makeCylinder(10.1, 6, App.Vector(20, 12.5, 0)))
    arm = arm.cut(Part.makeBox(6.2, 6, 6, App.Vector(16.9, 12.5, 0)))
    # Force application hole is exactly 250 mm from shaft centre.
    arm = arm.cut(Part.makeCylinder(4.5, 6, App.Vector(270, 12.5, 0)))
    return arm


def gate1_feed_chute():
    outer = Part.makeBox(120, 90, 95)
    inner = Part.makeBox(117.6, 87.6, 95, App.Vector(1.2, 1.2, 1.2))
    chute = outer.cut(inner)
    # Anti-reach offset baffle; coupon strips enter with a push stick only.
    chute = chute.fuse(Part.makeBox(100, 1.2, 30, App.Vector(10, 44.4, 37)))
    return chute


def gate1_chip_tray():
    outer = Part.makeBox(180, 160, 42)
    inner = Part.makeBox(177.6, 157.6, 42, App.Vector(1.2, 1.2, 1.2))
    return outer.cut(inner)


def gate1_guard_frame():
    """Printed low-load corners for 3 mm polycarbonate; sheet is in the BOM."""
    corner = Part.makeBox(10, 10, 180)
    corner = corner.cut(Part.makeBox(6, 2, 176, App.Vector(2, 6, 4)))
    corner = corner.cut(Part.makeBox(2, 6, 176, App.Vector(6, 2, 4)))
    return corner


def gate1_parts():
    return [
        dict(id="G1J-01", name="Reusable jig base plate", shape=gate1_base_plate(), qty=1, material="6-8 mm donor steel/aluminum plate", process="laser/drill or donor plate drill template", class_="metal"),
        dict(id="G1J-02", name="250 mm torque arm", shape=gate1_torque_arm(), qty=1, material="6 mm S45C/structural steel", process="laser cut + deburr", class_="metal"),
        dict(id="G1J-P01", name="Anti-reach coupon feed chute", shape=gate1_feed_chute(), qty=1, material="PLA", process="FDM", class_="print"),
        dict(id="G1J-P02", name="Removable chip collection tray", shape=gate1_chip_tray(), qty=1, material="PLA", process="FDM", class_="print"),
        dict(id="G1J-P03", name="Polycarbonate guard corner", shape=gate1_guard_frame(), qty=4, material="PLA", process="FDM", class_="print"),
    ]


def gate1_assembly(exploded=False):
    """Nominal Gate-1 arrangement using final CUT-03/05/08 and two CUT-01 coupons."""
    items = []

    def add(name, shape, color, group, material):
        if exploded:
            offsets = {"base": (0, 0, -30), "rotor": (0, 0, 25), "measure": (35, -20, 30), "guard": (0, 30, 55)}
            dx, dy, dz = offsets.get(group, (0, 0, 0))
            shape = shape.copy(); shape.translate(App.Vector(dx, dy, dz))
        items.append(dict(name=name, shape=shape, color=color, group=group, material=material))

    steel=(85,98,108); orange=(226,116,55); purple=(119,89,145); blue=(54,129,168); clear=(174,218,232); green=(65,151,96)
    add("G1JBase", gate1_base_plate(), steel, "base", "donor metal plate")
    # Side plates are final-machine CUT-03 geometry, stood upright at y=58/198.
    for y_max, label in ((70, "Front"), (210, "Rear")):
        p=bearing_side_plate(); p.rotate(App.Vector(),App.Vector(1,0,0),90); p.translate(App.Vector(85,y_max,18))
        add(f"CUT03{label}",p,steel,"rotor","final CUT-03")
    for cx in (135,183):
        shaft=cutter_shaft(); shaft.translate(App.Vector(cx,28,73)); add(f"CUT05Shaft{cx}",shaft,steel,"rotor","final CUT-05")
        for y in (58,198):
            b=Part.makeCylinder(21,12,App.Vector(cx,y,73),App.Vector(0,1,0)).cut(Part.makeCylinder(10.1,12,App.Vector(cx,y,73),App.Vector(0,1,0)))
            add(f"Bearing{cx}_{y}",b,purple,"rotor","6004-2RS")
    # One coupon per shaft, axially interleaved by 6.5 mm.
    for cx, y, angle in ((135,112,0),(183,118.5,180/7)):
        d=hook_disc(); d.rotate(App.Vector(),App.Vector(0,1,0),angle); d.translate(App.Vector(cx,y,73)); add(f"CUT01Coupon{cx}",d,orange,"rotor","CUT-01 coupon")
    screen=screen_plate(); screen.translate(App.Vector(91.5,82,38)); add("CUT04ScreenCoupon",screen,green,"rotor","CUT-04 5 mm screen coupon")
    # Three generic 6 mm laminations per gear; one pair is reusable in final machine.
    lam=generic_phase_gear_lamination()
    for cx, phase in ((135,0),(183,180/16)):
        for index in range(3):
            g=lam.copy(); g.rotate(App.Vector(),App.Vector(0,1,0),phase); g.translate(App.Vector(cx,214+6*index,73)); add(f"PhaseLam{cx}_{index}",g,purple,"rotor","S45C lamination")
    arm=gate1_torque_arm(); arm.rotate(App.Vector(),App.Vector(1,0,0),90); arm.translate(App.Vector(115,52,73)); add("TorqueArm250",arm,green,"measure","metal")
    load=Part.makeBox(45,25,45,App.Vector(365,34,40)); add("ForceGauge",load,purple,"measure","0-200 N force gauge/load cell")
    chute=gate1_feed_chute(); chute.translate(App.Vector(99,82,108)); add("FeedChute",chute,blue,"guard","printed")
    tray=gate1_chip_tray(); tray.translate(App.Vector(70,68,8)); add("ChipTray",tray,blue,"base","printed")
    # Transparent guard is represented as four 3 mm panels and four printed corners.
    add("GuardFront",Part.makeBox(230,3,180,App.Vector(65,45,18)),clear,"guard","3 mm polycarbonate")
    add("GuardRear",Part.makeBox(230,3,180,App.Vector(65,222,18)),clear,"guard","3 mm polycarbonate")
    add("GuardLeft",Part.makeBox(3,180,180,App.Vector(65,45,18)),clear,"guard","3 mm polycarbonate")
    right_panel=Part.makeBox(3,180,180,App.Vector(292,45,18))
    right_panel=right_panel.cut(Part.makeBox(3,18,42,App.Vector(292,43,68)))
    add("GuardRight",right_panel,clear,"guard","3 mm polycarbonate with torque-arm slot")
    add("TorqueSlotBaffle",Part.makeBox(30,3,55,App.Vector(286,35,60)),clear,"guard","3 mm polycarbonate offset fragment baffle")
    for x,y in ((65,45),(285,45),(65,215),(285,215)):
        c=gate1_guard_frame(); c.translate(App.Vector(x,y,18)); add(f"GuardCorner{x}_{y}",c,blue,"guard","printed")
    return items


def helical_flight_reference(length, z_offset=0, facet_step=1.0):
    """1 mm axial-facet quotation ridge with exact pitch and OD envelope."""
    segments=[]

    def section(z):
        if z < 128:
            root=5.44
        elif z < 192:
            root=5.44+(z-128)*1.60/64
        else:
            root=7.04
        theta=2*math.pi*z/16.0
        c,s=math.cos(theta),math.sin(theta)
        points=[
            App.Vector(root*c,root*s,z+z_offset-0.8),
            App.Vector(7.96*c,7.96*s,z+z_offset-0.8),
            App.Vector(7.96*c,7.96*s,z+z_offset+0.8),
            App.Vector(root*c,root*s,z+z_offset+0.8),
        ]
        points.append(points[0])
        return Part.Wire(Part.makePolygon(points).Edges)

    z=0.8
    while z < length-0.8-1e-6:
        z2=min(z+facet_step,length-0.8)
        segments.append(Part.makeLoft([section(z),section(z2)],True,False))
        z=z2
    return Part.makeCompound(segments)


def extruder_screw(facet_step=1.0):
    """16 mm, 16 L/D single-start screw with 8D/4D/4D zones.

    The helical sweep is quotation geometry.  The dimensioned notes remain
    controlling because FreeCAD tessellation does not encode GD&T.
    """
    feed_root=10.88/2; meter_root=14.08/2
    core=Part.makeCylinder(feed_root,128)
    core=core.fuse(Part.makeCone(feed_root,meter_root,64,App.Vector(0,0,128)))
    core=core.fuse(Part.makeCylinder(meter_root,64,App.Vector(0,0,192)))
    flight=helical_flight_reference(256,60,facet_step)
    # Rear drive/thrust features: total length 316 mm; active section z=60..316.
    core.translate(App.Vector(0,0,60))
    drive=Part.makeCylinder(6,35,App.Vector(0,0,0))
    drive=drive.cut(Part.makeBox(4.2,35,3.2,App.Vector(-2.1,0,3.8)))
    thrust=Part.makeCylinder(7.5,20,App.Vector(0,0,35))
    neck=Part.makeCylinder(feed_root,5,App.Vector(0,0,55))
    # Keep the helical CAM-reference ridge as a second valid solid in the STEP;
    # the controlling drawing requires the supplier to merge/finish the flight.
    return Part.makeCompound([drive.fuse(thrust).fuse(neck).fuse(core),flight])


def extruder_screw_process_coupon():
    """Three-pitch SCM440 supplier coupon; not an operating screw."""
    core=Part.makeCylinder(10.88/2,48)
    flight=helical_flight_reference(48)
    return Part.makeCompound([core,flight])


def extruder_barrel_process_coupon():
    """Matched 60 mm bore/hone/nitride coupon."""
    return Part.makeCylinder(17,60).cut(Part.makeCylinder(8.10,60))


def extruder_barrel():
    """SCM440 barrel quotation geometry, 34 OD x 16.20 ID x 280."""
    outer=Part.makeCylinder(17,280)
    bore=Part.makeCylinder(8.10,280)
    barrel=outer.cut(bore)
    # 18 x 20 mm feed opening, 12..32 mm from rear datum A.
    feed=Part.makeBox(18,34,20,App.Vector(-9,-17,12))
    barrel=barrel.cut(feed)
    # Four M5 front flange holes on PCD28, axial 10 mm deep.
    for angle in (45,135,225,315):
        a=math.radians(angle)
        hole=Part.makeCylinder(2.1,10,App.Vector(14*math.cos(a),14*math.sin(a),270))
        barrel=barrel.cut(hole)
    return barrel


def extruder_rfq_parts():
    return [
        dict(id="EX-SCR-01",name="16 mm x 16D single screw",shape=extruder_screw(),qty=1,material="SCM440 QT + gas nitride",process="turn, 4-axis flight mill, polish, nitride, finish grind"),
        dict(id="EX-BAR-01",name="ID16.20 x OD34 barrel",shape=extruder_barrel(),qty=1,material="SCM440 QT + gas nitride bore",process="deep drill/ream, hone, mill feed port, nitride, final hone"),
        dict(id="EX-CPN-SCR",name="Three-pitch screw process coupon",shape=extruder_screw_process_coupon(),qty=1,material="SCM440 QT + gas nitride",process="same flight mill/polish/nitride route as EX-SCR-01"),
        dict(id="EX-CPN-BAR",name="Matched barrel process coupon",shape=extruder_barrel_process_coupon(),qty=1,material="SCM440 QT + gas nitride bore",process="same bore/hone/nitride route as EX-BAR-01"),
    ]
