"""Generate the two-deck, three-stream vibratory sorter proof."""

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
    make_base,
    make_clamps,
    make_eccentric,
    make_fines_bin,
    make_isolators,
    make_motor,
    make_motor_bracket,
    make_outlets,
    make_screen_cassette,
    make_service_clamp,
    make_tray_frame,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_base_dxf(path: Path, params: dict) -> None:
    length, width = params["base_length_mm"], params["base_width_mm"]
    entities: list[str] = []

    def line(x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", "OUTLINE_T4", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(x, y, radius):
        entities.extend(["0", "CIRCLE", "8", "ISOLATOR_M6", "10", str(x), "20", str(y), "40", str(radius)])

    for a, b in (((0, 0), (length, 0)), ((length, 0), (length, width)), ((length, width), (0, width)), ((0, width), (0, 0))):
        line(*a, *b)
    for x, y in params["isolator_positions_mm"]:
        circle(x, y, 3.25)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["vibratory_sorter"]
    top = make_screen_cassette(params, params["top_screen_aperture_mm"], params["top_screen_pitch_mm"], 0.0)
    bottom = make_screen_cassette(
        params,
        params["bottom_screen_aperture_mm"],
        params["bottom_screen_pitch_mm"],
        -params["deck_spacing_mm"],
    )
    components = {
        "base": component("SorterBase", "BasePlate", "SRT-BASE-001", make_base(params), "Steel or aluminum", "sorter_base_plate"),
        "top_screen": component("SorterTopScreen", "TopScreen", "SRT-SCR-TOP", top, "Stainless screen cassette", "sorter_top_screen_6mm"),
        "bottom_screen": component("SorterBottomScreen", "BottomScreen", "SRT-SCR-BOT", bottom, "Stainless screen cassette", "sorter_bottom_screen_3mm"),
        "clamp": component("SorterClamp", "ServiceClamp", "SRT-CLP-001", make_service_clamp(params), "PETG/metal candidate", "sorter_service_clamp"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "sorter_base_plate.dxf"
    write_base_dxf(dxf, params)
    components["base"]["dxf"] = str(dxf.relative_to(ROOT))

    doc = App.newDocument("VibratorySorterProof")
    objects = [
        add_feature(doc, "BasePlate", "SRT-BASE-001", make_base(params), "SRT-BASE-001", "Steel or aluminum"),
        add_feature(doc, "Isolators", "SRT-ISO-001", make_isolators(params), "SRT-ISO-001", "Rubber candidate"),
        add_feature(doc, "TrayFrame", "SRT-TRAY-001", make_tray_frame(params), "SRT-TRAY-001", "Aluminum or steel"),
        add_feature(doc, "TopScreen6", "SRT-SCR-TOP", top, "SRT-SCR-TOP", "Stainless screen cassette"),
        add_feature(doc, "BottomScreen3", "SRT-SCR-BOT", bottom, "SRT-SCR-BOT", "Stainless screen cassette"),
        add_feature(doc, "ScrewClamps", "SRT-CLP-001", make_clamps(params), "SRT-CLP-001", "PETG/metal candidate"),
        add_feature(doc, "MotorBracket", "SRT-MNT-001", make_motor_bracket(params), "SRT-MNT-001", "Metal"),
        add_feature(doc, "DriveMotor", "SRT-MTR-001", make_motor(params), "SRT-MTR-001", "Donor DC/BLDC motor envelope"),
        add_feature(doc, "EccentricMass", "SRT-ECC-001", make_eccentric(params), "SRT-ECC-001", "Steel"),
        add_feature(doc, "OversizeAndAcceptableChutes", "SRT-OUT-001", make_outlets(params), "SRT-OUT-001", "Sheet metal"),
        add_feature(doc, "FinesBin", "SRT-BIN-FINE", make_fines_bin(params), "SRT-BIN-FINE", "Sealed removable bin"),
    ]
    outputs = export_document(doc, "vibratory_sorter_proof", objects)
    report = {
        "revision": load_parameters()["revision"],
        "assembly": bounding_box_report(doc.getObject("TrayFrame")),
        "screen_open_area_nominal": {
            "top_6mm": round((params["top_screen_aperture_mm"] / params["top_screen_pitch_mm"]) ** 2, 4),
            "bottom_3mm": round((params["bottom_screen_aperture_mm"] / params["bottom_screen_pitch_mm"]) ** 2, 4),
        },
        "routing": {
            "top_retained": "oversize_recirculation",
            "bottom_retained": "acceptable_to_dryer_or_storage",
            "bottom_pass": "sealed_fines_bin",
        },
        "outputs": {"assembly": outputs, "components": components},
        "limitations": [
            "Screen bars are a pitch/opening proof representation, not a sourced woven-mesh specification.",
            "Chutes are routing envelopes; seals, flexible boots and captive service latches remain to be detailed.",
            "Donor motor torque, bearing life, eccentric retention and balance require bench inspection.",
            "No simultaneous optical measurement is permitted until frame modal/transmissibility testing passes.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "vibratory_sorter_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
