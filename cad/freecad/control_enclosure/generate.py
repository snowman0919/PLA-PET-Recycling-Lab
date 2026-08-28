"""Generate a BOM-traceable control-enclosure layout and fabrication proof."""

from __future__ import annotations

import csv
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
    box_from_spec,
    make_backplate_and_partition,
    make_cable_management,
    make_control_enclosure,
    make_estop_candidate,
    make_glands_and_pe,
    make_pcb_board,
    make_pcb_reserved_keepout,
    make_pcb_standoffs,
    make_placeholder,
    make_qualification_candidate,
    make_selected_candidate,
    make_service_keepouts,
    make_shell,
    make_split_door,
    make_thermal_validation_zone,
    make_ui_placeholders,
    make_user_inventory,
    make_wire_route,
)


CATEGORY_STYLE = {
    "STRUCTURE": ((0.72, 0.72, 0.76), 0),
    "SELECTED_CANDIDATE_ENVELOPE": ((0.20, 0.72, 0.30), 15),
    "QUALIFICATION_CANDIDATE_ENVELOPE": ((0.95, 0.82, 0.12), 20),
    "PCB_RESERVED": ((0.12, 0.45, 0.85), 20),
    "PCB_SERVICE_KEEP_OUT": ((0.35, 0.65, 1.00), 75),
    "USER_INVENTORY_ENVELOPE": ((0.30, 0.70, 0.90), 35),
    "PLACEHOLDER_TBD": ((1.00, 0.55, 0.10), 55),
    "WIRE_ROUTE_24V_HIGH_CURRENT_HEATER": ((0.85, 0.12, 0.10), 15),
    "WIRE_ROUTE_HARDWIRED_SAFETY_CHAIN": ((1.00, 0.72, 0.00), 15),
    "WIRE_ROUTE_5V_LOGIC_SENSOR": ((0.20, 0.45, 1.00), 15),
    "WIRE_ROUTE_PROTECTIVE_EARTH": ((0.10, 0.75, 0.25), 15),
    "SERVICE_KEEP_OUT": ((0.85, 0.20, 0.75), 80),
    "THERMAL_VALIDATION_ZONE": ((0.75, 0.20, 0.20), 80),
}


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def styled_feature(doc, name, label, shape, part_id, material, category, ref="", evidence=""):
    obj = add_feature(doc, name, label, shape, part_id, material)
    obj.addProperty("App::PropertyString", "Category", "Layout")
    obj.Category = category
    obj.addProperty("App::PropertyString", "ReferenceDesignator", "Layout")
    obj.ReferenceDesignator = ref
    obj.addProperty("App::PropertyString", "DimensionEvidence", "Layout")
    obj.DimensionEvidence = evidence
    color, transparency = CATEGORY_STYLE[category]
    obj.addProperty("App::PropertyString", "DisplayColorRGB", "Layout")
    obj.DisplayColorRGB = ",".join(f"{channel:.2f}" for channel in color)
    obj.addProperty("App::PropertyInteger", "DisplayTransparencyPercent", "Layout")
    obj.DisplayTransparencyPercent = transparency
    # FreeCADCmd has no GUI ViewObject.  The explicit properties survive in
    # FCStd and downstream viewers can apply the same legend deterministically.
    if obj.ViewObject is not None:
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.Transparency = transparency
    return obj


