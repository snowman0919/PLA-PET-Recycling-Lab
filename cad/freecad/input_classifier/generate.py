"""Generate double-gate classifier and seven-port storage proofs."""

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
    diverter_port_centres,
    make_bottle_reference,
    make_classification_storage,
    make_classifier_frame,
    make_closed_gate,
    make_diverter_ports,
    make_diverter_rotor,
    make_input_classifier,
    make_light_tunnel,
    make_open_gate,
    make_reject_flap,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_gate_dxf(path: Path, params: dict) -> None:
    width = params["gate_panel_width_mm"] / 2.0
    depth = params["gate_panel_depth_mm"]
    entities = []
    for x1, y1, x2, y2 in ((0, 0, width, 0), (width, 0, width, depth), (width, depth, 0, depth), (0, depth, 0, 0)):
        entities.extend(["0", "LINE", "8", "OUTLINE_T4", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])
    for x, y in ((8, 8), (width - 8, 8), (8, depth - 8), (width - 8, depth - 8)):
        entities.extend(["0", "CIRCLE", "8", "HINGE_M4", "10", str(x), "20", str(y), "40", "2.25"])
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["input_classifier"]
    components = {
        "gate_half": component("ClassifierGateHalf", "ClassifierGateHalf", "INP-GATE-001", make_closed_gate(params, 0.0), "Metal or impact-rated panel", "classifier_gate_pair"),
        "diverter_rotor": component("ColorDiverterRotor", "ColorDiverterRotor", "BIN-DIV-001", make_diverter_rotor(params), "Printed cold fixture with metal shaft", "color_diverter_rotor"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    gate_dxf = dxf_dir / "classifier_gate_half.dxf"
    write_gate_dxf(gate_dxf, params)

    doc = App.newDocument("InputClassifierProof")
    objects = [
        add_feature(doc, "FrameAndLightShield", "INP-FRM-001", make_classifier_frame(params), "INP-ASM-001", "Segmented impact-rated enclosure and metal supports"),
        add_feature(doc, "UpperClosedGate", "INP-GATE-UPPER", make_closed_gate(params, 160.0), "INP-ASM-001", "Metal or impact-rated gate pair"),
        add_feature(doc, "LowerOpenGate", "INP-GATE-LOWER", make_open_gate(params, 50.0), "INP-ASM-001", "Reference open position"),
        add_feature(doc, "CameraLighting", "INP-OPT-001", make_light_tunnel(params), "INP-ASM-001", "Camera backlight and reference ray envelopes"),
        add_feature(doc, "BottleReference", "REFERENCE-BOTTLE-500ML", make_bottle_reference(params), "REFERENCE", "Maximum 500 mL bottle envelope"),
        add_feature(doc, "RejectFlapAndChute", "INP-REJ-001", make_reject_flap(params), "INP-ASM-001", "Metal shaft and guarded reject path"),
    ]
    input_outputs = export_document(doc, "input_classifier_proof", objects)

    storage_doc = App.newDocument("ClassificationStorageProof")
    storage_objects = [
        add_feature(storage_doc, "SevenPortFrame", "BIN-PORT-7", make_diverter_ports(params), "BIN-DIV-001", "Metal/printed segmented port frame"),
        add_feature(storage_doc, "RotatingChute", "BIN-DIV-001", make_diverter_rotor(params), "BIN-DIV-001", "Guarded rotating chute envelope"),
    ]
    storage_outputs = export_document(storage_doc, "classification_storage_proof", storage_objects)
    report = {
        "revision": load_parameters()["revision"],
        "input_classifier": bounding_box_report(doc.getObject("FrameAndLightShield")),
        "maximum_bottle": bounding_box_report(doc.getObject("BottleReference")),
        "storage_diverter": bounding_box_report(storage_doc.getObject("SevenPortFrame")),
        "port_count": len(diverter_port_centres(params)),
        "gate_separation_mm": params["gate_separation_mm"],
        "outputs": {"input": input_outputs, "storage": storage_outputs, "components": components, "gate_dxf": str(gate_dxf.relative_to(ROOT))},
        "limitations": [
            "The two gates prove mutually exclusive blocking positions; hinge, cam interlock, positive-opening switches and impact containment need sourced hardware and coupons.",
            "Camera, backlight, bottle and optical ray are keep-outs; material accuracy requires a source-object-grouped dataset.",
            "Seven ports map six fixed color bins plus Reject; external grounded hoses/bins and material-batch segregation are not modeled.",
            "The reject flap is a kinematic envelope without actuator, bearing, seal or fragment-load detail.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "input_classifier_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
