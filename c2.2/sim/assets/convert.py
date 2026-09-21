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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", nargs="*", default=["RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE"],
                    choices=sorted(TARGETS))
    ap.add_argument("--lods", nargs="*", default=["fine", "coarse"], choices=sorted(LODS))
    ap.add_argument("--out", default=str(C22 / "sim" / "assets" / "out"))
    ap.add_argument("--fallback-only", action="store_true",
                    help="skip STEP import; emit parametric hook-profile mesh only")
    args = ap.parse_args()

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
