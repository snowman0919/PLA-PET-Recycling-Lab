"""FIX A: material-flow localization for the integrated PPR VP1 machine.

The last integrated run (run_vp1_final) scored 0/200 probes reaching the S2
screen with ZERO contact events — "no fracture model" is NOT an acceptable
explanation.  This runner injects passable fragments SEPARATELY at four
points of the material path and records, per fragment:

  entered          — ever moved > 5 mm from its spawn point
  passed_through   — reached the next stage's acceptance region
  settled_stuck_at — final position + colliding body names (contact stream
                     + settle-time downward raycast / overlap via the PhysX
                     scene-query interface)

Injection points and acceptance regions (all mm, world F0; derived from
bodies.json bboxes and c2.1/results/path_check.json):
  P1 hopper_mouth   spawn inside the hopper funnel (z ~493..498)
                    pass = z < 438.5  (below the hopper, in the S1 chamber)
  P2 s1_discharge   spawn in the S1 chamber bottom free band (z 353..356)
                    pass = z < 352.3 (through the 4.3 mm S1 opening to pan)
                    screw pickup separately requires post-gate arrival in
                    x237..270,y223.3..240.9,z338..356
  P3 chute_inlet    isolated spawn above the U trough near x252..270
                    broad gate = x >= 335; in-trough gate checks y/z at
                    crossing before the x354 east edge; S2 mouth transfer
                    separately requires a +Y crossing of y255 with the
                    full fragment envelope inside the cap bore/outlet lips
  P4 s2_inlet       spawn above the real S2 open arc (x342..348,
                    y266..284,z344..346), not over the screw bearing;
                    broad gate = z < 300, with mouth-column arrival
                    checked separately (x340..360,y255..295)

The drivetrain runs with the exact kinematic stepping of verify_full.py
(ratios enforced, rotor pose-driven) so blockages are judged against the
real moving geometry.  Fragments get CCD (small spheres at up to ~2.2 m/s
would tunnel 4 mm screen holes at dt=5ms) and dt=0.0025.

Usage (one SimulationApp launch per phase, merged by the parent invocation):
  OMNI_KIT_ACCEPT_EULA=YES $HOME/env_isaacsim-c22/bin/python \
    c2.2/sim/flow_localize.py [--steps-per-phase 2400] [--phase N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
SIM = HERE.parent
C22 = SIM.parent
REPO = C22.parent
sys.path.insert(0, str(SIM))

USDA = C22 / "sim" / "assets" / "usd" / "full_machine.usda"
BODIES = C22 / "sim" / "assets" / "out" / "full" / "bodies.json"
USD_MANIFEST = USDA.with_suffix(".sidecar.json")

# single-sourced kinematic pivots (full_machine.py is the origin of truth;
# the stale x262 hardcode caused an invalid-pivot flow run — excluded from
# final evidence)
from full_machine import PIVOTS_MM as _PIVOTS_MM  # noqa: E402
PADDLE_PIVOT = _PIVOTS_MM["PADDLE"]
AUGER_PIVOT = _PIVOTS_MM["AUGER"]
CROSS_FEED_PIVOT = _PIVOTS_MM["CROSS_FEED"]
CROSS_FEED_IDLER_PIVOT = _PIVOTS_MM["CROSS_FEED_IDLER"]
OUTDIR = C22 / "results" / "full_machine" / "flow_localize"

# --- stage definitions ---------------------------------------------------
# Each phase: (name, spawn box (x0,x1, y0,y1, z0,z1), pass predicate name).
PHASES = ["hopper_mouth", "s1_discharge", "chute_inlet", "s2_inlet"]

SPAWN = {
    "hopper_mouth": (83.9, 153.9, 203.5, 283.5, 488.0, 497.0),
    "s1_discharge": (100.0, 220.0, 190.0, 290.0, 353.0, 356.0),
    # Above the flight OD, not embedded in its sweep; isolated downstream
    # injection is NOT evidence for connected S1 feed.
    "chute_inlet": (252.0, 270.0, 226.0, 238.0, 357.5, 359.5),
    # Isolated injection above the open S2 arc; the historical x355..359,
    # y226..238 position intersected the screw journal and was outside
    # the S2 mouth, so its plane crossings were not delivery.
    "s2_inlet": (342.0, 348.0, 266.0, 284.0, 344.0, 346.0),
}

# Flight axial window after VP1 raised-axis reconstruction (mm).
FLIGHT_X0, FLIGHT_X1 = 237.0, 354.0
AUGER_PITCH_MM = 28.5
DEFAULT_CHUTE_CYCLES = 5
# The cap occupies y251..255 outside r65.6. The screw's under-shaft
# outlet floor extends through y258 at z315.8..317.3, between side lips
# x350..359.7. Test the fragment envelope at the actual cap-bore plane,
# not an arbitrary z320 lower bound that rejected valid under-shaft entry.
S2_MOUTH_Y_MM = 255.0
S2_MOUTH_X_MM = (350.0, 359.7)
S2_CAP_INNER_R_MM = 65.6
S2_OUTLET_FLOOR_Z_MM = 317.3

# A screen bounding-box crossing is not a hole passage. The active Ø4
# bores are vertical in world Z; for a sphere, its centre must remain
# inside one bore by its own radius while crossing BOTH curved metal faces.
# At fixed X the actual inner/outer shell heights use sqrt(r²-x²), not
# r*sin(angle), because the same vertical ray intersects both radii.
SCREEN_HOLES = [
    (angle, local_y,
     308.56946468906176 - 63.8 * math.cos(math.radians(angle)),
     299.0 - local_y,
     280.0 - math.sqrt(62.8**2 -
                       (63.8 * math.cos(math.radians(angle)))**2),
     280.0 - math.sqrt(64.8**2 -
                       (63.8 * math.cos(math.radians(angle)))**2))
    for angle in range(228, 313, 7)
    for local_y in (9, 15, 21, 27, 33, 39)
]


def hole_transition(prior, current, radius, candidate):
    """Return (candidate, completed_hole) for one descending physics step.

    The candidate survives only while the sphere's XY path stays within
    the SAME bore. Interpolation handles a step crossing both faces.
    """
    if radius >= 2.0 or current[2] >= prior[2]:
        return None, None
    holes = ([(candidate, SCREEN_HOLES[candidate])]
             if candidate is not None else enumerate(SCREEN_HOLES))
    for idx, (angle, local_y, hx, hy, top, bottom) in holes:
        entry, exit_ = top + radius, bottom - radius
        margin2 = (2.0 - radius - 1e-3) ** 2
        if candidate is None:
            if not (prior[2] >= entry > current[2]):
                continue
            t = (prior[2] - entry) / (prior[2] - current[2])
            ex = prior[0] + t * (current[0] - prior[0])
            ey = prior[1] + t * (current[1] - prior[1])
            if (ex - hx) ** 2 + (ey - hy) ** 2 > margin2:
                continue
        if current[2] <= exit_:
            t = (prior[2] - exit_) / (prior[2] - current[2])
            xx = prior[0] + t * (current[0] - prior[0])
            yy = prior[1] + t * (current[1] - prior[1])
            if (xx - hx) ** 2 + (yy - hy) ** 2 <= margin2:
                return None, (angle, local_y, xx, yy, exit_)
            return None, None
        if (current[0] - hx) ** 2 + (current[1] - hy) ** 2 <= margin2:
            return idx, None
        return None, None
    return candidate, None

# drivetrain ratios per unit input rotation (must match verify_full.py)
Q = 8
GEAR_RATIO = -15.0 / 40.0
CHAIN_A = 24 / 24
S2_CHAIN = 24 / 12
CHAIN_B = GEAR_RATIO * S2_CHAIN   # PPR_VP1: chain B jack-driven, -0.75/input
THETA_TOTAL = 2 * math.pi * Q


def zone_analysis(phase, fragments):
    """Separate chute gate reach, in-trough reach, and subsequent loss.

    A final pose cannot establish where a moving fragment crossed x=335:
    it may leave the machine after a legitimate crossing, or cross the
    x-plane while already falling outside the trough.  in_path_passed is
    recorded at the crossing, independently of the final loss flag.
    """
    if phase != "chute_inlet":
        return {"applies": False, "note": "zone split defined for "
                "chute_inlet only (flight corridor x237..354)"}
    zones = {"upstream_entry": {"x_range": [FLIGHT_X0, 270.0],
                                "note": "isolated spawn band inside the "
                                        "active flight x237..354"},
             "downstream_exit": {"x_range": [354.0, None],
                                 "note": "east fallaway / spill edge "
                                         "(x>=335 predicate may trigger "
                                         "past the flight east edge)"}}
    for z in zones.values():
        z.update({"total": 0, "entered": 0, "passed_through": 0,
                  "true_passed": 0, "reached_s2_mouth": 0,
                  "stuck": 0, "lost_through_world": 0,
                  "lost_after_x335_before_mouth": 0,
                  "crossed_screen": 0})
    for f in fragments:
        sx = f["spawn_mm"][0]
        z = "downstream_exit" if sx > FLIGHT_X1 else "upstream_entry"
        zrec = zones[z]
        zrec["total"] += 1
        for k_src, k_dst in (("entered", "entered"),
                             ("passed_through", "passed_through"),
                             ("reached_s2_mouth", "reached_s2_mouth"),
                             ("stuck", "stuck"),
                             ("lost_through_world", "lost_through_world"),
                             ("lost_after_x335_before_mouth",
                              "lost_after_x335_before_mouth"),
                             ("crossed_screen", "crossed_screen")):
            if f.get(k_src):
                zrec[k_dst] += 1
        if f.get("in_path_passed"):
            zrec["true_passed"] += 1
    for z in zones.values():
        t = z["total"]
        z["pass_rate"] = round(z["passed_through"] / t, 3) if t else None
        z["true_pass_rate"] = (round(z["true_passed"] / t, 3)
                               if t else None)
    return {"applies": True, "pickup_window_x_mm": [FLIGHT_X0, FLIGHT_X1],
            "flight_x_range_mm": [FLIGHT_X0, FLIGHT_X1], "zones": zones,
            "true_pass_note": "in-trough at first x>=335 sample; S2 mouth "
                              "requires a separate +Y entrance-plane "
                              "crossing; final world loss is separate"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one_phase(phase: str, steps: int, dt: float, out_path: Path,
                  cycles: int = 1) -> int:
    """Runs one injection phase in its own Isaac process. Returns exit code."""
    bodies = json.loads(BODIES.read_text())
    solids = bodies["solids"]
    screen = next(r for r in solids
                  if r["name"] == "C2_VERTICAL_DISCHARGE_SCREEN")
    sb = screen["part_bbox"]
    sb_mid = (sb[2] + sb[5]) / 2.0
    hx0, hx1, hy0, hy1, hz0, hz1 = SPAWN[phase]

    log_lines: list[str] = []

    def log(msg: str) -> None:
        print(msg, flush=True)
        log_lines.append(msg)

    from isaacsim import SimulationApp
    sim = SimulationApp({"headless": True,
                         "--/app/viewport/enabled": "false",
                         "--/renderer/active": "disabled",
                         "--/rtx/viewports/enabled": "false"})
    try:
        import numpy as np
        import omni.physx
        import omni.timeline
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, PhysxSchema
        from isaacsim.core.experimental.utils import stage as stage_utils
        from isaacsim.core.simulation_manager import SimulationManager

        log(f"phase={phase} spawn_box={SPAWN[phase]}")
        log(f"STEP_SHA256={bodies['source_step_sha256']}")
        log(f"USDA sha={sha256_file(USDA)}")
        stage_utils.open_stage(str(USDA))
        stage = stage_utils.get_current_stage(backend="usd")
        stage_id = stage_utils.get_stage_id(stage)
        belt_api = PhysxSchema.PhysxSurfaceVelocityAPI.Apply(
            stage.GetPrimAtPath("/World/F0/BELT"))
        belt_velocity = belt_api.CreateSurfaceVelocityAttr()
        belt_velocity.Set(Gf.Vec3f(0.0, 0.0, 0.0))
        belt_api.CreateSurfaceVelocityLocalSpaceAttr().Set(False)
        transfer_api = PhysxSchema.PhysxSurfaceVelocityAPI.Apply(
            stage.GetPrimAtPath("/World/F0/TRANSFER_BELT"))
        transfer_velocity = transfer_api.CreateSurfaceVelocityAttr()
        transfer_velocity.Set(Gf.Vec3f(0.0, 0.0, 0.0))
        transfer_api.CreateSurfaceVelocityLocalSpaceAttr().Set(False)
        log(f"belt surface API: enabled="
            f"{belt_api.GetSurfaceVelocityEnabledAttr().Get()}, "
            f"local={belt_api.GetSurfaceVelocityLocalSpaceAttr().Get()}, "
            f"rigid={stage.GetPrimAtPath('/World/F0/BELT').HasAPI(UsdPhysics.RigidBodyAPI)}")

        # --- fragments: 10 x d3 spheres, 10 x d1.5 spheres, 2 slabs ----
        rng = np.random.default_rng(20260922)
        n_sphere_each = 10
        fr = []
        for i in range(n_sphere_each):
            fr.append(("sphere", 1.5))   # d=3 mm
        for i in range(n_sphere_each):
            fr.append(("sphere", 0.75))  # d=1.5 mm
        fr.append(("slab", (6.0, 6.0, 2.0)))
        fr.append(("slab", (5.0, 4.0, 2.0)))
        n = len(fr)
        sx = rng.uniform(hx0, hx1, n)
        sy = rng.uniform(hy0, hy1, n)
        sz = rng.uniform(hz0, hz1, n)
        paths = [f"/World/Flow/f{i}" for i in range(n)]
        for i, pp in enumerate(paths):
            kind, dim = fr[i]
            if kind == "sphere":
                xp = stage.DefinePrim(pp, "Sphere")
                UsdGeom.Sphere(xp).GetRadiusAttr().Set(float(dim))
            else:
                xp = stage.DefinePrim(pp, "Cube")
                UsdGeom.Cube(xp).GetSizeAttr().Set(1.0)
            UsdPhysics.RigidBodyAPI.Apply(xp)
            if kind == "sphere":
                m = 1e-6 * (4 / 3) * math.pi * float(dim) ** 3
            else:
                m = 1e-6 * dim[0] * dim[1] * dim[2]
            UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(m)
            UsdPhysics.CollisionAPI.Apply(xp)
            rb = PhysxSchema.PhysxRigidBodyAPI.Apply(xp)
            try:
                rb.CreateDisableSleepAttr().Set(True)
            except AttributeError:
                xp.CreateAttribute("physxRigidBody:disableSleep",
                                   Sdf.ValueTypeNames.Bool, True).Set(True)
            try:
                rb.CreateCcdEnabledAttr().Set(True)
            except AttributeError:
                xp.CreateAttribute("physxRigidBody:ccdEnabled",
                                   Sdf.ValueTypeNames.Bool, True).Set(True)
            PhysxSchema.PhysxContactReportAPI.Apply(xp)
            x = UsdGeom.Xformable(xp)
            x.ClearXformOpOrder()
            if kind == "sphere":
                x.AddTranslateOp().Set(Gf.Vec3d(float(sx[i]), float(sy[i]),
                                                float(sz[i])))
            else:
                x.AddTranslateOp().Set(Gf.Vec3d(float(sx[i]), float(sy[i]),
                                                float(sz[i])))
                x.AddOrientOp().Set(Gf.Quatf(1.0, 0.0, 0.0, 0.0))
        log(f"fragments created: {n} (10x d3, 10x d15, 2 slabs)")

        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                try:
                    PhysxSchema.PhysxContactReportAPI.Apply(prim)
                except Exception as exc:
                    log(f"report apply failed {prim.GetPath()}: {exc}")

        SimulationManager.set_physics_sim_device("cpu")
        PhysxSchema.PhysxSceneAPI.Apply(
            stage.GetPrimAtPath("/World/F0/PhysicsScene")
        ).CreateEnableGPUDynamicsAttr().Set(False)
        omni.physx.get_physx_simulation_interface().attach_stage(stage_id)
        SimulationManager.set_physics_dt(dt)
        omni.timeline.get_timeline_interface().play()
        for _ in range(5):
            sim.update()
        log("attached + played")

        import omni.physics.tensors as pt
        sv = pt.create_simulation_view("numpy")
        fv = sv.create_rigid_body_view(paths)

        # kinematic bodies driven exactly like verify_full.py
        roller_offsets = {}
        for s in solids:
            if s["body"].startswith("S2_ROLLER"):
                b = s["part_bbox"]
                roller_offsets[s["body"]] = ((b[0] + b[3]) / 2,
                                             (b[1] + b[4]) / 2,
                                             (b[2] + b[5]) / 2)
        S2_PIVOT = (308.56946468906176, 299.0, 280.0)
        ECC_MM = 7.0
        kin_paths = ["/World/F0/S2_ROTOR"] + [
            f"/World/F0/S2_ROLLER_{k}" for k in range(1, 7)] + \
            ["/World/F0/PADDLE", "/World/F0/AUGER",
             "/World/F0/CROSS_FEED", "/World/F0/CROSS_FEED_IDLER",
             "/World/F0/BELT", "/World/F0/BELT_DRIVE",
             "/World/F0/BELT_IDLER", "/World/F0/SWEEP_SOUTH",
             "/World/F0/SWEEP_NORTH", "/World/F0/TRANSFER_BELT",
             "/World/F0/TRANSFER_IDLER"]
        kv = sv.create_rigid_body_view(kin_paths)
        art_paths = ["/World/F0/IN_SHAFT", "/World/F0/S1A", "/World/F0/S1B",
                     "/World/F0/S2_ECC", "/World/F0/S2_CARRIER"]
        av = sv.create_articulation_view(["/World/F0/Machine"])
        log(f"views: art={av.count}x{av.max_dofs}, kin={kv.count}, "
            f"flow={fv.count}")

        sim_iface = omni.physx.get_physx_simulation_interface()
        from pxr import PhysicsSchemaTools

        # NOTE: the contact-report event stream (subscribe_contact_report_
        # events / get_contact_report) was verified NON-FUNCTIONAL in this
        # Isaac build when physics is stepped via the tensor SimulationView
        # (minimal floor+sphere scene: contact exists — bodies rest — yet
        # zero events on both the callback and the pull APIs, threshold 0).
        # Shape identification therefore uses the PhysX SCENE QUERY
        # interface: raycast_closest returns the hit collider path
        # (verified: {'collision': '/World/F0/Static/mesh_CHUTE_BODY',
        # 'position', 'normal', 'distance'}).  A corrected-signature
        # subscription is still registered and its (zero) count reported
        # for the record.
        contact_events: list[str] = []

        def on_contact(headers, data):
            for h in headers:
                try:
                    a = PhysicsSchemaTools.intToSdfPath(
                        int(h.collider0)).pathString
                    b = PhysicsSchemaTools.intToSdfPath(
                        int(h.collider1)).pathString
                except Exception:
                    continue
                if a.startswith("/World/Flow/") or \
                        b.startswith("/World/Flow/"):
                    contact_events.append(f"{a}|{b}")

        try:
            _sub = sim_iface.subscribe_contact_report_events(on_contact)
        except Exception as exc:
            log(f"contact subscription unavailable: {exc}")
            _sub = None

        # One q=8 input cycle turns the auger 0.75 rev. Five cycles offer
        # 5 * 0.75 * 28.5 = 106.875 mm of ideal travel, enough for
        # x237->335 (98 mm) without the old 130-cycle/60s, 1040-rpm
        # overspeed artifact. At dt=.0025, 24000 steps take 60s and
        # five cycles drive the input at 40rpm (rated 58rpm).
        omega = (cycles * THETA_TOTAL) / (steps * dt)
        log(f"omega={omega:.4f} rad/s; steps={steps}; dt={dt}; "
            f"input cycles={cycles}; auger revs={cycles * 0.75:.2f}; "
            f"ideal axial feed={cycles * 0.75 * AUGER_PITCH_MM:.1f} mm")

        kin_every = 4
        settle_count = [0] * n
        settled_at = [None] * n
        passed = [False] * n
        first_pass_mm = [None] * n
        in_path_passed = [False] * n
        entered = [False] * n
        crossed_screen = [False] * n
        spawn_pos = np.stack([sx, sy, sz], axis=1)
        previous_pos = spawn_pos.copy()
        reached_mouth = [False] * n
        first_mouth_mm = [None] * n
        first_mouth_plane_mm = [None] * n
        reached_auger_pickup = [False] * n
        first_auger_pickup_mm = [None] * n
        screen_candidate = [None] * n
        passed_screen_hole = [False] * n
        first_screen_hole_mm = [None] * n
        entered_buffer_mouth = [False] * n
        reached_buffer_throat = [False] * n
        first_buffer_throat_plane_mm = [None] * n
        theta_prev = 0.0   # measured input angle (unwrapped)
        prev_in = 0.0
        s2ecc_prev = 0.0   # measured S2 eccentric angle (unwrapped)
        prev_ecc = 0.0
        vel_prev = 0.0
        s1b_prev = 0.0
        prev_s1b = 0.0
        s1b_vel_prev = 0.0
        transfer_dx = (_PIVOTS_MM["TRANSFER_IDLER"][0]
                       - _PIVOTS_MM["BELT_DRIVE"][0])
        transfer_dz = (_PIVOTS_MM["TRANSFER_IDLER"][2]
                       - _PIVOTS_MM["BELT_DRIVE"][2])
        transfer_norm = math.hypot(transfer_dx, transfer_dz)
        transfer_vx = 2.0 * 2.3 * transfer_dx / transfer_norm
        transfer_vz = 2.0 * 2.3 * transfer_dz / transfer_norm
        belt_slope = ((_PIVOTS_MM["BELT_IDLER"][2]
                       - _PIVOTS_MM["BELT_DRIVE"][2])
                      / (_PIVOTS_MM["BELT_IDLER"][0]
                         - _PIVOTS_MM["BELT_DRIVE"][0]))

        def passes(phase_name, x, y, z):
            if phase_name == "hopper_mouth":
                return z < 438.5
            if phase_name == "s1_discharge":
                return z < 352.3
            if phase_name == "chute_inlet":
                return x >= 335.0
            if phase_name == "s2_inlet":
                return z < 300.0
            return False
        def in_receiver(phase_name, x, y, z):
            """Geometric receiver at the *first* broad-predicate crossing.

            Hopper/S1 bounds are the chamber and pan; chute bounds are the
            active U trough before its east edge; S2 is the screen-side
            mouth column, not the unsupported fall outside y=255.
            These are strict point-centre regions, not a success criterion
            for the connected B4 run.
            """
            if phase_name == "hopper_mouth":
                return 80.0 <= x <= 240.0 and 162.4 <= y <= 324.6 \
                    and 352.3 <= z <= 438.5
            if phase_name == "s1_discharge":
                return 75.4 <= x <= 225.0 and 163.5 <= y <= 323.5 \
                    and 336.0 <= z <= 352.3
            if phase_name == "chute_inlet":
                return 335.0 <= x <= FLIGHT_X1 and 223.3 <= y <= 240.9 \
                    and 338.6 <= z <= 356.3
            if phase_name == "s2_inlet":
                return 340.0 <= x <= 360.0 and 255.0 <= y <= 295.0 \
                    and 239.63 <= z <= 300.0
            return False
        gate_axis = 0 if phase == "chute_inlet" else 2
        gate_value = {
            "hopper_mouth": 438.5,
            "s1_discharge": 352.3,
            "chute_inlet": 335.0,
            "s2_inlet": 300.0,
        }[phase]

        sqi = None
        try:
            sqi = omni.physx.get_physx_scene_query_interface()
        except Exception as exc:
            log(f"scene query unavailable: {exc}")

        def _ray(origin, direction, dist, exclude_flow=True):
            """Nearest hit along a ray, excluding fragment colliders.
            Uses raycast_all with a callback (hit.collision is the prim
            path string).  Center-origin + self-filter replaces the
            offset-origin approach: a ray starting just below a resting
            fragment begins INSIDE the floor solid and misses its top
            surface (backfaces are not tested)."""
            hits = []

            def _cb(hit):
                try:
                    p = hit.collision
                    p = getattr(p, "pathString", p)
                    if exclude_flow and str(p).startswith("/World/Flow/"):
                        return True
                    hits.append({
                        "path": str(p),
                        "distance_mm": round(float(hit.distance), 2),
                        "position": [round(float(v), 1) for v in
                                     hit.position],
                        "normal": [round(float(v), 2) for v in hit.normal],
                    })
                except Exception:
                    pass
                return True

            try:
                sqi.raycast_all(Gf.Vec3f(float(origin[0]), float(origin[1]),
                                         float(origin[2])),
                                Gf.Vec3f(float(direction[0]),
                                         float(direction[1]),
                                         float(direction[2])),
                                float(dist), _cb)
            except Exception as exc:
                return {"error": repr(exc)[:120]}
            hits.sort(key=lambda h: h["distance_mm"])
            return hits[0] if hits else None

        def touch_probe(x, y, z, r):
            """6-direction raycasts from the fragment centre, self-hits
            filtered; the nearest non-fragment hits are the colliding
            solids (named via bodies.json sidecars)."""
            probe = {
                "down": ((x, y, z), (0, 0, -1), r + 12.0),
                "up": ((x, y, z), (0, 0, 1), r + 6.0),
                "neg_x": ((x, y, z), (-1, 0, 0), r + 4.0),
                "pos_x": ((x, y, z), (1, 0, 0), r + 4.0),
                "neg_y": ((x, y, z), (0, -1, 0), r + 4.0),
                "pos_y": ((x, y, z), (0, 1, 0), r + 4.0),
            }
            out = {}
            for name, (origin, direction, dist) in probe.items():
                h = _ray(origin, direction, dist)
                if h:
                    out[name] = h
            return out

        rows = []
        for step in range(steps):
            theta_cmd = omega * (step + 1) * dt
            # FIX C drive protocol (same as verify_full.py): ONE authored
            # input ramp; dependent targets from the MEASURED input state.
            in_m = float(theta_prev)
            vin_m = float(vel_prev)
            lead = in_m + vin_m * (2.0 / 40.0)
            dep = [GEAR_RATIO * CHAIN_A * lead, -GEAR_RATIO * CHAIN_A * lead,
                   CHAIN_B * lead, -(CHAIN_B * lead) / Q]
            av.set_dof_position_targets(
                np.array([[theta_cmd] + dep], dtype=np.float32).reshape(1, -1),
                np.arange(5, dtype=np.int32))
            # kinematic S2 rotor + rollers: pose derived from the MEASURED
            # S2 angles
            theta_s2 = float(s2ecc_prev)
            a = -theta_s2 / Q  # spin about +Y (world frame)
            qa = (0.0, math.sin(a / 2), 0.0, math.cos(a / 2))
            pos = (S2_PIVOT[0] - ECC_MM * math.cos(theta_s2), S2_PIVOT[1],
                   S2_PIVOT[2] + ECC_MM * math.sin(theta_s2))
            kin = np.zeros((len(kin_paths), 7), dtype=np.float32)
            kin[0, :3] = pos
            kin[0, 3:] = qa
            for k in range(1, 7):
                d = roller_offsets[f"S2_ROLLER_{k}"]
                dx = d[0] - S2_PIVOT[0]
                dz = d[2] - S2_PIVOT[2]
                ca, sa = math.cos(a), math.sin(a)
                kin[k, 0] = S2_PIVOT[0] + ca * dx + sa * dz
                kin[k, 1] = d[1]
                kin[k, 2] = S2_PIVOT[2] - sa * dx + ca * dz
                kin[k, 3:] = qa
            # worm shaft (VP1 rev 6): 1:1 with the measured S2Ecc angle
            # (chain P 12T/12T from the S2 12T sprocket); pivots are
            # single-sourced from full_machine.PIVOTS_MM — the rev-6
            # x262 stale hardcode caused an invalid-pivot flow run
            kin[7, 0] = PADDLE_PIVOT[0]
            kin[7, 1] = PADDLE_PIVOT[1]
            kin[7, 2] = PADDLE_PIVOT[2]
            kin[7, 3:] = (0.0, math.sin(theta_s2 / 2), 0.0,
                          math.cos(theta_s2 / 2))
            # auger conveyor: worm 2-start : wheel 16T = 8:1, same sign ->
            # measured S2Ecc / 8 about +X (RH flight conveys +x)
            theta_auger = theta_s2 / 8.0
            kin[8, 0] = AUGER_PIVOT[0]
            kin[8, 1] = AUGER_PIVOT[1]
            kin[8, 2] = AUGER_PIVOT[2]
            kin[8, 3:] = (math.sin(theta_auger / 2), 0.0, 0.0,
                          math.cos(theta_auger / 2))
            # Two external 12T spur meshes from PDL_SHAFT: cross-feed
            # turns with the measured S2Ecc angle, idler against it.
            # Screw flight remains collidable with fragments and shell.
            kin[9, :3] = CROSS_FEED_PIVOT
            kin[9, 3:] = (0.0, math.sin(theta_s2 / 2), 0.0,
                          math.cos(theta_s2 / 2))
            kin[10, :3] = CROSS_FEED_IDLER_PIVOT
            kin[10, 3:] = (0.0, -math.sin(theta_s2 / 2), 0.0,
                           math.cos(theta_s2 / 2))
            drum_angle = 2.0 * s1b_prev
            kin[11, :3] = _PIVOTS_MM["BELT"]
            kin[11, 3:] = (0.0, 0.0, 0.0, 1.0)
            for idx, body in ((12, "BELT_DRIVE"), (13, "BELT_IDLER")):
                kin[idx, :3] = _PIVOTS_MM[body]
                kin[idx, 3:] = (0.0, math.sin(drum_angle / 2), 0.0,
                               math.cos(drum_angle / 2))
            for idx, body in ((14, "SWEEP_SOUTH"), (15, "SWEEP_NORTH")):
                kin[idx, :3] = _PIVOTS_MM[body]
                kin[idx, 3:] = (0.0, -math.sin(drum_angle / 2), 0.0,
                               math.cos(drum_angle / 2))
            kin[16, :3] = _PIVOTS_MM["TRANSFER_BELT"]
            kin[16, 3:] = (0.0, 0.0, 0.0, 1.0)
            kin[17, :3] = _PIVOTS_MM["TRANSFER_IDLER"]
            kin[17, 3:] = (0.0, math.sin(drum_angle / 2), 0.0,
                           math.cos(drum_angle / 2))
            belt_speed = 2.0 * 3.8 * s1b_vel_prev
            # This stage is authored in millimetres. The isolated flat
            # conveyor probe moved a sphere 3.96 mm in 1 s at a command
            # of 12 stage-units/s (zero command: 0 mm); scaling by 0.001
            # erroneously removed all useful belt traction.
            belt_velocity.Set(Gf.Vec3f(
                belt_speed, 0.0, belt_speed * belt_slope))
            transfer_velocity.Set(Gf.Vec3f(
                transfer_vx * s1b_vel_prev, 0.0,
                transfer_vz * s1b_vel_prev))
            kv.set_kinematic_targets(kin, np.arange(len(kin_paths),
                                                     dtype=np.int32))
            for lp in art_paths:
                sim_iface.wake_up(
                    stage_id, PhysicsSchemaTools.sdfPathToInt(lp))
            sv.step(dt)

            # measured articulation state for the next step's dependent
            # targets (input + S2_ECC unwrapped)
            _p = av.get_dof_positions()
            pos_np = (_p.numpy() if hasattr(_p, "numpy")
                      else np.asarray(_p)).reshape(1, -1)[0]
            _v = av.get_dof_velocities()
            vel_np = (_v.numpy() if hasattr(_v, "numpy")
                      else np.asarray(_v)).reshape(1, -1)[0]
            theta_prev += math.atan2(math.sin(float(pos_np[0]) - prev_in),
                                     math.cos(float(pos_np[0]) - prev_in))
            prev_in = float(pos_np[0])
            s2ecc_prev += math.atan2(math.sin(float(pos_np[3]) - prev_ecc),
                                     math.cos(float(pos_np[3]) - prev_ecc))
            prev_ecc = float(pos_np[3])
            vel_prev = float(vel_np[0])
            s1b_prev += math.atan2(math.sin(float(pos_np[2]) - prev_s1b),
                                   math.cos(float(pos_np[2]) - prev_s1b))
            prev_s1b = float(pos_np[2])
            s1b_vel_prev = float(vel_np[2])

            T = fv.get_transforms()
            P = (T.numpy() if hasattr(T, "numpy")
                 else np.asarray(T)).reshape(-1, 7)
            V = fv.get_velocities()
            VS = (V.numpy() if hasattr(V, "numpy")
                  else np.asarray(V)).reshape(-1, 3)
            if step % 4 == 0:
                for i in range(n):
                    x, y, z = P[i][:3]
                    if not entered[i] and np.linalg.norm(
                            np.array([x, y, z]) - spawn_pos[i]) > 5.0:
                        entered[i] = True
                    sp = np.linalg.norm(VS[i])
                    if sp < 5.0:
                        settle_count[i] += 1
                        if settle_count[i] >= 20 and settled_at[i] is None:
                            settled_at[i] = step + 1
                    else:
                        settle_count[i] = 0
                        settled_at[i] = None
            # Capture the FIRST gate crossing at every physics step.
            # Interpolate to the threshold plane so a fast fragment cannot
            # skip the receiver's shallow z band between samples.
            for i in range(n):
                x, y, z = P[i][:3]
                prior = previous_pos[i]
                if not passed[i] and passes(phase, x, y, z):
                    delta = float(P[i][gate_axis] - prior[gate_axis])
                    t = ((gate_value - float(prior[gate_axis])) / delta
                         if delta else 1.0)
                    t = min(1.0, max(0.0, t))
                    crossing = prior + t * (P[i][:3] - prior)
                    crossing[gate_axis] = gate_value
                    passed[i] = True
                    first_pass_mm[i] = [round(float(v), 1) for v in crossing]
                    in_path_passed[i] = bool(in_receiver(
                        phase, *(float(v) for v in crossing)))
                # The pan gate is not the screw pickup. Record the first
                # later sample inside the upstream flight corridor.
                if (phase == "s1_discharge" and passed[i]
                        and not reached_auger_pickup[i]
                        and 237.0 <= x <= 270.0
                        and 223.3 <= y <= 240.9
                        and 338.0 <= z <= 356.0):
                    reached_auger_pickup[i] = True
                    first_auger_pickup_mm[i] = [
                        round(float(x), 1), round(float(y), 1),
                        round(float(z), 1)]
                # A screen-plane crossing is not screen-hole passage.
                # Evaluate XY at the descending crossing of the exact
                # measured screen bbox, not after a fast fragment overshot.
                if not crossed_screen[i] and prior[2] >= sb_mid > z:
                    t = (sb_mid - float(prior[2])) / (z - float(prior[2]))
                    cx = float(prior[0] + t * (x - prior[0]))
                    cy = float(prior[1] + t * (y - prior[1]))
                    crossed_screen[i] = bool(sb[0] <= cx <= sb[3]
                                             and sb[1] <= cy <= sb[4])
                if (phase == "s2_inlet" and fr[i][0] == "sphere"
                        and not passed_screen_hole[i]):
                    screen_candidate[i], completed = hole_transition(
                        prior, P[i][:3], float(fr[i][1]),
                        screen_candidate[i])
                    if completed is not None:
                        angle, local_y, hx, hy, hz = completed
                        passed_screen_hole[i] = True
                        first_screen_hole_mm[i] = {
                            "angle_deg": angle, "local_y_mm": local_y,
                            "xyz_mm": [round(float(hx), 3),
                                       round(float(hy), 3),
                                       round(float(hz), 3)]}
                if (phase == "s2_inlet" and not entered_buffer_mouth[i]
                        and prior[2] >= 218.0 > z):
                    t = (prior[2] - 218.0) / (prior[2] - z)
                    bx = prior[0] + t * (x - prior[0])
                    by = prior[1] + t * (y - prior[1])
                    radius = float(fr[i][1]) if fr[i][0] == "sphere" else 2.0
                    entered_buffer_mouth[i] = bool(
                        216.57 + radius <= bx <= 400.57 - radius
                        and 254.0 + radius <= by <= 296.0 - radius)
                if (phase == "s2_inlet" and not reached_buffer_throat[i]
                        and prior[2] >= 145.0 > z):
                    t = (prior[2] - 145.0) / (prior[2] - z)
                    bx = prior[0] + t * (x - prior[0])
                    by = prior[1] + t * (y - prior[1])
                    if first_buffer_throat_plane_mm[i] is None:
                        first_buffer_throat_plane_mm[i] = [
                            round(float(bx), 3), round(float(by), 3), 145.0]
                    radius = float(fr[i][1]) if fr[i][0] == "sphere" else 2.0
                    # FEED-BUF's lower loft is offset to world x289,
                    # not the S2 axis x308.57. Check its inner throat.
                    reached_buffer_throat[i] = bool(
                        267.0 + radius <= bx <= 311.0 - radius
                        and 258.0 + radius <= by <= 292.0 - radius)
                # A point inside an S2-looking box is not handoff. Require
                # forward crossing of the near y=255 mouth plane, then
                # interpolate x/z at that instant (no skipped-plane credit).
                if (phase == "chute_inlet" and not reached_mouth[i]
                        and prior[1] < S2_MOUTH_Y_MM <= y):
                    t = ((S2_MOUTH_Y_MM - float(prior[1])) /
                         (float(y) - float(prior[1])))
                    mx = float(prior[0] + t * (x - prior[0]))
                    mz = float(prior[2] + t * (z - prior[2]))
                    if first_mouth_plane_mm[i] is None:
                        first_mouth_plane_mm[i] = [
                            round(mx, 6), S2_MOUTH_Y_MM, round(mz, 6)]
                    radius = (float(fr[i][1]) if fr[i][0] == "sphere"
                              else max(fr[i][1][0], fr[i][1][1]) / 2.0)
                    half_height = (float(fr[i][1]) if fr[i][0] == "sphere"
                                   else fr[i][1][2] / 2.0)
                    if (S2_MOUTH_X_MM[0] + radius <= mx
                            <= S2_MOUTH_X_MM[1] - radius
                            and math.hypot(mx - 308.56946468906176,
                                           mz - 280.0) + radius
                            <= S2_CAP_INNER_R_MM
                            and mz - half_height + 1e-4 >= S2_OUTLET_FLOOR_Z_MM):
                        reached_mouth[i] = True
                        first_mouth_mm[i] = [round(mx, 1), S2_MOUTH_Y_MM,
                                             round(mz, 1)]
            previous_pos[:] = P[:, :3]
            if step % 100 == 0 or step == steps - 1:
                rows.append({
                    "step": step + 1,
                    "pos_mm": [[round(float(v), 1) for v in P[i][:3]]
                               for i in range(n)],
                })

        # --- final classification ------------------------------------
        T = fv.get_transforms()
        P = (T.numpy() if hasattr(T, "numpy")
             else np.asarray(T)).reshape(-1, 7)
        sb_ = sb

        def in_screen_band(x, y, z):
            return (sb_[0] - 5 <= x <= sb_[3] + 5
                    and sb_[1] - 5 <= y <= sb_[4] + 5
                    and sb_[2] - 5 <= z <= sb_[5] + 5)

        # prim path -> (solid name, body): /World/F0/<Body>/mesh_<Name>;
        # matched case-insensitively on the full prim path prefix
        # (bodies.json body tokens are upper case, USD paths use "Static")
        prim_index = []
        for s in solids:
            nm = s["name"].replace("-", "_")
            prim_index.append((f"/world/f0/{s['body'].lower()}/mesh_{nm.lower()}",
                               s["name"], s["body"]))

        def solid_of(prim_path):
            if not prim_path:
                return None, None
            key = prim_path.lower()
            for pp, name, bd in prim_index:
                if key.startswith(pp):
                    return name, bd
            return None, None

        fragments = []
        for i in range(n):
            kind, dim = fr[i]
            r = dim if kind == "sphere" else 2.0
            x, y, z = (float(P[i][0]), float(P[i][1]), float(P[i][2]))
            touches = touch_probe(x, y, z, r)
            touch_paths = sorted({h["path"] for h in touches.values()
                                  if isinstance(h, dict) and h.get("path")})
            touch_solids = [(solid_of(p)[0], solid_of(p)[1])
                            for p in touch_paths]
            lost = z < -50.0 or z > 900.0 or y < -100.0 or y > 800.0 \
                or x < -100.0 or x > 900.0
            destination_reached = {
                "hopper_mouth": passed[i],
                "s1_discharge": reached_auger_pickup[i],
                "chute_inlet": reached_mouth[i],
                "s2_inlet": (passed_screen_hole[i]
                             and entered_buffer_mouth[i]
                             and reached_buffer_throat[i]),
            }[phase]
            # Ground or below the catch pan is process loss, even if still
            # inside the much larger simulation-world bounds.
            lost_from_process = lost or (
                phase == "s1_discharge" and z < 320.0)
            frag = {
                "i": i,
                "kind": kind,
                "size_mm": (dim * 2 if kind == "sphere" else list(dim)),
                "spawn_mm": [round(float(v), 1) for v in spawn_pos[i]],
                "final_mm": [round(x, 1), round(y, 1), round(z, 1)],
                "entered": bool(entered[i]),
                "first_pass_mm": first_pass_mm[i],
                "in_path_passed": bool(in_path_passed[i]),
                "passed_through": bool(passed[i]),
                "settled_stuck_at_step": settled_at[i],
                "stuck": bool(settled_at[i] is not None
                              and not lost_from_process
                              and not destination_reached),
                "lost_through_world": bool(lost),
                "lost_from_process": bool(lost_from_process),
                "unaccepted_residue": bool(passed[i]
                                            and not destination_reached
                                            and not lost_from_process),
                "reached_screen_band": bool(in_screen_band(x, y, z)),
                "crossed_screen": bool(crossed_screen[i]),
                "reached_s2_mouth": bool(reached_mouth[i]),
                "first_s2_mouth_crossing_mm": first_mouth_mm[i],
                "first_s2_mouth_plane_crossing_mm": first_mouth_plane_mm[i],
                "reached_auger_pickup": bool(reached_auger_pickup[i]),
                "first_auger_pickup_mm": first_auger_pickup_mm[i],
                "passed_screen_hole": bool(passed_screen_hole[i]),
                "first_screen_hole_mm": first_screen_hole_mm[i],
                "entered_buffer_mouth": bool(entered_buffer_mouth[i]),
                "reached_buffer_throat": bool(reached_buffer_throat[i]),
                "first_buffer_throat_plane_mm":
                    first_buffer_throat_plane_mm[i],
                "screen_to_buffer": bool(passed_screen_hole[i]
                                         and entered_buffer_mouth[i]
                                         and reached_buffer_throat[i]),
                "missed_buffer_throat": bool(
                    phase == "s2_inlet"
                    and first_buffer_throat_plane_mm[i] is not None
                    and not reached_buffer_throat[i]),
                "lost_after_s2_mouth": bool(lost and reached_mouth[i]),
                "lost_after_x335_before_mouth": bool(
                    phase == "chute_inlet" and lost and passed[i]
                    and not reached_mouth[i]),
                "touch_probe": touches,
                "touching_solids": [
                    {"solid": sname, "body": bd}
                    for sname, bd in touch_solids if sname],
            }
            fragments.append(frag)

        n_passed = sum(passed)
        n_stuck = sum(1 for f in fragments if f["stuck"])
        n_screen = sum(1 for f in fragments if f["reached_screen_band"])
        n_lost = sum(1 for f in fragments if f["lost_through_world"])
        n_crossed = sum(crossed_screen)
        # first blocker per phase: solids touched by stuck fragments
        blocker_tally: dict[str, int] = {}
        for f in fragments:
            if f["stuck"]:
                for t in f["touching_solids"]:
                    key = f"{t['body']}:{t['solid']}"
                    blocker_tally[key] = blocker_tally.get(key, 0) + 1
        result = {
            "schema": "full_machine_flow_localize_phase/2",
            "phase": phase,
            "spawn_box_mm": list(SPAWN[phase]),
            "pass_predicate": {
                "hopper_mouth": "z < 438.5 (below hopper into S1 chamber)",
                "s1_discharge": "z < 352.3 (S1 opening; NOT auger pickup)",
                "chute_inlet": "x >= 335 (downstream flight gate, before x354 edge)",
                "s2_inlet": "z < 300 (drop into S2 bay)",
            }[phase],
            "receiver_predicate": {
                "hopper_mouth": "x80..240,y162.4..324.6,z352.3..438.5",
                "s1_discharge": "x75.4..225,y163.5..323.5,z336..352.3 belt corridor",
                "chute_inlet": "x335..354,y223.3..240.9,z338.6..356.3",
                "s2_inlet": "x340..360,y255..295,z239.63..300",
            }[phase],
            "s2_mouth_transition_predicate": (
                "first +Y crossing of y=255 with full fragment envelope "
                "inside x350..359.7 outlet lips, r<=65.6 cap bore, and "
                "z>=317.3 outlet floor; x335 flight gate alone is not "
                "transfer"),
            "auger_pickup_predicate": (
                "s1_discharge only: after z352.3 gate, ever inside "
                "x237..270,y223.3..240.9,z338..356"),
            "step_sha256": bodies["source_step_sha256"],
            "usda_sha256": sha256_file(USDA),
            "dt_s": dt,
            "steps": steps,
            "input_cycles": cycles,
            "input_rpm": omega * 60.0 / (2.0 * math.pi),
            "ideal_auger_travel_mm": cycles * 0.75 * AUGER_PITCH_MM,
            "measured_s1b_angle_rad": s1b_prev,
            "measured_s1b_velocity_rad_s": s1b_vel_prev,
            "belt_surface_velocity_command_mm_s": 7.6 * s1b_vel_prev,
            "fragments": fragments,
            "summary": {
                "total": n,
                "entered": sum(entered),
                "passed_through": n_passed,
                "in_path_passed": sum(in_path_passed),
                "reached_auger_pickup": sum(reached_auger_pickup),
                "stuck": n_stuck,
                "lost_through_world": n_lost,
                "lost_from_process": sum(
                    f["lost_from_process"] for f in fragments),
                "unaccepted_residue": sum(
                    f["unaccepted_residue"] for f in fragments),
                "reached_s2_mouth": sum(reached_mouth),
                "passed_screen_hole": sum(passed_screen_hole),
                "entered_buffer_mouth": sum(entered_buffer_mouth),
                "reached_buffer_throat": sum(reached_buffer_throat),
                "screen_to_buffer": sum(
                    f["screen_to_buffer"] for f in fragments),
                "missed_buffer_throat": sum(
                    f["missed_buffer_throat"] for f in fragments),
                "lost_after_s2_mouth": sum(
                    f["lost_after_s2_mouth"] for f in fragments),
                "lost_after_x335_before_mouth": sum(
                    f["lost_after_x335_before_mouth"] for f in fragments),
                "crossed_screen": n_crossed,
                "reached_screen_band": n_screen,
                "blocker_solids": blocker_tally,
            },
            "zone_breakdown": (
                zone_analysis(phase, fragments)),
            "contact_report_stream_events": len(contact_events),
            "contact_report_stream_note": ("event stream verified "
                                           "non-functional in this build "
                                           "under SimulationView stepping; "
                                           "final nearby collider shapes "
                                           "identified by scene-query rays, "
                                           "not measured impulse contacts"),
            "trajectory_rows": rows[::max(1, len(rows) // 64)][:64]
            + ([rows[-1]] if rows and rows[-1] not in rows[::max(1, len(rows) // 64)][:64] else []),
            "runner": "c2.2/sim/flow_localize.py",
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2) + "\n")
        log(f"RESULT {out_path} passed={n_passed}/{n} stuck={n_stuck} "
            f"screen={n_screen} blockers={blocker_tally}")
        return 0
    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        log_lines.append("EXCEPTION:\n" + tb)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(
            {"schema": "full_machine_flow_localize_phase/2",
             "phase": phase, "error": "\n".join(log_lines[-40:])},
            indent=2) + "\n")
        return 2
    finally:
        sim.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default=None,
                    help="run a single phase (default: all, merged)")
    ap.add_argument("--steps-per-phase", type=int, default=2400)
    ap.add_argument("--dt", type=float, default=0.0025)
    ap.add_argument("--cycles", type=int, default=DEFAULT_CHUTE_CYCLES,
                    help="q=8 input cycles for chute/S1 phases (default 5; "
                         "40rpm over the default 60s chute run)")
    ap.add_argument("--merge-only", action="store_true",
                    help="merge existing phase_*.json results without "
                         "running phases")
    ap.add_argument("--chute-steps", type=int, default=24000,
                    help="chute phase steps (default 24000 at dt=.0025)")
    ap.add_argument("--s1-steps", type=int, default=24000,
                    help="S1 discharge steps (default 24000 at dt=.0025)")
    args = ap.parse_args()
    out_root = OUTDIR
    run_phases = not args.merge_only
    if args.phase is not None:
        p = out_root / f"phase_{args.phase}.json"
        cyc = args.cycles if args.phase in ("chute_inlet", "s1_discharge") else 1
        steps_ph = (args.chute_steps if args.phase == "chute_inlet"
                    else args.s1_steps if args.phase == "s1_discharge"
                    else args.steps_per_phase)
        rc = run_one_phase(args.phase, steps_ph, args.dt, p, cycles=cyc)
        return rc
    # parent mode: spawn one child per phase, then merge
    out_root.mkdir(parents=True, exist_ok=True)
    child_codes = {}
    for ph in (PHASES if run_phases else []):
        t0 = time.time()
        # Chute and S1 pickup need sustained rotation; the chute default
        # spans 60 s and five cycles at 40 rpm, near the 58 rpm reference.
        cyc = args.cycles if ph in ("chute_inlet", "s1_discharge") else 1
        steps_ph = (args.chute_steps if ph == "chute_inlet"
                    else args.s1_steps if ph == "s1_discharge"
                    else args.steps_per_phase)
        child_args = [sys.executable, str(Path(__file__).resolve()),
                      "--phase", ph, "--steps-per-phase", str(steps_ph),
                      "--dt", str(args.dt), "--cycles", str(cyc)]
        if ph == "chute_inlet":
            child_args.extend(["--chute-steps", str(steps_ph)])
        if ph == "s1_discharge":
            child_args.extend(["--s1-steps", str(steps_ph)])
        r = subprocess.run(child_args,
            capture_output=True, text=True,
            env={**os.environ, "OMNI_KIT_ACCEPT_EULA": "YES"})
        child_codes[ph] = r.returncode
        (out_root / f"phase_{ph}_runner_log.txt").write_text(r.stdout)
        print(f"phase {ph}: rc={r.returncode} "
              f"({time.time() - t0:.0f}s)", flush=True)

    phases = {}
    for ph in PHASES:
        p = out_root / f"phase_{ph}.json"
        if p.is_file():
            phases[ph] = json.loads(p.read_text())
    step_shas = {r.get("step_sha256") for r in phases.values()}
    usd_shas = {r.get("usda_sha256") for r in phases.values()}
    current_step_sha = (json.loads(BODIES.read_text())["source_step_sha256"]
                        if BODIES.is_file() else None)
    current_usda_sha = sha256_file(USDA) if USDA.is_file() else None
    try:
        scene_manifest = json.loads(USD_MANIFEST.read_text())
    except (OSError, ValueError):
        scene_manifest = {}
    usd_source_linked = bool(
        scene_manifest.get("source_bodies", {}).get("step_sha256") ==
        current_step_sha and scene_manifest.get("usd_sha256") ==
        current_usda_sha and current_step_sha is not None
        and current_usda_sha is not None)
    # Merge-only must not launder an old set of phase artifacts as current.
    # Every phase must have been run on exactly the STEP and USD now selected.
    scene_consistent = (set(phases) == set(PHASES)
                        and all(r.get("schema") ==
                                "full_machine_flow_localize_phase/2"
                                for r in phases.values())
                        and step_shas == {current_step_sha}
                        and usd_shas == {current_usda_sha}
                        and usd_source_linked
                        and all(code == 0 for code in child_codes.values()))

    # Broad plane crossing, receiver reach, and final escape are distinct.
    # Older phase artifacts lack crossing coordinates: do not infer reach
    # from a final pose or present their broad plane count as a CLEAR path.
    verdicts = {}
    for ph, res in phases.items():
        s = res.get("summary", {})
        total = s.get("total", 0)
        broad = s.get("passed_through", 0)
        in_path = s.get("in_path_passed")
        lost = s.get("lost_through_world", 0)
        process_loss = s.get("lost_from_process")
        residue = s.get("unaccepted_residue")
        top = sorted((s.get("blocker_solids") or {}).items(),
                     key=lambda kv: -kv[1])
        verdicts[ph] = {
            "pass_rate": round(broad / total, 3) if total else None,
            "in_path_passed": in_path,
            "in_path_pass_rate": (round(in_path / total, 3)
                                  if total and in_path is not None else None),
            "stuck": s.get("stuck", 0),
            "crossed_screen": s.get("crossed_screen"),
            "passed_screen_hole": s.get("passed_screen_hole"),
            "entered_buffer_mouth": s.get("entered_buffer_mouth"),
            "reached_buffer_throat": s.get("reached_buffer_throat"),
            "screen_to_buffer": s.get("screen_to_buffer"),
            "missed_buffer_throat": s.get("missed_buffer_throat", 0),
            "reached_s2_mouth": s.get("reached_s2_mouth"),
            "reached_auger_pickup": s.get("reached_auger_pickup"),
            "lost_through_world": lost,
            "lost_from_process": process_loss,
            "unaccepted_residue": residue,
            "lost_after_s2_mouth": s.get("lost_after_s2_mouth"),
            "lost_after_x335_before_mouth": s.get(
                "lost_after_x335_before_mouth"),
            "scope": "local receiver crossing; S1 discharge separately "
                     "requires main-screw pickup, chute separately "
                     "requires +Y S2 mouth crossing. The S2 phase reports "
                     "same-bore Ø4 sphere passage, buffer-mouth entry, "
                     "lower-throat crossing or miss and world escape "
                     "separately; no local phase proves connected product "
                     "flow or filament output",
            "verdict": (
                "UNVERIFIED" if not scene_consistent or in_path is None
                or process_loss is None or residue is None or not total
                or (ph == "chute_inlet" and
                    s.get("reached_s2_mouth") is None)
                or (ph == "s1_discharge" and
                    s.get("reached_auger_pickup") is None)
                or (ph == "s2_inlet" and
                    s.get("screen_to_buffer") is None)
                else "CLEAR" if in_path == total and not process_loss
                and not residue and s.get("stuck", 0) == 0
                and (ph != "chute_inlet" or
                     s["reached_s2_mouth"] == total)
                and (ph != "s1_discharge" or
                     s["reached_auger_pickup"] == total)
                and (ph != "s2_inlet" or
                     s["screen_to_buffer"] == total)
                else "BLOCKED"),
            "top_blocker_solids": [k for k, _ in top[:5]],
        }

    # first-solid analysis across phases
    all_blockers: dict[str, int] = {}
    for ph, res in phases.items():
        for bd, c in (res.get("summary", {}).get("blocker_solids", {})
                      or {}).items():
            all_blockers[f"{ph}:{bd}"] = c
    merged = {
        "schema": "full_machine_flow_localize/2",
        "step_sha256": current_step_sha if scene_consistent else None,
        "usda_sha256": current_usda_sha if scene_consistent else None,
        "scene_consistent": scene_consistent,
        "usd_source_linked": usd_source_linked,
        "current_step_sha256": current_step_sha,
        "current_usda_sha256": current_usda_sha,
        "generated_by": "c2.2/sim/flow_localize.py",
        "child_exit_codes": child_codes,
        "verdicts": verdicts,
        "phases": {ph: {
            "spawn_box_mm": r.get("spawn_box_mm"),
            "pass_predicate": r.get("pass_predicate"),
            "receiver_predicate": r.get("receiver_predicate"),
            "auger_pickup_predicate": r.get("auger_pickup_predicate"),
            "s2_mouth_transition_predicate": r.get(
                "s2_mouth_transition_predicate"),
            "input_rpm": r.get("input_rpm"),
            "summary": r.get("summary"),
            "zone_breakdown": r.get("zone_breakdown"),
            "stuck_fragments": [f for f in r.get("fragments", [])
                                if f.get("stuck")][:10],
        } for ph, r in phases.items()},
        "blockers_across_phases": all_blockers,
    }
    (out_root / "results.json").write_text(json.dumps(merged, indent=2) + "\n")
    print(json.dumps({ph: r.get("summary") for ph, r in phases.items()},
                     indent=2))
    return 0 if scene_consistent else 1


if __name__ == "__main__":
    raise SystemExit(main())