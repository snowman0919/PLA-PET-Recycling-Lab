"""Generate segregated control enclosure proof artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App

HERE = Path(__file__).resolve().parent
COMMON = HERE.parent / "common"
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
from project import ROOT, add_feature, bounding_box_report, ensure_dir, export_document, load_parameters  # noqa: E402
from geometry import (  # noqa: E402
    make_backplate_and_partition,
    make_cable_management,
    make_control_enclosure,
    make_face_controls,
    make_high_current_devices,
    make_logic_devices,
    make_shell,
    make_split_door,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_door_half_dxf(path: Path, params: dict) -> None:
    width, height = params["door_split_width_mm"], params["height_mm"]
    entities = []
    for x1, y1, x2, y2 in ((0, 0, width, 0), (width, 0, width, height), (width, height, 0, height), (0, height, 0, 0)):
        entities.extend(["0", "LINE", "8", "OUTLINE_T1_5", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])
    for x, y in ((8, 8), (width - 8, 8), (8, height - 8), (width - 8, height - 8)):
        entities.extend(["0", "CIRCLE", "8", "DOOR_M4", "10", str(x), "20", str(y), "40", "2.25"])
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["control_enclosure"]
    components = {
        "door": component("ControlDoorSplit", "ControlDoorSplit", "CTL-DOOR-001", make_split_door(params), "Sheet metal or segmented impact-rated panel", "control_door_split"),
        "backplate": component("ControlBackplate", "ControlBackplate", "CTL-BACK-001", make_backplate_and_partition(params), "Grounded sheet metal", "control_backplate_partition"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "control_door_half.dxf"
    write_door_half_dxf(dxf, params)

    doc = App.newDocument("ControlEnclosureProof")
    objects = [
        add_feature(doc, "GroundedShell", "CTL-SHELL-001", make_shell(params), "CTL-ASM-001", "Grounded sheet metal enclosure"),
        add_feature(doc, "BackplatePartitionDIN", "CTL-BACK-001", make_backplate_and_partition(params), "CTL-ASM-001", "Grounded metal backplate partition and DIN rails"),
        add_feature(doc, "HighCurrentDevices", "REFERENCE-HIGH-CURRENT", make_high_current_devices(params), "REFERENCE", "Safety relay contactor fuse and heater-driver envelopes"),
        add_feature(doc, "LogicDevices", "REFERENCE-LOGIC", make_logic_devices(params), "REFERENCE", "Mega Pi buck sensor-interface envelopes"),
        add_feature(doc, "SplitDoor", "CTL-DOOR-001", make_split_door(params), "CTL-ASM-001", "Two serviceable sheet panels"),
        add_feature(doc, "FaceControls", "UI-PANEL-001", make_face_controls(params), "UI-CTL-001", "E-stop TFT buttons and rotary envelopes"),
        add_feature(doc, "CableManagementPE", "CTL-CABLE-001", make_cable_management(params), "MISC-WIR-001", "Separated ducts glands and PE stud"),
    ]
    outputs = export_document(doc, "control_enclosure_proof", objects)
    report = {
        "revision": load_parameters()["revision"],
        "shell": bounding_box_report(doc.getObject("GroundedShell")),
        "split_door": bounding_box_report(doc.getObject("SplitDoor")),
        "logic_partition_x_mm": params["logic_partition_x_mm"],
        "minimum_partition_gap_mm": params["minimum_partition_gap_mm"],
        "outputs": {"assembly": outputs, "components": components, "door_half_dxf": str(dxf.relative_to(ROOT))},
        "limitations": [
            "All electrical devices are keep-outs; exact MPN dimensions, heat dissipation, creepage, SCCR and terminal bend radii require selection.",
            "The enclosure is a grounded sheet-metal topology proof, not a certified panel or mains wiring drawing.",
            "Door halves prove the 210 mm fabrication/print envelope; hinges, gasket, captive fasteners and impact rating require sourced hardware.",
            "The E-stop actuator must mount to a rigid panel and a dual-channel safety relay; the UI cannot substitute for it.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "control_enclosure_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
