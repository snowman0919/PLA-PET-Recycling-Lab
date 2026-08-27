#!/usr/bin/env python3
"""Solid clearance and metal load-path checks for the extruder proof."""

from __future__ import annotations

import json
import sys
from math import cos, pi, sqrt
from pathlib import Path

import FreeCAD as App
import Part


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "freecad" / "extruder"))
from geometry import (  # noqa: E402
    AXIS_Y,
    AXIS_Z,
    FLIGHT_START_X,
    THRUST_BEARING_X,
    make_barrel,
    make_breaker_plate,
    make_die,
    make_drive_and_coupling,
    make_heat_shield,
    make_heaters,
    make_insulation,
    make_pressure_devices,
    make_screw,
    make_support_frame,
    make_thrust_bearing,
)


def main() -> None:
    p = json.loads((ROOT / "cad" / "parameters" / "baseline.json").read_text())["extruder"]
    screw = make_screw(p)
    barrel = make_barrel(p)
    breaker = make_breaker_plate(p)
    die = make_die(p)
    support = make_support_frame(p)
    thrust = make_thrust_bearing(p)
    heaters = make_heaters(p)
    insulation = make_insulation(p)
    shield = make_heat_shield(p)
    drive = make_drive_and_coupling(p)
    pressure_devices = make_pressure_devices(p)

    screw_length = p["screw_diameter_mm"] * p["length_to_diameter_ratio"]
    barrel_start = FLIGHT_START_X - 2.0
    barrel_end = FLIGHT_START_X + screw_length + 4.0
    bore_probe = Part.makeCylinder(
        p["screw_diameter_mm"] / 2,
        barrel_end - barrel_start,
        App.Vector(barrel_start, AXIS_Y, AXIS_Z),
        App.Vector(1, 0, 0),
    )
    pressure_probe = Part.makeCylinder(
        1.9,
        36.0,
        App.Vector(barrel_end - 28.0, AXIS_Y, AXIS_Z - 1.0),
        App.Vector(0, 0, 1),
    )
    rupture_probe = Part.makeCylinder(
        2.9,
        36.0,
        App.Vector(barrel_end - 52.0, AXIS_Y, AXIS_Z - 1.0),
        App.Vector(0, 0, 1),
    )
    die_land_probe = Part.makeCylinder(
        p["die_bore_mm"] / 2 - 0.1,
        p["die_land_mm"],
        App.Vector(breaker.BoundBox.XMax + 21.0, AXIS_Y, AXIS_Z),
        App.Vector(1, 0, 0),
    )
    chord_error = p["screw_diameter_mm"] / 2 * (1 - cos(5 * pi / 180))
    heat_break = barrel_start - (THRUST_BEARING_X + p["thrust_bearing"]["height_mm"])
    barrel_region_vertices = [vertex.Point for vertex in screw.Vertexes if vertex.Point.x >= barrel_start - 1e-6]
    maximum_screw_radius = max(
        sqrt((point.y - AXIS_Y) ** 2 + (point.z - AXIS_Z) ** 2) for point in barrel_region_vertices
    )
    shoulder_probe = Part.makeCylinder(
        11.5,
        8.0,
        App.Vector(135.0, AXIS_Y, AXIS_Z),
        App.Vector(1, 0, 0),
    )

    checks = {
        "screw_barrel_vertex_envelope_clearance_mm": p["barrel_inner_diameter_mm"] / 2 - maximum_screw_radius,
        "maximum_screw_radius_in_barrel_mm": maximum_screw_radius,
        "screw_breaker_bbox_gap_mm": breaker.BoundBox.XMin - screw.BoundBox.XMax,
        "breaker_die_contact_mm": breaker.distToShape(die)[0],
        "thrust_bearing_shoulder_contact_mm": thrust.distToShape(shoulder_probe)[0],
        "thrust_bearing_support_contact_mm": thrust.distToShape(support)[0],
        "barrel_support_contact_mm": barrel.distToShape(support)[0],
        "drive_support_contact_mm": drive.distToShape(support)[0],
        "barrel_bore_probe_clearance_mm": bore_probe.distToShape(barrel)[0],
        "barrel_bore_probe_intersection_mm3": bore_probe.common(barrel).Volume,
        "pressure_port_probe_intersection_mm3": pressure_probe.common(barrel).Volume,
        "rupture_port_probe_intersection_mm3": rupture_probe.common(barrel).Volume,
        "die_land_probe_intersection_mm3": die_land_probe.common(die).Volume,
        "heater_insulation_contact_mm": heaters.distToShape(insulation)[0],
        "insulation_shield_air_gap_mm": insulation.distToShape(shield)[0],
        "flight_chord_error_mm": chord_error,
        "thrust_bearing_to_hot_barrel_mm": heat_break,
        "support_base_x_min_mm": support.BoundBox.XMin,
        "support_base_x_max_mm": support.BoundBox.XMax,
        "pressure_devices_x_max_mm": pressure_devices.BoundBox.XMax,
    }
    for shape in (screw, barrel, breaker, die, support, thrust, heaters, insulation, shield, drive, pressure_devices):
        assert shape.isValid(), shape.ShapeType
    assert checks["screw_barrel_vertex_envelope_clearance_mm"] >= p["screw_barrel_radial_clearance_mm"] - 0.002, checks
    assert checks["screw_breaker_bbox_gap_mm"] >= 1.99, checks
    assert checks["breaker_die_contact_mm"] < 1e-7, checks
    assert checks["thrust_bearing_shoulder_contact_mm"] < 1e-7, checks
    assert checks["thrust_bearing_support_contact_mm"] < 1e-7, checks
    assert checks["barrel_support_contact_mm"] < 1e-7, checks
    assert checks["drive_support_contact_mm"] < 1e-7, checks
    assert checks["barrel_bore_probe_intersection_mm3"] < 1e-6, checks
    assert checks["barrel_bore_probe_clearance_mm"] >= p["screw_barrel_radial_clearance_mm"] - 0.002, checks
    assert checks["pressure_port_probe_intersection_mm3"] < 1e-6, checks
    assert checks["rupture_port_probe_intersection_mm3"] < 1e-6, checks
    assert checks["die_land_probe_intersection_mm3"] < 1e-6, checks
    assert checks["heater_insulation_contact_mm"] < 1e-7, checks
    assert checks["insulation_shield_air_gap_mm"] >= p["shield_air_gap_mm"] - 0.01, checks
    assert checks["flight_chord_error_mm"] < p["screw_barrel_radial_clearance_mm"], checks
    assert checks["thrust_bearing_to_hot_barrel_mm"] >= p["minimum_thrust_heat_break_mm"], checks
    assert checks["support_base_x_min_mm"] <= p["base_origin_x_mm"] + 1e-7, checks
    assert checks["support_base_x_max_mm"] >= p["base_origin_x_mm"] + p["base_length_mm"] - 1e-7, checks
    assert checks["pressure_devices_x_max_mm"] <= p["base_origin_x_mm"] + p["base_length_mm"] + 1e-7, checks

    report = {
        "checks": {key: round(value, 6) for key, value in checks.items()},
        "status": "PASS",
        "limits": [
            "Rigid nominal geometry excludes machined runout, thermal differential growth, bending, wear and polymer wedging.",
            "Screw/barrel clearance is a complete B-rep vertex-envelope proof: the convex planar flight facets lie at or inside their 9 mm-radius vertices; an all-face boolean was rejected as too slow for repeatable CI.",
            "The flight uses 36 planar facets per turn; a smooth machined helix must preserve the dimensioned OD and measured clearance.",
            "Zero-distance bearing and clamp contacts are load-path envelopes, not fit/preload or fastener approval.",
            "The drive-support check proves only geometric contact to the cradle/pedestal; bolt patterns and vibration isolation remain supplier-dependent.",
            "Pressure and rupture probes only prove open ports; thread strength, diaphragm rating and relief discharge are unverified.",
        ],
    }
    path = ROOT / "simulation" / "extruder" / "geometry_clearance.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("EXTRUDER_GEOMETRY_OK")


if __name__ == "__main__":
    main()
