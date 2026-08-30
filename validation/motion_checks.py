#!/usr/bin/env python3
"""Full dancer/traverse motion, service-path and operating-envelope checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cad/freecad/compact"))
from geometry import assembly_objects, dancer_arm_shape, print_parts, review_keepout_objects  # noqa: E402


def require(ok,message):
    if not ok: raise AssertionError(message)


def overlap(a,b): return a.common(b).Volume


def main():
    items=assembly_objects(); by={item["name"]:item["shape"] for item in items}
    printed={item["id"]:item["shape"] for item in print_parts()}
    keepouts={item["name"]:item["shape"] for item in review_keepout_objects()}
    dancer_positions=[]; dancer_min_clearance=1e9
    dancer_obstacles=[by[name] for name in ("Spool","TraverseRodA","TraverseRodB","PPR-C10_TraverseCarriage","CableDuct","ControlPanel")]
    for angle in range(-25,26):
        shape=dancer_arm_shape(angle); dancer_positions.append(shape)
        for obstacle in dancer_obstacles:
            require(overlap(shape,obstacle)<0.01,f"dancer collision at {angle} deg")
            dancer_min_clearance=min(dancer_min_clearance,shape.distToShape(obstacle)[0])

    traverse_positions=[]; traverse_min_clearance=1e9
    traverse_obstacles=[by[name] for name in ("Spool","DancerArm","CableDuct","ControlPanel","FrameColumn450_680")]
    for offset in range(0,81,2):
        shape=printed["PPR-C10"].copy(); shape.translate(App.Vector(270+offset,420,268)); traverse_positions.append(shape)
        for obstacle in traverse_obstacles:
            require(overlap(shape,obstacle)<0.01,f"traverse collision at {offset} mm")
            traverse_min_clearance=min(traverse_min_clearance,shape.distToShape(obstacle)[0])

    service_obstacles=("PSU","ControlPanel","SealedFeedHopper","CutterPlateFront","Spool")
    for name in service_obstacles:
        require(overlap(keepouts["KO_ScrewService"],by[name])<0.01,f"screw service path blocked by {name}")

    operating=Part.makeCompound([item["shape"] for item in items]+dancer_positions+traverse_positions)
    bb=operating.BoundBox
    require(bb.XMin>=0 and bb.YMin>=0 and bb.ZMin>=0,"motion leaves positive machine datum")
    require(bb.XLength<=500 and bb.YLength<=750 and bb.ZLength<=1000,"hard operating-motion envelope")
    require(bb.XLength<=480 and bb.YLength<=720 and bb.ZLength<=950,"target operating-motion envelope")
    result={
        "revision":"virtual-physics-closure-v0.5.1",
        "dancer":{"range_deg":[-25,25],"samples":len(dancer_positions),"minimum_checked_clearance_mm":round(dancer_min_clearance,3)},
        "traverse":{"stroke_mm":80,"samples":len(traverse_positions),"minimum_checked_clearance_mm":round(traverse_min_clearance,3)},
        "operating_motion_bounding_box_mm":[round(bb.XLength,3),round(bb.YLength,3),round(bb.ZLength,3)],
        "service_path_checked_against":list(service_obstacles),
        "status":"PASS",
        "scope":"nominal rigid CAD positions; donor cable flexibility and physical deflection remain EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN",
    }
    out=ROOT/"validation/results"; out.mkdir(parents=True,exist_ok=True)
    (out/"full_motion.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(f"FULL_MOTION_ENVELOPE_OK dancer={len(dancer_positions)} traverse={len(traverse_positions)} bbox={result['operating_motion_bounding_box_mm']}")


if __name__=="__main__": main()
