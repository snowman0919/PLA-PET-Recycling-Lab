"""Parametric 18 mm helical screw extruder proof geometry."""

from __future__ import annotations

from math import atan, cos, pi, sin

import FreeCAD as App
import Part


AXIS_Y = 110.0
AXIS_Z = 150.0
FLIGHT_START_X = 210.0
THRUST_PLATE_X = 114.0
THRUST_BEARING_X = 126.0
SHOULDER_X = 135.0
RADIAL_BEARING_X = (166.0, 190.0)


def _axis_cylinder(radius: float, length: float, x: float):
    return Part.makeCylinder(radius, length, App.Vector(x, AXIS_Y, AXIS_Z), App.Vector(1, 0, 0))


def _ring(outer_r: float, inner_r: float, length: float, x: float):
    return _axis_cylinder(outer_r, length, x).cut(_axis_cylinder(inner_r, length + 2, x - 1))


def _from_z_axis(shape):
    shape.rotate(App.Vector(0, 0, 0), App.Vector(0, 1, 0), 90)
    shape.translate(App.Vector(FLIGHT_START_X, AXIS_Y, AXIS_Z))
    return shape


def _helical_flight(length: float, pitch: float, width: float, outer_r: float, feed_root: float, meter_root: float, feed_length: float, compression_length: float):
    """Build a closed 10-degree faceted helix with an exact 9 mm vertex radius.

    OpenCascade's long solid-pipe helix produced invalid boolean intersections at
    this scale.  This deterministic B-rep uses one closed shell, not overlapping
    ring envelopes.  The 10 degree chord lies inside the nominal OD; its maximum
    radial chord error is reported and reserved in the clearance test.
    """

    turns = length / pitch
    segments = int(round(turns * 36))

    def root_radius(z: float) -> float:
        if z <= feed_length:
            return feed_root
        if z < feed_length + compression_length:
            fraction = (z - feed_length) / compression_length
            return feed_root + (meter_root - feed_root) * fraction
        return meter_root

    def triangle(a, b, c):
        return Part.Face(Part.makePolygon([a, b, c, a]))

    sections = []
    for index in range(segments + 1):
        fraction = index / segments
        theta = 2 * pi * turns * fraction
        z = length * fraction
        root = root_radius(z)
        sections.append(
            [
                App.Vector(root * cos(theta), root * sin(theta), z - width / 2),
                App.Vector(outer_r * cos(theta), outer_r * sin(theta), z - width / 2),
                App.Vector(outer_r * cos(theta), outer_r * sin(theta), z + width / 2),
                App.Vector(root * cos(theta), root * sin(theta), z + width / 2),
            ]
        )
    faces = []
    for first, second in zip(sections, sections[1:]):
        for edge in range(4):
            a, b = first[edge], first[(edge + 1) % 4]
            c, d = second[(edge + 1) % 4], second[edge]
            faces.extend((triangle(a, b, c), triangle(a, c, d)))
    faces.extend(
        (
            triangle(sections[0][0], sections[0][2], sections[0][1]),
            triangle(sections[0][0], sections[0][3], sections[0][2]),
            triangle(sections[-1][0], sections[-1][1], sections[-1][2]),
            triangle(sections[-1][0], sections[-1][2], sections[-1][3]),
        )
    )
    shell = Part.makeShell(faces)
    flight = Part.makeSolid(shell)
    if not shell.isClosed() or not flight.isValid():
        raise RuntimeError("faceted helical flight is not a closed valid solid")
    return flight


