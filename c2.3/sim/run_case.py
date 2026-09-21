"""A2 single-case Isaac headless runner (ONE frozen case + ONE ladder dt).

REUSE STATUS vs c2.2/sim/dynamics/s1_physx.py (frozen, must not edit):
  Reused by import: build_bond_list, cell_lattice, CUTTER_R_M,
  SHAFT_OFFSET_M, S1_RPM, IMPULSE_SCALE, FRAG_HALF_MIN_M.
  Scene assembly (USD stage, shafts, fragments, sensors) is transcribed 1:1
  from s1_physx.py main() with inline line references, because that file
  exposes no factored scene-builder functions (construction is inline).
  Transcription is exact, not an independent implementation.

TORQUE SOURCE VERDICT (documented equation, no fabrication):
  Shafts are KINEMATIC pose-driven RigidBodies (s1_physx.py: shafts built
  ~L168-179, pose overwritten each step ~L254-266 via set_world_poses under
  use_backend("usd")). There is no articulation joint, no drive, and no
  joint-effort / reaction / constraint-force readout on this path, so a
  measured shaft torque is UNAVAILABLE.
  The ONLY PhysX-traceable load quantity is the per-fragment ContactSensor
  force magnitude mag[i] in Newtons (s1_physx.py ~L270-280).
  Contact-derived moment-arm estimate (UNCALIBRATED, same basis as the
  C2.2b torque_impulse accumulator ~L284-285):
      tau(t) = CUTTER_R_M * sum_i |F_contact,i(t)|        [N m]
      W      = sum_t tau(t) * omega * dt = omega * J_tau  [J]
  with omega = S1_RPM * 2*pi/60 constant, J_tau the torque impulse.
  Recorded as torque_source=CONTACT_DERIVED_MOMENT_ARM. This is NOT a
  measured shaft torque.

PHYSICS DT MAPPING (SimulationManager.set_physics_dt):
  set_physics_dt(dt) is called once before tl.play(); each sim.update()
  advances exactly dt seconds with steps_per_run=240 updates, so
  T_sim = 240*dt: 0.01->2.4s, 0.005->1.2s, 0.0025->0.6s, 0.00125->0.3s.

Per-run layout: c2.3/results/<CASE>/dt_<dt>/ with config.json,
environment.json, asset_manifest.json, telemetry.jsonl, events.jsonl,
summary.json, stdout.log, stderr.log.

Isaac imports are lazy inside run(); module import is isaac-free so unit
tests run under system python3.
"""
import argparse
import hashlib
import json
import os
import sys
import traceback

HERE = os.path.abspath(__file__)
C23 = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(C23)
C22 = os.path.join(REPO, "c2.2")

CASES = ("FDM", "PURGE", "WRAP")
DT_LADDER = [0.01, 0.005, 0.0025, 0.00125]
STEPS_PER_RUN = 240
G_M_S2 = 9.81

TORQUE_SOURCE = "CONTACT_DERIVED_MOMENT_ARM"
TORQUE_EQUATION = ("tau(t) = CUTTER_R_M * sum_i |F_contact,i(t)|; "
                   "W = sum_t tau(t)*omega*dt")

# s1_physx reuse surface (imported lazily so module import stays stdlib).
S1_MOD = "s1_physx"


def dt_source_mapping(dt):
    """Document the SimulationApp/physics-dt mapping for one ladder value."""
    if dt not in DT_LADDER:
        raise ValueError("dt %r not in frozen ladder %r" % (dt, DT_LADDER))
    return {
        "physics_dt_s": dt,
        "set_call": "SimulationManager.set_physics_dt(%r) once pre-play" % dt,
        "updates": STEPS_PER_RUN,
        "sim_time_s": STEPS_PER_RUN * dt,
        "advance_rule": ("each sim.update() advances physics_dt_s; "
                         "telemetry t=(step+1)*dt"),
    }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


FROZEN_FILES = ("CONTRACT.md", "STATE.json", "NEXT.md",
                "configs/baseline.json", "configs/cases.json")


