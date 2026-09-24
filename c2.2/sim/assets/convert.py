"""I1 asset pipeline: STEP -> decimated collision meshes + traceability sidecars.

Reads (never writes): c2.1/cad/PPR_C2_1_S2_transmission.step and the
parametric truth (c2/src/engineering.py, c2.1/src/transmission.py).
Writes (only under c2.2/): STL meshes + per-asset JSON sidecars.

Fallback: if the STEP import fails, emits the parametric S2 hook-rotor
profile mesh (hook_polygon extruded over the 40 mm process width) with an
explicit fallback note. Exits nonzero iff any requested asset is invalid
or missing (empty file, invalid solid, unwritten sidecar).

Mass/material are screening assumptions from materials.py, with imported BRep
volume, actual STEP-solid bbox and explicit source/proxy limits. No measured mass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from materials import MATERIAL_SCOPE, SOURCE as MATERIAL_SOURCE, mass_properties

HERE = Path(__file__).resolve()
C22 = HERE.parents[2]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "c2" / "src"))

EXPECTED_STEP_SHA = "06398eaa1e277f393289b1e005c7745070e169a98708c06ffaec1436b59407c0"
STEP_REL = "c2.1/cad/PPR_C2_1_S2_transmission.step"

# Zero-based solid index in export order (c2.1/src/build_cad.py
# fixed_components 31 + moving; label order pinned by cad_validation.json).
TARGETS = {
    "RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE": 33,
    "C2_FIXED_SHEAR_SENSOR_BORE": 6,
    "C2_VERTICAL_DISCHARGE_SCREEN": 7,
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


FULL_STEP_REL = "c2.1/cad/PPR_VP1.step"

# Kinematic body assignment for the integrated machine (C2.1-S2 task spec):
# S1 cutter shafts A/B + cutter stacks, S2 input eccentric, rotor, output
# carrier/rollers are MOVING; everything else STATIC. The M1 input shaft
# assembly (shaft, coupling, 15T pinion halves, 24T chain-B sprocket, keys)
# is the single actuated input body. DRV-SP24-B25 (chain-A sprocket keyed to
# the S1 main shaft) is kept STATIC per the task's explicit classification;
# its 25 H7 bore on the 25 shaft is a by-design journal-fit contact pair.
MOVING_BODIES: dict[str, set[str]] = {
    # PPR_VP1.step: the doubled lower helical mesh pair (DRV-SH15R_001 +
    # DRV_SH40L_lower) and the input-shaft chain-B sprocket DRV-SP24-B12_001
    # are DELETED — chain B is now driven from the jackshaft
    # (DRV-SP24-B20_002, STATIC jack-side sprocket like the 40T gears)
    "IN_SHAFT": {"DRV-IN-SHAFT_001", "DRV-CPL12_001", "DRV-SH15L_001",
                 "KEY-4-70_001"},
    "S1A": {"S1-SHAFT-A_001", "KEY-8-154_001", "KEY-8-25_001", "S1-SYNC_001",
            "DRV-SP24-B25_001", "KEY-8-16_001"}
         | {f"S1-CUT-A-P{i:02d}_001" for i in range(13)}
         | {f"S1-SPACER-A_{i:03d}" for i in range(1, 13)},
    "S1B": {"S1-SHAFT-B_001", "KEY-8-154_002", "KEY-8-25_002", "S1-SYNC_002"}
         | {f"S1-CUT-B-P{i:02d}_001" for i in range(13)}
         | {f"S1-SPACER-B_{i:03d}" for i in range(1, 13)},
    "S2_ECC": {"INPUT_ECCENTRIC_SHAFT", "ECCENTRIC_BEARING_ENVELOPE_UNRATED",
               "DRV-SP12-B12_001"},
    # Worm shaft and perpendicular feed use one measured S2Ecc angle
    # through their keyed gear stages. Only supports/shells remain static.
    "PADDLE": {"PDL_SHAFT", "PDL_SPROCKET", "PDL_WORM",
               "PDL_FEED_GEAR"},
    "AUGER": {"AUG_SHAFT", "AUG_WHEEL"},
    "CROSS_FEED": {"CROSS_FEED_SHAFT", "CROSS_FEED_GEAR"},
    "CROSS_FEED_IDLER": {"CROSS_FEED_IDLER"},
    "S2_ROTOR": {"RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE"},
    "BELT": {"S1_BELT"},
    "BELT_DRIVE": {"S1_BELT_DRIVE", "S1_BELT_FOLLOWER"},
    "BELT_IDLER": {"S1_BELT_IDLER", "S1_SWEEP_GEAR_DRUM_S",
                   "S1_SWEEP_GEAR_DRUM_N"},
    "SWEEP_SOUTH": {"S1_SWEEP_SOUTH", "S1_SWEEP_GEAR_S"},
    "SWEEP_NORTH": {"S1_SWEEP_NORTH", "S1_SWEEP_GEAR_N"},
    "TRANSFER_BELT": {"S1_TRANSFER_BELT"},
    "TRANSFER_IDLER": {"S1_TRANSFER_IDLER"},
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



def _reconstruct_parts(cq):
    """Rebuild the exact integration part order from its source functions.

    The STEP exporter has no stable per-solid labels. Reuse the CAD builder's
    placement, deletion, second jackshaft key and S2 transform, then match
    each exported solid to this list by BRep geometry.
    """
    sys.path.insert(0, str(REPO / "c2.1" / "src"))
    import build_machine_integration as bmi

    config = json.loads((REPO/"c2.1/design/machine_integration.json").read_text())
    master = json.loads((REPO/config["legacy_master"]).read_text())
    legacy = bmi.legacy_parts(master, config)
    c21 = bmi.c21_parts(config)
    chain_parts = [{"name": name, "group": "drive", "shape": solid}
                   for name, solid in bmi.drive_teeth.chain_components()]
    chute_parts = [{"name": name, "group": group, "shape": solid}
                   for name, solid, group in bmi.chute_mod.components()]
    guard_parts = [{"name": name, "group": "guard", "shape": solid}
                   for name, solid in bmi.guards_mod.components()]
    winder_parts = [{"name": name, "group": group, "shape": solid}
                    for name, solid, group in bmi.winder_mod.components()]
    electrical_parts = [{"name": name, "group": "electrical", "shape": solid}
                        for name, solid in bmi.electrical_mod.components()]
    hopper_parts = [{"name": name, "group": "feed", "shape": solid}
                    for name, solid in bmi.hopper_panels.components()]
    new_solids = {r["name"]: r["shape"] for r in legacy if r.get("replaced")}
    new_solids.update({r["name"]: r["shape"] for r in
                       chain_parts + chute_parts + guard_parts +
                       winder_parts + electrical_parts + hopper_parts})
    bmi.chain_relief.apply(legacy, new_solids)
    parts = (legacy + c21 + chain_parts + chute_parts + guard_parts +
             winder_parts + electrical_parts + hopper_parts)
    # Compounds (multi-solid parts, e.g. the paddle bearing posts split by
    # their bores, the paddle wheel blades, bearing pairs) must expand to
    # one record per solid: the hungarian below matches records against
    # STEP solids 1:1 and reused-record matches emit WRONG meshes (the
    # rev-4 paddles produced 578/432/412 mm centre_dist pairings).
    expanded = []
    for p in parts:
        sh = p["shape"]
        try:
            sols = sh.Solids()
        except Exception:
            sols = None
        if sols is not None and len(sols) > 1:
            for s in sols:
                expanded.append({"name": p["name"],
                                 "group": p["group"], "shape": s})
        else:
            expanded.append(p)
    return [(p["name"], p["group"], p["shape"]) for p in expanded]




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

    # FIX: proper 1:1 part<->solid assignment (Main-approved).  The old
    # ordered bbox-containment pass mis-assigned when a part bbox contains
    # another part's solid (keys inside hubs, chain-wrap bulges larger than
    # the bare sprocket).  Hungarian assignment (scipy linear_sum_assignment)
    # on cost = bbox centre distance + 8*|ln(volume ratio)|; identical-size
    # twins resolve by minimum centre distance, ties broken by volume
    # overlap IoU (recorded policy; assignment is globally optimal and
    # deterministic for a given cost matrix).  Smallest-bbox-first remains
    # only as the row/column enumeration order (deterministic tie-break).
    import math as _math
    import numpy as _np
    from scipy.optimize import linear_sum_assignment as _lsa

    def _centre(bb):
        return _np.array([(bb[0] + bb[3]) / 2.0, (bb[1] + bb[4]) / 2.0,
                          (bb[2] + bb[5]) / 2.0])

    def _vol(bb):
        return max((bb[3] - bb[0]) * (bb[4] - bb[1]) * (bb[5] - bb[2]),
                   1e-9)

    def _iou(a, b):
        ox = max(0.0, min(a[3], b[3]) - max(a[0], b[0]))
        oy = max(0.0, min(a[4], b[4]) - max(a[1], b[1]))
        oz = max(0.0, min(a[5], b[5]) - max(a[2], b[2]))
        inter = ox * oy * oz
        return inter / max(_vol(a) + _vol(b) - inter, 1e-9)

    rows = []
    for pi, count in enumerate(expected_counts):
        for copy_i in range(count):
            rows.append((pi, copy_i))
    cols = list(range(len(solids)))
    pool_bbs = {i: _sbb(solids[i]) for i in cols}
    order = sorted(range(len(parts)),
                   key=lambda pi: (lambda b: (b[3] - b[0]) * (b[4] - b[1])
                                   * (b[5] - b[2]))(_bbox(parts[pi][2])))
    part_bbs = {pi: _bbox(parts[pi][2]) for pi in range(len(parts))}
    cost = _np.zeros((len(rows), len(cols)))
    for ri, (pi, _c) in enumerate(rows):
        pc = _centre(part_bbs[pi])
        pv = _vol(part_bbs[pi])
        for ci, si in enumerate(cols):
            sb = pool_bbs[si]
            dist = float(_np.linalg.norm(pc - _centre(sb)))
            vr = abs(_math.log(pv / _vol(sb)))
            cost[ri, ci] = dist + 8.0 * vr
    ri_idx, ci_idx = _lsa(cost)
    # Two-stage refinement: assignments whose centre distance exceeds
    # CONFIDENT_MM come from stale cfg placements (parts that MOVED in
    # PPR_VP1, e.g. keys/guards shifted with chain B) — their placement
    # prior is worthless, so re-assign just those rows/cols on bbox SIZE
    # distance only (solid identity is what matters; meshes are emitted
    # from the STEP solid at its true position).  Identical-size twins
    # (volume-overlap fallback per policy) resolve deterministically via
    # the solver's stable ordering.
    CONFIDENT_MM = 15.0

    def _size_vec(bb):
        return _np.array([bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]])

    keep, sus_r, sus_c = [], [], []
    for ri, ci in zip(ri_idx, ci_idx):
        d = _np.linalg.norm(_centre(part_bbs[rows[ri][0]])
                            - _centre(pool_bbs[cols[ci]]))
        if d <= CONFIDENT_MM:
            keep.append((ri, ci))
        else:
            sus_r.append(ri)
            sus_c.append(ci)
    if sus_r and sus_c:
        cost2 = _np.zeros((len(sus_r), len(sus_c)))
        for a, ri in enumerate(sus_r):
            sa = _size_vec(part_bbs[rows[ri][0]])
            for b, ci in enumerate(sus_c):
                cost2[a, b] = float(_np.linalg.norm(
                    sa - _size_vec(pool_bbs[cols[ci]])))
        r2, c2 = _lsa(cost2)
        keep += [(sus_r[a], sus_c[b]) for a, b in zip(r2, c2)]
    pairs = sorted((rows[ri], cols[ci],
                    float(cost[ri, ci])) for ri, ci in keep)
    records = []
    assign_audit = []
    for (pi, _c), si, cval in pairs:
        name, group, shape = parts[pi]
        body = next((b for b, names in MOVING_BODIES.items()
                     if name in names), STATIC_BODY)
        records.append({"name": name, "group": group, "body": body,
                        "step_index": si, "solid": solids[si],
                        "part_bbox": part_bbs[pi],
                        "solid_bbox": pool_bbs[si], "bbox_ok": True})
        assign_audit.append({"part": name, "step_index": si,
                             "centre_dist_mm": round(cval, 2) if cval < 1e8
                             else None})
    worst = max((a for a in assign_audit if a["centre_dist_mm"] is not None),
                key=lambda a: a["centre_dist_mm"], default=None)
    print(f"[full] hungarian assignment: {len(records)} pairs, worst "
          f"centre_dist {worst['centre_dist_mm'] if worst else '-'} mm "
          f"({worst['part'] if worst else '-'})",
          file=sys.stderr, flush=True)
    failures = [f for f in failures if "matched" not in f
                and "unassigned" not in f]

    records.sort(key=lambda r: r["step_index"])
    # Compound parts contain distinct STEP solids under one part name.
    # Never let the second solid overwrite the first one's STL/sidecar:
    # that silently removed the south S1 belt and duplicated bearing posts.
    from collections import Counter
    multiplicity = Counter(rec["name"] for rec in records)
    for rec in records:
        rec["mesh_stem"] = (rec["name"] if multiplicity[rec["name"]] == 1
                            else f"{rec['name']}_step{rec['step_index']:03d}")


    emitted = []
    for rec in records:
        lod = _lod_of(rec["body"])
        tol = LODS[lod]
        stem = f"{rec['mesh_stem']}__{lod}"
        stl = out / f"{stem}.stl"
        sidecar = out / f"{stem}.sidecar.json"
        try:
            if not rec["solid"].isValid():
                failures.append(f"{stem}: solid invalid")
                continue
            volume = rec["solid"].Volume()
            props = mass_properties(rec["name"], volume, rec["solid_bbox"])
            rec["mass_props"] = props
            cq.exporters.export(rec["solid"], str(stl), "STL",
                                tolerance=tol["linear_tolerance_mm"],
                                angularTolerance=tol["angular_tolerance_rad"])
            if not stl.is_file() or stl.stat().st_size == 0:
                failures.append(f"{stem}: empty STL")
                continue
            mesh_sha = sha256_file(stl)
            rec["mesh_sha256"] = mesh_sha
            write_sidecar(sidecar, {
                "asset_id": rec["name"], "group": rec["group"],
                "kinematic_body": rec["body"], "lod": lod,
                "step_index": rec["step_index"],
                "step_product_name": ("Open CASCADE STEP translator 7.9 1.%d"
                                      % rec["step_index"]),
                "mesh_file": str(stl.relative_to(C22)),
                "mesh_bytes": stl.stat().st_size,
                "mesh_sha256": mesh_sha,
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
                **props,
                "inertia": {"diagonal_kg_mm2": props["inertia_kg_mm2"],
                            "upper_bound_kg_mm2": props["inertia_upper_bound_kg_mm2"],
                            "center_of_mass_mm": props["center_of_mass_mm"],
                            "basis": props["inertia_basis"]},
                "evidence_level": "MASS_AND_INERTIA_SCREENING_ASSUMPTION",
            })
            emitted.append({"name": rec["name"], "body": rec["body"],
                            "lod": lod, "stl": str(stl.relative_to(C22)),
                            "bytes": stl.stat().st_size,
                            "sha256": mesh_sha})
            print(f"[full] {rec['step_index']+1}/{len(records)} {stem} "
                  f"({stl.stat().st_size} B)", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 - fail loudly, keep going
            failures.append(f"{stem}: {type(exc).__name__}: {exc}")

    solids_manifest = []
    for r in records:
        lod = _lod_of(r["body"])
        stl = out / f"{r['mesh_stem']}__{lod}.stl"
        entry = {k: v for k, v in r.items()
                 if k not in ("solid", "mesh_stem", "mass_props")}
        if "mass_props" in r:
            entry.update(r["mass_props"])
        else:
            failures.append(f"{r['name']}: no emitted mass properties")
        entry["mesh"] = str(stl.relative_to(REPO))
        solids_manifest.append(entry)
    mesh_paths = [entry["mesh"] for entry in solids_manifest]
    if len(mesh_paths) != len(set(mesh_paths)):
        failures.append("distinct STEP solids share an STL path")

    (out / "bodies.json").write_text(json.dumps({
        "schema": "full_machine_bodies/1",
        "source_step": FULL_STEP_REL,
        "source_step_sha256": step_sha,
        "source_step_solid_count": len(solids),
        "reconstructed_solid_count": n_expected,
        "revision": head,
        "conversion_script_sha256": script_sha,
        "solids": solids_manifest,
        "material_model": MATERIAL_SOURCE,
        "material_model_sha256": sha256_file(HERE.with_name("materials.py")),
        "material_scope": MATERIAL_SCOPE,
        "count_adjustments": adjustments,
        "moving_bodies": sorted(MOVING_BODIES),
        "static_body": STATIC_BODY,
        "emitted": emitted,
        "failures": failures,
        "assignment_audit": assign_audit,
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
    ap.add_argument("--out", default=None)
    ap.add_argument("--fallback-only", action="store_true",
                    help="skip STEP import; emit parametric hook-profile mesh only")
    ap.add_argument("--full", action="store_true",
                    help="convert ALL solids of the machine-integration STEP")
    args = ap.parse_args()
    if args.full:
        return run_full(Path(args.out) if args.out else
                        C22 / "sim" / "assets" / "out" / "full")

    import cadquery as cq

    out = Path(args.out) if args.out else C22 / "sim" / "assets" / "out"
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
                props = mass_properties(label, volume, _bbox(shape))
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
                    **props,
                    "inertia": {"diagonal_kg_mm2": props["inertia_kg_mm2"],
                                "upper_bound_kg_mm2": props["inertia_upper_bound_kg_mm2"],
                                "center_of_mass_mm": props["center_of_mass_mm"],
                                "basis": props["inertia_basis"]},
                    "evidence_level": "MASS_AND_INERTIA_SCREENING_ASSUMPTION",
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
