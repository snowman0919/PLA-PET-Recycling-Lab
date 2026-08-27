"""Generate Stage-3 granulator rotor/stator and 4/5/6 mm screen proofs."""

from __future__ import annotations

import json
import sys
from math import floor, pi
from pathlib import Path

import FreeCAD as App

HERE = Path(__file__).resolve().parent
COMMON = HERE.parent / "common"
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
from project import ROOT, add_feature, bounding_box_report, ensure_dir, export_document, load_parameters  # noqa: E402
from geometry import make_bearing, make_carrier, make_plate, make_retainer, make_rotor, make_screen, make_shaft, make_stator  # noqa: E402


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_plate_dxf(path: Path, params: dict) -> None:
    p = params["plate"]
    entities: list[str] = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    width, height = p["width_mm"], p["height_mm"]
    for a, b in (((0, 0), (width, 0)), ((width, 0), (width, height)), ((width, height), (0, height)), ((0, height), (0, 0))):
        line("OUTLINE_T14", *a, *b)
    cx, cy = p["shaft_center_x_mm"], p["shaft_center_y_mm"]
    circle("THRU", cx, cy, p["through_bore_mm"] / 2)
    circle("CBORE_DEPTH_11_8", cx, cy, p["counterbore_mm"] / 2)
    for x, y in ((8, 8), (92, 8), (8, 82), (92, 82)):
        circle("FRAME_M5", x, y, p["frame_hole_mm"] / 2)
    for x, y in ((cx - 24, cy), (cx + 24, cy), (cx, cy - 24), (cx, cy + 24)):
        circle("RETAINER_M4", x, y, p["retainer_hole_mm"] / 2)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["stage3"]
    axial = params["axial_layout"]
    components = {
        "rotor": component("Stage3Rotor", "Rotor", "GRN-ROTOR-001", make_rotor(params), "Steel; inserts TBD", "stage3_rotor"),
        "stator": component("Stage3Stator", "Stator", "GRN-STATOR-001", make_stator(params), "Tool steel TBD", "stage3_stator"),
        "plate": component("Stage3BearingPlate", "BearingPlate", "GRN-PLATE-001", make_plate(params, 0.0, True), "Steel or aluminum TBD", "stage3_bearing_plate"),
    }
    for opening in params["screen_opening_candidates_mm"]:
        tag = str(int(opening))
        components[f"screen_{tag}mm"] = component(
            f"Stage3Screen{tag}",
            "Screen",
            f"GRN-SCREEN-{tag}",
            make_screen(params, opening),
            "Perforated steel",
            f"stage3_screen_{tag}mm",
        )
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "stage3_bearing_plate.dxf"
    write_plate_dxf(dxf, params)
    components["plate"]["dxf"] = str(dxf.relative_to(ROOT))

    doc = App.newDocument("Stage3GranulatorProof")
    objects = [
        add_feature(doc, "Shaft", "GRN-SHAFT-001", make_shaft(params), "GRN-SHAFT-001", "C45 steel candidate"),
        add_feature(doc, "Rotor", "GRN-ROTOR-001", make_rotor(params), "GRN-ROTOR-001", "Steel; inserts TBD"),
        add_feature(doc, "Stator", "GRN-STATOR-001", make_stator(params), "GRN-STATOR-001", "Tool steel TBD"),
        add_feature(doc, "StatorCarrier", "GRN-CARRIER-001", make_carrier(params), "GRN-CARRIER-001", "Steel"),
        add_feature(doc, "BaselineScreen", "GRN-SCREEN-5", make_screen(params, params["baseline_screen_opening_mm"]), "GRN-SCREEN-5", "Perforated steel"),
        add_feature(doc, "LeftPlate", "GRN-PLATE-L", make_plate(params, axial["left_plate_z_mm"], True), "GRN-PLATE-001", "Steel or aluminum TBD"),
        add_feature(doc, "RightPlate", "GRN-PLATE-R", make_plate(params, axial["right_plate_z_mm"], False), "GRN-PLATE-001", "Steel or aluminum TBD"),
        add_feature(doc, "LeftBearing", "GRN-BRG-L", make_bearing(params, axial["left_bearing_z_mm"]), "GRN-BRG-001", "Bearing steel"),
        add_feature(doc, "RightBearing", "GRN-BRG-R", make_bearing(params, axial["right_bearing_z_mm"]), "GRN-BRG-001", "Bearing steel"),
        add_feature(doc, "LeftRetainer", "GRN-RET-L", make_retainer(params, axial["left_retainer_z_mm"]), "GRN-RET-001", "Steel"),
        add_feature(doc, "RightRetainer", "GRN-RET-R", make_retainer(params, axial["right_retainer_z_mm"]), "GRN-RET-001", "Steel"),
    ]
    outputs = export_document(doc, "stage3_granulator_proof", objects)
    candidate_ratios = {}
    screen_width = params["rotor_outer_diameter_mm"] + 10.0
    columns = floor((screen_width - 2 * params["screen_edge_margin_x_mm"]) / params["screen_pitch_mm"]) + 1
    rows = floor((params["active_width_mm"] - 2 * params["screen_edge_margin_z_mm"]) / params["screen_pitch_mm"]) + 1
    holes = columns * rows
    gross_area = screen_width * params["active_width_mm"]
    for opening in params["screen_opening_candidates_mm"]:
        candidate_ratios[f"{int(opening)}mm"] = round(holes * pi * (opening / 2) ** 2 / gross_area, 4)
    report = {
        "revision": load_parameters()["revision"],
        "rotor": bounding_box_report(doc.getObject("Rotor")),
        "baseline_screen": bounding_box_report(doc.getObject("BaselineScreen")),
        "screen_geometric_open_area_ratios": candidate_ratios,
        "screen_hole_grid": {"columns": columns, "rows": rows, "total": holes},
        "outputs": {"assembly": outputs, "components": components},
        "limitations": [
            "Flat perforated screen is a proof coupon, not the final curved screen/support frame.",
            "Rotor inserts are fused envelopes; retention, balance and sharpened edges are not detailed.",
            "Oversize recirculation, dust extraction, lower guard and clean-out interlock are not modeled.",
            "Final 3-6 mm distribution and fines fraction require physical sieve tests.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "stage3_granulator_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
