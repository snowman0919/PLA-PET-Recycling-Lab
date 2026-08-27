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
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["assembly"]
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "full_assembly_skeleton.FCStd"))
    modules = [o for o in doc.Objects if o.Name.startswith("MOD") or o.Label.startswith("MOD-")]
    require(len(modules) == 11, f"expected 11 module envelopes, found {len(modules)}")
    shapes = [o.Shape for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
    bb = Part.makeCompound(shapes).BoundBox
    require(
        bb.XLength <= p["overall_length_mm"] + 0.001
        and bb.YLength <= p["overall_depth_mm"] + 0.001
        and bb.ZLength <= p["overall_height_mm"] + 0.001,
        "assembly exceeds baseline envelope",
    )
    dryer = doc.getObject("DryerFeeder").Shape.BoundBox
    extruder = doc.getObject("Extruder").Shape.BoundBox
    forming = doc.getObject("CoolingGaugePuller").Shape.BoundBox
    spooler = doc.getObject("Spooler").Shape.BoundBox
    classifier = doc.getObject("InputClassifier").Shape.BoundBox
    storage = doc.getObject("ClassificationStorage").Shape.BoundBox
    control = doc.getObject("ControlEnclosure").Shape.BoundBox
    require(classifier.XLength >= 320.0 and classifier.ZLength >= 220.0, "input-classifier proof envelope regressed")
    require(storage.XLength >= 320.0 and storage.YLength >= 320.0, "classification-storage proof envelope regressed")
    require(dryer.XLength >= 320.0 and dryer.ZLength >= 580.0, "dryer proof envelope regressed")
    require(extruder.XLength >= 850.0 and extruder.YLength >= 220.0, "extruder proof envelope regressed")
    require(forming.XLength >= 760.0 and forming.YLength >= 160.0, "forming-line proof envelope regressed")
    require(spooler.XLength >= 355.0 and spooler.ZLength >= 320.0, "spooler proof envelope regressed")
    require(control.XLength >= 300.0 and control.YLength >= 220.0, "control-enclosure proof envelope regressed")
    App.closeDocument(doc.Name)


def validate_exports() -> None:
    stems = (
        "tolerance_coupon",
        "classifier_gate_pair",
        "color_diverter_rotor",
        "input_classifier_proof",
        "classification_storage_proof",
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
        "dryer_metal_hopper",
        "dryer_heat_shield",
        "dryer_metering_auger",
        "dryer_auger_housing",
        "dryer_feeder_proof",
        "extruder_screw",
        "extruder_barrel",
        "extruder_breaker_plate",
        "extruder_die",
        "extruder_thrust_plate",
        "extruder_proof",
        "cooling_tunnel_segment",
        "diameter_gauge_enclosure",
        "diameter_gauge_optical_proof",
        "puller_roller_pair",
        "gauge_calibration_fixture",
        "forming_line_proof",
        "spooler_shaft",
        "spool_adapter_set",
        "traverse_carriage",
        "spooler_bearing_plate",
        "spooler_proof",
        "control_door_split",
        "control_backplate_partition",
        "control_enclosure_proof",
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
    dryer_dxf = (ROOT / "exports" / "dxf" / "dryer_base_plate.dxf").read_text(encoding="ascii")
    require("OUTLINE_T6" in dryer_dxf and dryer_dxf.rstrip().endswith("EOF"), "dryer base DXF is incomplete")
    extruder_dxf = (ROOT / "exports" / "dxf" / "extruder_thrust_plate.dxf").read_text(encoding="ascii")
    require("SHAFT_CLEARANCE_D20" in extruder_dxf and "FRAME_M8" in extruder_dxf and extruder_dxf.rstrip().endswith("EOF"), "extruder thrust plate DXF is incomplete")
    cooling_dxf = (ROOT / "exports" / "dxf" / "cooling_fan_plate.dxf").read_text(encoding="ascii")
    require("FAN_AIR_D68_8" in cooling_dxf and "FAN_M4" in cooling_dxf and cooling_dxf.rstrip().endswith("EOF"), "cooling fan plate DXF is incomplete")
    spooler_dxf = (ROOT / "exports" / "dxf" / "spooler_bearing_plate.dxf").read_text(encoding="ascii")
    require("BEARING_6001_D28" in spooler_dxf and spooler_dxf.rstrip().endswith("EOF"), "spooler bearing plate DXF is incomplete")
    classifier_dxf = (ROOT / "exports" / "dxf" / "classifier_gate_half.dxf").read_text(encoding="ascii")
    require("HINGE_M4" in classifier_dxf and classifier_dxf.rstrip().endswith("EOF"), "classifier gate DXF is incomplete")
    control_dxf = (ROOT / "exports" / "dxf" / "control_door_half.dxf").read_text(encoding="ascii")
    require("DOOR_M4" in control_dxf and control_dxf.rstrip().endswith("EOF"), "control door DXF is incomplete")


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


def validate_dryer_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "dryer_feeder_proof.FCStd"))
    expected = {
        "BaseAndLoadCells",
        "MetalHopper",
        "Insulation",
        "VentilatedShield",
        "Lid",
        "Agitator",
        "DoubleGate",
        "MeteringAuger",
        "AugerHousing",
        "DrivesAndDryAir",
    }
    require(expected == {o.Name for o in doc.Objects}, "dryer proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null dryer shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid dryer shape: {obj.Name}")
    auger = doc.getObject("MeteringAuger").Shape.BoundBox
    require(max(auger.XLength, auger.YLength, auger.ZLength) <= 210.0, "auger proof exceeds print bed envelope")
    require(doc.getObject("MetalHopper").Shape.BoundBox.ZLength > 400.0, "dryer hopper active height missing")
    support_gap = doc.getObject("BaseAndLoadCells").Shape.distToShape(doc.getObject("AugerHousing").Shape)[0]
    require(support_gap < 1e-7, f"dryer support frame does not reach auger housing: {support_gap:.3f} mm")
    App.closeDocument(doc.Name)