def verify_freeze(c23dir=C23):
    """Recompute the five A1 control hashes and compare to the manifest.

    Raises RuntimeError on any mismatch; returns the manifest record.
    """
    man_path = os.path.join(c23dir, "results", "baseline_manifest.json")
    man = json.load(open(man_path))
    expect = man["config_hashes"]
    for rel in FROZEN_FILES:
        got = sha256_file(os.path.join(c23dir, rel))
        if expect.get(rel) != got:
            raise RuntimeError("freeze mismatch for %s: manifest %s != "
                               "file %s" % (rel, expect.get(rel), got))
    return man


def dt_label(dt):
    return "dt_%s" % dt


def run_paths(c23dir, case, dt):
    if case not in CASES:
        raise ValueError("unknown case %r" % case)
    d = os.path.join(c23dir, "results", case, dt_label(dt))
    names = ("config.json", "environment.json", "asset_manifest.json",
             "telemetry.jsonl", "events.jsonl", "summary.json",
             "stdout.log", "stderr.log")
    out = {"dir": d}
    for _n in names:
        out[_n] = os.path.join(d, _n)
    return out


def _import_s1():
    sys.path.insert(0, os.path.join(C22, "sim", "dynamics"))
    sys.path.insert(0, os.path.join(C22, "sim", "generators"))
    import importlib
    return importlib.import_module(S1_MOD)


def build_run_config(case, dt, c23dir=C23):
    """Assemble the frozen run configuration (no physics executed)."""
    man = verify_freeze(c23dir)
    base = json.load(open(os.path.join(c23dir, "configs", "baseline.json")))
    cases = json.load(open(os.path.join(c23dir, "configs", "cases.json")))
    if dt not in base["frozen_run"]["dt_ladder_s"]:
        raise ValueError("dt not in frozen ladder")
    return {"case": case, "dt_s": dt,
            "case_spec": cases[case], "baseline": base,
            "manifest": man, "dt_mapping": dt_source_mapping(dt),
            "torque_source": TORQUE_SOURCE,
            "torque_equation": TORQUE_EQUATION}


