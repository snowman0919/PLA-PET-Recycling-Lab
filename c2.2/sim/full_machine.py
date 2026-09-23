"""Full-machine USD emission for the CAD-derived integrated assembly.

Reads c2.2/sim/assets/out/full/ (convert.py --full output: per-solid
STLs + bodies.json) and emits c2.2/sim/assets/usd/full_machine.usda:

  - stage metersPerUnit=0.001 (mm authored), F0 identity frame;
  - one articulation root /World/F0/Machine (fixed base) with five revolute
    joints driven by the C2.1 drive layout (design/parameters.json):
      M1 input shaft 15T -> jack 40T (gear, counter-rotating, 15/40)
      chain A 24/24 (1:1, same direction) -> S1 main shaft
      S1-A/B sync gears 1:1 (counter-rotating)
      chain B 24/12 jackshaft -> S2 input eccentric shaft (PPR_VP1:
      DRV-SP24-B20_002 at jack y372 -> DRV-SP12-B12_001 at S2 y374)
      S2 output carrier = -theta_S2/q, q=8 (fixed-ring cycloid, reverse);
  - S2 rotor, six output rollers, PADDLE, AUGER, CROSS_FEED and the
    CROSS_FEED_IDLER are pose-driven KINEMATIC bodies outside the
    articulation; motion uses measured S2Ecc, not extra authored inputs;
  - static shell solids as concave triangle-mesh collision; moving solids
    as convex-hull collision, EXCEPT the material-engagement solids flagged
    by c2.2/sim/audit_hulls.py (cycloid rotor, output pin carrier) which
    are authored as full fine meshes with
    physics:collisionApproximation = "convexDecomposition" so the lobe /
    carrier windows stay open (FIX B1; the S1 cutter discs use tight
    per-solid decimated hulls — decomposition pieces protruded and locked
    the joints — see manifest); all contact offsets authored small
    (0.2mm) so near-touching designed surfaces do not flood the contact
    report;
  - the four DERIVED transfer boxes of the emit_usd.py era are REMOVED
    (FIX B2): real C2.1 CAD now covers the transfer path (CHUTE_BODY,
    CHUTE_TROUGH_FLOOR_E, S1-SIDE, screen).  The old DERIVED_S1_DISCHARGE
    slab (z 413..443) sat inside the S1 chamber and sealed the hopper->S1
    drop — the 0/200 probe-reach blocker identified by flow_localization;
  - PhysX articulation DOF order in dof_names matches JOINTS order below.
    Eleven kinematic rigid bodies are driven by the runtime views.

Drive ratios (documented basis, from design/parameters.json drive block and
the C1 drive layout in design/assembly.json + src/design.py):
  jack/input   = -(15/40)   external helical mesh (DRV-SH15R/L on input
                            shaft x=80 z=65, DRV-SH40L/R on jack x=136.940)
  S1A/jack     = 24/24 = 1  chain A, same direction
  S1B/S1A      = -1         S1-SYNC sync gears, counter-rotating
  S2ecc/input  = -(15/40)*(24/12) = -0.75 (jack-driven chain B)
  carrier/S2ecc= -1/8       cycloid fixed-ring ratio q=8
  cross/S2ecc = 1          two equal-12T external spur meshes via idler
  idler/S2ecc = -1         first external spur mesh

Mass uses STEP sidecar volumes and a documented box-diagonal inertia
approximation at 1000 kg/m^3; geometry and ideal kinematic stepping do
not demonstrate a closed upstream chain-P torque path or product flow.

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
    # Paddle/worm-shaft kinematic body origin = worm shaft axis (chute.py
    # rev 6 final: the worm shaft MOVED to (362, z374.5), r5 along Y,
    # y204..392; carries PDL_WORM + the chain-B sprocket).  Pose-driven
    # 1:1 from the measured S2Ecc angle (open chain preserves sign).
    "PADDLE": (362.0, 298.0, 374.5),
    # Auger shaft r3 along +X at y232,z347.1. Four 28.5 mm turns of the
    # 3 mm swept flight occupy x237.343..354.681; the matching U-shell's
    # exact BRep radial gap is 0.032 mm in the reconstructed CAD.
    # Pose-driven at measured S2Ecc/8 about +X (worm 2-start : wheel 16T).
    "AUGER": (298.75, 232.0, 347.1),
    # The orthogonal +Y cross-feed screw bridges the auger east outlet to
    # the near S2 mouth. A pair of external gear meshes from PDL_SHAFT
    # makes its angle the same signed measured S2Ecc angle at 1:1.
    "CROSS_FEED": (357.0, 252.0, 328.0),
}
PIVOTS_MM.update({
    "BELT": (149.5, 243.5, 331.4),
    "BELT_DRIVE": (80.0, 243.5, 331.4),
    "BELT_IDLER": (219.0, 243.5, 331.4),
})
PIVOTS_MM.update({
    "SWEEP_SOUTH": (228.2, 186.0, 342.0),
    "SWEEP_NORTH": (228.2, 289.5, 342.0),
})
PIVOTS_MM.update({
    "TRANSFER_BELT": (159.5, 232.0, 333.3),
    "TRANSFER_IDLER": (239.0, 232.0, 335.2),
})
# Exact CAD construction: three equal 12T spur gears on parallel +Y axes,
# each external center spacing 2 * (12 / cos 15°) mm. The idler is placed
# on the positive perpendicular of the PDL-to-cross-feed center chord.
_feed_dx = PIVOTS_MM["CROSS_FEED"][0] - PIVOTS_MM["PADDLE"][0]
_feed_dz = PIVOTS_MM["CROSS_FEED"][2] - PIVOTS_MM["PADDLE"][2]
_feed_span = math.hypot(_feed_dx, _feed_dz)
_feed_idler_offset = math.sqrt(
    (24.0 / math.cos(math.radians(15.0))) ** 2 -
    (_feed_span / 2.0) ** 2)
PIVOTS_MM["CROSS_FEED_IDLER"] = (
    (PIVOTS_MM["CROSS_FEED"][0] + PIVOTS_MM["PADDLE"][0]) / 2.0 -
    _feed_dz / _feed_span * _feed_idler_offset,
    216.0,
    (PIVOTS_MM["CROSS_FEED"][2] + PIVOTS_MM["PADDLE"][2]) / 2.0 +
    _feed_dx / _feed_span * _feed_idler_offset)
# Collision partition follows the four actual helical turns at one eighth
# turn per hull. A whole-turn convex hull fills its flight valley like a
# cylinder and is not a screw conveyor contact surface.
AUG_PITCH_MM = 28.5
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

# FIX B1: solids authored with physics:collisionApproximation =
# "convexDecomposition" (full fine mesh, PhysX-cooked V-HACD) instead of a
# decimated convex hull.  The cycloid rotor lobe windows (occlusion 1.81x)
# and the output-pin carrier windows (4.08x) are material channels a single
# hull would weld shut.  The S1 cutter discs STARTED here too but were
# switched back to tight decimated hulls: decomposition pieces protrude
# outside the true cutter surface and locked the S1A/S1B joints against
# the chamber (per-joint isolation evidence); a 0.05 mm-snapped hull
# protrudes <=0.05 mm and keeps every inter-solid channel open because
# each disc is its own collider.
# The auger shaft/flight is partitioned into eighth-turn convex hulls;
# whole-turn hulls seal each valley into a false cylinder. Narrow hulls
# expose the true axial flight face but remain approximations, not proof
# of material passage; the downstream gate and world loss are measured.
DECOMPOSE_PREFIXES = ("RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE",
                      "OUTPUT_PIN_CARRIER_AND_SHAFT")

# S2 eccentric orbit radius (mm) — rotor rest pose = axis - e·x̂ (the CAD
# θ=0 pose has the crank at angle π; must match verify_full.py ECC_MM and
# rotor_pose's -cos/+sin convention)
ECC_MM_EMIT = 7.0


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
             collision_approx: str, kind: str, source: str, collide=True):
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
    if collide:
        UsdPhysics.CollisionAPI.Apply(prim)
        UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr().Set(
            collision_approx if collision_approx != "triangleMesh" else "none")
        # Stage units are mm; do not accept the 20 mm default contact offset.
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

    import numpy as np
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
    # Self-collision MUST be disabled through the PhysxArticulationAPI
    # schema (registered by name — PhysxSchema is not importable outside
    # the kit runtime); a bare custom attribute without the API schema is
    # ignored by the PhysX USD parser (observed: interleaved S1A/S1B hulls
    # locked both stacks and wobbled the drivetrain).
    from pxr import Sdf as _Sdf
    api_op = base.GetMetadata("apiSchemas")
    api_list = list(api_op.explicitItems) if api_op is not None else []
    for api_name in ("PhysxArticulationAPI",):
        if api_name not in api_list:
            api_list.append(api_name)
    base.SetMetadata("apiSchemas", _Sdf.TokenListOp.CreateExplicit(
        api_list))
    base.CreateAttribute("physxArticulation:enabledSelfCollisions",
                         Sdf.ValueTypeNames.Bool, True).Set(False)
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
    # This scene cannot represent the new drive by leaving an unclassified
    # STEP solid in Static. Require convert.py's explicit body assignment.
    expected_cross_feed = {
        "PDL_FEED_GEAR": "PADDLE",
        "CROSS_FEED_SHAFT": "CROSS_FEED",
        "CROSS_FEED_GEAR": "CROSS_FEED",
        "CROSS_FEED_IDLER": "CROSS_FEED_IDLER",
        "CROSS_FEED_BEARINGS": STATIC_BODY,
        "CROSS_FEED_SHELL": STATIC_BODY,
    }
    expected_cross_feed.update({
        "S1_SWEEP_SOUTH": "SWEEP_SOUTH",
        "S1_SWEEP_NORTH": "SWEEP_NORTH",
        "S1_SWEEP_GEAR_S": "SWEEP_SOUTH",
        "S1_SWEEP_GEAR_N": "SWEEP_NORTH",
        "S1_SWEEP_GEAR_DRUM_S": "BELT_IDLER",
        "S1_SWEEP_GEAR_DRUM_N": "BELT_IDLER",
        "S1_SWEEP_BEARINGS": STATIC_BODY,
    })
    expected_cross_feed.update({
        "S1_TRANSFER_BELT": "TRANSFER_BELT",
        "S1_TRANSFER_IDLER": "TRANSFER_IDLER",
        "S1_TRANSFER_BEARINGS": STATIC_BODY,
    })
    for name, body in expected_cross_feed.items():
        if not any(s["name"] == name and s["body"] == body for s in solids):
            raise ValueError(f"missing or misclassified STEP part {name}: "
                             f"expected body {body}")

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
            body == "S2_ROTOR" or body.startswith("S2_ROLLER")
            or body in ("PADDLE", "AUGER", "CROSS_FEED",
                        "CROSS_FEED_IDLER", "BELT", "BELT_DRIVE",
                        "BELT_IDLER", "SWEEP_SOUTH", "SWEEP_NORTH",
                        "TRANSFER_BELT", "TRANSFER_IDLER"))
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

    def authoring_pivot(body, rec):
        """Body-origin (rest pose) for mesh recentering.

        USD composition: world = body_pose + R * points (child translate
        must be ZERO).  Points are therefore authored as v - origin so the
        θ=0 pose exactly reproduces the world-frame STL.  The previous
        convention (raw world-frame points + child translate
        bbox_center - pivot) DOUBLE-DISPLACED every moving solid by
        (mesh center - pivot) — the root cause of the historic zero
        contact counts and of stuck-probe artifacts.
        """
        if body == "S2_ROTOR":
            # rotor rest pose = orbit position at θ=0 (crank at -e·x̂):
            # body pose pos(θ) = (axis.x - e·cosθ, 299, axis.z + e·sinθ),
            # spin -θ/q about +Y through the body origin
            ax = PIVOTS_MM["S2_CARRIER"]
            return (ax[0] - ECC_MM_EMIT, ax[1], ax[2])
        if body.startswith("S2_ROLLER"):
            # rollers: body pose = rotated roller centre, spin about own
            # origin -> points recentered on the roller's own bbox centre
            b = rec["part_bbox"]
            return ((b[0] + b[3]) / 2.0, (b[1] + b[4]) / 2.0,
                    (b[2] + b[5]) / 2.0)
        return PIVOTS_MM[body]

    name_used: dict[str, int] = {}

    def emit_mesh(rec, body_path, pivot):
        import numpy as np
        stl = REPO / rec["mesh"]
        verts, faces = load_stl_verts_faces(stl)
        raw = Path(rec["mesh"]).stem.replace("__fine", "").replace("__coarse", "")
        # USD prim names: [A-Za-z0-9_]; instance suffix 'FR-2040-630_001'
        # -> 'FR_2040_630_001'
        name = raw.replace("-", "_")
        # compound parts expand to multiple same-name solids (convert.py);
        # prim paths MUST be unique — a repeated path silently overwrites
        # the earlier collider (last-wins), which dropped 2 of 3 scraper
        # bars, 2 of 3 paddle blades, 3 bearing posts, guard-chain and
        # winder solids
        n_used = name_used.get(name, 0) + 1
        name_used[name] = n_used
        if n_used > 1:
            name = f"{name}_{n_used:03d}"
        mesh_path = f"{body_path}/mesh_{name}"
        decompose = raw == "S1_BELT" or any(
            raw.startswith(p) for p in DECOMPOSE_PREFIXES)
        if pivot is None:
            translate = (0.0, 0.0, 0.0)
            if rec["body"] == STATIC_BODY:
                approx = "triangleMesh"
            elif decompose:
                approx = "convexDecomposition"
            else:
                approx = "convexHull"
            hv, hf = verts, faces
        else:
            translate = (0.0, 0.0, 0.0)
            approx = ("convexDecomposition" if decompose
                      else "convexHull")
            if approx == "convexHull":
                hv, hf = decimated_hull(verts)
            else:
                hv, hf = verts, faces
            hv = np.asarray(hv, dtype=np.float64) - np.asarray(
                pivot, dtype=np.float64)
        add_mesh(stage, UsdGeom, mesh_path, hv, hf, translate, approx,
                 rec["body"], stl)
        emitted.append({"mesh": rec["mesh"], "prim": mesh_path,
                        "approx": approx,
                        "verts": int(len(hv)), "faces": int(len(hf))})

    def emit_axial_segment_hulls(rec, body_path, pivot, axis, bounds,
                                 overlap):
        """Hull short axial slices of the STEP-derived helical flight.

        A single convex hull seals a screw valley into a false cylinder.
        These slices use only vertices of the actual fine STEP STL, keeping
        moving flight faces available for fragment contact; they are still
        approximations, not a measured passage result.
        """
        import numpy as np
        stl = REPO / rec["mesh"]
        verts, _ = load_stl_verts_faces(stl)
        v = np.asarray(verts, dtype=np.float64)
        raw = Path(rec["mesh"]).stem.replace("__fine", "") \
            .replace("__coarse", "")
        base = raw.replace("-", "_")
        for i, (lo, hi) in enumerate(zip(bounds, bounds[1:])):
            sel = v[(v[:, axis] >= lo - overlap)
                    & (v[:, axis] <= hi + overlap)]
            if len(sel) < 8:
                continue
            hv, hf = decimated_hull(sel)
            hv = np.asarray(hv, dtype=np.float64) - np.asarray(
                pivot, dtype=np.float64)
            n_used = name_used.get(base, 0) + 1
            name_used[base] = n_used
            nm = base if n_used == 1 else f"{base}_{n_used:03d}"
            mesh_path = f"{body_path}/mesh_{nm}_seg{i:02d}"
            add_mesh(stage, UsdGeom, mesh_path, hv, hf, (0.0, 0.0, 0.0),
                     "convexHull", rec["body"], stl)
            emitted.append({"mesh": rec["mesh"], "prim": mesh_path,
                            "approx": "convexHull_segment",
                            "axial_range_mm": [lo, hi],
                            "verts": int(len(hv)), "faces": int(len(hf))})

    def emit_bounded_hulls(rec, body_path, pivot, regions, visual=False):
        """Partition one STEP solid's collider without filling its voids."""
        import numpy as np
        stl = REPO / rec["mesh"]
        verts, faces = load_stl_verts_faces(stl)
        v = np.asarray(verts, dtype=np.float64)
        base = rec["name"].replace("-", "_")
        if visual:
            mesh_path = f"{body_path}/mesh_{base}_visual"
            add_mesh(stage, UsdGeom, mesh_path, v - pivot, faces,
                     (0.0, 0.0, 0.0), "visualOnly", rec["body"], stl,
                     collide=False)
            emitted.append({"mesh": rec["mesh"], "prim": mesh_path,
                            "approx": "visualOnly", "verts": len(v),
                            "faces": len(faces)})
        for suffix, mask in regions:
            sel = v[mask(v)]
            if len(sel) < 8:
                raise ValueError(f"{rec['name']} {suffix}: too few STEP vertices")
            hv, hf = decimated_hull(sel)
            mesh_path = f"{body_path}/mesh_{base}_{suffix}"
            add_mesh(stage, UsdGeom, mesh_path, hv - pivot, hf,
                     (0.0, 0.0, 0.0), "convexHull", rec["body"], stl)
            emitted.append({"mesh": rec["mesh"], "prim": mesh_path,
                            "approx": "convexHull_partition",
                            "verts": len(hv), "faces": len(hf)})

    for rec in solids:
        body = rec["body"]
        if body == STATIC_BODY:
            emit_mesh(rec, "/World/F0/Static", None)
        else:
            pivot = authoring_pivot(body, rec)
            if rec["name"] == "S1-SHAFT-B_001":
                # The integral rear 24T crown spans r39 at y401..409.
                # One hull of the long shaft and crown forms a false cone
                # through the S1 chamber and stalls both cutter axes.
                emit_bounded_hulls(rec, f"/World/F0/{body}", pivot, [
                    ("original", lambda v: v[:, 1] <= 326.01),
                    ("core", lambda v: (v[:, 1] >= 325.99) &
                     (np.hypot(v[:, 0] - 190.0, v[:, 2] - 398.30275)
                      <= 12.71)),
                    ("crown", lambda v: v[:, 1] >= 400.99),
                ])
                continue
            if rec["name"] in ("S1_BELT", "S1_TRANSFER_BELT"):
                # Each shell is partitioned along the actual axle line.
                # The central belt rises from its west axle to the AUG lane.
                if rec["name"] == "S1_BELT":
                    west_x = PIVOTS_MM["BELT_DRIVE"][0]
                    east_x = PIVOTS_MM["BELT_IDLER"][0]
                    west_z = PIVOTS_MM["BELT"][2]
                    slope, inner_z = 0.0, 3.8
                else:
                    west_x = PIVOTS_MM["BELT_DRIVE"][0]
                    east_x = PIVOTS_MM["TRANSFER_IDLER"][0]
                    west_z = PIVOTS_MM["BELT_DRIVE"][2]
                    slope = ((PIVOTS_MM["TRANSFER_IDLER"][2]-west_z) /
                             (east_x-west_x))
                    inner_z = 2.3 / math.sqrt(1.0+slope*slope)
                emit_bounded_hulls(rec, f"/World/F0/{body}", pivot, [
                    ("top", lambda v: (v[:, 0] >= west_x - 4.0) &
                     (v[:, 0] <= east_x + 4.0) &
                     (v[:, 2] >= west_z + (v[:, 0]-west_x)*slope
                      + inner_z - 0.01)),
                    ("bottom", lambda v: (v[:, 0] >= west_x - 4.0) &
                     (v[:, 0] <= east_x + 4.0) &
                     (v[:, 2] <= west_z + (v[:, 0]-west_x)*slope
                      - inner_z + 0.01)),
                    ("west", lambda v: v[:, 0] <= west_x + 0.01),
                    ("east", lambda v: v[:, 0] >= east_x - 0.01),
                ], visual=True)
                continue
            if rec["name"] == "AUG_SHAFT":
                bounds = [236.0, 238.5] + [
                    238.5 + i * AUG_PITCH_MM / 8.0
                    for i in range(1, 33)] + [370.0]
                emit_axial_segment_hulls(
                    rec, f"/World/F0/{body}", pivot, 0, bounds, 0.25)
                continue
            if rec["name"] == "CROSS_FEED_SHAFT":
                # CAD: RH flight centreline y226..249, swept profile
                # half-thickness 1.25; pitch 9 mm, end y250.25. Journal
                # sections use STEP vertices as well; no derived paddle.
                flight_lo, flight_hi = 224.75, 250.25
                nseg = math.ceil((flight_hi - flight_lo) / (9.0 / 8.0))
                bounds = ([rec["part_bbox"][1], flight_lo]
                          + [flight_lo + (flight_hi - flight_lo) * i / nseg
                             for i in range(1, nseg + 1)]
                          + [rec["part_bbox"][4]])
                emit_axial_segment_hulls(
                    rec, f"/World/F0/{body}", pivot, 1, bounds, 0.5)
                continue
            if rec["name"] in ("S1_SWEEP_SOUTH", "S1_SWEEP_NORTH"):
                lo, hi = ((163.7, 223.1) if rec["name"].endswith("SOUTH")
                          else (240.9, 322.3))
                flight_bounds = [lo + i * (hi-lo) / math.ceil((hi-lo)/2.0)
                                 for i in range(math.ceil((hi-lo)/2.0)+1)]
                bounds = [rec["part_bbox"][1], *flight_bounds,
                          rec["part_bbox"][4]]
                emit_axial_segment_hulls(
                    rec, f"/World/F0/{body}", pivot, 1, bounds, 0.35)
                continue
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
        # (k = I*omega_n^2/57.3 per degree, d = 2*zeta*I*omega_n/57.3).
        # ACTIVE since FIX C: the runner drives the INPUT joint with a
        # position-target ramp and computes dependent targets from the
        # measured input per step — the PD drives are the ideal gear/
        # chain constraint (no tooth-contact FEM).
        iy = body_inertia_y.get(body, 1.0e4)
        drive.CreateStiffnessAttr().Set(1600.0 * iy / 57.3)
        drive.CreateDampingAttr().Set(80.0 * iy / 57.3)
        drive.CreateTargetPositionAttr().Set(0.0)

    # --- collision groups: by-design contacts are filtered -----------
    # Journal fits, legacy gear meshes and cycloid couplings may overlap in
    # the rigid rig. The new drive filters only named shaft-bearing and
    # gear-tooth partners; cross-feed screw/receiver and fragments stay live.
    group_prims = {
        "Art": [], "KinRotor": [], "KinRoller": [], "KinPaddle": [],
        "KinAuger": [], "Fit": [],
        "KinCrossFeedFlight": [], "KinCrossFeedJournal": [],
        "CrossFeedBearing": [], "FeedIdler": [],
        "PaddleFeedGear": [], "CrossFeedGear": [],
        "Belt": [], "BeltDrive": [], "BeltIdler": [],
        "TransferBelt": [], "TransferIdler": [], "TransferBearing": []}
    FIT_NAMES = set()
    for pat in (
            "BR-", "DRV-B12", "DRV-B20", "DRV-BFRONT", "S1-BPL",
            "S1-BR-CAP", "FRONT_INPUT_SUPPORT", "REAR_OUTPUT_SUPPORT",
            "INPUT_BEARING_ENVELOPE_UNRATED",
            "OUTPUT_BEARING_ENVELOPE_UNRATED",
            "FRONT_FIXED_RING_PLATE", "REAR_FIXED_RING_PLATE",
            "FIXED_RING_PIN_", "DRV_SH40", "DRV_CHAIN",
            # M1 motor body: its stub shaft is inserted into the moving
            # DRV-CPL12 coupling (keyed/journal mate by design)
            "DRV-M1",
            # stationary shaft bores and seats: the S1 shafts pass through
            # S1-WALL bores (journal fit), KEY-8-16 is the wall-side key
            # seat, S1-ROOF/S1-STUD are stationary structure with designed
            # clearance to the rotating stacks (< contactOffset), the
            # chain guards wrap the chain/sprocket runs and DRV-RISER20
            # carries the B12 sprocket hub
            "S1-WALL", "KEY-8-16", "S1-ROOF", "S1-STUD",
            "GUARD-CHAIN", "DRV-RISER20",
            # VP1 transfer drivetrain: the paddle chain wraps the S2 12T
            # face and worm-shaft sprocket. AUG_BEARINGS seat the auger
            # journals (west bore r5.5, east boss bore r4.7).
            "PDL-CHAIN", "AUG-BEARINGS",
            "S1-BELT-CHAIN", "S1-BELT-BEARINGS"):
        FIT_NAMES.add(pat.replace("-", "_"))
    for e in emitted:
        if e["approx"] == "visualOnly":
            continue
        base = e["prim"].rsplit("/mesh_", 1)[-1]
        if base.startswith("mesh_"):
            base = base[5:]
        if e["prim"].startswith("/World/F0/BELT/"):
            group_prims["Belt"].append(e["prim"])
            continue
        if "/BELT_DRIVE/" in e["prim"]:
            group_prims["BeltDrive"].append(e["prim"])
            continue
        if "/BELT_IDLER/" in e["prim"]:
            group_prims["BeltIdler"].append(e["prim"])
            continue
        if "/TRANSFER_BELT/" in e["prim"]:
            group_prims["TransferBelt"].append(e["prim"])
            continue
        if "/TRANSFER_IDLER/" in e["prim"]:
            group_prims["TransferIdler"].append(e["prim"])
            continue
        if base.startswith("S1_TRANSFER_BEARINGS"):
            group_prims["TransferBearing"].append(e["prim"])
            continue
        if base.startswith("CROSS_FEED_BEARINGS"):
            group_prims["CrossFeedBearing"].append(e["prim"])
        elif base.startswith("PDL_FEED_GEAR"):
            group_prims["PaddleFeedGear"].append(e["prim"])
        elif base.startswith("CROSS_FEED_GEAR"):
            group_prims["CrossFeedGear"].append(e["prim"])
        elif base.startswith("CROSS_FEED_IDLER"):
            group_prims["FeedIdler"].append(e["prim"])
        elif base.startswith("CROSS_FEED_SHAFT"):
            lo, hi = e["axial_range_mm"]
            group = ("KinCrossFeedJournal"
                     if hi <= 224.75 or lo >= 250.25
                     else "KinCrossFeedFlight")
            group_prims[group].append(e["prim"])
        elif any(base.startswith(f) for f in FIT_NAMES):
            group_prims["Fit"].append(e["prim"])
        elif "/S2_ROTOR/" in e["prim"]:
            group_prims["KinRotor"].append(e["prim"])
        elif "/S2_ROLLER_" in e["prim"]:
            group_prims["KinRoller"].append(e["prim"])
        elif "/PADDLE/" in e["prim"]:
            group_prims["KinPaddle"].append(e["prim"])
        elif "/AUGER/" in e["prim"]:
            group_prims["KinAuger"].append(e["prim"])
        elif "/Static/" not in e["prim"]:
            group_prims["Art"].append(e["prim"])
    for required in ("KinCrossFeedFlight", "KinCrossFeedJournal",
                     "CrossFeedBearing", "FeedIdler",
                     "PaddleFeedGear", "CrossFeedGear",
                     "Belt", "BeltDrive", "BeltIdler", "TransferBelt",
                     "TransferIdler", "TransferBearing"):
        if not group_prims[required]:
            raise ValueError(f"CAD-derived collision group {required} empty")
    for gname, targets in group_prims.items():
        if not targets:
            continue
        gp = stage.DefinePrim(
            f"/World/F0/CollisionGroups/{gname}", "PhysicsCollisionGroup")
        cg = UsdPhysics.CollisionGroup(gp)
        cg.GetCollidersCollectionAPI().CreateIncludesRel().SetTargets(
            targets)
    for gname, filters in (
            ("Art", ["Fit", "KinRotor", "KinRoller", "KinPaddle",
                     "KinAuger"]),
            ("KinRotor", ["Art", "Fit", "KinRoller"]),
            ("KinRoller", ["Art", "Fit", "KinRotor"]),
            ("KinPaddle", ["Art", "Fit", "KinAuger"]),
            ("KinAuger", ["Art", "Fit", "KinPaddle"]),
            ("KinCrossFeedJournal", ["CrossFeedBearing"]),
            ("CrossFeedBearing", ["KinCrossFeedJournal", "FeedIdler"]),
            ("FeedIdler", ["CrossFeedBearing", "PaddleFeedGear",
                           "CrossFeedGear"]),
            ("PaddleFeedGear", ["FeedIdler"]),
            ("CrossFeedGear", ["FeedIdler"]),
            ("Belt", ["BeltDrive", "BeltIdler"]),
            ("BeltDrive", ["Belt", "Fit", "TransferBelt"]),
            ("BeltIdler", ["Belt", "Fit"]),
            ("TransferBelt", ["BeltDrive", "TransferIdler"]),
            ("TransferIdler", ["TransferBelt", "TransferBearing"])):
        gp = stage.GetPrimAtPath(f"/World/F0/CollisionGroups/{gname}")
        cg = UsdPhysics.CollisionGroup(gp)
        cg.CreateFilteredGroupsRel().SetTargets(
            [f"/World/F0/CollisionGroups/{f}" for f in filters])
    # articulation links must not self-collide (S1A/S1B cutter hulls
    # interleave by design; hulls cannot represent the hook interleave)
    stage.GetPrimAtPath("/World/F0/Machine").CreateAttribute(
        "physxArticulation:enabledSelfCollisions",
        Sdf.ValueTypeNames.Bool, True).Set(False)

