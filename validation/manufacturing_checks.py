#!/usr/bin/env python3
"""FreeCAD checks for VE drive, Gate-1 jig and extruder RFQ package."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from manufacturing import extruder_rfq_parts, extruder_screw, gate1_assembly, gate1_parts, motor_side_fuse_pin, solid_phase_gear, universal_motor_plate  # noqa: E402
from geometry import assembly_objects, gmp60_60127_reference_shape, machine_fabrication_parts, mica_band_heater_shape, print_parts, shredder_metal_parts, thermocouple_retainer_shape  # noqa: E402


def require(value,message):
    if not value: raise AssertionError(message)


def main():
    jig_specs=gate1_parts()
    rfq_specs=extruder_rfq_parts()
    machine_specs=machine_fabrication_parts()
    shredder_specs=shredder_metal_parts()
    require({p["id"] for p in jig_specs}=={f"G1J-{i:02d}" for i in range(1,13)}|{f"G1J-P{i:02d}" for i in range(1,4)},"Gate-1 part family set incomplete")
    for spec in jig_specs+rfq_specs+machine_specs:
        shape=spec["shape"]
        require(shape.isValid() and not shape.isNull(),f"invalid shape {spec['id']}")
    for mode in ("manual","powered"):
        jig=Part.makeCompound([item["shape"] for item in gate1_assembly(mode=mode)])
        bb=jig.BoundBox
        require(bb.XLength <= 420 and bb.YLength <= 280 and bb.ZLength <= 238,f"Gate-1 {mode} envelope {bb.XLength,bb.YLength,bb.ZLength}")
    by={item["name"]:item["shape"] for item in gate1_assembly()}
    require(by["CUT01Coupon135"].common(by["CUT01Coupon183"]).Volume < 0.01,"coupon collision")
    require(by["CUT01Coupon135"].distToShape(by["CUT01Coupon183"])[0] >= 0.49,"coupon metal-shim gap")
    require(min(by[name].distToShape(by["CUT04ScreenCoupon"])[0] for name in ("CUT01Coupon135","CUT01Coupon183")) >= 1.9,"Gate-1 screen clearance")
    require(by["TorqueArm250"].common(by["GuardRight"]).Volume < 0.01,"torque arm/guard slot collision")
    require(by["TorqueArm250"].distToShape(by["GuardRight"])[0] >= 0.49,"torque arm slot running clearance")
    require(all(name in by for name in ("G1J08ScreenRailLeft","G1J08ScreenRailRight","G1J09InterlockBracket")),"screen rail/interlock hardware missing from assembly")
    require(all(name in by for name in ("CUT08Front","CUT08Rear","GuardTop")),"bearing retainers or closed roof missing from Gate-1 assembly")
    require(sum(1 for name in by if name.startswith("G1J07Upright"))==4,"four metal guard uprights required")
    require(sum(1 for name in by if name.startswith("G1J10PlateFoot"))==4,"four metal CUT-03 feet required")
    powered={item["name"]:item["shape"] for item in gate1_assembly(mode="powered")}
    require("TorqueArm250" not in powered,"manual torque arm must not coexist with powered drive")
    for name in ("GMP60Reference","DRV01UniversalPlate","DRV-A60","DRV-F01A","DRV-F01B","DRV-F01P","DRV02CutterHub","MotorSprocket12T","CutterSprocket30T","ChainTight","ChainSlack"):
        require(name in powered,f"powered Gate-1 drive component missing: {name}")
    require(powered["GMP60Reference"].common(powered["DRV-A60"]).Volume < 0.01 and powered["GMP60Reference"].distToShape(powered["DRV-A60"])[0] < 0.01,"motor face/DRV-A60 must touch without body penetration")
    require(powered["DRV-A60"].common(powered["DRV01UniversalPlate"]).Volume < 0.01 and powered["DRV-A60"].distToShape(powered["DRV01UniversalPlate"])[0] < 0.01,"DRV-A60/DRV-01 face stack mismatch")
    require(powered["DRV01UniversalPlate"].common(powered["GuardTop"]).Volume < 0.01,"powered DRV-01 penetrates Gate-1 roof")
    chute=next(p["shape"] for p in jig_specs if p["id"]=="G1J-P01")
    through=Part.makeBox(1,1,117,App.Vector(59.5,10.0,-1))
    require(chute.common(through).Volume < 0.01,"Gate-1 feed chute must be open at both ends")
    # Released solid gear registration must be explicit metal fasteners/dowel and matched key.
    gear=solid_phase_gear()
    for angle,diameter in ((0,4.5),(120,4.5),(240,3.0)):
        import math
        a=math.radians(angle)
        probe=Part.makeCylinder(diameter/2,18,App.Vector(15*math.cos(a),0,15*math.sin(a)),App.Vector(0,1,0))
        require(gear.common(probe).Volume < 0.01,f"DRV-03 PCD30 hole missing at {angle}")
    key_probe=Part.makeBox(8.0,18,5.5,App.Vector(-4.0,0,9.7))
    require(gear.common(key_probe).Volume < 0.01,"DRV-03 matched 8 mm shaft keyway missing")
    common_plate=universal_motor_plate()
    gearbox_probe=Part.makeCylinder(32.0,6,App.Vector(90,70,0))
    require(common_plate.common(gearbox_probe).Volume < 0.01,"DRV-01 common plate lacks Ø65 gearbox pass-through")
    screw=next(p["shape"] for p in rfq_specs if p["id"]=="EX-SCR-01")
    barrel=next(p["shape"] for p in rfq_specs if p["id"]=="EX-BAR-01")
    require(abs(screw.BoundBox.ZLength-316.0)<0.02,"screw total length")
    require(max((v.Point.x**2+v.Point.y**2)**0.5 for v in screw.Vertexes if v.Point.z >= 60) <= 7.961,
            "active screw OD exceeds 15.92")
    shoulder_probe=Part.makeCylinder(11.45,8.8,App.Vector(0,0,46.1)).cut(
        Part.makeCylinder(7.51,8.8,App.Vector(0,0,46.1)))
    require(screw.common(shoulder_probe).Volume > 1900,"Ø23 thrust-bearing abutment missing")
    render_screw=extruder_screw(facet_step=2.0)
    require(not render_screw.isNull() and render_screw.isValid() and len(render_screw.Solids)==1,"RFQ render screw must remain one valid solid")
    require(abs(barrel.BoundBox.ZLength-280.0)<0.01,"barrel length")
    require(len(barrel.Solids)==1,"barrel must be one solid")
    # Controlling RFQ port is 18 mm axial x 20 mm chord from B+12 to B+30.
    # Probe the radial +X cut volume directly so STEP cannot silently turn the
    # port into a structurally invalid transverse slot through both walls.
    feed_probe=Part.makeBox(9.5,20,18,App.Vector(8,-10,12))
    require(barrel.common(feed_probe).Volume<0.01,"barrel feed port 18 axial x 20 chord missing")
    for z in (11.0,30.5):
        intact_probe=Part.makeBox(0.5,1,0.5,App.Vector(16,0,z))
        require(barrel.common(intact_probe).Volume>0.1,"barrel feed port exceeds B+12..30")
    # Ø34 body / Ø16.20 bore / M4 PCD26 leaves a machinable ligament on both
    # sides.  This gate prevents reintroducing the former M5/PCD28 0.5 mm edge.
    outer_ligament=17.0-(13.0+2.0)
    inner_ligament=(13.0-2.0)-8.10
    require(outer_ligament>=2.0 and inner_ligament>=2.9,"barrel front thread ligament")
    for angle in (45,135,225,315):
        a=math.radians(angle)
        probe=Part.makeCylinder(1.65,11,App.Vector(13*math.cos(a),13*math.sin(a),269))
        require(barrel.common(probe).Volume<0.01,f"barrel M4 tap-drill missing at {angle}")
    for z in (95.0,170.0,245.0):
        # Stay inside the released Ø3.20 +0.05/0, flat-bottom 5.40±0.05 bore.
        probe=Part.makeCylinder(1.59,5.30,App.Vector(0,16.98,z),App.Vector(0,-1,0))
        require(barrel.common(probe).Volume<0.01,f"barrel Ø3.20 blind sensor bore missing at B+{z}")
        ligament=Part.makeCylinder(1.2,2.5,App.Vector(0,10.8,z),App.Vector(0,-1,0))
        require(barrel.common(ligament).Volume>5.0,f"barrel sensor melt-bore ligament missing at B+{z}")
        for station in (z-5.0,z+5.0):
            thread=Part.makeCylinder(1.24,3.9,App.Vector(0,16.95,station),App.Vector(0,-1,0))
            require(barrel.common(thread).Volume<0.01,f"barrel M3 sensor-retainer thread missing at B+{station}")
    rfq_by={p["id"]:p["shape"] for p in rfq_specs}
    require({f"EX-DIE-{i:02d}" for i in range(1,6)} <= set(rfq_by),"connected die RFQ set incomplete")
    body=rfq_by["EX-DIE-01"]
    horizontal=Part.makeCylinder(3.9,21,App.Vector(19,0,0),App.Vector(1,0,0))
    vertical=Part.makeCylinder(3.9,28,App.Vector(20,0,-24))
    require(body.common(horizontal).Volume<0.01 and body.common(vertical).Volume<0.01,"90 degree die melt channels missing")
    heater_bore=Part.makeCylinder(3.274,40,App.Vector(20,-20,18),App.Vector(0,1,0))
    require(body.common(heater_bore).Volume<0.01,"die Ø6.55 H7 heater bore missing")
    for x in (13,27):
        flange_thread=Part.makeCylinder(1.24,5.9,App.Vector(x,14.05,18),App.Vector(0,1,0))
        require(body.common(flange_thread).Volume<0.01,f"die M3 heater-flange thread missing at x={x}")
    sensor_bore=Part.makeCylinder(1.59,11.9,App.Vector(8,-19.95,15),App.Vector(0,1,0))
    require(body.common(sensor_bore).Volume<0.01,"die Ø3.20 sensor bore missing")
    for z in (10,20):
        thread=Part.makeCylinder(1.24,3.9,App.Vector(8,-19.95,z),App.Vector(0,1,0))
        require(body.common(thread).Volume<0.01,f"die M3 sensor-retainer thread missing at z={z}")
    probe=thermocouple_retainer_shape()
    require(probe.isValid() and probe.BoundBox.XLength==12 and probe.BoundBox.ZLength==16,"TH-TCR-01 retainer invalid")
    require(horizontal.common(vertical).Volume>1.0,"90 degree die channels do not intersect")
    require(rfq_by["EX-DIE-02"].Solids and rfq_by["EX-DIE-03"].Solids and rfq_by["EX-DIE-04"].Solids,"die removable parts invalid")
    retainer=rfq_by["EX-DIE-04"]
    for x in (13.0,26.5):
        web_probe=Part.makeBox(1,10,1.5,App.Vector(x,-5,-25.5))
        require(retainer.common(web_probe).Volume>14.0,"sacrificial retainer 10 mm web missing")
    for rel in (
        "exports/jigs/gate1/gate1_assembly.FCStd",
        "exports/jigs/gate1/gate1_assembly.step",
        "exports/jigs/gate1/gate1_powered_assembly.FCStd",
        "exports/jigs/gate1/gate1_powered_assembly.step",
        "exports/jigs/gate1/gate1_powered_assembly.stl",
        "exports/jigs/gate1/bom.csv",
        "exports/jigs/gate1/jig_manifest.csv",
        "exports/jigs/gate1/assembly_ko.md",
        "exports/jigs/gate1/test_procedure_ko.md",
        "exports/jigs/gate1/fastener_schedule.csv",
        "exports/jigs/gate1/wiring_bom.csv",
        "exports/jigs/gate1/wiring_24v_hardcut.svg",
        "exports/jigs/gate1/specimen_schedule.csv",
        "exports/jigs/gate1/calibration_log_template.csv",
        "exports/jigs/gate1/preflight_inspection_template.csv",
        "exports/jigs/gate1/drive_calibration_template.csv",
        "exports/jigs/gate1/gate1_results_template.csv",
        "exports/jigs/gate1/jam_recovery_results_template.csv",
        "exports/jigs/gate1/chip_size_results_template.csv",
        "exports/jigs/gate1/evidence_manifest_template.csv",
        "exports/jigs/gate1/gate1_release_record_ko.md",
        "exports/cnc/extruder/EX-SCR-01_drawing.svg",
        "exports/cnc/extruder/EX-BAR-01_drawing.svg",
        "exports/cnc/extruder/EX-CPN_drawing.svg",
        "exports/cnc/extruder/EX-DIE_drawing.svg",
        "exports/cnc/extruder/inspection_report_template.csv",
        "exports/cnc/extruder/supplier_deviation_template.csv",
        "exports/cnc/extruder/manufacturing_audit_ko.md",
        "exports/cnc/extruder/supplier_rfq_checklist_ko.md",
        "exports/drive_interface/interface_contract_ko.md",
        "exports/drive_interface/reference_variant.json",
        "exports/thermal/manifest.csv",
        "exports/thermal/heater_rfq_ko.md",
        "exports/thermal/channel_schedule.csv",
    ):
        path=ROOT/rel; require(path.exists() and path.stat().st_size>100,f"missing {rel}")
    for spec in jig_specs:
        folder=ROOT/"exports/jigs/gate1/parts"/spec["id"]
        for ext in ("FCStd","step","stl","dxf"):
            require((folder/f"{spec['id']}.{ext}").exists(),f"missing Gate-1 fabrication format {spec['id']}.{ext}")
        notes=(folder/"drawing_notes.md"); require(notes.exists() and "controlling requirements" in notes.read_text(),f"missing Gate-1 drawing note {spec['id']}")
    for spec in rfq_specs:
        folder=ROOT/"exports/cnc/extruder/parts"/spec["id"]
        for ext in ("FCStd","step","stl","dxf"):
            require((folder/f"{spec['id']}.{ext}").exists(),f"missing extruder fabrication format {spec['id']}.{ext}")
    required_machine_ids={"IN-HOP-01","FD-BIN-01","FD-HOP-01","FD-GSK-01","FD-MET-01","FD-MET-02","FD-MET-03","FD-DA-01","FD-CP-01","EX-THR-01","EX-SH-01","DRV-GD-01","FM-PL-01","FM-RL-01","FM-AX-01","FM-EB-01","FM-GR-01","FM-GC-01","FM-GA-01","SP-DA-01","SP-AX-01","SP-RL-01","SP-SH-01","SP-BP-01","SP-BR-01","SP-MM-01","SP-TR-01","SP-DS-01","CT-ENC-01"}
    required_machine_ids |= {"SP-TG-01", "SP-AX-02", "SP-AW-08"}
    require({spec["id"] for spec in machine_specs}==required_machine_ids,"machine fabrication family set incomplete")
    shredder_by={spec["id"]:spec["shape"] for spec in shredder_specs}
    require("CUT-09" in shredder_by,"CUT-09 chamber sleeves missing")
    sleeve=shredder_by["CUT-09"]
    require(len(sleeve.Solids)==1 and abs(sleeve.BoundBox.ZLength-128)<.01,"CUT-09 must be one OD10/ID6.6/L128 solid")
    for spec in machine_specs:
        folder=ROOT/"exports/fabrication/parts"/spec["id"]
        for ext in ("FCStd","step","stl","dxf"):
            require((folder/f"{spec['id']}.{ext}").exists(),f"missing machine fabrication format {spec['id']}.{ext}")
        require((folder/"drawing_notes.md").exists(),f"missing machine fabrication notes {spec['id']}")

    drive_ids={"DRV-01","DRV-02","DRV-03","DRV-03R","DRV-A42","DRV-A60","DRV-F01A","DRV-F01B","DRV-F01P"}
    drive_rows=list(csv.DictReader((ROOT/"exports/drive_interface/manifest.csv").open()))
    require({row["part_id"] for row in drive_rows}==drive_ids,"drive interface family set incomplete")
    drive_by_id={row["part_id"]:row for row in drive_rows}
    require(drive_by_id["DRV-02"]["release_state"]=="LEGACY_SUPERSEDED_BY_DIRECT_KEYED_GGM_SH_30T","DRV-02 was reactivated")
    active_drive={"DRV-03","DRV-03R"}
    for pid,row in drive_by_id.items():
        if pid in active_drive:
            require(row["release_state"].startswith("ACTIVE_GGM_PHASE_GEAR"),pid+" active phase state drift")
        else:
            require(row["release_state"].startswith("LEGACY_"),pid+" generic drive part was not marked legacy")
        note=(ROOT/"exports/drive_interface/parts"/pid/"drawing_notes.md").read_text(encoding="utf-8")
        require(row["release_state"] in note,pid+" drawing note release state drift")
    for part_id in drive_ids:
        folder=ROOT/"exports/drive_interface/parts"/part_id
        for ext in ("FCStd","step","stl","dxf"):
            require((folder/f"{part_id}.{ext}").exists(),f"missing drive format {part_id}.{ext}")
    pin=motor_side_fuse_pin()
    require(len(pin.Solids)==1 and pin.isValid(),"DRV-F01P must be one valid waisted solid")
    centre_outer=Part.makeCylinder(1.40,0.2,App.Vector(-0.1,0,0),App.Vector(1,0,0)).cut(Part.makeCylinder(0.95,0.2,App.Vector(-0.1,0,0),App.Vector(1,0,0)))
    require(pin.common(centre_outer).Volume<0.001,"DRV-F01P centre must be actual Ø1.8 waist")
    end_probe=Part.makeCylinder(1.40,0.2,App.Vector(9.9,0,0),App.Vector(1,0,0)).cut(Part.makeCylinder(1.0,0.2,App.Vector(9.9,0,0),App.Vector(1,0,0)))
    require(pin.common(end_probe).Volume>0.2,"DRV-F01P ends must remain Ø3")
    gmp=gmp60_60127_reference_shape().BoundBox
    require(abs(gmp.ZLength-211.8)<0.01 and abs(gmp.XLength-60.5)<0.01,"exact GMP60 reference envelope mismatch")
    band=mica_band_heater_shape()
    require(len(band.Solids)==1 and abs(band.BoundBox.ZLength-45.0)<0.01,"custom band heater solid invalid")

    # PPR-C08 correction: two 625 bearings are seated in the turned roller,
    # while the printed brackets locate a fixed Ø5 axle.  The former Ø8.4
    # hole/"625 bearing" contradiction must not return.
    machine_by={spec["id"]:spec["shape"] for spec in machine_specs}
    auger=machine_by["FD-MET-02"]
    feeder_shaft=machine_by["FD-MET-03"]
    auger_pin_probe=Part.makeCylinder(1.49,12,App.Vector(-6,0,8),App.Vector(1,0,0))
    shaft_pin_probe=Part.makeCylinder(1.49,8,App.Vector(-4,0,11),App.Vector(1,0,0))
    require(auger.common(auger_pin_probe).Volume<0.01,"FD-MET-02 Ø3 cross-pin hole missing")
    require(feeder_shaft.common(shaft_pin_probe).Volume<0.01,"FD-MET-03 Ø3 cross-pin hole missing")
    upper_pin_probe=Part.makeCylinder(1.49,8,App.Vector(-4,0,292),App.Vector(1,0,0))
    require(feeder_shaft.common(upper_pin_probe).Volume<0.01,"FD-MET-03 upper coupling pin hole missing")
    coupling=machine_by["FD-CP-01"]
    require(coupling.common(Part.makeCylinder(4.02,24)).Volume<0.01,
            "FD-CP-01 Ø8 coupling bore missing")
    mount=machine_by["FD-DA-01"]
    require(mount.isValid() and len(mount.Solids)==1 and abs(mount.BoundBox.XLength-126)<.01,
            "FD-DA-01 frame mount geometry invalid")
    # 2.2 N.m at r=4 mm; double-shear Ø3 pin and two 2 mm boss walls.
    pin_shear_mpa=(2.2/.004)/(2*math.pi*.003**2/4)/1e6
    boss_bearing_mpa=(2.2/.004)/(2*.003*.002)/1e6
    require(124/pin_shear_mpa>=2 and 215/boss_bearing_mpa>=2,
            "SYS-15 pin/boss static safety factor below 2")
    eccentric=machine_by["FM-EB-01"]
    require(len(eccentric.Solids)==1 and eccentric.isValid(),"FM-EB-01 must be one valid metal solid")
    require(abs(eccentric.BoundBox.XLength-24)<.01 and abs(eccentric.BoundBox.YLength-13)<.01,
            "FM-EB-01 flange/shank envelope mismatch")
    guide=machine_by["FM-GR-01"]
    for z in (1.10,13.90):
        seat_probe=Part.makeCylinder(7.9,5.0,App.Vector(0,0,z))
        require(guide.common(seat_probe).Volume<0.01,f"FM-GR-01 Ø16 bearing seat missing at z={z}")
    shoulder_probe=Part.makeCylinder(7.8,0.2,App.Vector(0,0,6.2)).cut(Part.makeCylinder(6.2,0.2,App.Vector(0,0,6.2)))
    require(guide.common(shoulder_probe).Volume>5.0,"FM-GR-01 bearing shoulder missing")
    cap=machine_by["FM-GC-01"]
    require(len(cap.Solids)==1 and abs(cap.BoundBox.ZLength-1)<.01,"FM-GC-01 must be one 1 mm metal cap")
    cap_overlap=Part.makeCylinder(7.95,.9,App.Vector(0,0,.05)).cut(Part.makeCylinder(7.55,.9,App.Vector(0,0,.05)))
    require(cap.common(cap_overlap).Volume>1.0,"FM-GC-01 outer-ring overlap missing")
    axle=machine_by["FM-GA-01"]
    require(abs(axle.BoundBox.XLength-5.0)<0.01 and abs(axle.BoundBox.ZLength-30.0)<0.01,"FM-GA-01 must be Ø5 x30")
    spool_plate=machine_by["SP-BP-01"]
    require(abs(spool_plate.BoundBox.YLength-10.0)<0.01,"SP-BP-01 must be 10 mm thick")
    pocket_probe=Part.makeCylinder(13.9,8.0,App.Vector(30,0.02,30),App.Vector(0,1,0))
    require(spool_plate.common(pocket_probe).Volume<0.01,"SP-BP-01 Ø28 H7 pocket missing")
    shoulder_probe=Part.makeCylinder(13.9,1.8,App.Vector(30,8.15,30),App.Vector(0,1,0)).cut(
        Part.makeCylinder(13.1,1.8,App.Vector(30,8.15,30),App.Vector(0,1,0)))
    require(spool_plate.common(shoulder_probe).Volume>4.0,"SP-BP-01 integral bearing shoulder missing")
    spool_retainer=machine_by["SP-BR-01"]
    require(abs(spool_retainer.BoundBox.YLength-2.0)<0.01 and len(spool_retainer.Solids)==1,
            "SP-BR-01 must be one 2 mm metal retainer")
    overlap_probe=Part.makeCylinder(13.9,1.8,App.Vector(30,0.1,30),App.Vector(0,1,0)).cut(
        Part.makeCylinder(13.1,1.8,App.Vector(30,0.1,30),App.Vector(0,1,0)))
    require(spool_retainer.common(overlap_probe).Volume>4.0,"SP-BR-01 outer-ring overlap missing")
    ppr08=next(spec["shape"] for spec in print_parts() if spec["id"]=="PPR-C08")
    axle_probe=Part.makeCylinder(2.55,4.8,App.Vector(30,0.1,50),App.Vector(0,1,0))
    require(ppr08.common(axle_probe).Volume<0.01,"PPR-C08 Ø5.2 axle bore missing")
    assembly_by={item["name"]:item["shape"] for item in assembly_objects()}
    assembly_names=set(assembly_by)
    require({"GuideBearingRetainerFront","GuideBearingRetainerRear"} <= assembly_names,
            "guide-bearing retainers missing from assembly")
    require({"PullerEccentricBushFront","PullerEccentricBushRear"} <= assembly_names,
            "paired puller eccentric bushes missing from assembly")
    gap=assembly_by["PullerRoll53.6"].distToShape(assembly_by["PullerRoll95.4"])[0]
    require(1.79 <= gap <= 1.81,f"puller nominal adjusted gap mismatch: {gap}")
    require(abs((53.6+95.4)/2-74.5)<.01,"puller nip centreline mismatch")
    require(sum(name.startswith("CUT09Sleeve") for name in assembly_names)==4,"four chamber sleeves missing from assembly")
    require({"GuideBearingFront","GuideBearingRear"} <= assembly_names,"625 bearings missing from assembly")
    require({"DriveMotorGMP60Reference","DriveAdapterGMP60","BarrelBandHeaterZ1","BarrelBandHeaterZ2","BarrelBandHeaterZ3","DieCartridgeHeater","TemperatureProbeT1","TemperatureProbeT2","TemperatureProbeT3","TemperatureProbeT4","TemperatureProbeT5"} <= assembly_names,"motor/thermal assembly objects incomplete")
    require("FeederAugerSpringPin" in assembly_names,"SYS-15 feeder auger pin missing from assembly")
    require({"FeederDriveMount","FeederDriveCoupling","FeederDriveReference"} <= assembly_names,
            "selected feeder reference drive path missing from assembly")
    sys.path.insert(0,str(ROOT))
    from validation.physical_v08.frame_release import validate as validate_frame
    frame = validate_frame(ROOT)
    require(frame['status']=='FRAME_CUTLIST_BINDING_PASS', 'current GGM cut list binding failed')
    require(frame['members']==40 and frame['cut_authorization'] is False,
            'frame member count or authorization drift')
    require(frame['totals']=={'2020':{'count':36,'length_mm':15078.0},
                             '2040':{'count':4,'length_mm':2180.0}},
            'current modest frame reduction changed unexpectedly')
    jig_bom=list(csv.DictReader((ROOT/"exports/jigs/gate1/bom.csv").open()))
    require(any(r["item_id"]=="CUT-01" and r["qty"]=="2" for r in jig_bom),"Gate-1 coupon quantity")
    p4_path=next(r for r in jig_bom if r["item_id"]=="GGM-SH-PATH")
    require("DRV-02" not in p4_path["source"] and "direct-keyed" in p4_path["item"],"P4 powered path still depends on DRV-02")
    require("4x4 key" in p4_path["notes"] and "6x6 key" in p4_path["notes"],"P4 direct sprocket torque path missing")
    fst19=next(r for r in csv.DictReader((ROOT/"exports/jigs/gate1/fastener_schedule.csv").open()) if r["joint_id"]=="FST-19")
    require(fst19["nominal_torque_Nm"]=="HOLD" and "axial retention" in fst19["mating_parts"],"P4 sprocket retention was given an unverified fixed torque")
    require({r["item_id"] for r in jig_bom if r["item_id"].startswith("G1J-")} >= {f"G1J-{i:02d}" for i in range(1,13)},"Gate-1 BOM part coverage")
    hardcut=(ROOT/"exports/jigs/gate1/wiring_24v_hardcut.svg").read_text()
    for token in ("F1 20 A","F2 2 A","S0 E-STOP","S1 GUARD","K0 coil","K1 NO","M1 GGM SH","manual-reset"):
        require(token in hardcut,f"hard-cut schematic token missing: {token}")
    result_rows=list(csv.DictReader((ROOT/"exports/jigs/gate1/gate1_results_template.csv").open()))
    require(len(result_rows)==25,"Gate-1 result template must preallocate 25 specimen trials")
    require(len(list(csv.DictReader((ROOT/"exports/jigs/gate1/jam_recovery_results_template.csv").open())))==6,"Gate-1 jam template must preallocate 3 trials/material")
    require(len(list(csv.DictReader((ROOT/"exports/jigs/gate1/chip_size_results_template.csv").open())))==2,"Gate-1 chip template must preallocate PLA/PET batches")
    release=(ROOT/"exports/jigs/gate1/gate1_release_record_ko.md").read_text()
    require("현재 상태: `NOT_RUN`" in release,"Gate-1 template must not claim a physical result")
    print_rows=list(csv.DictReader((ROOT/"exports/jigs/gate1/print_manifest.csv").open()))
    require(sum(float(r["estimated_mass_g"]) for r in print_rows) <= 250.0,"Gate-1 jig print mass")
    rfq=(ROOT/"exports/cnc/extruder/manufacturing_audit_ko.md").read_text()
    for token in ("SCM440 KS D3867/JIS G4105","Datum A","Datum B","Datum C","Datum D","4x M4 x0.7-6H","2.0/2.9","0.28–0.32","Ø3.20 +0.05/0","EX-DIE-01","Ø8 수평 유로","3–6 MPa","HOLD"):
        require(token in rfq,f"extruder RFQ controlling token missing: {token}")
    print("MANUFACTURING_GEOMETRY_RFQ_OK")


if __name__=="__main__": main()
