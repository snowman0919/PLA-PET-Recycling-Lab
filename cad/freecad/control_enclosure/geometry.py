"""Parametric control-enclosure geometry with explicit BOM placement states.

The coordinate convention is X=width, Y=door-to-backplate depth and Z=height.
Selected candidates use supplier dimensions, PCB geometry is a reserved mounting
interface, user inventory remains measurement-dependent, and unselected devices
are deliberately conservative placeholders.
"""

from __future__ import annotations

import FreeCAD as App
import Part


def compound(shapes):
    return Part.makeCompound([shape for shape in shapes if shape is not None and not shape.isNull()])


def box_from_spec(spec: dict):
    return Part.makeBox(*spec["size_mm"], App.Vector(*spec["origin_mm"]))


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
    w, d, h = params["width_mm"], params["depth_mm"], params["height_mm"]
    backplate = Part.makeBox(w - 20.0, 3.0, h - 20.0, App.Vector(10.0, d - 8.0, 10.0))
    partition = Part.makeBox(3.0, d - 20.0, h - 20.0, App.Vector(params["logic_partition_x_mm"], 10.0, 10.0))
    high_din = Part.makeBox(
        params["high_current_din_rail_length_mm"], 8.0, 35.0,
        App.Vector(20.0, d - 16.0, 312.5),
    )
    logic_din = Part.makeBox(
        params["logic_din_rail_length_mm"], 8.0, 35.0,
        App.Vector(260.0, d - 16.0, 312.5),
    )
    return compound([backplate, partition, high_din, logic_din])


def selected_candidate_specs(params: dict):
    return params["layout"]["selected_candidates"]


def placeholder_specs(params: dict):
    return params["layout"]["placeholders"]


def user_inventory_specs(params: dict):
    return params["layout"]["user_inventory"]


def wire_route_specs(params: dict):
    return params["layout"]["wire_routes"]


def make_selected_candidate(spec: dict):
    return box_from_spec(spec)


def make_placeholder(spec: dict):
    return box_from_spec(spec)


def make_user_inventory(spec: dict):
    return box_from_spec(spec)


def make_wire_route(spec: dict):
    return box_from_spec(spec)


def make_pcb_board(params: dict):
    spec = params["layout"]["pcb_reserved"]
    x, _, z = spec["origin_mm"]
    width, height, thickness = spec["board_size_mm"]
    backplate_face_y = params["depth_mm"] - 8.0
    board_y = backplate_face_y - params["pcb_standoff_mm"] - thickness
    board = Part.makeBox(width, thickness, height, App.Vector(x, board_y, z))
    holes = []
    for hx, hz in spec["mounting_holes_local_mm"]:
        holes.append(
            Part.makeCylinder(1.6, thickness + 0.2, App.Vector(x + hx, board_y - 0.1, z + hz), App.Vector(0, 1, 0))
        )
    return board.cut(compound(holes))


def make_pcb_standoffs(params: dict):
    spec = params["layout"]["pcb_reserved"]
    x, _, z = spec["origin_mm"]
    length = params["pcb_standoff_mm"]
    backplate_face_y = params["depth_mm"] - 8.0
    return compound(
        Part.makeCylinder(3.0, length, App.Vector(x + hx, backplate_face_y - length, z + hz), App.Vector(0, 1, 0)).cut(
            Part.makeCylinder(1.6, length + 0.2, App.Vector(x + hx, backplate_face_y - length - 0.1, z + hz), App.Vector(0, 1, 0))
        )
        for hx, hz in spec["mounting_holes_local_mm"]
    )


def make_pcb_reserved_keepout(params: dict):
    return box_from_spec(params["layout"]["pcb_reserved"])


def make_terminal_service_keepout(spec: dict, clearance_mm: float):
    x, y, z = spec["origin_mm"]
    sx, _, sz = spec["size_mm"]
    return Part.makeBox(sx, clearance_mm, sz, App.Vector(x, max(0.0, y - clearance_mm), z))


def make_service_keepouts(params: dict):
    clearance = params["terminal_service_keepout_mm"]
    specs = [*selected_candidate_specs(params), *placeholder_specs(params), *user_inventory_specs(params)]
    specs.append(params["layout"]["pcb_reserved"])
    return compound(make_terminal_service_keepout(spec, clearance) for spec in specs)


