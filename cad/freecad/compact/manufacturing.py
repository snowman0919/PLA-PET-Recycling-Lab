"""Manufacturing geometry for compact v0.4 drive, Gate-1 jig and extruder RFQ.

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
    gear=spur_phase_gear(module=3.0, teeth=16, thickness=6.0, bore=20.2)
    # Two M4 clamp bolts and one Ø3 H7 dowel on PCD30 make the three-sheet
    # stack deterministic without relying on tooth contact for registration.
    for angle,diameter in ((0,4.5),(120,4.5),(240,3.0)):
        a=math.radians(angle)
        hole=Part.makeCylinder(diameter/2,6,App.Vector(15*math.cos(a),0,15*math.sin(a)),App.Vector(0,1,0))
        gear=gear.cut(hole)
    return gear


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
    chute = chute.fuse(Part.makeBox(120, 1.2, 30, App.Vector(0, 44.4, 37)))
    return chute.removeSplitter()


def gate1_chip_tray():
    outer = Part.makeBox(180, 160, 42)
    inner = Part.makeBox(177.6, 157.6, 42, App.Vector(1.2, 1.2, 1.2))
    return outer.cut(inner)


def gate1_guard_frame():
    """Printed edge trim only; metal angles retain the polycarbonate."""
    corner = Part.makeBox(10, 10, 180)
    corner = corner.cut(Part.makeBox(6, 2, 176, App.Vector(2, 6, 4)))
    corner = corner.cut(Part.makeBox(2, 6, 176, App.Vector(6, 2, 4)))
    return corner


def _flat_panel(width,height,holes=True,mid_holes=False):
    panel=Part.makeBox(width,height,3)
    if holes:
        rows=(10,height/2,height-10) if mid_holes else (10,height-10)
        for x in (10,width-10):
            for y in rows:
                panel=panel.cut(Part.makeCylinder(2.25,3,App.Vector(x,y,0)))
    return panel


def gate1_guard_front_rear_panel():
    return _flat_panel(230,180,mid_holes=True)


def gate1_guard_left_panel():
    return _flat_panel(180,180,mid_holes=True)


def gate1_guard_right_panel():
    panel=_flat_panel(180,180,mid_holes=True)
    # After the panel rotates into the machine YZ plane, local X maps to Z and
    # local Y maps to machine Y.  The slot therefore opens from local Y=0 and
    # spans local X=53..82 to leave 2 mm around the arm at z=73..98.
    return panel.cut(Part.makeBox(29,20,3,App.Vector(53,0,0)))


def gate1_torque_slot_baffle():
    return _flat_panel(30,55)


def gate1_guard_upright():
    """20 x20 x2 standard metal angle, L180, with panel attachment holes."""
    angle=Part.makeBox(20,2,180).fuse(Part.makeBox(2,20,180))
    for z in (10,90,170):
        angle=angle.cut(Part.makeCylinder(2.25,20,App.Vector(10,0,z),App.Vector(0,1,0)))
        angle=angle.cut(Part.makeCylinder(2.25,20,App.Vector(0,10,z),App.Vector(1,0,0)))
    return angle


def gate1_screen_rail():
    """20 x20 x2 angle, L150, supporting the removable screen coupon."""
    rail=Part.makeBox(2,150,20).fuse(Part.makeBox(20,150,2))
    for y in (15,135):
        rail=rail.cut(Part.makeCylinder(2.75,20,App.Vector(10,y,0),App.Vector(0,0,1)))
    return rail


def gate1_interlock_bracket():
    """Universal 2 mm metal L bracket for a positive-opening guard switch."""
    bracket=Part.makeBox(50,30,2).fuse(Part.makeBox(50,2,30))
    for x in (12,38):
        bracket=bracket.cut(Part.makeBox(5,14,2,App.Vector(x-2.5,8,0)))
        bracket=bracket.cut(Part.makeCylinder(2.25,2,App.Vector(x,0,18),App.Vector(0,1,0)))
    return bracket


def gate1_plate_foot():
    """50 mm length of 40 x40 x4 standard angle for CUT-03 support."""
    foot=Part.makeBox(50,40,4).fuse(Part.makeBox(50,4,40))
    for x in (12,38):
        foot=foot.cut(Part.makeCylinder(3.3,4,App.Vector(x,20,0)))
        foot=foot.cut(Part.makeCylinder(3.3,4,App.Vector(x,0,20),App.Vector(0,1,0)))
    return foot


def gate1_parts():
    return [
        dict(id="G1J-01", name="Reusable jig base plate", shape=gate1_base_plate(), qty=1, material="8 mm donor steel/aluminum plate", process="laser/drill or donor plate drill template", class_="metal",critical="320 x240 x8; table holes Ø9; flatness <=0.30; deburr C0.5"),
        dict(id="G1J-02", name="250 mm torque arm", shape=gate1_torque_arm(), qty=1, material="6 mm S45C/structural steel", process="laser cut + deburr", class_="metal",critical="shaft bore Ø20.2 +0.10/0; 6.2 keyway; shaft centre to force hole 250.0 ±0.5; flatness 0.20"),
        dict(id="G1J-03", name="Front/rear guard panel", shape=gate1_guard_front_rear_panel(), qty=2, material="3 mm polycarbonate", process="CNC router/laser only if supplier permits; drill and deburr", class_="sheet",critical="230 x180 x3; 6x Ø4.5 at X10/220 and Y10/90/170; no acrylic; edges R0.5"),
        dict(id="G1J-04", name="Left guard panel", shape=gate1_guard_left_panel(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="180 x180 x3; 6x Ø4.5 at X10/170 and Y10/90/170; no acrylic; edges R0.5"),
        dict(id="G1J-05", name="Right slotted guard panel", shape=gate1_guard_right_panel(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="180 x180 x3; open-edge slot X53..82 x Y0..20; 2 mm minimum arm clearance; 6x Ø4.5; no cracks"),
        dict(id="G1J-06", name="Torque-slot offset baffle", shape=gate1_torque_slot_baffle(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="30 x55 x3; 4x Ø4.5; offset >=10 from arm slot; blocks line of sight"),
        dict(id="G1J-07", name="Metal guard upright", shape=gate1_guard_upright(), qty=4, material="20 x20 x2 aluminum/steel angle", process="saw cut + drill", class_="stock",critical="L180 ±0.5; 6x Ø4.5; verticality 0.5/180; primary fragment load path"),
        dict(id="G1J-08", name="Removable screen rail", shape=gate1_screen_rail(), qty=2, material="20 x20 x2 steel angle", process="saw cut + drill", class_="stock",critical="L150 ±0.5; 2x Ø5.5; screen plane shimmed for >=1.9 cutter clearance"),
        dict(id="G1J-09", name="Universal guard-interlock bracket", shape=gate1_interlock_bracket(), qty=1, material="2 mm steel", process="laser/drill + 90° bend", class_="metal",critical="50 x30 L bracket; 5 x14 slots; switch plunger overtravel per received switch"),
        dict(id="G1J-10", name="CUT-03 plate foot angle", shape=gate1_plate_foot(), qty=4, material="40 x40 x4 steel/aluminum angle", process="saw cut + drill", class_="stock",critical="L50 ±0.5; 4x Ø6.6; plate perpendicularity 0.20/125 after torque"),
        dict(id="G1J-P01", name="Anti-reach coupon feed chute", shape=gate1_feed_chute(), qty=1, material="PLA", process="FDM", class_="print",critical="3 walls minimum; no load-path duty; baffle intact"),
        dict(id="G1J-P02", name="Removable chip collection tray", shape=gate1_chip_tray(), qty=1, material="PLA", process="FDM", class_="print",critical="3 walls minimum; removable without rotor access"),
        dict(id="G1J-P03", name="Guard edge trim", shape=gate1_guard_frame(), qty=4, material="PLA", process="FDM", class_="print",critical="edge trim only; metal G1J-07 retains panel"),
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
    left_rail=gate1_screen_rail(); left_rail.translate(App.Vector(89.5,67,36)); add("G1J08ScreenRailLeft",left_rail,steel,"base","20 x20 x2 steel angle")
    right_rail=gate1_screen_rail(); right_rail.rotate(App.Vector(),App.Vector(0,0,1),180); right_rail.translate(App.Vector(228.5,217,36)); add("G1J08ScreenRailRight",right_rail,steel,"base","20 x20 x2 steel angle")
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
    # Primary guard retention is metal angle, never the printed edge trim.
    for x,y in ((55,35),(285,35),(55,215),(285,215)):
        upright=gate1_guard_upright(); upright.translate(App.Vector(x,y,18)); add(f"G1J07Upright{x}_{y}",upright,steel,"guard","20 x20 x2 metal angle")
    front=gate1_guard_front_rear_panel(); front.rotate(App.Vector(),App.Vector(1,0,0),90); front.translate(App.Vector(65,48,18)); add("GuardFront",front,clear,"guard","G1J-03 3 mm polycarbonate")
    rear=gate1_guard_front_rear_panel(); rear.rotate(App.Vector(),App.Vector(1,0,0),90); rear.translate(App.Vector(65,225,18)); add("GuardRear",rear,clear,"guard","G1J-03 3 mm polycarbonate")
    left=gate1_guard_left_panel(); left.rotate(App.Vector(),App.Vector(0,1,0),-90); left.translate(App.Vector(68,45,18)); add("GuardLeft",left,clear,"guard","G1J-04 3 mm polycarbonate")
    right_panel=gate1_guard_right_panel(); right_panel.rotate(App.Vector(),App.Vector(0,1,0),-90); right_panel.translate(App.Vector(295,45,18)); add("GuardRight",right_panel,clear,"guard","G1J-05 3 mm polycarbonate with arm slot")
    baffle=gate1_torque_slot_baffle(); baffle.rotate(App.Vector(),App.Vector(1,0,0),90); baffle.translate(App.Vector(286,32,60)); add("TorqueSlotBaffle",baffle,clear,"guard","G1J-06 3 mm polycarbonate offset baffle")
    switch_bracket=gate1_interlock_bracket(); switch_bracket.translate(App.Vector(225,43,165)); add("G1J09InterlockBracket",switch_bracket,steel,"guard","2 mm metal + positive-opening switch")
    switch=Part.makeBox(36,16,28,App.Vector(232,42,168)); add("GuardInterlockSwitch",switch,purple,"guard","positive-opening NC switch envelope")
    for x,y in ((85,66),(185,66),(85,194),(185,194)):
        foot=gate1_plate_foot(); foot.translate(App.Vector(x,y,8)); add(f"G1J10PlateFoot{x}_{y}",foot,steel,"base","40 x40 x4 standard angle")
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
    # Adjacent lofts overlap at their section faces.  Fuse them into one B-Rep
    # so the quotation ridge can be joined to the core as one manufactured
    # screw rather than exported as hundreds of disconnected solids.
    flight=segments[0]
    for segment in segments[1:]:
        flight=flight.fuse(segment)
    return flight.removeSplitter()


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
    body=drive.fuse(thrust).fuse(neck).fuse(core).removeSplitter()
    joined=body.fuse(flight).removeSplitter()
    return joined.Solids[0] if len(joined.Solids)==1 else joined


def extruder_screw_process_coupon():
    """Three-pitch SCM440 supplier coupon; not an operating screw."""
    core=Part.makeCylinder(10.88/2,48)
    flight=helical_flight_reference(48)
    joined=core.fuse(flight).removeSplitter()
    return joined.Solids[0] if len(joined.Solids)==1 else joined


def extruder_barrel_process_coupon():
    """Matched 60 mm bore/hone/nitride coupon."""
    return Part.makeCylinder(17,60).cut(Part.makeCylinder(8.10,60))


def extruder_barrel():
    """SCM440 barrel quotation geometry, 34 OD x 16.20 ID x 280."""
    outer=Part.makeCylinder(17,280)
    bore=Part.makeCylinder(8.10,280)
    barrel=outer.cut(bore)
    # Feed opening: 18 mm axial x 20 mm chord, B+12..30 from rear datum.
    # The cylinder axis is local Z, so the box's Z length is the axial size.
    feed=Part.makeBox(20,34,18,App.Vector(-10,-17,12))
    barrel=barrel.cut(feed)
    # Four M4 die-interface holes on PCD26, axial 8 mm deep.  The previous
    # M5/PCD28 pattern left only 0.5 mm nominal metal to the Ø34 outside
    # surface and was not a defensible RFQ interface.
    for angle in (45,135,225,315):
        a=math.radians(angle)
        hole=Part.makeCylinder(1.65,11,App.Vector(13*math.cos(a),13*math.sin(a),269))
        barrel=barrel.cut(hole)
    return barrel


def extruder_rfq_parts():
    return [
        dict(id="EX-SCR-01",name="16 mm x 16D single screw",shape=extruder_screw(),qty=1,material="SCM440 (KS D3867/JIS G4105 equivalent) QT + gas nitride",process="turn between centres, 4-axis flight mill, polish, nitride, finish grind",critical="total 316.00; active 256.00; OD 15.92 -0.02/0; RH pitch 16.00; land 1.60; Datum A axis from Ø12 h6 and Ø15 h6 journals; full part HOLD"),
        dict(id="EX-BAR-01",name="ID16.20 x OD34 barrel",shape=extruder_barrel(),qty=1,material="SCM440 (KS D3867/JIS G4105 equivalent) QT + gas nitride bore",process="deep drill, stress relieve, ream/hone, port, die-interface thread, nitride, final hone",critical="L280.00; ID16.20 +0.02/0 after hone; OD34.00; 4x M4-6H depth8 PCD26; outer/inner thread ligament >=2.0/2.9; Datum B rear face/C front face; bore axis Datum D; full part HOLD"),
        dict(id="EX-CPN-SCR",name="Three-pitch screw process coupon",shape=extruder_screw_process_coupon(),qty=1,material="same certified SCM440 heat as EX-SCR-01",process="same flight mill/polish/nitride route as EX-SCR-01",critical="L48.00; three pitches; OD/root/land/finish/case same as feed zone; coupon RFQ only"),
        dict(id="EX-CPN-BAR",name="Matched barrel process coupon",shape=extruder_barrel_process_coupon(),qty=1,material="same certified SCM440 heat as EX-BAR-01",process="same bore/hone/nitride route as EX-BAR-01",critical="L60.00; ID/OD/finish/case same as barrel; coupon RFQ only"),
    ]
