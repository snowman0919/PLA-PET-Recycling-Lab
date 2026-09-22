"""I1 asset pipeline: STEP -> decimated collision meshes + traceability sidecars.

Reads (never writes): c2.1/cad/PPR_C2_1_S2_transmission.step and the
parametric truth (c2/src/engineering.py, c2.1/src/transmission.py).
Writes (only under c2.2/): STL meshes + per-asset JSON sidecars.

Fallback: if the STEP import fails, emits the parametric S2 hook-rotor
profile mesh (hook_polygon extruded over the 40 mm process width) with an
explicit fallback note. Exits nonzero iff any requested asset is invalid
or missing (empty file, invalid solid, unwritten sidecar).

Evidence: GEOMETRIC_ONLY. Mass/inertia/material are recorded as
ASSUMPTION (null) — never invented. Units mm, frame F0, identity transform.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[2]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "c2" / "src"))

EXPECTED_STEP_SHA = "fbba8932ab7a132d67eeafeba519bd368a78bf564a22e4d8ea59e5df94f5a42b"
STEP_REL = "c2.1/cad/PPR_C2_1_S2_transmission.step"

# Zero-based solid index in export order (c2.1/src/build_cad.py
# fixed_components 31 + moving; label order pinned by cad_validation.json).
TARGETS = {
    "RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE": 33,
    "C2_FIXED_SHEAR_SENSOR_BORE": 6,
    "C2_PERFORATED_SCREEN_REFERENCE": 7,
    "INPUT_ECCENTRIC_SHAFT": 31,
    "OUTPUT_PIN_CARRIER_AND_SHAFT": 34,
    "OUTPUT_ROLLER_1": 35,
}

LODS = {
    "fine": {"linear_tolerance_mm": 0.1, "angular_tolerance_rad": 0.1},
    "coarse": {"linear_tolerance_mm": 0.5, "angular_tolerance_rad": 0.5},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    import subprocess

    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
        text=True, check=True,
    ).stdout.strip()


def write_sidecar(path: Path, record: dict) -> None:
    path.write_text(json.dumps(record, indent=2) + "\n")


FULL_STEP_REL = "c2.1/cad/PPR_C2_1_machine_integration.step"

# Kinematic body assignment for the integrated machine (C2.1-S2 task spec):
# S1 cutter shafts A/B + cutter stacks, S2 input eccentric, rotor, output
# carrier/rollers are MOVING; everything else STATIC. The M1 input shaft
# assembly (shaft, coupling, 15T pinion halves, 24T chain-B sprocket, keys)
# is the single actuated input body. DRV-SP24-B25 (chain-A sprocket keyed to
# the S1 main shaft) is kept STATIC per the task's explicit classification;
# its 25 H7 bore on the 25 shaft is a by-design journal-fit contact pair.
MOVING_BODIES: dict[str, set[str]] = {
    "IN_SHAFT": {"DRV-IN-SHAFT_001", "DRV-CPL12_001", "DRV-SH15R_001",
                 "DRV-SH15L_001", "DRV-SP24-B12_001", "KEY-4-70_001",
                 "KEY-4-16_001"},
    "S1A": {"S1-SHAFT-A_001", "KEY-8-154_001", "KEY-8-25_001", "S1-SYNC_001",
            "DRV-SP24-B25_001"}
         | {f"S1-CUT-A-P{i:02d}_001" for i in range(13)}
         | {f"S1-SPACER-A_{i:03d}" for i in range(1, 13)},
    "S1B": {"S1-SHAFT-B_001", "KEY-8-154_002", "KEY-8-25_002", "S1-SYNC_002"}
         | {f"S1-CUT-B-P{i:02d}_001" for i in range(13)}
         | {f"S1-SPACER-B_{i:03d}" for i in range(1, 13)},
    "S2_ECC": {"INPUT_ECCENTRIC_SHAFT", "ECCENTRIC_BEARING_ENVELOPE_UNRATED",
               "DRV-SP12-B12_001"},
    "S2_ROTOR": {"RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE"},
    "S2_CARRIER": {"OUTPUT_PIN_CARRIER_AND_SHAFT"},
    **{f"S2_ROLLER_{i}": {f"OUTPUT_ROLLER_{i}"} for i in range(1, 7)},
}
STATIC_BODY = "STATIC"


def _bbox(shape):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    box = Bnd_Box()
    BRepBndLib.Add_s(shape.wrapped, box, True)
    return box.Get()  # xmin, ymin, zmin, xmax, ymax, zmax


def master_instances(cfg):
    master = json.loads((REPO / cfg["legacy_master"]).read_text())
    return master["instances"]


def _reconstruct_parts(cq):
    """Deterministic (name, group, shape) list in integration-STEP export
    order: legacy master instances (excluding legacy S2 group) then the
    c2.1 subassembly components (build_cad.components(), theta=0).

    Mirrors c2.1/src/build_machine_integration.py exactly (y-overrides,
    c2_subassembly_transform). Runs under the cad-env (cadquery 2.8).
    """
    repo = REPO
    cfg = json.loads((repo / "c2.1" / "design" / "machine_integration.json")
                     .read_text())
    excluded = cfg["excluded_legacy_group"]
    overrides = cfg["legacy_instance_y_overrides_mm"]

    part_cache: dict[str, object] = {}

    def load_part(name):
        if name not in part_cache:
            part_cache[name] = cq.importers.importStep(
                str(repo / "cad/parts" / (name + ".step"))).val()
        return part_cache[name]

    parts = []  # records: {"name", "group", "shape"}
    _dt = _import_c21_module(repo, "drive_teeth")
    _bmi = _import_c21_module(repo, "build_machine_integration")
    for item in master_instances(cfg):
        if item["group"] == excluded:
            continue
        if item["name"] in _bmi.EXCLUDED_LEGACY_INSTANCES:
            continue  # replaced by winder/EL bay real geometry (VP1 stage 2)
        if item["name"] in _dt.INSTANCE_PART:
            # VP1 stage 1: real toothed gear/sprocket solid, same instance
            # name and part-local frame (mirrors the updated
            # build_machine_integration.py legacy_parts())
            shape = _dt.replacement_local_solid(item["name"])
        else:
            shape = load_part(item["part"])
        axis, deg = item["rotation"][:3], item["rotation"][3]
        if deg:
            shape = shape.rotate((0, 0, 0), tuple(axis), deg)
        at = list(item["at"])
        if item["name"] in overrides:
            at[1] = overrides[item["name"]]
        shape = shape.translate(tuple(at))
        parts.append({"name": item["name"], "group": item["group"],
                      "shape": shape})

    _sys = sys
    _sys.path.insert(0, str(repo / "c2.1" / "src"))
    _sys.path.insert(0, str(repo / "c2" / "src"))
    from importlib.util import spec_from_file_location, module_from_spec
    _spec = spec_from_file_location(
        "c21_build_cad", str(repo / "c2.1" / "src" / "build_cad.py"))
    c21_cad = module_from_spec(_spec)
    _spec.loader.exec_module(c21_cad)
    tr = cfg["c2_subassembly_transform"]
    for name, shape in c21_cad.components():
        if name == "GUARD_SECTION_ENVELOPE_HOLD":
            continue  # replaced by real guards (VP1 stage 2)
        shape = shape.rotate((0, 0, 0), tuple(tr["rotation_axis"]),
                             tr["rotation_deg"]).translate(
            tuple(tr["translation_mm"]))
        parts.append({"name": name, "group": "S2-C2.1", "shape": shape})
    # VP1 stage 1/2 parts, in builder order: chains, chute, guards,
    # winder, electrical bay
    for name, solid in _dt.chain_components():
        parts.append({"name": name, "group": "drive", "shape": solid})
    _chute = _import_c21_module(repo, "chute")
    for name, solid in _chute.components():
        parts.append({"name": name, "group": "feed", "shape": solid})
    _guards = _import_c21_module(repo, "guards")
    for name, solid in _guards.components():
        parts.append({"name": name, "group": "guard", "shape": solid})
    _winder = _import_c21_module(repo, "winder")
    for name, solid, group in _winder.components():
        parts.append({"name": name, "group": group, "shape": solid})
    _elec = _import_c21_module(repo, "electrical_bay")
    for name, solid in _elec.components():
        parts.append({"name": name, "group": "electrical", "shape": solid})
    # VP1 stage 3: chain/gear path reliefs cut into legacy solids (in
    # place, mirroring chain_relief.apply(legacy, new_solids))
    new_solids = {r["name"]: r["shape"] for r in parts}
    _relief = _import_c21_module(repo, "chain_relief")
    _relief.apply(parts, new_solids)
    return [(p["name"], p["group"], p["shape"]) for p in parts]


def _import_c21_module(repo, mod_name):
    from importlib.util import spec_from_file_location, module_from_spec
    _spec = spec_from_file_location(
        f"c21_{mod_name}", str(repo / "c2.1" / "src" / f"{mod_name}.py"))
    mod = module_from_spec(_spec)
    _spec.loader.exec_module(mod)
    return mod


def _lod_of(body: str) -> str:
    return "coarse" if body == STATIC_BODY else "fine"


def run_full(out: Path) -> int:
    """Convert ALL solids of the integration STEP to collision meshes.

    Moving solids at fine LOD (0.1mm), static shell solids at coarse LOD
    (0.5mm); per-solid SHA sidecar pattern kept; plus a bodies.json manifest
    consumed by c2.2/sim/full_machine.py.
    """
    import time

    t0 = time.time()
    out = Path(out).resolve()
    full_step = REPO / FULL_STEP_REL
    if not full_step.is_file():
        print(json.dumps({"failures": [f"{FULL_STEP_REL} missing"]}))
        return 1
    step_sha = sha256_file(full_step)
    head = git_head()
    script_sha = sha256_file(HERE)
    out.mkdir(parents=True, exist_ok=True)

    import cadquery as cq

    print("[full] reconstructing placements from assembly sources ...",
          file=sys.stderr, flush=True)
    parts = _reconstruct_parts(cq)
    expected_counts = [len(p[2].Solids()) for p in parts]
    n_expected = sum(expected_counts)
    print(f"[full] reconstruction: {len(parts)} parts, "
          f"{n_expected} expected solids ({time.time()-t0:.0f}s)",
          file=sys.stderr, flush=True)

    print(f"[full] importing integration STEP "
          f"({full_step.stat().st_size/1e6:.1f} MB) ...",
          file=sys.stderr, flush=True)
    t1 = time.time()
    solids = cq.importers.importStep(str(full_step)).solids().vals()
    print(f"[full] STEP import: {len(solids)} solids ({time.time()-t1:.0f}s)",
          file=sys.stderr, flush=True)
    failures: list[str] = []
    adjustments = []
    if len(solids) != n_expected:
        surplus = n_expected - len(solids)
        # multi-solid reconstructed parts: reduce their expected counts by
        # the surplus (the builder exported fewer solids for these; the
        # rest of the order is 1:1). Recorded in the manifest.
        for pi in range(len(parts) - 1, -1, -1):
            if surplus <= 0:
                break
            c = expected_counts[pi]
            if c > 1:
                take = min(surplus, c - 1)
                expected_counts[pi] -= take
                surplus -= take
                adjustments.append({"part": parts[pi][0],
                                    "from": c, "to": expected_counts[pi]})
        if surplus:
            failures.append(f"solid count mismatch: STEP {len(solids)} != "
                            f"expected {n_expected} (unresolved surplus "
                            f"{surplus})")
            print(json.dumps({"failures": failures}), flush=True)
            return 1

    # Order-preserving bbox mapping: the exporter may reorder solids
    # locally, so each reconstructed part consumes the next step solids
    # (with bounded lookahead) whose bboxes fit inside the part bbox.
    # Bboxes are exact STEP-space (verified 1:1 for the ordered prefix).
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib

    def _sbb(solid):
        b = Bnd_Box()
        BRepBndLib.Add_s(solid.wrapped, b, True)
        return b.Get()

    def _fits(inside, outer, tol=0.5):
        return all(outer[i] - tol <= inside[i]
                   and inside[i + 3] <= outer[i + 3] + tol
                   for i in range(3))

    pool = list(range(len(solids)))
    pool_bbs = {i: _sbb(solids[i]) for i in pool}
    records = []
    for (name, group, shape), count in zip(parts, expected_counts):
        pb = _bbox(shape)
        got = [i for i in pool if _fits(pool_bbs[i], pb)][:count]
        if len(got) != count:
            failures.append(f"part {name}: matched {len(got)}/{count} "
                            f"solids")
            continue
        for sidx in got:
            pool.remove(sidx)
            body = next((b for b, names in MOVING_BODIES.items()
                         if name in names), STATIC_BODY)
            records.append({"name": name, "group": group, "body": body,
                            "step_index": sidx, "solid": solids[sidx],
                            "part_bbox": pb, "bbox_ok": True})
    assigned = {r["step_index"] for r in records}
    unassigned = [i for i in range(len(solids)) if i not in assigned]
    if unassigned:
        failures.append(f"{len(unassigned)} step solids unassigned by "
                        f"bbox matching (first: {unassigned[:5]})")
    records.sort(key=lambda r: r["step_index"])

    emitted = []
    for rec in records:
        lod = _lod_of(rec["body"])
        tol = LODS[lod]
        stem = f"{rec['name']}__{lod}"
        stl = out / f"{stem}.stl"
        sidecar = out / f"{stem}.sidecar.json"
        try:
            if not rec["solid"].isValid():
                failures.append(f"{stem}: solid invalid")
                continue
            volume = rec["solid"].Volume()
            cq.exporters.export(rec["solid"], str(stl), "STL",
                                tolerance=tol["linear_tolerance_mm"],
                                angularTolerance=tol["angular_tolerance_rad"])
            if not stl.is_file() or stl.stat().st_size == 0:
                failures.append(f"{stem}: empty STL")
                continue
            write_sidecar(sidecar, {
                "asset_id": rec["name"], "group": rec["group"],
                "kinematic_body": rec["body"], "lod": lod,
                "step_index": rec["step_index"],
                "step_product_name": ("Open CASCADE STEP translator 7.9 1.%d"
                                      % rec["step_index"]),
                "mesh_file": str(stl.relative_to(C22)),
                "mesh_bytes": stl.stat().st_size,
                "mesh_sha256": sha256_file(stl),
                "mesh_format": "STL",
                "source_step": FULL_STEP_REL,
                "source_step_sha256": step_sha,
                "naming_basis": ("deterministic reconstruction order "
                                 "(design/assembly.json instances + "
                                 "build_cad.components); STEP product names "
                                 "are generic"),
                "bbox_containment_ok": rec["bbox_ok"],
                "part_bbox_mm": list(rec["part_bbox"]),
                "revision": head,
                "conversion_script": str(HERE.relative_to(REPO)),
                "conversion_script_sha256": script_sha,
                "tessellation": tol,
                "coords": "F0 identity (no transform applied)",
                "units": "mm",
                "volume_mm3": volume,
                "mass_kg": None, "inertia": None, "material": None,
                "mass_material_status": "ASSUMPTION_UNCHOSEN",
                "evidence_level": "GEOMETRIC_ONLY",
            })
            emitted.append({"name": rec["name"], "body": rec["body"],
                            "lod": lod, "stl": str(stl.relative_to(C22)),
                            "bytes": stl.stat().st_size,
                            "sha256": sha256_file(stl)})
            print(f"[full] {rec['step_index']+1}/{len(records)} {stem} "
                  f"({stl.stat().st_size} B)", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 - fail loudly, keep going
            failures.append(f"{stem}: {type(exc).__name__}: {exc}")

    solids_manifest = []
    for r in records:
        lod = _lod_of(r["body"])
        stl = out / f"{r['name']}__{lod}.stl"
        entry = {k: v for k, v in r.items() if k != "solid"}
        entry["mesh"] = str(stl.relative_to(REPO))
        if stl.is_file():
            entry["mesh_sha256"] = sha256_file(stl)
        solids_manifest.append(entry)

    (out / "bodies.json").write_text(json.dumps({
        "schema": "full_machine_bodies/1",
        "source_step": FULL_STEP_REL,
        "source_step_sha256": step_sha,
        "revision": head,
        "conversion_script_sha256": script_sha,
        "solids": solids_manifest,
        "count_adjustments": adjustments,
        "moving_bodies": sorted(MOVING_BODIES),
        "static_body": STATIC_BODY,
        "emitted": emitted,
        "failures": failures,
        "wall_time_s": time.time() - t0,
    }, indent=2) + "\n")

    print(json.dumps({"emitted_count": len(emitted), "failures": failures,
                      "step_sha256": step_sha,
                      "wall_time_s": time.time() - t0}, indent=2))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", nargs="*", default=["RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE"],
                    choices=sorted(TARGETS))
    ap.add_argument("--lods", nargs="*", default=["fine", "coarse"], choices=sorted(LODS))
    ap.add_argument("--out", default=str(C22 / "sim" / "assets" / "out"))
    ap.add_argument("--fallback-only", action="store_true",
                    help="skip STEP import; emit parametric hook-profile mesh only")
    ap.add_argument("--full", action="store_true",
                    help="convert ALL solids of the machine-integration STEP")
    args = ap.parse_args()
    if args.full:
        return run_full(Path(args.out))

    import cadquery as cq

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    head = git_head()
    script_sha = sha256_file(HERE)
    step_path = REPO / STEP_REL
    step_sha = sha256_file(step_path) if step_path.is_file() else None
    step_match = (step_sha == EXPECTED_STEP_SHA)

    solids = None
    fallback_note = None
    if not args.fallback_only:
        try:
            imported = cq.importers.importStep(str(step_path))
            solids = imported.solids().vals()
            if len(solids) != 41:
                print(f"WARN: expected 41 solids, got {len(solids)}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - headless OCC failure is the fallback trigger
            fallback_note = f"STEP import failed ({type(exc).__name__}: {exc}); parametric fallback"
            print(f"WARN: {fallback_note}", file=sys.stderr)
            solids = None
    else:
        fallback_note = "fallback-only requested; parametric hook-profile mesh"

    failures: list[str] = []
    emitted: list[dict] = []
    for label in args.assets:
        idx = TARGETS[label]
        for lod, tol in ((l, LODS[l]) for l in args.lods):
            stem = f"{label.lower()}__{lod}"
            stl = out / f"{stem}.stl"
            sidecar = out / f"{stem}.sidecar.json"
            shape = None
            provenance = "step"
            if solids is not None and idx < len(solids):
                shape = solids[idx]
            elif label == "RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE":
                from engineering import S2, hook_polygon  # noqa: E402

                c = S2("C2.1-NOMINAL")
                pts = hook_polygon(c)
                wire = cq.Wire.makePolygon(
                    [cq.Vector(float(x), 4.0, float(z)) for x, z in pts], close=True)
                shape = cq.Solid.extrudeLinear(
                    wire, [], cq.Vector(0, 40, 0)).clean()
                provenance = "parametric-fallback:engineering.hook_polygon extruded y=4..44"
            else:
                failures.append(f"{label}/{lod}: no STEP solid and no parametric fallback")
                continue
            try:
                if not shape.isValid():
                    failures.append(f"{label}/{lod}: solid invalid")
                    continue
                volume = shape.Volume()
                cq.exporters.export(
                    shape, str(stl), "STL",
                    tolerance=tol["linear_tolerance_mm"],
                    angularTolerance=tol["angular_tolerance_rad"])
                if not stl.is_file() or stl.stat().st_size == 0:
                    failures.append(f"{label}/{lod}: empty STL")
                    continue
                record = {
                    "asset_id": label,
                    "lod": lod,
                    "mesh_file": str(stl.relative_to(C22)),
                    "mesh_bytes": stl.stat().st_size,
                    "mesh_format": "STL (OBJ unavailable in installed CadQuery exporters)",
                    "provenance": provenance,
                    "source_step": STEP_REL if provenance == "step" else None,
                    "source_step_sha256": step_sha,
                    "source_step_sha_match": step_match,
                    "source_label_index": idx,
                    "revision": head,
                    "conversion_script": str(HERE.relative_to(REPO)),
                    "conversion_script_sha256": script_sha,
                    "tessellation": tol,
                    "note_tessellation": "tessellation-tolerance LOD, not edge-collapse decimation (no trimesh installed)",
                    "coords": "F0 identity (no transform applied)",
                    "units": "mm",
                    "volume_mm3": volume,
                    "mass_kg": None,
                    "inertia": None,
                    "material": None,
                    "mass_material_status": "ASSUMPTION_UNCHOSEN",
                    "evidence_level": "GEOMETRIC_ONLY",
                    "fallback_note": fallback_note,
                }
                write_sidecar(sidecar, record)
                emitted.append({"label": label, "lod": lod,
                                "stl": str(stl.relative_to(C22)),
                                "bytes": stl.stat().st_size,
                                "volume_mm3": volume,
                                "sidecar": str(sidecar.relative_to(C22))})
            except Exception as exc:  # noqa: BLE001 - record and fail loudly
                failures.append(f"{label}/{lod}: {type(exc).__name__}: {exc}")

    print(json.dumps({"emitted": emitted, "failures": failures,
                      "fallback_note": fallback_note,
                      "step_sha_match": step_match}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
