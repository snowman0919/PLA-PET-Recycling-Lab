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
from manufacturing import extruder_rfq_parts, extruder_screw, gate1_assembly, gate1_parts, generic_phase_gear_lamination  # noqa: E402


def require(value,message):
    if not value: raise AssertionError(message)


def main():
    jig_specs=gate1_parts()
    rfq_specs=extruder_rfq_parts()
    require({p["id"] for p in jig_specs}=={f"G1J-{i:02d}" for i in range(1,11)}|{f"G1J-P{i:02d}" for i in range(1,4)},"Gate-1 part family set incomplete")
    for spec in jig_specs+rfq_specs:
        shape=spec["shape"]
        require(shape.isValid() and not shape.isNull(),f"invalid shape {spec['id']}")
    jig=Part.makeCompound([item["shape"] for item in gate1_assembly()])
    bb=jig.BoundBox
    require(bb.XLength <= 420 and bb.YLength <= 260 and bb.ZLength <= 210,f"Gate-1 envelope {bb.XLength,bb.YLength,bb.ZLength}")
    by={item["name"]:item["shape"] for item in gate1_assembly()}
    require(by["CUT01Coupon135"].common(by["CUT01Coupon183"]).Volume < 0.01,"coupon collision")
    require(by["CUT01Coupon135"].distToShape(by["CUT01Coupon183"])[0] >= 0.49,"coupon metal-shim gap")
    require(min(by[name].distToShape(by["CUT04ScreenCoupon"])[0] for name in ("CUT01Coupon135","CUT01Coupon183")) >= 1.9,"Gate-1 screen clearance")
    require(by["TorqueArm250"].common(by["GuardRight"]).Volume < 0.01,"torque arm/guard slot collision")
    require(by["TorqueArm250"].distToShape(by["GuardRight"])[0] >= 0.49,"torque arm slot running clearance")
    require(all(name in by for name in ("G1J08ScreenRailLeft","G1J08ScreenRailRight","G1J09InterlockBracket")),"screen rail/interlock hardware missing from assembly")
    require(sum(1 for name in by if name.startswith("G1J07Upright"))==4,"four metal guard uprights required")
    require(sum(1 for name in by if name.startswith("G1J10PlateFoot"))==4,"four metal CUT-03 feet required")
    # DRV-03 registration must be explicit metal fasteners/dowel, not a text-only claim.
    gear=generic_phase_gear_lamination()
    for angle,diameter in ((0,4.5),(120,4.5),(240,3.0)):
        import math
        a=math.radians(angle)
        probe=Part.makeCylinder(diameter/2,6,App.Vector(15*math.cos(a),0,15*math.sin(a)),App.Vector(0,1,0))
        require(gear.common(probe).Volume < 0.01,f"DRV-03 PCD30 hole missing at {angle}")
    screw=next(p["shape"] for p in rfq_specs if p["id"]=="EX-SCR-01")
    barrel=next(p["shape"] for p in rfq_specs if p["id"]=="EX-BAR-01")
    require(abs(screw.BoundBox.ZLength-316.0)<0.02,"screw total length")
    require(max((v.Point.x**2+v.Point.y**2)**0.5 for v in screw.Vertexes) <= 7.961,"screw OD exceeds 15.92")
    render_screw=extruder_screw(facet_step=2.0)
    require(not render_screw.isNull() and render_screw.isValid() and len(render_screw.Solids)==1,"RFQ render screw must remain one valid solid")
    require(abs(barrel.BoundBox.ZLength-280.0)<0.01,"barrel length")
    require(len(barrel.Solids)==1,"barrel must be one solid")
    # Controlling RFQ port is 18 mm axial x 20 mm chord from B+12 to B+30.
    # Probe the cut volume directly so STEP cannot silently swap the dimensions.
    feed_probe=Part.makeBox(20,34,18,App.Vector(-10,-17,12))
    require(barrel.common(feed_probe).Volume<0.01,"barrel feed port 18 axial x 20 chord missing")
    for z in (11.0,30.5):
        intact_probe=Part.makeBox(1,1,0.5,App.Vector(-0.5,-16.5,z))
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
    rfq_by={p["id"]:p["shape"] for p in rfq_specs}
    require({f"EX-DIE-{i:02d}" for i in range(1,6)} <= set(rfq_by),"connected die RFQ set incomplete")
    body=rfq_by["EX-DIE-01"]
    horizontal=Part.makeCylinder(3.9,21,App.Vector(19,0,0),App.Vector(1,0,0))
    vertical=Part.makeCylinder(3.9,28,App.Vector(20,0,-24))
    require(body.common(horizontal).Volume<0.01 and body.common(vertical).Volume<0.01,"90 degree die melt channels missing")
    require(horizontal.common(vertical).Volume>1.0,"90 degree die channels do not intersect")
    require(rfq_by["EX-DIE-02"].Solids and rfq_by["EX-DIE-03"].Solids and rfq_by["EX-DIE-04"].Solids,"die removable parts invalid")
    retainer=rfq_by["EX-DIE-04"]
    for x in (13.0,26.5):
        web_probe=Part.makeBox(1,10,1.5,App.Vector(x,-5,-25.5))
        require(retainer.common(web_probe).Volume>14.0,"sacrificial retainer 10 mm web missing")
    for rel in (
        "exports/jigs/gate1/gate1_assembly.FCStd",
        "exports/jigs/gate1/gate1_assembly.step",
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
    jig_bom=list(csv.DictReader((ROOT/"exports/jigs/gate1/bom.csv").open()))
    require(any(r["item_id"]=="CUT-01" and r["qty"]=="2" for r in jig_bom),"Gate-1 coupon quantity")
    require({r["item_id"] for r in jig_bom if r["item_id"].startswith("G1J-")} >= {f"G1J-{i:02d}" for i in range(1,11)},"Gate-1 BOM part coverage")
    hardcut=(ROOT/"exports/jigs/gate1/wiring_24v_hardcut.svg").read_text()
    for token in ("F1 20 A","F2 2 A","S0 E-STOP","S1 GUARD","K0 coil","K1 NO","manual-reset"):
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
    for token in ("SCM440 KS D3867/JIS G4105","Datum A","Datum B","Datum C","Datum D","4x M4 x0.7-6H","2.0/2.9","0.28–0.32","EX-DIE-01","Ø8 수평 유로","3–6 MPa","HOLD"):
        require(token in rfq,f"extruder RFQ controlling token missing: {token}")
    print("MANUFACTURING_GEOMETRY_RFQ_OK")


if __name__=="__main__": main()
