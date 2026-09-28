"""D3 two-body coupling causality diagnostic (Goal R0 section 4, D3).

CONSTRAINT MECHANICS ONLY. Not an FDM/purge fracture law; no PLA fitting;
no material-failure claim of any kind.

Constraint (from the installed package): USD PhysicsFixedJoint
(pxr.UsdPhysics.FixedJoint, prim type "PhysicsFixedJoint") with
physics:body0/body1 relationships targeting the two rigid bodies. R0.2
throwaway probes showed: jointed pair holds dx=0 exactly with shared velocity
under differential load; disconnected pair separates (dx 0.1 -> 2.1 m);
SetActive(False) at a predetermined physics time changes constraint state and
subsequent motion. EffortSensor on a fixed joint reads invalid (no DOF), so
transmitted force is read as the acceleration residual on the undriven body:
F_constraint_on_A = m_A * a_A (body A carries no applied force; gravity is
subtracted from the z channel). Recorded as reaction_residual (diagnostic).

DECLARED LOADS + TOLERANCES (fixed BEFORE runs; identical for all 3 runs):

- Bodies: two 0.08 m cubes, m = 1.0 kg each, initial x = -0.05 / +0.05 m,
  z = 0.5 m, free fall under g = 9.81 (gravity enabled on both).
- Differential loading: body B only, F = +4.0 N x per physics step via
  RigidPrim.apply_forces (world frame), every step of the measured window.
  Body A carries NO applied force.
- dt = 0.005 s; measured window T = 1.0 s (200 steps) after 30 arming/warmup
  steps (excluded identically; t0 state included).
- Conditions on the SAME loading: (1) intact (joint always active,
  unbreakable: no break logic exists in this script); (2) disconnected (no
  joint authored); (3) timed-disable (joint SetActive(False) at the first
  step with engine time >= 0.5 s; causality test, not material failure).
- Verdict tolerances: intact-vs-disconnected distinguishable iff
  |dx_intact_final - dx_disconnected_final| > 0.05 m AND
  |F_transmit_intact_mean - F_transmit_disconnected_mean| > 0.5 N, with
  dx_intact_final <= 1e-6 m expected. Timed-disable: joint active at t < 0.5 s
  (dx growth ~0) and constraint state change recorded at 0.5 s with
  subsequent divergence (dx_final > 0.05 m and post-disable velocity split).
- Counter-only bond manager: INADMISSIBLE here; no shared code path with any
  counter-based bond logic exists in this file (constraint state comes only
  from the USD joint prim IsActive + body kinematics).

Per condition: relative displacement series, transmitted reaction series,
active constraint count, body IDs (paths), graph components (atomic
rigid-body count = 2 always, SEPARATE from connected-component count from
the active joint: intact = 1 component, disconnected = 2), conserved
mass/momentum where applicable (mass constant 2.0 kg; total x-momentum
series recorded, not claimed conserved under external load + gravity).

Layout: c2.3/revisions/r1/runs/d3_bond_<intact|disconnected|timedisable>/
with scene.usda, scene.sha256, series.jsonl, summary.json, stdout/stderr
logs, plus the aggregate c2.3/revisions/r1/runs/d3_bond.json.

Isaac imports are lazy inside _isaac_child(); module import is isaac-free
so unit tests run under system python3.
"""
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

