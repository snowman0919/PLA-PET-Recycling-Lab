"""Parametric two-deck vibratory sorter proof geometry."""

from __future__ import annotations

from math import cos, radians, sin

import FreeCAD as App
import Part


def _place_on_tray(shape, params: dict):
    shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), -params["tray_slope_deg"])
    shape.translate(
        App.Vector(
            params["tray_origin_x_mm"],
            params["tray_origin_y_mm"],
            params["tray_origin_z_mm"],
        )
    )
    return shape


def make_base(params: dict):
    return Part.makeBox(
        params["base_length_mm"],
        params["base_width_mm"],
        params["base_thickness_mm"],
    )


def make_screen_cassette(params: dict, aperture_mm: float, pitch_mm: float, deck_z_mm: float):
    length = params["screen_outer_length_mm"]
    width = params["screen_outer_width_mm"]
    border_x = params["screen_border_x_mm"]
    border_y = params["screen_border_y_mm"]
    thickness = params["screen_thickness_mm"]
    wire = pitch_mm - aperture_mm
    if wire <= 0:
        raise ValueError("screen pitch must exceed aperture")

    parts = [
        Part.makeBox(length, border_y, thickness, App.Vector(8, 6, deck_z_mm)),
        Part.makeBox(length, border_y, thickness, App.Vector(8, 6 + width - border_y, deck_z_mm)),
        Part.makeBox(border_x, width - 2 * border_y, thickness, App.Vector(8, 6 + border_y, deck_z_mm)),
        Part.makeBox(border_x, width - 2 * border_y, thickness, App.Vector(8 + length - border_x, 6 + border_y, deck_z_mm)),
    ]
    x = 8 + border_x
    while x <= 8 + length - border_x + 1e-9:
        parts.append(Part.makeBox(wire, width - 2 * border_y, thickness, App.Vector(x, 6 + border_y, deck_z_mm)))
        x += pitch_mm
    y = 6 + border_y
    while y <= 6 + width - border_y + 1e-9:
        parts.append(Part.makeBox(length - 2 * border_x, wire, thickness, App.Vector(8 + border_x, y, deck_z_mm)))
        y += pitch_mm
    return _place_on_tray(Part.makeCompound(parts), params)


def make_tray_frame(params: dict):
    length = params["tray_length_mm"]
    width = params["tray_outer_width_mm"]
    spacing = params["deck_spacing_mm"]
    parts = [
        Part.makeBox(length, 5, 44, App.Vector(0, 0, -spacing - 5)),
        Part.makeBox(length, 5, 44, App.Vector(0, width - 5, -spacing - 5)),
        Part.makeBox(12, width, 5, App.Vector(0, 0, -spacing - 5)),
        Part.makeBox(12, width, 5, App.Vector(length - 12, 0, -spacing - 5)),
        Part.makeBox(length, 8, 4, App.Vector(0, 12, -spacing - 4)),
        Part.makeBox(length, 8, 4, App.Vector(0, width - 20, -spacing - 4)),
    ]
    return _place_on_tray(Part.makeCompound(parts), params)


def make_service_clamp(params: dict):
    block = Part.makeBox(28, 18, 8)
    hole = Part.makeCylinder(2.75, 10, App.Vector(20, 9, -1))
    return block.cut(hole).removeSplitter()


def make_clamps(params: dict):
    spacing = params["deck_spacing_mm"]
    clamp = make_service_clamp(params)
    parts = []
    for x in (12.0, params["tray_length_mm"] - 40.0):
        for z in (2.0, -spacing + 2.0):
            item = clamp.copy()
            item.translate(App.Vector(x, -8, z))
            parts.append(item)
    return _place_on_tray(Part.makeCompound(parts), params)


def make_isolators(params: dict):
    base_z = params["base_thickness_mm"]
    slope = radians(params["tray_slope_deg"])
    origin_x = params["tray_origin_x_mm"]
    origin_z = params["tray_origin_z_mm"]
    spacing = params["deck_spacing_mm"]
    parts = []
    for x, y in params["isolator_positions_mm"]:
        local_x = x - origin_x
        rail_bottom_z = origin_z - local_x * sin(slope) + (-spacing - 4) * cos(slope)
        rubber_top_z = rail_bottom_z - 1.0
        height = max(12.0, rubber_top_z - base_z)
        rubber = Part.makeCylinder(9.0, height, App.Vector(x, y, base_z))
        stud = Part.makeCylinder(3.0, 10.0, App.Vector(x, y, rubber_top_z))
        parts.extend([rubber, stud])
    return Part.makeCompound(parts)


def make_motor(params: dict):
    motor = Part.makeCylinder(22.0, 70.0, App.Vector(90, 35, -45), App.Vector(0, 1, 0))
    shaft = Part.makeCylinder(4.0, 88.0, App.Vector(90, 26, -45), App.Vector(0, 1, 0))
    return _place_on_tray(motor.fuse(shaft).removeSplitter(), params)


def make_eccentric(params: dict):
    radius = 18.0
    offset = params["eccentric_radius_mm"]
    disc = Part.makeCylinder(radius, 8.0, App.Vector(90 + offset, 105, -45), App.Vector(0, 1, 0))
    bore = Part.makeCylinder(4.0, 10.0, App.Vector(90, 104, -45), App.Vector(0, 1, 0))
    return _place_on_tray(disc.cut(bore).removeSplitter(), params)


def make_motor_bracket(params: dict):
    parts = [
        Part.makeBox(80, 80, 5, App.Vector(50, 30, -72)),
        Part.makeBox(80, 5, 34, App.Vector(50, 5, -67)),
        Part.makeBox(80, 5, 34, App.Vector(50, 130, -67)),
        Part.makeBox(6, 25, 30, App.Vector(50, 10, -67)),
        Part.makeBox(6, 25, 30, App.Vector(124, 10, -67)),
        Part.makeBox(6, 25, 30, App.Vector(50, 105, -67)),
        Part.makeBox(6, 25, 30, App.Vector(124, 105, -67)),
    ]
    return _place_on_tray(Part.makeCompound(parts), params)


def make_outlets(params: dict):
    spacing = params["deck_spacing_mm"]
    oversize = Part.makeBox(68, 42, 3, App.Vector(params["tray_length_mm"] - 4, 0, 0))
    acceptable = Part.makeBox(68, 70, 3, App.Vector(params["tray_length_mm"] - 4, 52, -spacing))
    return _place_on_tray(Part.makeCompound([oversize, acceptable]), params)


def make_fines_bin(params: dict):
    x0, y0, z0 = 145.0, 52.0, 5.0
    length, width, height, wall = 120.0, 76.0, 28.0, 3.0
    return Part.makeCompound(
        [
            Part.makeBox(length, width, wall, App.Vector(x0, y0, z0)),
            Part.makeBox(length, wall, height, App.Vector(x0, y0, z0)),
            Part.makeBox(length, wall, height, App.Vector(x0, y0 + width - wall, z0)),
            Part.makeBox(wall, width, height, App.Vector(x0, y0, z0)),
            Part.makeBox(wall, width, height, App.Vector(x0 + length - wall, y0, z0)),
        ]
    )
