#!/usr/bin/env python3
"""Load-path, dancer sweep and full-spool checks for the spooler proof."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "freecad" / "spooler"))
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


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["spooler"]
    spool = make_spool_reference(p)
    shaft = make_spool_shaft(p)
    bearings = make_spool_bearings(p)
    frame = make_spooler_frame(p)
    adapters = make_installed_adapters(p)
    dancer = make_dancer(p)
    sweep = make_dancer_sweep(p)
    traverse = make_traverse(p)
    drive = make_spool_drive(p)
    guard = make_spool_guard(p)
    adapter_set = make_adapter_set(p)
    carriage = make_traverse_carriage_component(p)
    plate = make_bearing_plate_component(p)
    shaft_analysis = json.loads((ROOT / "simulation" / "forming" / "line_design.json").read_text())["spooler"]

    checks = {
        "shaft_bearing_contact_mm": shaft.distToShape(bearings)[0],
        "shaft_bearing_intersection_mm3": shaft.common(bearings).Volume,
        "bearing_frame_contact_mm": bearings.distToShape(frame)[0],
        "adapter_spool_contact_mm": adapters.distToShape(spool)[0],
        "adapter_spool_intersection_mm3": adapters.common(spool).Volume,
        "adapter_shaft_radial_clearance_mm": adapters.distToShape(shaft)[0],
        "dancer_sweep_spool_intersection_mm3": sweep.common(spool).Volume,
        "minimum_dancer_spool_clearance_mm": minimum_dancer_spool_clearance_mm(p),
        "spool_guard_radial_clearance_mm": spool.distToShape(guard)[0],
        "drive_shaft_contact_mm": drive.distToShape(shaft)[0],
        "base_x_min_mm": frame.BoundBox.XMin,
        "base_x_max_mm": frame.BoundBox.XMax,
        "spool_width_mm": spool.BoundBox.YLength,
        "spool_outer_diameter_mm": max(spool.BoundBox.XLength, spool.BoundBox.ZLength),
        "shaft_safety_factor": shaft_analysis["shaft_safety_factor_at_250mpa_yield"],
        "shaft_deflection_mm": shaft_analysis["shaft_center_deflection_mm"],
    }
    for shape in (spool, shaft, bearings, frame, adapters, dancer, sweep, traverse, drive, guard, adapter_set, carriage, plate):
        assert shape.isValid(), shape.ShapeType
    for shape in (adapter_set, carriage):
        box = shape.BoundBox
        assert max(box.XLength, box.YLength, box.ZLength) <= 210.0 + 1e-7, box
    assert checks["shaft_bearing_contact_mm"] < 1e-7, checks
    assert checks["shaft_bearing_intersection_mm3"] < 1e-7, checks
    assert checks["bearing_frame_contact_mm"] < 1e-7, checks
    assert checks["adapter_spool_contact_mm"] < 1e-7, checks
    assert checks["adapter_spool_intersection_mm3"] < 1e-7, checks
    assert checks["adapter_shaft_radial_clearance_mm"] >= 0.099, checks
    assert checks["dancer_sweep_spool_intersection_mm3"] < 1e-7, checks
    assert checks["minimum_dancer_spool_clearance_mm"] >= 6.0, checks
    assert checks["spool_guard_radial_clearance_mm"] >= 4.99, checks
    assert checks["drive_shaft_contact_mm"] < 1e-7, checks
    assert checks["base_x_min_mm"] <= p["base_origin_x_mm"] + 1e-7, checks
    assert checks["base_x_max_mm"] >= p["base_origin_x_mm"] + p["base_length_mm"] - 1e-7, checks
    assert abs(checks["spool_width_mm"] - p["maximum_spool_width_mm"]) < 1e-7, checks
    assert checks["spool_outer_diameter_mm"] >= p["maximum_spool_outer_diameter_mm"] - 0.1, checks
    assert checks["shaft_safety_factor"] >= 5.0, checks
    assert checks["shaft_deflection_mm"] <= 0.05, checks

    report = {
        "checks": {key: round(value, 6) for key, value in checks.items()},
        "status": "PASS",
        "limits": [
            "The adapter has 0.1 mm nominal shaft clearance; a separate metal clamp/key must transmit torque and retain the spool axially.",
            "Dancer clearance is a rigid end-angle envelope and excludes arm flex, roller runout, loose filament and guard deflection.",
            "The 4 g shaft screen does not qualify printed adapters, frame joints, bearings, tip stability or resonance.",
            "Traverse geometry proves travel space only; backlash, layer reversal and full-spool winding require a physical coupon.",
        ],
    }
    path = ROOT / "simulation" / "forming" / "spooler_geometry.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("SPOOLER_GEOMETRY_OK")


if __name__ == "__main__":
    main()