def make_screw(params: dict, phase_deg: float = 0.0):
    diameter = params["screw_diameter_mm"]
    length = diameter * params["length_to_diameter_ratio"]
    zone = [value * diameter for value in params["zone_lengths_d"]]
    feed_h = params["feed_depth_ratio"] * diameter
    meter_h = params["metering_depth_ratio"] * diameter
    feed_root = diameter / 2 - feed_h
    meter_root = diameter / 2 - meter_h
    outer_r = diameter / 2

    feed_core = Part.makeCylinder(feed_root, zone[0])
    compression_core = Part.makeCone(feed_root, meter_root, zone[1], App.Vector(0, 0, zone[0]))
    meter_core = Part.makeCylinder(meter_root, zone[2], App.Vector(0, 0, zone[0] + zone[1]))

    pitch = diameter * params["pitch_ratio"]
    flight_width = diameter * params["flight_width_ratio"]
    flight = _helical_flight(length, pitch, flight_width, outer_r, feed_root, meter_root, zone[0], zone[1])
    tail_length = params["screw_tail_length_mm"]
    tail_r = params["screw_tail_diameter_mm"] / 2
    # Fuse in the native Z-axis frame; rotating the long faceted flight before
    # boolean union exposes an OpenCascade compound-volume defect.
    tail = Part.makeCylinder(tail_r, tail_length + 0.5, App.Vector(0, 0, -tail_length))
    shoulder = Part.makeCylinder(11.5, 8.0, App.Vector(0, 0, SHOULDER_X - FLIGHT_START_X))
    nose = Part.makeCone(meter_root, 3.0, 4.0, App.Vector(0, 0, length))
    body = feed_core.fuse(compression_core).fuse(meter_core).fuse(flight).fuse(tail).fuse(shoulder)
    # The nose meets the metering core at an exact end face.  Retain it as a
    # second solid in the component compound to avoid a zero-overlap fuse loss.
    screw = Part.makeCompound([body, nose])
    screw.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), phase_deg)
    return _from_z_axis(screw)


def make_barrel(params: dict):
    screw_length = params["screw_diameter_mm"] * params["length_to_diameter_ratio"]
    start = FLIGHT_START_X - 2.0
    end = FLIGHT_START_X + screw_length + 4.0
    length = end - start
    inner_r = params["barrel_inner_diameter_mm"] / 2
    outer_r = params["barrel_outer_diameter_mm"] / 2
    feed_x = FLIGHT_START_X + 18.0

    barrel_outer = _axis_cylinder(outer_r, length, start)
    feed_outer = Part.makeCylinder(18.0, 86.0, App.Vector(feed_x, AXIS_Y, AXIS_Z), App.Vector(0, 0, 1))
    pressure_boss = Part.makeCylinder(6.0, 35.0, App.Vector(end - 28.0, AXIS_Y, AXIS_Z), App.Vector(0, 0, 1))
    rupture_boss = Part.makeCylinder(7.0, 35.0, App.Vector(end - 52.0, AXIS_Y, AXIS_Z), App.Vector(0, 0, 1))
    outer = barrel_outer.fuse(feed_outer).fuse(pressure_boss).fuse(rupture_boss)

    axial_bore = _axis_cylinder(inner_r, length + 2.0, start - 1.0)
    feed_bore = Part.makeCylinder(13.0, 88.0, App.Vector(feed_x, AXIS_Y, AXIS_Z - 1), App.Vector(0, 0, 1))
    pressure_bore = Part.makeCylinder(2.0, 37.0, App.Vector(end - 28.0, AXIS_Y, AXIS_Z - 1), App.Vector(0, 0, 1))
    rupture_bore = Part.makeCylinder(3.0, 37.0, App.Vector(end - 52.0, AXIS_Y, AXIS_Z - 1), App.Vector(0, 0, 1))
    bores = axial_bore.fuse(feed_bore).fuse(pressure_bore).fuse(rupture_bore)
    return outer.cut(bores).removeSplitter()


def make_feed_throat_cooling(params: dict):
    feed_x = FLIGHT_START_X + 18.0
    jacket = Part.makeCylinder(25.0, 50.0, App.Vector(feed_x, AXIS_Y, AXIS_Z + 20), App.Vector(0, 0, 1)).cut(
        Part.makeCylinder(18.2, 52.0, App.Vector(feed_x, AXIS_Y, AXIS_Z + 19), App.Vector(0, 0, 1))
    )
    ports = [
        Part.makeCylinder(4.0, 16.0, App.Vector(feed_x, AXIS_Y, z), App.Vector(0, 1, 0))
        for z in (AXIS_Z + 32.0, AXIS_Z + 58.0)
    ]
    return Part.makeCompound([jacket, *ports])


