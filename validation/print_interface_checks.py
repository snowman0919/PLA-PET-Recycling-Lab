#!/usr/bin/env python3
"""Printed-wall and physical fastener/insert interface release checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad/freecad/compact"))
from geometry import print_parts  # noqa: E402


AXIS = {"x": App.Vector(1, 0, 0), "y": App.Vector(0, 1, 0), "z": App.Vector(0, 0, 1)}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sampled_solid_runs(shape, start, direction, length, step=0.025):
    origin = App.Vector(*start); vector = App.Vector(*direction)
    count = int(length / step) + 1
    flags = [shape.isInside(origin + vector * (i * step), 1e-6, False) for i in range(count)]
    runs=[]; began=None
    for i, flag in enumerate(flags + [False]):
        if flag and began is None: began=i
        if not flag and began is not None:
            runs.append((i-began)*step); began=None
    return runs


def bore_probe(shape, axis, start, radius, length):
    direction=AXIS[axis]
    origin=App.Vector(*start) + direction*0.10
    inner=Part.makeCylinder(radius*0.92, max(0.1,length-0.20), origin, direction)
    void_overlap=shape.common(inner).Volume
    outer=Part.makeCylinder(radius+1.60, max(0.1,length-0.20), origin, direction)
    annulus=outer.cut(Part.makeCylinder(radius+0.25,max(0.1,length-0.20),origin,direction))
    surrounding=shape.common(annulus).Volume
    return void_overlap,surrounding


def perpendicular_edge_distance(shape, axis, start):
    bb=shape.BoundBox; x,y,z=start
    coordinates={"x":((y,bb.YMin,bb.YMax),(z,bb.ZMin,bb.ZMax)),"y":((x,bb.XMin,bb.XMax),(z,bb.ZMin,bb.ZMax)),"z":((x,bb.XMin,bb.XMax),(y,bb.YMin,bb.YMax))}[axis]
    return min(min(value-low,high-value) for value,low,high in coordinates)


def main():
    rows=[]
    for spec in print_parts():
        required_lines=spec["walls"]*spec["nozzle_mm"]
        require(abs(required_lines-spec["minimum_wall_mm"])<1e-6,f"{spec['id']} wall declaration/line count mismatch")
        runs=sampled_solid_runs(spec["shape"],*spec["wall_probe"])
        require(runs,f"{spec['id']} wall probe missed solid")
        measured=min(runs)
        require(measured+0.06>=spec["minimum_wall_mm"],f"{spec['id']} sampled wall {measured:.3f} < {spec['minimum_wall_mm']}")
        bore_rows=[]
        for axis,start,radius,length in spec["interface_bores"]:
            void,surround=bore_probe(spec["shape"],axis,start,radius,length)
            edge=perpendicular_edge_distance(spec["shape"],axis,start)
            require(void<1e-4,f"{spec['id']} {axis}-bore is not open: {void}")
            require(surround>1.0,f"{spec['id']} {axis}-bore lacks load-bearing surrounding material")
            require(edge>=radius+1.5,f"{spec['id']} bore edge ligament {edge-radius:.2f} mm")
            bore_rows.append({"axis":axis,"start_mm":start,"diameter_mm":2*radius,"length_mm":length,"bbox_edge_distance_mm":round(edge,3),"void_overlap_mm3":round(void,8),"surrounding_probe_mm3":round(surround,3)})
        rows.append({"part_id":spec["id"],"required_wall_mm":spec["minimum_wall_mm"],"sampled_wall_mm":round(measured,3),"perimeters":spec["walls"],"nozzle_mm":spec["nozzle_mm"],"fastener":spec["fastener"],"insert_or_nut":spec["insert"],"interfaces":bore_rows,"status":"PASS"})
    result={"revision":"solid-manifold-openmodelica-v0.4","method":"design-specific B-Rep line sampling plus exact bore-void/annular-material probes","limitations":"sampling proves the declared critical walls and fastener interfaces, not every local mesh thickness; source dimensions remain controlling","parts":rows,"status":"PASS"}
    out=ROOT/"validation/results"; out.mkdir(parents=True,exist_ok=True)
    (out/"print_interfaces.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(f"MINIMUM_WALL_FASTENER_INSERT_OK parts={len(rows)}")


if __name__=="__main__": main()
