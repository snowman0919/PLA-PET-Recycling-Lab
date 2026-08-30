#!/usr/bin/env python3
"""Software-render actual FreeCAD tessellations without an OpenGL dependency."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import FreeCAD as App
import Part
from PIL import Image, ImageDraw, ImageFont

try:
    import FreeCADGui as Gui
except ImportError:
    Gui = None

ROOT = Path(__file__).resolve().parents[2]
GEOM = ROOT / "cad/freecad/compact"
sys.path.insert(0, str(GEOM))
from geometry import (  # noqa: E402
    assembly_objects,
    cycloidal_hook_profile_points,
    down_die_body,
    down_die_breaker_plate,
    down_die_copper_gasket,
    down_die_insert,
    down_die_relief_retainer,
    hook_disc,
    print_parts,
    review_keepout_objects,
)
from manufacturing import (  # noqa: E402
    bolt_on_sprocket_hub,
    extruder_barrel,
    extruder_screw,
    gate1_assembly,
    generic_phase_gear_lamination,
    universal_motor_plate,
)

W, H = 1600, 1200


def gui_render(items, output, title, view="iso", support=False, arrow=False, arrow_target=(1060,430)):
    """Render exact B-Rep edges through Coin3D; no tessellation edges are shown."""
    doc=App.newDocument("PPR_Render")
    for index,item in enumerate(items):
        obj=doc.addObject("PartDesign::Feature",f"R{index:03d}_{item['name']}")
        obj.Shape=item["shape"]
        obj.ViewObject.ShapeColor=tuple(channel/255 for channel in item["color"])
        obj.ViewObject.LineColor=tuple(max(0,channel-55)/255 for channel in item["color"])
        obj.ViewObject.LineWidth=0.7
        obj.ViewObject.DisplayMode="Flat Lines"
        if support:
            obj.ViewObject.ShapeColor=(0.80,0.22,0.18)
    doc.recompute()
    active=Gui.activeDocument().activeView()
    {"front":active.viewFront,"top":active.viewTop,"right":active.viewRight}.get(view,active.viewAxonometric)()
    active.fitAll()
    output.parent.mkdir(parents=True,exist_ok=True)
    active.saveImage(str(output),W,H,"White")
    App.closeDocument(doc.Name)
    image=Image.open(output).convert("RGB"); draw=ImageDraw.Draw(image); font=ImageFont.load_default(size=25)
    draw.rectangle((24,20,W-24,67),fill=(255,255,255),outline=(75,95,105),width=2)
    draw.text((42,31),title,fill=(25,45,55),font=font)
    if arrow:
        tx,ty=arrow_target; draw.line((1320,250,tx,ty),fill=(196,43,43),width=12)
        draw.polygon([(tx,ty),(tx+45,ty-18),(tx+35,ty+28)],fill=(196,43,43))
        draw.text((1130,205),"M6 through-bolt access",fill=(160,30,30),font=font)
    image.save(output)


def mesh_render(items,output,title,view="iso",support=False,arrow=False,arrow_target=(1060,430)):
    """Triangle z-sort for isolated high-detail parts; mesh edges stay hidden."""
    triangles=[]
    for item in items:
        points,faces=item["shape"].tessellate(5.0)
        for indices in faces:
            vertices=[App.Vector(*points[index]) for index in indices]
            projected=[project(point,view) for point in vertices]
            color=item["color"]
            if support and normal_z(*vertices) < -0.45:
                color=(205,55,45)
            triangles.append((sum(point[2] for point in projected)/3,[(point[0],point[1]) for point in projected],color))
    xs=[p[0] for _,triangle,_ in triangles for p in triangle]; ys=[p[1] for _,triangle,_ in triangles for p in triangle]
    margin=110; scale=min((W-2*margin)/(max(xs)-min(xs) or 1),(H-2*margin)/(max(ys)-min(ys) or 1))
    def screen(point): return (margin+(point[0]-min(xs))*scale,H-margin-(point[1]-min(ys))*scale)
    image=Image.new("RGB",(W,H),(246,248,249)); draw=ImageDraw.Draw(image)
    for _,triangle,color in sorted(triangles,key=lambda item:item[0],reverse=True):
        draw.polygon([screen(point) for point in triangle],fill=color)
    font=ImageFont.load_default(size=25)
    draw.rectangle((24,20,W-24,67),fill=(255,255,255),outline=(75,95,105),width=2)
    draw.text((42,31),title,fill=(25,45,55),font=font)
    if arrow:
        tx,ty=arrow_target
        draw.line((1320,250,tx,ty),fill=(196,43,43),width=12)
        draw.polygon([(tx,ty),(tx+45,ty-18),(tx+35,ty+28)],fill=(196,43,43))
        draw.text((1130,205),"M6 through-bolt access",fill=(160,30,30),font=font)
    output.parent.mkdir(parents=True,exist_ok=True); image.save(output)


def project(p, view):
    x, y, z = p.x, p.y, p.z
    if view == "front": return x, z, y
    if view == "top": return x, y, z
    if view == "right": return y, z, x
    return x - 0.58 * y, z + 0.26 * x + 0.18 * y, x + y - 0.4 * z


def normal_z(a, b, c):
    ux, uy, uz = b.x-a.x, b.y-a.y, b.z-a.z
    vx, vy, vz = c.x-a.x, c.y-a.y, c.z-a.z
    nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
    n = math.sqrt(nx*nx+ny*ny+nz*nz) or 1
    return nz/n


def render(items, output, title, view="iso", clip=None, support=False, arrow=False, arrow_target=(1060,430)):
    if Gui is not None and App.GuiUp:
        gui_render(items,output,title,view,support,arrow,arrow_target)
        return
    # OCC wire discretization dereferences a null curve on one valid
    # intersecting-bore seam in EX-DIE-01.  Use only its exact bounding solid
    # in cabinet views; a separate exact tessellated die exploded view below
    # preserves every hole/channel/retainer feature for visual inspection.
    safe_items=[]
    for item in items:
        if item["name"] == "DownDieBody":
            bb=item["shape"].BoundBox
            item={**item,"shape":Part.makeBox(bb.XLength,bb.YLength,bb.ZLength,App.Vector(bb.XMin,bb.YMin,bb.ZMin))}
        safe_items.append(item)
    items=safe_items
    faces_2d = []
    for item in items:
        for face in item["shape"].Faces:
            center=face.CenterOfMass
            if clip and not clip((center.x,center.y,center.z)): continue
            outer=face.OuterWire.discretize(Deflection=3.0)
            if len(outer)<3: continue
            pp=[project(point,view) for point in outer]
            holes=[]
            for wire in face.Wires:
                if wire.isSame(face.OuterWire): continue
                points=wire.discretize(Deflection=3.0)
                if len(points)>=3: holes.append([(q[0],q[1]) for q in map(lambda p:project(p,view),points)])
            color = item["color"]
            if support:
                try:
                    u0,u1,v0,v1=face.ParameterRange
                    normal=face.normalAt((u0+u1)/2,(v0+v1)/2)
                    if normal.z < -0.45: color=(205,55,45)
                except Exception:
                    pass
            faces_2d.append((project(center,view)[2],[(q[0],q[1]) for q in pp],holes,color))
    if not faces_2d: raise RuntimeError(f"no B-Rep faces for {output}")
    xs = [p[0] for _,outer,holes,_ in faces_2d for p in outer]; ys = [p[1] for _,outer,holes,_ in faces_2d for p in outer]
    margin = 110; scale = min((W-2*margin)/(max(xs)-min(xs) or 1), (H-2*margin)/(max(ys)-min(ys) or 1))
    def screen(pt): return (margin + (pt[0]-min(xs))*scale, H-margin-(pt[1]-min(ys))*scale)
    image = Image.new("RGB", (W, H), (246, 248, 249)); draw = ImageDraw.Draw(image)
    for _,outer,holes,color in sorted(faces_2d,key=lambda item:item[0],reverse=True):
        draw.polygon([screen(p) for p in outer],fill=color,outline=tuple(max(0,c-42) for c in color))
        for hole in holes:
            draw.polygon([screen(p) for p in hole],fill=(246,248,249))
    font = ImageFont.load_default(size=25)
    draw.rectangle((24, 20, W-24, 67), fill=(255,255,255), outline=(75,95,105), width=2)
    draw.text((42, 31), title, fill=(25,45,55), font=font)
    if arrow:
        tx,ty=arrow_target
        draw.line((1320, 250, tx, ty), fill=(196,43,43), width=12)
        draw.polygon([(tx,ty),(tx+45,ty-18),(tx+35,ty+28)], fill=(196,43,43))
        draw.text((1130, 205), "M6 through-bolt access", fill=(160,30,30), font=font)
    output.parent.mkdir(parents=True, exist_ok=True); image.save(output)


def part_items():
    result=[]
    for i, spec in enumerate(print_parts()):
        shape=spec["shape"].copy(); col=i%4; row=i//4
        shape.translate(App.Vector(col*220, row*220, 0))
        result.append({"name":spec["id"],"shape":shape,"color":(63,137,178),"group":"print"})
    return result


def render_section(assembly=None):
    assembly = assembly or assembly_objects()
    slab = Part.makeBox(470, 10, 930, App.Vector(0, 342, 0))
    section=[]
    for item in assembly:
        bb=item["shape"].BoundBox
        if item["group"] == "frame" or bb.YMax <= 342 or bb.YMin >= 352: continue
        shape=item["shape"].common(slab)
        if not shape.isNull(): section.append({**item,"shape":shape})
    render(section, ROOT/"renders/review/compact_section.png", "True center slab section y=342..352 mm", "front")


def render_tool_access(assembly=None):
    assembly = assembly or assembly_objects()
    render([i for i in assembly if i["group"]=="shredder"], ROOT/"renders/review/shredder_fastener_tool_access.png", "Shredder bearing plates / interleaved discs / M6 through-bolts", "right", arrow=True, arrow_target=(1210,680))


def render_release_review_views(assembly):
    """Views required for the parent visual release audit."""
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_side.png", "Right side | hot zone, forming path, and enclosed services", "right")
    render(assembly, ROOT/"renders/review/closed_operating_state.png", "Closed operating state | guards, shield, panel, and ducts installed", "iso")
    heater_review = [i for i in assembly if i["group"] == "extruder" and i["name"] != "HotShield"]
    render(heater_review, ROOT/"renders/review/heater_and_hot_zone.png", "Heater inspection | shield removed; 3 bands, die cartridge, 4 probes, fuses, duct", "iso")
    render([i for i in assembly if i["group"] == "forming"], ROOT/"renders/review/cooling_and_forming.png", "Cooling/forming | straight soft-strand path through X/Y gauge and puller", "iso")
    render([i for i in assembly if i["group"] == "spooler"], ROOT/"renders/review/spool_and_dancer.png", "Spool/dancer | solid guide, dancer, traverse, spindle, full spool", "iso")
    cable_names = ("HeaterLead", "HeaterCableDuct", "CableDuct", "PPR-C12_CableClip", "ControlPanel", "PSU")
    render([i for i in assembly if i["name"].startswith(cable_names)], ROOT/"renders/review/cable_routing.png", "Cable routing | fixed hot-zone duct to segregated vertical service duct", "iso")
    service_items = [i for i in assembly_objects(exploded=True) if i["group"] in ("extruder", "control", "frame")]
    for item in review_keepout_objects():
        if item["name"] == "KO_ScrewService":
            service_items.append({**item, "color": (220, 80, 70), "group": "review"})
    render(service_items, ROOT/"renders/review/service_access.png", "Service access | exploded hot zone/control with screw-withdrawal keep-out", "iso")


def gate1_render_items(exploded=False, mode="manual"):
    """Review LOD: preserve the exact screen envelope without tessellating holes."""
    items=gate1_assembly(exploded=exploded, mode=mode)
    for item in items:
        if item["name"]=="CUT04ScreenCoupon":
            bb=item["shape"].BoundBox
            item["shape"]=Part.makeBox(bb.XLength,bb.YLength,bb.ZLength,App.Vector(bb.XMin,bb.YMin,bb.ZMin))
            item["material"]="CUT-04 envelope; fabrication DXF contains 5 mm holes"
    return items


def render_drive_interface():
    # Use the exact powered Gate-1 assembly solids instead of an unrelated
    # cylinder-and-bar schematic.  The red GMP60 solid remains a dimensional
    # reference only; a received donor changes DRV-Axx, not DRV-01/F01/02.
    names=("GMP60Reference","DRV01UniversalPlate","DRV-A60","DRV-F01A","DRV-F01B","DRV-F01P",
           "DRV02CutterHub","MotorSprocket12T","CutterSprocket30T","ChainTight","ChainSlack",
           "CUT05Shaft","PhaseLam")
    items=[item for item in gate1_assembly(mode="powered") if item["name"].startswith(names)]
    render(items,ROOT/"renders/modules/interchangeable_drive_interface.png","Interchangeable drive | exact DRV-01/Axx/F01/#35/DRV-02/keyed DRV-03 solids","iso")


def render_cycloidal_hook_construction():
    """Annotated controlling profile, so the cycloidal-derived flank is visible."""
    points=cycloidal_hook_profile_points()
    image=Image.new("RGB",(W,H),(248,250,251)); draw=ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",30)
        small=ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",24)
    except OSError:
        font=ImageFont.load_default(size=30); small=ImageFont.load_default(size=24)
    cx,cy,scale=525,615,14.0
    xy=lambda p:(cx+p.x*scale,cy-p.z*scale)
    for radius,color,label in ((18,(130,145,155),"root Ø36"),(29,(75,95,105),"nominal OD Ø58")):
        box=(cx-radius*scale,cy-radius*scale,cx+radius*scale,cy+radius*scale)
        draw.ellipse(box,outline=color,width=3)
        draw.text((cx+radius*scale+12,cy-18),label,fill=color,font=small)
    profile=[xy(p) for p in points]
    draw.polygon(profile,fill=(244,218,197)); draw.line(profile,fill=(35,52,62),width=5,joint="curve")
    capture=[xy(p) for p in points[:19]]
    nose=[xy(p) for p in points[18:22]]
    relief=[xy(p) for p in points[21:30]]
    draw.line(capture,fill=(225,116,55),width=11,joint="curve")
    draw.line(nose,fill=(196,43,43),width=11,joint="curve")
    draw.line(relief,fill=(119,89,145),width=11,joint="curve")
    draw.rectangle((24,20,W-24,72),fill="white",outline=(75,95,105),width=2)
    draw.text((42,31),"CUT-01 controlling asymmetric cycloidal-derived 7-hook profile",fill=(25,45,55),font=font)
    x0=1010
    draw.text((x0,210),"Actual DXF/STEP profile construction",fill=(25,45,55),font=font)
    draw.line((x0,290,x0+95,290),fill=(225,116,55),width=11); draw.text((x0+115,272),"76% pitch capture flank",fill=(55,65,70),font=small)
    draw.text((x0,335),"r(u)=r_root+(r_tip-r_root)·s(u)",fill=(55,65,70),font=small)
    draw.text((x0,380),"s(u)=u-sin(2πu)/(2π)",fill=(55,65,70),font=small)
    draw.line((x0,460,x0+95,460),fill=(196,43,43),width=11); draw.text((x0+115,442),"rounded overhung nose",fill=(55,65,70),font=small)
    draw.line((x0,540,x0+95,540),fill=(119,89,145),width=11); draw.text((x0+115,522),"fast cubic relief",fill=(55,65,70),font=small)
    draw.text((x0,620),"7 identical sectors · 6 mm plate",fill=(55,65,70),font=small)
    draw.text((x0,665),"Ø20.2 bore + internal 6.2 mm keyway",fill=(55,65,70),font=small)
    draw.text((x0,735),"Gate-1 releases only 2 coupons.",fill=(155,35,35),font=small)
    draw.text((x0,780),"Physical PLA/PET torque, jam,",fill=(155,35,35),font=small)
    draw.text((x0,825),"and chip-size data remain NOT_RUN.",fill=(155,35,35),font=small)
    output=ROOT/"renders/modules/CUT-01_cycloidal_hook_profile.png"; output.parent.mkdir(parents=True,exist_ok=True); image.save(output)


def render_manufacturing():
    render(gate1_render_items(),ROOT/"renders/jigs/gate1_assembly.png","Gate-1 | metal uprights / screen rails / full guard","iso")
    render(gate1_render_items(exploded=True),ROOT/"renders/jigs/gate1_exploded.png","Gate-1 exploded | metal load path and removable guard","iso")
    render(gate1_render_items(mode="powered"),ROOT/"renders/jigs/gate1_powered_assembly.png","Gate-1 powered | exact interchangeable drive inside closed guard","iso")
    render(gate1_render_items(exploded=True, mode="powered"),ROOT/"renders/jigs/gate1_powered_exploded.png","Gate-1 powered exploded | DRV-01/Axx/F01/#35/DRV-02","iso")
    render([i for i in gate1_render_items(mode="powered") if i["group"] != "guard"],ROOT/"renders/jigs/gate1_powered_guard_removed.png","Gate-1 powered guard removed | assembly review only / energization prohibited","iso")
    rotor=[i for i in gate1_assembly() if i["name"].startswith(("CUT01","CUT04","CUT05"))]
    mesh_render(rotor,ROOT/"renders/jigs/gate1_rotor_detail.png","Gate-1 | two cycloidal-derived hook coupons / 5 mm screen","front")
    render_extruder_rfq()
    render_drive_interface()


def render_extruder_rfq():
    """Regenerate only the screw/barrel inspection view."""
    # Keep this on a valid solid: a 4 mm helical loft step can self-intersect
    # and collapse to null.  The 2 mm visualization solid is separately checked;
    # controlling RFQ STEP remains the 1 mm source exported by manufacturing.py.
    screw=extruder_screw(facet_step=2.0); barrel=extruder_barrel()
    screw.rotate(App.Vector(),App.Vector(0,1,0),90)
    barrel.rotate(App.Vector(),App.Vector(0,1,0),90)
    barrel.translate(App.Vector(0,0,55))
    mesh_render([
        {"name":"EX-SCR-01","shape":screw,"color":(225,116,55),"group":"rfq"},
        {"name":"EX-BAR-01","shape":barrel,"color":(88,101,112),"group":"rfq"},
    ],ROOT/"renders/cnc/extruder_screw_barrel.png","16 mm x 16D RFQ | screw SCM440 / barrel SCM440 / process coupons first","iso")
    die_items=[]
    for index,(name,shape,color) in enumerate((
        ("EX-DIE-01",down_die_body(),(88,101,112)),
        ("EX-DIE-02",down_die_breaker_plate(),(69,151,97)),
        ("EX-DIE-03",down_die_insert(),(225,116,55)),
        ("EX-DIE-04",down_die_relief_retainer(),(119,89,145)),
        ("EX-DIE-05",down_die_copper_gasket(),(190,125,65)),
    )):
        shape=shape.copy(); bb=shape.BoundBox
        shape.translate(App.Vector(index*58-bb.XMin,-bb.YMin,-bb.ZMin))
        die_items.append({"name":name,"shape":shape,"color":color,"group":"rfq"})
    mesh_render(die_items,ROOT/"renders/cnc/extruder_die_exploded.png","EX-DIE-01..05 | exact tessellation | connected dia8 turn / breaker / insert / relief / gasket","iso")


def main():
    assembly = assembly_objects()
    cutter = hook_disc()
    if "--manufacturing-only" in sys.argv:
        render_manufacturing()
        print("COMPACT_MANUFACTURING_RENDER_OK images=6")
        return
    if "--jig-only" in sys.argv:
        render(gate1_render_items(),ROOT/"renders/jigs/gate1_assembly.png","Gate-1 | metal uprights / screen rails / full guard","iso")
        render(gate1_render_items(exploded=True),ROOT/"renders/jigs/gate1_exploded.png","Gate-1 exploded | metal load path and removable guard","iso")
        render(gate1_render_items(mode="powered"),ROOT/"renders/jigs/gate1_powered_assembly.png","Gate-1 powered | exact interchangeable drive inside closed guard","iso")
        render(gate1_render_items(exploded=True, mode="powered"),ROOT/"renders/jigs/gate1_powered_exploded.png","Gate-1 powered exploded | DRV-01/Axx/F01/#35/DRV-02","iso")
        render([i for i in gate1_render_items(mode="powered") if i["group"] != "guard"],ROOT/"renders/jigs/gate1_powered_guard_removed.png","Gate-1 powered guard removed | assembly review only / energization prohibited","iso")
        rotor=[i for i in gate1_assembly() if i["name"].startswith(("CUT01","CUT04","CUT05"))]
        render(rotor,ROOT/"renders/jigs/gate1_rotor_detail.png","Gate-1 | two cycloidal-derived hook coupons / 5 mm screen","front")
        print("COMPACT_GATE1_RENDER_OK images=6")
        return
    if "--jig-rotor-only" in sys.argv:
        rotor=[i for i in gate1_assembly() if i["name"].startswith(("CUT01","CUT04","CUT05"))]
        render(rotor,ROOT/"renders/jigs/gate1_rotor_detail.png","Gate-1 | two cycloidal-derived hook coupons / 5 mm screen","front")
        print("COMPACT_GATE1_ROTOR_RENDER_OK")
        return
    if "--shredder-only" in sys.argv:
        render_cycloidal_hook_construction()
        visible_names = ("DriveMotorDonorEnvelope", "DriveMotorOutputInterface", "CutterSprocket", "MotorSprocket", "ChainTightSide", "ChainSlackSide", "PhaseGear", "Shaft", "MotorMountPlate")
        drive = [i for i in assembly if i["name"].startswith(visible_names) or i["name"] in ("Hook105_0", "Hook153_0")]
        mesh_render(drive, ROOT/"renders/modules/shredder_drive_guard_removed.png", "Guard removed | interchangeable #35 chain / M3 Z16 phase gears", "iso")
        print("COMPACT_SHREDDER_RENDER_OK images=2")
        return
    if "--drive-interface-only" in sys.argv:
        render_drive_interface()
        print("COMPACT_DRIVE_INTERFACE_RENDER_OK")
        return
    if "--extruder-only" in sys.argv:
        render_extruder_rfq()
        print("COMPACT_EXTRUDER_RFQ_RENDER_OK")
        return
    if "--tool-only" in sys.argv:
        render_tool_access(assembly)
        print("COMPACT_TOOL_ACCESS_RENDER_OK images=1")
        return
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_isometric.png", "safety-orchestration-closure-v0.6.1 | 470 x 700 x 930 mm", "iso")
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_front.png", "Front | vertical forming path and full spool", "front")
    render(assembly, ROOT/"renders/assembly/compact_full_assembly_top.png", "Top | all normal-operation components inside frame", "top")
    render_release_review_views(assembly)
    shredder=[i for i in assembly if i["group"] in ("input","shredder","feed")]
    render(shredder, ROOT/"renders/modules/shared_shredder_module.png", "Shared hopper / hook cutter / removable screen / bin", "iso")
    render_cycloidal_hook_construction()
    visible_names = ("DriveMotorDonorEnvelope", "DriveMotorOutputInterface", "CutterSprocket", "MotorSprocket", "ChainTightSide", "ChainSlackSide", "PhaseGear", "Shaft", "MotorMountPlate")
    drive = [i for i in assembly if i["name"].startswith(visible_names) or i["name"] in ("Hook105_0", "Hook153_0")]
    mesh_render(drive, ROOT/"renders/modules/shredder_drive_guard_removed.png", "Interchangeable #35 chain / M3 Z16 functional phase gears", "iso")
    anti=print_parts()[1]
    render([{"name":anti["id"],"shape":anti["shape"],"color":(63,137,178),"group":"part"}], ROOT/"renders/modules/PPR-C02_individual.png", "PPR-C02 anti-reach baffle | individual part", "iso")
    render(assembly_objects(exploded=True), ROOT/"renders/review/compact_exploded.png", "Exploded by service module", "iso")
    render_section(assembly)
    render_tool_access(assembly)
    prints=part_items()
    render(prints, ROOT/"renders/review/print_orientation.png", "Print orientation overview | every axis <= 210 mm", "top")
    render(prints, ROOT/"renders/review/support_contact.png", "Support-contact review | downward facets in red", "iso", support=True)
    render([i for i in assembly if i["group"] in ("forming","spooler")], ROOT/"renders/review/forming_spool_motion.png", "Gauge/puller then solid guide, dancer, traverse and full spool", "iso")
    render_manufacturing()
    print("COMPACT_RENDER_GENERATION_OK images=29")


if __name__ == "__main__":
    main()
