"""Generate the dual-profile dryer and metering feeder proof."""

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
    make_agitator,
    make_auger,
    make_auger_housing,
    make_base_and_load_cells,
    make_drive_and_air_system,
    make_gates,
    make_heat_shield,
    make_hopper,
    make_insulation,
    make_lid,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_base_dxf(path: Path, params: dict) -> None:
    entities: list[str] = []

    def line(x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", "OUTLINE_T6", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    length = params["base_length_mm"]
    width = params["base_width_mm"]
    for a, b in (((0, 0), (length, 0)), ((length, 0), (length, width)), ((length, width), (0, width)), ((0, width), (0, 0))):
        line(*a, *b)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["dryer_feeder"]
    components = {
        "hopper": component("DryerHopper", "MetalHopper", "DRY-VSL-001", make_hopper(params), "Stainless steel", "dryer_metal_hopper"),
        "shield": component("DryerShield", "VentilatedShield", "DRY-INS-001", make_heat_shield(params), "Sheet metal", "dryer_heat_shield"),
        "auger": component("DryerAuger", "MeteringAuger", "DRY-FDR-AUG", make_auger(params), "Stainless steel proof", "dryer_metering_auger"),
        "housing": component("DryerAugerHousing", "AugerHousing", "DRY-FDR-HSG", make_auger_housing(params), "Metal", "dryer_auger_housing"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "dryer_base_plate.dxf"
    write_base_dxf(dxf, params)

    doc = App.newDocument("DryerFeederProof")
    objects = [
        add_feature(doc, "BaseAndLoadCells", "DRY-BASE-001", make_base_and_load_cells(params), "DRY-BASE-001", "Metal and load-cell envelopes"),
        add_feature(doc, "MetalHopper", "DRY-VSL-001", make_hopper(params), "DRY-VSL-001", "Stainless steel"),
        add_feature(doc, "Insulation", "DRY-INS-001", make_insulation(params), "DRY-INS-001", "High-temperature insulation"),
        add_feature(doc, "VentilatedShield", "DRY-SHD-001", make_heat_shield(params), "DRY-INS-001", "Sheet metal"),
        add_feature(doc, "Lid", "DRY-LID-001", make_lid(params), "DRY-LID-001", "Stainless steel"),
        add_feature(doc, "Agitator", "DRY-AGT-001", make_agitator(params), "DRY-AGT-001", "Stainless steel"),
        add_feature(doc, "DoubleGate", "DRY-GATE-001", make_gates(params), "DRY-GATE-001", "Stainless steel"),
        add_feature(doc, "MeteringAuger", "DRY-FDR-AUG", make_auger(params), "DRY-FDR-001", "Stainless steel proof"),
        add_feature(doc, "AugerHousing", "DRY-FDR-HSG", make_auger_housing(params), "DRY-FDR-001", "Metal"),
        add_feature(doc, "DrivesAndDryAir", "DRY-AIR-001", make_drive_and_air_system(params), "DRY-AIR-001", "Donor/buy envelopes"),
    ]
    outputs = export_document(doc, "dryer_feeder_proof", objects)
    report = {
        "revision": load_parameters()["revision"],
        "hopper": bounding_box_report(doc.getObject("MetalHopper")),
        "heat_shield": bounding_box_report(doc.getObject("VentilatedShield")),
        "auger": bounding_box_report(doc.getObject("MeteringAuger")),
        "thermal_profiles": {
            "pla": params["pla_profile"],
            "pet": params["pet_profile"],
        },
        "outputs": {"assembly": outputs, "components": components, "base_dxf": str(dxf)},
        "limitations": [
            "Auger flights are axial pitch envelopes, not a fabrication-ready continuous helix.",
            "Insulation and dry-air equipment are keep-out solids; seals, ducts and cartridge internals are not detailed.",
            "Double gates are open-bore proof plates; actuators, overlap timing and gas leakage are not validated.",
            "The three-point support frame is a load-path envelope; joints, fasteners and load-cell side-load protection are not detailed.",
            "PET operation remains prohibited until agglomeration, dew point and outlet moisture tests pass.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "dryer_feeder_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