def write_service_door_dxf(path: Path, params: dict) -> None:
    width, height = params["width_mm"], params["height_mm"]
    entities = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    for x1, y1, x2, y2 in ((0, 0, width, 0), (width, 0, width, height), (width, height, 0, height), (0, height, 0, 0)):
        line("OUTLINE_T1_5", x1, y1, x2, y2)
    for x, y in ((8, 8), (width - 8, 8), (8, height - 8), (width - 8, height - 8)):
        circle("DOOR_M4_TBD", x, y, 2.25)
    circle("SELECTED_S0_A22E_M_02", 170.0, 330.0, params["layout"]["door_selected_candidate"]["panel_cutout_diameter_mm"] / 2)
    for x1, y1, x2, y2 in ((285, 300, 385, 300), (385, 300, 385, 364), (385, 364, 285, 364), (285, 364, 285, 300)):
        line("PLACEHOLDER_TFT_CUTOUT", x1, y1, x2, y2)
    for x in (300.0, 350.0, 400.0):
        circle("PLACEHOLDER_UI_22MM", x, 260.0, 11.15)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def write_layout_csv(path: Path, params: dict) -> None:
    fields = [
        "reference", "bom_part_id", "placement_state", "zone", "origin_mm", "size_mm",
        "mpn_or_class", "dimension_or_qualification_evidence", "harnesses",
    ]
    rows = []

    def row(spec, state, zone, evidence_key="source"):
        rows.append({
            "reference": spec["ref"],
            "bom_part_id": spec["part_id"],
            "placement_state": state,
            "zone": zone,
            "origin_mm": ";".join(str(v) for v in spec["origin_mm"]),
            "size_mm": ";".join(str(v) for v in spec["size_mm"]),
            "mpn_or_class": spec.get("mpn", spec.get("class", "TBD")),
            "dimension_or_qualification_evidence": spec.get(evidence_key, ""),
            "harnesses": spec.get("harnesses", ""),
        })

    enclosure = params["enclosure_candidate"]
    row(
        {
            **enclosure,
            "part_id": enclosure["part_id"],
            "origin_mm": [0.0, 0.0, 0.0],
            "size_mm": enclosure["external_size_mm"],
            "mpn": enclosure["mpn"],
        },
        "QUALIFICATION_CANDIDATE_ENVELOPE",
        "ENCLOSURE_STRUCTURE",
        "qualification",
    )
    for spec in params["layout"]["selected_candidates"]:
        row(spec, "SELECTED_CANDIDATE_ENVELOPE", "HIGH_CURRENT_SAFETY" if spec["part_id"] == "SAF-REL-001" else "LOGIC_LOW_VOLTAGE")
    row(params["layout"]["door_selected_candidate"], "SELECTED_CANDIDATE_ENVELOPE", "DOOR_HARDWIRED_SAFETY")
    row(params["layout"]["pcb_reserved"], "PCB_RESERVED_FABRICATION_HOLD", "LOGIC_LOW_VOLTAGE")
    for spec in params["layout"]["user_inventory"]:
        row(spec, "USER_INVENTORY_VERIFY_MEASUREMENT", "LOGIC_LOW_VOLTAGE")
    for spec in params["layout"]["qualification_candidates"]:
        row(spec, "QUALIFICATION_CANDIDATE_ENVELOPE", "HIGH_CURRENT_SAFETY", "qualification")
    for spec in params["layout"]["placeholders"]:
        row(spec, "PLACEHOLDER_TBD_NOT_ORDERABLE", "HIGH_CURRENT_SAFETY" if spec["origin_mm"][0] < params["logic_partition_x_mm"] else "LOGIC_LOW_VOLTAGE", "qualification")
    for spec in params["layout"]["wire_routes"]:
        route_spec = {**spec, "part_id": "MISC-WIR-001", "qualification": "reserved route/duct envelope; conductor gauge, connector and bend radius remain open"}
        row(route_spec, "WIRE_ROUTE_RESERVED", spec["class"], "qualification")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build():
    params = load_parameters()["control_enclosure"]
    components = {
        "door": component("ControlServiceDoor", "ControlServiceDoor", "CTL-DOOR-001", make_split_door(params), "Purchased/fabricated grounded sheet-metal door", "control_door_split"),
        "backplate": component("ControlBackplate", "ControlBackplate", "CTL-BACK-001", make_backplate_and_partition(params), "Grounded sheet metal", "control_backplate_partition"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "control_door_half.dxf"  # legacy release filename; now contains the full service door.
    write_service_door_dxf(dxf, params)
    layout_csv = ROOT / "electronics" / "architecture" / "control_enclosure_layout.csv"
    write_layout_csv(layout_csv, params)

    doc = App.newDocument("ControlEnclosureLayout")
    objects = [
        styled_feature(doc, "GroundedShell", "ENC1 | CTL-ENC-001 | QUALIFICATION CANDIDATE", make_shell(params), "CTL-ENC-001", "nVent HOFFMAN MAS0405021R5", "QUALIFICATION_CANDIDATE_ENVELOPE", "ENC1", params["enclosure_candidate"]["source"]),
        styled_feature(doc, "BackplatePartitionDIN", "CTL-BACK-001", make_backplate_and_partition(params), "CTL-ASM-001", "Grounded backplate, metal partition and DIN rails", "STRUCTURE"),
        styled_feature(doc, "ServiceDoor", "ENC1 DOOR | CTL-ENC-001 | QUALIFICATION CANDIDATE", make_split_door(params), "CTL-ENC-001", "nVent HOFFMAN MAS0405021R5 service door", "QUALIFICATION_CANDIDATE_ENVELOPE", "ENC1", params["enclosure_candidate"]["source"]),
    ]

    for spec in params["layout"]["selected_candidates"]:
        objects.append(styled_feature(
            doc, spec["ref"], f'{spec["ref"]} | {spec["part_id"]} | SELECTED', make_selected_candidate(spec),
            spec["part_id"], spec["mpn"], "SELECTED_CANDIDATE_ENVELOPE", spec["ref"], spec["source"],
        ))
    door_spec = params["layout"]["door_selected_candidate"]
    objects.append(styled_feature(
        doc, door_spec["ref"], f'{door_spec["ref"]} | {door_spec["part_id"]} | SELECTED', make_estop_candidate(params),
        door_spec["part_id"], door_spec["mpn"], "SELECTED_CANDIDATE_ENVELOPE", door_spec["ref"], door_spec["source"],
    ))

    pcb = params["layout"]["pcb_reserved"]
    objects.extend([
        styled_feature(doc, "PCB1BoardReserved", "PCB1 | ELE-PCB-IF | PCB RESERVED", make_pcb_board(params), pcb["part_id"], "FR-4, fabrication HOLD", "PCB_RESERVED", pcb["ref"], pcb["source"]),
        styled_feature(doc, "PCB1StandoffsReserved", "PCB1 | M3 STANDOFFS RESERVED", make_pcb_standoffs(params), "MISC-WIR-001", "M3 conductive/nonconductive selection TBD", "PCB_RESERVED", pcb["ref"], pcb["source"]),
        styled_feature(doc, "PCB1ComponentServiceKeepout", "PCB1 | COMPONENT + SERVICE KEEP-OUT", make_pcb_reserved_keepout(params), pcb["part_id"], "Non-fabricated clearance volume", "PCB_SERVICE_KEEP_OUT", pcb["ref"], pcb["source"]),
    ])

    for spec in params["layout"]["user_inventory"]:
        objects.append(styled_feature(
            doc, spec["ref"], f'{spec["ref"]} | {spec["part_id"]} | INVENTORY VERIFY', make_user_inventory(spec),
            spec["part_id"], "User-owned assembly", "USER_INVENTORY_ENVELOPE", spec["ref"], spec["source"],
        ))
    for spec in params["layout"]["qualification_candidates"]:
        objects.append(styled_feature(
            doc, spec["ref"], f'{spec["ref"]} | {spec["part_id"]} | QUALIFICATION CANDIDATE', make_qualification_candidate(spec),
            spec["part_id"], spec["mpn"], "QUALIFICATION_CANDIDATE_ENVELOPE", spec["ref"], f'{spec["source"]}; {spec["qualification"]}',
        ))
    for spec in params["layout"]["placeholders"]:
        objects.append(styled_feature(
            doc, spec["ref"], f'{spec["ref"]} | {spec["part_id"]} | PLACEHOLDER TBD', make_placeholder(spec),
            spec["part_id"], "Not selected / not orderable", "PLACEHOLDER_TBD", spec["ref"], spec["qualification"],
        ))
    for spec in params["layout"]["wire_routes"]:
        category = f'WIRE_ROUTE_{spec["class"]}'
        objects.append(styled_feature(
            doc, spec["ref"].replace("-", "_"), f'{spec["ref"]} | {spec["class"]}', make_wire_route(spec),
            "MISC-WIR-001", "Reserved duct/cable path", category, spec["ref"], spec["harnesses"],
        ))

    objects.extend([
        styled_feature(doc, "GlandsAndPEStuds", "GLANDS + PE STUDS", make_glands_and_pe(params), "MISC-WIR-001", "TBD glands, dedicated PE and door bond studs", "STRUCTURE", "XPE1", "H17 physical bond test remains open"),
        styled_feature(doc, "TerminalServiceKeepouts", "30 mm TERMINAL SERVICE KEEP-OUTS", make_service_keepouts(params), "REFERENCE", "Non-fabricated clearance volume", "SERVICE_KEEP_OUT", "KO-SERVICE", "minimum 30 mm; final bend radii depend on selected conductors"),
        styled_feature(doc, "ThermalValidationZone", "THERMAL INTERFACE TBD — NO VENT SELECTED", make_thermal_validation_zone(params), "CTL-ASM-001", "Non-fabricated thermal validation volume", "THERMAL_VALIDATION_ZONE", "TBD-THERMAL", "thermal-rise calculation and ingress strategy remain open"),
        styled_feature(doc, "UIPlaceholders", "TFT + BUTTONS | PLACEHOLDER TBD", make_ui_placeholders(params), "UI-CTL-001", "Unselected UI hardware", "PLACEHOLDER_TBD", "UI-TBD", "supplier cutouts and rear depth not selected"),
    ])

    outputs = export_document(doc, "control_enclosure_proof", objects)
    report = {
        "revision": load_parameters()["revision"],
        "design_state": "BOM_TRACEABLE_LAYOUT_PHYSICAL_APPROVAL_OPEN",
        "enclosure_mm": {"width": params["width_mm"], "depth": params["depth_mm"], "height": params["height_mm"]},
        "shell": bounding_box_report(doc.getObject("GroundedShell")),
        "service_door": bounding_box_report(doc.getObject("ServiceDoor")),
        "logic_partition_x_mm": params["logic_partition_x_mm"],
        "minimum_partition_gap_mm": params["minimum_partition_gap_mm"],
        "terminal_service_keepout_mm": params["terminal_service_keepout_mm"],
        "placement_state_counts": {
            "selected_candidate_envelopes": len(params["layout"]["selected_candidates"]) + 1,
            "qualification_candidate_envelopes": len(params["layout"]["qualification_candidates"]) + 2,
            "pcb_reserved": 1,
            "user_inventory_verify": len(params["layout"]["user_inventory"]),
            "placeholder_tbd": len(params["layout"]["placeholders"]) + 1,
            "wire_route_classes": len(params["layout"]["wire_routes"]),
        },
        "wire_route_classes": [spec["class"] for spec in params["layout"]["wire_routes"]],
        "outputs": {
            "assembly": outputs,
            "components": components,
            "service_door_dxf": str(dxf.relative_to(ROOT)),
            "layout_csv": str(layout_csv.relative_to(ROOT)),
        },
        "limitations": [
            "The green E-stop envelope is the selected physical interface; yellow exact-MPN envelopes still require application qualification and neither state is purchase approval.",
            "Blue PCB placement reserves the generated 190 x 130 mm board and four M3 holes, but its fabrication status remains HOLD.",
            "Orange placeholder solids cannot be used for ordering or drilling until exact candidates replace them.",
            "Red/yellow/blue/green wiring solids are route reservations, not conductor sizing or completed harness drawings. PCB, purchased Arduino and orange placeholders are distinct non-overlapping states.",
            "Thermal rise, SCCR, creepage, bend radius, PE continuity, ingress and door rear-depth checks remain physical/engineering gates.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "control_enclosure_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
