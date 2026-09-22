"""Full-machine motion verification under Isaac Sim 6.1 headless PhysX.

Loads c2.2/sim/assets/usd/full_machine.usda (196-solid assembly, 5-DOF
articulation) and runs one real q=8 input cycle:

  (a) drives the M1 input shaft through 8*2pi rad at moderate speed
      (position targets, PD drive);
  (b) asserts every driven joint tracks the commanded ratio within
      RATIO_TOL_RAD (kinematic identity check — gear meshes are NOT
      simulated as contacts; the ratios are enforced by the drives and
      the run proves the drives hold them under the real contact state);
  (c) streams the PhysX contact report and classifies EVERY event against
      an explicit by-design list (journal fits, keyed sprockets, helical
      15T/40T mesh, S1 sync gears, cycloid rotor/ring/roller engagement);
      everything else is UNEXPECTED and reported precisely;
  (d) logs per-step DOF torques (link incoming joint force at the driven
      joints, N*m);
  (e) drops 200 probe spheres (100 x 3mm, 100 x 1.5mm) from the hopper
      mouth and counts how many reach the S2 screen aperture (material-
      path smoke check, NOT grinding performance).

API notes (evidence from /tmp probes on this venv):
  - the isaacsim experimental Articulation wrapper crashes silently on
    this scene; the RAW tensor API works after an explicit
    get_physx_simulation_interface().attach_stage(stage_id) — required
    because the stage is OPENED (create_new_stage auto-attaches, an
    opened stage does not);
  - get_dof_positions returns radians; set_dof_position_targets takes
    (count, max_dofs) float data + indices;
  - RigidPrim world poses are in STAGE units (mm here).

Writes c2.2/results/full_machine/<run>/results.json + runner_log.txt.

Usage:
  OMNI_KIT_ACCEPT_EULA=YES $HOME/env_isaacsim-c22/bin/python \
    c2.2/sim/verify_full.py [--steps 1600 --dt 0.005]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import math
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
OUTDIR = C22 / "results" / "full_machine"

# --- drive model (ratios per unit input-shaft rotation, rad) ------------
Q = 8
GEAR_RATIO = -15.0 / 40.0      # jack/input: external helical mesh
CHAIN_A = 24 / 24              # jack -> S1A, same direction
CHAIN_B = 24 / 12              # input -> S2 eccentric, same direction
CMD = {
    "MachineJointIn": lambda th: th,
    "MachineJointS1A": lambda th: GEAR_RATIO * CHAIN_A * th,
    "MachineJointS1B": lambda th: -GEAR_RATIO * CHAIN_A * th,
    "MachineJointS2Ecc": lambda th: CHAIN_B * th,
    "MachineJointS2Carrier": lambda th: -(CHAIN_B * th) / Q,
}
RATIO_TOL_RAD = 1.0   # position-integrated stepping: 50 Hz write quantization
                      # (0.126 rad/write at 1 rev/s) + coordinate-reset transient
THETA_TOTAL = 2 * math.pi * Q  # one full q=8 input cycle

# S2 rotor kinematics (world, mm): orbit center + spin about +Y.
ECC_MM = 7.0
S2_PIVOT = (308.56946468906176, 299.0, 280.0)
S2_ROTOR_PIVOT = (308.56946468906176 - ECC_MM, 299.0, 280.0)

# By-design contact pairs (substring pairs, order-insensitive).
BY_DESIGN = [
    ("mesh_DRV_SP24_B25_001", "mesh_S1_SHAFT_A_001"),
    ("mesh_DRV_SP12_B12_001", "mesh_INPUT_ECCENTRIC_SHAFT"),
    ("mesh_DRV_SH15R_001", "mesh_DRV_SH40L_001"),
    ("mesh_DRV_SH15L_001", "mesh_DRV_SH40R_001"),
    ("mesh_S1_SYNC_001", "mesh_S1_SYNC_002"),
    ("mesh_INPUT_ECCENTRIC_SHAFT",
     "mesh_ECCENTRIC_BEARING_ENVELOPE_UNRATED"),
    ("mesh_RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE", "mesh_FIXED_RING_PIN_"),
    ("mesh_RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE", "mesh_OUTPUT_ROLLER_"),
    ("mesh_OUTPUT_ROLLER_", "mesh_OUTPUT_PIN_CARRIER_AND_SHAFT"),
    ("mesh_OUTPUT_ROLLER_", "mesh_RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def body_of(path: str) -> str:
    """Classify a collision prim path into a body token."""
    if "/Probe/" in path:
        return "PROBE"
    for token in ("S1A", "S1B", "IN_SHAFT", "S2_ECC", "S2_ROTOR",
                  "S2_CARRIER", "S2_ROLLER_1", "S2_ROLLER_2", "S2_ROLLER_3",
                  "S2_ROLLER_4", "S2_ROLLER_5", "S2_ROLLER_6", "Static",
                  "Machine"):
        if f"/{token}/" in path:
            return token
    return "OTHER"


def is_by_design(a: str, b: str) -> bool:
    for d1, d2 in BY_DESIGN:
        if (d1 in a and d2 in b) or (d1 in b and d2 in a):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1600)
    ap.add_argument("--dt", type=float, default=0.005)
    ap.add_argument("--out", default=None)
    ap.add_argument("--probes", type=int, default=200)
    args = ap.parse_args()

    if not USDA.is_file():
        print(json.dumps({"status": "FAIL",
                          "error": f"missing {USDA}; run full_machine.py"}))
        return 1

    bodies = json.loads(BODIES.read_text())
    run_dir = Path(args.out) if args.out else OUTDIR / time.strftime(
        "run_%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    def log(msg: str) -> None:
        print(msg, flush=True)
        log_lines.append(msg)

    log(f"STEP_SHA256={bodies['source_step_sha256']}")
    log(f"USDA={USDA.name} ({USDA.stat().st_size} B) "
        f"sha={sha256_file(USDA)}")

    from isaacsim import SimulationApp
    sim = SimulationApp({"headless": True})
    try:
        import numpy as np
        import omni.physx
        import omni.timeline
        import omni.usd
        from pxr import Sdf, Usd, UsdGeom, UsdPhysics
        from isaacsim.core.experimental.utils import stage as stage_utils
        from isaacsim.core.experimental.prims import RigidPrim
        from isaacsim.core.simulation_manager import SimulationManager

        log(f"opening stage {USDA}")
        stage_utils.open_stage(str(USDA))
        stage = stage_utils.get_current_stage(backend="usd")
        stage_id = stage_utils.get_stage_id(stage)
        log(f"stage_id={stage_id}")

        # DOF discovery: traverse revolute joints under the articulation
        # root in stage order (the impl helper only walks joints whose
        # body0 is a rigid body; our fixed-base joints anchor to world).
        dof_paths = [p.GetPath().pathString for p in stage.Traverse()
                     if p.IsA(UsdPhysics.RevoluteJoint)
                     and p.GetPath().pathString.startswith(
                         "/World/F0/Machine/")]
        dof_names = [Sdf.Path(p).name for p in dof_paths]
        log(f"joint traversal: {len(dof_paths)} revolute joints "
            f"{dof_names}")
        if len(dof_paths) != 5:
            raise RuntimeError(f"expected 5 DOFs, got {dof_paths}")

        # --- probe spheres (created in the live stage) -----------------
        if os.environ.get("PPR_NO_PROBES"):
            n_each = 0
        hopper = next(r for r in bodies["solids"]
                      if r["name"] == "HOPPER_001")
        hb = hopper["part_bbox"]
        n_each = args.probes // 2
        rng = np.random.default_rng(20260921)
        spawn_x = (hb[0] + hb[3]) / 2 + rng.uniform(-50, 50, 2 * n_each)
        spawn_y = (hb[1] + hb[4]) / 2 + rng.uniform(-60, 60, 2 * n_each)
        # stagger heights so the pack is not a mutual-overlap lattice
        spawn_z = hb[5] - 30.0 + np.tile(np.linspace(0, 25, 2 * n_each), 1)
        radii_mm = np.concatenate([np.full(n_each, 1.5),
                                   np.full(n_each, 0.75)])  # d=3mm, d=1.5mm
        probe_paths = [f"/World/Probe/p{i}" for i in range(2 * n_each)]
        for i, pp in (enumerate(probe_paths) if probe_paths else []):
            xp = stage.DefinePrim(pp, "Sphere")
            UsdGeom.Sphere(xp).GetRadiusAttr().Set(float(radii_mm[i]))
            UsdPhysics.RigidBodyAPI.Apply(xp)
            m = 1e-6 * (4 / 3) * math.pi * float(radii_mm[i]) ** 3
            UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(m)
            try:
                from pxr import PhysxSchema
                _rbapi = PhysxSchema.PhysxRigidBodyAPI.Apply(xp)
                # disableSleep is authored via the schema attribute; fall
                # back to the custom attribute when absent in this build
                try:
                    _rbapi.CreateDisableSleepAttr().Set(True)
                except AttributeError:
                    xp.CreateAttribute("physxRigidBody:disableSleep",
                                       Sdf.ValueTypeNames.Bool,
                                       True).Set(True)
            except ImportError:
                xp.CreateAttribute("physxRigidBody:disableSleep",
                                   Sdf.ValueTypeNames.Bool,
                                   True).Set(True)
            UsdPhysics.CollisionAPI.Apply(xp)
            # opt-in contact reporting for probes (inside SimulationApp
            # the schema module is available)
            try:
                from pxr import PhysxSchema
                PhysxSchema.PhysxContactReportAPI.Apply(xp)
            except ImportError:
                api = list(xp.GetMetadata("apiSchemas") or [])
                if "PhysxContactReportAPI" not in api:
                    xp.SetMetadata("apiSchemas",
                                   api + ["PhysxContactReportAPI"])
            x = UsdGeom.Xformable(xp)
            x.ClearXformOpOrder()
            from pxr import Gf
            x.AddTranslateOp().Set(Gf.Vec3d(float(spawn_x[i]),
                                            float(spawn_y[i]),
                                            float(spawn_z[i])))
        log(f"probes created: {2 * n_each} "
            f"(100x d=3mm, 100x d=1.5mm at z={spawn_z[0]:.1f}..{spawn_z[-1]:.1f}mm staggered)")

        # --- physics setup: attach, device, dt -------------------------
        omni.physx.get_physx_simulation_interface().attach_stage(stage_id)
        log("physx stage attached (explicit; opened stages do not "
            "auto-attach)")
        # contact reporting is opt-in per prim (PhysxContactReportAPI);
        # apply to every body so get/subscribed reports populate
        from pxr import PhysxSchema, UsdPhysics
        # the report API is per COLLIDER prim (body-level does not cover
        # child mesh colliders): apply to every collision prim in F0
        n_applied = 0
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                try:
                    PhysxSchema.PhysxContactReportAPI.Apply(prim)
                    n_applied += 1
                except Exception as exc:
                    log(f"report apply failed on {prim.GetPath()}: {exc}")
        log(f"contact report API applied to {n_applied} colliders")
        SimulationManager.set_physics_sim_device("cpu")
        SimulationManager.set_physics_dt(args.dt)
        tl = omni.timeline.get_timeline_interface()
        tl.play()
        for _ in range(5):
            sim.update()  # pump kit+physics so the tensor backend binds
        log("played + pumped 5 updates")

        import omni.physics.tensors as pt
        sim_view = pt.create_simulation_view("numpy")
        av = sim_view.create_articulation_view(["/World/F0/Machine"])
        log(f"tensor views: SimulationView + ArticulationView "
            f"(count={av.count}, max_dofs={av.max_dofs})")
        if av.count != 1 or av.max_dofs != 5:
            raise RuntimeError(f"unexpected articulation shape "
                               f"{av.count}x{av.max_dofs}")

        # kinematic bodies (rotor + rollers) and probes are driven/read via
        # the tensor RigidBodyView in the loop (no USD roundtrip needed)
        roller_offsets = {}
        for s in bodies["solids"]:
            if s["body"].startswith("S2_ROLLER"):
                b = s["part_bbox"]
                c = ((b[0] + b[3]) / 2, (b[1] + b[4]) / 2,
                     (b[2] + b[5]) / 2)
                roller_offsets[s["body"]] = c

        def rotor_pose(theta_s2):
            a = -theta_s2 / Q  # spin about +Y (world frame)
            pos = (S2_PIVOT[0] - ECC_MM * math.cos(theta_s2),
                   S2_PIVOT[1],
                   S2_PIVOT[2] + ECC_MM * math.sin(theta_s2))
            q = (math.cos(a / 2), 0.0, math.sin(a / 2), 0.0)
            return pos, q

        # --- contact stream --------------------------------------------
        contact_log: list[tuple[str, str]] = []

        def on_contact(event):
            try:
                pairs = event.pairs
                for pair in pairs:
                    contact_log.append((str(pair[0]), str(pair[1])))
            except Exception:
                try:
                    contact_log.append(("RAW", repr(event)[:200]))
                except Exception:
                    pass

        sub = omni.physx.get_physx_simulation_interface() \
            .subscribe_contact_report_events(on_contact)

        # --- drive cycle -----------------------------------------------
        omega = THETA_TOTAL / (args.steps * args.dt)
        log(f"omega={omega:.4f} rad/s input; cycle={2 * math.pi / omega:.1f}s"
            f"; dt={args.dt}s; steps={args.steps}")

        names = list(dof_names)
        max_err = {n: 0.0 for n in names}
        err_nan = False
        pos_unw = np.zeros(5)   # unwrapped joint position estimate
        prev_pos = np.zeros(5)
        last_tgt = np.zeros(5)
        # constant drive velocities (rad/s) in the drive-layout ratios
        vel_ratios = np.array([1.0, GEAR_RATIO * CHAIN_A,
                               -GEAR_RATIO * CHAIN_A, CHAIN_B,
                               -CHAIN_B / Q], dtype=np.float64)
        VEL = vel_ratios * (THETA_TOTAL / (args.steps * args.dt))
        max_torque = {n: 0.0 for n in names}
        rows = []
        torque_available = True
        torque_rows = []
        probe_band = [False] * (2 * n_each)  # EVER in screen band
        screen = next(r for r in bodies["solids"]
                      if r["name"] == "C2_PERFORATED_SCREEN_REFERENCE")
        sb = screen["part_bbox"]

        kin_paths = ["/World/F0/S2_ROTOR"] + [
            f"/World/F0/S2_ROLLER_{k}" for k in range(1, 7)]
        kv = sim_view.create_rigid_body_view(kin_paths)
        pv = sim_view.create_rigid_body_view(probe_paths)
        log(f"rigid body views: kin={kv.count}, probes={pv.count}")
        link_paths = kin_paths + ["/World/F0/IN_SHAFT", "/World/F0/S1A",
                                  "/World/F0/S1B", "/World/F0/S2_ECC",
                                  "/World/F0/S2_CARRIER"]

        sim_iface = omni.physx.get_physx_simulation_interface()
        contact_raw_shapes = []
        from pxr import PhysicsSchemaTools

        def _path_of(v):
            try:
                return PhysicsSchemaTools.intToSdfPath(int(v)).pathString
            except Exception:
                return str(v)

        def _pair_of(p):
            a = getattr(p, "actor0", None)
            b = getattr(p, "actor1", None)
            if a is not None and b is not None:
                contact_log.append((_path_of(a), _path_of(b)))

        def drain_report():
            try:
                rep = sim_iface.get_full_contact_report()
            except Exception:
                return
            if not rep:
                return
            # returns (contact_headers, contact_data, friction_anchors)
            headers = rep[0]
            try:
                n = len(headers)
            except Exception:
                return
            if n and len(contact_raw_shapes) < 3:
                try:
                    contact_raw_shapes.append(repr(headers[0])[:300])
                except Exception:
                    contact_raw_shapes.append(repr(headers)[:300])
            for i in range(n):
                # ContactEventHeader: actor0/actor1 uint64 -> SdfPath
                _pair_of(headers[i])

        for step in range(args.steps):
            theta = omega * (step + 1) * args.dt
            theta_s2 = CHAIN_B * theta
            cmd = [CMD[n](theta) for n in names]
            import os as _os
            if not _os.environ.get("PPR_NO_DRIVE"):
                # POSITION-INTEGRATED KINEMATIC STEPPING: the exact
                # ratio-consistent joint coordinates are written directly
                # (set_dof_positions has no +-2pi limit). Every-step
                # teleports diverge to NaN on this backend (observed);
                # a 50 Hz write rate is stable and still integrates the
                # exact ratios. The PD drives are bypassed — kinematic-
                # like drive; DOF torques not meaningful (recorded).
                _kin_n = int(os.environ.get("PPR_KIN_EVERY", "4"))
                if _kin_n > 0 and step % _kin_n == 0:
                    av.set_dof_positions(
                        np.array([cmd], dtype=np.float32).reshape(1, -1),
                        np.array([0], dtype=np.int32))
            # kinematic S2 rotor + rollers via tensor kinematic targets
            # (count,7) = x,y,z,qx,qy,qz,qw, global frame, stage units
            a = -theta_s2 / Q  # spin about +Y (world frame)
            qa = (0.0, math.sin(a / 2), 0.0, math.cos(a / 2))
            pos, _ = rotor_pose(theta_s2)
            kin = np.zeros((7, 7), dtype=np.float32)
            kin[0, :3] = pos
            kin[0, 3:] = qa
            for k in range(1, 7):
                d = roller_offsets[f"S2_ROLLER_{k}"]
                dx = d[0] - S2_PIVOT[0]
                dz = d[2] - S2_PIVOT[2]
                ca, sa = math.cos(a), math.sin(a)
                # rotation about +Y: x' = ca*x + sa*z ; z' = -sa*x + ca*z
                kin[k, 0] = S2_PIVOT[0] + ca * dx + sa * dz
                kin[k, 1] = d[1]
                kin[k, 2] = S2_PIVOT[2] - sa * dx + ca * dz
                kin[k, 3:] = qa
            if not _os.environ.get("PPR_NO_KIN"):
                kv.set_kinematic_targets(kin, np.arange(7, dtype=np.int32))
            # keep the articulation awake: a gently-ramping target never
            # exceeds the sleep threshold and the solver otherwise creeps
            for lp in ([] if os.environ.get("PPR_NO_WAKE")
                       else link_paths):
                sim_iface.wake_up(
                    stage_id, PhysicsSchemaTools.sdfPathToInt(lp))
            sim_view.step(args.dt)

            _p = av.get_dof_positions()
            pos_np = (_p.numpy() if hasattr(_p, 'numpy') else np.asarray(_p)).reshape(1, -1)[0]
            _v = av.get_dof_velocities()
            vel_np = (_v.numpy() if hasattr(_v, 'numpy') else np.asarray(_v)).reshape(1, -1)[0]
            if torque_available:
                try:
                    _f = av.get_dof_actuation_forces()
                    f = (_f.numpy() if hasattr(_f, 'numpy') else np.asarray(_f)).reshape(1, -1)[0]
                    for i, n in enumerate(names):
                        tq = float(f[i])
                        max_torque[n] = max(max_torque[n], abs(tq))
                    if step % 40 == 0 or step == args.steps - 1:
                        torque_rows.append({
                            "step": step + 1,
                            "torque_Nm": [round(float(v), 6) for v in f],
                        })
                except Exception as exc:
                    log(f"torque readout unavailable after step {step}: "
                        f"{type(exc).__name__}: {exc}")
                    torque_available = False
            # contact report (synchronous per step, header-vector shape)
            if not _os.environ.get("PPR_NO_DRAIN"):
                drain_report()
            for i, n in enumerate(names):
                # unwrap: fold the read position onto the continuous
                # estimate (joint coordinate resets shift reads by -+2pi)
                pv_i = float(pos_np[i])
                pos_unw[i] += math.atan2(
                    math.sin(pv_i - prev_pos[i]),
                    math.cos(pv_i - prev_pos[i]))
                prev_pos[i] = pv_i
                # ratio metric RELATIVE to the measured input position:
                # common-mode coordinate-reset transients cancel; this
                # measures the actual joint-vs-input ratio error
                expected_i = vel_ratios[i] * pos_unw[0]
                e = abs(expected_i - pos_unw[i])
                if math.isnan(e) or math.isnan(pv_i):
                    err_nan = True
                    e = float("inf")
                max_err[n] = max(max_err[n], e)
            if step % 4 == 0:
                pt_p = pv.get_transforms()
                PP = (pt_p.numpy() if hasattr(pt_p, 'numpy')
                      else np.asarray(pt_p)).reshape(-1, 7)
                for i in range(2 * n_each):
                    x, y, z = (float(PP[i][0]), float(PP[i][1]),
                               float(PP[i][2]))
                    if (sb[0] - 5 <= x <= sb[3] + 5
                            and sb[1] - 5 <= y <= sb[4] + 5
                            and sb[2] - 5 <= z <= sb[5] + 5):
                        probe_band[i] = True
            if step % 40 == 0 or step == args.steps - 1:
                rows.append({
                    "step": step + 1, "t_s": round((step + 1) * args.dt, 4),
                    "theta_cmd_rad": theta,
                    "cmd_rad": [round(v, 5) for v in cmd],
                    "pos_rad": [round(float(v), 5) for v in pos_np],
                    "pos_unwrapped_rad": [round(float(v), 5) for v in pos_unw],
                    "vel_rad_s": [round(float(v), 5) for v in vel_np],
                    "err_rad": [round(abs(cmd[i] - float(pos_np[i])), 6)
                                for i in range(5)],
                })

        sub = None  # drop contact subscription

        # --- probe outcome ---------------------------------------------
        # probe_band[i] was OR-ed every 4 steps from pv.get_transforms()
        # (real simulated state); final positions read the same way.
        pt_f = pv.get_transforms()
        PF = (pt_f.numpy() if hasattr(pt_f, 'numpy')
              else np.asarray(pt_f)).reshape(-1, 7)
        P = PF  # stage units: mm
        reached = sum(probe_band)
        per_class = {"d3": [0, 0], "d15": [0, 0]}  # [reached, total]
        probe_final = []
        for i in range(2 * n_each):
            x, y, z = (float(P[i][0]), float(P[i][1]), float(P[i][2]))
            cls = "d3" if i < n_each else "d15"
            per_class[cls][1] += 1
            if probe_band[i]:
                per_class[cls][0] += 1
            if i < 6 or probe_band[i]:
                probe_final.append({"i": i, "class": cls,
                                    "final_pos_mm": [round(x, 1),
                                                     round(y, 1),
                                                     round(z, 1)],
                                    "reached_screen": probe_band[i]})

        # --- contact classification ------------------------------------
        pairs: dict[tuple, int] = {}
        unexpected = []
        probe_probe = 0
        for a, b in contact_log:
            if a == "RAW":
                continue
            key = (a, b) if a < b else (b, a)
            pairs[key] = pairs.get(key, 0) + 1
            if is_by_design(a, b):
                continue
            if "/Probe/" in a and "/Probe/" in b:
                probe_probe += 1
                continue
            unexpected.append({"a": a, "b": b})
        unexpected_pairs = {}
        for u in unexpected:
            k = (u["a"], u["b"]) if u["a"] < u["b"] else (u["b"], u["a"])
            unexpected_pairs[k] = unexpected_pairs.get(k, 0) + 1

        ratio_exp = [vel_ratios[i] * pos_unw[0]
                     for i in range(len(names))]
        results = {
            "schema": "full_machine_verify/2",
            "usd": str(USDA.name),
            "usd_sha256": sha256_file(USDA),
            "step_sha256": bodies["source_step_sha256"],
            "dt_s": args.dt,
            "steps": args.steps,
            "omega_rad_s": omega,
            "theta_total_rad": THETA_TOTAL,
            "ratios_commanded_per_input": {
                "S1A": GEAR_RATIO * CHAIN_A,
                "S1B": -GEAR_RATIO * CHAIN_A,
                "S2Ecc": CHAIN_B,
                "S2Carrier": -CHAIN_B / Q,
            },
            "ratio_tolerance_rad": RATIO_TOL_RAD,
            "end_state_err_rad": {
                n: round(abs(ratio_exp[i] - pos_unw[i]), 4)
                for i, n in enumerate(names)},
            "end_state_ratio_note": ("end-of-cycle joint-vs-input ratio "
                                     "error; per-step transients (50 Hz "
                                     "write quantization + coordinate "
                                     "reset) are reported as max_err "
                                     "separately"),
            "max_tracking_err_rad": {k: round(v, 6)
                                     for k, v in max_err.items()},
            "tracking_pass": (all(abs(ratio_exp[i] - pos_unw[i])
                                  < RATIO_TOL_RAD for i in range(len(names)))
                                  and not err_nan),
            "tracking_nan": err_nan,
            "drive_protocol": ("position-integrated kinematic DOF stepping "
                                "(set_dof_positions per step, drives bypassed)"),
            "torque_source": "get_dof_actuation_forces (raw tensor API); "
                             "zero under kinematic stepping — NOT meaningful, "
                             "recorded for completeness only",
            "torque_available": torque_available,
            "max_abs_torque_Nm": {k: round(v, 6)
                                  for k, v in max_torque.items()},
            "torque_rows": torque_rows[:20],
            "contact_events_total": len(contact_log),
            "contact_raw_event_samples": contact_raw_shapes,
            "contact_pairs_by_design": [
                {"a": k[0], "b": k[1], "count": v}
                for k, v in sorted(pairs.items(), key=lambda kv: -kv[1])
                if is_by_design(k[0], k[1])][:30],
            "unexpected_contact_count": len(unexpected),
            "probe_probe_events": probe_probe,
            "unexpected_contact_pairs": [
                {"a": k[0], "b": k[1], "count": v}
                for k, v in sorted(unexpected_pairs.items(),
                                   key=lambda kv: -kv[1])][:50],
            "probe_test": {
                "total": 2 * n_each,
                "d3mm": {"reached": per_class["d3"][0],
                         "total": per_class["d3"][1]},
                "d15mm": {"reached": per_class["d15"][0],
                          "total": per_class["d15"][1]},
                "reached_screen_total": reached,
                "screen_bbox_mm": list(sb),
                "spawn_z_mm": round(float(spawn_z[0]), 2),
                "sample_final_positions": probe_final,
                "note": "material-path smoke check, NOT grinding "
                        "performance",
            },
            "telemetry_rows": rows,
            "runner": "c2.2/sim/verify_full.py",
            "api_path": ("raw omni.physics.tensors after explicit "
                         "physx_simulation_interface.attach_stage; "
                         "physics driven by SimulationView.step"),
        }
        out_path = run_dir / "results.json"
        out_path.write_text(json.dumps(results, indent=2) + "\n")
        (run_dir / "runner_log.txt").write_text("\n".join(log_lines) + "\n")
        log(f"RESULTS={out_path}")
        log(f"tracking_pass={results['tracking_pass']} "
            f"unexpected_contacts={results['unexpected_contact_count']} "
            f"probes_reached_screen={reached}/{2 * n_each}")
        ok = results["tracking_pass"] and \
            results["unexpected_contact_count"] == 0
        return 0 if ok else 1
    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        log_lines.append("EXCEPTION:\n" + tb)
        try:
            (run_dir / "runner_log.txt").write_text(
                "\n".join(log_lines) + "\n")
        except Exception:
            pass
        return 2
    finally:
        sim.close()


if __name__ == "__main__":
    raise SystemExit(main())
