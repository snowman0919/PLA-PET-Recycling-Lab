"""Gate A: machine USD emission from staged STL + parametric DERIVED transfer assets.

Reads (never writes outside c2.2/): cad/parts/*.stl, c2.2/sim/assets/out/*.stl,
design/parameters.json (C2.1 CAD read paths only).

Writes (c2.2/ only): c2.2/sim/assets/usd/machine.usda + machine.sidecar.json.

Frame/units: F0 identity, mm authored -> stage metersPerUnit=0.001. Collision:
convex-hull approximation for cutters/rotor (RigidBody convexHull), hopper +
transfer assets as static concave triangle-mesh collision. No mass/inertia
claims: density ASSUMPTION recorded, evidence GEOMETRIC_ONLY.

Runs under $HOME/env_isaacsim-c22 (pxr + numpy-stl + scipy + trimesh present).
NO SimulationApp needed for emission.

Usage:
  $HOME/env_isaacsim-c22/bin/python c2.2/sim/assets/emit_usd.py --out c2.2/sim/assets/usd
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[2]
REPO = HERE.parents[3]

HULL_MAX_VERTS = 256  # PhysX convex-mesh vertex limit

# --- DERIVED transfer assets (Gate C geometry, staged here for USD emission).
# S1 discharge + chute + S2 entry/exit are MISSING from C2.1 CAD (PARAM_TRACE
# items 5/6/12). Dims below are DERIVED parametric boxes with assumptions
# recorded in the sidecar; C2.1 sources are never mutated.
DERIVED = {
    "S1_DISCHARGE": {"dx": 120.0, "dy": 100.0, "dz": 30.0,
                     "center": [120.0, 243.5, 428.0],
                     "note": "outlet under S1 chamber datum Y162.4..324.6"},
    "CHUTE": {"dx": 110.0, "dy": 90.0, "dz": 120.0,
              "center": [200.0, 243.5, 350.0],
              "note": "45deg-class gravity slide S1 outlet -> S2 entry"},
    "S2_ENTRY": {"dx": 90.0, "dy": 45.0, "dz": 25.0,
                 "center": [308.6, 275.0, 330.0],
                 "note": "throat above S2 bay"},
    "S2_EXIT": {"dx": 90.0, "dy": 45.0, "dz": 40.0,
                "center": [308.6, 275.0, 200.0],
                "note": "duct below screen arc"},
}

SOURCES = [
    ("cad/parts/HOPPER.stl", "/World/F0/Hopper", "static",
     "hopper shell collision (concave mesh)"),
    ("cad/parts/S1-SHAFT-A.stl", "/World/F0/S1/ShaftA", "kinematic-shaft",
     "S1-A shaft A axis"),
    ("cad/parts/S1-CUT-A-P00.stl", "/World/F0/S1/CutterA00",
     "kinematic-cutter", "hook cutter convex-hull collision"),
    ("cad/parts/S2-ROTOR.stl", "/World/F0/S2/Rotor", "kinematic-rotor",
     "S2-A hook rotor convex-hull collision"),
    ("cad/parts/S1-SHAFT-B.stl", None, "kinematic-shaft",
     "S1-A shaft B axis (mesh staged if present)"),
    ("cad/parts/S1-CUT-B-P00.stl", None, "kinematic-cutter",
     "hook cutter convex-hull collision (mesh staged if present)"),
    ("c2.2/sim/assets/out/rigid_cycloid_hook_rotor_envelope__fine.stl",
     None, "reference",
     "I1 S2 envelope reference mesh (visual only, no collision)"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def load_stl_verts_faces(path: Path):
    from stl import mesh as stlm
    import numpy as np
    m = stlm.Mesh.from_file(str(path))
    tris = np.asarray(m.vectors, dtype=np.float64).reshape(-1, 3, 3)
    verts, idx = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
    return verts, idx.reshape(-1, 3)


def convex_hull_of_verts(verts):
    import numpy as np
    from scipy.spatial import ConvexHull
    v = np.asarray(verts, dtype=np.float64)
    hull = ConvexHull(v)
    used = np.unique(hull.simplices)
    remap = np.full(len(v), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))
    return v[used], remap[np.asarray(hull.simplices)]


def box_mesh(center, dims):
    import numpy as np
    cx, cy, cz = center
    dx, dy, dz = (d / 2.0 for d in dims)
    v = np.array([
        [cx - dx, cy - dy, cz - dz], [cx + dx, cy - dy, cz - dz],
        [cx + dx, cy + dy, cz - dz], [cx - dx, cy + dy, cz - dz],
        [cx - dx, cy - dy, cz + dz], [cx + dx, cy - dy, cz + dz],
        [cx + dx, cy + dy, cz + dz], [cx - dx, cy + dy, cz + dz],
    ], dtype=np.float64)
    f = np.array([[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
                  [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
                  [0, 3, 7], [0, 7, 4], [1, 5, 6], [1, 6, 2]])
    return v, f


def mesh_prim(stage, UsdGeom, path: str, verts, faces, collision: str,
              role: str, doc: str):
    import numpy as np
    verts = np.asarray(verts, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    prim = stage.DefinePrim(path, "Mesh")
    mesh = UsdGeom.Mesh(prim)
    mesh.GetPointsAttr().Set([tuple(map(float, v)) for v in verts])
    mesh.GetFaceVertexCountsAttr().Set([3] * len(faces))
    mesh.GetFaceVertexIndicesAttr().Set([int(i) for i in faces.reshape(-1)])
    mesh.GetExtentAttr().Set(
        [tuple(map(float, verts.min(axis=0))),
         tuple(map(float, verts.max(axis=0)))])
    prim.SetCustomDataByKey("ppr:role", role)
    prim.SetCustomDataByKey("ppr:collision_approximation", collision)
    prim.SetCustomDataByKey("ppr:doc", doc)
    prim.SetCustomDataByKey("ppr:units", "mm (stage metersPerUnit=0.001)")
    return prim


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="c2.2/sim/assets/usd")
    args = ap.parse_args()

    from pxr import Usd, UsdGeom

    out = Path(args.out)
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    usd_path = out / "machine.usda"

    stage = Usd.Stage.CreateNew(str(usd_path))
    UsdGeom.SetStageMetersPerUnit(stage, 0.001)
    stage.DefinePrim("/World", "Xform")
    f0 = stage.DefinePrim("/World/F0", "Xform")
    f0.SetCustomDataByKey(
        "ppr:frame",
        "F0 identity (+Y axial/material-width, +X shear-blade, +Z up)")

    head = git_head()
    script_sha = sha256_file(HERE)
    assets: list[dict] = []
    failures: list[str] = []

    for rel, prim_path, role, doc in SOURCES:
        src = REPO / rel
        if prim_path is None or not src.is_file():
            assets.append({"source": rel, "prim": prim_path, "role": role,
                           "status": "STAGED_NOT_EMITTED" if src.is_file()
                           else "MISSING_SOURCE",
                           "sha256": sha256_file(src) if src.is_file()
                           else None})
            continue
        try:
            verts, faces = load_stl_verts_faces(src)
            if "cutter" in role or "rotor" in role:
                hv, hf = convex_hull_of_verts(verts)
                if len(hv) > HULL_MAX_VERTS:
                    failures.append(
                        f"{rel}: hull {len(hv)} verts exceeds cap "
                        f"{HULL_MAX_VERTS} (convex decomposition HOLD)")
                    continue
                mesh_prim(stage, UsdGeom, prim_path, hv, hf,
                          collision="convexHull", role=role, doc=doc)
                approx = f"convexHull({len(hv)}v/{len(hf)}f)"
                assets.append({"source": rel, "prim": prim_path,
                               "role": role, "status": "EMITTED",
                               "sha256": sha256_file(src),
                               "src_verts": int(len(verts)),
                               "src_faces": int(len(faces)),
                               "collision": approx})
            else:
                mesh_prim(stage, UsdGeom, prim_path, verts, faces,
                          collision="concaveMesh", role=role, doc=doc)
                approx = f"concaveMesh({len(verts)}v/{len(faces)}f)"
                assets.append({"source": rel, "prim": prim_path,
                               "role": role, "status": "EMITTED",
                               "sha256": sha256_file(src),
                               "collision": approx})
        except Exception as exc:
            failures.append(f"{rel}: {type(exc).__name__}: {exc}")

    for name, spec in DERIVED.items():
        try:
            v, f = box_mesh(spec["center"],
                            (spec["dx"], spec["dy"], spec["dz"]))
            prim_path = f"/World/F0/Transfer/{name}"
            mesh_prim(stage, UsdGeom, prim_path, v, f,
                      collision="concaveMesh", role="static-derived",
                      doc=f"DERIVED {name}: {spec['note']}; NOT C2.1 CAD")
            assets.append({"source": f"DERIVED:{name}", "prim": prim_path,
                           "role": "static-derived", "status": "EMITTED",
                           "dims_mm": [spec["dx"], spec["dy"], spec["dz"]],
                           "center_mm": list(spec["center"]),
                           "note": spec["note"]})
        except Exception as exc:
            failures.append(f"DERIVED {name}: {type(exc).__name__}: {exc}")

    stage.GetRootLayer().Save()

    manifest = {
        "schema": "dyn_usd_manifest/1",
        "usd_file": str(usd_path),
        "usd_bytes": usd_path.stat().st_size,
        "stage_meters_per_unit": 0.001,
        "frame": "F0 identity",
        "units": "mm authored",
        "revision": head,
        "emission_script_sha256": script_sha,
        "hull_vertex_cap": HULL_MAX_VERTS,
        "mass_material_status": "ASSUMPTION_UNCHOSEN",
        "material_density_assumption_g_cc": {"PLA": 1.24, "PET": 1.38,
                                             "TPU": 1.21},
        "evidence_level": "GEOMETRIC_ONLY",
        "derived_transfer_spec": DERIVED,
        "derived_note": ("S1 discharge/chute/S2 entry/exit are DERIVED "
                         "parametric boxes; C2.1 CAD unmutated (PARAM_TRACE "
                         "items 5/6/12 MISSING inputs)."),
        "assets": assets,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    (out / "machine.sidecar.json").write_text(json.dumps(manifest, indent=2)
                                              + "\n")
    print(json.dumps(manifest, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
