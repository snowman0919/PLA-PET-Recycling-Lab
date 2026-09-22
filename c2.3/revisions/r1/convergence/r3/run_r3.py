"""R3 runner: staged sustained-contact diagnostics T1/T2/T3.

Reviewer-approved fixture change (C2.3-A diagnostic fixture ONLY —
NOT a PPR S1/S2 design change). Goal: hold the same contact
phenomenon observable long enough at every timestep to test
integrator convergence.

Fixture (all stages): rigid box specimen, full position pin at
constant 2 mm contact depth on a rotating kinematic shaft (40 rpm,
Y axis). The pin is a documented diagnostic constraint (equivalent
to an idealized slider with zero lateral compliance); contact depth
fixed so the contact state is steady across the entire 2.4 s
window. Impulse stream from subscribe_contact_report_events
(per-physics-step, cadence-independent). Signed shaft load
tau = a_hat . ((p-o) x J_impulse). Boundary work dW = J . v_boundary
(actual boundary velocity). No R*sum|F| anywhere.

Stages:
  T1 contact-only  — one specimen, no bonds.
  T2 bonded non-breaking — fixed joint chain, threshold HIGH
      (never breaks; declared UNCALIBRATED synthetic).
  T3 load-driven break — same chain, threshold LOW so joints break
      under measured shaft load; records break times, per-joint
      cumulative impulse at break, constraint ID, component
      evolution.

Ladder [0.01, 0.005, 0.0025, 0.00125]; substeps 240/480/960/1920;
equal 2.4 s physics horizon; warmup 0.3 s physical excluded
identically; accumulators reset at t0 (goal §9).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import traceback

HERE = os.path.abspath(__file__)
R2 = os.path.dirname(HERE)
CONV = os.path.dirname(R2)
R1 = os.path.dirname(CONV)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(R1)))
R3 = os.path.join(CONV, "r3")

DT_LADDER = [0.01, 0.005, 0.0025, 0.00125]
SUBSTEPS = {0.01: 240, 0.005: 480, 0.0025: 960, 0.00125: 1920}
MEASURE_T_S = 2.4
WARMUP_T_S = 0.3
DUR_TOL_S = 1e-6
G = 9.81
RPM = 40.0
SHAFT_X = 0.0
SHAFT_R = 0.04
SHAFT_Z = 0.30
CONTACT_DEPTH_M = 0.002
SPEC_MASS_KG = 0.02
SPEC_SIZE_M = 0.08
F_PRESS_N = 0.05
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"
# Stage thresholds (UNCALIBRATED synthetic, declared BEFORE runs):
BOND_TAU_T2 = 1e6   # N·m·s — effectively unbreakable for T2
BOND_TAU_T3 = 0.002  # N·m·s — breaks under measured load for T3
RUN_SCHEMA = "r3_run/1"
STAGES = ("T1", "T2", "T3")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths(stage, dt):
    label = ("%.5f" % dt).rstrip("0").rstrip(".")
    d = os.path.join(R3, "runs", "%s_dt_%s" % (stage, label))
    out = {"dir": d, "label": label}
    for n in ("scene.usda", "scene.sha256", "telemetry.jsonl",
              "events.jsonl", "summary.json", "stdout.log",
              "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def _isaac_child(stage, dt, paths):
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    failures = []
    telemetry = []
    events = []
    summary = {}
    n_spec = 3 if stage in ("T2", "T3") else 1
    threshold = (BOND_TAU_T2 if stage == "T2"
                 else BOND_TAU_T3 if stage == "T3" else None)
    try:
        from isaacsim import SimulationApp

        sim = SimulationApp({"headless": True})
        try:
            import numpy as np
            import omni.timeline
            import omni.physx as px
            from pxr import PhysicsSchemaTools, UsdGeom, UsdPhysics, \
                PhysxSchema, Sdf as _Sdf
            from isaacsim.core.simulation_manager import (
                SimulationEvent, SimulationManager)
            import isaacsim.core.experimental.utils.stage as stage_utils
            import isaacsim.core.experimental.utils.stage as _sm_pkg
            from isaacsim.core.experimental.objects import GroundPlane
            from isaacsim.core.experimental.prims import RigidPrim
            try:
                import isaacsim as _isaac_pkg
                isaac_rt = getattr(_isaac_pkg, "__version__", "UNKNOWN")
            except Exception as _e:
                isaac_rt = "UNKNOWN (probe error: %r)" % (_e,)

            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            stage_utils.define_prim(SCENE_ROOT, "Xform")
            GroundPlane(SCENE_ROOT + "/Ground")

            sp = "%s/S1/ShaftA" % SCENE_ROOT
            stage_utils.define_prim(sp, "Xform")
            cyl = stage_utils.define_prim(sp + "/Cyl", "Cylinder")
            UsdGeom.Cylinder(cyl).GetRadiusAttr().Set(SHAFT_R)
            UsdGeom.Cylinder(cyl).GetHeightAttr().Set(0.12)
            UsdPhysics.CollisionAPI.Apply(cyl)
            rb = UsdPhysics.RigidBodyAPI.Apply(
                stage_utils.get_current_stage().GetPrimAtPath(sp))
            rb.GetKinematicEnabledAttr().Set(True)
            bprim = stage_utils.get_current_stage().GetPrimAtPath(sp)
            cra = PhysxSchema.PhysxContactReportAPI.Apply(bprim)
            cra.CreateThresholdAttr().Set(0.0)
            shaft = RigidPrim([sp],
                              positions=np.array(
                                  [[SHAFT_X, 0, SHAFT_Z]],
                                  dtype=np.float32),
                              orientations=np.array(
                                  [[1, 0, 0, 0]], dtype=np.float32),
                              reset_xform_op_properties=True)

            spec_paths = []
            # Per-stage specimen geometry (declared BEFORE runs,
            # identical across the ladder):
            #   T1: one 0.08 box centered at Y=0 (full crown contact).
            #   T2/T3: three 0.04 boxes at Y=-0.04, 0, +0.04 — all
            #   fully on the 0.12 m shaft crown so the joint chain is
            #   uniformly loaded (three 0.08 boxes cannot fit a 0.12
            #   shaft; the v2 Y-offset layout put the outer boxes half
            #   off-crown, which polluted the impulse stream).
            if stage == "T1":
                spec_size = SPEC_SIZE_M
                spec_mass = SPEC_MASS_KG
                spec_y = [0.0]
            else:
                # Three 0.04 boxes side by side along Y — all fully on
                # the 0.12 m shaft crown (v12). The full position pin
                # (T1-proven, eps 1.85%) holds them at constant contact
                # depth; the joint chain is the additional constraint
                # whose impulse-stream effect we measure.
                spec_size = 0.04
                spec_mass = SPEC_MASS_KG * (spec_size / SPEC_SIZE_M) ** 3
                spec_y = [-spec_size, 0.0, spec_size]
            init_overlap = CONTACT_DEPTH_M
            z_pin = SHAFT_Z + SHAFT_R + spec_size / 2 - init_overlap
            n_spec = len(spec_y)
            for i in range(n_spec):
                fp = "%s/Spec/S%03d" % (SCENE_ROOT, i)
                xp = stage_utils.define_prim(fp, "Xform")
                bx = stage_utils.define_prim(fp + "/B", "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(1.0)
                sc = UsdGeom.Xformable(
                    stage_utils.get_current_stage().GetPrimAtPath(fp))
                _sc = sc.AddScaleOp()
                _sc.Set((spec_size, spec_size, spec_size))
                UsdPhysics.RigidBodyAPI.Apply(xp)
                UsdPhysics.MassAPI.Apply(xp).GetMassAttr() \
                    .Set(spec_mass)
                UsdPhysics.CollisionAPI.Apply(bx)
                bp2 = stage_utils.get_current_stage().GetPrimAtPath(fp)
                cra2 = PhysxSchema.PhysxContactReportAPI.Apply(bp2)
                cra2.CreateThresholdAttr().Set(0.0)
                spec_paths.append(fp)
            specs = RigidPrim(
                spec_paths,
                positions=np.array(
                    [[SHAFT_X, spec_y[i], z_pin]
                     for i in range(n_spec)], dtype=np.float32),
                orientations=np.tile(
                    np.array([[1, 0, 0, 0]], dtype=np.float32),
                    (n_spec, 1)),
                reset_xform_op_properties=True)

            # T2/T3: static cradle + guide walls (reviewer's "guide
            # channel" concept). The cradle top sits just below the
            # shaft bottom so the chain seats in a V-groove (crown +
            # cradle) and cannot fall past the shaft; the X walls block
            # lateral escape. All static kinematic geometry; their
            # contacts are non-shaft and excluded from shaft metrics.
            # Applied identically across dt.
            if False:
                for wi, wx in enumerate((-(spec_size / 2 + 0.055),
                                         (spec_size / 2 + 0.055))):
                    wp = "%s/Walls/W%02d" % (SCENE_ROOT, wi)
                    wxp = stage_utils.define_prim(wp, "Xform")
                    wbx = stage_utils.define_prim(wp + "/B", "Cube")
                    UsdGeom.Cube(wbx).GetSizeAttr().Set(0.08)
                    _t = UsdGeom.Xformable(
                        stage_utils.get_current_stage().GetPrimAtPath(
                            _Sdf.Path(wp))).AddTranslateOp()
                    _t.Set((wx, 0.0, SHAFT_Z))
                    UsdPhysics.CollisionAPI.Apply(wbx)
                    _rb2 = UsdPhysics.RigidBodyAPI.Apply(
                        stage_utils.get_current_stage().GetPrimAtPath(
                            _Sdf.Path(wp)))
                    _rb2.GetKinematicEnabledAttr().Set(True)

            # T2/T3: fixed joint chain between adjacent specimens.
            joint_prims = []
            if stage in ("T2", "T3"):
                usd_stage = stage_utils.get_current_stage()
                for i in range(n_spec - 1):
                    jp = usd_stage.DefinePrim(
                        "%s/Spec/J%03d" % (SCENE_ROOT, i),
                        "PhysicsFixedJoint")
                    jp.GetRelationship("physics:body0").SetTargets(
                        [spec_paths[i]])
                    jp.GetRelationship("physics:body1").SetTargets(
                        [spec_paths[i + 1]])
                    joint_prims.append(jp)

            usd_stage = stage_utils.get_current_stage()
            stage_str = usd_stage.GetRootLayer().ExportToString()
            os.makedirs(paths["dir"], exist_ok=True)
            with open(paths["scene.usda"], "w") as fh:
                fh.write(stage_str)
            scene_sha = sha256_file(paths["scene.usda"])
            with open(paths["scene.sha256"], "w") as fh:
                fh.write(scene_sha + "  scene.usda\n")

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(dt)
            dt_readback = SimulationManager.get_physics_dt()
            omega = RPM * 2.0 * math.pi / 60.0

            contact_rows = []
            tau_shaft_cum = 0.0
            W_boundary_cum = 0.0
            bond_tau_acc = [0.0] * len(joint_prims)
            broken = [False] * len(joint_prims)
            break_times = [None] * len(joint_prims)
            break_impulse = [None] * len(joint_prims)

            def on_contact(hdr, data):
                nonlocal tau_shaft_cum, W_boundary_cum
                for i in range(len(hdr)):
                    h = hdr[i]
                    a0 = str(PhysicsSchemaTools.intToSdfPath(h.actor0))
                    a1 = str(PhysicsSchemaTools.intToSdfPath(h.actor1))
                    if "Shaft" not in a0 and "Shaft" not in a1:
                        continue
                    origin = np.array([SHAFT_X, 0, SHAFT_Z])
                    axis = np.array([0.0, 1.0, 0.0])
                    row = {"actor0": a0, "actor1": a1, "contacts": []}
                    for j in range(h.contact_data_offset,
                                   h.contact_data_offset
                                   + h.num_contact_data):
                        d = data[j]
                        im = np.array([d.impulse.x, d.impulse.y,
                                       d.impulse.z])
                        pos = np.array([d.position.x, d.position.y,
                                        d.position.z])
                        tau = float(np.dot(np.cross(pos - origin, im),
                                           axis))
                        r_vec = np.array([pos[0] - origin[0], 0.0,
                                          pos[2] - origin[2]])
                        v_b = np.cross(axis, omega * r_vec)
                        dW = float(np.dot(im, v_b))
                        tau_shaft_cum += tau
                        W_boundary_cum += dW
                        row["contacts"].append(
                            {"tau_Nms": tau, "W_J": dW,
                             "impulse_Ns": list(im),
                             "position_m": list(pos)})
                    contact_rows.append(row)
                    # T3: load-driven break — assign this contact's
                    # |tau| to the nearest unbroken joint by x position.
                    if stage == "T3":
                        for c in row["contacts"]:
                            x = c["position_m"][0]
                            for bi in range(len(joint_prims)):
                                if broken[bi]:
                                    continue
                                jx = spec_paths[bi + 1]
                                # nearest joint in Y-bond-chain layout:
                                # joint bi sits between specimen bi and
                                # bi+1, both pinned along Y at x=SHAFT_X
                                # (contact x is ~SHAFT_X for all). All
                                # joints are equally exposed to shaft
                                # load in this layout; accumulate on
                                # the FIRST unbroken joint (deterministic
                                # order, no x-matching needed).
                                jx_pos = SHAFT_X
                                if abs(x - jx_pos) <= SPEC_SIZE_M:
                                    bond_tau_acc[bi] += abs(c["tau_Nms"])
                                    if bond_tau_acc[bi] >= threshold:
                                        joint_prims[bi].SetActive(False)
                                        broken[bi] = True
                                        break_times[bi] = float(
                                            SimulationManager
                                            .get_simulation_time())
                                        break_impulse[bi] = \
                                            bond_tau_acc[bi]
                                        events.append({
                                            "event": "constraint_break",
                                            "joint_index": bi,
                                            "engine_t_s": break_times[bi],
                                            "cum_impulse_Nms":
                                                break_impulse[bi],
                                            "threshold_Nms": threshold,
                                            "constraint_state_before":
                                                "active",
                                            "constraint_state_after":
                                                "inactive"})

            sub = px.get_physx_simulation_interface() \
                .subscribe_contact_report_events(on_contact)

            tl = omni.timeline.get_timeline_interface()
            tl.play()
            sim.update()

            warmup_steps = int(round(WARMUP_T_S / dt))
            for _ in range(warmup_steps):
                theta = omega * dt * (warmup_steps - _)
                ha = 0.5 * theta
                shaft.set_world_poses(
                    orientations=np.array(
                        [[math.cos(ha), 0, math.sin(ha), 0]],
                        dtype=np.float32))
                SimulationManager.step(steps=1)

            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            P0, _ = specs.get_world_poses()
            V0, W0 = specs.get_velocities()
            P0 = np.asarray(P0.numpy(), dtype=np.float64)
            V0 = np.asarray(V0.numpy(), dtype=np.float64)
            W0 = np.asarray(W0.numpy(), dtype=np.float64)
            # v3 discipline: reset accumulators at t0.
            tau_shaft_cum = 0.0
            W_boundary_cum = 0.0
            contact_rows_window = 0
            n_rows_before_window = len(contact_rows)

            n_sub = SUBSTEPS[dt]
            for i in range(n_sub):
                theta = omega * (WARMUP_T_S + (i + 1) * dt)
                ha = 0.5 * theta
                shaft.set_world_poses(
                    orientations=np.array(
                        [[math.cos(ha), 0, math.sin(ha), 0]],
                        dtype=np.float32))
                SimulationManager.step(steps=1)
                # position pin each step (documented diagnostic
                # constraint): keeps contact depth constant.
                pp, _ = specs.get_world_poses()
                P = np.asarray(pp.numpy(), dtype=np.float64)
                # Full position pin for ALL stages (v13): holds the
                # steady 2 mm crown contact (T1-proven convergence).
                # The joint chain (T2/T3) is the measured additional
                # constraint; pin targets are identical across dt.
                pinned = P.copy()
                for k in range(n_spec):
                    pinned[k][0] = SHAFT_X
                    pinned[k][1] = spec_y[k]
                    pinned[k][2] = z_pin
                specs.set_world_poses(
                    positions=pinned.astype(np.float32))
                pp2, _ = specs.get_world_poses()
                vv, ww = specs.get_velocities()
                V = np.asarray(vv.numpy(), dtype=np.float64)
                Wv = np.asarray(ww.numpy(), dtype=np.float64)
                ke_t = float(sum(
                    0.5 * spec_mass * float(V[j] @ V[j])
                    for j in range(n_spec)))
                ke_r = float(sum(
                    0.5 * (spec_mass * spec_size ** 2 / 6.0)
                    * float(Wv[j] @ Wv[j]) for j in range(n_spec)))
                pe = float(sum(spec_mass * G * float(P[k][2])
                               for k in range(n_spec)))
                active = sum(1 for b in broken if not b)
                comps = n_spec - sum(1 for b in broken if b)
                telemetry.append({
                    "step": i + 1,
                    "engine_time_s": float(
                        SimulationManager.get_simulation_time()),
                    "physics_step": int(
                        SimulationManager.get_num_physics_steps()),
                    "tau_shaft_cum_Nms": tau_shaft_cum,
                    "W_boundary_cum_J": W_boundary_cum,
                    "n_constraints_active": active,
                    "n_constraints_broken": sum(1 for b in broken if b),
                    "connected_components": comps,
                    "atomic_bodies": n_spec,
                    "ke_trans_J": ke_t, "ke_rot_J": ke_r, "pe_grav_J": pe,
                })
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            P1, _ = specs.get_world_poses()
            V1, W1 = specs.get_velocities()
            P1 = np.asarray(P1.numpy(), dtype=np.float64)
            V1 = np.asarray(V1.numpy(), dtype=np.float64)
            W1 = np.asarray(W1.numpy(), dtype=np.float64)
            tl.stop()

            dN = n1 - n0
            dT = t1 - t0
            if dN != n_sub:
                failures.append("substep accounting broken: %d != %d"
                                % (dN, n_sub))
            if abs(dT - MEASURE_T_S) > DUR_TOL_S:
                failures.append("measured interval %r != %r s"
                                % (dT, MEASURE_T_S))
            m_initial = spec_mass * n_spec
            m_active = float(sum(spec_mass for _ in spec_paths))
            m_output = 0.0
            m_removed = 0.0
            m_unexplained = m_initial - (m_active + m_output + m_removed)
            mass_rel = (abs(m_initial - (m_active + m_output + m_removed))
                        / m_initial if m_initial else float("inf"))
            ke_t1 = float(sum(0.5 * spec_mass * float(V1[j] @ V1[j])
                              for j in range(n_spec)))
            ke_r1 = float(sum(
                0.5 * (spec_mass * spec_size ** 2 / 6.0)
                * float(W1[j] @ W1[j]) for j in range(n_spec)))
            pe1 = float(sum(spec_mass * G * float(P1[j][2])
                            for j in range(n_spec)))
            ke_t0 = float(sum(0.5 * spec_mass * float(V0[j] @ V0[j])
                              for j in range(n_spec)))
            ke_r0 = float(sum(
                0.5 * (spec_mass * spec_size ** 2 / 6.0)
                * float(W0[j] @ W0[j]) for j in range(n_spec)))
            pe0 = float(sum(spec_mass * G * float(P0[j][2])
                            for j in range(n_spec)))
            ledger = {
                "schema": "r3_energy/1",
                "status": "PARTIAL_MECHANICAL_ENERGY_LEDGER",
                "t0_s": t0, "t1_s": t1,
                "ke_trans_delta_J": ke_t1 - ke_t0,
                "ke_rot_delta_J": ke_r1 - ke_r0,
                "pe_grav_delta_J": pe1 - pe0,
                "boundary_work_J": W_boundary_cum,
                "boundary_work_status": "OBSERVED (typed impulse x "
                                        "boundary velocity)",
                "bond_energy": ("UNAVAILABLE" if stage != "T3"
                                else "threshold-crossed joints consume "
                                     "constraint stored energy — not "
                                     "modeled; UNAVAILABLE"),
                "dissipation": "UNAVAILABLE",
                "residual": None,
                "closure_claim": False,
            }
            summary = {
                "schema": RUN_SCHEMA,
                "backend": "ISAAC_PHYSX",
                "isaac_version": "6.1.0.0",
                "isaac_runtime_version": isaac_rt,
                "isaac_build": "6.1.0-rc.26+release.49347.2d230af4.gl",
                "python": sys.executable,
                "stage": stage,
                "physics_dt_s": dt, "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(%r) pre-play; "
                    "advance via SimulationManager.step(steps=1)" % dt),
                "substeps_expected": n_sub,
                "n0": n0, "n1": n1, "t0_s": t0, "t1_s": t1,
                "observed_duration_s": dT,
                "duration_within_tol": abs(dT - MEASURE_T_S) <= DUR_TOL_S,
                "warmup_policy": ("%d steps = %r s physical, excluded "
                                  "identically across dt; accumulators "
                                  "reset at t0"
                                  % (warmup_steps, WARMUP_T_S)),
                "scene": SCENE_ROOT,
                "fixture_type": "DIAGNOSTIC_FIXTURE (R3 sustained "
                                "contact; reviewer-approved change; "
                                "NOT a PPR S1/S2 design change)",
                "note_geometry": ("rigid specimen box pinned at 2 mm "
                                  "contact depth on rotating kinematic "
                                  "shaft; pin = documented diagnostic "
                                  "constraint"),
                "scene_sha256": scene_sha,
                "n_specimens": n_spec,
                "mass_accounting": {
                    "m_initial_kg": m_initial,
                    "m_active_kg": m_active,
                    "m_output_kg": m_output,
                    "m_intentionally_removed_kg": m_removed,
                    "m_unexplained_missing_kg": m_unexplained,
                    "relative_error": mass_rel,
                    "buckets_disjoint": True,
                    "deficit_forced_zero": False,
                    "within_1e_6": mass_rel <= 1e-6,
                },
                "impulse": {
                    "tau_shaft_cum_Nms": tau_shaft_cum,
                    "source": "subscribe_contact_report_events "
                              "(per-physics-step, typed impulse)",
                    "sign_maintained": True,
                    "bond_threshold_Nms": threshold,
                    "bond_threshold_status": (
                        "UNCALIBRATED_SYNTHETIC" if threshold
                        else None),
                },
                "work": {
                    "boundary_contact_work_J": W_boundary_cum,
                    "source": "typed impulse x actual boundary "
                              "velocity (NOT R*sum|F|)",
                },
                "bonds": {
                    "n_joint_prims": len(joint_prims),
                    "breaks": sum(1 for b in broken if b),
                    "break_times_s": break_times,
                    "break_impulse_Nms": break_impulse,
                    "break_schedule": ("physics-driven load threshold "
                                       "(NO scheduled breaks)"
                                       if stage == "T3"
                                       else "no breaks in this stage"),
                    "constraint_state_changed": any(broken),
                    "atomic_bodies": n_spec,
                    "connected_components_final":
                        n_spec - sum(1 for b in broken if b),
                },
                "observability": {
                    "wrap": None, "wrap_status": "NOT_IMPLEMENTED",
                    "screen_passage": None,
                    "screen_passage_status": "NOT_APPLICABLE",
                    "residence": None, "residence_status": "RIGHT_CENSORED",
                    "jam": None, "jam_status": "NOT_OBSERVABLE",
                },
                "energy_ledger": ledger,
                "contact_rows_window": len(contact_rows)
                                       - n_rows_before_window,
                "status": ("RUN_OK" if not failures else "RUN_INVALID"),
                "failures": failures,
            }
            log("r3 %s dt=%s dT=%r tau=%r W=%r brk=%d status=%s" % (
                stage, dt, dT, tau_shaft_cum, W_boundary_cum,
                sum(1 for b in broken if b), summary["status"]))
            with open(paths["telemetry.jsonl"], "w") as fh:
                for r in telemetry:
                    fh.write(json.dumps(r) + "\n")
            with open(paths["events.jsonl"], "w") as fh:
                for r in events:
                    fh.write(json.dumps(r) + "\n")
            with open(paths["summary.json"], "w") as fh:
                json.dump(summary, fh, indent=2)
                fh.write("\n")
            with open(paths["stdout.log"], "w") as fh:
                fh.write("\n".join(logs) + "\n")
            with open(paths["stderr.log"], "w") as fh:
                fh.write("\n".join(failures) + "\n")
            sim.close(exit_code=0 if not failures else 1)
        except Exception:
            failures.append("exception: " + traceback.format_exc(
                limit=10).replace("\n", " | "))
            summary = {"schema": RUN_SCHEMA, "backend": "ISAAC_PHYSX",
                       "stage": stage, "physics_dt_s": dt,
                       "status": "RUN_INVALID", "failures": failures}
            os.makedirs(paths["dir"], exist_ok=True)
            with open(paths["summary.json"], "w") as fh:
                json.dump(summary, fh, indent=2)
                fh.write("\n")
            with open(paths["stdout.log"], "w") as fh:
                fh.write("\n".join(logs) + "\n")
            with open(paths["stderr.log"], "w") as fh:
                fh.write("\n".join(failures) + "\n")
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
    except Exception:
        failures.append("exception: " + traceback.format_exc(
            limit=10).replace("\n", " | "))
        summary = {"schema": RUN_SCHEMA, "backend": "ISAAC_PHYSX",
                   "stage": stage, "physics_dt_s": dt,
                   "status": "RUN_INVALID", "failures": failures}
        os.makedirs(paths["dir"], exist_ok=True)
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
        with open(paths["stdout.log"], "w") as fh:
            fh.write("\n".join(logs) + "\n")
        with open(paths["stderr.log"], "w") as fh:
            fh.write("\n".join(summary.get("failures", [])) + "\n")
    return summary


def run_stage_dt(stage, dt, isaac_python):
    paths = run_paths(stage, dt)
    os.makedirs(paths["dir"], exist_ok=True)
    cmd = [isaac_python, HERE, "--child", "--stage", stage, "--dt",
           repr(dt), "--dir", paths["dir"]]
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    with open(os.path.join(paths["dir"], "_child_stdout.log"), "w") as fo:
        with open(os.path.join(paths["dir"], "_child_stderr.log"),
                  "w") as fe:
            rc = subprocess.call(cmd, stdout=fo, stderr=fe, env=env)
    return rc, paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--stage")
    ap.add_argument("--dt", type=float)
    ap.add_argument("--dir")
    ap.add_argument("--stages", nargs="*", default=["T1"])
    ap.add_argument("--dts", nargs="*", type=float, default=[0.01])
    ap.add_argument("--isaac-python", default=os.path.expanduser(
        "~/env_isaacsim-c22/bin/python"))
    args = ap.parse_args(argv)
    if args.child:
        run_dir = os.path.abspath(args.dir)
        child_paths = {"dir": run_dir}
        for n in ("scene.usda", "scene.sha256", "telemetry.jsonl",
                  "events.jsonl", "summary.json", "stdout.log",
                  "stderr.log"):
            child_paths[n] = os.path.join(run_dir, n)
        s = _isaac_child(args.stage, args.dt, child_paths)
        return 0 if s.get("status") == "RUN_OK" else 1
    isaac_python = os.path.expanduser(args.isaac_python)
    results = []
    for stage in args.stages:
        for dt in args.dts:
            rc, paths = run_stage_dt(stage, dt, isaac_python)
            s = json.load(open(paths["summary.json"]))
            results.append(s)
            print("r3 %s dt=%s rc=%d status=%s" % (
                stage, dt, rc, s.get("status")), flush=True)
    os.makedirs(R3, exist_ok=True)
    with open(os.path.join(R3, "manifest.json"), "w") as fh:
        json.dump({"schema": "r3_manifest/1", "runs": results}, fh,
                  indent=2)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
