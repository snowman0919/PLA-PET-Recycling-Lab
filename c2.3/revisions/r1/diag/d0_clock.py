"""D0 clock + 2.4 s horizon diagnostic (Goal R0 section 4, D0).

Minimal scene: ground plane + one falling rigid box under
/World/DIAGNOSTIC_FIXTURE (fixture name is diagnostic-only by contract).

Design (from installed-package probes, recorded in the run summary):

- Advance path is SimulationManager.step(steps=1): exactly one physics step
  per call (probe 4: sim.update() advances a render-driven 3-5 physics steps
  per call and MUST NOT be used as the clock).
- Sampling is inside a PHYSICS_POST_STEP callback registered via
  SimulationManager.register_callback: the callback fires once per physics
  step, so accumulation is exact (probe 3: rel err 3.1e-08 vs m*g*T; probe 6:
  callbacks fire under step() and the sensor cache refreshes).
- Warmup: 120 step() calls post-play with the callback already registered,
  captures discarded. t0 state included: n0/t0 recorded after warmup, before
  the measured window.
- Telemetry: one row per callback fire (dedup by physics step: ignore a fire
  whose get_num_physics_steps() equals the previous fire's).
- Kinematic commands: none (free-fall box only; no pose driving).
- Per dt in [0.01, 0.005, 0.0025, 0.00125]: substeps 240/480/960/1920 give a
  shared 2.4 s measured interval. Verdict per dt: observed duration == 2.4 s
  within 1e-6 AND substep count demonstrated, else a BLOCKED finding.

Layout per run: c2.3/revisions/r1/runs/d0_clock_dt_<dt>/ with scene.usda,
scene.sha256, frames.jsonl, summary.json, stdout.log, stderr.log, plus the
aggregate c2.3/revisions/r1/runs/d0_clock.json.

Isaac imports are lazy inside run_dt(); module import is isaac-free so unit
tests run under system python3.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import traceback

HERE = os.path.abspath(__file__)
R1 = os.path.dirname(os.path.dirname(HERE))
C23 = os.path.dirname(os.path.dirname(R1))
REPO = os.path.dirname(C23)

DT_LADDER = [0.01, 0.005, 0.0025, 0.00125]
SUBSTEPS = {0.01: 240, 0.005: 480, 0.0025: 960, 0.00125: 1920}
MEASURED_T = 2.4
DUR_TOL = 1e-6
WARMUP_STEPS = 120
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths(dt):
    d = os.path.join(R1, "runs", "d0_clock_dt_%s" % dt)
    out = {"dir": d}
    for n in ("scene.usda", "scene.sha256", "frames.jsonl",
              "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def _isaac_child(dt, paths):
    """Child body: runs under the Isaac venv python; one dt only."""
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    failures = []
    frames = []
    summary = {}
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
            from pxr import UsdGeom, UsdPhysics
            import isaacsim.sensors.experimental.physics.impl.contact_sensor as _cs_mod

            try:
                import isaacsim as _isaac_pkg
                isaac_rt = getattr(_isaac_pkg, "__version__", "UNKNOWN")
            except Exception as _e:
                isaac_rt = "UNKNOWN (probe error: %r)" % (_e,)

            n_sub = SUBSTEPS[dt]
            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            stage_utils.define_prim(SCENE_ROOT, "Xform")
            GroundPlane(SCENE_ROOT + "/Ground")
            xp = stage_utils.define_prim(SCENE_ROOT + "/Box", "Xform")
            bx = stage_utils.define_prim(SCENE_ROOT + "/Box/B", "Cube")
            UsdGeom.Cube(bx).GetSizeAttr().Set(0.05)
            UsdPhysics.RigidBodyAPI.Apply(xp)
            mapi = UsdPhysics.MassAPI.Apply(xp)
            mapi.GetMassAttr().Set(1.0)
            UsdPhysics.CollisionAPI.Apply(bx)
            box = RigidPrim(
                [SCENE_ROOT + "/Box"],
                positions=np.array([[0.0, 0.0, 0.5]], dtype=np.float32),
                orientations=np.array([[1, 0, 0, 0]], dtype=np.float32),
                reset_xform_op_properties=True)

            # Scene export BEFORE play (R6): executed-scene provenance.
            stage = stage_utils.get_current_stage()
            os.makedirs(paths["dir"], exist_ok=True)
            scene_str = stage.GetRootLayer().ExportToString()
            with open(paths["scene.usda"], "w") as fh:
                fh.write(scene_str)
            scene_sha = sha256_file(paths["scene.usda"])
            with open(paths["scene.sha256"], "w") as fh:
                fh.write(scene_sha + "  scene.usda\n")

            state = {"fires": []}

            def on_post(step_dt, context):
                n = SimulationManager.get_num_physics_steps()
                t = SimulationManager.get_simulation_time()
                # Dedup by physics step: ignore repeat fires at same step.
                if state["fires"] and state["fires"][-1]["n"] == n:
                    state["dup_ignored"] = state.get("dup_ignored", 0) + 1
                    return
                state["fires"].append(
                    {"n": int(n), "t": float(t),
                     "cb_dt": float(step_dt)})

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(dt)
            dt_readback = SimulationManager.get_physics_dt()
            cbid = SimulationManager.register_callback(
                on_post, event=SimulationEvent.PHYSICS_POST_STEP)
            tl = omni.timeline.get_timeline_interface()
            tl.play()
            # Arming: the first sim.update() after play runs the warm-start
            # (creates the simulation view that gates PHYSICS step
            # callbacks). Warmup step() calls alone never arm it, so without
            # this the callback fires zero times. One update() advances a
            # render-driven handful of physics steps; those steps are
            # excluded by the n0/t0 reset below.
            sim.update()
            if not SimulationManager._simulation_view_created:
                failures.append("simulation view not created after arming")
            # Warmup (excluded identically at every dt); t0 included below.
            for _ in range(WARMUP_STEPS):
                SimulationManager.step(steps=1)
            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            state["fires"] = []
            for _ in range(n_sub):
                SimulationManager.step(steps=1)
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            SimulationManager.deregister_callback(cbid)
            tl.stop()

            rows = state["fires"]
            dN = n1 - n0
            dT = t1 - t0
            ns = [r["n"] for r in rows]
            dense = (len(rows) == n_sub and dN == n_sub
                     and ns == list(range(n0 + 1, n1 + 1)))
            cb_dts = sorted(set(round(r["cb_dt"], 12) for r in rows))
            cb_ok = all(abs(v - dt) <= 1e-6 * max(1.0, abs(dt))
                        for v in cb_dts) and len(cb_dts) == 1
            mono = all(b >= a for a, b in zip(
                [r["t"] for r in rows], [r["t"] for r in rows][1:]))
            dur_ok = abs(dT - MEASURED_T) <= DUR_TOL
            if not dur_ok:
                failures.append(
                    "observed duration %r != 2.4 within 1e-6" % (dT,))
            if not dense:
                failures.append(
                    "substep count not demonstrated: rows=%d dN=%d "
                    "expect=%d" % (len(rows), dN, n_sub))
            if not cb_ok:
                failures.append("callback dt not uniform: %r" % (cb_dts,))
            if not mono:
                failures.append("engine time not monotone")

            for i, r in enumerate(rows):
                frames.append({
                    "callback_step_id": i + 1,
                    "physics_step": r["n"],
                    "engine_time_s": r["t"],
                    "callback_dt_s": r["cb_dt"]})

            summary = {
                "schema": "r02_d0/1", "backend": "ISAAC_PHYSX",
                "isaac_version": "6.1.0.0",
                "isaac_runtime_version": isaac_rt,
                "isaac_build": "6.1.0-rc.26+release.49347.2d230af4.gl",
                "python": sys.executable,
                "module_paths": {
                    "contact_sensor": _cs_mod.__file__,
                    "simulation_manager": _sm_pkg.__file__,
                },
                "scene": SCENE_ROOT,
                "physics_dt_s": dt,
                "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(%r) once pre-play; "
                    "advance via SimulationManager.step(steps=1), exactly "
                    "one physics step per call (sim.update() is "
                    "render-driven and not used)" % (dt,)),
                "substeps": n_sub,
                "warmup_steps": WARMUP_STEPS,
                "n0": n0, "t0_s": t0, "n1": n1, "t1_s": t1,
                "observed_duration_s": dT,
                "expected_duration_s": MEASURED_T,
                "duration_within_1e_6": bool(dur_ok),
                "substep_count_demonstrated": bool(dense),
                "callback_dt_values": cb_dts,
                "dup_fires_ignored": state.get("dup_ignored", 0),
                "scene_sha256": scene_sha,
                "status": "RUN_OK" if not failures else "RUN_FAILED",
                "verdict": ("IMPLEMENTED" if not failures
                            else "BLOCKED"),
                "failures": failures,
            }
            log("d0 dt=%s dT=%r dN=%d status=%s" % (
                dt, dT, dN, summary["status"]))
            with open(paths["frames.jsonl"], "w") as fh:
                for r in frames:
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
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            summary = {"schema": "r02_d0/1", "backend": "ISAAC_PHYSX",
                       "physics_dt_s": dt, "status": "RUN_FAILED",
                       "verdict": "BLOCKED", "failures": failures}
    except Exception:
        failures.append("exception: " + traceback.format_exc(
            limit=10).replace("\n", " | "))
        summary = {"schema": "r02_d0/1", "backend": "ISAAC_PHYSX",
                   "physics_dt_s": dt, "status": "RUN_FAILED",
                   "verdict": "BLOCKED", "failures": failures}
    os.makedirs(paths["dir"], exist_ok=True)
    if not os.path.exists(paths["summary.json"]):
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    if not os.path.exists(paths["frames.jsonl"]):
        with open(paths["frames.jsonl"], "w") as fh:
            for r in frames:
                fh.write(json.dumps(r) + "\n")
    with open(paths["stdout.log"], "a") as fh:
        fh.write("\n".join(logs) + "\n")
    with open(paths["stderr.log"], "w") as fh:
        fh.write("\n".join(summary.get("failures", [])) + "\n")
    return summary


def run_dt(dt, isaac_python):
    paths = run_paths(dt)
    os.makedirs(paths["dir"], exist_ok=True)
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    cmd = [isaac_python, os.path.abspath(__file__),
           "--child", "--dt", repr(float(dt))]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=REPO)
    with open(paths["stdout.log"], "w") as fh:
        fh.write(r.stdout)
    with open(paths["stderr.log"], "w") as fh:
        fh.write(r.stderr)
    try:
        summary = json.load(open(paths["summary.json"]))
    except Exception as exc:
        summary = {"schema": "r02_d0/1", "backend": "ISAAC_PHYSX",
                   "physics_dt_s": dt, "status": "RUN_FAILED",
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
    ap.add_argument("--dt", type=float, default=None)
    ap.add_argument("--isaac-python",
                    default=os.path.expanduser(
                        "~/env_isaacsim-c22/bin/python"))
    args = ap.parse_args(argv)
    if args.child:
        _isaac_child(args.dt, run_paths(args.dt))
        s = json.load(open(run_paths(args.dt)["summary.json"]))
        print(json.dumps({k: s.get(k) for k in
                          ("physics_dt_s", "status", "verdict")}, indent=2))
        return 0 if s.get("status") == "RUN_OK" else 1
    recs = {}
    for dt in DT_LADDER:
        recs[str(dt)] = run_dt(dt, args.isaac_python)
    agg = {"schema": "r02_d0_agg/1", "backend": "ISAAC_PHYSX",
           "measured_interval_s": MEASURED_T, "runs": recs,
           "verdict": ("IMPLEMENTED" if all(
               r.get("verdict") == "IMPLEMENTED"
               for r in recs.values()) else "BLOCKED")}
    with open(os.path.join(R1, "runs", "d0_clock.json"), "w") as fh:
        json.dump(agg, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: v.get("verdict") for k, v in recs.items()},
                     indent=2))
    return 0 if agg["verdict"] == "IMPLEMENTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
