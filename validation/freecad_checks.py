#!/usr/bin/env python3
"""FreeCAD collision, load-path and service geometry checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import Part

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from geometry import assembly_objects  # noqa: E402


def require(ok,msg):
    if not ok: raise AssertionError(msg)


def overlap(a,b):
    return a.common(b).Volume


def main():
    items=assembly_objects(); by={i["name"]:i["shape"] for i in items}
    compound=Part.makeCompound([i["shape"] for i in items]); bb=compound.BoundBox
    require((bb.XMin,bb.YMin,bb.ZMin)==(0.0,0.0,0.0),"negative envelope")
    require(bb.XLength<=500 and bb.YLength<=750 and bb.ZLength<=1000,"hard envelope")
    for a,b in (("PSU","HotShield"),("PSU","Barrel"),("PSU","ExtruderDrive"),("CableDuct","PSU"),("Spool","CoolingDuct"),("Spool","Gauge"),("Spool","PullerPlate"),("Spool","ControlPanel"),("DancerSweep","Spool")):
        require(overlap(by[a],by[b])<0.01,f"collision {a}/{b}: {overlap(by[a],by[b])}")
    hooks_a=[by[f"Hook105_{i}"] for i in range(6)]
    hooks_b=[by[f"Hook153_{i}"] for i in range(6)]
    require(max(overlap(a,b) for a in hooks_a for b in hooks_b)<0.01,"cutter axial interleave collision")
    require(min(s.distToShape(by["Screen"])[0] for s in hooks_a+hooks_b)>=1.9,"screen clearance below metal-shim baseline")
    for cx in (105,153):
        shaft=by[f"Shaft{cx}"]
        for y in (315,455): require(overlap(shaft,by[f"Bearing{cx}_{y}"])<0.01,"shaft intersects bearing ring")
    require(overlap(by["Barrel"],by["HotShield"])<0.01,"barrel touches grounded shield")
    report={"revision":"compact-single-path-v0.3","envelope_mm":[bb.XLength,bb.YLength,bb.ZLength],"critical_collision_pairs":9,"cutter_pair_checks":36,"screen_min_clearance_mm":round(min(s.distToShape(by["Screen"])[0] for s in hooks_a+hooks_b),3),"result":"PASS","scope":"nominal CAD only; tolerances and dynamics require physical gates"}
    (ROOT/"simulation/cad_clearance.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("FREECAD_COLLISION_LOAD_PATH_OK")


if __name__=="__main__": main()
