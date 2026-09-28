"""D1 contact units + isolation diagnostic (Goal R0 section 4, D1).

Exact installed API (isaacsim 6.1.0.0, ext
isaacsim.sensors.experimental.physics-3.3.0):

- Authoring: isaacsim.sensors.experimental.physics.Contact (+ .create(path,
  min_threshold, max_threshold, radius)); runtime:
  isaacsim.sensors.experimental.physics.ContactSensor(path).
  Source: .../sensors/experimental/physics/impl/contact.py,
  .../impl/contact_sensor.py, .../impl/common.py.
- Runtime data comes from the physics tensor API (IRigidContactView); the
  sensor must sit under an enabled rigid-body ancestor (docs/Overview.md).
- ContactSensorReading: value [scalar float, Newtons], time [s], is_valid,
  in_contact. Frame: in_contact / force [scalar N] / time / physics_step /
  number_of_contacts, plus raw "contacts" list when enabled via
  add_raw_contact_data_to_frame().
- Raw contact dicts (C++ get_raw_contacts, keys asserted in the installed
  test_contact_sensor_cpp_interface.py): body0, body1 (int handles ->
  PhysicsSchemaTools.intToSdfPath), position {x,y,z} [m], normal {x,y,z}
  [unit], impulse {x,y,z} [N s vector], time [s], dt [s].
- Unit rule (probes 1-3,6): impulse entries are VECTORS in N s (NOT forces):
  J[N s] entries are summed ONCE (|J| per contact); F[N] = |J| / dt_contact,
  summed as F*dt. Never multiply an impulse entry by dt a second time.
  Settled-box finding: per-update reads DOUBLE-COUNT (N updates advance
  ~N*dt_ratio physics steps while get_raw_data returns the latest step
  buffer); exact accounting requires per-physics-step callback capture.
  Friction coverage: raw impulse vectors carry the full contact impulse
  (normal + tangential components resolved by PhysX); the scalar
  reading.value/frame force is the magnitude aggregate. Sign: impulse on the
  sensor body points along the contact resolution on that body; body0/body1
  identify the pair; no per-body sign split is exposed -> torque/work use
  action-reaction explicitly (see d2_torque.py). Duplicates: repeated fires
  at the same physics step are deduped by step id.

Controls (equal interval T = 1.0 s measured, per-step callback capture):

- Stationary supported box of known mass m: support impulse vs m*g*T within
  5% after settling. Sensor failure / invalid / stale / missing-field /
  overflow readings INVALIDATE the diagnostic (never except-to-zero):
  any invalid/stale/missing/overflow sample aborts the run as BLOCKED.
- No-contact control (box held far above ground, no settle possible):
  accumulate |impulse| over the same window; must read ~0 (<= 1e-6 N s).

Ground forces are NEVER labeled cutter forces: outputs use support_* names.

Layout per control: c2.3/revisions/r1/runs/d1_contact_<support|nocontact>_dt_<dt>/
with scene.usda, scene.sha256, samples.jsonl, summary.json, stdout/stderr logs,
plus the aggregate c2.3/revisions/r1/runs/d1_contact.json.
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

DT_LADDER = [0.01, 0.005, 0.0025, 0.00125]
SETTLE_STEPS = 300
MEASURE_T = 1.0
SUPPORT_TOL = 0.05
NOCONTACT_TOL_Ns = 1e-6
G = 9.81
MASS_KG = 2.0
BOX_SIZE_M = 0.05
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths(control, dt):
    d = os.path.join(R1, "runs", "d1_contact_%s_dt_%s" % (control, dt))
    out = {"dir": d}
    for n in ("scene.usda", "scene.sha256", "samples.jsonl",
              "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def _isaac_child(control, dt, paths):
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    failures = []
    samples = []
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
            from isaacsim.sensors.experimental.physics import (
                Contact, ContactSensor)
            import isaacsim.sensors.experimental.physics.impl.contact_sensor as _cs_mod
            import isaacsim.sensors.experimental.physics.impl.contact as _c_mod
            import isaacsim.sensors.experimental.physics.impl.common as _common_mod
            try:
                import isaacsim as _isaac_pkg
                isaac_rt = getattr(_isaac_pkg, "__version__", "UNKNOWN")
            except Exception as _e:
                isaac_rt = "UNKNOWN (probe error: %r)" % (_e,)

            z0 = 0.030 if control == "support" else 8.0
            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            stage_utils.define_prim(SCENE_ROOT, "Xform")
            GroundPlane(SCENE_ROOT + "/Ground")
            xp = stage_utils.define_prim(SCENE_ROOT + "/Box", "Xform")
            bx = stage_utils.define_prim(SCENE_ROOT + "/Box/B", "Cube")
            from pxr import UsdGeom, UsdPhysics
            UsdGeom.Cube(bx).GetSizeAttr().Set(BOX_SIZE_M)
            UsdPhysics.RigidBodyAPI.Apply(xp)
            UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(MASS_KG)
            UsdPhysics.CollisionAPI.Apply(bx)
            box = RigidPrim(
                [SCENE_ROOT + "/Box"],
                positions=np.array([[0.0, 0.0, z0]], dtype=np.float32),
                orientations=np.array([[1, 0, 0, 0]], dtype=np.float32),
                reset_xform_op_properties=True)
            Contact.create(SCENE_ROOT + "/Box/csensor",
                           min_threshold=0.0, max_threshold=1e5,
                           radius=0.06)
            sens = ContactSensor(SCENE_ROOT + "/Box/csensor")

            stage = stage_utils.get_current_stage()
            os.makedirs(paths["dir"], exist_ok=True)
            scene_str = stage.GetRootLayer().ExportToString()
            with open(paths["scene.usda"], "w") as fh:
                fh.write(scene_str)
            scene_sha = sha256_file(paths["scene.usda"])
            with open(paths["scene.sha256"], "w") as fh:
                fh.write(scene_sha + "  scene.usda\n")

            state = {"J": 0.0, "fires": 0, "checked": 0, "bad": []}

            def on_post(step_dt, context):
                state["fires"] += 1
                rd = sens.get_sensor_reading()
                raw = sens.get_raw_data()
                # Validity gate: invalid/stale/missing aborts the diagnostic.
                if not rd.is_valid:
                    state["bad"].append("invalid reading at fire %d"
                                        % state["fires"])
                    return
                if not isinstance(raw, list):
                    state["bad"].append("raw not a list at fire %d"
                                        % state["fires"])
                    return
                for d in raw:
                    for k in ("body0", "body1", "position", "normal",
                              "impulse", "time", "dt"):
                        if k not in d:
                            state["bad"].append(
                                "missing field %s at fire %d"
                                % (k, state["fires"]))
                            return
                    im = d["impulse"]
                    for k in ("x", "y", "z"):
                        v = float(im[k])
                        if not math.isfinite(v):
                            state["bad"].append(
                                "non-finite impulse at fire %d" % state["fires"])
                            return
                        if abs(v) > 1e9:
                            state["bad"].append(
                                "overflow impulse at fire %d" % state["fires"])
                            return
                    state["J"] += float(
                        math.sqrt(im["x"] ** 2 + im["y"] ** 2 + im["z"] ** 2))
                state["checked"] += 1
                if state["fires"] <= 3 or state["fires"] % 200 == 0:
                    samples.append({
                        "fire": state["fires"],
                        "reading_valid": bool(rd.is_valid),
                        "reading_value_N": float(rd.value),
                        "reading_time_s": float(rd.time),
                        "in_contact": bool(rd.in_contact),
                        "n_raw": len(raw)})

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(dt)
            dt_readback = SimulationManager.get_physics_dt()
            cbid = SimulationManager.register_callback(
                on_post, event=SimulationEvent.PHYSICS_POST_STEP)
            tl = omni.timeline.get_timeline_interface()
            tl.play()
            sim.update()  # arming: warm-start creates the simulation view
            # that gates PHYSICS step callbacks (D0 probe 8); this update's
            # steps are excluded by the counters reset below.
            if control == "support":
                for _ in range(SETTLE_STEPS):
                    SimulationManager.step(steps=1)
            # Equal measured interval; counters reset after settling.
            state["J"] = 0.0
            state["fires"] = 0
            state["checked"] = 0
            n_sub = int(round(MEASURE_T / dt))
            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            for _ in range(n_sub):
                SimulationManager.step(steps=1)
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            SimulationManager.deregister_callback(cbid)
            tl.stop()

            dN = n1 - n0
            dT = t1 - t0
            J = state["J"]
            if state["bad"]:
                failures.append("sensor invalid/stale/missing/overflow: %s"
                                % (state["bad"][0],))
                failures.append("diagnostic invalidated (never except-to-zero)")
            if control == "support":
                expect = MASS_KG * G * dN * dt
                rel = abs(J - expect) / expect if expect else float("inf")
                ok = rel <= SUPPORT_TOL
                if not ok:
                    failures.append(
                        "support impulse %r vs m*g*T %r rel %r > 5%%"
                        % (J, expect, rel))
            else:
                rel = None
                expect = 0.0
                ok = J <= NOCONTACT_TOL_Ns
                if not ok:
                    failures.append(
                        "no-contact control reads nonzero: %r Ns > 1e-6" % (J,))
            if dN != n_sub or state["fires"] != n_sub:
                failures.append("step accounting broken: dN=%d fires=%d "
                                "expect=%d" % (dN, state["fires"], n_sub))
            if abs(dT - MEASURE_T) > 1e-6:
                failures.append("measured interval %r != 1.0 s" % (dT,))

            summary = {
                "schema": "r02_d1/1", "backend": "ISAAC_PHYSX",
                "isaac_version": "6.1.0.0",
                "isaac_runtime_version": isaac_rt,
                "isaac_build": "6.1.0-rc.26+release.49347.2d230af4.gl",
                "python": sys.executable,
                "module_paths": {
                    "contact_sensor": _cs_mod.__file__,
                    "contact_authoring": _c_mod.__file__,
                    "sensor_common": _common_mod.__file__,
                    "simulation_manager": _sm_pkg.__file__,
                },
                "contact_api": {
                    "reading": ("ContactSensorReading{value[N scalar], "
                                "time[s], is_valid, in_contact}"),
                    "frame": ("get_data(){in_contact, force[N scalar], "
                              "time, physics_step, number_of_contacts} "
                              "+ raw contacts after "
                              "add_raw_contact_data_to_frame()"),
                    "raw_keys": ["body0", "body1", "position", "normal",
                                 "impulse", "time", "dt"],
                    "impulse_semantics": ("vector N s per contact; sum |J| "
                                          "ONCE; F[N]=|J|/dt_contact"),
                    "normal": "unit contact normal",
                    "position": "contact position [m]",
                    "bodies": ("int handles -> "
                               "PhysicsSchemaTools.intToSdfPath"),
                },
                "scene": SCENE_ROOT,
                "control": control,
                "mass_kg": MASS_KG, "gravity": G,
                "physics_dt_s": dt, "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(%r) once pre-play; "
                    "advance via SimulationManager.step(steps=1)" % (dt,)),
                "substeps": n_sub,
                "settle_steps": SETTLE_STEPS if control == "support" else 0,
                "support_impulse_Ns": J,
                "expected_mgT_Ns": expect,
                "relative_error": rel,
                "within_5pct": bool(ok) if control == "support" else None,
                "nophysics_reading_Ns": J if control == "nocontact" else None,
                "invalid_samples": len(state["bad"]),
                "scene_sha256": scene_sha,
                "status": "RUN_OK" if not failures else "RUN_FAILED",
                "verdict": ("IMPLEMENTED" if not failures else "BLOCKED"),
                "failures": failures,
            }
            log("d1 %s dt=%s J=%r expect=%r status=%s" % (
                control, dt, J, expect, summary["status"]))
            with open(paths["samples.jsonl"], "w") as fh:
                for r in samples:
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
            summary = {"schema": "r02_d1/1", "backend": "ISAAC_PHYSX",
                       "control": control, "physics_dt_s": dt,
                       "status": "RUN_FAILED", "verdict": "BLOCKED",
                       "failures": failures}
    except Exception:
        failures.append("exception: " + traceback.format_exc(
            limit=10).replace("\n", " | "))
        summary = {"schema": "r02_d1/1", "backend": "ISAAC_PHYSX",
                   "control": control, "physics_dt_s": dt,
                   "status": "RUN_FAILED", "verdict": "BLOCKED",
                   "failures": failures}
    os.makedirs(paths["dir"], exist_ok=True)
    if not os.path.exists(paths["summary.json"]):
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    if not os.path.exists(paths["samples.jsonl"]):
        with open(paths["samples.jsonl"], "w") as fh:
            for r in samples:
                fh.write(json.dumps(r) + "\n")
    with open(paths["stdout.log"], "a") as fh:
        fh.write("\n".join(logs) + "\n")
    with open(paths["stderr.log"], "w") as fh:
        fh.write("\n".join(summary.get("failures", [])) + "\n")
    return summary


def run_one(control, dt, isaac_python):
    paths = run_paths(control, dt)
    os.makedirs(paths["dir"], exist_ok=True)
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    cmd = [isaac_python, os.path.abspath(__file__),
           "--child", "--control", control, "--dt", repr(float(dt))]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=REPO)
    with open(paths["stdout.log"], "w") as fh:
        fh.write(r.stdout)
    with open(paths["stderr.log"], "w") as fh:
        fh.write(r.stderr)
    try:
        summary = json.load(open(paths["summary.json"]))
    except Exception as exc:
        summary = {"schema": "r02_d1/1", "backend": "ISAAC_PHYSX",
                   "control": control, "physics_dt_s": dt,
                   "status": "RUN_FAILED", "verdict": "BLOCKED",
                   "failures": ["summary unreadable: %r (rc=%s)" % (
                       exc, r.returncode)]}
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--control", default=None)
    ap.add_argument("--dt", type=float, default=None)
    ap.add_argument("--isaac-python",
                    default=os.path.expanduser(
                        "~/env_isaacsim-c22/bin/python"))
    args = ap.parse_args(argv)
    if args.child:
        _isaac_child(args.control, args.dt, run_paths(args.control, args.dt))
        s = json.load(open(run_paths(args.control, args.dt)["summary.json"]))
        print(json.dumps({k: s.get(k) for k in
                          ("control", "physics_dt_s", "status", "verdict")},
                         indent=2))
        return 0 if s.get("status") == "RUN_OK" else 1
    recs = {}
    for control in ("support", "nocontact"):
        for dt in DT_LADDER:
            recs["%s@%s" % (control, dt)] = run_one(
                control, dt, args.isaac_python)
    agg = {"schema": "r02_d1_agg/1", "backend": "ISAAC_PHYSX",
           "support_tol": SUPPORT_TOL, "runs": recs,
           "verdict": ("IMPLEMENTED" if all(
               r.get("verdict") == "IMPLEMENTED"
               for r in recs.values()) else "BLOCKED")}
    with open(os.path.join(R1, "runs", "d1_contact.json"), "w") as fh:
        json.dump(agg, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: v.get("verdict") for k, v in recs.items()},
                     indent=2))
    return 0 if agg["verdict"] == "IMPLEMENTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
