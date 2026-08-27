#!/usr/bin/env python3
"""Decision-relevant geometry checks for the two-tower FreeCAD assembly."""

from __future__ import annotations

import json
from pathlib import Path

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[1]
TOL = 1e-6


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, label: str, tolerance: float = TOL) -> None:
    require(abs(actual - expected) <= tolerance, f"{label}: {actual:.6f} != {expected:.6f}")


def category(obj) -> str:
    return getattr(obj, "Category", "")


def tower(obj) -> str:
    return getattr(obj, "Tower", "")


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["assembly"]
    contract = json.loads((ROOT / "simulation" / "architecture" / "two_tower_contract.json").read_text())
    path = ROOT / "cad" / "generation" / "fcstd" / "full_assembly_skeleton.FCStd"
    doc = App.openDocument(str(path))

    physical = [obj for obj in doc.Objects if category(obj) != "REFERENCE_VOLUME_NOT_EXPORTED"]
    shapes = [obj.Shape for obj in physical if hasattr(obj, "Shape") and not obj.Shape.isNull()]
    require(all(shape.isValid() for shape in shapes), "assembly contains an invalid shape")
    overall = Part.makeCompound(shapes).BoundBox
    close(overall.XLength, p["overall_length_mm"], "overall X")
    close(overall.YLength, p["overall_depth_mm"], "overall Y")
    close(overall.ZLength, p["overall_height_mm"], "overall Z")

    tower_a_shapes = [obj.Shape for obj in physical if tower(obj) == "TowerA"]
    tower_b_shapes = [obj.Shape for obj in physical if tower(obj) == "TowerB"]
    a_box = Part.makeCompound(tower_a_shapes).BoundBox
    b_box = Part.makeCompound(tower_b_shapes).BoundBox
    close(a_box.XMin, p["tower_a_origin_x_mm"], "Tower A origin")
    close(a_box.XMax, p["tower_a_origin_x_mm"] + p["tower_a_width_mm"], "Tower A boundary")
    close(b_box.XMin, p["tower_b_origin_x_mm"], "Tower B origin")
    close(b_box.XMin - a_box.XMax, p["tower_separation_mm"], "tower separation")

    anchors = [obj for obj in doc.Objects if category(obj) == "ANCHOR"]
    require(len(anchors) == 8, f"expected 8 anchor feet, found {len(anchors)}")
    anchor_evidence = {}
    for tower_name, expected_x, expected_y in (
        ("TowerA", p["tower_a_anchor_spacing_x_mm"], p["tower_a_anchor_spacing_y_mm"]),
        ("TowerB", p["tower_b_anchor_spacing_x_mm"], p["tower_b_anchor_spacing_y_mm"]),
    ):
        feet = [obj for obj in anchors if tower(obj) == tower_name]
        require(len(feet) == 4, f"{tower_name} does not have four anchors")
        centers = [(obj.Shape.BoundBox.Center.x, obj.Shape.BoundBox.Center.y) for obj in feet]
        close(max(x for x, _ in centers) - min(x for x, _ in centers), expected_x, f"{tower_name} anchor X")
        close(max(y for _, y in centers) - min(y for _, y in centers), expected_y, f"{tower_name} anchor Y")
        for foot in feet:
            close(foot.Shape.BoundBox.ZLength, 8.0, f"{foot.Name} plate thickness")
            require(foot.Shape.Volume < 80 * 80 * 8, f"{foot.Name} anchor hole missing")
        anchor_evidence[tower_name] = {"centers_mm": [[round(x, 3), round(y, 3)] for x, y in centers]}

    modules = [obj for obj in doc.Objects if category(obj) == "MODULE_ENVELOPE"]
    require(len(modules) == 11, f"expected 11 module envelopes, found {len(modules)}")
    order = [
        "ClassificationStorage", "VibratorySorter", "GranulatorStage3",
        "ShredderStage2", "ShredderStage1", "InputClassifier",
    ]
    z_centers = [doc.getObject(name).Shape.BoundBox.Center.z for name in order]
    require(z_centers == sorted(z_centers), "Tower A module order is not bottom-to-top")
    require(doc.getObject("InputClassifier").Shape.BoundBox.ZMax <= p["maximum_input_lip_height_mm"],
            "input lip exceeds architecture contract")

    bin_obj = doc.getObject("ClassificationStorage")
    gross = doc.getObject("BatchBinGrossCavityReference")
    usable = doc.getObject("BatchBinUsableVolumeReference")
    close(gross.Shape.Volume / 1_000_000, p["batch_bin_gross_volume_l"], "batch gross L")
    close(usable.Shape.Volume / 1_000_000, p["batch_bin_usable_volume_l"], "batch usable L")
    close(float(bin_obj.GrossCavity) / 1_000_000, p["batch_bin_gross_volume_l"], "batch property gross L")
    close(float(bin_obj.UsableVolume) / 1_000_000, p["batch_bin_usable_volume_l"], "batch property usable L")
    require(bin_obj.Shape.common(gross.Shape).Volume < TOL, "gross cavity is not removed from the batch bin")

    chute_pairs = (
        ("A_Chute_Input_Stage1", "InputClassifier", "ShredderStage1"),
        ("A_Chute_Stage1_Stage2", "ShredderStage1", "ShredderStage2"),
        ("A_Chute_Stage2_Stage3", "ShredderStage2", "GranulatorStage3"),
        ("A_Chute_Stage3_Sorter", "GranulatorStage3", "VibratorySorter"),
        ("A_Chute_Sorter_Bin", "VibratorySorter", "ClassificationStorage"),
    )
    for chute_name, upstream, downstream in chute_pairs:
        chute = doc.getObject(chute_name)
        require(chute.Shape.distToShape(doc.getObject(upstream).Shape)[0] <= TOL,
                f"{chute_name} does not meet {upstream}")
        require(chute.Shape.distToShape(doc.getObject(downstream).Shape)[0] <= TOL,
                f"{chute_name} does not meet {downstream}")

    dock = doc.getObject("BatchDockReceiver")
    require(dock.Shape.distToShape(doc.getObject("DryerFeeder").Shape)[0] <= TOL,
            "batch dock does not meet dryer")
    require(len(dock.Shape.Solids) == 1, "batch dock key/clamps/throat are not one connected review body")

    longitudinal = [obj for obj in doc.Objects if obj.Name.startswith("TowerB_ServiceRail_")]
    require(len(longitudinal) == 2, "two longitudinal service rails required")
    rail_start = p["tower_b_origin_x_mm"] + p["tower_b_width_mm"]
    rail_end = rail_start + p["service_rail_extension_mm"]
    for rail in longitudinal:
        close(rail.Shape.BoundBox.XMin, rail_start, f"{rail.Name} start")
        close(rail.Shape.BoundBox.XMax, rail_end, f"{rail.Name} end")
        close(rail.Shape.BoundBox.XLength, p["service_rail_extension_mm"], f"{rail.Name} length")
        require(rail.Shape.Volume < rail.Shape.BoundBox.XLength * 20 * 20,
                f"{rail.Name} is a solid envelope rather than a bored profile")
    forming = doc.getObject("CoolingGaugePuller").Shape.BoundBox
    close(forming.XMin, rail_start, "forming line start")
    close(forming.XLength, p["service_rail_extension_mm"], "forming line length")

    energy_zones = {obj.Name: tower(obj) for obj in doc.Objects if category(obj) == "SAFETY_ZONE"}
    require(energy_zones == {
        "TowerA_MotionContactorZone": "TowerA",
        "TowerB_HeaterDriveZone": "TowerB",
    }, f"energy zone split differs: {energy_zones}")

    contract_a = contract["tower_a"]["rack_envelope_mm"]
    contract_b = contract["tower_b"]["rack_envelope_mm"]
    require(contract_a == {"width": 600.0, "depth": 600.0, "height": 1350.0}, "Tower A contract drift")
    require(contract_b == {"width": 900.0, "depth": 600.0, "height": 1150.0}, "Tower B contract drift")

    evidence = {
        "status": "VIRTUAL_GEOMETRY_PASS_PHYSICAL_GATES_OPEN",
        "source": "cad/generation/fcstd/full_assembly_skeleton.FCStd",
        "overall_mm": [overall.XLength, overall.YLength, overall.ZLength],
        "tower_separation_mm": b_box.XMin - a_box.XMax,
        "anchor_patterns": anchor_evidence,
        "batch_volume_l": {"gross": gross.Shape.Volume / 1_000_000, "usable": usable.Shape.Volume / 1_000_000},
        "service_rail_mm": {"start_x": rail_start, "end_x": rail_end, "length": rail_end - rail_start},
        "module_count": len(modules),
        "physical_gates_open": [
            "anchor substrate and pullout test",
            "measured mass and centre of gravity",
            "operator reach and refill handling",
            "profile joint and shelf load test",
            "vibration, chute cleaning and service-path test",
        ],
    }
    output = ROOT / "simulation" / "architecture" / "two_tower_geometry.json"
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    App.closeDocument(doc.Name)
    print("TWO_TOWER_GEOMETRY_VALIDATION_OK")


if __name__ == "__main__":
    main()
