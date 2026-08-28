#!/usr/bin/env python3
"""Clearance, optical-path and nip checks for the forming-line proof."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "freecad" / "forming_line"))
from geometry import (  # noqa: E402
    cooling_segment_length,
    make_calibration_fixture,
    make_cooling_fans,
    make_cooling_segment,
    make_cooling_tunnel,
    make_filament_reference,
    make_forming_frame,
    make_gauge_enclosure,
    make_gauge_optics,
    make_odometer,
    make_optical_ray_keepouts,
    make_puller_guard_and_support,
    make_puller_rollers,
)


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["filament_forming"]
    segment = make_cooling_segment(p)
    tunnel = make_cooling_tunnel(p)
    fans = make_cooling_fans(p)
    frame = make_forming_frame(p)
    filament = make_filament_reference(p)
    enclosure = make_gauge_enclosure(p)
    optics = make_gauge_optics(p)
    rays = make_optical_ray_keepouts(p)
    rollers = make_puller_rollers(p)
    odometer = make_odometer(p)
    puller_support = make_puller_guard_and_support(p)
    fixture = make_calibration_fixture(p)

    roller_solids = rollers.Solids
    ray_intersections = [solid.common(filament).Volume for solid in rays.Solids]
    checks = {
        "cooling_segment_length_mm": cooling_segment_length(p),
        "tunnel_length_mm": tunnel.BoundBox.XLength,
        "fan_tunnel_contact_mm": fans.distToShape(tunnel)[0],
        "frame_tunnel_contact_mm": frame.distToShape(tunnel)[0],
        "filament_tunnel_intersection_mm3": filament.common(tunnel).Volume,
        "filament_gauge_enclosure_intersection_mm3": filament.common(enclosure).Volume,
        "direct_ray_filament_intersection_mm3": ray_intersections[0],
        "orthogonal_ray_filament_intersection_mm3": ray_intersections[1],
        "nip_gap_mm": roller_solids[0].distToShape(roller_solids[1])[0],
        "filament_nip_intersection_mm3": filament.common(rollers).Volume,
        "filament_puller_guard_intersection_mm3": filament.common(puller_support).Volume,
        "odometer_filament_contact_mm": odometer.distToShape(filament)[0],
    }
    for shape in (segment, tunnel, fans, frame, filament, enclosure, optics, rays, rollers, odometer, puller_support, fixture):
        assert shape.isValid(), shape.ShapeType
    for shape in (segment, enclosure, rollers, fixture):
        box = shape.BoundBox
        assert max(box.XLength, box.YLength, box.ZLength) <= 210.0 + 1e-7, box
    assert abs(checks["tunnel_length_mm"] - p["cooling_tunnel_length_mm"]) < 1e-7, checks
    assert checks["fan_tunnel_contact_mm"] < 1e-7, checks
    assert checks["frame_tunnel_contact_mm"] < 1e-7, checks
    assert checks["filament_tunnel_intersection_mm3"] < 1e-7, checks
    assert checks["filament_gauge_enclosure_intersection_mm3"] < 1e-7, checks
    assert checks["direct_ray_filament_intersection_mm3"] > 0.1, checks
    assert checks["orthogonal_ray_filament_intersection_mm3"] > 0.1, checks
    assert abs(checks["nip_gap_mm"] - p["puller"]["nominal_nip_gap_mm"]) < 1e-7, checks
    assert checks["filament_nip_intersection_mm3"] > 0.1, checks
    assert checks["filament_puller_guard_intersection_mm3"] < 1e-7, checks
    assert checks["odometer_filament_contact_mm"] < 1e-7, checks

    report = {
        "checks": {key: round(value, 6) for key, value in checks.items()},
        "status": "PASS",
        "limits": [
            "Ray cylinders prove only nominal dual-axis crossings; they do not prove optical resolution or uncertainty.",
            "The 1.5 mm nip gap intentionally compresses a nominal 1.75 mm strand by 0.25 mm across compliant tyres.",
            "Fan contact and openings do not prove occupied-duct air speed, pressure loss or thermal resistance.",
            "Odometer zero distance is intended light contact; spring force, wheel runout and slip are unverified.",
        ],
    }
    path = ROOT / "simulation" / "forming" / "geometry_clearance.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("FORMING_GEOMETRY_OK")


if __name__ == "__main__":
    main()
