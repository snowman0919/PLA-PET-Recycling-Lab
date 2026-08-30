#!/usr/bin/env python3
"""Generate the Fusion-neutral v0.6 handoff directly from FreeCAD source shapes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from generate import normalize_step  # noqa: E402
from geometry import (  # noqa: E402
    assembly_objects,
    bearing_side_plate,
    cutter_shaft,
    down_die_body,
    down_die_breaker_plate,
    down_die_copper_gasket,
    down_die_insert,
    down_die_relief_retainer,
    spool_bearing_plate_shape,
)
from manufacturing import extruder_barrel, extruder_barrel_process_coupon  # noqa: E402

OUT = ROOT / "exports" / "fusion_validation"
GEOMETRY = OUT / "geometry"
LOADS = OUT / "loads"
RESULTS = OUT / "results"
CORRELATION = ROOT / "analysis" / "cross_solver"
ENVELOPE_PATH = ROOT / "analysis" / "load_cases" / "openmodelica_dynamic_envelope.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def compound(items: list[dict], names: set[str] | None = None, group: str | None = None) -> Part.Shape:
    selected = [
        item["shape"]
        for item in items
        if (names is None or item["name"] in names) and (group is None or item["group"] == group)
    ]
    if not selected:
        raise ValueError(f"empty compound names={names} group={group}")
    return Part.makeCompound(selected)


def source_tree_hash() -> str:
    digest = hashlib.sha256()
    for path in (
        ROOT / "cad/parameters/baseline.json",
        ROOT / "cad/freecad/compact/geometry.py",
        ROOT / "cad/freecad/compact/manufacturing.py",
        ROOT / "analysis/load_cases/openmodelica_dynamic_envelope.json",
    ):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def export_geometry(source_sha: str) -> list[list[object]]:
    items = assembly_objects()
    frame = compound(items, group="frame")
    shredder_frame_names = {
        "CutterPlateFront", "CutterPlateRear", "MotorMountPlate", "BearingRetainerFront",
        "BearingRetainerRear", "M6Fastener70_550", "M6Fastener70_645", "M6Fastener190_550",
        "M6Fastener190_645",
    }
    rotor_support_names = {
        "CutterPlateFront", "CutterPlateRear", "Shaft105", "Shaft153", "Bearing105_315",
        "Bearing105_455", "Bearing153_315", "Bearing153_455", "BearingRetainerFront",
        "BearingRetainerRear",
    }
    hot_zone_names = {
        "Barrel", "BarrelBandHeaterZ1", "BarrelBandHeaterZ2", "BarrelBandHeaterZ3",
        "DownDieBody", "DownDieBreaker", "DownDieInsert", "DownDieRelief", "DownDieGasket",
        "DieCartridgeHeater", "BarrelThermalFuse", "DieThermalFuse",
    }
    spool_support_names = {
        "DancerArm", "DancerSupportPlate", "DancerSupportPost", "DancerPivotAxle",
        "DancerEndRoller", "DancerEndAxle", "SpoolSpindle", "SpoolBearingPlateFront",
        "SpoolBearingPlateRear", "TraverseRodA", "TraverseRodB", "TraverseEndPlateLeft",
        "TraverseEndPlateRight", "SpoolMotorMount",
    }
    die = Part.makeCompound([
        down_die_body(), down_die_breaker_plate(), down_die_insert(),
        down_die_relief_retainer(), down_die_copper_gasket(),
    ])
    shapes = {
        "frame.step": frame,
        "shredder_frame.step": compound(items, shredder_frame_names),
        "shredder_rotor_support.step": compound(items, rotor_support_names),
        "cutter_shaft.step": cutter_shaft(),
        "bearing_plate.step": bearing_side_plate(),
        "extruder_hot_zone.step": compound(items, hot_zone_names),
        "die.step": die,
        "thermocouple_bore_coupon.step": extruder_barrel_process_coupon(),
        "spooler_support.step": compound(items, spool_support_names),
    }
    roles = {
        "frame.step": "global metal load path and table interface",
        "shredder_frame.step": "shredder fixed support and motor plate",
        "shredder_rotor_support.step": "two-shaft bearing support assembly",
        "cutter_shaft.step": "decision-critical shaft",
        "bearing_plate.step": "decision-critical bearing plate",
        "extruder_hot_zone.step": "barrel/heater/die thermal assembly",
        "die.step": "pressure relief and die interfaces",
        "thermocouple_bore_coupon.step": "matched material/process coupon envelope",
        "spooler_support.step": "metal spindle/dancer/traverse support",
    }
    rows = []
    for filename, shape in shapes.items():
        path = GEOMETRY / filename
        doc = App.newDocument("FusionValidation_" + filename.removesuffix(".step"))
        obj = doc.addObject("PartDesign::Feature", "ControllingShape")
        obj.Label = filename.removesuffix(".step")
        obj.Shape = shape
        doc.recompute()
        Part.export([obj], str(path))
        App.closeDocument(doc.Name)
        normalize_step(path)
        box = shape.BoundBox
        rows.append([
            filename, roles[filename], "mm", source_sha, source_tree_hash(), sha256(path),
            f"{box.XLength:.6f}", f"{box.YLength:.6f}", f"{box.ZLength:.6f}", f"{shape.Volume:.6f}",
            "FreeCAD Python controlling geometry",
        ])
    return rows


def load_cases(envelope: dict, source_sha: str) -> list[dict]:
    loads = envelope["loads"]
    caps = envelope["design_caps"]
    blocked_thrust = 6.0e6 * math.pi * 0.016**2 / 4
    cases = [
        ("LC01", "rated shredder dynamic envelope", "shredder_rotor_support.step", {"cutter_torque_nm": loads["peak_cutter_torque_nm"], "phase_torque_nm": loads["peak_phase_torque_nm"]}),
        ("LC02", "mechanical fuse shaft jam", "cutter_shaft.step", {"cutter_torque_nm": caps["mechanical_fuse_cutter_equivalent_nm"], "bearing_load_n": loads["peak_bearing_load_n"]}),
        ("LC03", "phase gear load reversal", "shredder_rotor_support.step", {"phase_torque_nm": caps["phase_allowable_torque_nm"], "reversal": True}),
        ("LC04", "peak bearing reaction", "bearing_plate.step", {"bearing_load_n": loads["peak_bearing_load_n"]}),
        ("LC05", "peak chain force and overhang", "cutter_shaft.step", {"chain_force_n": loads["peak_chain_force_n"], "overhang_mm": 30.0}),
        ("LC06", "blocked die pressure trip", "extruder_hot_zone.step", {"pressure_mpa": 6.0, "axial_thrust_n": blocked_thrust}),
        ("LC07", "PLA thermal steady/transient", "extruder_hot_zone.step", {"barrel_setpoint_c": 205.0, "ambient_c": 25.0, "heater_total_w": 360.0}),
        ("LC08", "PET thermal steady/transient", "extruder_hot_zone.step", {"barrel_setpoint_c": 255.0, "ambient_c": 25.0, "heater_total_w": 360.0}),
        ("LC09", "full spool plus line tension", "spooler_support.step", {"spool_mass_kg": 1.35, "line_tension_n": 8.0, "gravity_m_s2": 9.80665}),
        ("LC10", "global frame reaction/modal/buckling", "frame.step", {"peak_frame_reaction_n": loads["peak_bearing_load_n"] * 0.7, "anchor_count": 4}),
    ]
    rows = []
    for case_id, title, geometry, values in cases:
        payload = {
            "schema_version": "1.0",
            "revision": "implementation-crosssolver-v0.6",
            "case_id": case_id,
            "title": title,
            "source_git_sha": source_sha,
            "source_tree_sha256": source_tree_hash(),
            "geometry": geometry,
            "geometry_sha256": sha256(GEOMETRY / geometry),
            "source_envelope": "analysis/load_cases/openmodelica_dynamic_envelope.json",
            "source_envelope_sha256": sha256(ENVELOPE_PATH),
            "loads": values,
            "units": "mm, N, N*mm, MPa, degC, s unless key suffix states otherwise",
            "physical_test_state": "NOT_RUN",
        }
        path = LOADS / f"{case_id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        rows.append({"case_id": case_id, "title": title, "geometry": geometry, "file": path.name})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", help="exact committed source revision; default is git HEAD")
    # FreeCADCmd keeps its own `-c` flag in sys.argv when code is piped to the console.
    args, _freecad_args = parser.parse_known_args()
    source_sha = args.source_sha or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if len(source_sha) != 40:
        raise SystemExit("source SHA must be a full 40-character Git object id")
    for directory in (GEOMETRY, LOADS, RESULTS, CORRELATION):
        directory.mkdir(parents=True, exist_ok=True)
    envelope = json.loads(ENVELOPE_PATH.read_text())
    shutil.copyfile(ENVELOPE_PATH, LOADS / "openmodelica_dynamic_envelope.json")
    geometry_rows = export_geometry(source_sha)
    write_csv(
        OUT / "model_manifest.csv",
        ["file", "role", "units", "source_git_sha", "source_tree_sha256", "step_sha256", "bbox_x_mm", "bbox_y_mm", "bbox_z_mm", "volume_mm3", "authority"],
        geometry_rows,
    )
    cases = load_cases(envelope, source_sha)
    load_manifest_rows = []
    for case in cases:
        path = LOADS / case["file"]
        load_manifest_rows.append([case["case_id"], case["title"], case["geometry"], case["file"], sha256(path), source_sha, sha256(GEOMETRY / case["geometry"])])
    write_csv(
        OUT / "load_case_manifest.csv",
        ["case_id", "title", "geometry", "load_file", "load_file_sha256", "source_git_sha", "geometry_sha256"],
        load_manifest_rows,
    )
    shutil.copyfile(OUT / "load_case_manifest.csv", LOADS / "load_case_manifest.csv")
    load_manifest_hash = sha256(OUT / "load_case_manifest.csv")
    run_binding = {
        "revision": "implementation-crosssolver-v0.6",
        "source_git_sha": source_sha,
        "source_tree_sha256": source_tree_hash(),
        "model_manifest_sha256": sha256(OUT / "model_manifest.csv"),
        "load_case_manifest_sha256": load_manifest_hash,
        "openmodelica_envelope_sha256": sha256(ENVELOPE_PATH),
        "fusion_result_state": "PENDING_EXTERNAL_EXECUTION",
        "required_result_binding": ["source_git_sha", "step_sha256", "load_case_manifest_sha256"],
    }
    (OUT / "run_binding.json").write_text(json.dumps(run_binding, indent=2, sort_keys=True) + "\n")
    result_manifest = {
        **run_binding,
        "runs": [],
        "status": "PENDING",
        "note": "No Autodesk Fusion result was supplied or executed in this repository environment.",
    }
    (RESULTS / "fusion_result_manifest.json").write_text(json.dumps(result_manifest, indent=2, sort_keys=True) + "\n")
    print(f"FUSION_NEUTRAL_PACKAGE_OK geometry={len(geometry_rows)} load_cases={len(cases)} source={source_sha[:12]}")


if __name__ == "__main__":
    main()
