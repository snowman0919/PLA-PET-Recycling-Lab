"""FIX B(1): convex-hull fidelity audit for the integrated machine.

For every solid in c2.2/sim/assets/out/full/bodies.json, compare the exact
closed-mesh volume of its fine STL (moving solids) / coarse STL (static
solids) against the volume of its convex hull.  A hull over a non-convex
solid occludes pockets/apertures (hook-cutter pockets, cycloid rotor
windows); the occlusion ratio hull_vol/mesh_vol quantifies it.

Output: c2.2/results/full_machine/hull_audit.json with a per-solid table,
per-body aggregation, explicit collision approximations, and sampled vertical
Ø3 passage through the emitted static screen triangle mesh. The BRep passage
gate in c2.1/src/path_check.py remains the exact geometry check.

Pure numpy/scipy — runs without Isaac Sim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SIM = HERE.parent
C22 = SIM.parent
REPO = C22.parent
sys.path.insert(0, str(SIM))

BODIES = C22 / "sim" / "assets" / "out" / "full" / "bodies.json"
OUT = C22 / "results" / "full_machine" / "hull_audit.json"

# Hook pockets on the S1 cutter discs remain tight per-solid decimated
# hulls: decomposition wedges protruded into the joint and jammed S1.
# Inter-disc channels remain between separate solids, but the intradisc
# hook-pocket approximation is not a proof of functional cutting contact.
# The cycloid rotor/output carrier windows use convex decomposition.
DECOMPOSE = ("RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE",
             "OUTPUT_PIN_CARRIER_AND_SHAFT")


def sha256_file(path: Path) -> str:
    h = __import__("hashlib").sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mesh_volume(verts, faces) -> float:
    """Signed volume of a closed triangle mesh via the divergence theorem
    (mm^3).  CAD-exported STLs are outward-wound; sign is normalised."""
    import numpy as np
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    return float(abs(np.einsum("ij,ij->i", v0,
                               np.cross(v1, v2)).sum() / 6.0))

def screen_vertical_mesh_paths(verts, faces):
    """Sample a centre and 16 rim rays of each Ø3 screen exit in mesh XY."""
    import math
    import numpy as np

    triangles = np.asarray(verts, dtype=np.float64)[faces, :2]
    lower = triangles.min(axis=1)
    upper = triangles.max(axis=1)
    blocked = []
    for angle in range(228, 313, 7):
        x = 308.56946468906176 - 63.8 * math.cos(math.radians(angle))
        for local_y in (9, 15, 21, 27, 33, 39):
            y = 299.0 - local_y
            rays_hit = 0
            for sample in range(17):
                phase = 2 * math.pi * (sample - 1) / 16 if sample else 0
                px = x + (1.5 * math.cos(phase) if sample else 0.0)
                py = y + (1.5 * math.sin(phase) if sample else 0.0)
                indices = np.where((lower[:, 0] <= px) &
                                   (upper[:, 0] >= px) &
                                   (lower[:, 1] <= py) &
                                   (upper[:, 1] >= py))[0]
                v = triangles[indices]
                ax, ay = v[:, 0, 0], v[:, 0, 1]
                bx, by = v[:, 1, 0] - ax, v[:, 1, 1] - ay
                cx, cy = v[:, 2, 0] - ax, v[:, 2, 1] - ay
                den = bx * cy - by * cx
                nondegenerate = np.abs(den) > 1e-10
                safe = np.where(nondegenerate, den, 1.0)
                u = ((px - ax) * cy - (py - ay) * cx) / safe
                w = (bx * (py - ay) - by * (px - ax)) / safe
                rays_hit += int(np.any(nondegenerate &
                                       (u >= -1e-8) & (w >= -1e-8) &
                                       (u + w <= 1 + 1e-8)))
            if rays_hit:
                blocked.append({"angle_deg": angle, "local_y_mm": local_y,
                                "rays_hit": rays_hit})
    return {"method": "17_SAMPLED_VERTICAL_RAYS_PER_3MM_HOLE_ON_STATIC_TRIANGLE_MESH",
            "holes": 78, "sampled_rays": 1326,
            "blocked_holes": blocked, "passed": not blocked,
            "limitation": "sampled mesh rays do not prove dynamic passage or PhysX cooking"}


def main() -> int:
    import numpy as np
    from scipy.spatial import ConvexHull

    from full_machine import load_stl_verts_faces, convex_hull_of_verts

    bodies = json.loads(BODIES.read_text())
    solids = bodies["solids"]
    rows = []
    screen_paths = None
    for rec in solids:
        lod = "fine" if rec["body"] != "STATIC" else "coarse"
        stl = REPO / rec["mesh"]
        verts, faces = load_stl_verts_faces(stl)
        if rec["name"] == "C2_VERTICAL_DISCHARGE_SCREEN":
            screen_paths = screen_vertical_mesh_paths(verts, faces)
        mv = mesh_volume(verts, faces)
        try:
            hull = ConvexHull(np.asarray(verts, dtype=np.float64))
            hv = abs(float(hull.volume))
            hull_verts = len(np.unique(hull.simplices))
        except Exception as exc:
            hv = -1.0
            hull_verts = -1
        occ = hv / mv if (mv > 0 and hv > 0) else None
        flag = bool(occ is not None and occ > 1.05)
        if rec["body"] == "STATIC":
            # static solids never use hull collision (concave
            # triangleMesh in the emitter) — the ratio is informational
            decision = "triangleMesh_concave"
        else:
            decompose = any(rec["name"].startswith(p) for p in DECOMPOSE)
            decision = "convexDecomposition" if decompose else "keep_hull"
        rows.append({
            "name": rec["name"],
            "body": rec["body"],
            "lod": lod,
            "mesh_volume_mm3": round(mv, 1),
            "hull_volume_mm3": round(hv, 1) if hv >= 0 else None,
            "occlusion_ratio": round(occ, 5) if occ is not None else None,
            "occlusion_flag": flag,
            "hull_vertices": hull_verts,
            "decision": decision,
        })

    flagged = [r for r in rows if r["occlusion_flag"]]
    moving = [r for r in rows if r["body"] != "STATIC"]
    dec = [r for r in rows if r["decision"] == "convexDecomposition"]
    by_body = {}
    for r in rows:
        b = by_body.setdefault(r["body"], {"solids": 0,
                                           "max_occlusion": 0.0,
                                           "flagged": 0})
        b["solids"] += 1
        if r["occlusion_ratio"]:
            b["max_occlusion"] = max(b["max_occlusion"],
                                     r["occlusion_ratio"])
        b["flagged"] += int(r["occlusion_flag"])

    result = {
        "schema": "full_machine_hull_audit/1",
        "bodies_json": str(BODIES),
        "step_sha256": bodies["source_step_sha256"],
        "revision": bodies.get("revision"),
        "method": ("closed-mesh volume (divergence theorem) of the "
                   "converted STL vs scipy ConvexHull volume; occlusion "
                   "ratio = hull/mesh; ratio 1.0 = convex solid, >1.05 "
                   "flagged as an occluded pocket/aperture"),
        "summary": {
            "solids": len(rows),
            "moving_solids": len(moving),
            "flagged": len(flagged),
            "flagged_names": [r["name"] for r in flagged],
            "convex_decomposition_applied": [r["name"] for r in dec],
            "max_occlusion_ratio": max(r["occlusion_ratio"]
                                       for r in rows
                                       if r["occlusion_ratio"]),
            "by_body": by_body,
        },
        # S1 cutter stacks are emitted PER SOLID (disc/hook/spacer each
        # separately hulled) so inter-disc channels are not spanned by
        # a single hull. Intradisc hook-pocket contact is approximate;
        # only the S2 rotor/output carrier use decomposition.
        "aperture_assessment": {
            "S1_cutter_stacks": {
                "collision": "per-solid (each cutter disc, spacer, shaft "
                             "segment its own collider)",
                "inter_solid_channels": "OPEN by construction — no hull "
                                        "spans multiple solids; disc pitch "
                                        "6.4 mm with spacer-filled hubs, "
                                        "A/B interleave gap is between "
                                        "bodies (articulation self-collision "
                                        "off)",
                "in_solid_occlusion": "hook pockets on cutter rims are "
                                      "approximated by tight per-solid hulls; "
                                      "cutting contact is not proven",
            },
            "S2_rotor": {
                "collision": "single solid RIGID_CYCLOID_HOOK_ROTOR_"
                             "ENVELOPE — convex hull would fill the lobe "
                             "windows and weld the rotor to an effective "
                             "full cylinder",
                "fix": "convexDecomposition approximation (PhysX cooked "
                       "V-HACD) authored in full_machine.py",
            },
            "S2_screen": screen_paths,
        },
        "flagged_above_threshold": [
            {k: r[k] for k in ("name", "body", "occlusion_ratio",
                               "decision")} for r in flagged],
        "per_solid": rows,
        "step_sha_source": "bodies.json:source_step_sha256",
        "runner": "c2.2/sim/audit_hulls.py",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k != "per_solid"}, indent=2))
    return 0 if screen_paths is not None and screen_paths["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())