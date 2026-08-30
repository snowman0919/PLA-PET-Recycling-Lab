"""Manufacturing geometry for compact v0.5 drive, Gate-1 jig and extruder RFQ.

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
    chain_sprocket_shape,
    cutter_shaft,
    down_die_body,
    down_die_breaker_plate,
    down_die_copper_gasket,
    down_die_insert,
    down_die_relief_retainer,
    gmp60_60127_reference_shape,
    hook_disc,
    motor_adapter_42gp775_shape,
    motor_adapter_gmp60_shape,
    motor_mount_plate,
    joined,
    one_solid,
    screen_plate,
    spur_phase_gear,
)


def universal_motor_plate():
    """Use the same DRV-01 solid as the full assembly and CNC export."""
    return motor_mount_plate()


def motor_side_fuse_inner_hub():
    """DRV-F01A keyed motor hub; a replaceable waisted pin is the fuse."""
    hub = Part.makeCylinder(10.0, 16.0).cut(Part.makeCylinder(6.1, 16.0))
    hub = hub.cut(Part.makeBox(5.0, 6.5, 16.0, App.Vector(-2.5, 0, 6.0)))
    hub = hub.cut(Part.makeCylinder(1.6, 20.0, App.Vector(-10, 0, 8), App.Vector(1, 0, 0)))
    return hub


def motor_side_fuse_outer_hub():
    """DRV-F01B sprocket carrier, free after DRV-F01P pin shears."""
    hub = Part.makeCylinder(18.0, 10.0).cut(Part.makeCylinder(10.2, 10.0))
    hub = hub.cut(Part.makeCylinder(1.6, 36.0, App.Vector(-18, 0, 5), App.Vector(1, 0, 0)))
    for angle in (45, 135, 225, 315):
        a = math.radians(angle)
        hub = hub.cut(Part.makeCylinder(2.25, 10, App.Vector(14 * math.cos(a), 14 * math.sin(a), 0)))
    return hub


def motor_side_fuse_pin():
    """DRV-F01P brass pin blank; Gate-1 sets the waisted diameter."""
    left = Part.makeCylinder(1.5, 16.0, App.Vector(-18, 0, 0), App.Vector(1, 0, 0))
    waist = Part.makeCylinder(0.9, 4.0, App.Vector(-2, 0, 0), App.Vector(1, 0, 0))
    right = Part.makeCylinder(1.5, 16.0, App.Vector(2, 0, 0), App.Vector(1, 0, 0))
    return one_solid(joined(left, waist, right))


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
    # The phase stack must transmit shaft torque; clamp bolts only register the
    # laminations and are not a substitute for this standard 6 mm keyway.
    gear = gear.cut(Part.makeBox(6.2, 6, 6.0, App.Vector(-3.1, 0, 7.0)))
    return gear


def gate1_base_plate():
    plate = Part.makeBox(380, 280, 8)
    for x in (20, 360):
        for y in (20, 260):
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
    outer = Part.makeBox(120, 90, 115)
    # Open at both ends: the former 1.2 mm printed floor could retain a coupon
    # above the rotor and was not a buildable feed path.
    inner = Part.makeBox(117.6, 87.6, 117, App.Vector(1.2, 1.2, -1))
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
    corner = Part.makeBox(10, 10, 210)
    corner = corner.cut(Part.makeBox(6, 2, 206, App.Vector(2, 6, 4)))
    corner = corner.cut(Part.makeBox(2, 6, 206, App.Vector(6, 2, 4)))
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
    return _flat_panel(340,220,mid_holes=True)


def gate1_guard_left_panel():
    return _flat_panel(220,260,mid_holes=True)


def gate1_guard_right_panel():
    panel=_flat_panel(220,260,mid_holes=True)
    # After the panel rotates into the machine YZ plane, local X maps to Z and
    # local Y maps to machine Y.  The slot therefore opens from local Y=0 and
    # spans local X=60..100 and local Y=30..55 around the manual arm.
    return panel.cut(Part.makeBox(40,25,3,App.Vector(60,30,0)))


def gate1_guard_top_panel():
    """Horizontal fragment-retention roof with a close-fit chute opening."""
    panel=_flat_panel(340,260,mid_holes=True)
    return panel.cut(Part.makeBox(122,92,3,App.Vector(69,84,0)))


def gate1_torque_slot_baffle():
    return _flat_panel(45,70)


def gate1_guard_upright():
    """20 x20 x2 standard metal angle, L220, with panel attachment holes."""
    angle=Part.makeBox(20,2,220).fuse(Part.makeBox(2,20,220))
    for z in (10,110,210):
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
        dict(id="G1J-01", name="Reusable jig base plate", shape=gate1_base_plate(), qty=1, material="8 mm donor steel/aluminum plate", process="laser/drill or donor plate drill template", class_="metal",critical="380 x280 x8; table holes Ø9; flatness <=0.30; deburr C0.5"),
        dict(id="G1J-02", name="250 mm torque arm", shape=gate1_torque_arm(), qty=1, material="6 mm S45C/structural steel", process="laser cut + deburr", class_="metal",critical="shaft bore Ø20.2 +0.10/0; 6.2 keyway; shaft centre to force hole 250.0 ±0.5; flatness 0.20"),
        dict(id="G1J-03", name="Front/rear guard panel", shape=gate1_guard_front_rear_panel(), qty=2, material="3 mm polycarbonate", process="CNC router/drill; laser only with supplier approval", class_="sheet",critical="340 x220 x3; 6x Ø4.5 at X10/330 and Y10/110/210; no acrylic; edges R0.5"),
        dict(id="G1J-04", name="Left guard panel", shape=gate1_guard_left_panel(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="220 x260 x3; 6x Ø4.5 at X10/210 and Y10/130/250; no acrylic; edges R0.5"),
        dict(id="G1J-05", name="Right slotted guard panel", shape=gate1_guard_right_panel(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="220 x260 x3; arm slot local X60..100/Y30..55; >=2 mm arm clearance; offset baffle required; no cracks"),
        dict(id="G1J-06", name="Torque-slot offset baffle", shape=gate1_torque_slot_baffle(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="45 x70 x3; 4x Ø4.5; offset >=10 from arm slot; blocks line of sight"),
        dict(id="G1J-07", name="Metal guard upright", shape=gate1_guard_upright(), qty=4, material="20 x20 x2 aluminum/steel angle", process="saw cut + drill", class_="stock",critical="L220 ±0.5; 6x Ø4.5; verticality 0.5/220; primary fragment load path"),
        dict(id="G1J-08", name="Removable screen rail", shape=gate1_screen_rail(), qty=2, material="20 x20 x2 steel angle", process="saw cut + drill", class_="stock",critical="L150 ±0.5; 2x Ø5.5; screen plane shimmed for >=1.9 cutter clearance"),
        dict(id="G1J-09", name="Universal guard-interlock bracket", shape=gate1_interlock_bracket(), qty=1, material="2 mm steel", process="laser/drill + 90° bend", class_="metal",critical="50 x30 L bracket; 5 x14 slots; switch plunger overtravel per received switch"),
        dict(id="G1J-10", name="CUT-03 plate foot angle", shape=gate1_plate_foot(), qty=4, material="40 x40 x4 steel/aluminum angle", process="saw cut + drill", class_="stock",critical="L50 ±0.5; 4x Ø6.6; plate perpendicularity 0.20/125 after torque"),
        dict(id="G1J-11", name="DRV-01 motor-plate foot angle", shape=gate1_plate_foot(), qty=2, material="40 x40 x4 steel/aluminum angle", process="saw cut + drill", class_="stock",critical="same stock profile as G1J-10; L50 ±0.5; DRV-01 verticality 0.5/140"),
        dict(id="G1J-12", name="Top guard panel with chute opening", shape=gate1_guard_top_panel(), qty=1, material="3 mm polycarbonate", process="CNC router/drill", class_="sheet",critical="340 x260 x3; 122 x92 chute opening at X69/Y84; no acrylic; no unguarded gap >6 mm"),
        dict(id="G1J-P01", name="Anti-reach coupon feed chute", shape=gate1_feed_chute(), qty=1, material="PLA", process="FDM", class_="print",critical="3 walls minimum; no load-path duty; baffle intact"),
        dict(id="G1J-P02", name="Removable chip collection tray", shape=gate1_chip_tray(), qty=1, material="PLA", process="FDM", class_="print",critical="3 walls minimum; removable without rotor access"),
        dict(id="G1J-P03", name="Guard edge trim", shape=gate1_guard_frame(), qty=4, material="PLA", process="FDM", class_="print",critical="edge trim only; metal G1J-07 retains panel"),
    ]


def gate1_assembly(exploded=False, mode="manual"):
    """Gate-1 manual-torque or powered-jam configuration on one guarded base."""
    if mode not in {"manual", "powered"}:
        raise ValueError(f"unknown Gate-1 mode: {mode}")
    items = []

    def add(name, shape, color, group, material):
        if exploded:
            offsets = {"base": (0, 0, -30), "rotor": (0, 0, 25), "measure": (35, -20, 30), "drive": (45, -25, 45), "guard": (0, 30, 70)}
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
        shaft=cutter_shaft(); shaft.translate(App.Vector(cx,20,73)); add(f"CUT05Shaft{cx}",shaft,steel,"rotor","final CUT-05")
        for y in (58,198):
            b=Part.makeCylinder(21,12,App.Vector(cx,y,73),App.Vector(0,1,0)).cut(Part.makeCylinder(10.1,12,App.Vector(cx,y,73),App.Vector(0,1,0)))
            add(f"Bearing{cx}_{y}",b,purple,"rotor","6004-2RS")
        for y in (48,126,190,210):
            collar=Part.makeCylinder(15,8,App.Vector(cx,y,73),App.Vector(0,1,0)).cut(Part.makeCylinder(10.1,8,App.Vector(cx,y,73),App.Vector(0,1,0)))
            add(f"SplitCollar{cx}_{y}",collar,steel,"rotor","standard Ø20 split clamp collar")
    retainer=bearing_retainer_plate()
    front_retainer=retainer.copy(); front_retainer.rotate(App.Vector(),App.Vector(1,0,0),90); front_retainer.translate(App.Vector(85,58,18))
    rear_retainer=retainer.copy(); rear_retainer.rotate(App.Vector(),App.Vector(1,0,0),90); rear_retainer.translate(App.Vector(85,212,18))
    add("CUT08Front",front_retainer,steel,"rotor","CUT-08 bearing retainer")
    add("CUT08Rear",rear_retainer,steel,"rotor","CUT-08 bearing retainer")
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
    if mode == "manual":
        arm=gate1_torque_arm(); arm.rotate(App.Vector(),App.Vector(1,0,0),90); arm.translate(App.Vector(115,52,73)); add("TorqueArm250",arm,green,"measure","metal")
        load=Part.makeBox(45,25,45,App.Vector(365,34,40)); add("ForceGauge",load,purple,"measure","0-200 N force gauge/load cell")
    else:
        # Reference powered configuration.  A donor changes only DRV-Axx and
        # its received dimensions; the fuse/chain/cutter interfaces stay fixed.
        motor=gmp60_60127_reference_shape(); motor.rotate(App.Vector(),App.Vector(1,0,0),90); motor.translate(App.Vector(265,226,160))
        add("GMP60Reference",motor,(185,54,54),"drive","digital reference only; donor receipt required")
        plate=universal_motor_plate(); plate.rotate(App.Vector(),App.Vector(1,0,0),90); plate.translate(App.Vector(175,34,90))
        add("DRV01UniversalPlate",plate,steel,"drive","DRV-01 shared load plate")
        adapter=motor_adapter_gmp60_shape(); adapter.rotate(App.Vector(),App.Vector(1,0,0),90); adapter.translate(App.Vector(225,40,120))
        add("DRV-A60",adapter,steel,"drive","reference adapter; replace with measured DRV-Axx")
        inner=motor_side_fuse_inner_hub(); inner.rotate(App.Vector(),App.Vector(1,0,0),-90); inner.translate(App.Vector(265,24,160))
        outer=motor_side_fuse_outer_hub(); outer.rotate(App.Vector(),App.Vector(1,0,0),-90); outer.translate(App.Vector(265,24,160))
        pin=motor_side_fuse_pin(); pin.rotate(App.Vector(),App.Vector(1,0,0),-90); pin.translate(App.Vector(265,29,160))
        add("DRV-F01A",inner,steel,"drive","motor-side keyed inner hub")
        add("DRV-F01B",outer,purple,"drive","sprocket carrier")
        add("DRV-F01P",pin,(245,190,45),"drive","replaceable calibrated shear pin")
        cutter_hub=bolt_on_sprocket_hub(); cutter_hub.rotate(App.Vector(),App.Vector(1,0,0),-90); cutter_hub.translate(App.Vector(183,20,73))
        add("DRV02CutterHub",cutter_hub,purple,"drive","keyed cutter-side hub")
        motor_sprocket=chain_sprocket_shape(12,12.2,10); motor_sprocket.rotate(App.Vector(),App.Vector(1,0,0),-90); motor_sprocket.translate(App.Vector(265,18,160))
        cutter_sprocket=chain_sprocket_shape(30,20.2,10); cutter_sprocket.rotate(App.Vector(),App.Vector(1,0,0),-90); cutter_sprocket.translate(App.Vector(183,18,73))
        add("MotorSprocket12T",motor_sprocket,orange,"drive","ANSI #35 12T")
        add("CutterSprocket30T",cutter_sprocket,purple,"drive","ANSI #35 30T")

        def chain_bar(x1,z1,x2,z2):
            dx,dz=x2-x1,z2-z1; length=(dx*dx+dz*dz)**0.5
            bar=Part.makeBox(length,8,4,App.Vector(0,18,-2))
            bar.rotate(App.Vector(),App.Vector(0,1,0),-math.degrees(math.atan2(dz,dx)))
            bar.translate(App.Vector(x1,0,z1))
            return bar

        dx,dz=82,87; length=(dx*dx+dz*dz)**0.5; nx,nz=-dz/length*26,dx/length*26
        add("ChainTight",chain_bar(183+nx,73+nz,265+nx,160+nz),green,"drive","#35 chain conservative solid LOD")
        add("ChainSlack",chain_bar(183-nx,73-nz,265-nx,160-nz),green,"drive","#35 chain conservative solid LOD")
        for x in (175,305):
            foot=gate1_plate_foot(); foot.translate(App.Vector(x,34,8)); add(f"G1J11MotorFoot{x}",foot,steel,"base","G1J-11 standard angle")

    chute=gate1_feed_chute(); chute.translate(App.Vector(90,95,115)); add("FeedChute",chute,blue,"guard","printed")
    tray=gate1_chip_tray(); tray.translate(App.Vector(70,68,8)); add("ChipTray",tray,blue,"base","printed")
    # Primary guard retention is metal angle, never the printed edge trim.
    for x,y in ((0,0),(360,0),(0,260),(360,260)):
        upright=gate1_guard_upright(); upright.translate(App.Vector(x,y,18)); add(f"G1J07Upright{x}_{y}",upright,steel,"guard","20 x20 x2 metal angle")
    front=gate1_guard_front_rear_panel(); front.rotate(App.Vector(),App.Vector(1,0,0),90); front.translate(App.Vector(20,13,10)); add("GuardFront",front,clear,"guard","G1J-03 3 mm polycarbonate")
    rear=gate1_guard_front_rear_panel(); rear.rotate(App.Vector(),App.Vector(1,0,0),90); rear.translate(App.Vector(20,273,10)); add("GuardRear",rear,clear,"guard","G1J-03 3 mm polycarbonate")
    left=gate1_guard_left_panel(); left.rotate(App.Vector(),App.Vector(0,1,0),-90); left.translate(App.Vector(23,10,10)); add("GuardLeft",left,clear,"guard","G1J-04 3 mm polycarbonate")
    right_panel=gate1_guard_right_panel(); right_panel.rotate(App.Vector(),App.Vector(0,1,0),-90); right_panel.translate(App.Vector(363,10,10)); add("GuardRight",right_panel,clear,"guard","G1J-05 3 mm polycarbonate with arm slot")
    top_panel=gate1_guard_top_panel(); top_panel.translate(App.Vector(20,10,230)); add("GuardTop",top_panel,clear,"guard","G1J-12 3 mm polycarbonate roof")
    baffle=gate1_torque_slot_baffle(); baffle.rotate(App.Vector(),App.Vector(1,0,0),90); baffle.translate(App.Vector(354,25,65)); add("TorqueSlotBaffle",baffle,clear,"guard","G1J-06 3 mm polycarbonate offset baffle")
    switch_bracket=gate1_interlock_bracket(); switch_bracket.translate(App.Vector(285,8,195)); add("G1J09InterlockBracket",switch_bracket,steel,"guard","2 mm metal + positive-opening switch")
    switch=Part.makeBox(36,16,28,App.Vector(292,7,198)); add("GuardInterlockSwitch",switch,purple,"guard","positive-opening NC switch envelope")
    for x,y in ((85,66),(185,66),(85,194),(185,194)):
        foot=gate1_plate_foot(); foot.translate(App.Vector(x,y,8)); add(f"G1J10PlateFoot{x}_{y}",foot,steel,"base","40 x40 x4 standard angle")
    for x,y in ((20,10),(360,10),(20,270),(360,270)):
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
    # Open only the +X radial side down to the bore.  After the assembly's
    # -90° Y rotation this is the upward feed opening, not a transverse slot
    # through both barrel walls.
    feed=Part.makeBox(9.5,20,18,App.Vector(8.0,-10,12))
    barrel=barrel.cut(feed)
    # Four M4 die-interface holes on PCD26, axial 8 mm deep.  The previous
    # M5/PCD28 pattern left only 0.5 mm nominal metal to the Ø34 outside
    # surface and was not a defensible RFQ interface.
    for angle in (45,135,225,315):
        a=math.radians(angle)
        hole=Part.makeCylinder(1.65,11,App.Vector(13*math.cos(a),13*math.sin(a),269))
        barrel=barrel.cut(hole)
    # Three Ø3.20 blind K-probe bores sit in the unheated gaps immediately
    # downstream of each band.  Depth 7.0 leaves 1.9 mm nominal ligament to
    # the Ø16.20 melt bore and measures barrel metal rather than heater skin.
    for z in (95.0, 170.0, 245.0):
        sensor=Part.makeCylinder(1.60,7.0,App.Vector(0,17.0,z),App.Vector(0,-1,0))
        barrel=barrel.cut(sensor)
    return barrel


def extruder_rfq_parts():
    return [
        dict(id="EX-SCR-01",name="16 mm x 16D single screw",shape=extruder_screw(),qty=1,material="SCM440 (KS D3867/JIS G4105 equivalent) QT + gas nitride",process="turn between centres, 4-axis flight mill, polish, nitride, finish grind",critical="total 316.00; active 256.00; OD 15.92 -0.02/0; RH pitch 16.00; land 1.60; Datum A axis from Ø12 h6 and Ø15 h6 journals; full part HOLD"),
        dict(id="EX-BAR-01",name="ID16.20 x OD34 barrel",shape=extruder_barrel(),qty=1,material="SCM440 (KS D3867/JIS G4105 equivalent) QT + gas nitride bore",process="deep drill, stress relieve, ream/hone, port, die-interface thread and sensor bores, nitride, final hone",critical="L280.00; ID16.20 +0.02/0 after hone; OD34.00; 4x M4-6H depth8 PCD26; 3x Ø3.20 +0.05/0 blind7 sensor bores at B+95/170/245; minimum bore ligament 1.85; outer/inner thread ligament >=2.0/2.9; Datum B rear face/C front face; bore axis Datum D; full part HOLD"),
        dict(id="EX-CPN-SCR",name="Three-pitch screw process coupon",shape=extruder_screw_process_coupon(),qty=1,material="same certified SCM440 heat as EX-SCR-01",process="same flight mill/polish/nitride route as EX-SCR-01",critical="L48.00; three pitches; OD/root/land/finish/case same as feed zone; coupon RFQ only"),
        dict(id="EX-CPN-BAR",name="Matched barrel process coupon",shape=extruder_barrel_process_coupon(),qty=1,material="same certified SCM440 heat as EX-BAR-01",process="same bore/hone/nitride route as EX-BAR-01",critical="L60.00; ID/OD/finish/case same as barrel; coupon RFQ only"),
        dict(id="EX-DIE-01",name="Connected 90 degree down-die body",shape=down_die_body(),qty=1,material="SCM440 QT + gas nitride",process="6-face mill; gun drill/ream intersecting Ø8 channels; counterbore, drill/tap; stress relieve; gas nitride; lap sealing face",critical="40 x40 x48; barrel datum face X40; Ø8 melt turn; Ø16.20 +0.05/0 x3 breaker seat; Ø12.00 +0.03/0 x14 insert seat; 4x Ø4.5 + Ø8 head recess PCD26; heater Ø6.20 H9; sensor Ø3.20 blind12; face flatness 0.03; channel intersection fully deburred; full part HOLD"),
        dict(id="EX-DIE-02",name="Seven-hole breaker plate",shape=down_die_breaker_plate(),qty=1,material="304 stainless",process="wire EDM or laser + double-side lap",critical="Ø15.90 -0.05/0 x2.00 ±0.03; 7x Ø2.00 +0.05/0, six on PCD10; flatness 0.03; all flow edges R0.15 max; HOLD with die body"),
        dict(id="EX-DIE-03",name="Replaceable Ø3 die insert",shape=down_die_insert(),qty=1,material="17-4PH H900 stainless",process="turn, drill/ream land, 60 degree included entrance blend, H900, finish lap",critical="OD Ø11.90 -0.02/0 x14.00 ±0.03; outlet Ø3.00 +0.02/0 x10.00 land; 4 mm transition from Ø8 to Ø3; land Ra<=0.4 um; concentricity 0.02 to OD; full part HOLD"),
        dict(id="EX-DIE-04",name="Sacrificial die relief retainer",shape=down_die_relief_retainer(),qty=1,material="304 stainless sheet t1.5",process="laser/waterjet + deburr; no heat treatment",critical="32 x20 x1.5; two 10 wide x2.5 long bending webs; 2x Ø4.5 at 24 centres; centre bypass Ø4; flatness 0.15; coupon-calibrate at operating temperature, analytical estimate is not release evidence"),
        dict(id="EX-DIE-05",name="Annealed copper face gasket",shape=down_die_copper_gasket(),qty=2,material="C110 annealed copper t0.5",process="waterjet/punch; anneal after cutting; bag clean",critical="OD34; ID16.20 +0.10/0; 4x Ø4.5 PCD26 at 45 degree; t0.50 ±0.03; burr <=0.03; one spare required"),
    ]
