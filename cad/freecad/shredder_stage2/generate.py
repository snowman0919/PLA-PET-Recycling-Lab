"""Generate the Stage-2 rotor/bed-knife proof assembly and exports."""

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
    make_bearing,
    make_bed_knife,
    make_carrier,
    make_plate,
    make_retainer,
    make_rotor,
    make_shaft,
)


def write_plate_dxf(path: Path, params: dict) -> None:
    plate = params["plate"]
    entities: list[str] = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    w, h = plate["width_mm"], plate["height_mm"]
    for a, b in (((0, 0), (w, 0)), ((w, 0), (w, h)), ((w, h), (0, h)), ((0, h), (0, 0))):
        line("OUTLINE_T14", *a, *b)
    cx, cy = plate["shaft_center_x_mm"], plate["shaft_center_y_mm"]
    circle("THRU", cx, cy, plate["through_bore_mm"] / 2)
    circle("CBORE_DEPTH_11_8", cx, cy, plate["counterbore_mm"] / 2)
    for x, y in ((10, 10), (100, 10), (10, 90), (100, 90)):
        circle("FRAME_M5", x, y, plate["frame_hole_mm"] / 2)
    for x, y in ((cx - 25, cy), (cx + 25, cy), (cx, cy - 25), (cx, cy + 25)):
        circle("RETAINER_M4", x, y, plate["retainer_hole_mm"] / 2)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def component_source(doc_name: str, object_name: str, label: str, part_id: str, shape, material: str, stem: str):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, object_name, label, shape, part_id, material)
    return export_document(doc, stem, [obj])


def build():
    params = load_parameters()["stage2"]
    axial = params["axial_layout"]
    components = {
        "rotor": component_source("Stage2Rotor", "Rotor", "SHR2-ROTOR-001", "SHR2-ROTOR-001", make_rotor(params), "Steel; blade grade TBD", "stage2_rotor"),
        "bed_knife": component_source("Stage2BedKnife", "BedKnife", "SHR2-KNIFE-001", "SHR2-KNIFE-001", make_bed_knife(params), "Tool steel TBD", "stage2_bed_knife"),
        "plate": component_source("Stage2BearingPlate", "BearingPlate", "SHR2-PLATE-001", "SHR2-PLATE-001", make_plate(params, 0.0, True), "Steel or aluminum TBD", "stage2_bearing_plate"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf_path = dxf_dir / "stage2_bearing_plate.dxf"
    write_plate_dxf(dxf_path, params)
    components["plate"]["dxf"] = str(dxf_path.relative_to(ROOT))

    doc = App.newDocument("Stage2ShredderProof")
    objects = [
        add_feature(doc, "Shaft", "SHR2-SHAFT-001", make_shaft(params), "SHR2-SHAFT-001", "C45 steel candidate"),
        add_feature(doc, "Rotor", "SHR2-ROTOR-001", make_rotor(params), "SHR2-ROTOR-001", "Steel; blade grade TBD"),
        add_feature(doc, "BedKnife", "SHR2-KNIFE-001", make_bed_knife(params), "SHR2-KNIFE-001", "Tool steel TBD"),
        add_feature(doc, "BedKnifeCarrier", "SHR2-CARRIER-001", make_carrier(params), "SHR2-CARRIER-001", "Steel"),
        add_feature(doc, "LeftPlate", "SHR2-PLATE-L", make_plate(params, axial["left_plate_z_mm"], True), "SHR2-PLATE-001", "Steel or aluminum TBD"),
        add_feature(doc, "RightPlate", "SHR2-PLATE-R", make_plate(params, axial["right_plate_z_mm"], False), "SHR2-PLATE-001", "Steel or aluminum TBD"),
        add_feature(doc, "LeftBearing", "SHR2-BRG-L", make_bearing(params, axial["left_bearing_z_mm"]), "SHR2-BRG-001", "Bearing steel"),
        add_feature(doc, "RightBearing", "SHR2-BRG-R", make_bearing(params, axial["right_bearing_z_mm"]), "SHR2-BRG-001", "Bearing steel"),
        add_feature(doc, "LeftRetainer", "SHR2-RET-L", make_retainer(params, axial["left_retainer_z_mm"]), "SHR2-RET-001", "Steel"),
        add_feature(doc, "RightRetainer", "SHR2-RET-R", make_retainer(params, axial["right_retainer_z_mm"]), "SHR2-RET-001", "Steel"),
    ]
    outputs = export_document(doc, "stage2_shredder_proof", objects)
    report = {
        "revision": load_parameters()["revision"],
        "rotor": bounding_box_report(doc.getObject("Rotor")),
        "bed_knife": bounding_box_report(doc.getObject("BedKnife")),
        "rotor_mass_steel_kg_estimate": round(doc.getObject("Rotor").Shape.Volume * 7.85e-6, 4),
        "nominal_blade_clearance_mm": params["blade_clearance_mm"],
        "outputs": {"assembly": outputs, "components": components},
        "limitations": [
            "The fused rotor is a proof envelope; replaceable blade pockets, bolts and balance features are not detailed.",
            "A 6-12 mm output distribution is not guaranteed without physical PLA/PET coupons and may require a grate or recirculation.",
            "Blade/bed-knife material, heat treatment, grind, shim stack and edge radius remain unselected.",
            "Hopper, lower chamber, discharge guard, seals and cleaning interlock are outside this proof assembly.",
        ],
    }
    report_path = ROOT / "validation" / "fabrication_review" / "stage2_shredder_proof.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
