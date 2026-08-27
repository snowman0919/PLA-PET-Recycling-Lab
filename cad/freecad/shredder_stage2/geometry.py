"""Parametric Stage-2 single-shaft rotor and fixed bed-knife geometry."""

from __future__ import annotations

from math import atan2, degrees, sqrt

import FreeCAD as App
import Part


def center(params: dict) -> tuple[float, float]:
    plate = params["plate"]
    return plate["shaft_center_x_mm"], plate["shaft_center_y_mm"]


def make_rotor(params: dict, z: float | None = None, phase_deg: float = 0.0):
    cx, cy = center(params)
    z = params["axial_layout"]["rotor_z_mm"] if z is None else z
    width = params["active_width_mm"]
    core_r = params["rotor_core_diameter_mm"] / 2
    outer_r = params["rotor_outer_diameter_mm"] / 2
    half_t = params["blade_tangential_thickness_mm"] / 2
    tip_x = sqrt(outer_r**2 - half_t**2)
    root_x = core_r - 0.2
    rotor = Part.makeCylinder(core_r, width, App.Vector(cx, cy, z))
    pitch = 360.0 / params["rotor_blade_count"]
    segments = params["blade_axial_segments"]
    segment_width = width / segments
    skew = params["blade_total_skew_deg"]
    for blade_index in range(params["rotor_blade_count"]):
        for segment_index in range(segments):
            segment_z = z + segment_index * segment_width
            profile = [
                App.Vector(cx + root_x, cy - half_t, segment_z),
                App.Vector(cx + tip_x, cy - half_t, segment_z),
                App.Vector(cx + tip_x, cy + half_t, segment_z),
                App.Vector(cx + root_x, cy + half_t, segment_z),
            ]
            blade = Part.Face(Part.makePolygon(profile + [profile[0]])).extrude(App.Vector(0, 0, segment_width))
            local_skew = -skew / 2 + segment_index * skew / (segments - 1)
            blade.rotate(
                App.Vector(cx, cy, segment_z),
                App.Vector(0, 0, 1),
                phase_deg + blade_index * pitch + local_skew,
            )
            rotor = rotor.fuse(blade)
    bore = Part.makeCylinder(params["shaft_diameter_mm"] / 2, width + 2, App.Vector(cx, cy, z - 1))
    key_width = params["key_width_mm"]
    slot_start = params["shaft_diameter_mm"] / 2 - 0.4
    keyway = Part.makeBox(
        params["keyway_radial_depth_mm"] + 1.0,
        key_width,
        width + 2,
        App.Vector(cx + slot_start, cy - key_width / 2, z - 1),
    )
    keyway.rotate(App.Vector(cx, cy, z), App.Vector(0, 0, 1), phase_deg)
    return rotor.cut(bore.fuse(keyway)).removeSplitter()


def make_shaft(params: dict):
    cx, cy = center(params)
    axial = params["axial_layout"]
    shaft = Part.makeCylinder(
        params["shaft_diameter_mm"] / 2,
        params["shaft_length_mm"],
        App.Vector(cx, cy, axial["shaft_start_z_mm"]),
    )
    key = Part.makeBox(
        params["keyway_radial_depth_mm"],
        params["key_width_mm"],
        params["active_width_mm"],
        App.Vector(
            cx + params["shaft_diameter_mm"] / 2 - 0.4,
            cy - params["key_width_mm"] / 2,
            axial["rotor_z_mm"],
        ),
    )
    return shaft.fuse(key)


def make_bed_knife(params: dict):
    cx, cy = center(params)
    outer_r = params["rotor_outer_diameter_mm"] / 2
    x0 = cx + outer_r + params["blade_clearance_mm"]
    y0 = cy - params["bed_knife_tangential_width_mm"] / 2
    z0 = params["axial_layout"]["rotor_z_mm"]
    knife = Part.makeBox(
        params["bed_knife_radial_thickness_mm"],
        params["bed_knife_tangential_width_mm"],
        params["active_width_mm"],
        App.Vector(x0, y0, z0),
    )
    for y in (cy - 5.0, cy + 5.0):
        for z in (z0 + 16.0, z0 + 48.0):
            hole = Part.makeCylinder(
                params["bed_knife_bolt_diameter_mm"] / 2,
                params["bed_knife_radial_thickness_mm"] + 2,
                App.Vector(x0 - 1, y, z),
                App.Vector(1, 0, 0),
            )
            knife = knife.cut(hole)
    return knife.removeSplitter()


