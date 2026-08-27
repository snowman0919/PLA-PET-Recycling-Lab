"""Parametric double-gate input classifier and seven-port storage diverter."""

from __future__ import annotations

import math

import FreeCAD as App
import Part


def compound(shapes):
    return Part.makeCompound([shape for shape in shapes if shape is not None and not shape.isNull()])


def make_gate_half(params: dict):
    return Part.makeBox(params["gate_panel_width_mm"] / 2.0, params["gate_panel_depth_mm"], 4.0)


def make_closed_gate(params: dict, z: float):
    half = params["gate_panel_width_mm"] / 2.0
    x0 = (params["module_width_mm"] - params["gate_panel_width_mm"]) / 2.0
    y0 = (params["module_depth_mm"] - params["gate_panel_depth_mm"]) / 2.0
    left = Part.makeBox(half, params["gate_panel_depth_mm"], 4.0, App.Vector(x0, y0, z))
    right = Part.makeBox(half, params["gate_panel_depth_mm"], 4.0, App.Vector(x0 + half, y0, z))
    return compound([left, right])


def make_open_gate(params: dict, z: float):
    half = params["gate_panel_width_mm"] / 2.0
    x0 = (params["module_width_mm"] - params["gate_panel_width_mm"]) / 2.0
    y0 = (params["module_depth_mm"] - params["gate_panel_depth_mm"]) / 2.0
    left = Part.makeBox(4.0, params["gate_panel_depth_mm"], half, App.Vector(x0, y0, z))
    right = Part.makeBox(4.0, params["gate_panel_depth_mm"], half, App.Vector(x0 + params["gate_panel_width_mm"] - 4.0, y0, z))
    return compound([left, right])


def make_classifier_frame(params: dict):
    width, depth, height = params["module_width_mm"], params["module_depth_mm"], params["module_height_mm"]
    shapes = []
    for x in (0.0, width - 10.0):
        for y in (0.0, depth - 10.0):
            shapes.append(Part.makeBox(10.0, 10.0, height, App.Vector(x, y, 0)))
    shapes.extend(
        [
            Part.makeBox(width, 10.0, height, App.Vector(0, 0, 0)),
            Part.makeBox(width, 10.0, height, App.Vector(0, depth - 10.0, 0)),
            Part.makeBox(10.0, depth, height, App.Vector(0, 0, 0)),
            Part.makeBox(10.0, depth, height, App.Vector(width - 10.0, 0, 0)),
        ]
    )
    roof = Part.makeBox(width, depth, 6.0, App.Vector(0, 0, height - 6.0))
    inlet = Part.makeBox(params["inlet_width_mm"], params["inlet_depth_mm"], 8.0,
                         App.Vector((width - params["inlet_width_mm"]) / 2.0,
                                    (depth - params["inlet_depth_mm"]) / 2.0, height - 7.0))
    shapes.append(roof.cut(inlet))
    return compound(shapes)


def make_light_tunnel(params: dict):
    width, depth = params["module_width_mm"], params["module_depth_mm"]
    camera = Part.makeBox(24.0, 28.0, 24.0, App.Vector(12.0, depth / 2.0 - 14.0, 174.0))
    backlight = Part.makeBox(8.0, 120.0, 90.0, App.Vector(width - 20.0, depth / 2.0 - 60.0, 130.0))
    ray = Part.makeCylinder(2.0, width - 40.0, App.Vector(20.0, depth / 2.0, 185.0), App.Vector(1, 0, 0))
    matte_reference = Part.makeBox(4.0, 70.0, 70.0, App.Vector(width - 32.0, depth / 2.0 - 35.0, 150.0))
    return compound([camera, backlight, ray, matte_reference])


def make_bottle_reference(params: dict):
    radius = params["maximum_bottle_diameter_mm"] / 2.0
    return Part.makeCylinder(radius, params["maximum_bottle_length_mm"],
                             App.Vector(params["module_width_mm"] / 2.0, 5.0, 185.0), App.Vector(0, 1, 0))


def make_reject_flap(params: dict):
    width = params["inlet_width_mm"]
    flap = Part.makeBox(width, 5.0, 55.0, App.Vector((params["module_width_mm"] - width) / 2.0, 105.0, 5.0))
    shaft = Part.makeCylinder(5.0, width + 20.0, App.Vector((params["module_width_mm"] - width) / 2.0 - 10.0, 110.0, 60.0), App.Vector(1, 0, 0))
    reject_chute = Part.makeBox(100.0, 90.0, 40.0, App.Vector(params["module_width_mm"] - 110.0, 120.0, 0.0))
    return compound([flap, shaft, reject_chute])


def make_input_classifier(params: dict):
    upper_z = 160.0
    lower_z = upper_z - params["gate_separation_mm"]
    return compound(
        [
            make_classifier_frame(params),
            make_closed_gate(params, upper_z),
            make_open_gate(params, lower_z),
            make_light_tunnel(params),
            make_bottle_reference(params),
            make_reject_flap(params),
        ]
    )


def make_diverter_rotor(params: dict):
    diameter = params["diverter_rotor_diameter_mm"]
    hub = Part.makeCylinder(diameter / 2.0, 12.0, App.Vector(160.0, 160.0, 20.0))
    throat = Part.makeBox(diameter / 2.0 + 20.0, params["diverter_port_width_mm"], 35.0,
                          App.Vector(160.0, 160.0 - params["diverter_port_width_mm"] / 2.0, 32.0))
    return compound([hub, throat])


def diverter_port_centres(params: dict):
    count = int(params["color_port_count"])
    radius = params["diverter_outer_diameter_mm"] / 2.0 - 20.0
    return [
        (160.0 + radius * math.cos(2.0 * math.pi * index / count),
         160.0 + radius * math.sin(2.0 * math.pi * index / count))
        for index in range(count)
    ]


def make_diverter_ports(params: dict):
    shapes = []
    width = params["diverter_port_width_mm"]
    for x, y in diverter_port_centres(params):
        shapes.append(Part.makeBox(width, width, 50.0, App.Vector(x - width / 2.0, y - width / 2.0, 0.0)))
    centre = App.Vector(160.0, 160.0, 0.0)
    frame = Part.makeCylinder(160.0, 5.0, centre).cut(Part.makeCylinder(145.0, 5.0, centre))
    return compound([frame, *shapes])


def make_classification_storage(params: dict):
    return compound([make_diverter_ports(params), make_diverter_rotor(params)])