def make_breaker_plate(params: dict):
    screw_length = params["screw_diameter_mm"] * params["length_to_diameter_ratio"]
    x = FLIGHT_START_X + screw_length + 6.0
    thickness = params["breaker_thickness_mm"]
    plate = _axis_cylinder(params["barrel_outer_diameter_mm"] / 2, thickness, x)
    positions = [(0.0, 0.0)] + [
        (4.5 * cos(index * pi / 3), 4.5 * sin(index * pi / 3)) for index in range(6)
    ]
    for dy, dz in positions:
        hole = Part.makeCylinder(
            params["breaker_hole_diameter_mm"] / 2,
            thickness + 2,
            App.Vector(x - 1, AXIS_Y + dy, AXIS_Z + dz),
            App.Vector(1, 0, 0),
        )
        plate = plate.cut(hole)
    return plate.removeSplitter()


def make_die(params: dict):
    screw_length = params["screw_diameter_mm"] * params["length_to_diameter_ratio"]
    x = FLIGHT_START_X + screw_length + 6.0 + params["breaker_thickness_mm"]
    body_length = 34.0
    body = _axis_cylinder(params["barrel_outer_diameter_mm"] / 2, body_length, x)
    chamber = _axis_cylinder(7.0, 12.0, x - 1.0)
    taper = Part.makeCone(7.0, params["die_bore_mm"] / 2, 10.0, App.Vector(x + 11.0, AXIS_Y, AXIS_Z), App.Vector(1, 0, 0))
    land = _axis_cylinder(params["die_bore_mm"] / 2, params["die_land_mm"] + 1.0, x + 21.0)
    return body.cut(chamber.fuse(taper).fuse(land)).removeSplitter()


def make_heaters(params: dict):
    inner = params["barrel_outer_diameter_mm"] / 2
    bands = [
        _ring(inner + 3.0, inner, 80.0, x)
        for x in (FLIGHT_START_X + 50.0, FLIGHT_START_X + 164.0, FLIGHT_START_X + 308.0)
    ]
    screw_length = params["screw_diameter_mm"] * params["length_to_diameter_ratio"]
    die_x = FLIGHT_START_X + screw_length + 12.0
    bands.append(_ring(inner + 6.0, inner, 26.0, die_x))
    return Part.makeCompound(bands)


def make_insulation(params: dict):
    inner = params["barrel_outer_diameter_mm"] / 2 + 3.0
    outer = params["barrel_outer_diameter_mm"] / 2 + params["insulation_thickness_mm"]
    segments = [(FLIGHT_START_X + 42.0, 112.0), (FLIGHT_START_X + 162.0, 126.0), (FLIGHT_START_X + 296.0, 132.0)]
    return Part.makeCompound([_ring(outer, inner, length, x) for x, length in segments])


def make_heat_shield(params: dict):
    insulation_outer = params["barrel_outer_diameter_mm"] / 2 + params["insulation_thickness_mm"]
    inner = insulation_outer + params["shield_air_gap_mm"]
    outer = inner + params["shield_thickness_mm"]
    x = FLIGHT_START_X + 38.0
    length = 396.0
    shell = _ring(outer, inner, length, x)
    # Longitudinal slots are ventilation/visibility proof cut-outs, not a final guard pattern.
    for x_slot in (x + 18.0, x + length - 38.0):
        for angle in (0, 90, 180, 270):
            slot = Part.makeBox(22.0, 12.0, 34.0, App.Vector(x_slot, AXIS_Y + inner - 6, AXIS_Z - 17))
            slot.rotate(App.Vector(x_slot, AXIS_Y, AXIS_Z), App.Vector(1, 0, 0), angle)
            shell = shell.cut(slot)
    return shell.removeSplitter()


def make_thrust_bearing(params: dict):
    b = params["thrust_bearing"]
    return _ring(b["outer_diameter_mm"] / 2, b["bore_mm"] / 2, b["height_mm"], THRUST_BEARING_X)


def make_radial_bearings(params: dict):
    b = params["radial_bearing"]
    return Part.makeCompound([
        _ring(b["outer_diameter_mm"] / 2, b["bore_mm"] / 2, b["width_mm"], x)
        for x in RADIAL_BEARING_X
    ])


