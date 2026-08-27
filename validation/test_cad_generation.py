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
    stems = (
        "tolerance_coupon",
        "full_assembly_skeleton",
        "stage1_cutter_disc",
        "stage1_bearing_plate",
        "stage1_cutter_stack",
        "stage1_shredder_proof",
        "stage2_rotor",
        "stage2_bed_knife",
        "stage2_bearing_plate",
        "stage2_shredder_proof",
        "stage3_rotor",
        "stage3_stator",
        "stage3_bearing_plate",
        "stage3_screen_4mm",
        "stage3_screen_5mm",
        "stage3_screen_6mm",
        "stage3_granulator_proof",
        "sorter_base_plate",
        "sorter_top_screen_6mm",
        "sorter_bottom_screen_3mm",
        "sorter_service_clamp",
        "vibratory_sorter_proof",
    )
    for stem in stems:
        step_shape = Part.read(str(ROOT / "exports" / "step" / f"{stem}.step"))
        require(not step_shape.isNull(), f"{stem} STEP is null")
        require(step_shape.isValid(), f"{stem} STEP is invalid")
        mesh = Mesh.Mesh(str(ROOT / "exports" / "stl" / f"{stem}.stl"))
        require(mesh.CountFacets > 0, f"{stem} STL has no facets")
    dxf = (ROOT / "exports" / "dxf" / "stage1_bearing_plate.dxf").read_text(encoding="ascii")
    require("CBORE_DEPTH_11_8" in dxf and dxf.rstrip().endswith("EOF"), "Stage 1 plate DXF is incomplete")
    dxf2 = (ROOT / "exports" / "dxf" / "stage2_bearing_plate.dxf").read_text(encoding="ascii")
    require("CBORE_DEPTH_11_8" in dxf2 and dxf2.rstrip().endswith("EOF"), "Stage 2 plate DXF is incomplete")
    dxf3 = (ROOT / "exports" / "dxf" / "stage3_bearing_plate.dxf").read_text(encoding="ascii")
    require("CBORE_DEPTH_11_8" in dxf3 and dxf3.rstrip().endswith("EOF"), "Stage 3 plate DXF is incomplete")
    sorter_dxf = (ROOT / "exports" / "dxf" / "sorter_base_plate.dxf").read_text(encoding="ascii")
    require("ISOLATOR_M6" in sorter_dxf and sorter_dxf.rstrip().endswith("EOF"), "sorter base DXF is incomplete")


def validate_stage1_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "stage1_shredder_proof.FCStd"))
    counts = {
        "plates": len([o for o in doc.Objects if o.Name.endswith("Plate")]),
        "bearings": len([o for o in doc.Objects if o.Name.startswith("Bearing")]),
        "retainers": len([o for o in doc.Objects if o.Name.endswith("Retainer")]),
        "timing_envelopes": len([o for o in doc.Objects if o.Name.startswith("TimingEnvelope")]),
    }
    require(counts == {"plates": 3, "bearings": 6, "retainers": 3, "timing_envelopes": 2}, f"Stage 1 object counts differ: {counts}")
    require(doc.getObject("TimingSupportPlate") is not None, "timing support plate missing")
    require(doc.getObject("InputCouplingEnvelope") is not None, "input coupling envelope missing")
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            require(obj.Shape.isValid(), f"invalid Stage 1 shape: {obj.Name}")
    App.closeDocument(doc.Name)


def validate_stage2_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "stage2_shredder_proof.FCStd"))
    expected = {
        "Shaft",
        "Rotor",
        "BedKnife",
        "BedKnifeCarrier",
        "LeftPlate",
        "RightPlate",
        "LeftBearing",
        "RightBearing",
        "LeftRetainer",
        "RightRetainer",
    }
    require(expected == {o.Name for o in doc.Objects}, "Stage 2 proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null Stage 2 shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid Stage 2 shape: {obj.Name}")
    App.closeDocument(doc.Name)


def validate_stage3_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "stage3_granulator_proof.FCStd"))
    expected = {
        "Shaft",
        "Rotor",
        "Stator",
        "StatorCarrier",
        "BaselineScreen",
        "LeftPlate",
        "RightPlate",
        "LeftBearing",
        "RightBearing",
        "LeftRetainer",
        "RightRetainer",
    }
    require(expected == {o.Name for o in doc.Objects}, "Stage 3 proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null Stage 3 shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid Stage 3 shape: {obj.Name}")
    App.closeDocument(doc.Name)


def validate_sorter_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "vibratory_sorter_proof.FCStd"))
    expected = {
        "BasePlate",
        "Isolators",
        "TrayFrame",
        "TopScreen6",
        "BottomScreen3",
        "ScrewClamps",
        "MotorBracket",
        "DriveMotor",
        "EccentricMass",
        "OversizeAndAcceptableChutes",
        "FinesBin",
    }
    require(expected == {o.Name for o in doc.Objects}, "sorter proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null sorter shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid sorter shape: {obj.Name}")
    top = doc.getObject("TopScreen6").Shape.BoundBox
    bottom = doc.getObject("BottomScreen3").Shape.BoundBox
    require(top.Center.z - bottom.Center.z >= 30.0, "sorter deck separation is too small")
    clamp = Part.read(str(ROOT / "exports" / "step" / "sorter_service_clamp.step"))
    require(max(clamp.BoundBox.XLength, clamp.BoundBox.YLength, clamp.BoundBox.ZLength) <= 210.0, "service clamp exceeds print bed")
    App.closeDocument(doc.Name)


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
    validate_stage1_assembly()
    validate_stage2_assembly()
    validate_stage3_assembly()
    validate_sorter_assembly()
    validate_stage1_envelope()
    print("CAD_VALIDATION_OK")


if __name__ == "__main__":
    main()
