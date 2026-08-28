"""Generate cooling, dual-view diameter gauge and puller proof artifacts."""

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
    MODULE_LENGTH,
    cooling_segment_length,
    make_calibration_fixture,
    make_cooling_fans,
    make_cooling_segment,
    make_cooling_tunnel,
    make_filament_reference,
    make_forming_frame,
    make_gauge_enclosure,
    make_gauge_optical_proof,
    make_gauge_optics,
    make_odometer,
    make_optical_ray_keepouts,
    make_puller_guard_and_support,
    make_puller_rollers,
)


def component(doc_name, name, part_id, shape, material, stem):
    doc = App.newDocument(doc_name)
    obj = add_feature(doc, name, part_id, shape, part_id, material)
    return export_document(doc, stem, [obj])


def write_fan_plate_dxf(path: Path, params: dict) -> None:
    width, height = cooling_segment_length(params), 140.0
    fan = params["fan_envelope_mm"]
    cx, cy = width / 2, height / 2
    entities: list[str] = []

    def line(layer, x1, y1, x2, y2):
        entities.extend(["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)])

    def circle(layer, x, y, radius):
        entities.extend(["0", "CIRCLE", "8", layer, "10", str(x), "20", str(y), "40", str(radius)])

    for a, b in (((0, 0), (width, 0)), ((width, 0), (width, height)), ((width, height), (0, height)), ((0, height), (0, 0))):
        line("OUTLINE_T1_5", *a, *b)
    circle("FAN_AIR_D68_8", cx, cy, fan * 0.43)
    for dx in (-35.75, 35.75):
        for dy in (-35.75, 35.75):
            circle("FAN_M4", cx + dx, cy + dy, 2.25)
    path.write_text("\n".join(["0", "SECTION", "2", "ENTITIES", *entities, "0", "ENDSEC", "0", "EOF", ""]), encoding="ascii")


def build():
    params = load_parameters()["filament_forming"]
    components = {
        "cooling_segment": component("CoolingSegment", "CoolingSegment", "COOL-DUCT-SEG", make_cooling_segment(params), "Sheet metal or qualified cold duct", "cooling_tunnel_segment"),
        "gauge_enclosure": component("GaugeEnclosure", "GaugeEnclosure", "GAU-ENC-001", make_gauge_enclosure(params), "Opaque cold-side printed enclosure", "diameter_gauge_enclosure"),
        "gauge_optical_proof": component("GaugeOpticalProof", "GaugeOpticalProof", "GAU-OPT-001", make_gauge_optical_proof(params), "Reference rays and optical keep-outs", "diameter_gauge_optical_proof"),
        "puller_rollers": component("PullerRollers", "PullerRollers", "PUL-ROL-001", make_puller_rollers(params), "Metal shafts with compliant replaceable tyres", "puller_roller_pair"),
        "calibration_fixture": component("GaugeCalibrationFixture", "CalibrationFixture", "GAU-CAL-001", make_calibration_fixture(params), "Printed cold fixture", "gauge_calibration_fixture"),
    }
    dxf_dir = ensure_dir(ROOT / "exports" / "dxf")
    dxf = dxf_dir / "cooling_fan_plate.dxf"
    write_fan_plate_dxf(dxf, params)

    doc = App.newDocument("FormingLineProof")
    objects = [
        add_feature(doc, "Frame", "FRM-FORM-001", make_forming_frame(params), "FRM-001", "2020/2040 aluminum profile envelopes"),
        add_feature(doc, "CoolingTunnel", "COOL-AIR-001", make_cooling_tunnel(params), "COOL-AIR-001", "Sheet metal or heat-qualified duct segments"),
        add_feature(doc, "CoolingFans", "COOL-FAN-001", make_cooling_fans(params), "COOL-AIR-001", "80 mm donor/buy fan envelopes"),
        add_feature(doc, "GaugeEnclosure", "GAU-ENC-001", make_gauge_enclosure(params), "GAU-SEN-001", "Opaque printed cold enclosure"),
        add_feature(doc, "GaugeOptics", "GAU-OPT-001", make_gauge_optics(params), "GAU-SEN-001", "Two shadow-sensor heads and LED backlight envelopes"),
        add_feature(doc, "OpticalRayKeepouts", "REFERENCE-OPTICAL-RAYS", make_optical_ray_keepouts(params), "REFERENCE", "Reference only"),
        add_feature(doc, "PullerRollers", "PUL-ROL-001", make_puller_rollers(params), "PUL-ASM-001", "Synchronized roller and gear envelopes"),
        add_feature(doc, "OdometerAndSlipEncoder", "PUL-ODO-001", make_odometer(params), "PUL-ASM-001", "Low-force encoder wheel envelope"),
        add_feature(doc, "PullerGuardAndSupport", "PUL-GRD-001", make_puller_guard_and_support(params), "PUL-ASM-001", "Cold printed guard with metal supports"),
        add_feature(doc, "FilamentReference", "REFERENCE-D1_75", make_filament_reference(params), "REFERENCE", "Reference only"),
    ]
    outputs = export_document(doc, "forming_line_proof", objects)
    segment_box = make_cooling_segment(params).BoundBox
    overall_box = App.BoundBox()
    for obj in objects:
        overall_box.add(obj.Shape.BoundBox)
    report = {
        "revision": load_parameters()["revision"],
        "overall": {
            "x_mm": round(overall_box.XLength, 3),
            "y_mm": round(overall_box.YLength, 3),
            "z_mm": round(overall_box.ZLength, 3),
            "fits_210_cube": max(overall_box.XLength, overall_box.YLength, overall_box.ZLength) <= 210.0,
        },
        "cooling_segment": {
            "x_mm": round(segment_box.XLength, 3),
            "y_mm": round(segment_box.YLength, 3),
            "z_mm": round(segment_box.ZLength, 3),
            "fits_210_cube": max(segment_box.XLength, segment_box.YLength, segment_box.ZLength) <= 210.0,
        },
        "gauge": bounding_box_report(doc.getObject("GaugeEnclosure")),
        "puller": bounding_box_report(doc.getObject("PullerGuardAndSupport")),
        "layout": {
            "module_length_mm": MODULE_LENGTH,
            "cooling_length_mm": params["cooling_tunnel_length_mm"],
            "die_to_gauge_mm": params["die_to_gauge_distance_mm"],
            "puller_start_mm": 600.0,
        },
        "outputs": {"assembly": outputs, "components": components, "fan_plate_dxf": str(dxf.relative_to(ROOT))},
        "limitations": [
            "Fan blocks and shadow-sensor parts are supplier keep-outs; mounting holes, cable bends, apertures and airflow plenums require selection.",
            "Reference rays prove two orthogonal line crossings, not edge linearity, ambient-light rejection or uncertainty.",
            "The first hot strand-facing duct must be metal or temperature-qualified; PLA is prohibited near an unverified hot strand.",
            "Roller tyre compression, shaft bearings, synchronized gears, spring adjustment and guard interlock require detailed drawings and coupons.",
        ],
    }
    report_path = ROOT / "validation" / "fabrication_review" / "forming_line_proof.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()
