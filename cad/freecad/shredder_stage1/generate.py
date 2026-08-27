"""Generate the Stage-1 dual-shaft proof assembly and fabrication sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Mesh
import Part

HERE = Path(__file__).resolve().parent
COMMON = HERE.parent / "common"
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
from project import ROOT, add_feature, bounding_box_report, ensure_dir, export_document, load_parameters  # noqa: E402
from geometry import (  # noqa: E402
    make_bearing,
    make_coupling_envelope,
    make_cutter,
    make_plate,
    make_retainer,
    make_shaft,
    make_spacer,
    make_timing_envelope,
)


CENTERS = ((50.0, 60.0), (100.0, 60.0))


def write_plate_dxf(path: Path, params: dict) -> None:
    plate = params["plate"]
    entities = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    w, h = plate["width_mm"], plate["height_mm"]
    for a, b in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        line("OUTLINE_T14", *a, *b)
    for center in CENTERS:
        circle("THRU", *center, plate["through_bore_mm"] / 2)
        circle("CBORE_DEPTH_11_8", *center, plate["counterbore_mm"] / 2)
    for x, y in ((50, 35), (50, 85), (100, 35), (100, 85)):
        circle("RETAINER_M4", x, y, plate["retainer_hole_mm"] / 2)
    for x, y in ((12, 12), (138, 12), (12, 108), (138, 108)):
        circle("FRAME_M5", x, y, plate["frame_hole_mm"] / 2)
    text = "\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""])
    path.write_text(text, encoding="ascii")


def build_component_sources(params: dict) -> dict:
    cutter_doc = App.newDocument("Stage1CutterDisc")
    cutter_obj = add_feature(cutter_doc, "CutterDisc", "SHR-CUT-001", make_cutter(params), "SHR-CUT-001", "Hardened steel TBD")
    cutter_outputs = export_document(cutter_doc, "stage1_cutter_disc", [cutter_obj])

    plate_doc = App.newDocument("Stage1BearingPlate")
    plate_obj = add_feature(plate_doc, "BearingPlate", "SHR-PLATE-001", make_plate(params, 0, True), "SHR-PLATE-001", "Steel or aluminum TBD")
    plate_outputs = export_document(plate_doc, "stage1_bearing_plate", [plate_obj])
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf_path = dxf_dir / "stage1_bearing_plate.dxf"
    write_plate_dxf(dxf_path, params)
    return {"cutter": cutter_outputs, "plate": {**plate_outputs, "dxf": str(dxf_path.relative_to(ROOT))}}


def build():
    params = load_parameters()["stage1"]
    axial = params["axial_layout"]
    component_outputs = build_component_sources(params)
    doc = App.newDocument("Stage1ShredderProof")
    objects = []
    shaft_a, _ = make_shaft(params, CENTERS[0], axial["shaft_start_z_mm"], phase_deg=0)
    shaft_b, _ = make_shaft(
        params,
        CENTERS[1],
        axial["shaft_start_z_mm"],
        phase_deg=params["phase_offset_deg"],
    )
    objects.append(add_feature(doc, "ShaftA", "SHR-SHAFT-A", shaft_a, "SHR-SHAFT-001", "C45 steel candidate"))
    objects.append(add_feature(doc, "ShaftB", "SHR-SHAFT-B", shaft_b, "SHR-SHAFT-001", "C45 steel candidate"))

    t = params["cutter_thickness_mm"]
    s = params["spacer_thickness_mm"]
    for index in range(params["cutter_count_per_shaft"]):
        pair_pitch = t + s
        z_a_cutter = index * pair_pitch
        z_a_spacer = z_a_cutter + t
        z_b_spacer = index * pair_pitch - params["axial_cutter_clearance_mm"]
        z_b_cutter = z_b_spacer + s
        objects.append(add_feature(doc, f"CutterA{index+1}", f"SHR-CUT-A{index+1}", make_cutter(params, CENTERS[0], z_a_cutter, 0), "SHR-CUT-001", "Hardened steel TBD"))
        objects.append(add_feature(doc, f"SpacerA{index+1}", f"SHR-SPACER-A{index+1}", make_spacer(params, CENTERS[0], z_a_spacer), "SHR-SPACER-001", "Steel"))
        objects.append(add_feature(doc, f"SpacerB{index+1}", f"SHR-SPACER-B{index+1}", make_spacer(params, CENTERS[1], z_b_spacer), "SHR-SPACER-001", "Steel"))
        objects.append(add_feature(doc, f"CutterB{index+1}", f"SHR-CUT-B{index+1}", make_cutter(params, CENTERS[1], z_b_cutter, params["phase_offset_deg"]), "SHR-CUT-001", "Hardened steel TBD"))

    stack_outputs = export_document(doc, "stage1_cutter_stack", list(objects))

    plate_specs = (
        ("LeftPlate", axial["left_plate_z_mm"], True),
        ("RightPlate", axial["right_plate_z_mm"], False),
        ("TimingSupportPlate", axial["timing_support_plate_z_mm"], True),
    )
    for name, z, from_low in plate_specs:
        objects.append(add_feature(doc, name, f"SHR-PLATE-{name}", make_plate(params, z, from_low), "SHR-PLATE-001", "Steel or aluminum TBD"))

    bearing_z = (
        axial["left_bearing_z_mm"],
        axial["right_bearing_z_mm"],
        axial["timing_support_bearing_z_mm"],
    )
    for shaft_index, center in enumerate(CENTERS):
        for side_index, z in enumerate(bearing_z):
            objects.append(add_feature(doc, f"Bearing{shaft_index}{side_index}", "SHR-BRG-001", make_bearing(params, center, z), "SHR-BRG-001", "Bearing steel"))
    objects.append(add_feature(doc, "LeftRetainer", "SHR-BRG-RETAINER-L", make_retainer(params, axial["left_retainer_z_mm"]), "SHR-RET-001", "Steel"))
    objects.append(add_feature(doc, "RightRetainer", "SHR-BRG-RETAINER-R", make_retainer(params, axial["right_retainer_z_mm"]), "SHR-RET-001", "Steel"))
    objects.append(add_feature(doc, "TimingSupportRetainer", "SHR-BRG-RETAINER-S", make_retainer(params, axial["timing_support_retainer_z_mm"]), "SHR-RET-001", "Steel"))

    for index, center in enumerate(CENTERS):
        objects.append(add_feature(doc, f"TimingEnvelope{index+1}", "TIMING-GEAR-PITCH-ENVELOPE", make_timing_envelope(params, center, axial["timing_envelope_z_mm"]), "SHR-GEAR-TBD", "Envelope only"))
    objects.append(add_feature(doc, "InputCouplingEnvelope", "INPUT-COUPLING-ENVELOPE", make_coupling_envelope(params, CENTERS[0], axial["input_coupling_z_mm"]), "SHR-COUPLING-TBD", "Envelope only"))

    outputs = export_document(doc, "stage1_shredder_proof", objects)
    cutter_volume = make_cutter(params).Volume
    report = {
        "revision": load_parameters()["revision"],
        "cutter": bounding_box_report(doc.getObject("CutterA1")),
        "plate": bounding_box_report(doc.getObject("LeftPlate")),
        "cutter_volume_mm3": round(cutter_volume, 1),
        "cutter_mass_steel_kg_each": round(cutter_volume * 7.85e-6, 4),
        "cutter_count_total": params["cutter_count_per_shaft"] * 2,
        "bearing_candidate": params["bearing"],
        "outputs": {"assembly": outputs, "cutter_stack": stack_outputs, "components": component_outputs},
        "limitations": [
            "Timing gears are pitch-envelope cylinders, not tooth geometry.",
            "The third plate and two bearings are the Engineering Recommended timing-gear support; Target Budget omission needs a lower validated trip load.",
            "Cutter material, heat treatment and edge grind remain unselected.",
            "Bearing counterbore fit and retainer preload require fabrication drawing tolerances.",
            "Hopper, chamber liners, seals and service guard are not included in this proof assembly.",
        ],
    }
    report_path = ROOT / "validation" / "fabrication_review" / "stage1_shredder_proof.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