def validate_extruder_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "extruder_proof.FCStd"))
    expected = {
        "SupportFrame",
        "HelicalScrew",
        "BarrelAndFeedThroat",
        "FeedThroatCooling",
        "BreakerPlate",
        "FilamentDie",
        "HeaterClamps",
        "Insulation",
        "VentilatedShield",
        "ThrustBearing",
        "RadialBearings",
        "DriveAndCoupling",
        "PressureSafetyAndCatch",
    }
    require(expected == {o.Name for o in doc.Objects}, "extruder proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null extruder shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid extruder shape: {obj.Name}")
    require(doc.getObject("HelicalScrew").Shape.BoundBox.XLength > 570.0, "18 mm 24 L/D screw/tail length missing")
    require(doc.getObject("BarrelAndFeedThroat").Shape.BoundBox.XLength > 430.0, "extruder barrel length missing")
    for name in ("FilamentDie",):
        box = doc.getObject(name).Shape.BoundBox
        require(max(box.XLength, box.YLength, box.ZLength) <= 210.0, f"{name} exceeds print-bed envelope")
    thrust_plate = Part.read(str(ROOT / "exports" / "step" / "extruder_thrust_plate.step"))
    require(max(thrust_plate.BoundBox.XLength, thrust_plate.BoundBox.YLength, thrust_plate.BoundBox.ZLength) <= 210.0, "thrust plate exceeds 210 mm envelope")
    App.closeDocument(doc.Name)


def validate_forming_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "forming_line_proof.FCStd"))
    expected = {
        "Frame",
        "CoolingTunnel",
        "CoolingFans",
        "GaugeEnclosure",
        "GaugeOptics",
        "OpticalRayKeepouts",
        "PullerRollers",
        "OdometerAndSlipEncoder",
        "PullerGuardAndSupport",
        "FilamentReference",
    }
    require(expected == {o.Name for o in doc.Objects}, "forming-line proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null forming-line shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid forming-line shape: {obj.Name}")
    require(doc.getObject("CoolingTunnel").Shape.BoundBox.XLength >= 440.0, "cooling tunnel length missing")
    require(doc.getObject("Frame").Shape.BoundBox.XLength >= 760.0, "forming line rail length missing")
    for stem in ("cooling_tunnel_segment", "diameter_gauge_enclosure", "puller_roller_pair", "gauge_calibration_fixture"):
        shape = Part.read(str(ROOT / "exports" / "step" / f"{stem}.step"))
        require(max(shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength) <= 210.0, f"{stem} exceeds print-bed envelope")
    App.closeDocument(doc.Name)


def validate_spooler_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "spooler_proof.FCStd"))
    expected = {
        "BaseAndMetalFrame",
        "SpoolShaft",
        "SpoolBearings",
        "LoadedSpoolReference",
        "InstalledAdapters",
        "Dancer",
        "DancerSweepKeepout",
        "Traverse",
        "DriveAndTorqueGuard",
        "SpoolGuard",
    }
    require(expected == {o.Name for o in doc.Objects}, "spooler proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null spooler shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid spooler shape: {obj.Name}")
    spool = doc.getObject("LoadedSpoolReference").Shape.BoundBox
    require(spool.YLength >= 73.0 and max(spool.XLength, spool.ZLength) >= 199.9, "full spool reference regressed")
    for stem in ("spool_adapter_set", "traverse_carriage"):
        shape = Part.read(str(ROOT / "exports" / "step" / f"{stem}.step"))
        require(max(shape.BoundBox.XLength, shape.BoundBox.YLength, shape.BoundBox.ZLength) <= 210.0, f"{stem} exceeds print-bed envelope")
    App.closeDocument(doc.Name)


def validate_classifier_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "input_classifier_proof.FCStd"))
    expected = {
        "FrameAndLightShield",
        "UpperClosedGate",
        "LowerOpenGate",
        "CameraLighting",
        "BottleReference",
        "RejectFlapAndChute",
    }
    require(expected == {o.Name for o in doc.Objects}, "input-classifier proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null classifier shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid classifier shape: {obj.Name}")
    App.closeDocument(doc.Name)


def validate_control_enclosure_assembly() -> None:
    doc = App.openDocument(str(ROOT / "cad" / "generation" / "fcstd" / "control_enclosure_proof.FCStd"))
    expected = {
        "GroundedShell",
        "BackplatePartitionDIN",
        "HighCurrentDevices",
        "LogicDevices",
        "SplitDoor",
        "FaceControls",
        "CableManagementPE",
    }
    require(expected == {o.Name for o in doc.Objects}, "control-enclosure proof object set differs")
    for obj in doc.Objects:
        require(hasattr(obj, "Shape") and not obj.Shape.isNull(), f"null control-enclosure shape: {obj.Name}")
        require(obj.Shape.isValid(), f"invalid control-enclosure shape: {obj.Name}")
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
    validate_dryer_assembly()
    validate_extruder_assembly()
    validate_forming_assembly()
    validate_spooler_assembly()
    validate_classifier_assembly()
    validate_control_enclosure_assembly()
    validate_stage1_envelope()
    print("CAD_VALIDATION_OK")


if __name__ == "__main__":
    main()
