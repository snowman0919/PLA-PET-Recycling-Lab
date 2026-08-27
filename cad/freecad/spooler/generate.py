"""Generate the guarded 1 kg dancer/traverse spooler proof."""

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
    make_adapter_set,
    make_bearing_plate_component,
    make_dancer,
    make_dancer_sweep,
    make_installed_adapters,
    make_spool_bearings,
    make_spool_drive,
    make_spool_guard,
    make_spool_reference,
    make_spool_shaft,
    make_spooler_frame,
    make_traverse,
    make_traverse_carriage_component,
    minimum_dancer_spool_clearance_mm,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_bearing_plate_dxf(path: Path, params: dict) -> None:
    width, height = 140.0, 250.0
    entities: list[str] = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    for a, b in (((0, 0), (width, 0)), ((width, 0), (width, height)), ((width, height), (0, height)), ((0, height), (0, 0))):
        line("OUTLINE_T17", *a, *b)
    circle("BEARING_6001_D28", 70.0, 164.0, 14.0)
    for x in (15.0, 125.0):
        circle("FRAME_M8", x, 16.0, 4.5)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["spooler"]
    components = {
        "shaft": component("SpoolerShaft", "SpoolerShaft", "SPL-SHAFT-001", make_spool_shaft(params), "Steel", "spooler_shaft"),
        "adapters": component("SpoolAdapterSet", "SpoolAdapterSet", "SPL-ADP-001", make_adapter_set(params), "Printed cold fixture with metal clamp", "spool_adapter_set"),
        "carriage": component("TraverseCarriage", "TraverseCarriage", "SPL-TRV-001", make_traverse_carriage_component(params), "Printed cold fixture", "traverse_carriage"),
        "bearing_plate": component("SpoolerBearingPlate", "SpoolerBearingPlate", "SPL-PLATE-001", make_bearing_plate_component(params), "Structural metal", "spooler_bearing_plate"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "spooler_bearing_plate.dxf"
    write_bearing_plate_dxf(dxf, params)

    doc = App.newDocument("SpoolerProof")
    objects = [
        add_feature(doc, "BaseAndMetalFrame", "SPL-FRM-001", make_spooler_frame(params), "SPL-ASM-001", "Metal plate and profile load path"),
        add_feature(doc, "SpoolShaft", "SPL-SHAFT-001", make_spool_shaft(params), "SPL-ASM-001", "12 mm steel shaft"),
        add_feature(doc, "SpoolBearings", "SPL-BRG-6001", make_spool_bearings(params), "SPL-ASM-001", "6001-2RS envelopes"),
        add_feature(doc, "LoadedSpoolReference", "REFERENCE-SPOOL-D200-W73", make_spool_reference(params), "REFERENCE", "Maximum loaded spool reference"),
        add_feature(doc, "InstalledAdapters", "SPL-ADP-001", make_installed_adapters(params), "SPL-ASM-001", "Taper adapters with metal shaft clamp required"),
        add_feature(doc, "Dancer", "SPL-DAN-001", make_dancer(params), "SPL-ASM-001", "Low-force arm roller and angle sensor envelopes"),
        add_feature(doc, "DancerSweepKeepout", "REFERENCE-DANCER-SWEEP", make_dancer_sweep(params), "REFERENCE", "End-angle keepout"),
        add_feature(doc, "Traverse", "SPL-TRV-001", make_traverse(params), "SPL-ASM-001", "Lead screw carriage guide and endstop envelopes"),
        add_feature(doc, "DriveAndTorqueGuard", "SPL-DRV-001", make_spool_drive(params), "SPL-ASM-001", "Motor coupling slip clutch and guard envelopes"),
        add_feature(doc, "SpoolGuard", "SPL-GRD-001", make_spool_guard(params), "SPL-ASM-001", "Metal or impact-rated cage envelope"),
    ]
    outputs = export_document(doc, "spooler_proof", objects)
    analysis = json.loads((ROOT / "simulation" / "forming" / "line_design.json").read_text())["spooler"]
    report = {
        "revision": load_parameters()["revision"],
        "frame": bounding_box_report(doc.getObject("BaseAndMetalFrame")),
        "spool": bounding_box_report(doc.getObject("LoadedSpoolReference")),
        "dancer_clearance_mm": minimum_dancer_spool_clearance_mm(params),
        "shaft_analysis": analysis,
        "outputs": {"assembly": outputs, "components": components, "bearing_plate_dxf": str(dxf)},
        "limitations": [
            "The loaded spool is a 200 by 73 mm maximum reference; hub-hole geometry is intentionally adapter-dependent.",
            "Printed taper adapters center the spool but may not be the sole torque or axial-retention load path.",
            "Dancer reference solids show only end-angle collision envelopes; spring law, sensor linearity and dynamic tension require coupons.",
            "Drive, clutch, traverse screw, endstops and guard are supplier/space envelopes without detailed fasteners or wiring.",
        ],
    }
    report_path = ROOT / "validation" / "fabrication_review" / "spooler_proof.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
