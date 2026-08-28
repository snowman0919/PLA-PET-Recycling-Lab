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
        (190, 400, 650), p,
    )
    add_rack(
        doc, objects, "TowerB", p["tower_b_origin_x_mm"], p["tower_b_width_mm"],
        p["tower_b_depth_mm"], p["tower_b_height_mm"],
        (340, 460, 900), p,
    )

    modules = [
        ("BatchBin", "MOD-BATCH-BIN", "TowerA", (100, 130, 40), (300, 240, 135), "Sealed removable 3 L gross batch bin envelope"),
        ("GranulatorStage2", "MOD-SHRED-2-SCREEN", "TowerA", (145, 185, 250), (210, 130, 95), "Former Stage 3 proof reused as the MVP second stage"),
        ("ShredderStage1", "MOD-SHRED-1", "TowerA", (120, 170, 500), (260, 160, 105), "Primary twin-shaft proof module envelope"),
        ("ManualFeedHopper", "MOD-MANUAL-HOPPER", "TowerA", (120, 140, 700), (260, 220, 320), "Fixed anti-reach manual hopper; no classifier"),
        ("Extruder", "MOD-EXTRUDER", "TowerB", (700, 270, 60), (850, 220, 240), "Guarded hot-line proof envelope"),
        ("DryerFeeder", "MOD-DRYER", "TowerB", (720, 20, 500), (320, 270, 400), "Compact 0.5 kg insulated dryer keep-out"),
        ("ControlEnclosure", "MOD-CONTROL", "TowerB", (1050, 20, 500), (500, 200, 400), "BOM-traceable grounded control enclosure envelope"),
        ("CoolingGaugePuller", "MOD-COOL-GAUGE-PULLER", "TowerB", (1550, 310, 80), (700, 160, 180), "Straight forming-line proof envelope"),
        ("Spooler", "MOD-SPOOLER", "TowerB", (1895, 20, 40), (355, 240, 320), "Offset spooler proof envelope"),
    ]
    placements = {}
    for name, part_id, tower, xyz, size, material in modules:
        if name == "BatchBin":
            # 250 x 160 x 75 mm = 3.0 L gross; 50 mm is the 2.0 L usable fill.
            outer = Part.makeBox(300, 240, 135, App.Vector(*xyz))
            cavity_origin = (xyz[0] + 25, xyz[1] + 40, xyz[2] + 5)
            gross_cavity = Part.makeBox(250, 160, 75, App.Vector(*cavity_origin))
            obj = feature(doc, objects, name, part_id, part_id, outer.cut(gross_cavity), material,
                          "MODULE_ENVELOPE", tower)
            obj.addProperty("App::PropertyVolume", "GrossCavity", "BatchInterface")
            obj.GrossCavity = 3_000_000
            obj.addProperty("App::PropertyVolume", "UsableVolume", "BatchInterface")
            obj.UsableVolume = 2_000_000
            for ref_name, ref_shape in (
                ("BatchBinGrossCavityReference", gross_cavity),
                ("BatchBinUsableVolumeReference", Part.makeBox(250, 160, 50, App.Vector(*cavity_origin))),
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
        ("A_Chute_Hopper_Stage1", (200, 215, 605), (100, 70, 95)),
        ("A_Chute_Stage1_Stage2", (205, 215, 345), (90, 70, 155)),
        ("A_Chute_Stage2_Bin", (215, 215, 175), (70, 70, 75)),
    )
    for name, xyz, size in chute_specs:
        box(doc, objects, name, name.replace("_", "-"), name.replace("_", "-"), xyz, size,
            "Grounded stainless removable chute envelope", "TRANSFER_CHUTE", "TowerA")

    # Tower B batch receiver: asymmetric key, twin clamp bosses and sealed
    # metal throat are explicit so docking cannot be inferred from prose only.
    receiver = Part.makeBox(240, 200, 12, App.Vector(755, 35, 900))
    throat = Part.makeBox(100, 80, 48, App.Vector(825, 95, 912))
    key = Part.makeBox(24, 55, 20, App.Vector(755, 35, 912))
    clamps = Part.makeCylinder(8, 28, App.Vector(800, 35, 912), App.Vector(0, 0, 1)).fuse(
        Part.makeCylinder(8, 28, App.Vector(945, 35, 912), App.Vector(0, 0, 1))
    )
    feature(doc, objects, "BatchDockReceiver", "IF-BATCH-DOCK", "IF-BATCH-DOCK",
            receiver.fuse(throat).fuse(key).fuse(clamps), "Grounded stainless batch dock",
            "BATCH_DOCK", "TowerB")

    # The straight 2040 rail begins at the Tower B rack boundary and terminates
    # exactly 760 mm later.  Cross ties keep the two rails in one review plane.
    rail_start = p["tower_b_origin_x_mm"] + p["tower_b_width_mm"]
    rail_length = p["service_rail_extension_mm"]
    for y in (290, 470):
        profile(doc, objects, f"TowerB_ServiceRail_{y}", (rail_start, y, 60), rail_length, "x", 20, "TowerB", "SERVICE_RAIL")
    for index, x in enumerate((rail_start, rail_start + rail_length / 2, rail_start + rail_length - 20), 1):
        profile(doc, objects, f"TowerB_RailCrossTie_{index}", (x, 290, 60), 200, "y", 20, "TowerB", "SERVICE_RAIL")

    # Physical energy boundaries used by the wiring/cable review.  These are
    # enclosure/contact-zone envelopes; ratings still come from the BOM gate.
    box(doc, objects, "CommonActuatorContactorPlaceholder", "PLACEHOLDER-KACT", "PLACEHOLDER-KACT",
        (1080, 40, 540), (120, 140, 130), "Unselected DC-rated contactor keep-out", "PLACEHOLDER", "TowerB")
    box(doc, objects, "MonitorInterfacePCBReserved", "PCB-RESERVED", "ELE-PCB-IF",
        (1260, 45, 560), (190, 32, 130), "PCB fabrication-hold reserved volume", "PCB_RESERVED", "TowerB")
    box(doc, objects, "ArduinoMegaPurchasedPlacement", "PURCHASED-MCU1", "SYS-CTRL-002",
        (1280, 45, 760), (102, 18, 54), "Arduino Mega nominal purchased-part placement", "PURCHASED_PART", "TowerB")
    box(doc, objects, "TowerA_DrivePlaceholder_Stage1", "PLACEHOLDER-DRV1", "SHR-DRV-001",
        (70, 380, 470), (140, 80, 120), "Drive rating and shaft interface unselected", "PLACEHOLDER", "TowerA")
    box(doc, objects, "TowerA_DrivePlaceholder_Stage2", "PLACEHOLDER-DRV2", "GRN-DRV-001",
        (250, 380, 220), (140, 80, 120), "Drive rating and shaft interface unselected", "PLACEHOLDER", "TowerA")
    box(doc, objects, "WireRouteTowerA", "WIRE-ROUTE-A", "WIRE-ROUTE-A",
        (450, 40, 70), (20, 80, 950), "Wire duct keep-out; power and sensor partitions required", "WIRE_ROUTE", "TowerA")
    box(doc, objects, "WireRouteInterTower", "WIRE-ROUTE-INTER", "WIRE-ROUTE-INTER",
        (500, 440, 80), (200, 25, 40), "Keyed inter-tower harness keep-out", "WIRE_ROUTE", "System")
    box(doc, objects, "WireRouteHighCurrent", "WIRE-ROUTE-HIGH", "WIRE-ROUTE-HIGH",
        (1030, 40, 520), (20, 140, 360), "24 V motor/heater wire duct keep-out", "WIRE_ROUTE", "TowerB")
    box(doc, objects, "WireRouteLogic", "WIRE-ROUTE-LOGIC", "WIRE-ROUTE-LOGIC",
        (1500, 40, 520), (20, 140, 360), "5 V sensor wire duct keep-out", "WIRE_ROUTE", "TowerB")

    outputs = export_document(doc, "full_assembly_skeleton", objects)
    compound = Part.makeCompound([obj.Shape for obj in objects])
    bb = compound.BoundBox
    report = {
        "revision": parameters["revision"],
        "architecture": "UNDERGRADUATE_TWO_TOWER_TWO_STAGE_MVP",
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
