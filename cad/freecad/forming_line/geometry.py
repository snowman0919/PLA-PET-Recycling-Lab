"""Parametric cooling, dual-view gauge and closed-loop puller proof."""

from __future__ import annotations

import FreeCAD as App
import Part


PATH_Y = 80.0
PATH_Z = 100.0
TUNNEL_Y = 10.0
TUNNEL_Z = 40.0
TUNNEL_WIDTH = 140.0
TUNNEL_HEIGHT = 120.0
GAUGE_X = 470.0
PULLER_X = 600.0
MODULE_LENGTH = 700.0


def _axis_x_cylinder(radius: float, length: float, x: float, y: float = PATH_Y, z: float = PATH_Z):
    return Part.makeCylinder(radius, length, App.Vector(x, y, z), App.Vector(1, 0, 0))


def _axis_y_cylinder(radius: float, length: float, x: float, y: float, z: float):
    return Part.makeCylinder(radius, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def cooling_segment_length(params: dict) -> float:
    return params["cooling_tunnel_length_mm"] / params["fan_count"]


def make_cooling_segment(params: dict, index: int = 0):
    length = cooling_segment_length(params)
    x = index * length
    outer = Part.makeBox(length, TUNNEL_WIDTH, TUNNEL_HEIGHT, App.Vector(x, TUNNEL_Y, TUNNEL_Z))
    inner = Part.makeBox(length + 2, 100.0, 80.0, App.Vector(x - 1, 30.0, 60.0))
    shell = outer.cut(inner)

    fan_size = params["fan_envelope_mm"]
    fan_opening = Part.makeBox(
        fan_size,
        fan_size,
        23.0,
        App.Vector(x + (length - fan_size) / 2, PATH_Y - fan_size / 2, TUNNEL_Z + TUNNEL_HEIGHT - 1),
    )
    side_slots = Part.makeCompound([
        Part.makeBox(length - 24.0, 12.0, 18.0, App.Vector(x + 12.0, TUNNEL_Y - 1, 70.0)),
        Part.makeBox(length - 24.0, 12.0, 18.0, App.Vector(x + 12.0, TUNNEL_Y + TUNNEL_WIDTH - 11.0, 70.0)),
    ])
    return shell.cut(fan_opening.fuse(side_slots)).removeSplitter()


def make_cooling_tunnel(params: dict):
    return Part.makeCompound([make_cooling_segment(params, index) for index in range(params["fan_count"])])


def make_cooling_fans(params: dict):
    length = cooling_segment_length(params)
    size = params["fan_envelope_mm"]
    fans = []
    for index in range(params["fan_count"]):
        x = index * length + (length - size) / 2
        block = Part.makeBox(size, size, 25.0, App.Vector(x, PATH_Y - size / 2, TUNNEL_Z + TUNNEL_HEIGHT))
        bore = Part.makeCylinder(size * 0.43, 27.0, App.Vector(x + size / 2, PATH_Y, TUNNEL_Z + TUNNEL_HEIGHT - 1))
        fans.append(block.cut(bore))
    return Part.makeCompound(fans)


def make_forming_frame(params: dict):
    rails = [Part.makeBox(MODULE_LENGTH, 20.0, 20.0, App.Vector(0, y, 0)) for y in (10.0, 130.0)]
    crossbars = [Part.makeBox(20.0, 140.0, 20.0, App.Vector(x, 10.0, 0)) for x in (0.0, 140.0, 290.0, 430.0, 470.0, 580.0, 600.0, 680.0)]
    supports = [Part.makeBox(12.0, 20.0, 20.0, App.Vector(x, y, 20.0)) for x in (10.0, 420.0) for y in (20.0, 120.0)]
    return Part.makeCompound([*rails, *crossbars, *supports])


def make_filament_reference(params: dict):
    return _axis_x_cylinder(params["target_diameter_mm"] / 2, MODULE_LENGTH, 0.0)


def make_gauge_enclosure(params: dict):
    gauge = params["gauge"]
    length, width, height = gauge["enclosure_length_mm"], gauge["enclosure_width_mm"], gauge["enclosure_height_mm"]
    outer = Part.makeBox(length, width, height, App.Vector(GAUGE_X, 0.0, 30.0))
    inner = Part.makeBox(length - 10.0, width - 20.0, height - 20.0, App.Vector(GAUGE_X + 5.0, 10.0, 40.0))
    shell = outer.cut(inner)
    path = _axis_x_cylinder(8.0, length + 2.0, GAUGE_X - 1.0)
    camera_window = Part.makeBox(55.0, 12.0, 72.0, App.Vector(GAUGE_X + 27.5, -1.0, 78.0))
    rear_window = Part.makeBox(55.0, 12.0, 52.0, App.Vector(GAUGE_X + 27.5, width - 11.0, 74.0))
    lower_window = Part.makeBox(42.0, 48.0, 12.0, App.Vector(GAUGE_X + 55.0, 56.0, 29.0))
    return shell.cut(path.fuse(camera_window).fuse(rear_window).fuse(lower_window)).removeSplitter()


def make_gauge_optics(params: dict):
    sensor_y = Part.makeBox(32.0, 10.0, 32.0, App.Vector(GAUGE_X + 14.0, 10.0, 84.0))
    sensor_z = Part.makeBox(32.0, 32.0, 10.0, App.Vector(GAUGE_X + 58.0, 64.0, 40.0))
    direct_backlight = Part.makeBox(36.0, 5.0, 36.0, App.Vector(GAUGE_X + 12.0, 145.0, 82.0))
    lower_backlight = Part.makeBox(36.0, 36.0, 5.0, App.Vector(GAUGE_X + 57.0, 62.0, 145.0))
    windows = [
        Part.makeBox(40.0, 1.0, 48.0, App.Vector(GAUGE_X + 10.0, 139.0, 76.0)),
        Part.makeBox(40.0, 44.0, 1.0, App.Vector(GAUGE_X + 55.0, 58.0, 59.0)),
    ]
    return Part.makeCompound([sensor_y, sensor_z, direct_backlight, lower_backlight, *windows])


def make_optical_ray_keepouts(params: dict):
    direct = Part.makeCylinder(0.8, 126.0, App.Vector(GAUGE_X + 30.0, 18.0, PATH_Z), App.Vector(0, 1, 0))
    vertical = Part.makeCylinder(0.8, 84.0, App.Vector(GAUGE_X + 75.0, PATH_Y, 58.0), App.Vector(0, 0, 1))
    return Part.makeCompound([direct, vertical])


def make_gauge_optical_proof(params: dict):
    filament = _axis_x_cylinder(params["target_diameter_mm"] / 2, 110.0, GAUGE_X)
    return Part.makeCompound([make_gauge_optics(params), make_optical_ray_keepouts(params), filament])


def puller_center_distance(params: dict) -> float:
    return params["puller"]["roller_outer_diameter_mm"] + params["puller"]["nominal_nip_gap_mm"]


def make_puller_rollers(params: dict):
    puller = params["puller"]
    radius = puller["roller_outer_diameter_mm"] / 2
    center_offset = puller_center_distance(params) / 2
    y = PATH_Y - puller["roller_width_mm"] / 2
    rollers = [
        _axis_y_cylinder(radius, puller["roller_width_mm"], PULLER_X + 52.0, y, PATH_Z - center_offset),
        _axis_y_cylinder(radius, puller["roller_width_mm"], PULLER_X + 52.0, y, PATH_Z + center_offset),
    ]
    gear_radius = puller_center_distance(params) / 2
    gears = [
        _axis_y_cylinder(gear_radius, 6.0, PULLER_X + 52.0, y + puller["roller_width_mm"] + 4.0, PATH_Z - center_offset),
        _axis_y_cylinder(gear_radius, 6.0, PULLER_X + 52.0, y + puller["roller_width_mm"] + 4.0, PATH_Z + center_offset),
    ]
    return Part.makeCompound([*rollers, *gears])


def make_odometer(params: dict):
    puller = params["puller"]
    radius = puller["odometer_outer_diameter_mm"] / 2
    center_z = PATH_Z - radius - params["target_diameter_mm"] / 2
    wheel = _axis_y_cylinder(radius, 8.0, PULLER_X + 80.0, PATH_Y - 4.0, center_z)
    encoder = _axis_y_cylinder(10.0, 6.0, PULLER_X + 80.0, PATH_Y + 7.0, center_z)
    arm = Part.makeBox(10.0, 12.0, 52.0, App.Vector(PULLER_X + 75.0, PATH_Y - 6.0, center_z - 26.0))
    return Part.makeCompound([wheel, encoder, arm])


def make_puller_guard_and_support(params: dict):
    base = Part.makeBox(100.0, 160.0, 10.0, App.Vector(PULLER_X - 5.0, 0.0, 20.0))
    supports = [Part.makeBox(18.0, 20.0, 110.0, App.Vector(x, y, 30.0)) for x in (PULLER_X + 34.0, PULLER_X + 72.0) for y in (50.0, 90.0)]
    outer = Part.makeBox(100.0, 150.0, 125.0, App.Vector(PULLER_X - 5.0, 5.0, 45.0))
    inner = Part.makeBox(90.0, 140.0, 115.0, App.Vector(PULLER_X, 10.0, 50.0))
    path = _axis_x_cylinder(8.0, 102.0, PULLER_X - 6.0)
    service = Part.makeBox(70.0, 80.0, 20.0, App.Vector(PULLER_X + 15.0, 40.0, 151.0))
    guard = outer.cut(inner).cut(path).cut(service).removeSplitter()
    motor = Part.makeBox(42.0, 42.0, 48.0, App.Vector(PULLER_X + 12.0, 108.0, 56.0))
    return Part.makeCompound([base, *supports, guard, motor])


def make_calibration_fixture(params: dict):
    base = Part.makeBox(100.0, 55.0, 8.0)
    holes = None
    for index, diameter in enumerate(params["gauge"]["calibration_pin_diameters_mm"]):
        hole = Part.makeCylinder(diameter / 2 + 0.10, 10.0, App.Vector(18.0 + index * 22.0, 27.5, -1.0))
        holes = hole if holes is None else holes.fuse(hole)
    return base.cut(holes).removeSplitter()
