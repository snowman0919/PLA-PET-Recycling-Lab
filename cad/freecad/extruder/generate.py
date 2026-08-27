"""Generate the 18 mm pressure-limited single-screw extruder proof."""

from __future__ import annotations

import json
import sys
from math import cos, pi
from pathlib import Path

import FreeCAD as App

HERE = Path(__file__).resolve().parent
COMMON = HERE.parent / "common"
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
from project import ROOT, add_feature, bounding_box_report, ensure_dir, export_document, load_parameters  # noqa: E402
from geometry import (  # noqa: E402
    FLIGHT_START_X,
    THRUST_BEARING_X,
    make_barrel,
    make_breaker_plate,
    make_die,
    make_drive_and_coupling,
    make_feed_throat_cooling,
    make_heat_shield,
    make_heaters,
    make_insulation,
    make_pressure_devices,
    make_radial_bearings,
    make_screw,
    make_support_frame,
    make_thrust_bearing,
    make_thrust_plate_component,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_thrust_plate_dxf(path: Path, params: dict) -> None:
    width, height = 120.0, 174.0
    shaft_x, shaft_y = 60.0, 124.0
    entities: list[str] = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    for first, second in (((0, 0), (width, 0)), ((width, 0), (width, height)), ((width, height), (0, height)), ((0, height), (0, 0))):
        line("OUTLINE_T12", *first, *second)
    circle("SHAFT_CLEARANCE_D20", shaft_x, shaft_y, 10.0)
    for x in (12.0, width - 12.0):
        circle("FRAME_M8", x, 12.0, 4.5)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["extruder"]
    components = {
        "screw": component("ExtruderScrew", "HelicalScrew", "EXT-SCR-001", make_screw(params), "4140 candidate", "extruder_screw"),
        "barrel": component("ExtruderBarrel", "BarrelAndFeedThroat", "EXT-BRL-001", make_barrel(params), "Tool steel or stainless-lined", "extruder_barrel"),
        "breaker": component("ExtruderBreaker", "BreakerPlate", "EXT-BRK-001", make_breaker_plate(params), "Tool steel candidate", "extruder_breaker_plate"),
        "die": component("ExtruderDie", "FilamentDie", "EXT-DIE-001", make_die(params), "Hard-chrome tool steel candidate", "extruder_die"),
        "thrust_plate": component("ExtruderThrustPlate", "ThrustPlate", "EXT-THR-001", make_thrust_plate_component(params), "Structural steel", "extruder_thrust_plate"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "extruder_thrust_plate.dxf"
    write_thrust_plate_dxf(dxf, params)
    components["thrust_plate"]["dxf"] = str(dxf.relative_to(ROOT))

    doc = App.newDocument("ExtruderProof")
    objects = [
        add_feature(doc, "SupportFrame", "EXT-FRAME-001", make_support_frame(params), "EXT-THR-001", "Metal plate and 4040 envelopes"),
        add_feature(doc, "HelicalScrew", "EXT-SCR-001", make_screw(params), "EXT-SCR-001", "4140 candidate"),
        add_feature(doc, "BarrelAndFeedThroat", "EXT-BRL-001", make_barrel(params), "EXT-BRL-001", "Tool steel or stainless-lined"),
        add_feature(doc, "FeedThroatCooling", "EXT-COOL-001", make_feed_throat_cooling(params), "EXT-BRL-001", "Metal coolant jacket envelope"),
        add_feature(doc, "BreakerPlate", "EXT-BRK-001", make_breaker_plate(params), "EXT-BRK-001", "Tool steel candidate"),
        add_feature(doc, "FilamentDie", "EXT-DIE-001", make_die(params), "EXT-DIE-001", "Hard-chrome tool steel candidate"),
        add_feature(doc, "HeaterClamps", "EXT-HTR-001", make_heaters(params), "EXT-HTR-001", "Heater clamp envelopes"),
        add_feature(doc, "Insulation", "EXT-INS-001", make_insulation(params), "EXT-HTR-001", "High-temperature insulation"),
        add_feature(doc, "VentilatedShield", "EXT-SHIELD-001", make_heat_shield(params), "EXT-HTR-001", "Grounded sheet metal"),
        add_feature(doc, "ThrustBearing", "EXT-THR-51102", make_thrust_bearing(params), "EXT-THR-001", "51102 envelope"),
        add_feature(doc, "RadialBearings", "EXT-RAD-6002", make_radial_bearings(params), "EXT-THR-001", "6002-2RS envelopes"),
        add_feature(doc, "DriveAndCoupling", "EXT-DRV-001", make_drive_and_coupling(params), "EXT-DRV-001", "Donor/buy and guard envelopes"),
        add_feature(doc, "PressureSafetyAndCatch", "EXT-REL-001", make_pressure_devices(params), "EXT-REL-001", "Sensor, rupture and metal catch envelopes"),
    ]
    outputs = export_document(doc, "extruder_proof", objects)
    chord_error = params["screw_diameter_mm"] / 2 * (1 - cos((10 / 2) * pi / 180))
    screw_length = params["screw_diameter_mm"] * params["length_to_diameter_ratio"]
    report = {
        "revision": load_parameters()["revision"],
        "screw": bounding_box_report(doc.getObject("HelicalScrew")),
        "barrel": bounding_box_report(doc.getObject("BarrelAndFeedThroat")),
        "die": bounding_box_report(doc.getObject("FilamentDie")),
        "flight": {
            "turns": screw_length / (params["screw_diameter_mm"] * params["pitch_ratio"]),
            "facets_per_turn": 36,
            "maximum_radial_chord_error_mm": chord_error,
        },
        "pressure_mpa": {
            "clean_target": params["clean_pressure_target_mpa"],
            "warning": params["pressure_warning_mpa"],
            "reduction": params["pressure_reduction_mpa"],
            "latched_trip": params["normal_pressure_limit_mpa"],
            "mechanical_relief_candidate": params["mechanical_relief_candidate_mpa"],
            "structure_proof": params["structural_proof_pressure_mpa"],
        },
        "thrust_heat_break_mm": FLIGHT_START_X - 2.0 - (THRUST_BEARING_X + params["thrust_bearing"]["height_mm"]),
        "outputs": {"assembly": outputs, "components": components, "thrust_plate_dxf": str(dxf.relative_to(ROOT))},
        "limitations": [
            "The 10-degree faceted flight is a collision/manufacturing-path proof; the machinist must generate a smooth 18 mm helix from the dimension table.",
            "Pressure-sensor and rupture-device solids are keep-outs; threads, rated diaphragms and guarded discharge hardware are not selected.",
            "Heaters, insulation and shield are envelopes; clamp contact, wiring, thermocouple wells and thermal bridges are not detailed.",
            "Bearing seats, seals, keyway, surface finish, heat treatment and screw/barrel runout tolerances require a controlled fabrication drawing.",
            "No polymer operation is allowed before hydrostatic/thermal/pressure-relief and material-flow coupons pass.",
        ],
    }
    path = ROOT / "validation" / "fabrication_review" / "extruder_proof.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