def run(case, dt, c23dir=C23):
    """Execute ONE frozen case at ONE ladder dt under Isaac headless.

    Writes the per-run directory; returns the summary dict.
    """
    import numpy as _np  # noqa: F401  (isaac venv provides numpy)
    logs, errlogs = [], []

    def log(msg):
        logs.append(msg)
        print(msg)

    cfg = build_run_config(case, dt, c23dir)
    base, spec = cfg["baseline"], cfg["case_spec"]
    S1 = _import_s1()
    from waste_gen import generate

    wclass, seed = spec["waste_class"], spec["seed"]
    meta = generate(wclass, seed, material=spec.get("material", "PLA"))
    dims = meta["dims_mm"]
    # Lattice resolution mirrors s1_physx.py L101-107 exactly.
    nx = max(1, min(12, int(round(dims["dx"] / 10.0))))
    ny = max(1, min(10, int(round(dims["dy"] / 10.0))))
    layers = max(1, int(round(dims["dz"] / 0.2)))
    nz = max(1, min(6, layers // max(1, layers // 6)))
    strengths = meta["bonds"]["nominal_strengths"]
    bonds = S1.build_bond_list(nx, ny, nz, strengths)  # s1_physx L54-72
    ncells = nx * ny * nz
    # Sub-lattice keep-list mirrors s1_physx.py L113-134 exactly.
    import math as _math
    _target = min(ncells, 24)
    _snx = max(1, min(nx, int(round(_target ** (1.0 / 3.0)) * 2)))
    _sny = max(1, min(ny, int(round(_target ** (1.0 / 3.0)))))
    _snz = max(1, min(nz, 2))
    while _snx * _sny * _snz > 24:
        _snx -= 1
    keep = []
    for _iz in range(_snz):
        for _iy in range(_sny):
            for _ix in range(_snx):
                keep.append((_iz * ny + _iy) * nx + _ix)
    sx = dims["dx"] / 1000.0 / _snx
    sy = dims["dy"] / 1000.0 / _sny
    sz = dims["dz"] / 1000.0 / _snz
    keep_set = set(keep)
    idmap = {g: i for i, g in enumerate(keep)}
    bonds = [(idmap[a], idmap[b], t, s) for (a, b, t, s) in bonds
             if a in keep_set and b in keep_set]
    n = len(keep)
    nxyz_hint = meta["bonds"]["cells"]
    mass_total_g = meta["mass_g"]
    mass_per_kg = (mass_total_g / nxyz_hint
                   * (ncells / max(1, len(keep))) / 1000.0)
    frag_size = float(min(sx, sy, sz))
    center_mm = 60.0  # frozen baseline (no sweep in C2.3-A)
    shaft_offset_m = center_mm / 2000.0
    omega = S1.S1_RPM * 2.0 * _np.pi / 60.0
    box_I = (1.0 / 6.0) * mass_per_kg * frag_size ** 2  # solid cube inertia

    paths = run_paths(c23dir, case, dt)
    os.makedirs(paths["dir"], exist_ok=True)

    failures = []
    tele_rows, events = [], []
    summary = {}
    try:
        from isaacsim import SimulationApp
        sim = SimulationApp({"headless": True})
        try:
            import omni.timeline
            from isaacsim.sensors.experimental.physics import (
                Contact, ContactSensor)
            import isaacsim.core.experimental.utils.stage as stage_utils
            from isaacsim.core.experimental.objects import GroundPlane
            from isaacsim.core.experimental.prims import RigidPrim
            from isaacsim.core.experimental.utils.backend import use_backend
            from isaacsim.core.simulation_manager import SimulationManager
            from pxr import UsdGeom, UsdPhysics

            try:
                isaac_version = __import__("importlib").import_module(
                    "isaacsim").__version__
            except Exception:
                isaac_version = base["backend"]["isaac_sim"] + " (unqueried)"

            # --- scene transcription of s1_physx.py L160-232 ---
            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            GroundPlane("/World/ground_plane")
            stage = stage_utils.get_current_stage()
            UsdGeom.SetStageMetersPerUnit(stage, 1.0)
            shafts = []
            for side, path in ((-1.0, "/World/S1/ShaftA"),
                               (1.0, "/World/S1/ShaftB")):
                xp = stage_utils.define_prim(path, "Xform")
                cyl = stage_utils.define_prim(path + "/Cyl", "Cylinder")
                UsdGeom.Cylinder(cyl).GetRadiusAttr().Set(S1.CUTTER_R_M)
                UsdGeom.Cylinder(cyl).GetHeightAttr().Set(0.16)
                rb = UsdPhysics.RigidBodyAPI.Apply(xp)
                rb.GetKinematicEnabledAttr().Set(True)
                UsdPhysics.CollisionAPI.Apply(cyl)
                shafts.append((path, side))
            frag_paths = ["/World/Frag/f%d" % i for i in range(n)]
            for i, fp in enumerate(frag_paths):
                xp = stage_utils.define_prim(fp, "Xform")
                bx = stage_utils.define_prim(fp + "/B", "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(frag_size)
                UsdPhysics.RigidBodyAPI.Apply(xp)
                mapi = UsdPhysics.MassAPI.Apply(xp)
                mapi.GetMassAttr().Set(float(mass_per_kg))
                UsdPhysics.CollisionAPI.Apply(bx)
            gx = _np.array([(k % nx) % _snx for k in keep],
                           dtype=_np.float64)
            gy = _np.array([((k // nx) % ny) % _sny for k in keep],
                           dtype=_np.float64)
            gz = _np.array([((k // (nx * ny)) % nz) % _snz for k in keep],
                           dtype=_np.float64)
            _kx = float(gx.max()) if len(gx) else 0.0
            px = (gx - _kx / 2.0) * sx * 0.9
            py = ((gy - float(gy.max()) / 2.0) * sy * 0.9
                  if len(gy) else 0.0)
            pz = S1.CUTTER_R_M + 0.004 + (gz + 0.5) * sz * 0.9
            pos0 = _np.stack([px, py, pz], axis=1).astype(_np.float32)
            ori0 = _np.tile(_np.array([1, 0, 0, 0], dtype=_np.float32),
                            (n, 1))
            frags = RigidPrim(frag_paths, positions=pos0,
                              orientations=ori0,
                              reset_xform_op_properties=True)
            _sens_r = float(_math.sqrt(3.0) * frag_size / 2.0 + 0.005)
            sensors = []
            for fp in frag_paths:
                Contact.create(fp + "/csensor", min_threshold=1e-4,
                               max_threshold=1e5, radius=_sens_r)
                sensors.append(ContactSensor(fp + "/csensor"))
            shaft_views = {
                p: RigidPrim(
                    [p], positions=_np.array(
                        [[s * shaft_offset_m, 0.0, S1.CUTTER_R_M]],
                        dtype=_np.float32),
                    orientations=_np.array([[1.0, 0.0, 0.0, 0.0]],
                                           dtype=_np.float32),
                    reset_xform_op_properties=True)
                for p, s in shafts}

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(dt)
            tl = omni.timeline.get_timeline_interface()
            tl.play()

            alive = [True] * len(bonds)
            impulse_acc = [0.0] * len(bonds)
            breaks = 0
            work_cum = 0.0
            torque_impulse_cum = 0.0
            first_contact_t, last_contact_t = None, None
            m0 = pos0.astype(_np.float64)
            for step in range(STEPS_PER_RUN):
                th = omega * step * dt
                for prim_path, side in shafts:
                    ang = side * th
                    c, s_ = float(_np.cos(ang / 2)), float(_np.sin(ang / 2))
                    q = _np.array([[c, 0.0, s_, 0.0]], dtype=_np.float32)
                    p = _np.array([[side * shaft_offset_m, 0.0,
                                    S1.CUTTER_R_M]], dtype=_np.float32)
                    with use_backend("usd"):
                        shaft_views[prim_path].set_world_poses(p, q)
                sim.update()
                fpos, _fori = frags.get_world_poses()
                lvel, avel = frags.get_velocities()
                P = _np.asarray(fpos.numpy(), dtype=_np.float64)
                V = _np.asarray(lvel.numpy(), dtype=_np.float64)
                W_ = _np.asarray(avel.numpy(), dtype=_np.float64)
                mag = _np.zeros(n, dtype=_np.float64)
                for _fi, _sens in enumerate(sensors):
                    try:
                        _d = _sens.get_data()
                        if _d.get("in_contact"):
                            mag[_fi] = float(_d.get("force", 0.0))
                    except Exception:
                        pass
                f_total = float(_np.abs(mag).sum())
                torque = S1.CUTTER_R_M * f_total  # contact-derived arm
                work_cum += torque * float(omega) * dt
                torque_impulse_cum += torque * dt
                t_now = (step + 1) * dt
                if bool((mag > 1e-9).any()):
                    if first_contact_t is None:
                        first_contact_t = t_now
                    last_contact_t = t_now
                for bi, (a, b, _t, s) in enumerate(bonds):
                    if not alive[bi]:
                        continue
                    share = (mag[a] + mag[b]) * 0.5 * dt
                    impulse_acc[bi] += share
                    if impulse_acc[bi] > s * S1.IMPULSE_SCALE:
                        alive[bi] = False
                        breaks += 1
                        events.append({"type": "bond_break", "step": step + 1,
                                       "t_s": t_now, "bond_id": bi,
                                       "endpoints": [a, b],
                                       "bond_type": _t,
                                       "threshold_Ns": s * S1.IMPULSE_SCALE,
                                       "impulse_Ns": impulse_acc[bi]})
                ke_t = float(0.5 * mass_per_kg * (V ** 2).sum())
                ke_r = float(0.5 * box_I * (W_ ** 2).sum())
                pe = float(mass_per_kg * G_M_S2 * P[:, 2].sum())
                tele_rows.append(
                    {"step": step + 1, "t_s": t_now, "theta_rad": float(th),
                     "omega_rad_s": float(omega),
                     "n_contacts": int((mag > 1e-9).sum()),
                     "contact_force_total_N": f_total,
                     "max_contact_N": float(mag.max()),
                     "torque_Nm": torque, "work_cum_J": work_cum,
                     "torque_impulse_cum_Nms": torque_impulse_cum,
                     "ke_trans_J": ke_t, "ke_rot_J": ke_r,
                     "pe_grav_J": pe,
                     "breaks_cum": breaks,
                     "bonds_alive": int(sum(alive)),
                     "frag_pos_m": P.tolist(), "frag_vel_m_s": V.tolist(),
                     "frag_angvel_rad_s": W_.tolist()})
            tl.stop()
            fpos, _ = frags.get_world_poses()
            P1 = _np.asarray(fpos.numpy(), dtype=_np.float64)
            moved = float(_np.linalg.norm(P1 - m0, axis=1).max())
            finite = bool(_np.isfinite(P1).all())
            if not finite:
                failures.append("non-finite fragment poses")
            J_contact = float(sum(r["contact_force_total_N"]
                                  for r in tele_rows) * dt)
            m_init = mass_per_kg * n
            summary = {
                "schema": "c2.3_run/1", "backend": "ISAAC_PHYSX",
                "isaac_version": isaac_version,
                "physics_dt_s": dt, "dt_source_mapping": cfg["dt_mapping"],
                "case": case, "waste_class": wclass, "seed": seed,
                "steps": STEPS_PER_RUN, "sim_time_s": STEPS_PER_RUN * dt,
                "torque_source": TORQUE_SOURCE,
                "torque_equation": TORQUE_EQUATION,
                "contact_impulse_Ns": J_contact,
                "shaft_work_J": work_cum,
                "torque_impulse_Nms": torque_impulse_cum,
                "bond_breaks": breaks, "bonds_alive": int(sum(alive)),
                "max_frag_displacement_m": moved,
                "mass_initial_kg": m_init, "mass_final_kg": m_init,
                "first_contact_t_s": first_contact_t,
                "last_contact_t_s": last_contact_t,
                "freeze_hashes": {r: sha256_file(os.path.join(c23dir, r))
                                  for r in FROZEN_FILES},
                "status": "RUN_OK" if not failures else "RUN_FAILED",
                "failures": failures,
            }
            sim.close(exit_code=0 if not failures else 1)
        except Exception:
            failures.append("exception: "
                            + traceback.format_exc(limit=10)
                            .replace("\n", " | "))
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            summary = {"schema": "c2.3_run/1", "backend": "ISAAC_PHYSX",
                       "case": case, "physics_dt_s": dt,
                       "status": "RUN_FAILED", "failures": failures}
    except Exception:
        failures.append("exception: "
                        + traceback.format_exc(limit=10)
                        .replace("\n", " | "))
        summary = {"schema": "c2.3_run/1", "backend": "ISAAC_PHYSX",
                   "case": case, "physics_dt_s": dt,
                   "status": "RUN_FAILED", "failures": failures}
        isaac_version = base["backend"]["isaac_sim"] + " (unqueried)"

    env_rec = {"backend": "ISAAC_PHYSX",
               "isaac_version": locals().get("isaac_version",
                                             base["backend"]["isaac_sim"]),
               "physics_device": base["backend"]["physics_device"],
               "gpu": base["backend"]["gpu"],
               "gpu_driver": base["backend"]["gpu_driver"],
               "venv": base["backend"]["venv"],
               "python": sys.executable}
    asset_rec = {"usd": base["reference_assets"],
                 "waste_object_id": meta["object_id"],
                 "waste_dims_mm": meta["dims_mm"],
                 "waste_mass_g": meta["mass_g"],
                 "lattice": {"nx": nx, "ny": ny, "nz": nz,
                             "sub": [_snx, _sny, _snz],
                             "kept_cells": n, "bonds_total": len(bonds)},
                 "frag_cube_size_m": frag_size,
                 "mass_per_fragment_kg": mass_per_kg}
    with open(paths["config.json"], "w") as fh:
        json.dump(cfg, fh, indent=2, default=str)
    with open(paths["environment.json"], "w") as fh:
        json.dump(env_rec, fh, indent=2)
    with open(paths["asset_manifest.json"], "w") as fh:
        json.dump(asset_rec, fh, indent=2)
    with open(paths["telemetry.jsonl"], "w") as fh:
        for r in tele_rows:
            fh.write(json.dumps(r) + "\n")
    with open(paths["events.jsonl"], "w") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")
    with open(paths["summary.json"], "w") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    with open(paths["stdout.log"], "w") as fh:
        fh.write("\n".join(logs) + "\n")
    with open(paths["stderr.log"], "w") as fh:
        fh.write("\n".join(summary.get("failures", [])) + "\n")
    log("run %s dt=%s status=%s" % (case, dt, summary.get("status")))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, choices=CASES)
    ap.add_argument("--dt", type=float, required=True)
    ap.add_argument("--c23", default=C23)
    args = ap.parse_args(argv)
    summary = run(args.case, args.dt, args.c23)
    print(json.dumps({k: summary.get(k) for k in
                      ("case", "physics_dt_s", "status")}, indent=2))
    return 0 if summary.get("status") == "RUN_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
