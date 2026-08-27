"""Parametric Stage-3 staggered granulator and flat-screen proof geometry."""

from __future__ import annotations

from math import sqrt

import FreeCAD as App
import Part


def center(params: dict) -> tuple[float, float]:
    p = params["plate"]
    return p["shaft_center_x_mm"], p["shaft_center_y_mm"]


def make_rotor(params: dict, phase_deg: float = 0.0):
    cx, cy = center(params)
    z0 = params["axial_layout"]["rotor_z_mm"]
    width = params["active_width_mm"]
    core_r = params["rotor_core_diameter_mm"] / 2
    outer_r = params["rotor_outer_diameter_mm"] / 2
    half_t = params["blade_tangential_thickness_mm"] / 2
    tip_x = sqrt(outer_r**2 - half_t**2)
    rotor = Part.makeCylinder(core_r, width, App.Vector(cx, cy, z0))
    rows = params["rotor_blade_rows"]
    segments = params["blade_axial_segments"]
    segment_width = width / segments
    for row in range(rows):
        for segment in range(segments):
            z = z0 + segment * segment_width
            profile = [
                App.Vector(cx + core_r - 0.2, cy - half_t, z),
                App.Vector(cx + tip_x, cy - half_t, z),
                App.Vector(cx + tip_x, cy + half_t, z),
                App.Vector(cx + core_r - 0.2, cy + half_t, z),
            ]
            blade = Part.Face(Part.makePolygon(profile + [profile[0]])).extrude(App.Vector(0, 0, segment_width))
            local_skew = -params["blade_total_skew_deg"] / 2 + segment * params["blade_total_skew_deg"] / (segments - 1)
            blade.rotate(App.Vector(cx, cy, z), App.Vector(0, 0, 1), phase_deg + row * 360 / rows + local_skew)
            rotor = rotor.fuse(blade)
    bore = Part.makeCylinder(params["shaft_diameter_mm"] / 2, width + 2, App.Vector(cx, cy, z0 - 1))
    slot_start = params["shaft_diameter_mm"] / 2 - 0.4
    keyway = Part.makeBox(
        params["keyway_radial_depth_mm"] + 1.0,
        params["key_width_mm"],
        width + 2,
        App.Vector(cx + slot_start, cy - params["key_width_mm"] / 2, z0 - 1),
    )
    keyway.rotate(App.Vector(cx, cy, z0), App.Vector(0, 0, 1), phase_deg)
    return rotor.cut(bore.fuse(keyway)).removeSplitter()


def make_shaft(params: dict):
    cx, cy = center(params)
    axial = params["axial_layout"]
    shaft = Part.makeCylinder(params["shaft_diameter_mm"] / 2, params["shaft_length_mm"], App.Vector(cx, cy, axial["shaft_start_z_mm"]))
    key = Part.makeBox(
        params["keyway_radial_depth_mm"],
        params["key_width_mm"],
        params["active_width_mm"],
        App.Vector(cx + params["shaft_diameter_mm"] / 2 - 0.4, cy - params["key_width_mm"] / 2, axial["rotor_z_mm"]),
    )
    return shaft.fuse(key)


def make_stator(params: dict):
    cx, cy = center(params)
    x0 = cx + params["rotor_outer_diameter_mm"] / 2 + params["blade_clearance_mm"]
    y0 = cy - params["stator_tangential_width_mm"] / 2
    z0 = params["axial_layout"]["rotor_z_mm"]
    shape = Part.makeBox(
        params["stator_radial_thickness_mm"],
        params["stator_tangential_width_mm"],
        params["active_width_mm"],
        App.Vector(x0, y0, z0),
    )
    for y in (cy - 4.0, cy + 4.0):
        for z in (z0 + 12.0, z0 + 36.0):
            hole = Part.makeCylinder(params["stator_bolt_diameter_mm"] / 2, params["stator_radial_thickness_mm"] + 2, App.Vector(x0 - 1, y, z), App.Vector(1, 0, 0))
            shape = shape.cut(hole)
    return shape.removeSplitter()


