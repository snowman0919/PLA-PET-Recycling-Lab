"""Parametric segregated control-enclosure proof geometry."""

from __future__ import annotations

import FreeCAD as App
import Part


def compound(shapes):
    return Part.makeCompound([shape for shape in shapes if shape is not None and not shape.isNull()])


def make_shell(params: dict):
    w, d, h, t = params["width_mm"], params["depth_mm"], params["height_mm"], params["sheet_thickness_mm"]
    return compound(
        [
            Part.makeBox(w, d, t),
            Part.makeBox(w, d, t, App.Vector(0, 0, h - t)),
            Part.makeBox(t, d, h),
            Part.makeBox(t, d, h, App.Vector(w - t, 0, 0)),
            Part.makeBox(w, t, h, App.Vector(0, d - t, 0)),
        ]
    )


def make_backplate_and_partition(params: dict):
    w, d, h, t = params["width_mm"], params["depth_mm"], params["height_mm"], params["sheet_thickness_mm"]
    backplate = Part.makeBox(w - 20.0, 3.0, h - 20.0, App.Vector(10.0, d - 8.0, 10.0))
    partition = Part.makeBox(3.0, d - 20.0, h - 20.0, App.Vector(params["logic_partition_x_mm"], 10.0, 10.0))
    high_din = Part.makeBox(params["din_rail_length_mm"], 8.0, 35.0, App.Vector(10.0, d - 18.0, 35.0))
    logic_din = Part.makeBox(params["din_rail_length_mm"], 8.0, 35.0, App.Vector(165.0, d - 18.0, 35.0))
    return compound([backplate, partition, high_din, logic_din])


def make_high_current_devices(params: dict):
    d = params["depth_mm"]
    safety_relay = Part.makeBox(45.0, 65.0, 100.0, App.Vector(12.0, d - 78.0, 65.0))
    contactor = Part.makeBox(55.0, 70.0, 90.0, App.Vector(65.0, d - 83.0, 70.0))
    fuse_bank = Part.makeBox(110.0, 45.0, 45.0, App.Vector(12.0, d - 58.0, 12.0))
    heater_drivers = Part.makeBox(120.0, 45.0, 50.0, App.Vector(10.0, 25.0, 105.0))
    return compound([safety_relay, contactor, fuse_bank, heater_drivers])


def make_logic_devices(params: dict):
    d = params["depth_mm"]
    mega = Part.makeBox(102.0, 54.0, 18.0, App.Vector(165.0, d - 67.0, 120.0))
    pi = Part.makeBox(85.0, 56.0, 22.0, App.Vector(175.0, d - 67.0, 80.0))
    buck = Part.makeBox(55.0, 40.0, 25.0, App.Vector(165.0, d - 52.0, 35.0))
    sensor_if = Part.makeBox(105.0, 50.0, 28.0, App.Vector(165.0, 25.0, 110.0))
    terminals = Part.makeBox(120.0, 25.0, 35.0, App.Vector(160.0, 25.0, 20.0))
    return compound([mega, pi, buck, sensor_if, terminals])


def make_split_door(params: dict):
    half = params["door_split_width_mm"]
    h, t = params["height_mm"], params["sheet_thickness_mm"]
    left = Part.makeBox(half, t, h)
    right = Part.makeBox(half, t, h, App.Vector(half, 0, 0))
    tft_opening = Part.makeBox(95.0, t + 2.0, 58.0, App.Vector(172.0, -1.0, 92.0))
    left = left.cut(Part.makeCylinder(12.0, t + 2.0, App.Vector(45.0, -1.0, 130.0), App.Vector(0, 1, 0)))
    right = right.cut(tft_opening)
    return compound([left, right])


def make_face_controls(params: dict):
    t = params["sheet_thickness_mm"]
    estop = Part.makeCylinder(20.0, 25.0, App.Vector(45.0, -25.0, 130.0), App.Vector(0, 1, 0))
    tft = Part.makeBox(100.0, 12.0, 64.0, App.Vector(170.0, -12.0, 89.0))
    start = Part.makeCylinder(10.0, 18.0, App.Vector(185.0, -18.0, 55.0), App.Vector(0, 1, 0))
    back = Part.makeCylinder(10.0, 18.0, App.Vector(225.0, -18.0, 55.0), App.Vector(0, 1, 0))
    rotary = Part.makeCylinder(12.0, 22.0, App.Vector(265.0, -22.0, 55.0), App.Vector(0, 1, 0))
    return compound([estop, tft, start, back, rotary])


def make_cable_management(params: dict):
    w, d = params["width_mm"], params["depth_mm"]
    high_duct = Part.makeBox(20.0, d - 30.0, 25.0, App.Vector(125.0, 15.0, 12.0))
    logic_duct = Part.makeBox(20.0, d - 30.0, 25.0, App.Vector(145.0, 15.0, 12.0))
    high_glands = Part.makeBox(120.0, 20.0, 20.0, App.Vector(10.0, d - 20.0, 0.0))
    logic_glands = Part.makeBox(120.0, 20.0, 20.0, App.Vector(w - 130.0, d - 20.0, 0.0))
    pe_stud = Part.makeCylinder(4.0, 18.0, App.Vector(18.0, d - 18.0, 2.0))
    return compound([high_duct, logic_duct, high_glands, logic_glands, pe_stud])


def make_control_enclosure(params: dict):
    return compound(
        [
            make_shell(params),
            make_backplate_and_partition(params),
            make_high_current_devices(params),
            make_logic_devices(params),
            make_split_door(params),
            make_face_controls(params),
            make_cable_management(params),
        ]
    )
