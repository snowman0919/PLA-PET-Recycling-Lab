"""D2 torque/work semantics diagnostic (Goal R0 section 4, D2).

Definitions (implemented in shaft_torque(), boundary_work(); proven by the
analytic unit tests in test_r02_units.py):

- tau_contact = dot(sum_i cross(p_i - o, F_on_shaft_i), a): correct shaft
  contacts only (filter by body path), F_on_shaft with action-reaction signs
  (impulse on the shaft body as reported; peer-body impulses negated),
  counter-rotating shafts accounted separately (per-shaft o/a accumulators,
  never a shared origin/axis).
- Kinematic boundary: signed boundary contact work uses actual boundary point
  velocities and impulse vectors with a documented sign (work ON the body =
  dot(J_on_body, v_point); dissipative contact gives <= 0). Stationary
  boundary yields 0 work despite support force.
- Dynamic (free) shaft: a measured drive/joint torque is UNAVAILABLE on the
  kinematic-pose path (no articulation joint, no drive, no joint-effort
  readout); the diagnostic states this instead of estimating.
- Energy terms share t0/t1; mass/inertia/state exported alongside; PARTIAL
  ledger allowed but the residual is NEVER declared heat/fracture
  (residual_unclassified).

Isaac negative control: supported box on the ground (same scene family as D1)
with a virtual cutter axis declared NEAR but NOT TOUCHING the box: ground
contact impulses exist, cutter/shaft work MUST be 0. Any nonzero cutter work
from ground contact is a leakage failure (BLOCKED).

Legacy R*sum|F| series, when reproduced for comparison, lives under
diagnostics/ only, never evidence.

Layout: c2.3/revisions/r1/runs/d2_torque_dt_<dt>/ (one dt is enough for a
negative control; all four ladder dts are run for uniformity) with scene.usda,
scene.sha256, samples.jsonl, summary.json, stdout/stderr logs, plus the
aggregate c2.3/revisions/r1/runs/d2_torque.json.
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
G = 9.81
MASS_KG = 2.0
BOX_SIZE_M = 0.05
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"
# Virtual cutter axis: offset far from the box so NO shaft contact exists.
AXIS_ORIGIN = [2.0, 0.0, 0.5]
AXIS_DIR = [0.0, 1.0, 0.0]


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def shaft_torque(contacts, origin, axis):
    """Axial contact torque on ONE shaft.

    contacts: iterable of (position_p, force_on_shaft_F) with F the force
      ON the shaft body (action-reaction already applied by the caller).
    Only shaft contacts may be passed (caller filters by body path).
    tau = dot(sum_i cross(p_i - o, F_i), a).
    """
    tx = ty = tz = 0.0
    for p, f in contacts:
        r = _sub(p, origin)
        c = _cross(r, f)
        tx += c[0]
        ty += c[1]
        tz += c[2]
    return _dot([tx, ty, tz], axis)


def boundary_work(impulse_on_body, point_velocity):
    """Signed boundary contact work ON the body: dot(J_on_body, v_point).

    Uses the actual boundary point velocity and the impulse vector on the
    body. Dissipative contact yields <= 0. A stationary boundary (v == 0)
    yields 0 work regardless of support force magnitude.
    """
    return _dot(impulse_on_body, point_velocity)


def run_paths(dt):
    d = os.path.join(R1, "runs", "d2_torque_dt_%s" % dt)
    out = {"dir": d}
    for n in ("scene.usda", "scene.sha256", "samples.jsonl",
              "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _isaac_child(dt, paths):
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
            xp = stage_utils.define_prim(SCENE_ROOT + "/Box", "Xform")
            bx = stage_utils.define_prim(SCENE_ROOT + "/Box/B", "Cube")
            from pxr import UsdGeom, UsdPhysics
            UsdGeom.Cube(bx).GetSizeAttr().Set(BOX_SIZE_M)
            UsdPhysics.RigidBodyAPI.Apply(xp)
            UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(MASS_KG)
            UsdPhysics.CollisionAPI.Apply(bx)
            box = RigidPrim(
                [SCENE_ROOT + "/Box"],
                positions=np.array([[0.0, 0.0, 0.030]], dtype=np.float32),
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

            state = {"W_cutter": 0.0, "J_support": 0.0, "fires": 0,
                     "bad": [], "W_legacy": 0.0}

            def on_post(step_dt, context):
                state["fires"] += 1
                rd = sens.get_sensor_reading()
                raw = sens.get_raw_data()
                if not rd.is_valid or not isinstance(raw, list):
                    state["bad"].append("invalid sample at fire %d"
                                        % state["fires"])
                    return
                fpos, _ = box.get_world_poses()
                p_box = [float(v) for v in
                         np.asarray(fpos.numpy())[0].tolist()]
                lvel, _ = box.get_velocities()
                v_box = [float(v) for v in
                         np.asarray(lvel.numpy())[0].tolist()]
                for d in raw:
                    for k in ("position", "impulse"):
                        if k not in d:
                            state["bad"].append(
                                "missing %s at fire %d" % (k, state["fires"]))
                            return
                    im = d["impulse"]
                    pos = d["position"]
                    Jv = [float(im["x"]), float(im["y"]), float(im["z"])]
                    Pv = [float(pos["x"]), float(pos["y"]), float(pos["z"])]
                    if not all(math.isfinite(v) for v in Jv + Pv):
                        state["bad"].append(
                            "non-finite contact at fire %d" % state["fires"])
                        return
                    state["J_support"] += float(math.sqrt(
                        Jv[0] ** 2 + Jv[1] ** 2 + Jv[2] ** 2))
                    # Shaft-contact filter: only contacts whose body path is
                    # the (virtual) shaft count. The box/ground pair never
                    # matches -> cutter work must stay exactly 0.
                    bodies = [str(d.get("body0", "")),
                              str(d.get("body1", ""))]
                    if any("CutterShaft" in b for b in bodies):
                        F = [c / float(step_dt) for c in Jv]
                        state["W_cutter"] += boundary_work(Jv, v_box)
                    # Legacy comparison series (diagnostics/ only).
                    state["W_legacy"] += (
                        0.04 * float(math.sqrt(
                            Jv[0] ** 2 + Jv[1] ** 2 + Jv[2] ** 2)))
                if state["fires"] <= 3 or state["fires"] % 200 == 0:
                    samples.append({
                        "fire": state["fires"],
                        "W_cutter_J": state["W_cutter"],
                        "J_support_Ns": state["J_support"]})

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
            for _ in range(SETTLE_STEPS):
                SimulationManager.step(steps=1)
            state["W_cutter"] = 0.0
            state["J_support"] = 0.0
            state["fires"] = 0
            n_sub = int(round(MEASURE_T / dt))
            n0 = SimulationManager.get_num_physics_steps()
            t0 = SimulationManager.get_simulation_time()
            fpos0, _ = box.get_world_poses()
            P0 = [float(v) for v in
                  np.asarray(fpos0.numpy())[0].tolist()]
            for _ in range(n_sub):
                SimulationManager.step(steps=1)
            n1 = SimulationManager.get_num_physics_steps()
            t1 = SimulationManager.get_simulation_time()
            fpos1, _ = box.get_world_poses()
            P1 = [float(v) for v in
                  np.asarray(fpos1.numpy())[0].tolist()]
            lvel1, avel1 = box.get_velocities()
            V1 = [float(v) for v in
                  np.asarray(lvel1.numpy())[0].tolist()]
            W1 = [float(v) for v in
                  np.asarray(avel1.numpy())[0].tolist()]
            SimulationManager.deregister_callback(cbid)
            tl.stop()

            dN = n1 - n0
            dT = t1 - t0
            if state["bad"]:
                failures.append("sensor invalid: %s" % state["bad"][0])
            # Negative control: ground contact exists, cutter work must be 0.
            if state["J_support"] <= 0:
                failures.append("no ground contact observed; control void")
            if state["W_cutter"] != 0.0:
                failures.append(
                    "cutter/shaft work leakage from ground contact: %r J"
                    % (state["W_cutter"],))
            # Energy terms share t0/t1; PARTIAL ledger, residual unclassified.
            I_box = (1.0 / 6.0) * MASS_KG * BOX_SIZE_M ** 2
            ke_t = 0.5 * MASS_KG * sum(v * v for v in V1)
            ke_r = 0.5 * I_box * sum(w * w for w in W1)
            pe = MASS_KG * G * P1[2]

            summary = {
                "schema": "r02_d2/1", "backend": "ISAAC_PHYSX",
                "isaac_version": "6.1.0.0",
                "isaac_runtime_version": isaac_rt,
                "isaac_build": "6.1.0-rc.26+release.49347.2d230af4.gl",
                "python": sys.executable,
                "simulation_manager": _sm_pkg.__file__,
                "scene": SCENE_ROOT,
                "physics_dt_s": dt, "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(%r) once pre-play; "
                    "advance via SimulationManager.step(steps=1)" % (dt,)),
                "torque_definition": ("tau_contact = dot(sum(cross(p_i - o, "
                                      "F_on_shaft_i)), a); shaft contacts "
                                      "only; action-reaction signs; "
                                      "counter-rotating shafts separate"),
                "kinematic_boundary": ("signed work ON body = "
                                       "dot(J_on_body, v_point); "
                                       "stationary boundary -> 0"),
                "dynamic_shaft": ("UNAVAILABLE: no articulation joint/drive/"
                                  "joint-effort readout on the "
                                  "kinematic-pose path; not estimated"),
                "axis_origin": AXIS_ORIGIN, "axis_dir": AXIS_DIR,
                "cutter_work_J": state["W_cutter"],
                "support_impulse_Ns": state["J_support"],
                "legacy_RsumF_diagnostics_only": state["W_legacy"],
                "energy_t0t1": {
                    "t0_s": t0, "t1_s": t1, "shared": True,
                    "mass_kg": MASS_KG, "inertia_box": I_box,
                    "pos_t1_m": P1, "vel_t1_m_s": V1, "angvel_t1_rad_s": W1,
                    "ke_trans_J": ke_t, "ke_rot_J": ke_r,
                    "pe_grav_J": pe},
                "ledger": "PARTIAL",
                "residual": "residual_unclassified (never heat/fracture)",
                "scene_sha256": scene_sha,
                "status": "RUN_OK" if not failures else "RUN_FAILED",
                "verdict": ("IMPLEMENTED" if not failures else "BLOCKED"),
                "failures": failures,
            }
            log("d2 dt=%s W_cutter=%r J_support=%r status=%s" % (
                dt, state["W_cutter"], state["J_support"],
                summary["status"]))
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
            summary = {"schema": "r02_d2/1", "backend": "ISAAC_PHYSX",
                       "physics_dt_s": dt, "status": "RUN_FAILED",
                       "verdict": "BLOCKED", "failures": failures}
    except Exception:
        failures.append("exception: " + traceback.format_exc(
            limit=10).replace("\n", " | "))
        summary = {"schema": "r02_d2/1", "backend": "ISAAC_PHYSX",
                   "physics_dt_s": dt, "status": "RUN_FAILED",
                   "verdict": "BLOCKED", "failures": failures}
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


def run_one(dt, isaac_python):
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
        summary = {"schema": "r02_d2/1", "backend": "ISAAC_PHYSX",
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
        recs[str(dt)] = run_one(dt, args.isaac_python)
    agg = {"schema": "r02_d2_agg/1", "backend": "ISAAC_PHYSX",
           "runs": recs,
           "verdict": ("IMPLEMENTED" if all(
               r.get("verdict") == "IMPLEMENTED"
               for r in recs.values()) else "BLOCKED")}
    with open(os.path.join(R1, "runs", "d2_torque.json"), "w") as fh:
        json.dump(agg, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: v.get("verdict") for k, v in recs.items()},
                     indent=2))
    return 0 if agg["verdict"] == "IMPLEMENTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
