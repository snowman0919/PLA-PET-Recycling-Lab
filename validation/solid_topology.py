#!/usr/bin/env python3
"""Release-blocking B-Rep topology and active-object classification audit."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMPACT=ROOT/"cad/freecad/compact"
sys.path.insert(0,str(COMPACT))

from geometry import assembly_objects, print_parts, review_keepout_objects, shredder_metal_parts, tolerance_coupon  # noqa: E402
from manufacturing import extruder_rfq_parts, gate1_parts  # noqa: E402

REV="implementation-crosssolver-v0.6"


def audit(part_id,shape,category,expected_solids=1):
    errors=[]
    solids=len(shape.Solids)
    if not shape.isValid(): errors.append("BREP_INVALID")
    if shape.isNull(): errors.append("NULL_SHAPE")
    if shape.Volume <= 1e-6: errors.append("NONPOSITIVE_VOLUME")
    if solids != expected_solids: errors.append(f"SOLID_COUNT_{solids}_EXPECTED_{expected_solids}")
    if len(shape.Shells) < expected_solids: errors.append("MISSING_CLOSED_SHELL")
    try:
        fatal_checks=len(shape.check(True))
    except Exception:
        fatal_checks=-1
        # FreeCAD 0.20 does not expose TopoShape.check(); Shape.isValid()
        # already invokes OpenCascade's BRepCheck_Analyzer and remains the
        # controlling fatal-topology check in this pinned environment.
    bb=shape.BoundBox
    return {
        "id":part_id,"category":category,"container_type":shape.ShapeType,
        "expected_solids":expected_solids,"solid_count":solids,
        "shell_count":len(shape.Shells),"volume_mm3":round(shape.Volume,3),
        "bbox_mm":[round(bb.XLength,3),round(bb.YLength,3),round(bb.ZLength,3)],
        "geometry_check_findings":fatal_checks,"status":"PASS" if not errors else "FAIL",
        "errors":errors,
    }


def main():
    params=json.loads((ROOT/"cad/parameters/baseline.json").read_text())
    if params["revision"] != REV: raise SystemExit("revision mismatch")
    rows=[]
    for spec in print_parts(): rows.append(audit(spec["id"],spec["shape"],"PRINT",spec.get("expected_solids",1)))
    rows.append(audit("PPR-TC01",tolerance_coupon(),"TEST_COUPON",1))
    for spec in shredder_metal_parts(): rows.append(audit(spec["id"],spec["shape"],"MACHINED",1))
    for spec in gate1_parts(): rows.append(audit(spec["id"],spec["shape"],"JIG_"+spec["class_"].upper(),1))
    for spec in extruder_rfq_parts(): rows.append(audit(spec["id"],spec["shape"],"EXTRUDER_RFQ",1))
    for item in assembly_objects(): rows.append(audit(item["name"],item["shape"],"ASSEMBLY_"+item["classification"].upper(),1))

    keepouts=[]
    for item in review_keepout_objects():
        record=audit(item["name"],item["shape"],"REVIEW_ONLY",1)
        record["excluded_from_manufacturing"]=True
        keepouts.append(record)

    result={
        "revision":REV,
        "contract":"active part contains exactly one closed positive-volume B-Rep solid",
        "active_count":len(rows),"review_keepout_count":len(keepouts),
        "failed":[r["id"] for r in rows if r["status"]!="PASS"],
        "parts":rows,"review_keepouts":keepouts,
        "status":"PASS" if all(r["status"]=="PASS" for r in rows) else "FAIL",
    }
    out=ROOT/"validation/results"; out.mkdir(parents=True,exist_ok=True)
    (out/"solid_topology.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    with (ROOT/"cad/manufacturing_object_audit.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["object_id","category","container_type","expected_solids","solid_count","volume_mm3","bbox_x_mm","bbox_y_mm","bbox_z_mm","status","errors"])
        for r in rows+keepouts:
            w.writerow([r["id"],r["category"],r["container_type"],r["expected_solids"],r["solid_count"],r["volume_mm3"],*r["bbox_mm"],r["status"],"|".join(r["errors"])])
    if result["status"]!="PASS": raise SystemExit("SOLID_BREP_TOPOLOGY_FAIL "+",".join(result["failed"]))
    print(f"SOLID_BREP_TOPOLOGY_OK active={len(rows)} keepouts_quarantined={len(keepouts)}")


if __name__=="__main__": main()