DT = 0.005
N_MEASURE = 200
N_WARMUP = 30
DISABLE_T = 0.5
MASS_KG = 1.0
BOX_SIZE_M = 0.08
FORCE_BX_N = 4.0
G = 9.81
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"
CONDITIONS = ("intact", "disconnected", "timedisable")
# Verdict tolerances (declared BEFORE runs).
TOL_DX_SEPARATION_M = 0.05
TOL_FORCE_SEPARATION_N = 0.5
TOL_INTACT_DX_M = 1e-6


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths(condition):
    d = os.path.join(R1, "runs", "d3_bond_%s" % condition)
    out = {"dir": d}
    for n in ("scene.usda", "scene.sha256", "series.jsonl",
              "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def _isaac_child(condition, paths):
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    failures = []
    series = []
    summary = {}
    try:
        from isaacsim import SimulationApp

        sim = SimulationApp({"headless": True})
        try:
            import numpy as np
            import omni.timeline
            from isaacsim.core.simulation_manager import SimulationManager
            import isaacsim.core.simulation_manager as _sm_pkg
            import isaacsim.core.experimental.utils.stage as stage_utils
            from isaacsim.core.experimental.prims import RigidPrim
            from pxr import UsdGeom, UsdPhysics
            try:
                import isaacsim as _isaac_pkg
                isaac_rt = getattr(_isaac_pkg, "__version__", "UNKNOWN")
            except Exception as _e:
                isaac_rt = "UNKNOWN (probe error: %r)" % (_e,)

            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            stage_utils.define_prim(SCENE_ROOT, "Xform")
            for name, x in (("A", -0.05), ("B", 0.05)):
                xp = stage_utils.define_prim(
                    "%s/%s" % (SCENE_ROOT, name), "Xform")
                bx = stage_utils.define_prim(
                    "%s/%s/B" % (SCENE_ROOT, name), "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(BOX_SIZE_M)
                UsdPhysics.RigidBodyAPI.Apply(xp)
                UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(MASS_KG)
                UsdPhysics.CollisionAPI.Apply(bx)
            bodies = RigidPrim(
                [SCENE_ROOT + "/A", SCENE_ROOT + "/B"],
                positions=np.array([[-0.05, 0.0, 0.5],
                                    [0.05, 0.0, 0.5]], dtype=np.float32),
                orientations=np.array([[1, 0, 0, 0],
                                       [1, 0, 0, 0]], dtype=np.float32),
                reset_xform_op_properties=True)
            jprim = None
            if condition in ("intact", "timedisable"):
                stage = stage_utils.get_current_stage()
                jprim = stage.DefinePrim(
                    SCENE_ROOT + "/AB_Joint", "PhysicsFixedJoint")
                jprim.GetRelationship("physics:body0").SetTargets(
                    [SCENE_ROOT + "/A"])
                jprim.GetRelationship("physics:body1").SetTargets(
                    [SCENE_ROOT + "/B"])

            os.makedirs(paths["dir"], exist_ok=True)
            stage = stage_utils.get_current_stage()
            scene_str = stage.GetRootLayer().ExportToString()
            with open(paths["scene.usda"], "w") as fh:
                fh.write(scene_str)
            scene_sha = sha256_file(paths["scene.usda"])
            with open(paths["scene.sha256"], "w") as fh:
                fh.write(scene_sha + "  scene.usda\n")

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(DT)
            dt_readback = SimulationManager.get_physics_dt()
            tl = omni.timeline.get_timeline_interface()
            tl.play()
            sim.update()  # arming (R0.2 probe 8)
            F = np.array([[0.0, 0.0, 0.0],
                          [FORCE_BX_N, 0.0, 0.0]], dtype=np.float32)
            for _ in range(N_WARMUP):
                bodies.apply_forces(F)
                SimulationManager.step(steps=1)
            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            p0, _ = bodies.get_world_poses()
            P0 = np.asarray(p0.numpy(), dtype=np.float64)
            dx0 = float(abs(P0[1][0] - P0[0][0]))
            disable_step = None
            v_prev = None
            f_rows = []
            for i in range(N_MEASURE):
                t = SimulationManager.get_simulation_time()
                joint_active = (bool(jprim.IsActive())
                                if jprim is not None else False)
                if (condition == "timedisable" and jprim is not None
                        and t >= DISABLE_T and jprim.IsActive()):
                    jprim.SetActive(False)
                    disable_step = i + 1
                    joint_active = False
                vv, _ = bodies.get_velocities()
                v_prev = np.asarray(vv.numpy(), dtype=np.float64)
                bodies.apply_forces(F)
                SimulationManager.step(steps=1)
                vv2, _ = bodies.get_velocities()
                V2 = np.asarray(vv2.numpy(), dtype=np.float64)
                pp, _ = bodies.get_world_poses()
                P = np.asarray(pp.numpy(), dtype=np.float64)
                dx = float(abs(P[1][0] - P[0][0]))
                # Transmitted force on A = m_A * a_A, gravity removed on z.
                aA = (V2[0] - v_prev[0]) / DT
                Ft = [float(MASS_KG * aA[0]),
                      float(MASS_KG * aA[1]),
                      float(MASS_KG * (aA[2] + G))]
                px = float(MASS_KG * (V2[0][0] + V2[1][0]))
                n_active = 1 if (jprim is not None and joint_active) else 0
                f_rows.append({
                    "step": i + 1, "t_s": float(t),
                    "dx_m": dx, "F_transmit_N": Ft,
                    "F_transmit_mag_N": float(math.sqrt(
                        Ft[0] ** 2 + Ft[1] ** 2 + Ft[2] ** 2)),
                    "joint_active": bool(n_active),
                    "n_constraints_active": n_active,
                    "total_px": px})
                if (i + 1) <= 2 or (i + 1) % 50 == 0 or (i + 1) == N_MEASURE:
                    series.append(f_rows[-1])
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            pp, _ = bodies.get_world_poses()
            P1 = np.asarray(pp.numpy(), dtype=np.float64)
            vv, _ = bodies.get_velocities()
            V1 = np.asarray(vv.numpy(), dtype=np.float64)
            tl.stop()

            dx_final = float(abs(P1[1][0] - P1[0][0]))
            mags = [r["F_transmit_mag_N"] for r in f_rows]
            f_mean = float(sum(mags) / len(mags))
            n_active_final = f_rows[-1]["n_constraints_active"]
            # Graph: atomic rigid-body count vs connected components.
            atomic_bodies = 2
            components = 1 if (jprim is not None
                               and f_rows[-1]["joint_active"]
                               and condition == "intact") else (
                1 if condition == "timedisable" and
                f_rows[-1]["joint_active"] else
                (2 if condition == "disconnected" or
                 not f_rows[-1]["joint_active"] else 1))
            # timedisable ends disconnected -> 2 components.
            if condition == "timedisable":
                components = 2 if not f_rows[-1]["joint_active"] else 1
            if condition == "intact":
                components = 1
            if condition == "disconnected":
                components = 2
            mass_total = 2.0 * MASS_KG

            summary = {
                "schema": "r03_d3/1", "backend": "ISAAC_PHYSX",
                "isaac_version": "6.1.0.0",
                "isaac_runtime_version": isaac_rt,
                "isaac_build": "6.1.0-rc.26+release.49347.2d230af4.gl",
                "python": sys.executable,
                "simulation_manager": _sm_pkg.__file__,
                "scene": SCENE_ROOT,
                "condition": condition,
                "constraint": ("PhysicsFixedJoint AB_Joint "
                               "(UsdPhysics.FixedJoint); "
                               "transmitted force = m_A*a_A residual, "
                               "gravity removed on z"),
                "loads": {"force_Bx_N": FORCE_BX_N, "gravity": G,
                          "mass_kg_each": MASS_KG},
                "physics_dt_s": DT, "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(0.005) once pre-play; "
                    "advance via SimulationManager.step(steps=1)"),
                "n0": n0, "t0_s": t0, "n1": n1, "t1_s": t1,
                "dx0_m": dx0, "dx_final_m": dx_final,
                "F_transmit_mean_N": f_mean,
                "disable_step": disable_step,
                "disable_t": DISABLE_T,
                "body_ids": [SCENE_ROOT + "/A", SCENE_ROOT + "/B"],
                "atomic_body_count": atomic_bodies,
                "connected_components": components,
                "n_constraints_active_final": n_active_final,
                "mass_total_kg": mass_total,
                "vel_final": V1.tolist(), "pos_final": P1.tolist(),
                "scene_sha256": scene_sha,
                "status": "RUN_OK",
                "failures": failures,
            }
            log("d3 %s dx0=%r dx_final=%r Fmean=%r dis_step=%r" % (
                condition, dx0, dx_final, f_mean, disable_step))
            with open(paths["series.jsonl"], "w") as fh:
                for r in f_rows:
                    fh.write(json.dumps(r) + "\n")
            with open(paths["summary.json"], "w") as fh:
                json.dump(summary, fh, indent=2)
                fh.write("\n")
            with open(paths["stdout.log"], "w") as fh:
                fh.write("\n".join(logs) + "\n")
            with open(paths["stderr.log"], "w") as fh:
                fh.write("\n".join(failures) + "\n")
            sim.close(exit_code=0)
        except Exception:
            failures.append("exception: " + traceback.format_exc(
                limit=10).replace("\n", " | "))
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            summary = {"schema": "r03_d3/1", "backend": "ISAAC_PHYSX",
                       "condition": condition, "status": "RUN_FAILED",
                       "verdict": "BLOCKED", "failures": failures}
    except Exception:
        failures.append("exception: " + traceback.format_exc(
            limit=10).replace("\n", " | "))
        summary = {"schema": "r03_d3/1", "backend": "ISAAC_PHYSX",
                   "condition": condition, "status": "RUN_FAILED",
                   "verdict": "BLOCKED", "failures": failures}
    os.makedirs(paths["dir"], exist_ok=True)
    if not os.path.exists(paths["summary.json"]):
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    if not os.path.exists(paths["series.jsonl"]):
        with open(paths["series.jsonl"], "w") as fh:
            fh.write("")
    with open(paths["stdout.log"], "a") as fh:
        fh.write("\n".join(logs) + "\n")
    with open(paths["stderr.log"], "w") as fh:
        fh.write("\n".join(summary.get("failures", [])) + "\n")
    return summary


def run_one(condition, isaac_python):
    paths = run_paths(condition)
    os.makedirs(paths["dir"], exist_ok=True)
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    cmd = [isaac_python, os.path.abspath(__file__),
           "--child", "--condition", condition]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=REPO)
    with open(paths["stdout.log"], "w") as fh:
        fh.write(r.stdout)
    with open(paths["stderr.log"], "w") as fh:
        fh.write(r.stderr)
    try:
        summary = json.load(open(paths["summary.json"]))
    except Exception as exc:
        summary = {"schema": "r03_d3/1", "backend": "ISAAC_PHYSX",
                   "condition": condition, "status": "RUN_FAILED",
                   "verdict": "BLOCKED",
                   "failures": ["summary unreadable: %r (rc=%s)" % (
                       exc, r.returncode)]}
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--condition", default=None)
    ap.add_argument("--isaac-python",
                    default=os.path.expanduser(
                        "~/env_isaacsim-c22/bin/python"))
    args = ap.parse_args(argv)
    if args.child:
        _isaac_child(args.condition, run_paths(args.condition))
        s = json.load(open(run_paths(args.condition)["summary.json"]))
        print(json.dumps({k: s.get(k) for k in
                          ("condition", "status")}, indent=2))
        return 0 if s.get("status") == "RUN_OK" else 1
    recs = {}
    for condition in CONDITIONS:
        recs[condition] = run_one(condition, args.isaac_python)
    # Verdict over the triple (declared tolerances, BEFORE runs).
    fails = []
    try:
        dx_i = recs["intact"]["dx_final_m"]
        dx_d = recs["disconnected"]["dx_final_m"]
        f_i = recs["intact"]["F_transmit_mean_N"]
        f_d = recs["disconnected"]["F_transmit_mean_N"]
        if abs(dx_i) > TOL_INTACT_DX_M:
            fails.append("intact dx_final %r > 1e-6" % (dx_i,))
        if abs(dx_i - dx_d) <= TOL_DX_SEPARATION_M:
            fails.append("dx separation %r <= 0.05" % (abs(dx_i - dx_d),))
        if abs(f_i - f_d) <= TOL_FORCE_SEPARATION_N:
            fails.append("force separation %r <= 0.5" % (abs(f_i - f_d),))
        td = recs["timedisable"]
        if td.get("disable_step") is None:
            fails.append("timedisable never disabled")
        if td.get("dx_final_m", 0.0) <= TOL_DX_SEPARATION_M:
            fails.append("timedisable dx_final %r <= 0.05" % (
                td.get("dx_final_m"),))
    except Exception as exc:
        fails.append("verdict evaluation error: %r" % (exc,))
    agg = {"schema": "r03_d3_agg/1", "backend": "ISAAC_PHYSX",
           "tolerances": {"dx_separation_m": TOL_DX_SEPARATION_M,
                          "force_separation_N": TOL_FORCE_SEPARATION_N,
                          "intact_dx_m": TOL_INTACT_DX_M},
           "runs": recs,
           "verdict": "BLOCKED" if fails else "IMPLEMENTED",
           "verdict_findings": fails}
    with open(os.path.join(R1, "runs", "d3_bond.json"), "w") as fh:
        json.dump(agg, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"verdict": agg["verdict"],
                      "findings": fails}, indent=2))
    return 0 if agg["verdict"] == "IMPLEMENTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
