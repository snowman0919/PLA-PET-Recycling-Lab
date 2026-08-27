#!/usr/bin/env python3
"""Decision-relevant validation for baseline FreeCAD outputs."""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App
import Mesh
import Part


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_coupon() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "tolerance_coupon.FCStd"))
    base = doc.getObject("CouponBase")
    comb = doc.getObject("CouponComb")
    require(base is not None and comb is not None, "coupon objects missing")
    require(base.Shape.common(comb.Shape).Volume < 1e-6, "coupon base and comb intersect")
    distance = base.Shape.distToShape(comb.Shape)[0]
    require(distance >= 4.999, f"coupon print-plate separation {distance:.3f} mm < 5 mm")
    for obj in (base, comb):
        bb = obj.Shape.BoundBox
        require(max(bb.XLength, bb.YLength, bb.ZLength) <= 210.0, f"{obj.Name} exceeds print volume")
    App.closeDocument(doc.Name)


def validate_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "full_assembly_skeleton.FCStd"))
    modules = [o for o in doc.Objects if o.Name.startswith("MOD") or o.Label.startswith("MOD-")]
    require(len(modules) == 10, f"expected 10 module envelopes, found {len(modules)}")
    shapes = [o.Shape for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
    bb = Part.makeCompound(shapes).BoundBox
    require(bb.XLength <= 1300.001 and bb.YLength <= 400.001 and bb.ZLength <= 720.001, "assembly exceeds baseline envelope")
    App.closeDocument(doc.Name)


def validate_exports() -> None:
    for stem in ("tolerance_coupon", "full_assembly_skeleton"):
        step_shape = Part.read(str(ROOT / "exports" / "step" / f"{stem}.step"))
        require(not step_shape.isNull(), f"{stem} STEP is null")
        mesh = Mesh.Mesh(str(ROOT / "exports" / "stl" / f"{stem}.stl"))
        require(mesh.CountFacets > 0, f"{stem} STL has no facets")


def validate_stage1_envelope() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["stage1"]
    tip_root_clearance = p["shaft_center_distance_mm"] - (
        p["cutter_outer_diameter_mm"] + p["cutter_root_diameter_mm"]
    ) / 2
    radial_overlap = p["cutter_outer_diameter_mm"] - p["shaft_center_distance_mm"]
    require(tip_root_clearance > 0, "Stage 1 tip collides with opposite root envelope")
    require(radial_overlap > 0, "Stage 1 cutters do not overlap radially")
    print(f"stage1 tip-root envelope clearance={tip_root_clearance:.3f} mm, radial overlap={radial_overlap:.3f} mm")


def main() -> None:
    validate_coupon()
    validate_assembly()
    validate_exports()
    validate_stage1_envelope()
    print("CAD_VALIDATION_OK")


if __name__ == "__main__":
    main()