def make_carrier(params: dict):
    cx, cy = center(params)
    x0 = cx + params["rotor_outer_diameter_mm"] / 2 + params["blade_clearance_mm"] + params["stator_radial_thickness_mm"]
    y0 = cy - params["carrier_tangential_width_mm"] / 2
    z0 = params["axial_layout"]["carrier_z_mm"]
    shape = Part.makeBox(
        params["carrier_radial_thickness_mm"],
        params["carrier_tangential_width_mm"],
        params["active_width_mm"] + 4,
        App.Vector(x0, y0, z0),
    )
    rotor_z = params["axial_layout"]["rotor_z_mm"]
    for y in (cy - 4.0, cy + 4.0):
        for z in (rotor_z + 12.0, rotor_z + 36.0):
            hole = Part.makeCylinder(params["stator_bolt_diameter_mm"] / 2, params["carrier_radial_thickness_mm"] + 2, App.Vector(x0 - 1, y, z), App.Vector(1, 0, 0))
            shape = shape.cut(hole)
    return shape.removeSplitter()


def make_screen(params: dict, opening_mm: float):
    cx, cy = center(params)
    rotor_r = params["rotor_outer_diameter_mm"] / 2
    screen_width = params["rotor_outer_diameter_mm"] + 10.0
    x0 = cx - screen_width / 2
    y_top = cy - rotor_r - params["screen_rotor_gap_mm"]
    y0 = y_top - params["screen_thickness_mm"]
    z0 = params["axial_layout"]["screen_z_mm"]
    shape = Part.makeBox(screen_width, params["screen_thickness_mm"], params["active_width_mm"], App.Vector(x0, y0, z0))
    pitch = params["screen_pitch_mm"]
    margin_x = params["screen_edge_margin_x_mm"]
    margin_z = params["screen_edge_margin_z_mm"]
    x = x0 + margin_x
    while x <= x0 + screen_width - margin_x + 1e-9:
        z = z0 + margin_z
        while z <= z0 + params["active_width_mm"] - margin_z + 1e-9:
            hole = Part.makeCylinder(opening_mm / 2, params["screen_thickness_mm"] + 2, App.Vector(x, y0 - 1, z), App.Vector(0, 1, 0))
            shape = shape.cut(hole)
            z += pitch
        x += pitch
    return shape.removeSplitter()


def make_plate(params: dict, z: float, counterbore_from_low: bool):
    p = params["plate"]
    cx, cy = center(params)
    shape = Part.makeBox(p["width_mm"], p["height_mm"], p["thickness_mm"], App.Vector(0, 0, z))
    shape = shape.cut(Part.makeCylinder(p["through_bore_mm"] / 2, p["thickness_mm"] + 2, App.Vector(cx, cy, z - 1)))
    cb_z = z if counterbore_from_low else z + p["thickness_mm"] - p["counterbore_depth_mm"]
    shape = shape.cut(Part.makeCylinder(p["counterbore_mm"] / 2, p["counterbore_depth_mm"], App.Vector(cx, cy, cb_z)))
    for x, y in ((8, 8), (92, 8), (8, 82), (92, 82)):
        shape = shape.cut(Part.makeCylinder(p["frame_hole_mm"] / 2, p["thickness_mm"] + 2, App.Vector(x, y, z - 1)))
    for x, y in ((cx - 24, cy), (cx + 24, cy), (cx, cy - 24), (cx, cy + 24)):
        shape = shape.cut(Part.makeCylinder(p["retainer_hole_mm"] / 2, p["thickness_mm"] + 2, App.Vector(x, y, z - 1)))
    return shape.removeSplitter()


def make_bearing(params: dict, z: float):
    cx, cy = center(params)
    b = params["bearing"]
    return Part.makeCylinder(b["outer_diameter_mm"] / 2, b["width_mm"], App.Vector(cx, cy, z)).cut(
        Part.makeCylinder(b["bore_mm"] / 2, b["width_mm"] + 2, App.Vector(cx, cy, z - 1))
    )


def make_retainer(params: dict, z: float):
    cx, cy = center(params)
    ring = Part.makeCylinder(28.0, 3.0, App.Vector(cx, cy, z)).cut(Part.makeCylinder(16.5, 5.0, App.Vector(cx, cy, z - 1)))
    for x, y in ((cx - 24, cy), (cx + 24, cy), (cx, cy - 24), (cx, cy + 24)):
        ring = ring.cut(Part.makeCylinder(2.25, 5.0, App.Vector(x, y, z - 1)))
    return ring.removeSplitter()
