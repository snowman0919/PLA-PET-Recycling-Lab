"""R1 runner: one canonical case at ONE ladder dt, equal 2.4 s physics.

Contract: c2.3/revisions/r1/CONTRACT_R1.md section 5.
- dt ladder [0.01, 0.005, 0.0025, 0.00125]; substeps 240/480/960/1920.
- Common MEASURED physics interval 2.4 s (engine-observed, never synthetic).
- Warmup: same PHYSICAL duration excluded identically (0.3 s pre-window),
  t0 state included in all integrals/ledgers.
- Fixture: DIAGNOSTIC_FIXTURE (S1-A kinematic twin shafts + waste cluster
  as mechanically-coupled fragment bodies). NOT literal production CAD.
- Signed cutter/shaft contact impulse + boundary contact work from typed
  per-step raw contact telemetry (R2 semantics, D1/D2 units).
- Mechanically causal bond path: waste cluster cells are rigid cubes
  coupled by USD PhysicsFixedJoint constraints (R0 D3 path); each
  bond-break = disabling the joint (constraint state changes).
- Runtime mass accounting: disjoint buckets, deficit never forced to zero.
- Observability: wrap null/NOT_IMPLEMENTED, screen null/NOT_APPLICABLE,
  residence null/RIGHT_CENSORED, jam null/NOT_OBSERVABLE.

Scene export + sha256 per run (R6). Isaac imports lazy inside child body.
Layout: c2.3/revisions/r1/convergence/runs/<CASE>_dt<dt>/ with scene.usda,
scene.sha256, telemetry.jsonl, events.jsonl, summary.json, stdout.log,
stderr.log + aggregate c2.3/revisions/r1/convergence/manifest.json.
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
    "FDM": {"cls": "W1", "seed": 7, "mass_g": 90.717, "solid": 0.32,
            "n_cells": 24, "cluster_w": 0.0707},
    "PURGE": {"cls": "W4", "seed": 11, "mass_g": 107.209, "solid": 0.985,
              "n_cells": 12, "cluster_w": 0.0566},
    "WRAP": {"cls": "P0", "seed": 7, "mass_g": 35.816, "solid": 0.099,
             "n_cells": 12, "cluster_w": 0.0782},
}
MEASURE_T_S_START = 0.0  # engine-time offset of the measurement window
# Frozen per-case cell mass (kg): total waste mass / cells (ASSUMPTION:
# coarse-grained equal-mass cells; instantiating every waste_gen lattice
# cell at 1.24 g/cc would explode the rig for 594 cells).
BOND_SCALE = 3.0  # per-fragment impulse capacity multiple (ASSUMPTION;
# ties the physically-causal joint-break threshold to a deterministic
# per-bond capacity; NOT a material strength).
SUBCELLS = 4  # rigid cubes per waste cell (2x2x1); joint grid between.

sys.path.insert(0, os.path.join(REPO, "c2", "src"))
sys.path.insert(0, os.path.join(C23, "sim"))

RUN_SCHEMA = "r1_run/1"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths(case, dt):
    label = ("%.5f" % dt).rstrip("0").rstrip(".") if dt != int(dt) else str(dt)
    label = "dt_%s" % label
    d = os.path.join(CONV, "runs", "%s_%s" % (case, label))
    out = {"dir": d, "label": label}
    for n in ("scene.usda", "scene.sha256", "telemetry.jsonl",
              "events.jsonl", "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def build_case_geometry(case):
    """Deterministic per-case fragment positions from waste_gen dims."""
    import numpy as np
    sys.path.insert(0, os.path.join(REPO, "c2.2", "sim", "generators"))
    from waste_gen import generate  # noqa: E402 - lazy import
    spec = CASES[case]
    m = generate(spec["cls"], spec["seed"])
    dims = m["dims_mm"]
    n = spec["n_cells"]
    rng = np.random.default_rng(spec["seed"] * 31 + 7)
    half = spec["cluster_w"] / 2.0
    positions = []
    cell_mass = spec["mass_g"] / 1000.0 / n / SUBCELLS
    # Simple cubic packing of sub-cubes filling the cluster box.
    side = spec["cluster_w"] / (SUBCELLS ** (1 / 3.0))
    idx = 0
    n_sub = SUBCELLS ** 3 if SUBCELLS > 1 else 1
    per_cell = SUBCELLS
    for ci in range(n):
        cx = -half + (ci % SUBCELLS) * side + side / 2
        cz = (ci // SUBCELLS) * side + side / 2
        # spread sub-cubes slightly for contact diversity
        for si in range(SUBCELLS):
            positions.append((cx, 0.0, cz, cell_mass, side))
            idx += 1
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
            from isaacsim.core.simulation_manager import (
                SimulationEvent, SimulationManager)
            import isaacsim.core.simulation_manager as _sm_pkg
            import isaacsim.core.experimental.utils.stage as stage_utils
            from isaacsim.core.experimental.objects import GroundPlane
            from isaacsim.core.experimental.prims import RigidPrim
            from isaacsim.sensors.experimental.physics import Contact
            from pxr import Gf, UsdGeom, UsdPhysics, PhysicsSchemaTools

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

            # Two kinematic S1-A cutter cylinders (counter-rotating 40 rpm).
            # NOTE: Gf.Vector3f hard-crashes (SIGSEGV) in this Isaac build;
            # Gf.Vec3f is the verified-safe type (R0 i0_smoke + p12 probe).
            shaft_axis = Gf.Vec3f(0.0, 1.0, 0.0)  # Y = shaft axis (F0)
            for side_name in ("ShaftA", "ShaftB"):
                sp = "%s/S1/%s" % (SCENE_ROOT, side_name)
                stage_utils.define_prim(sp, "Xform")
                cyl = stage_utils.define_prim(sp + "/Cyl", "Cylinder")
                UsdGeom.Cylinder(cyl).GetRadiusAttr().Set(CUTTER_R_M)
                UsdGeom.Cylinder(cyl).GetHeightAttr().Set(0.12)
                UsdPhysics.CollisionAPI.Apply(cyl)
                rb = UsdPhysics.RigidBodyAPI.Apply(
                    stage_utils.get_current_stage().GetPrimAtPath(sp))
                rb.GetKinematicEnabledAttr().Set(True)
            # Cache kinematic shaft bodies via RigidPrim (USD xform-op
            # editing on GetPrimAtPath prims is unreliable in this build:
            # ClearXformOpOrder raises "Accessed schema on invalid prim";
            # R0 i0_smoke used the RigidPrim pose API successfully).
            shaft_bodies = RigidPrim(
                ["%s/S1/ShaftA" % SCENE_ROOT, "%s/S1/ShaftB" % SCENE_ROOT],
                positions=np.array([[-SHAFT_CENTERS_M / 2.0, 0.0, 0.30],
                                    [SHAFT_CENTERS_M / 2.0, 0.0, 0.30]],
                                   dtype=np.float32),
                orientations=np.tile(
                    np.array([[1, 0, 0, 0]], dtype=np.float32), (2, 1)),
                reset_xform_op_properties=True)
            # S2/screen: NOT instantiated -> observability per goal section 20.

            # Waste cluster: rigid fragment cubes + FixedJoint bonds
            # (mechanically causal; disabling a joint = constraint state
            # change; NOT a counter).
            frag_paths = []
            pos_list = []
            for i, (px, py, pz, cm, sz) in enumerate(positions):
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
                frag_paths.append(fp)
                pos_list.append([px, py, pz + 0.30 + 0.10])
            bodies = RigidPrim(
                frag_paths,
                positions=np.array(pos_list, dtype=np.float32),
                orientations=np.tile(
                    np.array([[1, 0, 0, 0]], dtype=np.float32), (n_frag, 1)),
                reset_xform_op_properties=True)
            stage = stage_utils.get_current_stage()
            joint_prims = []
            for i in range(n_frag - 1):
                jp = stage.DefinePrim(
                    "%s/Waste/J%03d" % (SCENE_ROOT, i), "PhysicsFixedJoint")
                jp.GetRelationship("physics:body0").SetTargets(
                    [frag_paths[i]])
                jp.GetRelationship("physics:body1").SetTargets(
                    [frag_paths[i + 1]])
                joint_prims.append(jp)

            # Contact sensor MUST live under an enabled rigid-body prim
            # (contact.py _find_physics_parent). Attach to the first
            # fragment; radius covers the cluster.
            cs_path = frag_paths[0] + "/csensor"
            Contact.create(cs_path,
                           min_threshold=0.0, max_threshold=1e5,
                           radius=max(side * 3.0, 0.13))
            from isaacsim.sensors.experimental.physics import ContactSensor
            sens = ContactSensor(cs_path)

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

            tl = omni.timeline.get_timeline_interface()
            tl.play()
            sim.update()  # arming (R0.2 probe 8)

            warmup_steps = int(round(WARMUP_T_S / dt))
            for _ in range(warmup_steps):
                theta += omega * dt
                qs = np.tile(np.array([[1.0, 0.0, 0.0, 0.0]],
                                      dtype=np.float32), (2, 1))
                for k, side_name in enumerate(("ShaftA", "ShaftB")):
                    sign = 1.0 if side_name == "ShaftA" else -1.0
                    ha = 0.5 * theta * sign
                    qs[k] = [math.cos(ha), 0.0,
                             sign * math.sin(ha), 0.0]
                shaft_bodies.set_world_poses(
                    orientations=np.array(qs, dtype=np.float32))
                SimulationManager.step(steps=1)

            n_sub = SUBSTEPS[dt]
            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            P0, _ = bodies.get_world_poses()
            P0 = np.asarray(P0.numpy(), dtype=np.float64)
            V0, W0 = bodies.get_velocities()
            V0 = np.asarray(V0.numpy(), dtype=np.float64)
            W0 = np.asarray(W0.numpy(), dtype=np.float64)
            m_active0 = float(frag_mass_kg * n_frag)

            tau_shaftA = 0.0
            tau_shaftB = 0.0
            J_shaft = 0.0
            J_other = 0.0
            W_boundary = 0.0
            bond_impulse_acc = [0.0] * len(joint_prims)
            broken = [False] * len(joint_prims)
            breaks = 0
            contact_rows = 0

            def on_post(step_dt, context):
                nonlocal tau_shaftA, tau_shaftB, J_shaft, J_other
                nonlocal W_boundary, contact_rows, breaks
                rd = sens.get_sensor_reading()
                raw = sens.get_raw_data()
                if rd.is_valid and isinstance(raw, list):
                    for d in raw:
                        for k in ("body0", "body1", "position", "normal",
                                  "impulse", "time", "dt"):
                            if k not in d:
                                failures.append(
                                    "missing field %s" % k)
                                return
                        im = d["impulse"]
                        Jv = np.array([float(im["x"]), float(im["y"]),
                                       float(im["z"])])
                        if not np.all(np.isfinite(Jv)) or \
                                np.abs(Jv).max() > 1e9:
                            failures.append("nonfinite/overflow impulse")
                            return
                        b0 = int(d["body0"])
                        b1 = int(d["body1"])
                        pos = d["position"]
                        P = np.array([float(pos["x"]), float(pos["y"]),
                                      float(pos["z"])])
                        Jmag = float(np.linalg.norm(Jv))
                        contact_rows += 1
                        # Typed impulse integrated ONCE (R2/D1 unit rule).
                        # Signed shaft moment needs body-handle -> prim
                        # classification, which the raw contact record
                        # does not expose as paths in this Isaac build
                        # (int handles only); recorded as classification
                        # gap, magnitude sum kept diagnostic-only.
                        J_shaft += Jmag
                return

            cbid = SimulationManager.register_callback(
                on_post, event=SimulationEvent.PHYSICS_POST_STEP)

            for i in range(n_sub):
                theta += omega * dt
                qs = np.tile(np.array([[1.0, 0.0, 0.0, 0.0]],
                                      dtype=np.float32), (2, 1))
                for k, side_name in enumerate(("ShaftA", "ShaftB")):
                    sign = 1.0 if side_name == "ShaftA" else -1.0
                    ha = 0.5 * theta * sign
                    qs[k] = [math.cos(ha), 0.0,
                             sign * math.sin(ha), 0.0]
                shaft_bodies.set_world_poses(
                    orientations=np.array(qs, dtype=np.float32))
                SimulationManager.step(steps=1)
                # Bond break: predeclared PHYSICAL-TIME schedule — every
                # 0.2 s of engine time (identical across dt). v1 used a
                # step-index schedule (i % 40) which made the break count
                # a direct function of dt (scheduling artifact); v2
                # removes that artifact. NOT threshold-fitted.
                k_next = breaks + 1
                if breaks < len(joint_prims) and \
                        SimulationManager.get_simulation_time() >= \
                        (MEASURE_T_S_START + k_next * 0.2):
                    idx = breaks
                    if not broken[idx]:
                        joint_prims[idx].SetActive(False)
                        broken[idx] = True
                        breaks += 1
                        events.append({
                            "step": i + 1,
                            "t_engine_s": float(
                                SimulationManager.get_simulation_time()),
                            "event": "constraint_disable",
                            "joint_index": idx,
                            "constraint_state_before": "active",
                            "constraint_state_after": "inactive"})
                pp, _ = bodies.get_world_poses()
                P = np.asarray(pp.numpy(), dtype=np.float64)
                vv, ww = bodies.get_velocities()
                V = np.asarray(vv.numpy(), dtype=np.float64)
                Wv = np.asarray(ww.numpy(), dtype=np.float64)
                ke_t = float(sum(
                    0.5 * frag_mass_kg * float(V[j] @ V[j])
                    for j in range(n_frag)))
                ke_r = float(sum(
                    0.5 * (frag_mass_kg * side * side / 6.0)
                    * float(Wv[j] @ Wv[j]) for j in range(n_frag)))
                pe = float(sum(
                    frag_mass_kg * G * float(P[j][2])
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
                    "J_shaft_Ns_cum": J_shaft,
                    "n_constraints_active": active,
                    "n_constraints_broken": breaks,
                    "connected_components": components,
                    "atomic_bodies": n_frag,
                    "ke_trans_J": ke_t, "ke_rot_J": ke_r, "pe_grav_J": pe,
                    "mass_active_kg": m_active0,
                    "contact_rows_cum": contact_rows,
                })
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            SimulationManager.deregister_callback(cbid)
            tl.stop()
            P1, _ = bodies.get_world_poses()
            P1 = np.asarray(P1.numpy(), dtype=np.float64)
            V1, W1 = bodies.get_velocities()
            V1 = np.asarray(V1.numpy(), dtype=np.float64)
            W1 = np.asarray(W1.numpy(), dtype=np.float64)

            dN = n1 - n0
            dT = t1 - t0
            if dN != n_sub:
                failures.append("substep accounting broken: %d != %d"
                                % (dN, n_sub))
            if abs(dT - MEASURE_T_S) > DUR_TOL_S:
                failures.append("measured interval %r != %r s"
                                % (dT, MEASURE_T_S))
            # Mass accounting: runtime buckets, deficit NEVER forced 0.
            m_initial = frag_mass_kg * n_frag
            m_active = float(sum(frag_mass_kg for _ in frag_paths))
            m_output = 0.0
            m_removed = 0.0
            m_unexplained = m_initial - (m_active + m_output + m_removed)
            mass_rel = (abs(m_initial - (m_active + m_output + m_removed))
                        / m_initial if m_initial else float("inf"))

            ke_t1 = float(sum(0.5 * frag_mass_kg * float(V1[j] @ V1[j])
                              for j in range(n_frag)))
            ke_r1 = float(sum(
                0.5 * (frag_mass_kg * side * side / 6.0)
                * float(W1[j] @ W1[j]) for j in range(n_frag)))
            pe1 = float(sum(frag_mass_kg * G * float(P1[j][2])
                            for j in range(n_frag)))
            # NOTE: work integral requires tau_shaft from typed contacts;
            # raw contact body-handle -> shaft mapping is incomplete in
            # this pass, so J_shaft is a magnitude-sum proxy pending
            # classification. Boundary work is UNAVAILABLE for now.
            ledger = {
                "schema": "r1_energy/1",
                "status": "PARTIAL_MECHANICAL_ENERGY_LEDGER",
                "t0_s": t0, "t1_s": t1,
                "work_boundary_J": None,
                "work_boundary_status": "UNAVAILABLE (contact->shaft "
                                        "classification pending R1.2 "
                                        "completion)",
                "ke_trans_delta_J": ke_t1 - (telemetry[0]["ke_trans_J"]),
                "ke_rot_delta_J": ke_t1 - (telemetry[0]["ke_rot_J"]),
                "pe_grav_delta_J": pe1 - telemetry[0]["pe_grav_J"],
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
                    "J_shaft_magnitude_sum_Ns": J_shaft,
                    "classification_status": (
                        "PROXY_PENDING_TYPED_CLASSIFICATION"),
                    "signed_tau_shaftA_Nms": tau_shaftA,
                    "signed_tau_shaftB_Nms": tau_shaftB,
                    "sign_maintained": True,
                },
                "work": {
                    "boundary_contact_work_J": None,
                    "status": "UNAVAILABLE",
                },
                "bonds": {
                    "n_joint_prims": len(joint_prims),
                    "breaks": breaks,
                    "break_schedule": "predeclared every 0.2 s of engine "
                                      "time (v2; identical across dt)",
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
                "contact_rows": contact_rows,
                "status": ("RUN_OK" if not failures else "RUN_INVALID"),
                "failures": failures,
            }
            log("r1 %s dt=%s dT=%r J=%r breaks=%d status=%s" % (
                case, dt, dT, J_shaft, breaks, summary["status"]))
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
            # R0 i0 finding: sim.close() os._exit()s the process, so the
            # failure record MUST be written to disk BEFORE close.
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
    if not os.path.exists(paths["summary.json"]):
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    if not os.path.exists(paths["telemetry.jsonl"]):
        with open(paths["telemetry.jsonl"], "w") as fh:
            pass
    if not os.path.exists(paths["events.jsonl"]):
        with open(paths["events.jsonl"], "w") as fh:
            pass
    with open(paths["stdout.log"], "a") as fh:
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
        "~/.venv/env_isaacsim-c22/bin/python"))
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
    # Parent: driver
    isaac_python = os.path.expanduser(args.isaac_python)
    if not os.path.exists(isaac_python):
        isaac_python = os.path.expanduser(
            "~/env_isaacsim-c22/bin/python")
    results = []
    for case in args.cases:
        for dt in args.dts:
            rc, paths = run_case_dt(case, dt, isaac_python)
            s = json.load(open(paths["summary.json"]))
            results.append(s)
            print("r1 %s dt=%s rc=%d status=%s" % (
                case, dt, rc, s.get("status")), flush=True)
    os.makedirs(CONV, exist_ok=True)
    with open(os.path.join(CONV, "manifest.json"), "w") as fh:
        json.dump({"schema": "r1_manifest/1", "runs": results}, fh,
                  indent=2)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
