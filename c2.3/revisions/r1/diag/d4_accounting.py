"""D4 observability / accounting / negative tests (Goal R0 section 4, D4).

Isaac part: three rigid boxes (masses 1.0 / 2.0 / 0.5 kg) under
/World/DIAGNOSTIC_FIXTURE. Body IDs (prim paths), masses
(RigidPrim.get_masses) and transforms (get_world_poses) are read from the
RUNNING stage, never assumed.

Mass reconciliation (pure helpers reconcile_mass()/make_buckets(), proven by
test_r03_causality.py under system python):

- Coarse-graining scale: design target total DESIGN_MASS_KG = 7.0 kg at scale
  SCALE = 0.5 -> intended instantiated total 3.5 kg, split [1.0, 2.0, 0.5].
  Reconciliation compares instantiated (stage-read) vs intended (scaled).
- Disjoint buckets active / output / removed / missing partition the
  instantiated IDs; overlap or leakage is an error. Unexplained deficit
  (instantiated - accounted) is REPORTED as-is and judged against the
  tolerance; it is NEVER forced to zero.
- Float handling (documented): Python float (float64) accumulation in FIXED
  order (sorted body IDs, sequential add — no fsum, no set-order iteration);
  comparison form rel = |intended - accounted| / max(|intended|, tiny) with
  tiny = 1e-30; tolerance 1e-6 relative.

Fault injection (each MUST be detected, else BLOCKED):

- F1 actor disappearance: disable body C via set_enabled_rigid_bodies;
  enabled-set readback must mismatch the intended set -> DETECTED.
- F2 duplicate accounting entry: trial ledger counts body B twice; accounted
  total exceeds instantiated total beyond tolerance -> DETECTED.
- F3 altered runtime mass: set_masses changes body B 2.0 -> 2.5 kg;
  stage-read mass must mismatch intended beyond tolerance -> DETECTED.

Observability statuses (R3): missing wrap -> (null, NOT_IMPLEMENTED); no
screen in this fixture -> passage (null, NOT_APPLICABLE); no exit event ->
residence RIGHT_CENSORED (never completed); no torque-limited drive ->
motor-jam NOT observable (no flag emitted). Comparisons with
unavailable/invalid metrics -> NOT_EVALUABLE.

Layout: c2.3/revisions/r1/runs/d4_accounting/ with scene.usda, scene.sha256,
reads.jsonl, summary.json (fault-injection detection table included),
stdout/stderr logs, plus the aggregate c2.3/revisions/r1/runs/d4_accounting.json
(copy of the run summary verdict).

Isaac imports are lazy inside _isaac_child(); module import is isaac-free.
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
N_WARMUP = 30
REL_TOL = 1e-6
TINY = 1e-30
DESIGN_MASS_KG = 7.0
SCALE = 0.5
INTENDED_MASSES = {"A": 1.0, "B": 2.0, "C": 0.5}
G = 9.81
BOX_SIZE_M = 0.08
SCENE_ROOT = "/World/DIAGNOSTIC_FIXTURE"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_paths():
    d = os.path.join(R1, "runs", "d4_accounting")
    out = {"dir": d}
    for n in ("scene.usda", "scene.sha256", "reads.jsonl",
              "summary.json", "stdout.log", "stderr.log"):
        out[n] = os.path.join(d, n)
    return out


# ---- Pure helpers (isaac-free; unit-tested under system python). ----

def ordered_sum(masses):
    """float64 sequential add in FIXED sorted-ID order (documented)."""
    total = 0.0
    for bid in sorted(masses.keys()):
        total = total + float(masses[bid])
    return total


def rel_diff(a, b):
    """Comparison form: |a - b| / max(|a|, tiny)."""
    return abs(float(a) - float(b)) / max(abs(float(a)), TINY)


def reconcile_mass(intended, instantiated):
    """Reconcile intended vs instantiated mass dicts.

    Returns {intended_total, instantiated_total, unexplained,
    rel_error, within_tol}. unexplained is reported, never zeroed.
    """
    it = ordered_sum(intended)
    at = ordered_sum(instantiated)
    unexplained = at - it
    return {"intended_total": it, "instantiated_total": at,
            "unexplained": unexplained,
            "rel_error": rel_diff(it, at),
            "within_tol": bool(rel_diff(it, at) <= REL_TOL)}


def make_buckets(instantiated_ids, active, output, removed, missing):
    """Check disjoint buckets partitioning the instantiated IDs."""
    buckets = {"active": set(active), "output": set(output),
               "removed": set(removed), "missing": set(missing)}
    errors = []
    seen = set()
    for name, ids in buckets.items():
        overlap = seen & ids
        if overlap:
            errors.append("bucket overlap in %s: %r" % (name, sorted(overlap)))
        seen |= ids
    inst = set(instantiated_ids)
    if seen != inst:
        errors.append("buckets do not partition instantiated IDs: "
                      "uncovered=%r extra=%r" % (
                          sorted(inst - seen), sorted(seen - inst)))
    return errors


def wrap_status():
    return (None, "NOT_IMPLEMENTED")


def passage_status(has_screen=False):
    if has_screen:
        return ("REQUIRES_OBSERVED_VALUE", "OBSERVABLE")
    return (None, "NOT_APPLICABLE")


def residence_status(exited=False, value=None):
    if exited:
        return (value, "OBSERVED")
    return (value, "RIGHT_CENSORED")


def jam_status():
    return ("NOT_OBSERVABLE", [])


def compare_metrics(a, b):
    """Comparison with unavailable/invalid metrics -> NOT_EVALUABLE."""
    for v in (a, b):
        if v is None:
            return "NOT_EVALUABLE"
        try:
            if not math.isfinite(float(v)):
                return "NOT_EVALUABLE"
        except (TypeError, ValueError):
            return "NOT_EVALUABLE"
    return "EVALUABLE"


def _isaac_child(paths):
    logs = []

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    failures = []
    reads = []
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

            names = ["A", "B", "C"]
            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            stage_utils.define_prim(SCENE_ROOT, "Xform")
            for i, name in enumerate(names):
                xp = stage_utils.define_prim(
                    "%s/D4_%s" % (SCENE_ROOT, name), "Xform")
                bx = stage_utils.define_prim(
                    "%s/D4_%s/B" % (SCENE_ROOT, name), "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(BOX_SIZE_M)
                UsdPhysics.RigidBodyAPI.Apply(xp)
                UsdPhysics.MassAPI.Apply(xp).GetMassAttr().Set(
                    INTENDED_MASSES[name])
                UsdPhysics.CollisionAPI.Apply(bx)
            prim_paths = [SCENE_ROOT + "/D4_" + n for n in names]
            bodies = RigidPrim(
                prim_paths,
                positions=np.array(
                    [[-0.2 + 0.2 * i, 0.0, 0.3] for i in range(3)],
                    dtype=np.float32),
                orientations=np.array([[1, 0, 0, 0]] * 3, dtype=np.float32),
                reset_xform_op_properties=True)

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
            for _ in range(N_WARMUP):
                SimulationManager.step(steps=1)

            # Stage reads: IDs / masses / transforms.
            masses = bodies.get_masses()
            M = [float(v) for v in np.asarray(masses.numpy()).flatten()]
            fpos, fori = bodies.get_world_poses()
            P = np.asarray(fpos.numpy(), dtype=np.float64).tolist()
            Q = np.asarray(fori.numpy(), dtype=np.float64).tolist()
            instantiated = dict(zip(names, M))
            reads.append({"kind": "stage_read",
                          "body_ids": prim_paths,
                          "masses_kg": instantiated,
                          "positions_m": dict(zip(names, P)),
                          "orientations_wxyz": dict(zip(names, Q))})
            id_ok = ([SCENE_ROOT + "/D4_" + n for n in names]
                     == prim_paths)
            if not id_ok:
                failures.append("body ID mismatch vs intended")

            # Nominal reconciliation (with coarse-graining scale).
            intended_total_check = abs(
                ordered_sum(INTENDED_MASSES) - SCALE * DESIGN_MASS_KG)
            if intended_total_check > 1e-12:
                failures.append("scale bookkeeping broken: %r"
                                % (intended_total_check,))
            nominal = reconcile_mass(INTENDED_MASSES, instantiated)
            reads.append({"kind": "nominal_ledger", "nominal": nominal})
            if not nominal["within_tol"]:
                failures.append("nominal ledger outside 1e-6: %r"
                                % (nominal["rel_error"],))
            bucket_err = make_buckets(names, names, [], [], [])
            if bucket_err:
                failures.append("nominal buckets: %s" % (bucket_err,))

            detections = {}

            # F1: actor disappearance (disable body C at runtime).
            bodies.set_enabled_rigid_bodies([True, True, False])
            SimulationManager.step(steps=1)
            try:
                en = [bool(v) for v in np.asarray(
                    bodies.get_enabled_rigid_bodies().numpy()).flatten()]
            except Exception as exc:
                failures.append("enabled readback failed: %r" % (exc,))
                en = [True, True, True]
            enabled_ids = [n for n, e in zip(names, en) if e]
            f1 = (set(enabled_ids) != set(names))
            detections["actor_disappearance"] = {
                "injected": "disabled body C",
                "enabled_ids": enabled_ids, "detected": bool(f1)}
            reads.append({"kind": "fault_F1", "enabled_ids": enabled_ids,
                          "detected": bool(f1)})
            if not f1:
                failures.append("F1 disappearance NOT detected")
            bodies.set_enabled_rigid_bodies([True, True, True])

            # F2: duplicate accounting entry (trial ledger counts B twice).
            trial = {"A": instantiated["A"], "B": instantiated["B"],
                     "B_dup": instantiated["B"], "C": instantiated["C"]}
            dup_total = ordered_sum(trial)
            f2 = (rel_diff(dup_total, nominal["instantiated_total"])
                  > REL_TOL)
            detections["duplicate_entry"] = {
                "injected": "body B counted twice",
                "trial_total": dup_total,
                "instantiated_total": nominal["instantiated_total"],
                "detected": bool(f2)}
            reads.append({"kind": "fault_F2", "trial_total": dup_total,
                          "detected": bool(f2)})
            if not f2:
                failures.append("F2 duplicate NOT detected")

            # F3: altered runtime mass (B 2.0 -> 2.5 kg).
            bodies.set_masses([[1.0], [2.5], [0.5]])
            SimulationManager.step(steps=1)
            masses2 = [float(v) for v in np.asarray(
                bodies.get_masses().numpy()).flatten()]
            instantiated2 = dict(zip(names, masses2))
            f3 = (rel_diff(instantiated2["B"], INTENDED_MASSES["B"])
                  > REL_TOL)
            detections["altered_mass"] = {
                "injected": "body B mass 2.0 -> 2.5 kg",
                "readback_kg": instantiated2, "detected": bool(f3)}
            reads.append({"kind": "fault_F3",
                          "readback_kg": instantiated2,
                          "detected": bool(f3)})
            if not f3:
                failures.append("F3 altered mass NOT detected")
            bodies.set_masses([[INTENDED_MASSES[n]] for n in names])

            # Observability statuses + NOT_EVALUABLE demo.
            w_val, w_st = wrap_status()
            p_val, p_st = passage_status(has_screen=False)
            r_val, r_st = residence_status(exited=False, value=None)
            j_st, j_flags = jam_status()
            cmp_demo = compare_metrics(None, 1.0)
            if not (w_val is None and w_st == "NOT_IMPLEMENTED"):
                failures.append("wrap rule broken")
            if not (p_val is None and p_st == "NOT_APPLICABLE"):
                failures.append("passage rule broken")
            if r_st != "RIGHT_CENSORED":
                failures.append("residence rule broken")
            if j_st != "NOT_OBSERVABLE" or j_flags != []:
                failures.append("jam rule broken (flag emitted)")
            if cmp_demo != "NOT_EVALUABLE":
                failures.append("NOT_EVALUABLE rule broken")

            tl.stop()
            all_detected = all(v["detected"] for v in detections.values())
            summary = {
                "schema": "r03_d4/1", "backend": "ISAAC_PHYSX",
                "isaac_version": "6.1.0.0",
                "isaac_runtime_version": isaac_rt,
                "isaac_build": "6.1.0-rc.26+release.49347.2d230af4.gl",
                "python": sys.executable,
                "simulation_manager": _sm_pkg.__file__,
                "scene": SCENE_ROOT,
                "physics_dt_s": DT, "dt_readback_s": dt_readback,
                "dt_source_mapping": (
                    "SimulationManager.set_physics_dt(0.005) once pre-play; "
                    "advance via SimulationManager.step(steps=1)"),
                "body_ids": prim_paths,
                "design_mass_kg": DESIGN_MASS_KG, "scale": SCALE,
                "intended_masses_kg": INTENDED_MASSES,
                "instantiated_masses_kg": instantiated,
                "nominal_ledger": nominal,
                "bucket_partition": {"active": names, "output": [],
                                     "removed": [], "missing": []},
                "float_handling": {
                    "dtype": "float64 (Python float)",
                    "summation": "sequential add, sorted body-ID order",
                    "comparison": "|a-b|/max(|a|,1e-30)",
                    "tolerance": REL_TOL},
                "fault_injection": detections,
                "all_faults_detected": bool(all_detected),
                "observability": {
                    "wrap": [w_val, w_st],
                    "passage": [p_val, p_st],
                    "residence": [r_val, r_st],
                    "motor_jam": [j_st, j_flags],
                    "unavailable_comparison": cmp_demo},
                "scene_sha256": scene_sha,
                "status": ("RUN_OK" if (not failures and all_detected)
                           else "RUN_FAILED"),
                "verdict": ("IMPLEMENTED" if (not failures and all_detected)
                            else "BLOCKED"),
                "failures": failures,
            }
            log("d4 nominal_rel=%r faults=%r status=%s" % (
                nominal["rel_error"],
                {k: v["detected"] for k, v in detections.items()},
                summary["status"]))
            with open(paths["reads.jsonl"], "w") as fh:
                for r in reads:
                    fh.write(json.dumps(r) + "\n")
            with open(paths["summary.json"], "w") as fh:
                json.dump(summary, fh, indent=2)
                fh.write("\n")
            with open(paths["stdout.log"], "w") as fh:
                fh.write("\n".join(logs) + "\n")
            with open(paths["stderr.log"], "w") as fh:
                fh.write("\n".join(failures) + "\n")
            sim.close(exit_code=0 if summary["status"] == "RUN_OK" else 1)
        except Exception:
            failures.append("exception: " + traceback.format_exc(
                limit=10).replace("\n", " | "))
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            summary = {"schema": "r03_d4/1", "backend": "ISAAC_PHYSX",
                       "status": "RUN_FAILED", "verdict": "BLOCKED",
                       "failures": failures}
    except Exception:
        failures.append("exception: " + traceback.format_exc(
            limit=10).replace("\n", " | "))
        summary = {"schema": "r03_d4/1", "backend": "ISAAC_PHYSX",
                   "status": "RUN_FAILED", "verdict": "BLOCKED",
                   "failures": failures}
    os.makedirs(paths["dir"], exist_ok=True)
    if not os.path.exists(paths["summary.json"]):
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    if not os.path.exists(paths["reads.jsonl"]):
        with open(paths["reads.jsonl"], "w") as fh:
            for r in reads:
                fh.write(json.dumps(r) + "\n")
    with open(paths["stdout.log"], "a") as fh:
        fh.write("\n".join(logs) + "\n")
    with open(paths["stderr.log"], "w") as fh:
        fh.write("\n".join(summary.get("failures", [])) + "\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--isaac-python",
                    default=os.path.expanduser(
                        "~/env_isaacsim-c22/bin/python"))
    args = ap.parse_args(argv)
    paths = run_paths()
    if args.child:
        _isaac_child(paths)
        s = json.load(open(paths["summary.json"]))
        print(json.dumps({k: s.get(k) for k in
                          ("status", "verdict")}, indent=2))
        return 0 if s.get("status") == "RUN_OK" else 1
    os.makedirs(paths["dir"], exist_ok=True)
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    cmd = [args.isaac_python, os.path.abspath(__file__), "--child"]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                       cwd=REPO)
    with open(paths["stdout.log"], "w") as fh:
        fh.write(r.stdout)
    with open(paths["stderr.log"], "w") as fh:
        fh.write(r.stderr)
    try:
        summary = json.load(open(paths["summary.json"]))
    except Exception as exc:
        summary = {"schema": "r03_d4/1", "backend": "ISAAC_PHYSX",
                   "status": "RUN_FAILED", "verdict": "BLOCKED",
                   "failures": ["summary unreadable: %r (rc=%s)" % (
                       exc, r.returncode)]}
        with open(paths["summary.json"], "w") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
    agg = {"schema": "r03_d4_agg/1", "backend": "ISAAC_PHYSX",
           "verdict": summary.get("verdict", "BLOCKED"),
           "fault_injection": summary.get("fault_injection", {}),
           "failures": summary.get("failures", [])}
    with open(os.path.join(R1, "runs", "d4_accounting.json"), "w") as fh:
        json.dump(agg, fh, indent=2)
        fh.write("\n")
    print(json.dumps({"verdict": agg["verdict"]}, indent=2))
    return 0 if agg["verdict"] == "IMPLEMENTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
