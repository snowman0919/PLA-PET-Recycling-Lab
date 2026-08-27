#!/usr/bin/env python3
"""Geometry gates for control enclosure segregation and service panels."""

from __future__ import annotations

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
    make_backplate_and_partition,
    make_cable_management,
    make_control_enclosure,
    make_face_controls,
    make_high_current_devices,
    make_logic_devices,
    make_shell,
    make_split_door,
)


def main():
    p = load_parameters()["control_enclosure"]
    shell = make_shell(p)
    high = make_high_current_devices(p)
    logic = make_logic_devices(p)
    door = make_split_door(p)
    face = make_face_controls(p)
    cable = make_cable_management(p)
    partition_gap = logic.BoundBox.XMin - high.BoundBox.XMax
    checks = {
        "assembly_valid": make_control_enclosure(p).isValid(),
        "shell_width_mm": shell.BoundBox.XLength,
        "shell_depth_mm": shell.BoundBox.YLength,
        "shell_height_mm": shell.BoundBox.ZLength,
        "high_logic_partition_gap_mm": partition_gap,
        "high_logic_intersection_mm3": high.common(logic).Volume,
        "split_door_max_part_mm": max(p["door_split_width_mm"], p["height_mm"], p["sheet_thickness_mm"]),
        "face_control_solid_count": len(face.Solids),
        "cable_management_solid_count": len(cable.Solids),
        "partition_present": len(make_backplate_and_partition(p).Solids) >= 4,
    }
    assert checks["assembly_valid"], checks
    assert checks["shell_width_mm"] == 300.0 and checks["shell_depth_mm"] == 220.0 and checks["shell_height_mm"] == 180.0, checks
    assert checks["high_logic_partition_gap_mm"] >= p["minimum_partition_gap_mm"], checks
    assert checks["high_logic_intersection_mm3"] < 1e-7, checks
    assert checks["split_door_max_part_mm"] <= 210.0, checks
    assert checks["face_control_solid_count"] == 5, checks
    assert checks["cable_management_solid_count"] == 5, checks
    assert checks["partition_present"], checks
    report = {"checks": checks, "status": "PASS", "limitations": [
        "Rigid envelopes prove spatial segregation only; selected device creepage, heat, terminal access and wire bend radii remain open.",
        "PE stud geometry does not prove bonding resistance or fault-current capacity.",
        "Door cutouts and control envelopes require supplier drawings and an impact/ingress review.",
    ]}
    output = ROOT / "simulation" / "control" / "control_enclosure_geometry.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("CONTROL_ENCLOSURE_GEOMETRY_OK")


if __name__ == "__main__":
    main()
