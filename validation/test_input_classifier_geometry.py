#!/usr/bin/env python3
"""Geometry gates for the double-gate classifier and storage diverter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "cad" / "freecad" / "input_classifier"
COMMON = HERE.parent / "common"
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
from project import load_parameters  # noqa: E402
from geometry import (  # noqa: E402
    diverter_port_centres,
    make_bottle_reference,
    make_closed_gate,
    make_diverter_rotor,
    make_input_classifier,
    make_light_tunnel,
    make_open_gate,
)


def main():
    p = load_parameters()["input_classifier"]
    upper = make_closed_gate(p, 160.0)
    lower_open = make_open_gate(p, 50.0)
    bottle = make_bottle_reference(p)
    optics = make_light_tunnel(p)
    ray = optics.Solids[2]
    reach_probe = Part.makeBox(20.0, 20.0, 220.0, App.Vector(150.0, 100.0, 0.0))
    rotor = make_diverter_rotor(p)
    checks = {
        "assembly_valid": make_input_classifier(p).isValid(),
        "upper_gate_probe_intersection_mm3": reach_probe.common(upper).Volume,
        "lower_open_probe_intersection_mm3": reach_probe.common(lower_open).Volume,
        "gate_separation_mm": p["gate_separation_mm"],
        "bottle_length_mm": bottle.BoundBox.YLength,
        "bottle_diameter_mm": bottle.BoundBox.XLength,
        "optical_ray_bottle_intersection_mm3": ray.common(bottle).Volume,
        "diverter_port_count": len(diverter_port_centres(p)),
        "diverter_rotor_max_mm": max(rotor.BoundBox.XLength, rotor.BoundBox.YLength, rotor.BoundBox.ZLength),
    }
    assert checks["assembly_valid"], checks
    assert checks["upper_gate_probe_intersection_mm3"] > 1.0, checks
    assert checks["lower_open_probe_intersection_mm3"] < 1e-7, checks
    assert checks["gate_separation_mm"] >= 105.0, checks
    assert abs(checks["bottle_length_mm"] - 210.0) < 1e-6, checks
    assert abs(checks["bottle_diameter_mm"] - 66.0) < 0.1, checks
    assert checks["optical_ray_bottle_intersection_mm3"] > 1.0, checks
    assert checks["diverter_port_count"] == 7, checks
    assert checks["diverter_rotor_max_mm"] <= 210.0, checks
    report = {"checks": checks, "status": "PASS", "limitations": [
        "A solid upper gate blocks the nominal reach probe while the lower gate is shown open; simultaneous-open prevention still needs a mechanical cam/interlock coupon.",
        "The bottle envelope proves space only, not singulation, exposure quality or fragment containment.",
        "The seven-port head does not include external bin volume, hose bend loss or cross-contamination seals.",
    ]}
    output = ROOT / "simulation" / "kinematic" / "input_classifier_geometry.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("INPUT_CLASSIFIER_GEOMETRY_OK")


if __name__ == "__main__":
    main()
