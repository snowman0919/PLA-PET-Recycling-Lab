#!/usr/bin/env python3
"""FreeCAD checks for VE drive, Gate-1 jig and extruder RFQ package."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from manufacturing import extruder_rfq_parts, gate1_assembly, gate1_parts  # noqa: E402


def require(value,message):
    if not value: raise AssertionError(message)


def main():
    for spec in gate1_parts()+extruder_rfq_parts():
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
    screw=next(p["shape"] for p in extruder_rfq_parts() if p["id"]=="EX-SCR-01")
    barrel=next(p["shape"] for p in extruder_rfq_parts() if p["id"]=="EX-BAR-01")
    require(abs(screw.BoundBox.ZLength-316.0)<0.02,"screw total length")
    require(max((v.Point.x**2+v.Point.y**2)**0.5 for v in screw.Vertexes) <= 7.961,"screw OD exceeds 15.92")
    require(abs(barrel.BoundBox.ZLength-280.0)<0.01,"barrel length")
    require(len(barrel.Solids)==1,"barrel must be one solid")
    for rel in (
        "exports/jigs/gate1/gate1_assembly.FCStd",
        "exports/jigs/gate1/gate1_assembly.step",
        "exports/jigs/gate1/bom.csv",
        "exports/jigs/gate1/assembly_ko.md",
        "exports/jigs/gate1/test_procedure_ko.md",
        "exports/cnc/extruder/EX-SCR-01_drawing.svg",
        "exports/cnc/extruder/EX-BAR-01_drawing.svg",
        "exports/cnc/extruder/manufacturing_audit_ko.md",
        "exports/cnc/extruder/supplier_rfq_checklist_ko.md",
        "exports/drive_interface/interface_contract_ko.md",
    ):
        path=ROOT/rel; require(path.exists() and path.stat().st_size>100,f"missing {rel}")
    jig_bom=list(csv.DictReader((ROOT/"exports/jigs/gate1/bom.csv").open()))
    require(any(r["item"]=="CUT-01 coupon disc" and r["qty"]=="2" for r in jig_bom),"Gate-1 coupon quantity")
    print_rows=list(csv.DictReader((ROOT/"exports/jigs/gate1/print_manifest.csv").open()))
    require(sum(float(r["estimated_mass_g"]) for r in print_rows) <= 250.0,"Gate-1 jig print mass")
    print("MANUFACTURING_GEOMETRY_RFQ_OK")


if __name__=="__main__": main()