def make_high_current_devices(params: dict):
    specs = [
        *[s for s in selected_candidate_specs(params) if s["part_id"] == "SAF-REL-001"],
        *[s for s in placeholder_specs(params) if s["part_id"] in {"SAF-CON-001", "SAF-FUS-001", "ELE-HTR-DRV"}],
    ]
    return compound(box_from_spec(spec) for spec in specs)


def make_logic_devices(params: dict):
    specs = [
        *[s for s in selected_candidate_specs(params) if s["part_id"] == "ELE-BUCK-001"],
        *user_inventory_specs(params),
        *[s for s in placeholder_specs(params) if s["part_id"] == "MISC-WIR-001"],
    ]
    return compound([*(box_from_spec(spec) for spec in specs), make_pcb_reserved_keepout(params)])


def make_split_door(params: dict):
    """Legacy function name; the selected 500 x 400 enclosure uses one service door."""
    w, h, t = params["width_mm"], params["height_mm"], params["sheet_thickness_mm"]
    door = Part.makeBox(w, t, h)
    estop_cut = Part.makeCylinder(11.15, t + 2.0, App.Vector(170.0, -1.0, 330.0), App.Vector(0, 1, 0))
    tft_cut = Part.makeBox(100.0, t + 2.0, 64.0, App.Vector(285.0, -1.0, 300.0))
    for x in (300.0, 350.0, 400.0):
        tft_cut = tft_cut.fuse(Part.makeCylinder(11.15, t + 2.0, App.Vector(x, -1.0, 260.0), App.Vector(0, 1, 0)))
    return door.cut(estop_cut.fuse(tft_cut))


def make_estop_candidate(params: dict):
    # A22E-M official head diameter is 40 mm; 80 mm rear keep-out remains conservative.
    head = Part.makeCylinder(20.0, 25.0, App.Vector(170.0, -25.0, 330.0), App.Vector(0, 1, 0))
    rear_keepout = Part.makeCylinder(20.0, 80.0, App.Vector(170.0, 0.0, 330.0), App.Vector(0, 1, 0))
    return compound([head, rear_keepout])


def make_ui_placeholders(params: dict):
    tft = Part.makeBox(100.0, 14.0, 64.0, App.Vector(285.0, -14.0, 300.0))
    buttons = [
        Part.makeCylinder(11.0, 20.0, App.Vector(x, -20.0, 260.0), App.Vector(0, 1, 0))
        for x in (300.0, 350.0, 400.0)
    ]
    return compound([tft, *buttons])


def make_face_controls(params: dict):
    return compound([make_estop_candidate(params), make_ui_placeholders(params)])


def make_glands_and_pe(params: dict):
    w, d = params["width_mm"], params["depth_mm"]
    high_glands = Part.makeBox(190.0, 20.0, 18.0, App.Vector(20.0, d - 20.0, 0.0))
    logic_glands = Part.makeBox(210.0, 20.0, 18.0, App.Vector(w - 230.0, d - 20.0, 0.0))
    pe_stud = Part.makeCylinder(4.0, 18.0, App.Vector(20.0, d - 18.0, 20.0), App.Vector(0, 1, 0))
    door_bond_stud = Part.makeCylinder(4.0, 18.0, App.Vector(w - 25.0, 0.0, 20.0), App.Vector(0, 1, 0))
    return compound([high_glands, logic_glands, pe_stud, door_bond_stud])


def make_cable_management(params: dict):
    return compound([*(make_wire_route(spec) for spec in wire_route_specs(params)), make_glands_and_pe(params)])


def make_thermal_validation_zone(params: dict):
    # Reserved analysis volume only: no vent or fan selection is implied.
    return Part.makeBox(80.0, 18.0, 80.0, App.Vector(25.0, 2.0, 25.0)).fuse(
        Part.makeBox(80.0, 18.0, 80.0, App.Vector(25.0, 2.0, 295.0))
    )


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
            make_service_keepouts(params),
            make_thermal_validation_zone(params),
        ]
    )
