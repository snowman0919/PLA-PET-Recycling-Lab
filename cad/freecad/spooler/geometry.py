"""Parametric 1 kg spool, dancer and traverse proof geometry."""

from __future__ import annotations

from math import cos, radians, sin, sqrt

import FreeCAD as App
import Part


SPOOL_X = 230.0
SPOOL_Y = 120.0
SPOOL_Z = 170.0
DANCER_PIVOT_X = 60.0
DANCER_PIVOT_Z = 230.0
BEARING_ORIGINS_Y = (63.5, 168.5)


def _axis_y_cylinder(radius: float, length: float, x: float, y: float, z: float):
    return Part.makeCylinder(radius, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def _axis_y_ring(outer_r: float, inner_r: float, length: float, x: float, y: float, z: float):
    return _axis_y_cylinder(outer_r, length, x, y, z).cut(_axis_y_cylinder(inner_r, length + 2, x, y - 1, z))


def make_spool_reference(params: dict):
    width = params["maximum_spool_width_mm"]
    radius = params["maximum_spool_outer_diameter_mm"] / 2
    y0 = SPOOL_Y - width / 2
    flange_t = 4.0
    core_outer = params["minimum_supported_core_diameter_mm"] / 2
    core_inner = 25.0
    core = _axis_y_ring(core_outer, core_inner, width - 2 * flange_t, SPOOL_X, y0 + flange_t, SPOOL_Z)
    flanges = [
        _axis_y_ring(radius, core_inner, flange_t, SPOOL_X, y0, SPOOL_Z),
        _axis_y_ring(radius, core_inner, flange_t, SPOOL_X, y0 + width - flange_t, SPOOL_Z),
    ]
    return Part.makeCompound([core, *flanges])


def make_spool_shaft(params: dict):
    return _axis_y_cylinder(params["shaft_diameter_mm"] / 2, 160.0, SPOOL_X, 40.0, SPOOL_Z)


def make_spool_bearings(params: dict):
    return Part.makeCompound([
        _axis_y_ring(14.0, params["shaft_diameter_mm"] / 2, 8.0, SPOOL_X, y, SPOOL_Z)
        for y in BEARING_ORIGINS_Y
    ])


def _bearing_plate(y: float):
    plate = Part.makeBox(140.0, 17.0, 250.0, App.Vector(160.0, y, 6.0))
    seat = _axis_y_cylinder(14.0, 19.0, SPOOL_X, y - 1.0, SPOOL_Z)
    frame_holes = None
    for x in (175.0, 285.0):
        hole = _axis_y_cylinder(4.5, 19.0, x, y - 1.0, 22.0)
        frame_holes = hole if frame_holes is None else frame_holes.fuse(hole)
    return plate.cut(seat.fuse(frame_holes)).removeSplitter()


def make_spooler_frame(params: dict):
    base = Part.makeBox(
        params["base_length_mm"],
        params["base_width_mm"],
        6.0,
        App.Vector(params["base_origin_x_mm"], 0.0, 0.0),
    )
    left = _bearing_plate(55.0)
    right = _bearing_plate(168.0)
    rails = [Part.makeBox(320.0, 20.0, 20.0, App.Vector(10.0, y, 6.0)) for y in (30.0, 190.0)]
    crossbars = [Part.makeBox(20.0, 180.0, 20.0, App.Vector(x, 30.0, 6.0)) for x in (20.0, 150.0, 310.0)]
    return Part.makeCompound([base, left, right, *rails, *crossbars])


def make_bearing_plate_component(params: dict):
    return _bearing_plate(0.0)


def make_adapter_set(params: dict):
    parts = []
    for x in (45.0, 135.0):
        cone = Part.makeCone(40.0, 25.0, 18.0, App.Vector(x, 45.0, 0.0))
        bore = Part.makeCylinder(params["shaft_diameter_mm"] / 2 + 0.1, 20.0, App.Vector(x, 45.0, -1.0))
        parts.append(cone.cut(bore))
    return Part.makeCompound(parts)


def make_installed_adapters(params: dict):
    bore_r = params["shaft_diameter_mm"] / 2 + 0.1
    left = Part.makeCone(40.0, 25.0, 18.0, App.Vector(SPOOL_X, 65.5, SPOOL_Z), App.Vector(0, 1, 0)).cut(
        _axis_y_cylinder(bore_r, 20.0, SPOOL_X, 64.5, SPOOL_Z)
    )
    right = Part.makeCone(40.0, 25.0, 18.0, App.Vector(SPOOL_X, 174.5, SPOOL_Z), App.Vector(0, -1, 0)).cut(
        Part.makeCylinder(bore_r, 20.0, App.Vector(SPOOL_X, 175.5, SPOOL_Z), App.Vector(0, -1, 0))
    )
    return Part.makeCompound([left, right])


def dancer_end(params: dict, angle_deg: float) -> App.Vector:
    length = params["dancer_arm_length_mm"]
    angle = radians(angle_deg)
    return App.Vector(
        DANCER_PIVOT_X + length * sin(angle),
        SPOOL_Y,
        DANCER_PIVOT_Z - length * cos(angle),
    )


def _dancer_at(params: dict, angle_deg: float, reference: bool = False):
    end = dancer_end(params, angle_deg)
    pivot = App.Vector(DANCER_PIVOT_X, SPOOL_Y, DANCER_PIVOT_Z)
    direction = end.sub(pivot)
    arm = Part.makeCylinder(4.0 if reference else 6.0, params["dancer_arm_length_mm"], pivot, direction)
    roller_r = params["dancer_roller_outer_diameter_mm"] / 2
    roller = _axis_y_cylinder(roller_r, 16.0, end.x, SPOOL_Y - 8.0, end.z)
    return Part.makeCompound([arm, roller])


def make_dancer(params: dict):
    pivot = _axis_y_ring(14.0, 6.0, 20.0, DANCER_PIVOT_X, SPOOL_Y - 10.0, DANCER_PIVOT_Z)
    sensor = Part.makeBox(24.0, 12.0, 24.0, App.Vector(DANCER_PIVOT_X - 12.0, SPOOL_Y + 12.0, DANCER_PIVOT_Z - 12.0))
    return Part.makeCompound([pivot, sensor, _dancer_at(params, 0.0)])


def make_dancer_sweep(params: dict):
    return Part.makeCompound([_dancer_at(params, angle, True) for angle in params["dancer_angle_range_deg"]])


def minimum_dancer_spool_clearance_mm(params: dict) -> float:
    spool_r = params["maximum_spool_outer_diameter_mm"] / 2
    roller_r = params["dancer_roller_outer_diameter_mm"] / 2
    clearances = []
    for angle in params["dancer_angle_range_deg"]:
        end = dancer_end(params, angle)
        center_distance = sqrt((end.x - SPOOL_X) ** 2 + (end.z - SPOOL_Z) ** 2)
        clearances.append(center_distance - spool_r - roller_r)
    return min(clearances)


def make_traverse(params: dict):
    y0 = SPOOL_Y - params["traverse_travel_mm"] / 2 - 10.0
    length = params["traverse_travel_mm"] + 20.0
    leadscrew = _axis_y_cylinder(4.0, length, 125.0, y0, 160.0)
    rods = [
        _axis_y_cylinder(3.0, length, x, y0, 145.0) for x in (110.0, 140.0)
    ]
    carriage = Part.makeBox(36.0, 20.0, 34.0, App.Vector(107.0, SPOOL_Y - 10.0, 138.0))
    eye = Part.makeCylinder(7.0, 10.0, App.Vector(143.0, SPOOL_Y, 165.0), App.Vector(1, 0, 0)).cut(
        Part.makeCylinder(2.5, 12.0, App.Vector(142.0, SPOOL_Y, 165.0), App.Vector(1, 0, 0))
    )
    endstops = [Part.makeBox(12.0, 8.0, 18.0, App.Vector(119.0, y, 130.0)) for y in (y0, y0 + length - 8.0)]
    return Part.makeCompound([leadscrew, *rods, carriage, eye, *endstops])


def make_traverse_carriage_component(params: dict):
    carriage = Part.makeBox(36.0, 20.0, 34.0)
    bores = Part.makeCylinder(4.2, 22.0, App.Vector(18.0, -1.0, 17.0), App.Vector(0, 1, 0))
    return carriage.cut(bores).removeSplitter()


def make_spool_drive(params: dict):
    motor = Part.makeBox(50.0, 42.0, 50.0, App.Vector(SPOOL_X - 25.0, 190.0, SPOOL_Z - 25.0))
    coupling = _axis_y_ring(12.0, params["shaft_diameter_mm"] / 2, 18.0, SPOOL_X, 182.0, SPOOL_Z)
    guard = Part.makeBox(70.0, 48.0, 70.0, App.Vector(SPOOL_X - 35.0, 185.0, SPOOL_Z - 35.0)).cut(
        Part.makeBox(60.0, 44.0, 60.0, App.Vector(SPOOL_X - 30.0, 184.0, SPOOL_Z - 30.0))
    )
    slip_clutch = _axis_y_ring(18.0, 6.0, 8.0, SPOOL_X, 176.0, SPOOL_Z)
    return Part.makeCompound([motor, coupling, guard, slip_clutch])


def make_spool_guard(params: dict):
    outer, inner = params["maximum_spool_outer_diameter_mm"] / 2 + 10.0, params["maximum_spool_outer_diameter_mm"] / 2 + 5.0
    rings = [
        _axis_y_ring(outer, inner, 5.0, SPOOL_X, y, SPOOL_Z) for y in (43.0, 192.0)
    ]
    bars = [
        Part.makeBox(8.0, 154.0, 8.0, App.Vector(x, 43.0, z))
        for x, z in (
            (SPOOL_X - 4.0, SPOOL_Z + inner),
            (SPOOL_X - 4.0, SPOOL_Z - inner - 8.0),
            (SPOOL_X + inner, SPOOL_Z - 4.0),
            (SPOOL_X - inner - 8.0, SPOOL_Z - 4.0),
        )
    ]
    return Part.makeCompound([*rings, *bars])
