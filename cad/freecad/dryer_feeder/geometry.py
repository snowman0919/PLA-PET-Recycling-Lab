"""Parametric high-temperature dryer hopper and metering feeder proof."""

from __future__ import annotations

import FreeCAD as App
import Part


CX, CY = 150.0, 130.0
CONE_BOTTOM_Z = 112.0


def _ring(outer_r: float, inner_r: float, height: float, z: float):
    outer = Part.makeCylinder(outer_r, height, App.Vector(CX, CY, z))
    inner = Part.makeCylinder(inner_r, height + 2, App.Vector(CX, CY, z - 1))
    return outer.cut(inner)


def make_hopper(params: dict):
    inner_r = params["hopper_inner_diameter_mm"] / 2
    wall = params["hopper_wall_mm"]
    cone_h = params["hopper_cone_height_mm"]
    outlet_r = params["hopper_outlet_diameter_mm"] / 2
    cylinder_z = CONE_BOTTOM_Z + cone_h
    cylinder = _ring(inner_r + wall, inner_r, params["hopper_active_height_mm"], cylinder_z)
    outer_cone = Part.makeCone(outlet_r + wall, inner_r + wall, cone_h, App.Vector(CX, CY, CONE_BOTTOM_Z))
    inner_cone = Part.makeCone(outlet_r, inner_r, cone_h + 2, App.Vector(CX, CY, CONE_BOTTOM_Z - 1))
    cone = outer_cone.cut(inner_cone)
    outlet = _ring(outlet_r + wall, outlet_r, 24.0, CONE_BOTTOM_Z - 24.0)
    return cylinder.fuse(cone).fuse(outlet).removeSplitter()


def make_insulation(params: dict):
    inner_r = params["hopper_inner_diameter_mm"] / 2 + params["hopper_wall_mm"]
    outer_r = inner_r + params["insulation_thickness_mm"]
    z = CONE_BOTTOM_Z + params["hopper_cone_height_mm"]
    return _ring(outer_r, inner_r, params["hopper_active_height_mm"], z).removeSplitter()


def make_heat_shield(params: dict):
    hopper_outer = params["hopper_inner_diameter_mm"] / 2 + params["hopper_wall_mm"] + params["insulation_thickness_mm"]
    inner_r = hopper_outer + params["shield_air_gap_mm"]
    z = CONE_BOTTOM_Z + params["hopper_cone_height_mm"] - 12
    height = params["hopper_active_height_mm"] + 24
    shell = _ring(inner_r + params["shield_thickness_mm"], inner_r, height, z)
    # Four vertical ventilation slots are proof cut-outs, not a final perforation pattern.
    for angle in (0, 90, 180, 270):
        slot = Part.makeBox(18, 8, 120, App.Vector(CX + inner_r - 4, CY - 4, z + 20))
        slot.rotate(App.Vector(CX, CY, z), App.Vector(0, 0, 1), angle)
        shell = shell.cut(slot)
    return shell.removeSplitter()


def make_lid(params: dict):
    inner_r = params["hopper_inner_diameter_mm"] / 2
    z = CONE_BOTTOM_Z + params["hopper_cone_height_mm"] + params["hopper_active_height_mm"]
    lid = Part.makeCylinder(inner_r + 15, 4, App.Vector(CX, CY, z))
    lid = lid.cut(Part.makeCylinder(6, 6, App.Vector(CX, CY, z - 1)))
    return lid.removeSplitter()


def make_agitator(params: dict, phase_deg: float = 0.0):
    shaft_r = params["agitator_shaft_diameter_mm"] / 2
    shaft = Part.makeCylinder(shaft_r, params["hopper_active_height_mm"] + params["hopper_cone_height_mm"] + 34, App.Vector(CX, CY, CONE_BOTTOM_Z - 10))
    paddle_r = params["agitator_paddle_radius_mm"]
    parts = [shaft]
    for index, z in enumerate((245.0, 335.0, 425.0)):
        paddle = Part.makeBox(paddle_r * 2, 8, 4, App.Vector(CX - paddle_r, CY - 4, z))
        paddle.rotate(App.Vector(CX, CY, z), App.Vector(0, 0, 1), phase_deg + index * 60)
        parts.append(paddle)
    return Part.makeCompound(parts)


def make_gates(params: dict):
    throat = params["hopper_outlet_diameter_mm"]
    gate1 = Part.makeBox(78, 52, 4, App.Vector(CX - 39, CY - 26, CONE_BOTTOM_Z - 31))
    gate2 = Part.makeBox(78, 52, 4, App.Vector(CX - 39, CY - 26, CONE_BOTTOM_Z - 43))
    bore1 = Part.makeCylinder(throat / 2, 6, App.Vector(CX, CY, CONE_BOTTOM_Z - 32))
    bore2 = Part.makeCylinder(throat / 2, 6, App.Vector(CX, CY, CONE_BOTTOM_Z - 44))
    return Part.makeCompound([gate1.cut(bore1), gate2.cut(bore2)])


