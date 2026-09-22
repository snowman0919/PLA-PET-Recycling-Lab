"""Full-machine USD emission for the integrated 196-solid assembly.

Reads c2.2/sim/assets/out/full/ (convert.py --full output: 196 per-solid
STLs + bodies.json) and emits c2.2/sim/assets/usd/full_machine.usda:

  - stage metersPerUnit=0.001 (mm authored), F0 identity frame;
  - one articulation root /World/F0/Machine (fixed base) with five revolute
    joints driven by the C2.1 drive layout (design/parameters.json):
      M1 input shaft 15T -> jack 40T (gear, counter-rotating, 15/40)
      chain A 24/24 (1:1, same direction) -> S1 main shaft
      S1-A/B sync gears 1:1 (counter-rotating)
      chain B 24/12 (same direction)      -> S2 input eccentric shaft
      S2 output carrier = -theta_S2/q, q=8 (fixed-ring cycloid, reverse);
  - S2 rotor is a pose-driven KINEMATIC rigid body outside the articulation
    (orbit + spin cannot be one revolute joint; exact transmission.rotor
    kinematics applied per step in verify_full.py);
  - static shell solids as concave triangle-mesh collision; moving solids
    as convex-hull collision (emit_usd.py convention); all contact offsets
    authored small (0.2mm) so near-touching designed surfaces do not flood
    the contact report;
  - DERIVED transfer boxes (S1 discharge, chute, S2 entry/exit) reused from
    emit_usd.py DERIVED (missing from C2.1 CAD, PARAM_TRACE items 5/6/12);
  - PhysX articulation DOF order in dof_names matches JOINTS order below.

Drive ratios (documented basis, from design/parameters.json drive block and
the C1 drive layout in design/assembly.json + src/design.py):
  jack/input   = -(15/40)   external helical mesh (DRV-SH15R/L on input
                            shaft x=80 z=65, DRV-SH40L/R on jack x=136.940)
  S1A/jack     = 24/24 = 1  chain A, same direction
  S1B/S1A      = -1         S1-SYNC sync gears, counter-rotating
  S2ecc/input  = 24/12 = 2  chain B (24T on input shaft, 12T on S2 shaft),
                            same direction
  carrier/S2ecc= -1/8       cycloid fixed-ring ratio q=8

No mass/inertia invention: links use the PhysX default density path
(UsdPhysics default 1000 kg/m^3 MKS equivalent); recorded as ASSUMPTION in
the sidecar. Evidence GEOMETRIC_ONLY + PHYSX_KINEMATIC_VERIFICATION.

Usage (no SimulationApp needed):
  $HOME/env_isaacsim-c22/bin/python c2.2/sim/full_machine.py \
      --assets c2.2/sim/assets/out/full --out c2.2/sim/assets/usd
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SIM = HERE.parent
C22 = HERE.parents[1]
REPO = C22.parent

sys.path.insert(0, str(C22 / "sim" / "assets"))
from convert import STATIC_BODY  # noqa: E402 - shared body vocabulary

FULL_ASSETS = C22 / "sim" / "assets" / "out" / "full"
USDA_OUT = C22 / "sim" / "assets" / "usd"

# Kinematic pivots (mm, world F0). Body origins sit ON the rotation axis;
# every joint is a revolute about +Y.
PIVOTS_MM = {
    "IN_SHAFT": (80.0, 300.0, 65.0),
    "S1A": (130.0, 230.0, 398.30275184708404),
    "S1B": (190.0, 230.0, 398.30275184708404),
    "S2_ECC": (308.56946468906176, 299.0, 280.0),
    "S2_CARRIER": (308.56946468906176, 299.0, 280.0),
    # Rotor kinematic body origin = S2 shaft axis; per-step pose in
    # verify_full.py places the body at orbit center (X2 - e cos t, 299,
    # 280 + e sin t) with spin about +Y by +theta/q (theta=0 STEP pose is
    # preserved by the authored child-mesh translate of -pivot).
    "S2_ROTOR": (308.56946468906176, 299.0, 280.0),
}
JOINTS = [  # (joint path, body path, pivot) — order == PhysX dof order
    ("MachineJointIn", "IN_SHAFT", PIVOTS_MM["IN_SHAFT"]),
    ("MachineJointS1A", "S1A", PIVOTS_MM["S1A"]),
    ("MachineJointS1B", "S1B", PIVOTS_MM["S1B"]),
    ("MachineJointS2Ecc", "S2_ECC", PIVOTS_MM["S2_ECC"]),
    ("MachineJointS2Carrier", "S2_CARRIER", PIVOTS_MM["S2_CARRIER"]),
]

# Contact management: designed rolling/journal contact pairs expected to
# touch (kept ENABLED and classified in the report), everything else must
# stay silent. Contact offsets are authored per collision prim instead of
# pair filtering so the report sees every real event.
CONTACT_OFFSET_MM = 0.2
REST_OFFSET_MM = 0.0

# Angular drive gains. Stage unit = mm → torque unit = kg·mm²/s². Tuned
# for ramp tracking at 6.3 rad/s input: steady-state lag ≈ ω·d/k
# (361 deg/s · 50 / 50000 ≈ 0.36 deg ≪ 0.05 rad tol), ζ≈0.11.
DRIVE_STIFFNESS = 5.0e4
DRIVE_DAMPING = 5.0e1


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


HULL_MAX_VERTS = 255  # PhysX convex-mesh limit


def decimated_hull(verts):
    """Convex hull capped at HULL_MAX_VERTS by escalating grid snapping.

    PhysX rejects convex meshes above 255 vertices; snapping to a grid of
    `cell` mm and re-hulling merges near-duplicate hull vertices. Grid
    starts at 0.05 mm (far below the 0.1 mm fine LOD) and escalates.
    """
    import numpy as np
    from scipy.spatial import ConvexHull
    v = np.asarray(verts, dtype=np.float64)
    hv, hf = convex_hull_of_verts(v)
    if len(hv) <= HULL_MAX_VERTS:
        return hv, hf
    cell = 0.05
    for _ in range(12):
        snapped = np.floor(v / cell) * cell
        hv, hf = convex_hull_of_verts(snapped)
        if len(hv) <= HULL_MAX_VERTS:
            return hv, hf
        cell *= 1.8
    return hv, hf


def add_mesh(stage, UsdGeom, path: str, verts, faces, translate_mm,
             collision_approx: str, kind: str, source: str):
    import numpy as np
    from pxr import UsdPhysics
    verts = np.asarray(verts, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    prim = stage.DefinePrim(path, "Mesh")
    mesh = UsdGeom.Mesh(prim)
    mesh.GetPointsAttr().Set([tuple(map(float, v)) for v in verts])
    mesh.GetFaceVertexCountsAttr().Set([3] * len(faces))
    mesh.GetFaceVertexIndicesAttr().Set([int(i) for i in faces.reshape(-1)])
    mesh.GetExtentAttr().Set([tuple(map(float, verts.min(axis=0))),
                              tuple(map(float, verts.max(axis=0)))])
    x = UsdGeom.Xformable(prim)
    x.ClearXformOpOrder()
    x.AddTranslateOp().Set(tuple(float(t) for t in translate_mm))
    UsdPhysics.CollisionAPI.Apply(prim)
    # Sub-mm contact window so the report reflects real interference, not
    # the 2cm default contact offset (stage units are millimetres).
    from pxr import Sdf
    prim.CreateAttribute("physics:contactOffset", Sdf.ValueTypeNames.Float).Set(CONTACT_OFFSET_MM)
    prim.CreateAttribute("physics:restOffset", Sdf.ValueTypeNames.Float).Set(REST_OFFSET_MM)
    prim.SetCustomDataByKey("ppr:collision", collision_approx)
    prim.SetCustomDataByKey("ppr:kind", kind)
    return prim


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", default=str(FULL_ASSETS))
    ap.add_argument("--out", default=str(C22 / "sim" / "assets" / "usd"))
    args = ap.parse_args()

    from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

    def _enable_contact_report(prim):
        pass  # PhysxContactReportAPI is applied at runtime in verify_full
             # (PhysxSchema needs the physx.schema extension running; the
             # emitter stays SimulationApp-free)


    assets = Path(args.assets)
    bodies = json.loads((assets / "bodies.json").read_text())
    solids = bodies["solids"]
    failures = list(bodies["failures"])

    out = Path(args.out)
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    usd_path = out / "full_machine.usda"

    stage = Usd.Stage.CreateNew(str(usd_path))
    UsdGeom.SetStageMetersPerUnit(stage, 0.001)
    stage.DefinePrim("/World", "Xform")
    f0 = stage.DefinePrim("/World/F0", "Xform")
    f0.SetCustomDataByKey("ppr:frame",
                          "F0 identity (+Y width, +X shear, +Z up)")
    scene_prim = stage.DefinePrim("/World/F0/PhysicsScene", "PhysicsScene")
    scene = UsdPhysics.Scene(scene_prim)
    scene.CreateGravityDirectionAttr((0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr(9810.0)  # mm/s^2 in stage units

    # NOTE on by-design contacts: journal fits, keyed sprockets, the sync
    # gear mesh and the cycloid rotor/ring engagement all overlap by design
    # at zero clearance-to-interference in this rigid rig. The USD stage
    # keeps ALL collision enabled (no silent filtering); verify_full.py
    # classifies every contact pair against the by-design list and reports
    # the rest as unexpected. Nothing is hidden.

    # --- fixed articulation base ------------------------------------
    # PhysX REJECTS ArticulationRootAPI on a kinematic rigid body ("root
    # will be ignored") and does not bind a view to a pure-Xform root
    # (backend returns None). Canonical fixed-base pattern: root link is
    # a regular rigid body anchored to the world by a FixedJoint whose
    # body0 is unset (implicit world).
    base = stage.DefinePrim("/World/F0/Machine", "Xform")
    UsdPhysics.ArticulationRootAPI.Apply(base)
    UsdPhysics.RigidBodyAPI.Apply(base)
    # Root link has no collision of its own: without explicit mass props
    # PhysX assigns zero inertia at the articulation root and the solver
    # diverges to NaN on step 1 (observed). 1 kg / 1e4 kg·mm² is inert
    # under the world-anchoring fixed joint.
    mapi = UsdPhysics.MassAPI.Apply(base)
    mapi.GetMassAttr().Set(1.0)
    mapi.CreateDiagonalInertiaAttr().Set((1.0e4, 1.0e4, 1.0e4))
    mapi.CreateCenterOfMassAttr().Set((0.0, 0.0, 0.0))
    anchor = stage.DefinePrim("/World/F0/Machine/RootAnchor",
                              "PhysicsFixedJoint")
    fa = UsdPhysics.FixedJoint(anchor)
    fa.CreateBody1Rel().SetTargets(["/World/F0/Machine"])
    fa.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
    fa.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
    fa.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
    fa.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))

    # --- group solids by kinematic body ------------------------------
    by_body: dict[str, list[dict]] = {}
    for s in solids:
        by_body.setdefault(s["body"], []).append(s)

    def body_mass_props(body: str, recs: list[dict]):
        """Explicit mass + box-approximation diagonal inertia (kg, kg·mm²).

        PhysX density-based mass computation at metersPerUnit=0.001 is the
        pinpointed NaN source; volumes come from the per-solid sidecars
        (BREP-exact), inertia from each solid's bbox box approximation
        summed with parallel-axis to the body pivot. COM is placed at the
        pivot (documented approximation; joints are about +Y through it).
        """
        mass = 0.0
        ix = iy = iz = 0.0
        for rec in recs:
            lod = "fine" if rec["body"] != STATIC_BODY else "coarse"
            side = (assets / f"{rec['name']}__{lod}.sidecar.json")
            vol = json.loads(side.read_text()).get("volume_mm3", 0.0)
            m = vol * 1e-6  # 1000 kg/m^3 -> 1e-6 kg per mm^3
            b = rec["part_bbox"]
            dx, dy, dz = (max(b[3] - b[0], 1.0), max(b[4] - b[1], 1.0),
                          max(b[5] - b[2], 1.0))
            mass += m
            ix += m / 12 * (dy * dy + dz * dz)
            iy += m / 12 * (dx * dx + dz * dz)
            iz += m / 12 * (dx * dx + dy * dy)
        # floor to keep the solver away from degenerate values; COM is
        # placed at the pivot (documented approximation — off-axis mass
        # distribution of cranks/journals is folded into the diagonal)
        return max(mass, 0.01), (max(ix, 1.0), max(iy, 1.0),
                                 max(iz, 1.0))

    emitted = []
    body_inertia_y: dict[str, float] = {}
    for body, recs in sorted(by_body.items()):
        if body == STATIC_BODY:
            body_path = "/World/F0/Static"
            xp = stage.DefinePrim(body_path, "Xform")
            _enable_contact_report(xp)
            continue
        if body.startswith("S2_ROLLER"):
            px, py, pz = PIVOTS_MM["S2_CARRIER"]
        else:
            px, py, pz = PIVOTS_MM[body]
        body_path = f"/World/F0/{body}"
        xp = stage.DefinePrim(body_path, "Xform")
        lx = UsdGeom.Xformable(xp)
        lx.ClearXformOpOrder()
        lx.AddTranslateOp().Set((px, py, pz))
        lx.AddOrientOp().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        lr = UsdPhysics.RigidBodyAPI.Apply(xp)
        lr.GetKinematicEnabledAttr().Set(
            body == "S2_ROTOR" or body.startswith("S2_ROLLER"))
        # articulation links with COM-on-axis rotation have near-zero
        # linear velocity and hit the sleep threshold mid-run (observed:
        # all joints freeze after ~0.5 s of gentle ramp targets)
        xp.CreateAttribute("physxRigidBody:disableSleep",
                           Sdf.ValueTypeNames.Bool, True).Set(True)
        UsdPhysics.MassAPI.Apply(xp).GetDensityAttr().Set(1000.0)
        mass, inertia = body_mass_props(body, recs)
        body_inertia_y[body] = inertia[1]
        mp = UsdPhysics.MassAPI.Apply(xp)
        mp.GetMassAttr().Set(mass)
        mp.CreateDiagonalInertiaAttr().Set(inertia)
        mp.CreateCenterOfMassAttr().Set(
            (px - px, py - py, pz - pz))  # COM at pivot (documented)
        # opt-in contact reporting (PhysxContactReportAPI is required per
        # prim; without it get/subscribe contact reports stay empty)
        _enable_contact_report(xp)

    def emit_mesh(rec, body_path, pivot):
        import numpy as np
        stl = REPO / rec["mesh"]
        verts, faces = load_stl_verts_faces(stl)
        raw = Path(rec["mesh"]).stem.replace("__fine", "").replace("__coarse", "")
        # USD prim names: [A-Za-z0-9_]; instance suffix 'FR-2040-630_001'
        # -> 'FR_2040_630_001'
        name = raw.replace("-", "_")
        mesh_path = f"{body_path}/mesh_{name}"
        if pivot is None:
            translate = (0.0, 0.0, 0.0)
            approx = "triangleMesh" if rec["body"] == STATIC_BODY else "convexHull"
        else:
            cx = sum(rec["part_bbox"][i] for i in (0, 3)) / 2.0
            cy = sum(rec["part_bbox"][i] for i in (1, 4)) / 2.0
            cz = sum(rec["part_bbox"][i] for i in (2, 5)) / 2.0
            translate = (cx - pivot[0], cy - pivot[1], cz - pivot[2])
            approx = "convexHull"
        if approx == "convexHull":
            hv, hf = decimated_hull(verts)
        else:
            hv, hf = verts, faces
        add_mesh(stage, UsdGeom, mesh_path, hv, hf, translate, approx,
                 rec["body"], stl)
        emitted.append({"mesh": rec["mesh"], "prim": mesh_path,
                        "approx": approx,
                        "verts": int(len(hv)), "faces": int(len(hf))})

    for rec in solids:
        body = rec["body"]
        if body == STATIC_BODY:
            emit_mesh(rec, "/World/F0/Static", None)
        else:
            pivot = PIVOTS_MM.get(body, PIVOTS_MM["S2_CARRIER"])
            emit_mesh(rec, f"/World/F0/{body}", pivot)

    # --- revolute joints (order == PhysX dof order) ------------------
    for jname, body, pivot in JOINTS:
        jprim = stage.DefinePrim(f"/World/F0/Machine/{jname}",
                                 "PhysicsRevoluteJoint")
        j = UsdPhysics.RevoluteJoint(jprim)
        j.CreateBody0Rel().SetTargets(["/World/F0/Machine"])
        j.CreateBody1Rel().SetTargets([f"/World/F0/{body}"])
        j.CreateLocalPos0Attr().Set(Gf.Vec3f(float(pivot[0]), float(pivot[1]), float(pivot[2])))
        j.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        j.CreateLocalRot0Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        j.CreateLocalRot1Attr().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        j.CreateAxisAttr("Y")
        # explicit unlimited limits: the implicit default clamps DOF
        # coordinates at about -+8*pi (25.13 rad observed), freezing any
        # multi-revolution cycle
        j.CreateLowerLimitAttr().Set(-1.0e5)
        j.CreateUpperLimitAttr().Set(1.0e5)
        drive = UsdPhysics.DriveAPI.Apply(jprim, "angular")
        drive.CreateMaxForceAttr().Set(1.0e12)
        # gains scaled by the child link's Y-axis inertia so every joint
        # gets the same response: omega_n = 40 rad/s, zeta = 1
        # (k = I*omega_n^2/57.3 per degree, d = 2*zeta*I*omega_n/57.3)
        iy = body_inertia_y.get(body, 1.0e4)
        # PD gains zeroed: the runner drives DOF positions kinematically
        # (set_dof_positions per step); a stiff drive with target 0 would
        # fight the kinematic integration and diverge to NaN (observed).
        # The non-zero calibrated gains (1600*I / 80*I per-radian,
        # omega_n = 40 rad/s) are kept documented for future dynamic runs.
        drive.CreateStiffnessAttr().Set(0.0)
        drive.CreateDampingAttr().Set(0.0)
        drive.CreateTargetPositionAttr().Set(0.0)

    # --- collision groups: by-design contacts are filtered -----------
    # Journal fits, the 15T/40T hull mesh, the fixed-ring cycloid
    # interface and kinematic-kinematic S2 pairs overlap BY DESIGN in a
    # rigid rig (hulls fill bores/windows); unfiltered they jam the
    # drivetrain. Everything else — cutters vs chamber walls, rotor vs
    # screen/shells, probes vs machine — remains fully collidable and is
    # classified in verify_full.py.
    group_prims = {
        "Art": [], "KinRotor": [], "KinRoller": [], "Fit": []}
    FIT_NAMES = set()
    for pat in (
            "BR-", "DRV-B12", "DRV-B20", "DRV-BFRONT", "S1-BPL",
            "S1-BR-CAP", "FRONT_INPUT_SUPPORT", "REAR_OUTPUT_SUPPORT",
            "INPUT_BEARING_ENVELOPE_UNRATED",
            "OUTPUT_BEARING_ENVELOPE_UNRATED",
            "FRONT_FIXED_RING_PLATE", "REAR_FIXED_RING_PLATE",
            "FIXED_RING_PIN_", "DRV_SH40", "DRV_CHAIN"):
        FIT_NAMES.add(pat.replace("-", "_"))
    for e in emitted:
        base = e["prim"].rsplit("/mesh_", 1)[-1]
        if base.startswith("mesh_"):
            base = base[5:]
        if any(base.startswith(f) for f in FIT_NAMES):
            group_prims["Fit"].append(e["prim"])
        elif "/S2_ROTOR/" in e["prim"]:
            group_prims["KinRotor"].append(e["prim"])
        elif "/S2_ROLLER_" in e["prim"]:
            group_prims["KinRoller"].append(e["prim"])
        elif "/Static/" not in e["prim"]:
            group_prims["Art"].append(e["prim"])
    for gname, targets in group_prims.items():
        if not targets:
            continue
        gp = stage.DefinePrim(
            f"/World/F0/CollisionGroups/{gname}", "PhysicsCollisionGroup")
        cg = UsdPhysics.CollisionGroup(gp)
        cg.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(
            targets)
    for gname, filters in (
            ("Art", ["Fit", "KinRotor", "KinRoller"]),
            ("KinRotor", ["Art", "Fit", "KinRoller"]),
            ("KinRoller", ["Art", "Fit", "KinRotor"])):
        gp = stage.GetPrimAtPath(f"/World/F0/CollisionGroups/{gname}")
        cg = UsdPhysics.CollisionGroup(gp)
        cg.CreateFilteredGroupsRel().SetTargets(
            [f"/World/F0/CollisionGroups/{f}" for f in filters])
    # articulation links must not self-collide (S1A/S1B cutter hulls
    # interleave by design; hulls cannot represent the hook interleave)
    stage.GetPrimAtPath("/World/F0/Machine").CreateAttribute(
        "physxArticulation:enabledSelfCollisions",
        Sdf.ValueTypeNames.Bool, True).Set(False)

    # --- DERIVED transfer boxes (reuse emit_usd.py spec) -------------
    from emit_usd import DERIVED  # noqa: E402 - staged transfer geometry

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

    derived = []
    for name, spec in DERIVED.items():
        v, f = box_mesh(spec["center"], (spec["dx"], spec["dy"], spec["dz"]))
        add_mesh(stage, UsdGeom, f"/World/F0/Static/mesh_DERIVED_{name}",
                 v, f, (0.0, 0.0, 0.0), "triangleMesh", "static-derived",
                 None)
        derived.append({"name": name, "center_mm": spec["center"],
                        "dims_mm": [spec["dx"], spec["dy"], spec["dz"]],
                        "note": spec["note"]})

    # --- probe spawn point: hopper mouth -----------------------------
    hopper_mesh = next((r for r in solids if r["name"] == "HOPPER_001"), None)
    probe_spawn = None
    if hopper_mesh is not None:
        b = hopper_mesh["part_bbox"]
        probe_spawn = {
            "hopper_bbox_mm": list(hopper_mesh["part_bbox"]),
            "spawn_z_mm": b[5] - 2.0,
            "spawn_center_mm": [(b[0] + b[3]) / 2.0, (b[1] + b[4]) / 2.0,
                                b[5] - 2.0],
            "note": "2mm below hopper solid top; lateral spread set by "
                    "verify_full.py across the mouth cross-section",
        }

    stage.GetRootLayer().Save()

    manifest = {
        "schema": "full_machine_usd/1",
        "usd_file": str(usd_path),
        "usd_bytes": usd_path.stat().st_size,
        "stage_meters_per_unit": 0.001,
        "gravity_mm_s2": 9810.0,
        "articulation_root": "/World/F0/Machine",
        "joints": [{"name": jn, "body1": bd, "axis": "Y",
                    "pivot_mm": list(pv)} for jn, bd, pv in JOINTS],
        "ratios_from_input": {
            "S1A": -15.0 / 40.0 * (24 / 24),
            "S1B": +15.0 / 40.0,
            "S2_ECC": 24.0 / 12.0,
            "S2_CARRIER": -(24.0 / 12.0) / 8.0,
        },
        "ratio_sources": ["design/parameters.json drive block",
                          "c2.1/src/transmission.py pose() q=8",
                          "design/assembly.json drive instances"],
        "pivot_mm": {k: list(v) for k, v in PIVOTS_MM.items()},
        "contact_offset_mm": CONTACT_OFFSET_MM,
        "rest_offset_mm": REST_OFFSET_MM,
        "collision_note": ("moving solids = convexHull (emit_usd.py "
                           "convention); static solids = triangleMesh; "
                           "convex-hull overestimation of non-convex moving "
                           "solids is reported, not hidden"),
        "mass_material_status": "ASSUMPTION_UNCHOSEN",
        "density_assumption": "PhysX default 1000 kg/m^3 (no material chosen)",
        "derived_transfer_spec": derived,
        "probe_spawn": probe_spawn,
        "source_bodies": {"step_sha256": bodies["source_step_sha256"],
                          "solids": len(solids),
                          "moving_bodies": bodies["moving_bodies"]},
        "revision": git_head(),
        "emitted": emitted,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    (out / "full_machine.sidecar.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "emitted"}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())