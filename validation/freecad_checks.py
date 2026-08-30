#!/usr/bin/env python3
"""FreeCAD collision, load-path and service geometry checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from geometry import assembly_objects, hook_disc, review_keepout_objects  # noqa: E402


def require(ok,msg):
    if not ok: raise AssertionError(msg)


def overlap(a,b):
    return a.common(b).Volume


def shape(by, *candidates):
    """Return first existing shape for a list of legacy/new names."""
    for candidate in candidates:
        if candidate in by:
            return by[candidate]
    return None


def main():
    for artifact in (ROOT/"cad/generation/fcstd/compact_full_assembly.FCStd", ROOT/"exports/print/PPR-C01/PPR-C01.FCStd", ROOT/"exports/cnc/CUT-01/CUT-01.FCStd", ROOT/"exports/cnc/CUT-08/CUT-08.FCStd"):
        document=App.openDocument(str(artifact)); require(document is not None and len(document.Objects)>0,f"cannot reopen {artifact}"); App.closeDocument(document.Name)
    items=assembly_objects(); by={i["name"]:i["shape"] for i in items}
    keepouts={i["name"]:i["shape"] for i in review_keepout_objects()}
    compound=Part.makeCompound([i["shape"] for i in items]); bb=compound.BoundBox
    require((bb.XMin,bb.YMin,bb.ZMin)==(0.0,0.0,0.0),"negative envelope")
    require(bb.XLength<=500 and bb.YLength<=750 and bb.ZLength<=1000,"hard envelope")
    # A blind bore keyway must leave root material outside its 13 mm radial end.
    # This catches an accidental radial slot through a hook/tooth.
    keyway_root_probe=Part.makeBox(2,6,2,App.Vector(-1,0,14))
    require(overlap(hook_disc(),keyway_root_probe)>20.0,"CUT-01 internal keyway opens through cutter root")
    require("DieOrifice" not in by,"process filament must not be a manufactured assembly solid")
    motor_donor_envelope = shape(by, "DriveMotorDonorEnvelope", "DriveMotorGMP60Reference")
    motor_output_interface = shape(by, "DriveMotorOutputInterface", "DriveAdapterGMP60")

    for a,b in (("PSU","HotShield"),("PSU","Barrel"),("PSU","ExtruderDrive"),("CableDuct","PSU"),
                ("Spool","PPR-C05_CoolingDuctLower"),("Spool","PPR-C05_CoolingDuctUpper"),
                ("Spool","PPR-C06_GaugeX"),("Spool","PPR-C06_GaugeY"),
                ("Spool","PullerPlateFront"),("Spool","PullerPlateRear"),("Spool","ControlPanel"),
                ("PPR-C05_CoolingDuctUpper","HotShield"),("PPR-C05_CoolingDuctUpper","Barrel"),
                ("PPR-C05_CoolingDuctUpper","DownDieBody"),("PPR-C05_CoolingDuctLower","PPR-C06_GaugeX"),
                ("PPR-C06_GaugeX","PPR-C06_GaugeY"),("PPR-C06_GaugeY","PPR-C07_PullerGuard"),
                ("PPR-C07_PullerGuard","PullerPlateFront"),("PPR-C07_PullerGuard","PullerPlateRear"),
                ("CableDuct","PPR-C12_CableClip0"),("Screw","Barrel"),("Screw","ThrustPlate")):
        require(overlap(by[a],by[b])<0.01,f"collision {a}/{b}: {overlap(by[a],by[b])}")
    require(motor_donor_envelope is not None, "missing motor donor envelope reference")
    require(motor_output_interface is not None, "missing motor output interface reference")
    require(overlap(motor_donor_envelope, by["MotorMountPlate"])<0.01,f"collision DriveMotorDonorEnvelope/MotorMountPlate: {overlap(motor_donor_envelope, by['MotorMountPlate'])}")
    require(overlap(motor_donor_envelope, by["DriveGuard"])<0.01,f"collision DriveMotorDonorEnvelope/DriveGuard: {overlap(motor_donor_envelope, by['DriveGuard'])}")
    require(overlap(motor_output_interface, by["MotorMountPlate"])<0.01,f"collision DriveMotorOutputInterface/MotorMountPlate: {overlap(motor_output_interface, by['MotorMountPlate'])}")
    require(by["PPR-C05_CoolingDuctUpper"].distToShape(by["HotShield"])[0]>=9.99,"ABS duct/hot-shield gap below 10 mm")
    require(by["PPR-C05_CoolingDuctUpper"].distToShape(by["DownDieBody"])[0]>=20.0,"ABS duct/die-body gap below 20 mm")
    require(overlap(keepouts["KO_DancerSweep"],by["Spool"])<0.01,"dancer full-motion keep-out/spool collision")
    hooks_a=[by[f"Hook105_{i}"] for i in range(6)]
    hooks_b=[by[f"Hook153_{i}"] for i in range(6)]
    require(max(overlap(a,b) for a in hooks_a for b in hooks_b)<0.01,"cutter axial interleave collision")
    require(min(s.distToShape(by["Screen"])[0] for s in hooks_a+hooks_b)>=1.9,"screen clearance below metal-shim baseline")
    require(overlap(by["PhaseGear105"],by["PhaseGear153"])<0.01,"phase gears have solid overlap")
    require(abs(by["PhaseGear105"].BoundBox.XMin + by["PhaseGear105"].BoundBox.XLength/2 - 105) < 0.01,"left phase gear center")
    require(by["PhaseGear105"].distToShape(by["CutterPlateRear"])[0] >= 3.9,"phase gear rear-plate service gap")
    # The active red body is the interchangeable interface keep-in, not the
    # former 270 mm vendor reference that cannot fit this cabinet position.
    require(motor_donor_envelope.BoundBox.XLength <= 90.01 and motor_donor_envelope.BoundBox.YLength <= 220.01 and motor_donor_envelope.BoundBox.ZLength <= 95.01,"donor motor interface envelope")
    require(motor_donor_envelope.distToShape(by["MotorMountPlate"])[0] > 0.5,"donor body is disconnected from universal plate datum")
    require(motor_output_interface.distToShape(by["MotorMountPlate"])[0]<0.01,"output interface does not pass plate notch datum")
    require(by["MotorMountPlate"].BoundBox.YMax <= 260.01,"motor plate orientation/position")
    require(overlap(by["BearingRetainerFront"],by["Bearing105_315"])<0.01,"front bearing retainer blocks rolling elements")
    require(overlap(by["BearingRetainerRear"],by["PhaseGear105"])<0.01,"rear bearing retainer/gear collision")
    for cx in (105,153):
        shaft=by[f"Shaft{cx}"]
        for y in (315,455): require(overlap(shaft,by[f"Bearing{cx}_{y}"])<0.01,"shaft intersects bearing ring")
    require(overlap(by["Barrel"],by["HotShield"])<0.01,"barrel touches grounded shield")
    require(0.13 <= by["Screw"].distToShape(by["Barrel"])[0] <= 0.17,"screw/barrel radial clearance outside 0.14-0.16 mm nominal band")
    require(abs(by["Screw"].BoundBox.XMin-by["Barrel"].BoundBox.XMin-24.0)<0.02,"screw tip setback from barrel front is not 24 mm")
    require(overlap(by["DownDieBody"],by["HotShield"])<0.01,"die body touches grounded shield")
    require(overlap(by["Barrel"],by["DownDieGasket"])<0.01 and by["Barrel"].distToShape(by["DownDieGasket"])[0]<0.01,"barrel/gasket interface is disconnected")
    require(overlap(by["DownDieGasket"],by["DownDieBody"])<0.01 and by["DownDieGasket"].distToShape(by["DownDieBody"])[0]<0.01,"gasket/die interface is disconnected")
    for name in ("DownDieBreaker","DownDieInsert","DownDieRelief"):
        require(overlap(by[name],by["DownDieBody"])<0.01,f"die removable part overlaps body: {name}")
    require(abs(by["DownDieInsert"].CenterOfMass.x-74.5)<0.05,"die outlet is off shared forming centreline")
    require(abs((by["PullerRoll54.5"].BoundBox.XMax+by["PullerRoll94.5"].BoundBox.XMin)/2-74.5)<0.05,"puller nip is off die centreline")
    require(abs(by["FeederHousing"].CenterOfMass.x-354.0)<0.05,"feeder housing not aligned to B+12..30 barrel port")
    require(by["FeederHousing"].distToShape(by["Barrel"])[0]<0.01,"feeder housing is disconnected from barrel port datum")
    require(0.19 <= by["FeederHousing"].distToShape(by["FeederRotor"])[0] <= 0.21,"feeder rotor radial clearance")
    for rod in ("TraverseRodA","TraverseRodB"):
        require(overlap(by[rod],by["PPR-C10_TraverseCarriage"])<0.01 and by[rod].distToShape(by["PPR-C10_TraverseCarriage"])[0]>=0.19,"traverse rod/carriage bore clearance")
    report={"revision":"safety-orchestration-closure-v0.6.1","envelope_mm":[bb.XLength,bb.YLength,bb.ZLength],"critical_collision_pairs":35,"cutter_pair_checks":36,"screen_min_clearance_mm":round(min(s.distToShape(by["Screen"])[0] for s in hooks_a+hooks_b),3),"forming_centerline_x_mm":74.5,"duct_to_hot_shield_gap_mm":round(by["PPR-C05_CoolingDuctUpper"].distToShape(by["HotShield"])[0],3),"screw_barrel_radial_clearance_mm":round(by["Screw"].distToShape(by["Barrel"])[0],3),"die_connection":"barrel -> C110 gasket -> EX-DIE-01 -> EX-DIE-02/03/04 open discharge","phase_drive":"interchangeable donor envelope + DRV-Axx + motor-side DRV-F01 relief + #35 chain + cutter-side DRV-02 hub + generic M3 Z16 face18 pair","result":"PASS","scope":"nominal CAD only; donor dimensions and dynamics require Gate-1"}
    (ROOT/"simulation/cad_clearance.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("FREECAD_COLLISION_LOAD_PATH_OK")


if __name__=="__main__": main()