def make_auger(params: dict, phase_deg: float = 0.0):
    length = params["auger_length_mm"]
    x0 = CX - length / 2
    z = 58.0
    shaft_r = params["auger_shaft_diameter_mm"] / 2
    outer_r = params["auger_outer_diameter_mm"] / 2
    shaft = Part.makeCylinder(shaft_r, length, App.Vector(x0, CY, z), App.Vector(1, 0, 0))
    parts = [shaft]
    x = x0 + 8
    while x <= x0 + length - 8 + 1e-9:
        flight = Part.makeCylinder(outer_r, 2.0, App.Vector(x, CY, z), App.Vector(1, 0, 0)).cut(
            Part.makeCylinder(shaft_r, 4.0, App.Vector(x - 1, CY, z), App.Vector(1, 0, 0))
        )
        flight.rotate(App.Vector(x, CY, z), App.Vector(1, 0, 0), phase_deg + (x - x0) / params["auger_pitch_mm"] * 360)
        parts.append(flight)
        x += params["auger_pitch_mm"] / 2
    return Part.makeCompound(parts)


def make_auger_housing(params: dict):
    length = params["auger_length_mm"] + 16
    x0 = CX - length / 2
    z = 58.0
    inner_r = params["auger_housing_inner_diameter_mm"] / 2
    outer_r = inner_r + params["auger_housing_wall_mm"]
    outer = Part.makeCylinder(outer_r, length, App.Vector(x0, CY, z), App.Vector(1, 0, 0))
    inner = Part.makeCylinder(inner_r, length + 2, App.Vector(x0 - 1, CY, z), App.Vector(1, 0, 0))
    inlet = Part.makeCylinder(params["hopper_outlet_diameter_mm"] / 2 + 3, 42, App.Vector(CX, CY, z), App.Vector(0, 0, 1))
    inlet_bore = Part.makeCylinder(params["hopper_outlet_diameter_mm"] / 2, 44, App.Vector(CX, CY, z - 1), App.Vector(0, 0, 1))
    outlet_x = x0 + length - 22
    outlet = Part.makeCylinder(inner_r + 3, 42, App.Vector(outlet_x, CY, z - 42))
    outlet_bore = Part.makeCylinder(inner_r, 44, App.Vector(outlet_x, CY, z - 43))
    outer_union = outer.fuse(inlet).fuse(outlet)
    bore_union = inner.fuse(inlet_bore).fuse(outlet_bore)
    return outer_union.cut(bore_union).removeSplitter()


def make_drive_and_air_system(params: dict):
    length = params["auger_length_mm"]
    motor = Part.makeBox(42, 42, 42, App.Vector(CX - length / 2 - 50, CY - 21, 37))
    blower = Part.makeBox(64, 52, 52, App.Vector(248, 18, 174))
    desiccant1 = Part.makeCylinder(24, 100, App.Vector(272, 104, 150))
    desiccant2 = Part.makeCylinder(24, 100, App.Vector(272, 170, 150))
    heater = Part.makeBox(58, 44, 44, App.Vector(245, 82, 272))
    return Part.makeCompound([motor, blower, desiccant1, desiccant2, heater])


def make_base_and_load_cells(params: dict):
    base_t = params["base_thickness_mm"]
    base = Part.makeBox(params["base_length_mm"], params["base_width_mm"], base_t)
    cells = [
        Part.makeBox(50, 14, 8, App.Vector(x, y, base_t))
        for x, y in params["load_cell_positions_mm"]
    ]

    # A three-point metal frame makes the nominal hopper/auger load path visible:
    # each post starts on a load-cell envelope and the two cross rails touch the
    # auger housing at its lower tangent plane.  Joint plates and fasteners remain
    # fabrication-detail work, so the shapes intentionally stay as an envelope.
    top_z = params["support_frame_top_z_mm"]
    post_h = top_z - (base_t + 8)
    post_xy = [(80.0, 52.0), (260.0, 52.0), (170.0, 222.0)]
    posts = [Part.makeBox(12, 12, post_h, App.Vector(x - 6, y - 6, base_t + 8)) for x, y in post_xy]
    front_rail = Part.makeBox(220, 12, 4, App.Vector(40, 46, top_z - 4))
    rear_rail = Part.makeBox(220, 12, 4, App.Vector(40, 216, top_z - 4))
    cross_left = Part.makeBox(12, 182, 4, App.Vector(60, 46, top_z - 4))
    cross_right = Part.makeBox(12, 182, 4, App.Vector(228, 46, top_z - 4))
    return Part.makeCompound([base, *cells, *posts, front_rail, rear_rail, cross_left, cross_right])
