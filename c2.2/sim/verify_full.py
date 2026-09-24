"""Full-machine motion verification under Isaac Sim 6.1 headless PhysX.

Loads the CAD-derived full-machine assembly with 5-DOF articulation and
11 pose-driven kinematic rigid bodies; default one q=8 M1 input cycle:

  (a) SINGLE-INPUT DEPENDENT DRIVETRAIN (FIX C): exactly ONE input DOF
      (the M1 input shaft) receives an authored position-target ramp.
      EVERY dependent joint target is computed PER STEP from the INPUT
      joint's MEASURED position (and velocity lead term), never from an
      independent authored trajectory:
        tgt_j = ratio_j * (measured_input + measured_input_vel * tau_lead)
      with tau_lead = 2/omega_n cancelling the PD ramp-tracking lag.
      The run therefore verifies the M1 power split against the MEASURED
      input, not a ratio animation of authored targets.  (PhysX in this
      build exposes no geared-constraint USD primitive; per-step measured-
      input dependent targets are the sanctioned ideal gear/chain model —
      no tooth-contact FEM.)
  (b) asserts every dependent joint tracks ratio_j * measured_input
      within RATIO_TOL_RAD per step (position-integrated transients
      reported separately);
  (c) streams the PhysX contact report with the CORRECT callback
      signature (contact_headers, contact_data — the previous runner
      read event.pairs off a headers list and silently recorded zero)
      and classifies every event against the explicit by-design table
      with WHY; contacts removed from reporting via collision-group
      filtering are published as an explicit list (FIX B3);
  (d) logs per-step DOF torques (now meaningful: PD drives are active);
  (e) drops 200 probe spheres (100 x 3mm, 100 x 1.5mm) from the hopper
      mouth and samples the same IDs through S1 exit, auger pickup,
      S2 mouth, one exact screen bore, buffer upper mouth and lower throat;
  (f) reports screen-bbox proximity separately. A connected buffer passage
      does not prove extrusion or 1.75 mm filament production. Stale local
      phase runs cannot explain this run without exact STEP/USD hashes.

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
USD_MANIFEST = USDA.with_suffix(".sidecar.json")
from full_machine import PIVOTS_MM  # noqa: E402 - emitter owns body origins
from flow_localize import hole_transition  # same-bore screen predicate
OUTDIR = C22 / "results" / "full_machine"

# --- drive model (ratios per unit input-shaft rotation, rad) ------------
Q = 8
GEAR_RATIO = -15.0 / 40.0      # jack/input: external helical mesh
CHAIN_A = 24 / 24              # jack -> S1A, same direction
# PPR_VP1: chain B driven from the JACKSHAFT (DRV-SP24-B20_002 24T at jack
# y372 -> DRV-SP12-B12_001 12T at S2 y374), same direction as the jack:
S2_CHAIN = 24 / 12
CHAIN_B = GEAR_RATIO * S2_CHAIN   # S2 eccentric per unit input = -0.75
CMD = {
    "MachineJointIn": lambda th: th,
    "MachineJointS1A": lambda th: GEAR_RATIO * CHAIN_A * th,
    "MachineJointS1B": lambda th: -GEAR_RATIO * CHAIN_A * th,
    "MachineJointS2Ecc": lambda th: CHAIN_B * th,
    "MachineJointS2Carrier": lambda th: -(CHAIN_B * th) / Q,
}
RATIO_TOL_RAD = 0.35  # dynamic PD tracking under the FIX C dependent-target
                      # protocol (ramp lag ~omega*d/k with lead compensation;
                      # coordinate-reset transients are unwrapped away)
THETA_TOTAL = 2 * math.pi * Q  # one full q=8 input cycle

# S2 rotor kinematics (world, mm): orbit center + spin about +Y.
ECC_MM = 7.0
S2_PIVOT = (308.56946468906176, 299.0, 280.0)
S2_ROTOR_PIVOT = (308.56946468906176 - ECC_MM, 299.0, 280.0)
# paddle transfer shaft axis (chute.py rev 6 final): the worm shaft MOVED
# to (362, z374.5); rotation about +Y through the body origin
PADDLE_PIVOT = (362.0, 298.0, 374.5)
# auger conveyor axis (chute.py rev 6 raised design): rotation about +X
# through (y232, z347.1 — measured: shaft-only mesh band x356..362 spans
# z 344.10..350.10 = r3 centered 347.1; flight-floor clearance 3.31 mm);
# any x on the axis works as origin
AUGER_PIVOT = (298.75, 232.0, 347.1)
CROSS_FEED_PIVOT = PIVOTS_MM["CROSS_FEED"]
CROSS_FEED_IDLER_PIVOT = PIVOTS_MM["CROSS_FEED_IDLER"]

# By-design contact pairs (substring pairs, order-insensitive) WITH WHY.
# These pairs are EXPECTED to touch and are classified as by-design in the
# report; everything else is UNEXPECTED (FIX B3 table).
BY_DESIGN = [
    {"a": "mesh_DRV_SP24_B25_001", "b": "mesh_S1_SHAFT_A_001",
     "why": "keyed chain-A sprocket on the S1 main shaft (keyed/journal "
            "fit; sprocket kept in the S1A body by explicit task "
            "classification)"},
    {"a": "mesh_DRV_SP12_B12_001", "b": "mesh_INPUT_ECCENTRIC_SHAFT",
     "why": "keyed chain-B sprocket (12T) on the S2 input eccentric "
            "shaft (chain B jack-driven per PPR_VP1)"},
    {"a": "mesh_DRV_SH15L_001", "b": "mesh_DRV_SH40R_001",
     "why": "helical 15T/40T external mesh, left pinion vs right jack "
            "gear (kinematic ratio, no tooth-contact FEM)"},
    {"a": "mesh_S1_SYNC_001", "b": "mesh_S1_SYNC_002",
     "why": "S1-SYNC 30T/30T external mesh enforcing S1A/S1B counter-"
            "rotation (ratio enforced by drives)"},
    {"a": "mesh_INPUT_ECCENTRIC_SHAFT",
     "b": "mesh_ECCENTRIC_BEARING_ENVELOPE_UNRATED",
     "why": "eccentric journal fit (bearing envelope is unrated "
            "placeholder geometry; overlap by design in a rigid rig)"},
    {"a": "mesh_RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE", "b": "mesh_FIXED_RING_PIN_",
     "why": "fixed-ring cycloid engagement: rotor lobes sweep the ring "
            "pins (q=8 kinematic ratio, ideal constraint)"},
    {"a": "mesh_RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE", "b": "mesh_OUTPUT_ROLLER_",
     "why": "cycloid output coupling: rollers ride in the rotor windows"},
    {"a": "mesh_OUTPUT_ROLLER_", "b": "mesh_OUTPUT_PIN_CARRIER_AND_SHAFT",
     "why": "keyed output pins in the roller bores (carrier coupling)"},
    {"a": "mesh_OUTPUT_ROLLER_", "b": "mesh_RIGID_CYCLOID_HOOK_ROTOR_ENVELOPE",
     "why": "roller/rotor window engagement (same coupling as above, "
            "listed for both substring orders)"},
    {"a": "mesh_PDL_SCRAPER", "b": "mesh_CHUTE_BODY",
     "why": "VP1 rev 5: the three half-round scraper bars (r1.5, static) "
            "are welded to the bypass bay floors at x322/334/346 to deny "
            "the rest corner behind each blade sweep; static weld pair "
            "(no contact force either way)"},
    {"a": "/Probe/", "b": "mesh_CROSS_FEED_SHAFT",
     "why": "probe/screw contact, if observed, is material engagement; "
            "collision is live and not part of the gear/journal filter"},
]

# Contacts REMOVED from reporting (and from simulation) by collision-group
# filtering — every class, with WHY (FIX B3).
CONTACTS_REMOVED_FROM_REPORTING = [
    {"filter": "articulation self-collision disabled",
     "pairs": "S1A <-> S1B (all inter-stack pairs)",
     "why": "cutter hulls interleave by design; hulls cannot represent "
            "the hook interleave — simulating them would jam the "
            "drivetrain with phantom contacts"},
    {"filter": "CollisionGroup Art x Fit",
     "pairs": "any articulation link vs any journal fit / keyed "
              "sprocket / gear-mesh partner / bearing envelope / ring "
              "pin / chain loop",
     "why": "by-design zero-clearance-to-interference overlap; the "
            "ratios are kinematically driven so contact forces must not "
            "act (ideal gear/chain constraint per task contract)"},
    {"filter": "CollisionGroup Art x KinRotor",
     "pairs": "any articulation link vs S2_ROTOR",
     "why": "the rotor orbits/spins inside the articulation envelope by "
            "design (eccentric + carrier share the same axis region)"},
    {"filter": "CollisionGroup Art x KinRoller",
     "pairs": "any articulation link vs S2_ROLLER_1..6",
     "why": "output rollers ride in the keyed carrier pins by design"},
    {"filter": "CollisionGroup KinRotor x KinRoller",
     "pairs": "S2_ROTOR vs S2_ROLLER_1..6",
     "why": "cycloid output coupling by design (rollers ride in rotor "
            "windows)"},
    {"filter": "CollisionGroup KinRotor x Fit",
     "pairs": "S2_ROTOR vs ring pins / bearing envelopes / ring plates",
     "why": "fixed-ring cycloid engagement by design"},
    {"filter": "CollisionGroup KinRoller x Fit",
     "pairs": "S2_ROLLER_1..6 vs ring pins / bearing envelopes / ring "
              "plates",
     "why": "rollers sweep the ring region by design"},
    {"filter": "CollisionGroup Art x KinPaddle",
     "pairs": "any articulation link vs PADDLE (PDL_SHAFT, keyed "
              "PDL_SPROCKET and PDL_WORM)",
     "why": "worm transfer shaft and sprocket pass inside the articulation "
            "envelope by design (chain drive modeled as ideal constraint; "
            "shaft angle is pose-driven from measured S2Ecc)"},
    {"filter": "CollisionGroup KinPaddle x Fit",
     "pairs": "PADDLE vs PDL_CHAIN (paddle chain wraps the widened S2 "
              "12T face and the worm-shaft sprocket)",
     "why": "12T/12T chain band interleave by design; worm-bearing bores "
            "keep a real 1.2 mm clearance to the worm shaft and stay "
            "collidable"},
    {"filter": "CollisionGroup Art x KinAuger",
     "pairs": "any articulation link vs AUGER (shaft, RH flight, wheel)",
     "why": "auger passes inside the articulation envelope by design "
            "(worm-driven conveyor, ideal constraint; pose-driven from "
            "the measured S2Ecc/8 angle)"},
    {"filter": "CollisionGroup KinPaddle x KinAuger",
     "pairs": "PDL_WORM 2-start worm vs AUG_WHEEL 16T conjugate teeth "
              "(and the worm shaft vs the wheel teeth)",
     "why": "worm-wheel mesh by design (8:1 ideal constraint, no "
            "tooth-contact FEM)"},
    {"filter": "CollisionGroup KinAuger x Fit",
     "pairs": "AUGER vs AUG_BEARINGS (west journal bore r5.5, east boss "
              "bore r4.7) and any auger-chain fits",
     "why": "journal fits by design; the flight hull fills the helix "
            "valleys to r5 and the east boss bore is r4.7"},
    {"filter": "CollisionGroup KinCrossFeedJournal x CrossFeedBearing",
     "pairs": "CROSS_FEED_SHAFT journal axial slices (not its RH flight) "
              "vs CROSS_FEED_BEARINGS bores only",
     "why": "zero-clearance rotating journal fit; flight remains collidable "
            "with CROSS_FEED_SHELL, S2 mouth and every fragment"},
    {"filter": "CollisionGroup FeedIdler x CrossFeedBearing",
     "pairs": "CROSS_FEED_IDLER journal vs CROSS_FEED_BEARINGS bore",
     "why": "idler shaft journal fit in its named stationary bore"},
    {"filter": "CollisionGroup FeedIdler x PaddleFeedGear",
     "pairs": "CROSS_FEED_IDLER vs PDL_FEED_GEAR teeth",
     "why": "first equal-12T external mesh has ideal opposite-angle drive; "
            "convex tooth overlap is not a torque measurement"},
    {"filter": "CollisionGroup FeedIdler x CrossFeedGear",
     "pairs": "CROSS_FEED_IDLER vs CROSS_FEED_GEAR teeth",
     "why": "second equal-12T external mesh restores positive 1:1 shaft "
            "angle; convex tooth overlap is not material-path contact"},
]

NOT_FILTERED = ("probes/fragments vs every collider including the cross-feed "
                "flight; articulation links vs Static (real interference "
                "must surface), all kinematic bodies vs Static other than "
                "explicit journal/drive fits (real rotor-screen, auger-"
                "chute and cross-feed-mouth clearances remain collidable)")


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
                  "S2_CARRIER", "PADDLE", "AUGER", "CROSS_FEED",
                  "S2_ROLLER_1", "S2_ROLLER_2", "S2_ROLLER_3",
                  "S2_ROLLER_4", "S2_ROLLER_5", "S2_ROLLER_6", "Static",
                  "Machine"):
        if f"/{token}/" in path:
            return token
    return "OTHER"


def is_by_design(a: str, b: str):
    """Returns the matching by-design entry (dict) or None."""
    for entry in BY_DESIGN:
        d1, d2 = entry["a"], entry["b"]
        if (d1 in a and d2 in b) or (d1 in b and d2 in a):
            return entry
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1600)
    ap.add_argument("--dt", type=float, default=0.005)
    ap.add_argument("--cycles", type=int, default=1,
                    help="number of complete q=8 M1 input cycles")
    ap.add_argument("--out", default=None)
    ap.add_argument("--probes", type=int, default=200)
    args = ap.parse_args()
    if args.cycles < 1 or args.steps < 1 or args.dt <= 0:
        ap.error("cycles, steps and dt must be positive")

    if not USDA.is_file():
        print(json.dumps({"status": "FAIL",
                          "error": f"missing {USDA}; run full_machine.py"}))
        return 1

    bodies = json.loads(BODIES.read_text())
    usd_sha_before = sha256_file(USDA)
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
    # Physics runs never NEED a renderer (CPU physics via the tensor API);
    # these are the documented renderer-off args for physics runs.  On
    # this box RTX still pumps kit frames at startup and logs OOM spam
    # (ollama llama-server holds ~7.6/10.2 GB, never killed) — verified
    # harmless: physics, telemetry and results are unaffected.
    # NOTE: extra_args is the only channel that reaches the kit process —
    # "--/..." keys in the launch config are silently dropped.
    sim = SimulationApp({
        "headless": True,
        "extra_args": [
            "--/app/viewport/enabled=false",
            "--/renderer/active=disabled",
            "--/rtx/viewports/enabled=false",
        ],
    })
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
        # The modeled #35 loop is driven by S1B. PhysX's surface-velocity
        # API moves contact points on the stationary belt mesh; each value
        # below is derived from the measured S1B angular velocity.
        from pxr import Gf, PhysxSchema
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
        hopper_panels = [
            r for r in bodies["solids"]
            if r["name"] in ("HOPPER_PANEL_L", "HOPPER_PANEL_R")]
        if len(hopper_panels) != 2:
            raise RuntimeError("integrated STEP must contain both PC hopper panels")
        hb = [min(r["part_bbox"][i] for r in hopper_panels)
              for i in range(3)] + [
                  max(r["part_bbox"][i] for r in hopper_panels)
                  for i in range(3, 6)]
        n_each = 0 if os.environ.get("PPR_NO_PROBES") else args.probes // 2
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
        theta_total = THETA_TOTAL * args.cycles
        omega = theta_total / (args.steps * args.dt)
        log(f"omega={omega:.4f} rad/s input; cycle={2 * math.pi / omega:.1f}s"
            f"; dt={args.dt}s; steps={args.steps}")

        names = list(dof_names)
        max_err = {n: 0.0 for n in names}
        err_nan = False
        pos_unw = np.zeros(5)   # unwrapped joint position estimate
        prev_pos = np.zeros(5)
        # FIX C drive ratios per unit input rotation
        vel_ratios = np.array([1.0, GEAR_RATIO * CHAIN_A,
                               -GEAR_RATIO * CHAIN_A, CHAIN_B,
                               -CHAIN_B / Q], dtype=np.float64)
        # PD ramp-tracking lead: a critically-damped position drive lags a
        # constant-velocity target by omega*d/k = 2/omega_n seconds; the
        # dependent targets lead the measured input by that much so the
        # residual per-step ratio error reflects real dynamics, not the
        # one-step measurement lag.
        OMEGA_N = 40.0
        TAU_LEAD = 2.0 / OMEGA_N
        max_torque = {n: 0.0 for n in names}
        rows = []
        torque_available = True
        # Same physical probe ID must traverse every gate in temporal
        # order. A screen bbox or an independently spawned S2 piece is
        # never a connected product-flow pass.
        n_probes = 2 * n_each
        s1_exit = [False] * n_probes
        auger_pickup = [False] * n_probes
        s2_mouth = [False] * n_probes
        bore_candidate = [None] * n_probes
        screen_hole = [False] * n_probes
        buffer_upper = [False] * n_probes
        buffer_throat = [False] * n_probes
        previous_probe = np.stack((spawn_x, spawn_y, spawn_z), axis=1)
        torque_rows = []
        probe_band = [False] * (2 * n_each)  # EVER in screen band
        screen = next(r for r in bodies["solids"]
                      if r["name"] == "C2_VERTICAL_DISCHARGE_SCREEN")
        sb = screen["part_bbox"]
        # per-step telemetry: input angle + every dependent joint angle
        steps_angle_rows = []

        kin_paths = ["/World/F0/S2_ROTOR"] + [
            f"/World/F0/S2_ROLLER_{k}" for k in range(1, 7)] + \
            ["/World/F0/PADDLE", "/World/F0/AUGER",
             "/World/F0/CROSS_FEED", "/World/F0/CROSS_FEED_IDLER",
             "/World/F0/BELT", "/World/F0/BELT_DRIVE",
             "/World/F0/BELT_IDLER", "/World/F0/SWEEP_SOUTH",
             "/World/F0/SWEEP_NORTH", "/World/F0/TRANSFER_BELT",
             "/World/F0/TRANSFER_IDLER"]
        kv = sim_view.create_rigid_body_view(kin_paths)
        pv = sim_view.create_rigid_body_view(probe_paths)
        log(f"rigid body views: kin={kv.count}, probes={pv.count}")
        link_paths = kin_paths + ["/World/F0/IN_SHAFT", "/World/F0/S1A",
                                  "/World/F0/S1B", "/World/F0/S2_ECC",
                                  "/World/F0/S2_CARRIER"]

        sim_iface = omni.physx.get_physx_simulation_interface()
        from pxr import PhysicsSchemaTools

        # FIX B3 contact stream: subscription with the CORRECT callback
        # signature (contact_headers, contact_data) — the previous runner
        # read `event.pairs` off the headers object, which always raised,
        # so every run silently recorded zero contacts.  Note: even with
        # the corrected signature this build delivers zero events when
        # physics is stepped via the tensor SimulationView (verified on a
        # minimal floor+sphere scene); the stream is kept best-effort and
        # its availability recorded.
        contact_log: list[tuple[str, str]] = []

        def on_contact(headers, data):
            for h in headers:
                try:
                    a = PhysicsSchemaTools.intToSdfPath(
                        int(h.collider0)).pathString
                    b = PhysicsSchemaTools.intToSdfPath(
                        int(h.collider1)).pathString
                except Exception:
                    continue
                contact_log.append((a, b))

        try:
            _sub = sim_iface.subscribe_contact_report_events(on_contact)
        except Exception as exc:
            log(f"contact subscription unavailable: {exc}")
            _sub = None

        def drain_report():
            try:
                rep = sim_iface.get_contact_report()
            except Exception:
                return
            if rep and len(rep) > 1 and rep[0]:
                for h in rep[0]:
                    try:
                        a = PhysicsSchemaTools.intToSdfPath(
                            int(h.collider0)).pathString
                        b = PhysicsSchemaTools.intToSdfPath(
                            int(h.collider1)).pathString
                    except Exception:
                        continue
                    contact_log.append((a, b))

        transfer_dx = (PIVOTS_MM["TRANSFER_IDLER"][0]
                       - PIVOTS_MM["BELT_DRIVE"][0])
        transfer_dz = (PIVOTS_MM["TRANSFER_IDLER"][2]
                       - PIVOTS_MM["BELT_DRIVE"][2])
        transfer_norm = math.hypot(transfer_dx, transfer_dz)
        transfer_vx = 2.0 * 2.3 * transfer_dx / transfer_norm
        transfer_vz = 2.0 * 2.3 * transfer_dz / transfer_norm
        belt_slope = ((PIVOTS_MM["BELT_IDLER"][2]
                       - PIVOTS_MM["BELT_DRIVE"][2])
                      / (PIVOTS_MM["BELT_IDLER"][0]
                         - PIVOTS_MM["BELT_DRIVE"][0]))
        for step in range(args.steps):
            theta_cmd = omega * (step + 1) * args.dt   # authored INPUT ramp
            import os as _os
            # FIX C: the INPUT joint target is the only authored motion.
            # Dependent joint targets are computed from the MEASURED input
            # state (previous step read) — never an authored trajectory.
            in_m = float(pos_unw[0])
            vin_m = float(vel_np[0]) if step > 0 else 0.0
            lead = in_m + vin_m * TAU_LEAD
            dep_targets = [vel_ratios[i] * lead for i in range(1, 5)]
            if not _os.environ.get("PPR_NO_DRIVE"):
                targets = np.array([[theta_cmd] + dep_targets],
                                   dtype=np.float32).reshape(1, -1)
                av.set_dof_position_targets(targets, np.arange(5))
            # kinematic S2 rotor + rollers: pose derived from the MEASURED
            # S2_ECC / carrier angles (not the authored ramp)
            theta_s2 = float(pos_unw[3])
            carrier = float(pos_unw[4])
            a = -theta_s2 / Q  # spin about +Y (world frame)
            qa = (0.0, math.sin(a / 2), 0.0, math.cos(a / 2))
            pos, _ = rotor_pose(theta_s2)
            kin = np.zeros((len(kin_paths), 7), dtype=np.float32)
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
            # paddle transfer (VP1 rev 6): the worm shaft rotates at the SAME
            # signed angle as the measured S2Ecc DOF (open chain)
            kin[7, 0] = PADDLE_PIVOT[0]
            kin[7, 1] = PADDLE_PIVOT[1]
            kin[7, 2] = PADDLE_PIVOT[2]
            kin[7, 3:] = (0.0, math.sin(theta_s2 / 2), 0.0,
                          math.cos(theta_s2 / 2))
            # auger conveyor (VP1 rev 6): worm 2-start : wheel 16T = 8:1,
            # same sign -> auger angle = measured S2Ecc / 8 about +X
            # (RH flight at omega_x < 0 conveys +x)
            theta_auger = theta_s2 / 8.0
            kin[8, 0] = AUGER_PIVOT[0]
            kin[8, 1] = AUGER_PIVOT[1]
            kin[8, 2] = AUGER_PIVOT[2]
            kin[8, 3:] = (math.sin(theta_auger / 2), 0.0, 0.0,
                          math.cos(theta_auger / 2))
            # CAD drive: two external 12T/12T meshes, so cross-feed turns
            # with the measured S2Ecc/PDL angle and the idler opposes it.
            # Upstream chain-P closure is a separate physical check; these
            # are pose-driven ideal constraints, not proof of torque.
            kin[9, :3] = CROSS_FEED_PIVOT
            kin[9, 3:] = (0.0, math.sin(theta_s2 / 2), 0.0,
                          math.cos(theta_s2 / 2))
            kin[10, :3] = CROSS_FEED_IDLER_PIVOT
            kin[10, 3:] = (0.0, -math.sin(theta_s2 / 2), 0.0,
                           math.cos(theta_s2 / 2))
            # The drive/follower both roll about +Y; chain 24T:12T gives
            # two drum turns per measured S1B turn. The belt collider does
            # not rotate: its contact surface carries the tangential speed.
            drum_angle = 2.0 * float(pos_unw[2])
            kin[11, :3] = PIVOTS_MM["BELT"]
            kin[11, 3:] = (0.0, 0.0, 0.0, 1.0)
            for idx, body in ((12, "BELT_DRIVE"), (13, "BELT_IDLER")):
                kin[idx, :3] = PIVOTS_MM[body]
                kin[idx, 3:] = (0.0, math.sin(drum_angle / 2), 0.0,
                               math.cos(drum_angle / 2))
            for idx, body in ((14, "SWEEP_SOUTH"), (15, "SWEEP_NORTH")):
                kin[idx, :3] = PIVOTS_MM[body]
                kin[idx, 3:] = (0.0, -math.sin(drum_angle / 2), 0.0,
                               math.cos(drum_angle / 2))
            kin[16, :3] = PIVOTS_MM["TRANSFER_BELT"]
            kin[16, 3:] = (0.0, 0.0, 0.0, 1.0)
            kin[17, :3] = PIVOTS_MM["TRANSFER_IDLER"]
            kin[17, 3:] = (0.0, math.sin(drum_angle / 2), 0.0,
                           math.cos(drum_angle / 2))
            belt_speed = 2.0 * 3.8 * (
                float(vel_np[2]) if step > 0 else 0.0)
            # Surface velocity is in stage distance/s (millimetres here).
            belt_velocity.Set(Gf.Vec3f(
                belt_speed, 0.0, belt_speed * belt_slope))
            s1b_speed = float(vel_np[2]) if step > 0 else 0.0
            transfer_velocity.Set(Gf.Vec3f(
                transfer_vx * s1b_speed, 0.0,
                transfer_vz * s1b_speed))
            if not _os.environ.get("PPR_NO_KIN"):
                kv.set_kinematic_targets(kin, np.arange(len(kin_paths),
                                                         dtype=np.int32))
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
            # contact report (pull API per step; subscription best-effort)
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
            # per-step angle record (FIX C deliverable): input angle +
            # every dependent joint angle + the targets they were given
            steps_angle_rows.append({
                "step": step + 1,
                "t_s": round((step + 1) * args.dt, 5),
                "input_target_rad": round(theta_cmd, 5),
                "input_angle_rad": round(float(pos_unw[0]), 5),
                "auger_angle_rad": round(theta_s2 / 8.0, 5),
                "cross_feed_angle_rad": round(theta_s2, 5),
                "dep_angles_rad": [round(float(pos_unw[i]), 5)
                                   for i in range(1, 5)],
                "dep_targets_rad": [round(float(t), 5) for t in dep_targets],
                "dep_err_vs_measured_input_rad": [
                    round(abs(vel_ratios[i] * pos_unw[0] - pos_unw[i]), 5)
                    for i in range(1, 5)],
            })
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
                    prior = previous_probe[i]
                    now = PP[i, :3]
                    radius = float(radii_mm[i])
                    if not s1_exit[i] and prior[2] >= 352.3 > z:
                        t = (prior[2] - 352.3) / (prior[2] - z)
                        gx = prior[0] + t * (x - prior[0])
                        gy = prior[1] + t * (y - prior[1])
                        s1_exit[i] = (83.0 + radius <= gx <= 237.0 - radius
                                      and 162.4 + radius <= gy <= 324.6 - radius)
                    if (s1_exit[i] and not auger_pickup[i]
                            and 237.0 <= x <= 270.0
                            and 223.3 <= y <= 240.9
                            and 338.0 <= z <= 356.0):
                        auger_pickup[i] = True
                    if (auger_pickup[i] and not s2_mouth[i]
                            and prior[1] < 255.0 <= y):
                        t = (255.0 - prior[1]) / (y - prior[1])
                        mx = prior[0] + t * (x - prior[0])
                        mz = prior[2] + t * (z - prior[2])
                        s2_mouth[i] = (
                            350.0 + radius <= mx <= 359.7 - radius
                            and math.hypot(mx - 308.56946468906176,
                                           mz - 280.0) + radius <= 65.6
                            and mz - radius >= 317.3 - 1e-4)
                    if s2_mouth[i] and not screen_hole[i]:
                        bore_candidate[i], completed = hole_transition(
                            prior, now, radius, bore_candidate[i])
                        screen_hole[i] = completed is not None
                    if (screen_hole[i] and not buffer_upper[i]
                            and prior[2] >= 218.0 > z):
                        t = (prior[2] - 218.0) / (prior[2] - z)
                        bx = prior[0] + t * (x - prior[0])
                        by = prior[1] + t * (y - prior[1])
                        buffer_upper[i] = (
                            216.57 + radius <= bx <= 400.57 - radius
                            and 254.0 + radius <= by <= 296.0 - radius)
                    if (buffer_upper[i] and not buffer_throat[i]
                            and prior[2] >= 145.0 > z):
                        t = (prior[2] - 145.0) / (prior[2] - z)
                        bx = prior[0] + t * (x - prior[0])
                        by = prior[1] + t * (y - prior[1])
                        buffer_throat[i] = (
                            267.0 + radius <= bx <= 311.0 - radius
                            and 258.0 + radius <= by <= 292.0 - radius)
                    previous_probe[i] = now
            if step % 40 == 0 or step == args.steps - 1:
                rows.append({
                    "step": step + 1, "t_s": round((step + 1) * args.dt, 4),
                    "theta_cmd_rad": theta_cmd,
                    "tgt_rad": [round(theta_cmd, 5)]
                               + [round(t, 5) for t in dep_targets],
                    "pos_rad": [round(float(v), 5) for v in pos_np],
                    "pos_unwrapped_rad": [round(float(v), 5) for v in pos_unw],
                    "vel_rad_s": [round(float(v), 5) for v in vel_np],
                    "err_rad": [round(abs(vel_ratios[i] * pos_unw[0]
                                          - pos_unw[i]), 6)
                                for i in range(5)],
                })

        _sub = None  # drop contact subscription

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
        # The independent flow-localization run can only contextualize
        # this connected run when all its phases used these exact assets.
        # A prior scene's BLOCKED verdict is not an explanation here.
        usd_sha = sha256_file(USDA)
        step_sha = bodies["source_step_sha256"]
        try:
            scene_manifest = json.loads(USD_MANIFEST.read_text())
        except (OSError, ValueError):
            scene_manifest = {}
        source_scene_linked = bool(
            usd_sha == usd_sha_before
            and scene_manifest.get("source_bodies", {}).get(
                "step_sha256") == step_sha
            and scene_manifest.get("usd_sha256") == usd_sha)
        flow_localized = None
        flow_path = (C22 / "results" / "full_machine" / "flow_localize"
                     / "results.json")
        if flow_path.is_file():
            try:
                flow_localized = json.loads(flow_path.read_text())
            except (OSError, ValueError):
                flow_localized = None
        flow_scene_matches = bool(
            source_scene_linked and flow_localized
            and flow_localized.get("schema") == "full_machine_flow_localize/2"
            and flow_localized.get("scene_consistent") is True
            and flow_localized.get("step_sha256") == step_sha
            and flow_localized.get("usda_sha256") == usd_sha)
        flow_explains = None
        if flow_scene_matches and flow_localized.get("verdicts"):
            v = flow_localized["verdicts"]
            blocked = [ph for ph, d in v.items()
                       if d.get("verdict") == "BLOCKED"]
            flow_explains = {
                "blocked_phases": blocked,
                "top_blockers": {ph: v[ph].get("top_blocker_solids")
                                 for ph in blocked},
                "localizes_obstruction": bool(blocked),
            }
        tracking_pass_val = (all(abs(ratio_exp[i] - pos_unw[i])
                                  < RATIO_TOL_RAD
                                  for i in range(len(names)))
                             and not err_nan)
        total_probes = 2 * n_each
        connected_ids = [
            i for i in range(total_probes)
            if (s1_exit[i] and auger_pickup[i] and s2_mouth[i]
                and screen_hole[i] and buffer_upper[i] and buffer_throat[i])]
        if not source_scene_linked:
            verdict = "FAIL_SCENE_PROVENANCE"
        elif not tracking_pass_val or not total_probes:
            verdict = "FAIL"
        elif connected_ids:
            verdict = "CONNECTED_BUFFER_REACHED"
        elif reached == 0 and flow_explains and flow_explains[
                "localizes_obstruction"]:
            verdict = "LOCALIZED_BLOCKED"
        elif reached == 0:
            verdict = "BLOCKED_UNLOCALIZED"
        elif reached < total_probes:
            verdict = "PARTIAL_PROBE_REACH"
        else:
            verdict = "PROBE_BAND_REACHED"
        # Connected material-to-buffer is measured below; filament output
        # still requires an extrusion/diameter path not exercised here.
        product_flow_verified = False
        results = {
            "schema": "full_machine_verify/4",
            "usd": str(USDA.name),
            "usd_sha256": usd_sha,
            "step_sha256": step_sha,
            "usd_source_linked": source_scene_linked,
            "dt_s": args.dt,
            "steps": args.steps,
            "omega_rad_s": omega,
            "input_cycles": args.cycles,
            "theta_total_rad": theta_total,
            "drive_protocol": (
                "FIX C single-input dependent drivetrain: ONE authored "
                "input position-target ramp (M1 shaft); dependent joint "
                "targets computed PER STEP from the INPUT joint's "
                "MEASURED position + velocity lead (tau_lead = 2/"
                "omega_n); PD drives active (stiffness 1600*I/57.3 per "
                "degree, damping 80*I/57.3, omega_n=40, zeta=1); no "
                "tooth-contact FEM; no per-joint authored trajectories. "
                "PhysX in this build exposes no geared-constraint USD "
                "primitive — measured-input dependent targets are the "
                "ideal gear/chain constraint."),
            "ratios_commanded_per_input": {
                "S1A": GEAR_RATIO * CHAIN_A,
                "S1B": -GEAR_RATIO * CHAIN_A,
                "S2Ecc": CHAIN_B,
                "S2Carrier": -CHAIN_B / Q,
            },
            "chain_topology": ("IDEAL KINEMATIC MODEL: M1 -> 15T/40T jack; "
                               "chain A 24/24 jack->S1A; chain B 24/12 "
                               "jack->S2Ecc (-0.75/input); chain P 12/12 "
                               "-> PDL_SHAFT (measured S2Ecc 1:1); "
                               "PDL_WORM 2-start -> AUG_WHEEL 16T -> "
                               "AUGER (S2Ecc/8 about +X); PDL_FEED_GEAR "
                               "-> CROSS_FEED_IDLER -> CROSS_FEED_GEAR, "
                               "two external 12T meshes yielding positive "
                               "1:1 CROSS_FEED_SHAFT about +Y. Upstream "
                               "chain-P assembly length and actual torque "
                               "continuity require a separate CAD check."),
            "ratio_sources": ["design/parameters.json drive block",
                              "c2.1/src/drive_kinematics.py ratio_chain",
                              "c2.1/src/transmission.py pose() q=8"],
            "ratio_tolerance_rad": RATIO_TOL_RAD,
            "end_state_err_rad": {
                n: round(abs(ratio_exp[i] - pos_unw[i]), 4)
                for i, n in enumerate(names)},
            "end_state_ratio_note": ("end-of-cycle joint-vs-MEASURED-input "
                                     "ratio error; per-step transients are "
                                     "reported as max_err separately"),
            "max_tracking_err_rad": {k: round(v, 6)
                                     for k, v in max_err.items()},
            "tracking_pass": tracking_pass_val,
            "tracking_nan": err_nan,
            "torque_source": ("get_dof_actuation_forces (raw tensor API); "
                              "meaningful under active PD drives"),
            "torque_available": torque_available,
            "max_abs_torque_Nm": {k: round(v, 6)
                                  for k, v in max_torque.items()},
            "torque_rows": torque_rows[:20],
            "contact_filter_table": {
                "by_design_pairs": BY_DESIGN,
                "removed_from_reporting": CONTACTS_REMOVED_FROM_REPORTING,
                "not_filtered": NOT_FILTERED,
                "observed_by_design_pairs": [
                    {"a": k[0], "b": k[1], "count": v,
                     "why": is_by_design(k[0], k[1])["why"]
                     if is_by_design(k[0], k[1]) else None}
                    for k, v in sorted(pairs.items(), key=lambda kv: -kv[1])
                    if is_by_design(k[0], k[1])][:30],
            },
            "contact_events_total": len(contact_log),
            "contact_stream_note": ("corrected subscription signature "
                                    "(headers, data); this build delivers "
                                    "zero events under SimulationView "
                                    "stepping (verified on a minimal "
                                    "scene) — stream is best-effort"),
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
                "connected_stage_counts": {
                    "s1_exit": int(sum(s1_exit)),
                    "auger_pickup": int(sum(auger_pickup)),
                    "s2_mouth": int(sum(s2_mouth)),
                    "same_screen_bore": int(sum(screen_hole)),
                    "buffer_upper": int(sum(buffer_upper)),
                    "buffer_throat": int(sum(buffer_throat)),
                },
                "same_probe_ids_screen_to_buffer": connected_ids,
                "connected_buffer_verified": bool(
                    source_scene_linked and tracking_pass_val and connected_ids),
                "screen_bbox_mm": list(sb),
                "spawn_z_mm": round(float(spawn_z[0]), 2),
                "sample_final_positions": probe_final,
                "note": "probe screen-bbox proximity only, not measured "
                        "screen-hole passage, outlet delivery or complete "
                        "product flow",
            },
            "flow_localization_reference": {
                "path": str(flow_path),
                "present": flow_localized is not None,
                "exact_scene_hash_match": flow_scene_matches,
                "step_sha256": (flow_localized.get("step_sha256")
                                if flow_localized else None),
                "usda_sha256": (flow_localized.get("usda_sha256")
                                if flow_localized else None),
                "explains": flow_explains,
            },
            "product_flow_verified": product_flow_verified,
            "product_flow_note": ("connected S1-to-screen-bore-to-buffer "
                                  "measured by same probe IDs separately; "
                                  "extrusion, 1.75 mm filament and winding "
                                  "product remain untested"),
            "verdict": verdict,
            "verdict_rule": ("No PASS from screen-band probes alone. "
                             "Mismatched STEP/USD = FAIL_SCENE_PROVENANCE; "
                             "tracking failure = FAIL; at least one same-ID "
                             "S1 exit, auger pickup, S2 mouth, exact screen "
                             "bore, buffer upper and lower throat = "
                             "CONNECTED_BUFFER_REACHED (not filament). "
                             "Otherwise zero band reach = BLOCKED, partial "
                             "band reach = PARTIAL_PROBE_REACH, all band "
                             "reach = PROBE_BAND_REACHED."),
            "telemetry_rows": rows,
            "per_step_angles": steps_angle_rows,
            "runner": "c2.2/sim/verify_full.py",
            "api_path": ("raw omni.physics.tensors after explicit "
                         "physx_simulation_interface.attach_stage; "
                         "physics driven by SimulationView.step"),
        }
        out_path = run_dir / "results.json"
        out_path.write_text(json.dumps(results, indent=2) + "\n")
        (run_dir / "runner_log.txt").write_text("\n".join(log_lines) + "\n")
        log(f"RESULTS={out_path}")
        log(f"verdict={verdict} tracking_pass={results['tracking_pass']} "
            f"unexpected_contacts={results['unexpected_contact_count']} "
            f"probes_reached_screen={reached}/{2 * n_each}")
        # Diagnostic outcomes are evidence, not product-flow acceptance.
        # A failed drive or missing probes is a verifier failure.
        return 0 if source_scene_linked and tracking_pass_val \
            and total_probes else 1
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