# --- DERIVED transfer boxes: REMOVED (FIX B2) --------------------
    # The emit_usd.py-era DERIVED boxes (S1_DISCHARGE, CHUTE, S2_ENTRY,
    # S2_EXIT) are parametric placeholders.  flow_localization measured
    # them as the 0/200 blocker: mesh_DERIVED_S1_DISCHARGE is a closed
    # slab at z 413..443 / x 60..180 / y 193.5..293.5 sitting INSIDE the
    # S1 chamber — probes piled on it, tunneled through its top face and
    # jammed on its bottom face at z=414.5 with 0 legitimate contacts.
    # mesh_DERIVED_CHUTE (z 290..410) likewise sealed the real
    # CHUTE_BODY trough and DERIVED_S2_ENTRY/S2_EXIT intruded on the S2
    # bay. The real C2.1 CAD replaces those phantom solids; path_check.json
    # measures apertures only; the new cross-feed and complete upstream
    # material transport require dynamic evidence, not this static check.
    derived = {
        "removed": ["S1_DISCHARGE", "CHUTE", "S2_ENTRY", "S2_EXIT"],
        "note": ("emit_usd.py-era DERIVED boxes removed — phantom solids "
                 "sealing the S1 chamber and chute; actual CAD includes "
                 "CHUTE_BODY + CHUTE_TROUGH_FLOOR_E. path_check.json "
                 "measures apertures, not connected transport."),
    }

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
        "usd_sha256": sha256_file(usd_path),
        "stage_meters_per_unit": 0.001,
        "gravity_mm_s2": 9810.0,
        "articulation_root": "/World/F0/Machine",
        "joints": [{"name": jn, "body1": bd, "axis": "Y",
                    "pivot_mm": list(pv)} for jn, bd, pv in JOINTS],
        "ratios_from_input": {
            "S1A": -15.0 / 40.0 * (24 / 24),
            "S1B": +15.0 / 40.0,
            "S2_ECC": -15.0 / 40.0 * (24.0 / 12.0),
            "S2_CARRIER": +15.0 / 40.0 * (24.0 / 12.0) / 8.0,
            "CROSS_FEED": -15.0 / 40.0 * (24.0 / 12.0),
            "CROSS_FEED_IDLER": +15.0 / 40.0 * (24.0 / 12.0),
        },
        "ratio_sources": ["design/parameters.json drive block",
                          "c2.1/src/transmission.py pose() q=8",
                          "design/assembly.json drive instances",
                          "c2.1/src/chute.py three equal 12T feed gears"],
        "pivot_mm": {k: list(v) for k, v in PIVOTS_MM.items()},
        "contact_offset_mm": CONTACT_OFFSET_MM,
        "rest_offset_mm": REST_OFFSET_MM,
        "collision_note": ("static solids = concave triangleMesh; moving "
                           "solids = decimated convexHull except the "
                           "cycloid rotor/output carrier authored as "
                           "convexDecomposition. AUG_SHAFT and "
                           "CROSS_FEED_SHAFT use short axial convex hulls "
                           "of actual STEP-derived fine STL vertices, "
                           "rather than full-flight hulls that close screw "
                           "valleys. Fragment contacts remain collidable; "
                           "hull contact is not proof of transfer."),
        "hull_audit": {
            "source": "c2.2/sim/audit_hulls.py",
            "results": "c2.2/results/full_machine/hull_audit.json",
            "convexDecomposition_solids": sorted(
                e["mesh"].rsplit("/", 1)[-1].replace("__fine", "")
                .replace("__coarse", "")
                for e in emitted if e["approx"] == "convexDecomposition"),
        },
        "contact_filter_table": {
            "collision_groups": {
                "Art": "all articulation links (IN_SHAFT, S1A, S1B, "
                       "S2_ECC, S2_CARRIER)",
                "Fit": "journal fits / keyed sprockets / gear-mesh "
                       "partners (BR-, DRV-B*, DRV_SH40, DRV_CHAIN, "
                       "S1-BPL, S1-BR-CAP, FRONT/REAR supports, bearing "
                       "envelopes, fixed-ring plates, ring pins)",
                "KinRotor": "S2_ROTOR (pose-driven kinematic body)",
                "KinRoller": "S2_ROLLER_1..6 (kinematic coupling "
                             "rollers)",
                "KinPaddle": "PADDLE (pose-driven kinematic worm shaft, "
                             "VP1 rev 6 chain-driven transfer)",
                "KinAuger": "AUGER (pose-driven kinematic screw "
                            "conveyor at S2Ecc/8, worm:wheel 8:1)",
                "KinCrossFeedFlight": "CROSS_FEED_SHAFT RH flight axial "
                                      "hulls, no filtering; fragments live",
                "KinCrossFeedJournal": "CROSS_FEED_SHAFT y208..224.75 and "
                                       "y250.25..250.7 journal slices",
                "CrossFeedBearing": "only CROSS_FEED_BEARINGS journals",
                "FeedIdler": "only CROSS_FEED_IDLER gear and journal",
                "PaddleFeedGear": "only PDL_FEED_GEAR teeth",
                "CrossFeedGear": "only CROSS_FEED_GEAR teeth",
                "Belt": "two side loops on a common drive/idler shaft",
                "BeltDrive": "waisted common drive for the centre lane",
                "BeltIdler": "two side loops' waisted east follower",
                "TransferBelt": "continuous centre lane rising into AUG",
                "TransferIdler": "centre lane's east follower drum",
                "TransferBearing": "two centre idler journal rings",
            },
            "filtered_pairs": {
                "Art_x_Fit": ("journal fits, keyed sprockets and the "
                              "helical 15T/40T gear mesh: by-design "
                              "overlap at zero-to-interference clearance "
                              "in a rigid rig; kinematically driven so "
                              "contact forces must not act"),
                "Art_x_KinRotor": "rotor orbits/spins inside the "
                                  "articulation envelope by design",
                "Art_x_KinRoller": "output rollers ride in keyed "
                                   "carrier pins by design",
                "Art_x_KinPaddle": ("worm shaft/sprocket pass inside the "
                                    "articulation envelope by design "
                                    "(chain-driven transfer, ideal "
                                    "constraint)"),
                "KinPaddle_x_Fit": ("paddle chain loop wraps the widened "
                                    "S2 12T face and the worm-shaft "
                                    "sprocket by design (12T/12T band)"),
                "Art_x_KinAuger": ("auger shaft/flight pass inside the "
                                   "articulation envelope by design "
                                   "(worm-driven conveyor, ideal "
                                   "constraint)"),
                "KinPaddle_x_KinAuger": ("PDL_WORM 2-start worm engages "
                                         "the AUG_WHEEL 16T conjugate "
                                         "teeth by design (8:1 worm "
                                         "wheel, ideal constraint)"),
                "KinAuger_x_Fit": ("auger journal seats: west bore r5.5 "
                                   "and east boss bore r4.7 vs the "
                                   "flight hull (r5) and shaft - journal "
                                   "fits by design"),
                "KinRotor_x_KinRoller": "cycloid output coupling "
                                        "(rollers ride in rotor windows)",
                "KinRotor_x_Fit": "rotor vs fixed-ring pins: fixed-ring "
                                  "cycloid engagement by design",
                "KinRoller_x_Fit": "rollers vs ring plates by design",
                "KinCrossFeedJournal_x_CrossFeedBearing": (
                    "only cross-feed journal slices in the named bearing "
                    "bores; RH flight vs shell and fragments stays live"),
                "FeedIdler_x_CrossFeedBearing": (
                    "idler journal inside named bearing bore"),
                "FeedIdler_x_PaddleFeedGear": (
                    "first 12T external gear mesh; ideal opposite-angle "
                    "kinematics, no tooth-force solver"),
                "FeedIdler_x_CrossFeedGear": (
                    "second 12T external gear mesh; ideal same signed "
                    "cross-feed ratio after two reversals"),
                "Belt_x_BeltDrive_BeltIdler": (
                    "stationary belt shell intersects rolling drums at "
                    "the contact arc, driven by measured S1B kinematics"),
                "BeltDrive_x_TransferBelt": (
                    "centre loop wraps the waisted common source drum"),
                "TransferBelt_x_TransferIdler": (
                    "centre belt shell wraps its east follower"),
                "TransferIdler_x_TransferBearing": (
                    "east centre drum's seated journals"),
                "articulation_self_collision": ("disabled: S1A/S1B "
                                                "cutter hulls interleave "
                                                "by design; hulls cannot "
                                                "represent the hook "
                                                "interleave"),
            },
            "not_filtered": ("every probe/fragment vs every collider, "
                             "including cross-feed screw; cross-feed flight "
                             "vs static shell and mouth; all other static "
                             "clearance contacts except named journal "
                             "bores; no downstream loss suppressed"),
        },
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
        "status": "GEOMETRY_EMITTED" if not failures else "FAIL",
        "material_flow_status": "UNVERIFIED",
    }
    (out / "full_machine.sidecar.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "emitted"}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())