def _plate_with_axis_hole(x: float, thickness: float, width: float, height: float, hole_r: float):
    plate = Part.makeBox(thickness, width, height, App.Vector(x, AXIS_Y - width / 2, 26.0))
    hole = _axis_cylinder(hole_r, thickness + 2, x - 1)
    holes = hole
    for y in (AXIS_Y - width / 2 + 12.0, AXIS_Y + width / 2 - 12.0):
        frame_hole = Part.makeCylinder(4.5, thickness + 2, App.Vector(x - 1, y, 38.0), App.Vector(1, 0, 0))
        holes = holes.fuse(frame_hole)
    return plate.cut(holes).removeSplitter()


def make_support_frame(params: dict):
    base_t = params["base_thickness_mm"]
    base_x = params["base_origin_x_mm"]
    base = Part.makeBox(params["base_length_mm"], params["base_width_mm"], base_t, App.Vector(base_x, 0, 0))
    rails = [
        Part.makeBox(800.0, 40.0, 40.0, App.Vector(-55.0, y, base_t)) for y in (35.0, 145.0)
    ]
    crossbars = [Part.makeBox(40.0, 150.0, 40.0, App.Vector(x, 35.0, base_t)) for x in (-45.0, 90.0, 650.0, 705.0)]
    motor_cradle = Part.makeBox(55.0, 50.0, 70.0, App.Vector(-60.0, 85.0, 46.0))
    gearbox_pedestal = Part.makeBox(50.0, 60.0, 66.0, App.Vector(10.0, 80.0, 46.0))
    thickness = params["support_plate_thickness_mm"]
    thrust_plate = _plate_with_axis_hole(THRUST_PLATE_X, thickness, 120.0, 174.0, 10.0)
    radial_plates = [
        _plate_with_axis_hole(x - 1.5, thickness, 110.0, 160.0, params["radial_bearing"]["outer_diameter_mm"] / 2)
        for x in RADIAL_BEARING_X
    ]
    barrel_plates = [
        _plate_with_axis_hole(x, thickness, 126.0, 174.0, params["barrel_outer_diameter_mm"] / 2)
        for x in (FLIGHT_START_X - 6.0, FLIGHT_START_X + params["screw_diameter_mm"] * params["length_to_diameter_ratio"] - 6.0)
    ]
    return Part.makeCompound([base, *rails, *crossbars, motor_cradle, gearbox_pedestal, thrust_plate, *radial_plates, *barrel_plates])


def make_thrust_plate_component(params: dict):
    return _plate_with_axis_hole(
        THRUST_PLATE_X,
        params["support_plate_thickness_mm"],
        120.0,
        174.0,
        10.0,
    )


def make_drive_and_coupling(params: dict):
    gearbox = Part.makeBox(64.0, 76.0, 76.0, App.Vector(5.0, AXIS_Y - 38.0, AXIS_Z - 38.0))
    motor = Part.makeCylinder(34.0, 78.0, App.Vector(-73.0, AXIS_Y, AXIS_Z), App.Vector(1, 0, 0))
    coupling = _ring(13.0, params["screw_tail_diameter_mm"] / 2, 22.0, 69.0)
    guard = Part.makeBox(42.0, 62.0, 62.0, App.Vector(62.0, AXIS_Y - 31.0, AXIS_Z - 31.0)).cut(
        Part.makeBox(44.0, 52.0, 52.0, App.Vector(61.0, AXIS_Y - 26.0, AXIS_Z - 26.0))
    )
    return Part.makeCompound([gearbox, motor, coupling, guard])


def make_pressure_devices(params: dict):
    screw_length = params["screw_diameter_mm"] * params["length_to_diameter_ratio"]
    barrel_end = FLIGHT_START_X + screw_length + 4.0
    sensor = Part.makeBox(24.0, 20.0, 34.0, App.Vector(barrel_end - 40.0, AXIS_Y - 10.0, AXIS_Z + 30.0))
    rupture = Part.makeCylinder(10.0, 28.0, App.Vector(barrel_end - 52.0, AXIS_Y, AXIS_Z + 31.0), App.Vector(0, 0, 1))
    catch_outer = Part.makeBox(92.0, 86.0, 54.0, App.Vector(barrel_end + 18.0, AXIS_Y - 43.0, 46.0))
    catch_inner = Part.makeBox(82.0, 76.0, 52.0, App.Vector(barrel_end + 23.0, AXIS_Y - 38.0, 51.0))
    catch = catch_outer.cut(catch_inner)
    return Part.makeCompound([sensor, rupture, catch])
