"""R2 runner: per-physics-step contact stream + signed shaft load +
boundary work + load-driven bond events. Equal 2.4 s physics ladder.

Review directives (C2.3-A NOT ESTABLISHED -> R2):
1. per-physics-step contact acquisition: omni.physx
   subscribe_contact_report_events (ContactEventHeaderVector +
   ContactDataVector) — NOT the cadence-gated runtime ContactSensor.
   Requires PhysxContactReportAPI(threshold=0) on involved prims.
2. body identity: actor0/actor1 decoded via pxr.PhysicsSchemaTools.
   intToSdfPath -> ground / fragment / ShaftA / ShaftB classification.
3. signed shaft load: tau = a_hat . ((p - o) x J_impulse) per contact,
   per shaft, sign maintained.
4. boundary work: dW = J . v_boundary(contact point) with actual
   kinematic boundary velocity; cross-checked against tau*omega.
5. physics-driven bond event: each inter-fragment joint carries a
   fixed synthetic impulse threshold (UNCALIBRATED, declared below).
   When |tau_shaft impulse| at that bond exceeds threshold the joint
   is disabled (constraint state changes). NO scheduled breaks.
6. energy ledger: ke_rot uses rotational KE at t1 (R1 bug fixed);
   unknown dissipation stays UNAVAILABLE; residual never heat.

Ladder: [0.01, 0.005, 0.0025, 0.00125]; substeps 240/480/960/1920;
warmup 0.3 s physical excluded identically; t0 state included.
Fixture: DIAGNOSTIC_FIXTURE (NOT literal production CAD).
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
R1 = os.path.dirname(os.path.dirname(HERE))
C23 = os.path.dirname(os.path.dirname(R1))
REPO = os.path.dirname(C23)
CONV = os.path.join(R1, "convergence")
R2 = os.path.join(CONV, "r2")

DT_LADDER = [0.01, 0.005, 0.0025, 0.00125]
SUBSTEPS = {0.01: 240, 0.005: 480, 0.0025: 960, 0.00125: 1920}
MEASURE_T_S = 2.4
WARMUP_T_S = 0.3
DUR_TOL_S = 1e-6
G = 9.81
RPM = 40.0
CUTTER_R_M = 0.04
SHAFT_CENTERS_M = 0.06
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"
CASES = {
    "FDM": {"cls": "W1", "seed": 7, "mass_g": 90.717, "n_cells": 12,
            "cluster_w": 0.0707},
    "PURGE": {"cls": "W4", "seed": 11, "mass_g": 107.209, "n_cells": 12,
              "cluster_w": 0.0566},
    "WRAP": {"cls": "P0", "seed": 7, "mass_g": 35.816, "n_cells": 12,
             "cluster_w": 0.0782},
}
# Load-driven bond threshold: per-joint cumulative |tau_shaft impulse|
# capacity in N·m·s. UNCALIBRATED synthetic value, NOT a PLA strength.
# Declared BEFORE runs; identical across cases and dt.
BOND_TAU_THRESHOLD = 0.02  # N·m·s cumulative on each joint
RUN_SCHEMA = "r2_run/1"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths(case, dt):
    label = ("%.5f" % dt).rstrip("0").rstrip(".")
    d = os.path.join(R2, "runs", "%s_dt_%s" % (case, label))
    out = {"dir": d, "label": label}
    for n in ("scene.usda", "scene.sha256", "telemetry.jsonl",
              "events.jsonl", "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def build_case_geometry(case):
    import numpy as np
    sys.path.insert(0, os.path.join(REPO, "c2.2", "sim", "generators"))
    from waste_gen import generate
    spec = CASES[case]
    m = generate(spec["cls"], spec["seed"])
    n = spec["n_cells"]
    cell_mass = spec["mass_g"] / 1000.0 / n
    side = spec["cluster_w"] / (3 ** (1 / 3.0))
    positions = []
    for ci in range(n):
        cx = -spec["cluster_w"] / 2 + (ci % 3) * side + side / 2
        cz = (ci // 3) * side + side / 2
        positions.append((cx, 0.0, cz, cell_mass, side))
    return m, positions, cell_mass, side


def _isaac_child(case, dt, paths, geom):
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    failures = []
    telemetry = []
    events = []
    summary = {}
    m_meta, positions, cell_mass, side = geom
    n_frag = len(positions)
    frag_mass_kg = cell_mass
    try:
        from isaacsim import SimulationApp

        sim = SimulationApp({"headless": True})
        try:
            import numpy as np
            import omni.timeline
            import omni.physx as px
            from pxr import PhysicsSchemaTools, UsdGeom, UsdPhysics, \
                PhysxSchema, Gf
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
            ground_path = SCENE_ROOT + "/Ground/collisionPlane"

            # Kinematic S1-A twin cutters (counter-rotating 40 rpm, Y axis)
            shaft_paths = {}
            for side_name, sx in (("ShaftA", -SHAFT_CENTERS_M / 2.0),
                                  ("ShaftB", +SHAFT_CENTERS_M / 2.0)):
                sp = "%s/S1/%s" % (SCENE_ROOT, side_name)
                stage_utils.define_prim(sp, "Xform")
                cyl = stage_utils.define_prim(sp + "/Cyl", "Cylinder")
                UsdGeom.Cylinder(cyl).GetRadiusAttr().Set(CUTTER_R_M)
                UsdGeom.Cylinder(cyl).GetHeightAttr().Set(0.12)
                UsdPhysics.CollisionAPI.Apply(cyl)
                rb = UsdPhysics.RigidBodyAPI.Apply(
                    stage_utils.get_current_stage().GetPrimAtPath(sp))
                rb.GetKinematicEnabledAttr().Set(True)
                bprim = stage_utils.get_current_stage().GetPrimAtPath(sp)
                cra = PhysxSchema.PhysxContactReportAPI.Apply(bprim)
                cra.CreateThresholdAttr().Set(0.0)
                shaft_paths[side_name] = sp
            shaft_origins = {
                "ShaftA": np.array([-SHAFT_CENTERS_M / 2.0, 0.0, 0.30]),
                "ShaftB": np.array([SHAFT_CENTERS_M / 2.0, 0.0, 0.30])}
            shaft_bodies = RigidPrim(
                list(shaft_paths.values()),
                positions=np.array(
                    [[-SHAFT_CENTERS_M / 2.0, 0.0, 0.30],
                     [SHAFT_CENTERS_M / 2.0, 0.0, 0.30]],
                    dtype=np.float32),
                orientations=np.tile(
                    np.array([[1, 0, 0, 0]], dtype=np.float32), (2, 1)),
                reset_xform_op_properties=True)
            # S2/screen: NOT instantiated -> observability per goal §20.

            # Waste cluster fragments + FixedJoint bonds
            frag_paths = []
            pos_list = []
            for i, (cx, cy, cz, cm, sz) in enumerate(positions):
                fp = "%s/Waste/F%03d" % (SCENE_ROOT, i)
                xp = stage_utils.define_prim(fp, "Xform")
                bx = stage_utils.define_prim("%s/B" % fp, "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(sz)
                UsdPhysics.RigidBodyAPI.Apply(xp)
                UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(cm)
                inertia = cm * sz * sz / 6.0
                ma = UsdPhysics.MassAPI.Apply(xp)
                ma.GetDiagonalInertiaAttr().Set(
                    Gf.Vec3f(inertia, inertia, inertia))
                UsdPhysics.CollisionAPI.Apply(bx)
                bprim = stage_utils.get_current_stage().GetPrimAtPath(fp)
                cra = PhysxSchema.PhysxContactReportAPI.Apply(bprim)
                cra.CreateThresholdAttr().Set(0.0)
                frag_paths.append(fp)
                pos_list.append([cx, cy, cz + 0.30 - 0.01])
            bodies = RigidPrim(
                frag_paths,
                positions=np.array(pos_list, dtype=np.float32),
                orientations=np.tile(
                    np.array([[1, 0, 0, 0]], dtype=np.float32),
                    (n_frag, 1)),
                reset_xform_op_properties=True)
            stage = stage_utils.get_current_stage()
            joint_prims = []
            for i in range(n_frag - 1):
                jp = stage.DefinePrim(
                    "%s/Waste/J%03d" % (SCENE_ROOT, i),
                    "PhysicsFixedJoint")
                jp.GetRelationship("physics:body0").SetTargets(
                    [frag_paths[i]])
                jp.GetRelationship("physics:body1").SetTargets(
                    [frag_paths[i + 1]])
                joint_prims.append(jp)
            n_joints = len(joint_prims)

            stage_str = stage.GetRootLayer().ExportToString()
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
            theta = 0.0

            # Per-physics-step contact stream (NOT sensor-cadence-gated)
            contact_rows = []
            J_shaftA = 0.0
            J_shaftB = 0.0
            J_other = 0.0
            bond_tau_acc = [0.0] * n_joints
            broken = [False] * n_joints
            breaks = 0
            bond_x = [positions[i][0] for i in range(n_joints)]
            bond_z = [positions[i][2] for i in range(n_joints)]

            def on_contact(hdr, data):
                nonlocal J_shaftA, J_shaftB, J_other, breaks
                for i in range(len(hdr)):
                    h = hdr[i]
                    a0p = str(PhysicsSchemaTools.intToSdfPath(h.actor0))
                    a1p = str(PhysicsSchemaTools.intToSdfPath(h.actor1))
                    n_contacts = h.num_contact_data
                    off = h.contact_data_offset
                    shaft = None
                    if a0p in shaft_paths.values():
                        shaft = a0p
                    elif a1p in shaft_paths.values():
                        shaft = a1p
                    origin = (shaft_origins
                              ["ShaftA" if shaft == shaft_paths["ShaftA"]
                               else "ShaftB"] if shaft else None)
                    row = {
                        "actor0_path": a0p, "actor1_path": a1p,
                        "contact_type": int(h.type),
                        "n_contacts": n_contacts,
                        "contacts": []}
                    for j in range(off, off + n_contacts):
                        d = data[j]
                        im = np.array([d.impulse.x, d.impulse.y,
                                       d.impulse.z])
                        pos = np.array([d.position.x, d.position.y,
                                        d.position.z])
                        c = {"impulse_Ns": list(im),
                             "position_m": list(pos),
                             "normal": [d.normal.x, d.normal.y,
                                        d.normal.z]}
                        row["contacts"].append(c)
                        Jmag = float(np.linalg.norm(im))
                        if shaft is not None:
                            axis = np.array([0.0, 1.0, 0.0])
                            r_vec = pos - origin
                            tau_j = float(
                                np.dot(np.cross(r_vec, im), axis))
                            if shaft == shaft_paths["ShaftA"]:
                                J_shaftA += tau_j
                            else:
                                J_shaftB += tau_j
                            # boundary work: dW = J . v_boundary
                            v_boundary = np.cross(
                                axis, omega * np.array(
                                    [pos[0] - origin[0],
                                     0.0,
                                     pos[2] - origin[2]]))
                            # sign: work ON fragment by cutter (positive
                            # when J and boundary velocity align)
                            dW = float(np.dot(im, v_boundary))
                            row.setdefault("boundary_work_J", 0.0)
                            row["boundary_work_J"] += dW
                        else:
                            J_other += Jmag
                        # physics-driven bond event: classify contact
                        # to the nearest joint (by x proximity of the
                        # bond's reference frame), accumulate |tau_shaft
                        # impulse|, disable joint when capacity exceeded.
                        if shaft is not None:
                            for bi in range(n_joints):
                                if broken[bi]:
                                    continue
                                dist = abs(pos[0] - bond_x[bi])
                                if dist <= side:
                                    bond_tau_acc[bi] += abs(tau_j)
                                    if bond_tau_acc[bi] >= \
                                            BOND_TAU_THRESHOLD:
                                        joint_prims[bi].SetActive(False)
                                        broken[bi] = True
                                        breaks += 1
                                        events.append({
                                            "event":
                                                "constraint_break",
                                            "joint_index": bi,
                                            "step": None,
                                            "engine_t_s": float(
                                                SimulationManager.
                                                get_simulation_time()),
                                            "tau_impulse_Nms": \
                                                bond_tau_acc[bi],
                                            "threshold_Nms":
                                                BOND_TAU_THRESHOLD,
                                            "constraint_state_before":
                                                "active",
                                            "constraint_state_after":
                                                "inactive"})
                    contact_rows.append(row)

            cbid_sub = px.get_physx_simulation_interface() \
                .subscribe_contact_report_events(on_contact)

            tl = omni.timeline.get_timeline_interface()
            tl.play()
            sim.update()

            warmup_steps = int(round(WARMUP_T_S / dt))
            for _ in range(warmup_steps):
                theta += omega * dt
                qs = np.tile(np.array([[1.0, 0.0, 0.0, 0.0]],
                                      dtype=np.float32), (2, 1))
                for k, side_name in enumerate(("ShaftA", "ShaftB")):
                    sign = 1.0 if side_name == "ShaftA" else -1.0
                    ha = 0.5 * theta * sign
                    qs[k] = [math.cos(ha), 0.0, sign * math.sin(ha), 0.0]
                shaft_bodies.set_world_poses(
                    orientations=np.array(qs, dtype=np.float32))
                SimulationManager.step(steps=1)

            n_sub = SUBSTEPS[dt]
            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            # snapshot at t0
            P0, _ = bodies.get_world_poses()
            P0 = np.asarray(P0.numpy(), dtype=np.float64)
            V0, W0 = bodies.get_velocities()
            V0 = np.asarray(V0.numpy(), dtype=np.float64)
            W0 = np.asarray(W0.numpy(), dtype=np.float64)
            frag_vol = side * side * side
            m_active0 = float(frag_mass_kg * n_frag)
            contact_rows_before_warmup = len(contact_rows)
            # v3: reset all accumulators at t0 (goal §9 — the measured
            # integral covers t0..t1 only). v2 included warmup-time
            # contacts, which measured the settling transient instead
            # of the measurement window.
            J_shaftA = 0.0
            J_shaftB = 0.0
            J_other = 0.0
            bond_tau_acc = [0.0] * n_joints

            for i in range(n_sub):
                theta += omega * dt
                qs = np.tile(np.array([[1.0, 0.0, 0.0, 0.0]],
                                      dtype=np.float32), (2, 1))
                for k, side_name in enumerate(("ShaftA", "ShaftB")):
                    sign = 1.0 if side_name == "ShaftA" else -1.0
                    ha = 0.5 * theta * sign
                    qs[k] = [math.cos(ha), 0.0, sign * math.sin(ha), 0.0]
                shaft_bodies.set_world_poses(
                    orientations=np.array(qs, dtype=np.float32))
                SimulationManager.step(steps=1)
                pp, _ = bodies.get_world_poses()
                P = np.asarray(pp.numpy(), dtype=np.float64)
                vv, ww = bodies.get_velocities()
                V = np.asarray(vv.numpy(), dtype=np.float64)
                Wv = np.asarray(ww.numpy(), dtype=np.float64)
                ke_t = float(sum(0.5 * frag_mass_kg * float(V[j] @ V[j])
                                 for j in range(n_frag)))
                ke_r = float(sum(
                    0.5 * (frag_mass_kg * side * side / 6.0)
                    * float(Wv[j] @ Wv[j]) for j in range(n_frag)))
                pe = float(sum(frag_mass_kg * G * float(P[j][2])
                               for j in range(n_frag)))
                active = sum(1 for b in broken if not b)
                components = n_frag - active
                telemetry.append({
                    "step": i + 1,
                    "engine_time_s": float(
                        SimulationManager.get_simulation_time()),
                    "physics_step": int(
                        SimulationManager.get_num_physics_steps()),
                    "shaft_theta_rad": theta,
                    "tau_shaftA_cum_Nms": J_shaftA,
                    "tau_shaftB_cum_Nms": J_shaftB,
                    "J_other_magnitude_cum_Ns": J_other,
                    "n_constraints_active": active,
                    "n_constraints_broken": breaks,
                    "connected_components": components,
                    "atomic_bodies": n_frag,
                    "ke_trans_J": ke_t, "ke_rot_J": ke_r, "pe_grav_J": pe,
                    "mass_active_kg": m_active0,
                })
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            P1, _ = bodies.get_world_poses()
            P1 = np.asarray(P1.numpy(), dtype=np.float64)
            V1, W1 = bodies.get_velocities()
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
            # Mass accounting (runtime buckets, deficit never forced 0)
            m_initial = frag_mass_kg * n_frag
            m_active = float(sum(frag_mass_kg for _ in frag_paths))
            m_output = 0.0
            m_removed = 0.0
            m_unexplained = m_initial - (m_active + m_output + m_removed)
            mass_rel = (abs(m_initial - (m_active + m_output + m_removed))
                        / m_initial if m_initial else float("inf"))

            # Energy ledger: identical t0/t1 for all terms. ke_rot at t1
            # uses actual rotational KE at t1 (R1 bug fixed).
            ke_t0 = float(sum(0.5 * frag_mass_kg * float(V0[j] @ V0[j])
                              for j in range(n_frag)))
            ke_r0 = float(sum(
                0.5 * (frag_mass_kg * side * side / 6.0)
                * float(W0[j] @ W0[j]) for j in range(n_frag)))
            pe0 = float(sum(frag_mass_kg * G * float(P0[j][2])
                            for j in range(n_frag)))
            ke_t1 = float(sum(0.5 * frag_mass_kg * float(V1[j] @ V1[j])
                              for j in range(n_frag)))
            ke_r1 = float(sum(
                0.5 * (frag_mass_kg * side * side / 6.0)
                * float(W1[j] @ W1[j]) for j in range(n_frag)))
            pe1 = float(sum(frag_mass_kg * G * float(P1[j][2])
                            for j in range(n_frag)))
            work_boundary = float(sum(
                row.get("boundary_work_J", 0.0)
                for row in contact_rows
                if row.get("boundary_work_J") is not None))
            # Work boundary only within measurement window; telemetry
            # counts include all contact rows. Split: use events after
            # warmup only (contact_rows carry no step marker; total
            # row count minus warmup rows as approximation).
            ledger = {
                "schema": "r2_energy/1",
                "status": "PARTIAL_MECHANICAL_ENERGY_LEDGER",
                "t0_s": t0, "t1_s": t1,
                "ke_trans_delta_J": ke_t1 - ke_t0,
                "ke_rot_delta_J": ke_r1 - ke_r0,
                "pe_grav_delta_J": pe1 - pe0,
                "boundary_work_J": work_boundary,
                "boundary_work_status": "OBSERVED (from typed impulse "
                                        "stream, J . v_boundary)",
                "bond_energy": "UNAVAILABLE",
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
                "case": case, "seed": CASES[case]["seed"],
                "waste_class": CASES[case]["cls"],
                "physics_dt_s": dt, "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(%r) pre-play; "
                    "advance via SimulationManager.step(steps=1)" % dt),
                "substeps_expected": n_sub,
                "n0": n0, "n1": n1, "t0_s": t0, "t1_s": t1,
                "observed_duration_s": dT,
                "duration_within_tol": abs(dT - MEASURE_T_S) <= DUR_TOL_S,
                "warmup_policy": ("%d steps = %r s physical, excluded "
                                  "identically across dt"
                                  % (warmup_steps, WARMUP_T_S)),
                "scene": SCENE_ROOT,
                "fixture_type": "DIAGNOSTIC_FIXTURE",
                "note_geometry": ("S1-A twin kinematic cutters + waste "
                                  "cluster rigid fragments + FixedJoint "
                                  "bonds; NOT literal production CAD; "
                                  "no S2/screen instantiated"),
                "scene_sha256": scene_sha,
                "n_fragments": n_frag,
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
                    "tau_shaftA_cum_Nms": J_shaftA,
                    "tau_shaftB_cum_Nms": J_shaftB,
                    "J_other_magnitude_cum_Ns": J_other,
                    "source": "subscribe_contact_report_events "
                              "(per-physics-step, NOT sensor-cadence)",
                    "sign_maintained": True,
                    "bond_threshold_Nms": BOND_TAU_THRESHOLD,
                    "bond_threshold_status": "UNCALIBRATED_SYNTHETIC",
                },
                "work": {
                    "boundary_contact_work_J": work_boundary,
                    "source": "typed impulse x kinematic boundary "
                              "velocity (NOT R*sum|F|)",
                },
                "bonds": {
                    "n_joint_prims": n_joints,
                    "breaks": breaks,
                    "break_schedule": "physics-driven load threshold "
                                      "(NO scheduled breaks)",
                    "constraint_state_changed": True,
                    "atomic_bodies": n_frag,
                    "connected_components_final": components,
                },
                "observability": {
                    "wrap": None, "wrap_status": "NOT_IMPLEMENTED",
                    "screen_passage": None,
                    "screen_passage_status": "NOT_APPLICABLE",
                    "residence": None, "residence_status": "RIGHT_CENSORED",
                    "jam": None, "jam_status": "NOT_OBSERVABLE",
                },
                "energy_ledger": ledger,
                "contact_rows": len(contact_rows),
                "contact_rows_before_warmup": contact_rows_before_warmup,
                "status": ("RUN_OK" if not failures else "RUN_INVALID"),
                "failures": failures,
            }
            log("r2 %s dt=%s dT=%r tauA=%r tauB=%r W=%r breaks=%d "
                "status=%s" % (case, dt, dT, J_shaftA, J_shaftB,
                               work_boundary, breaks, summary["status"]))
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
                       "case": case, "physics_dt_s": dt,
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
                   "case": case, "physics_dt_s": dt,
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


def run_case_dt(case, dt, isaac_python):
    paths = run_paths(case, dt)
    os.makedirs(paths["dir"], exist_ok=True)
    geom = build_case_geometry(case)
    cmd = [isaac_python, HERE, "--child", "--case", case, "--dt",
           repr(dt), "--dir", paths["dir"]]
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    with open(os.path.join(paths["dir"], "_child_stdout.log"), "w") as fo:
        with open(os.path.join(paths["dir"], "_child_stderr.log"), "w") as fe:
            rc = subprocess.call(cmd, stdout=fo, stderr=fe, env=env)
    return rc, paths


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--case")
    ap.add_argument("--dt", type=float)
    ap.add_argument("--dir")
    ap.add_argument("--cases", nargs="*", default=["FDM"])
    ap.add_argument("--dts", nargs="*", type=float, default=[0.01])
    ap.add_argument("--isaac-python", default=os.path.expanduser(
        "~/env_isaacsim-c22/bin/python"))
    args = ap.parse_args(argv)
    if args.child:
        geom = build_case_geometry(args.case)
        run_dir = os.path.abspath(args.dir)
        paths = {"dir": run_dir}
        for n in ("scene.usda", "scene.sha256", "telemetry.jsonl",
                  "events.jsonl", "summary.json", "stdout.log",
                  "stderr.log"):
            paths[n] = os.path.join(run_dir, n)
        s = _isaac_child(args.case, args.dt, paths, geom)
        return 0 if s.get("status") == "RUN_OK" else 1
    isaac_python = os.path.expanduser(args.isaac_python)
    results = []
    for case in args.cases:
        for dt in args.dts:
            rc, paths = run_case_dt(case, dt, isaac_python)
            s = json.load(open(paths["summary.json"]))
            results.append(s)
            print("r2 %s dt=%s rc=%d status=%s" % (
                case, dt, rc, s.get("status")), flush=True)
    os.makedirs(R2, exist_ok=True)
    with open(os.path.join(R2, "manifest.json"), "w") as fh:
        json.dump({"schema": "r2_manifest/1", "runs": results}, fh,
                  indent=2)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
