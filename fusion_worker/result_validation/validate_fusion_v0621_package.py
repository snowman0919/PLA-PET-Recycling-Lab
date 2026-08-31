#!/usr/bin/env python3
"""Validate the LC11 package without treating pending solver work as completed."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


EXPECTED_GEOMETRY = {
    "geometry/PF-04.step": "8508c8b3d594cd63c650f8e527ed0923a43134a65068ec1df27e067eca776892",
    "geometry/PF-05.step": "192b7fee75a114ae22ad5eabc76519ae21bbbae8ce3e6709bb761e019a0f422d",
    "geometry/process_feed_assembly.step": "2741a3cb1e4454c8b068c045b2147a62378a571c8fde3874d87f8ee0dcf4091a",
}
EXPECTED_SOURCE_PATHS = {
    "geometry/PF-04.step": "exports/process_v0621/parts/PF-04/PF-04.step",
    "geometry/PF-05.step": "exports/process_v0621/parts/PF-05/PF-05.step",
    "geometry/process_feed_assembly.step": "exports/process_v0621/process_feed_assembly.step",
}
RESULT_HEADER = [
    "run_id", "case_id", "study_type", "engineering_source_sha", "step_file",
    "step_sha256", "load_case_manifest_sha256", "mesh_level", "element_count",
    "metric", "value", "unit", "solver_name", "solver_version", "completed_utc",
    "evidence_file", "evidence_sha256", "operator", "status", "notes",
]


def fail(message: str) -> None:
    raise SystemExit(f"FUSION_V0621_PACKAGE_FAIL {message}")


def digest(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid JSON {path}: {error}")


def rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as error:
        fail(f"invalid CSV {path}: {error}")


def committed_blob(repo: Path, commit: str, path: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{path}"], cwd=repo, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        fail(f"cannot read {commit}:{path}: {error.stderr.decode(errors='replace').strip()}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_fusion_v0621_package.py PACKAGE_ROOT")
    package = Path(sys.argv[1]).resolve()
    repo = package.parents[1]

    state = load_json(package / "package_state.json")
    lock = load_json(package / "engineering_source_lock.json")
    binding = load_json(package / "run_binding.json")
    load = load_json(package / "loads/LC11.json")
    legacy = load_json(package / "legacy_package_reference.json")
    schema = load_json(package / "results/result_schema.json")

    if state.get("package_id") != "PPR-v0.6.2.1-LC11":
        fail("package id mismatch")
    for rel_path, expected in EXPECTED_GEOMETRY.items():
        actual = digest(package / rel_path)
        if actual != expected:
            fail(f"geometry hash mismatch {rel_path}: {actual}")
        source = lock.get("geometry_sources", {}).get(rel_path, {})
        if source.get("source_path") != EXPECTED_SOURCE_PATHS[rel_path] or source.get("sha256") != expected:
            fail(f"source lock mismatch {rel_path}")

    models = {row.get("file"): row for row in rows(package / "model_manifest.csv")}
    if set(models) != set(EXPECTED_GEOMETRY):
        fail("model manifest must contain exactly PF-04, PF-05 and process assembly")
    for rel_path, expected in EXPECTED_GEOMETRY.items():
        if models[rel_path].get("step_sha256") != expected:
            fail(f"model manifest hash mismatch {rel_path}")
    if models["geometry/PF-05.step"].get("analysis_body") != "yes":
        fail("PF-05 must be the primary analysis body")
    if models["geometry/PF-04.step"].get("analysis_body") != "no":
        fail("PF-04 must remain suppressed/reference in the attachment solve")

    if load.get("case_id") != "LC11_FEEDER_ATTACHMENT":
        fail("LC11 id mismatch")
    loads = load.get("loads", {})
    if loads.get("reaction_torque_n_mm") != 2200.0 or loads.get("inventory_vertical_load_n") != 5.4:
        fail("LC11 must bind exactly 2.2 N*m and 5.4 N")
    acceptance = load.get("acceptance", {})
    if acceptance.get("minimum_safety_factor") != 2.0:
        fail("minimum safety factor must be 2.0")
    if acceptance.get("medium_to_fine_max_displacement_change_percent_max") != 5.0:
        fail("mesh convergence limit must be 5 percent")

    material_rows = rows(package / "materials.csv")
    if len(material_rows) != 1 or material_rows[0].get("material_id") != "MAT-304":
        fail("exactly one AISI 304 material row is required")
    if material_rows[0].get("allowable_mpa") != "107.5":
        fail("AISI 304 allowable must be 107.5 MPa")
    constraint_rows = rows(package / "constraints.csv")
    if len(constraint_rows) != 1 or constraint_rows[0].get("constraint_id") != "BC11":
        fail("BC11 constraint missing")
    contact_rows = rows(package / "contact_pairs.csv")
    if {row.get("pair_id") for row in contact_rows} != {"CP11", "CP12"}:
        fail("LC11 clearance and attachment surrogate records are required")

    mesh_rows = rows(package / "mesh_plan.csv")
    if [row.get("mesh_level") for row in mesh_rows] != ["coarse", "medium", "fine"]:
        fail("mesh plan must be ordered coarse, medium, fine")
    global_sizes = [float(row["global_size_mm"]) for row in mesh_rows]
    local_sizes = [float(row["local_flange_size_mm"]) for row in mesh_rows]
    if not (global_sizes[0] > global_sizes[1] > global_sizes[2] > 0):
        fail("global mesh sizes must refine monotonically")
    if not (local_sizes[0] > local_sizes[1] > local_sizes[2] > 0):
        fail("local mesh sizes must refine monotonically")

    case_rows = rows(package / "load_case_manifest.csv")
    if len(case_rows) != 1 or case_rows[0].get("case_id") != "LC11_FEEDER_ATTACHMENT":
        fail("load manifest must contain exactly LC11")
    if case_rows[0].get("torque_n_mm") != "2200.0" or case_rows[0].get("axial_force_n") != "5.4":
        fail("load manifest values mismatch")
    if binding.get("model_manifest_sha256") != digest(package / "model_manifest.csv"):
        fail("model manifest binding mismatch")
    if binding.get("load_case_manifest_sha256") != digest(package / "load_case_manifest.csv"):
        fail("load case manifest binding mismatch")

    expected_metrics = {row.get("metric") for row in rows(package / "expected_metrics.csv")}
    required_metrics = {
        "element_count", "max_displacement", "non_singular_von_mises_stress",
        "minimum_safety_factor", "reaction_force_z", "reaction_moment_z",
        "medium_to_fine_displacement_change", "force_reaction_imbalance",
        "moment_reaction_imbalance",
    }
    if expected_metrics != required_metrics:
        fail("expected metric set mismatch")
    with (package / "results/fusion_result_template.csv").open(newline="") as handle:
        header = next(csv.reader(handle), [])
    if header != RESULT_HEADER:
        fail("result template header mismatch")
    if schema.get("properties", {}).get("case_id", {}).get("const") != "LC11_FEEDER_ATTACHMENT":
        fail("result schema case binding missing")

    if legacy.get("policy") != "READ_ONLY_REFERENCE_DO_NOT_COPY_OR_MODIFY":
        fail("legacy package must be read-only reference")
    if legacy.get("mandatory_cases") != ["LC02", "LC04", "LC05", "LC07", "LC08", "LC10"]:
        fail("legacy mandatory case list mismatch")
    if legacy.get("state") != "PENDING_EXTERNAL_EXECUTION":
        fail("legacy package state must remain pending")

    package_state = state.get("package_state")
    if package_state == "AWAITING_ENGINEERING_SOURCE_COMMIT":
        if state.get("engineering_source_sha") is not None or state.get("fusion_execution_permitted") is not False:
            fail("awaiting state cannot carry an engineering SHA or permit execution")
        if lock.get("engineering_source_sha") is not None or binding.get("engineering_source_sha") is not None:
            fail("awaiting lock/binding must have null engineering SHA")
        if binding.get("source_git_sha") is not None:
            fail("awaiting run binding must have null source Git SHA")
    elif package_state == "BOUND_TO_ENGINEERING_SOURCE":
        commit = state.get("engineering_source_sha")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            fail("bound state requires full engineering SHA")
        if state.get("fusion_execution_permitted") is not True:
            fail("bound state must permit Fusion execution")
        if lock.get("engineering_source_sha") != commit:
            fail("source lock SHA mismatch")
        if binding.get("engineering_source_sha") != commit or binding.get("source_git_sha") != commit:
            fail("run binding SHA mismatch")
        for packaged_path, source_path in EXPECTED_SOURCE_PATHS.items():
            if hashlib.sha256(committed_blob(repo, commit, source_path)).hexdigest() != EXPECTED_GEOMETRY[packaged_path]:
                fail(f"committed source mismatch {source_path}")
        source_manifest_hash = hashlib.sha256(
            committed_blob(repo, commit, "exports/process_v0621/manifest.json")
        ).hexdigest()
        if lock.get("source_process_manifest_sha256") != source_manifest_hash:
            fail("committed process manifest hash mismatch")
        if binding.get("source_process_manifest_sha256") != source_manifest_hash:
            fail("run binding process manifest hash mismatch")
    else:
        fail(f"unsupported package state {package_state!r}")

    if lock.get("package_state") != package_state or binding.get("package_state") != package_state:
        fail("state/lock/run binding state mismatch")
    print(
        "FUSION_V0621_PACKAGE_OK "
        f"state={package_state} execution_permitted={str(state['fusion_execution_permitted']).lower()}"
    )


if __name__ == "__main__":
    main()
