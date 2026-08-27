"""Parametric Stage-1 cutter, spacer, shaft, bearing and plate geometry."""

from __future__ import annotations

from math import cos, pi, sin

import FreeCAD as App
import Part


def polar(center, radius: float, degrees: float, z: float):
    angle = degrees * pi / 180
    return App.Vector(center[0] + radius * cos(angle), center[1] + radius * sin(angle), z)


def make_cutter(params: dict, center=(0.0, 0.0), z=0.0, phase_deg=0.0):
    outer_r = params["cutter_outer_diameter_mm"] / 2
    root_r = params["cutter_root_diameter_mm"] / 2
    thickness = params["cutter_thickness_mm"]
    teeth = int(params["cutter_teeth"])
    tip_land = params["tip_land_angle_deg"]
    shape = Part.makeCylinder(root_r, thickness, App.Vector(center[0], center[1], z))
    pitch = 360 / teeth
    for index in range(teeth):
        angle = phase_deg + index * pitch
        points = [
            polar(center, root_r - 0.4, angle - 18, z),
            polar(center, root_r + 3.0, angle - 12, z),
            polar(center, outer_r, angle - 3.5, z),
            polar(center, outer_r, angle - 3.5 + tip_land, z),
            polar(center, outer_r - 3.0, angle + 7, z),
            polar(center, root_r + 1.0, angle + 16, z),
            polar(center, root_r - 0.4, angle + 20, z),
        ]
        wire = Part.makePolygon(points + [points[0]])
        tooth = Part.Face(wire).extrude(App.Vector(0, 0, thickness))
        shape = shape.fuse(tooth)
    bore = Part.makeCylinder(params["shaft_diameter_mm"] / 2, thickness + 2, App.Vector(center[0], center[1], z - 1))
    shape = shape.cut(bore)
    key_width = params["key_width_mm"]
    slot_start = params["shaft_diameter_mm"] / 2 - 0.4
    keyway = Part.makeBox(
        params["keyway_radial_depth_mm"] + 1.0,
        key_width,
        thickness + 2,
        App.Vector(center[0] + slot_start, center[1] - key_width / 2, z - 1),
    )
    if phase_deg:
        keyway.rotate(App.Vector(center[0], center[1], z), App.Vector(0, 0, 1), phase_deg)
    return shape.cut(keyway).removeSplitter()


def make_spacer(params: dict, center=(0.0, 0.0), z=0.0):
    thickness = params["spacer_thickness_mm"]
    outer = Part.makeCylinder(params["spacer_outer_diameter_mm"] / 2, thickness, App.Vector(center[0], center[1], z))
    bore = Part.makeCylinder(params["shaft_diameter_mm"] / 2 + 0.1, thickness + 2, App.Vector(center[0], center[1], z - 1))
    return outer.cut(bore)


def make_shaft(params: dict, center=(0.0, 0.0), z=-30.0, phase_deg=0.0):
    shaft = Part.makeCylinder(params["shaft_diameter_mm"] / 2, params["shaft_length_mm"], App.Vector(center[0], center[1], z))
    key_height = params["keyway_radial_depth_mm"]
    key = Part.makeBox(
        key_height,
        params["key_width_mm"],
        params["active_width_mm"],
        App.Vector(center[0] + params["shaft_diameter_mm"] / 2 - 0.4, center[1] - params["key_width_mm"] / 2, 0),
    )
    if phase_deg:
        key.rotate(App.Vector(center[0], center[1], 0), App.Vector(0, 0, 1), phase_deg)
    return shaft.fuse(key), key


def make_bearing(params: dict, center, z: float):
    bearing = params["bearing"]
    outer = Part.makeCylinder(bearing["outer_diameter_mm"] / 2, bearing["width_mm"], App.Vector(center[0], center[1], z))
    inner = Part.makeCylinder(bearing["bore_mm"] / 2, bearing["width_mm"] + 2, App.Vector(center[0], center[1], z - 1))
    return outer.cut(inner)


def make_plate(params: dict, z: float, counterbore_from_low_z: bool):
    plate = params["plate"]
    shape = Part.makeBox(plate["width_mm"], plate["height_mm"], plate["thickness_mm"], App.Vector(0, 0, z))
    centers = ((50.0, 60.0), (100.0, 60.0))
    for center in centers:
        through = Part.makeCylinder(plate["through_bore_mm"] / 2, plate["thickness_mm"] + 2, App.Vector(center[0], center[1], z - 1))
        shape = shape.cut(through)
        cb_z = z if counterbore_from_low_z else z + plate["thickness_mm"] - plate["counterbore_depth_mm"]
        counterbore = Part.makeCylinder(plate["counterbore_mm"] / 2, plate["counterbore_depth_mm"], App.Vector(center[0], center[1], cb_z))
        shape = shape.cut(counterbore)
    for x, y in ((50, 35), (50, 85), (100, 35), (100, 85)):
        hole = Part.makeCylinder(plate["retainer_hole_mm"] / 2, plate["thickness_mm"] + 2, App.Vector(x, y, z - 1))
        shape = shape.cut(hole)
    for x, y in ((12, 12), (138, 12), (12, 108), (138, 108)):
        hole = Part.makeCylinder(plate["frame_hole_mm"] / 2, plate["thickness_mm"] + 2, App.Vector(x, y, z - 1))
        shape = shape.cut(hole)
    return shape.removeSplitter()


def make_retainer(params: dict, z: float):
    shape = Part.makeBox(100.0, 60.0, 3.0, App.Vector(25.0, 30.0, z))
    for center in ((50.0, 60.0), (100.0, 60.0)):
        inner = Part.makeCylinder(18.0, 5.0, App.Vector(center[0], center[1], z - 1))
        shape = shape.cut(inner)
    for x, y in ((50, 35), (50, 85), (100, 35), (100, 85)):
        hole = Part.makeCylinder(2.25, 5.0, App.Vector(x, y, z - 1))
        shape = shape.cut(hole)
    return shape


def make_timing_envelope(params: dict, center, z: float):
    radius = params["timing_pitch_envelope_diameter_mm"] / 2
    bore = params["shaft_diameter_mm"] / 2
    width = params["timing_envelope_width_mm"]
    outer = Part.makeCylinder(radius, width, App.Vector(center[0], center[1], z))
    inner = Part.makeCylinder(bore, width + 2, App.Vector(center[0], center[1], z - 1))
    return outer.cut(inner)


def make_coupling_envelope(params: dict, center, z: float):
    outer = Part.makeCylinder(15.0, 25.0, App.Vector(center[0], center[1], z))
    inner = Part.makeCylinder(params["shaft_diameter_mm"] / 2, 27.0, App.Vector(center[0], center[1], z - 1))
    return outer.cut(inner)
