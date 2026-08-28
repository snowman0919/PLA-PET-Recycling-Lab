"""Generate the quantified two-tower architecture review assembly.

Module bodies remain conservative keep-out envelopes.  Frames, shelves,
anchors, transfer chutes and the batch dock are explicit review geometry so
that placement and interface tests do not depend on a drawing annotation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

COMMON = Path(__file__).resolve().parents[1] / "common"
sys.path.insert(0, str(COMMON))
from project import ROOT, add_feature, export_document, load_parameters  # noqa: E402


def feature(doc, objects, name, label, part_id, shape, material, category, tower):
    obj = add_feature(doc, name, label, shape, part_id, material)
    obj.addProperty("App::PropertyString", "Category", "Architecture")
    obj.Category = category
    obj.addProperty("App::PropertyString", "Tower", "Architecture")
    obj.Tower = tower
    objects.append(obj)
    return obj


def box(doc, objects, name, label, part_id, xyz, size, material, category, tower):
    return feature(
        doc, objects, name, label, part_id,
        Part.makeBox(*size, App.Vector(*xyz)), material, category, tower,
    )


def profile_shape(xyz, length, axis, section):
    """Generic four-face slotted extrusion with an axial centre bore."""
    x, y, z = xyz
    slot_width = 6.0 if section >= 40 else 4.0
    slot_depth = 4.0 if section >= 40 else 3.0
    if axis == "x":
        outer = Part.makeBox(length, section, section, App.Vector(x, y, z))
        bore = Part.makeCylinder(3.0, length + 0.2, App.Vector(x - 0.1, y + section / 2, z + section / 2), App.Vector(1, 0, 0))
        grooves = (
            Part.makeBox(length + 0.2, slot_depth + 0.1, slot_width, App.Vector(x - 0.1, y - 0.05, z + (section - slot_width) / 2)),
            Part.makeBox(length + 0.2, slot_depth + 0.1, slot_width, App.Vector(x - 0.1, y + section - slot_depth, z + (section - slot_width) / 2)),
            Part.makeBox(length + 0.2, slot_width, slot_depth + 0.1, App.Vector(x - 0.1, y + (section - slot_width) / 2, z - 0.05)),
            Part.makeBox(length + 0.2, slot_width, slot_depth + 0.1, App.Vector(x - 0.1, y + (section - slot_width) / 2, z + section - slot_depth)),
        )
    elif axis == "y":
        outer = Part.makeBox(section, length, section, App.Vector(x, y, z))
        bore = Part.makeCylinder(3.0, length + 0.2, App.Vector(x + section / 2, y - 0.1, z + section / 2), App.Vector(0, 1, 0))
        grooves = (
            Part.makeBox(slot_depth + 0.1, length + 0.2, slot_width, App.Vector(x - 0.05, y - 0.1, z + (section - slot_width) / 2)),
            Part.makeBox(slot_depth + 0.1, length + 0.2, slot_width, App.Vector(x + section - slot_depth, y - 0.1, z + (section - slot_width) / 2)),
            Part.makeBox(slot_width, length + 0.2, slot_depth + 0.1, App.Vector(x + (section - slot_width) / 2, y - 0.1, z - 0.05)),
            Part.makeBox(slot_width, length + 0.2, slot_depth + 0.1, App.Vector(x + (section - slot_width) / 2, y - 0.1, z + section - slot_depth)),
        )
    elif axis == "z":
        outer = Part.makeBox(section, section, length, App.Vector(x, y, z))
        bore = Part.makeCylinder(3.0, length + 0.2, App.Vector(x + section / 2, y + section / 2, z - 0.1), App.Vector(0, 0, 1))
        grooves = (
            Part.makeBox(slot_depth + 0.1, slot_width, length + 0.2, App.Vector(x - 0.05, y + (section - slot_width) / 2, z - 0.1)),
            Part.makeBox(slot_depth + 0.1, slot_width, length + 0.2, App.Vector(x + section - slot_depth, y + (section - slot_width) / 2, z - 0.1)),
            Part.makeBox(slot_width, slot_depth + 0.1, length + 0.2, App.Vector(x + (section - slot_width) / 2, y - 0.05, z - 0.1)),
            Part.makeBox(slot_width, slot_depth + 0.1, length + 0.2, App.Vector(x + (section - slot_width) / 2, y + section - slot_depth, z - 0.1)),
        )
    else:
        raise ValueError(axis)
    return outer.cut(Part.makeCompound((bore, *grooves)))


def profile(doc, objects, name, xyz, length, axis, section, tower, category="FRAME"):
    designation = f"{int(section)}{int(section)}"
    return feature(
        doc, objects, name, name.replace("_", "-"), name.replace("_", "-"),
        profile_shape(xyz, length, axis, section),
        f"Aluminum profile {designation}; generic four-face slots and centre bore",
        category, tower,
    )


def anchor_foot(doc, objects, name, x, y, tower, hole_diameter):
    plate = Part.makeBox(80, 80, 8, App.Vector(x, y, 0))
    hole = Part.makeCylinder(hole_diameter / 2, 10, App.Vector(x + 40, y + 40, -1))
    return feature(
        doc, objects, name, name.replace("_", "-"), name.replace("_", "-"),
        plate.cut(hole), "Steel anchor foot, pullout proof pending", "ANCHOR", tower,
    )


def add_rack(doc, objects, tower, origin_x, width, depth, height, shelf_z, p):
    post_x = (origin_x + 20, origin_x + width - 60)
    post_y = (20, depth - 60)
    for i, (x, y) in enumerate((
        (post_x[0], post_y[0]), (post_x[1], post_y[0]),
        (post_x[0], post_y[1]), (post_x[1], post_y[1]),
    ), 1):
        profile(doc, objects, f"{tower}_Post_{i}", (x, y, 0), height, "z", 40, tower)

    rail_x_length = width - 40
    rail_y_length = depth - 40
    for level, z in (("Base", 0), ("Top", height - 40)):
        for side, y in (("Front", 20), ("Rear", depth - 60)):
            profile(doc, objects, f"{tower}_{level}_{side}_X", (origin_x + 20, y, z), rail_x_length, "x", 40, tower)
        for side, x in (("Left", origin_x + 20), ("Right", origin_x + width - 60)):
            profile(doc, objects, f"{tower}_{level}_{side}_Y", (x, 20, z), rail_y_length, "y", 40, tower)

    for index, z in enumerate(shelf_z, 1):
        for y in (70, depth - 90):
            profile(doc, objects, f"{tower}_Shelf_{index}_{int(y)}", (origin_x + 40, y, z), width - 80, "x", 20, tower, "SHELF")

    spacing_x = p[f"tower_{tower[-1].lower()}_anchor_spacing_x_mm"]
    spacing_y = p[f"tower_{tower[-1].lower()}_anchor_spacing_y_mm"]
    for index, (x, y) in enumerate((
        (origin_x, 0), (origin_x + spacing_x, 0),
        (origin_x, spacing_y), (origin_x + spacing_x, spacing_y),
    ), 1):
        anchor_foot(doc, objects, f"{tower}_AnchorFoot_{index}", x, y, tower, p["anchor_hole_diameter_mm"])


def build():
    parameters = load_parameters()
    p = parameters["assembly"]
    doc = App.newDocument("FullAssemblyTwoTower")
    objects = []

    add_rack(
        doc, objects, "TowerA", p["tower_a_origin_x_mm"], p["tower_a_width_mm"],
        p["tower_a_depth_mm"], p["tower_a_height_mm"],
        (210, 420, 630, 840, 1050), p,
    )
    add_rack(
        doc, objects, "TowerB", p["tower_b_origin_x_mm"], p["tower_b_width_mm"],
        p["tower_b_depth_mm"], p["tower_b_height_mm"],
        (330, 470, 1090), p,
    )

    modules = [
        ("ClassificationStorage", "MOD-BIN-DIVERTER", "TowerA", (140, 140, 40), (320, 320, 165), "Sealed removable 8 L gross batch bin envelope"),
        ("VibratorySorter", "MOD-SORTER", "TowerA", (160, 200, 245), (280, 200, 95), "Proof module envelope"),
        ("GranulatorStage3", "MOD-SHRED-3", "TowerA", (195, 235, 455), (210, 130, 95), "Proof module envelope"),
        ("ShredderStage2", "MOD-SHRED-2", "TowerA", (185, 230, 665), (230, 140, 95), "Proof module envelope"),
        ("ShredderStage1", "MOD-SHRED-1", "TowerA", (170, 220, 875), (260, 160, 105), "Proof module envelope"),
        ("InputClassifier", "MOD-INPUT", "TowerA", (140, 190, 1070), (320, 220, 220), "Proof module envelope"),
        ("Extruder", "MOD-EXTRUDER", "TowerB", (850, 300, 80), (850, 220, 240), "Guarded hot-line proof envelope"),
        ("DryerFeeder", "MOD-DRYER", "TowerB", (900, 20, 500), (320, 270, 580), "Insulated dryer proof envelope"),
        ("ControlEnclosure", "MOD-CONTROL", "TowerB", (1240, 20, 80), (500, 200, 400), "BOM-traceable grounded control enclosure envelope"),
        ("CoolingGaugePuller", "MOD-COOL-GAUGE-PULLER", "TowerB", (1750, 320, 100), (760, 160, 180), "Straight forming-line proof envelope"),
        ("Spooler", "MOD-SPOOLER", "TowerB", (2110, 20, 40), (355, 240, 320), "Offset spooler proof envelope"),
    ]
    placements = {}
    for name, part_id, tower, xyz, size, material in modules:
        if name == "ClassificationStorage":
            # 250 x 200 x 160 mm = 8.0 L gross cavity.  A 120 mm fill-height
            # reference gives the contracted 6.0 L usable volume.
            outer = Part.makeBox(320, 320, 165, App.Vector(*xyz))
            cavity_origin = (xyz[0] + 35, xyz[1] + 60, xyz[2] + 5)
            gross_cavity = Part.makeBox(250, 200, 160, App.Vector(*cavity_origin))
            obj = feature(doc, objects, name, part_id, part_id, outer.cut(gross_cavity), material,
                          "MODULE_ENVELOPE", tower)
            obj.addProperty("App::PropertyVolume", "GrossCavity", "BatchInterface")
            obj.GrossCavity = 8_000_000
            obj.addProperty("App::PropertyVolume", "UsableVolume", "BatchInterface")
            obj.UsableVolume = 6_000_000
            for ref_name, ref_shape in (
                ("BatchBinGrossCavityReference", gross_cavity),
                ("BatchBinUsableVolumeReference", Part.makeBox(250, 200, 120, App.Vector(*cavity_origin))),
            ):
                ref = add_feature(doc, ref_name, f"REFERENCE-{ref_name}", ref_shape, "REFERENCE-NOT-FABRICATED", "Reference volume")
                ref.addProperty("App::PropertyString", "Category", "Architecture")
                ref.Category = "REFERENCE_VOLUME_NOT_EXPORTED"
                ref.addProperty("App::PropertyString", "Tower", "Architecture")
                ref.Tower = tower
        else:
            box(doc, objects, name, part_id, part_id, xyz, size, material, "MODULE_ENVELOPE", tower)
        placements[name] = {"tower": tower, "origin_mm": list(xyz), "size_mm": list(size)}

    # Gravity-flow connections are removable metal boots with visible gaps from
    # the cutter guards.  They are review solids, not flow-qualified chutes.
    chute_specs = (
        ("A_Chute_Input_Stage1", (250, 265, 980), (100, 70, 90)),
        ("A_Chute_Stage1_Stage2", (255, 265, 760), (90, 70, 115)),
        ("A_Chute_Stage2_Stage3", (260, 265, 550), (80, 70, 115)),
        ("A_Chute_Stage3_Sorter", (260, 265, 340), (80, 70, 115)),
        ("A_Chute_Sorter_Bin", (160, 260, 200), (280, 80, 45)),
    )
    for name, xyz, size in chute_specs:
        box(doc, objects, name, name.replace("_", "-"), name.replace("_", "-"), xyz, size,
            "Grounded stainless removable chute envelope", "TRANSFER_CHUTE", "TowerA")

    # Tower B batch receiver: asymmetric key, twin clamp bosses and sealed
    # metal throat are explicit so docking cannot be inferred from prose only.
    receiver = Part.makeBox(260, 220, 12, App.Vector(930, 40, 1080))
    throat = Part.makeBox(120, 100, 60, App.Vector(1000, 100, 1092))
    key = Part.makeBox(28, 65, 24, App.Vector(930, 40, 1092))
    clamps = Part.makeCylinder(10, 35, App.Vector(980, 40, 1092), App.Vector(0, 0, 1)).fuse(
        Part.makeCylinder(10, 35, App.Vector(1140, 40, 1092), App.Vector(0, 0, 1))
    )
    feature(doc, objects, "BatchDockReceiver", "IF-BATCH-DOCK", "IF-BATCH-DOCK",
            receiver.fuse(throat).fuse(key).fuse(clamps), "Grounded stainless batch dock",
            "BATCH_DOCK", "TowerB")

    # The straight 2040 rail begins at the Tower B rack boundary and terminates
    # exactly 760 mm later.  Cross ties keep the two rails in one review plane.
    rail_start = p["tower_b_origin_x_mm"] + p["tower_b_width_mm"]
    rail_length = p["service_rail_extension_mm"]
    for y in (300, 500):
        profile(doc, objects, f"TowerB_ServiceRail_{y}", (rail_start, y, 60), rail_length, "x", 20, "TowerB", "SERVICE_RAIL")
    for index, x in enumerate((rail_start, rail_start + rail_length / 2, rail_start + rail_length - 20), 1):
        profile(doc, objects, f"TowerB_RailCrossTie_{index}", (x, 300, 60), 220, "y", 20, "TowerB", "SERVICE_RAIL")

    # Physical energy boundaries used by the wiring/cable review.  These are
    # enclosure/contact-zone envelopes; ratings still come from the BOM gate.
    box(doc, objects, "TowerA_MotionContactorZone", "SAFE-A-MOTION", "SAFE-A-MOTION",
        (30, 470, 120), (120, 80, 150), "Grounded steel enclosure envelope", "SAFETY_ZONE", "TowerA")
    box(doc, objects, "TowerB_HeaterDriveZone", "SAFE-B-HEATER-DRIVE", "SAFE-B-HEATER-DRIVE",
        (1240, 20, 80), (240, 200, 400), "Left-side high-current/safety zone within control enclosure", "SAFETY_ZONE", "TowerB")

    outputs = export_document(doc, "full_assembly_skeleton", objects)
    compound = Part.makeCompound([obj.Shape for obj in objects])
    bb = compound.BoundBox
    report = {
        "revision": parameters["revision"],
        "architecture": "TWO_TOWER_CONTRACT",
        "overall_mm": {"x": round(bb.XLength, 1), "y": round(bb.YLength, 1), "z": round(bb.ZLength, 1)},
        "contract_envelope_mm": {
            "x": p["overall_length_mm"], "y": p["overall_depth_mm"], "z": p["overall_height_mm"],
        },
        "tower_separation_mm": p["tower_separation_mm"],
        "service_rail": {"start_x_mm": rail_start, "length_mm": rail_length, "straight": True},
        "anchor_patterns_mm": {
            "tower_a": [p["tower_a_anchor_spacing_x_mm"], p["tower_a_anchor_spacing_y_mm"]],
            "tower_b": [p["tower_b_anchor_spacing_x_mm"], p["tower_b_anchor_spacing_y_mm"]],
        },
        "module_count": len(modules),
        "module_placements": placements,
        "review_object_count": len(objects),
        "notes": [
            "The former 2295 x 520 x 720 mm linear workbench skeleton is obsolete.",
            "Module solids are conservative keep-out envelopes; frame, anchor, chute, dock and rail objects are explicit architecture-review geometry.",
            "4040/2040 solids include generic four-face slot mouths and an axial centre bore but omit manufacturer-specific undercuts and joint hardware.",
            "All four anchor feet per tower are candidates; substrate, edge distance and 1 kN per-point pullout remain physical gates.",
            "No safety, cleaning, reach, vibration or fabrication acceptance may be inferred from this virtual assembly.",
        ],
        "outputs": outputs,
    }
    report_path = ROOT / "validation" / "visual_review" / "full_assembly_skeleton.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