def make_carrier(params: dict):
    cx, cy = center(params)
    outer_r = params["rotor_outer_diameter_mm"] / 2
    x0 = cx + outer_r + params["blade_clearance_mm"] + params["bed_knife_radial_thickness_mm"]
    y0 = cy - params["carrier_tangential_width_mm"] / 2
    z0 = params["axial_layout"]["carrier_z_mm"]
    carrier = Part.makeBox(
        params["carrier_radial_thickness_mm"],
        params["carrier_tangential_width_mm"],
        params["active_width_mm"] + 4.0,
        App.Vector(x0, y0, z0),
    )
    for y in (cy - 5.0, cy + 5.0):
        rotor_z = params["axial_layout"]["rotor_z_mm"]
        for z in (rotor_z + 16.0, rotor_z + 48.0):
            hole = Part.makeCylinder(
                params["bed_knife_bolt_diameter_mm"] / 2,
                params["carrier_radial_thickness_mm"] + 2,
                App.Vector(x0 - 1, y, z),
                App.Vector(1, 0, 0),
            )
            carrier = carrier.cut(hole)
    return carrier.removeSplitter()


def make_plate(params: dict, z: float, counterbore_from_low_z: bool):
    plate = params["plate"]
    cx, cy = center(params)
    shape = Part.makeBox(plate["width_mm"], plate["height_mm"], plate["thickness_mm"], App.Vector(0, 0, z))
    through = Part.makeCylinder(plate["through_bore_mm"] / 2, plate["thickness_mm"] + 2, App.Vector(cx, cy, z - 1))
    shape = shape.cut(through)
    cb_z = z if counterbore_from_low_z else z + plate["thickness_mm"] - plate["counterbore_depth_mm"]
    counterbore = Part.makeCylinder(plate["counterbore_mm"] / 2, plate["counterbore_depth_mm"], App.Vector(cx, cy, cb_z))
    shape = shape.cut(counterbore)
    for x, y in ((10, 10), (100, 10), (10, 90), (100, 90)):
        shape = shape.cut(Part.makeCylinder(plate["frame_hole_mm"] / 2, plate["thickness_mm"] + 2, App.Vector(x, y, z - 1)))
    for x, y in ((cx - 25, cy), (cx + 25, cy), (cx, cy - 25), (cx, cy + 25)):
        shape = shape.cut(Part.makeCylinder(plate["retainer_hole_mm"] / 2, plate["thickness_mm"] + 2, App.Vector(x, y, z - 1)))
    return shape.removeSplitter()


def make_bearing(params: dict, z: float):
    cx, cy = center(params)
    bearing = params["bearing"]
    outer = Part.makeCylinder(bearing["outer_diameter_mm"] / 2, bearing["width_mm"], App.Vector(cx, cy, z))
    inner = Part.makeCylinder(bearing["bore_mm"] / 2, bearing["width_mm"] + 2, App.Vector(cx, cy, z - 1))
    return outer.cut(inner)


def make_retainer(params: dict, z: float):
    cx, cy = center(params)
    ring = Part.makeCylinder(30.0, 3.0, App.Vector(cx, cy, z))
    ring = ring.cut(Part.makeCylinder(18.0, 5.0, App.Vector(cx, cy, z - 1)))
    for x, y in ((cx - 25, cy), (cx + 25, cy), (cx, cy - 25), (cx, cy + 25)):
        ring = ring.cut(Part.makeCylinder(2.25, 5.0, App.Vector(x, y, z - 1)))
    return ring.removeSplitter()


def blade_tip_half_angle_deg(params: dict) -> float:
    return degrees(atan2(params["blade_tangential_thickness_mm"] / 2, params["rotor_outer_diameter_mm"] / 2))
