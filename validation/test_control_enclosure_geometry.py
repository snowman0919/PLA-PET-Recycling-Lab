#!/usr/bin/env python3
"""Geometry and traceability gates for the BOM-driven control enclosure."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "cad" / "freecad" / "control_enclosure"
COMMON = HERE.parent / "common"
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(HERE))
from project import load_parameters  # noqa: E402
from geometry import (  # noqa: E402
    box_from_spec,
    make_backplate_and_partition,
    make_cable_management,
    make_control_enclosure,
    make_estop_candidate,
    make_face_controls,
    make_high_current_devices,
    make_logic_devices,
    make_pcb_board,
    make_pcb_reserved_keepout,
    make_pcb_standoffs,
    physical_shape_from_spec,
    make_service_keepouts,
    make_shell,
    make_split_door,
    wire_route_specs,
)


TOL = 1e-7


def main():
    p = load_parameters()["control_enclosure"]
    shell = make_shell(p)
    high = make_high_current_devices(p)
    logic = make_logic_devices(p)
    door = make_split_door(p)
    face = make_face_controls(p)
    cable = make_cable_management(p)
    pcb = make_pcb_board(p)
    pcb_keepout = make_pcb_reserved_keepout(p)
    standoffs = make_pcb_standoffs(p)
    service = make_service_keepouts(p)
    selected = [box_from_spec(spec) for spec in p["layout"]["selected_candidates"]]
    qualification = [physical_shape_from_spec(spec) for spec in p["layout"]["qualification_candidates"]]
    qualification_specs = p["layout"]["qualification_candidates"]
    placeholders = [box_from_spec(spec) for spec in p["layout"]["placeholders"]]
    routes = [box_from_spec(spec) for spec in wire_route_specs(p)]
    partition_gap = logic.BoundBox.XMin - high.BoundBox.XMax
    candidate_placeholder_intersection = sum(a.common(b).Volume for a in [*selected, *qualification] for b in placeholders)
    qualification_pair_intersection = sum(
        a.common(b).Volume
        for index, a in enumerate(qualification)
        for b in qualification[index + 1:]
    )
    device_route_intersection = sum(
        device.common(route).Volume
        for device in [*selected, *qualification, *placeholders, pcb_keepout]
        for route in routes
    )

    layout_path = ROOT / "electronics" / "architecture" / "control_enclosure_layout.csv"
    assert layout_path.exists(), "control-enclosure layout CSV has not been generated"
    with layout_path.open(newline="", encoding="utf-8") as stream:
        layout_rows = list(csv.DictReader(stream))
    bom_ids = {row["Part ID"] for row in csv.DictReader((ROOT / "bom" / "bom.csv").open(newline="", encoding="utf-8"))}
    traced_ids = {row["bom_part_id"] for row in layout_rows}
    expected_traced = {
        "SAF-REL-001", "ELE-BUCK-001", "SAF-EST-001", "ELE-PCB-IF",
        "SYS-CTRL-001", "SYS-CTRL-002", "SAF-CON-001", "SAF-FUS-001",
        "SAF-FUS-HLD", "ELE-HTR-DRV", "ELE-HTR-HS", "CTL-ENC-001", "MISC-WIR-001",
    }
    states = {row["placement_state"] for row in layout_rows}
    route_rows = [row for row in layout_rows if row["placement_state"] == "WIRE_ROUTE_RESERVED"]

    checks = {
        "assembly_valid": make_control_enclosure(p).isValid(),
        "shell_width_mm": shell.BoundBox.XLength,
        "shell_depth_mm": shell.BoundBox.YLength,
        "shell_height_mm": shell.BoundBox.ZLength,
        "high_logic_partition_gap_mm": partition_gap,
        "high_logic_intersection_mm3": high.common(logic).Volume,
        "candidate_placeholder_intersection_mm3": candidate_placeholder_intersection,
        "qualification_pair_intersection_mm3": qualification_pair_intersection,
        "tower_zone_contactor_count": sum(len(physical_shape_from_spec(spec).Solids) for spec in qualification_specs if spec["part_id"] == "SAF-CON-001"),
        "branch_fuse_holder_count": sum(len(physical_shape_from_spec(spec).Solids) for spec in qualification_specs if spec["part_id"] == "SAF-FUS-HLD"),
        "heater_ssr_count": sum(len(physical_shape_from_spec(spec).Solids) for spec in qualification_specs if spec["part_id"] == "ELE-HTR-DRV"),
        "heater_heat_sink_count": sum(len(physical_shape_from_spec(spec).Solids) for spec in qualification_specs if spec["part_id"] == "ELE-HTR-HS"),
        "device_wire_route_intersection_mm3": device_route_intersection,
        "door_width_mm": door.BoundBox.XLength,
        "door_height_mm": door.BoundBox.ZLength,
        "face_control_solid_count": len(face.Solids),
        "cable_management_solid_count": len(cable.Solids),
        "partition_present": len(make_backplate_and_partition(p).Solids) >= 4,
        "pcb_width_mm": pcb.BoundBox.XLength,
        "pcb_height_mm": pcb.BoundBox.ZLength,
        "pcb_thickness_mm": pcb.BoundBox.YLength,
        "pcb_standoff_count": len(standoffs.Solids),
        "pcb_keepout_depth_mm": pcb_keepout.BoundBox.YLength,
        "service_keepout_valid": service.isValid(),
        "layout_row_count": len(layout_rows),
        "wire_route_class_count": len(route_rows),
        "all_layout_bom_ids_exist": traced_ids <= bom_ids,
    }
    assert checks["assembly_valid"], checks
    assert checks["shell_width_mm"] == 500.0 and checks["shell_depth_mm"] == 210.0 and checks["shell_height_mm"] == 400.0, checks
    assert checks["high_logic_partition_gap_mm"] >= p["minimum_partition_gap_mm"], checks
    assert checks["high_logic_intersection_mm3"] < TOL, checks
    assert checks["candidate_placeholder_intersection_mm3"] < TOL, checks
    assert checks["qualification_pair_intersection_mm3"] < TOL, checks
    assert checks["tower_zone_contactor_count"] == 2, checks
    assert checks["branch_fuse_holder_count"] == 14, checks
    assert checks["heater_ssr_count"] == 6, checks
    assert checks["heater_heat_sink_count"] == 2, checks
    assert checks["device_wire_route_intersection_mm3"] < TOL, checks
    assert checks["door_width_mm"] == 500.0 and checks["door_height_mm"] == 400.0, checks
    assert checks["face_control_solid_count"] == 6, checks
    assert checks["cable_management_solid_count"] == 8, checks
    assert checks["partition_present"], checks
    assert checks["pcb_width_mm"] == 190.0 and checks["pcb_height_mm"] == 130.0, checks
    assert abs(checks["pcb_thickness_mm"] - 1.6) < 1e-6, checks
    assert checks["pcb_standoff_count"] == 4, checks
    assert checks["pcb_keepout_depth_mm"] == 32.0, checks
    assert checks["service_keepout_valid"], checks
    assert checks["layout_row_count"] == 21, checks
    assert checks["wire_route_class_count"] == 4, checks
    assert len({row["zone"] for row in route_rows}) == 4, route_rows
    assert checks["all_layout_bom_ids_exist"], traced_ids - bom_ids
    assert expected_traced <= traced_ids, expected_traced - traced_ids
    assert {
        "SELECTED_CANDIDATE_ENVELOPE", "PCB_RESERVED_FABRICATION_HOLD",
        "QUALIFICATION_CANDIDATE_ENVELOPE",
        "USER_INVENTORY_VERIFY_MEASUREMENT", "PLACEHOLDER_TBD_NOT_ORDERABLE",
        "WIRE_ROUTE_RESERVED",
    } <= states, states
    assert p["terminal_service_keepout_mm"] >= 30.0
    assert make_estop_candidate(p).BoundBox.YMax <= min(spec["origin_mm"][1] for spec in p["layout"]["qualification_candidates"] if spec["part_id"] == "SAF-CON-001"), "E-stop rear keep-out collides with contactor candidate"

    report = {
        "checks": checks,
        "status": "VIRTUAL_LAYOUT_PASS_PHYSICAL_APPROVAL_OPEN",
        "placement_legend": {
            "green": "selected candidate envelope",
            "yellow": "exact-MPN qualification candidate envelope",
            "blue": "PCB reserved / user inventory verification",
            "orange": "TBD placeholder, not orderable",
            "red_yellow_blue_green_routes": "high-current, hardwired safety, logic/sensor and PE reservations",
            "magenta": "service keep-out",
        },
        "limitations": [
            "Candidate-envelope fit is not a purchase, panel-build or safety approval.",
            "Thirty millimetres is a reserved minimum; selected wire gauge, ferrule and terminal data determine final bend/access clearance.",
            "PE studs and route geometry do not prove bonding resistance or fault-current capacity.",
            "Thermal rise, ingress, SCCR, creepage and exact door-device rear depth remain open.",
        ],
    }
    output = ROOT / "simulation" / "control" / "control_enclosure_geometry.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("CONTROL_ENCLOSURE_GEOMETRY_OK")


if __name__ == "__main__":
    main()
