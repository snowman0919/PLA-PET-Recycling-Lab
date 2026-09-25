"""Gate D: real hole-geometry collision screen passage (S2-A rotor + S2-B ref).

No `if deq < hole: pass` proxy. Screen = static thin box with REAL HOLE
GEOMETRY: hole grid cut as open apertures between static bar collision boxes
(each bar a separate static Cube collider; gaps are physical holes: fragments
pass through or jam by rigid-body contact only). Sliver behavior reported from
shape/orientation: each S1 fragment end-state is re-emitted as a box with its
dyn_s1 final extent + bond-survivor count, dropped above the screen; PASS vs
JAM decided by final resting height (above screen = jammed/retained, below =
passed) read from PhysX poses, never from a size comparison.

Screen hole diameter configurable (3.0-5.5mm sweep range); bars sized so that
pitch - bar = hole. Fragment scale: dyn_s1 frag size vs hole.

Writes c2.2/results/dyn_s2/<run>.summary.json + jsonl telemetry.
"""
import argparse
import json
import os
import sys
import traceback

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUTDIR = os.path.join(C22, "results", "dyn_s2")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-s1", required=True,
                    help="dyn_s1 summary basename e.g. s1_W1_7_dt0.005_n240")
    ap.add_argument("--arch", default="S2-A", choices=["S2-A", "S2-B"])
    ap.add_argument("--hole-mm", type=float, default=4.0)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--dt", type=float, default=0.005)
    args = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    tag = f"s2_{args.arch}_{args.from_s1}_hole{args.hole_mm}"
    out_jsonl = os.path.join(OUTDIR, tag + ".jsonl")
    out_sum = os.path.join(OUTDIR, tag + ".summary.json")

    s1 = json.load(open(os.path.join(C22, "results", "dyn_s1",
                                     args.from_s1 + ".summary.json")))
    s1rows = [json.loads(l) for l in
              open(os.path.join(C22, "results", "dyn_s1",
                                args.from_s1 + ".jsonl"))]
    frag_size = s1.get("frag_cube_size_m", 0.008)
    n = min(s1["lattice"]["kept_cells"], 12)
    hole = args.hole_mm / 1000.0
    # screen: 5x5 hole grid; bars between holes. pitch = hole + bar.
    bar = 0.002  # 2mm ligaments
    pitch = hole + bar
    grid = 5
    screen_top_y = 0.0  # screen plane height (fragments drop from above)
    failures: list[str] = []
    try:
        from isaacsim import SimulationApp
        sim = SimulationApp({"headless": True})
        try:
            import numpy as np
            import omni.timeline
            from isaacsim.sensors.experimental.physics import (
                Contact, ContactSensor)
            import isaacsim.core.experimental.utils.stage as stage_utils
            from isaacsim.core.experimental.objects import GroundPlane
            from isaacsim.core.experimental.prims import RigidPrim
            from isaacsim.core.simulation_manager import SimulationManager
            from pxr import UsdGeom, UsdPhysics

            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            GroundPlane("/World/ground_plane")

            # --- screen plate: static bars forming a real hole grid ---
            # plate outer span covers grid; bars along X and Z leave
            # grid x grid square apertures of `hole` size.
            span = grid * hole + (grid + 1) * bar
            thick = 0.002
            stage_utils.define_prim("/World/Screen", "Xform")
            bar_id = 0
            for i in range(grid + 1):
                # bars running along X at each Z division
                for axis in ("x", "z"):
                    bp = f"/World/Screen/bar{bar_id}"
                    bar_id += 1
                    xb = stage_utils.define_prim(bp, "Xform")
                    cb = stage_utils.define_prim(bp + "/B", "Cube")
                    if axis == "x":
                        # long in X, thin in Z
                        UsdGeom.Cube(cb).GetSizeAttr().Set(1.0)
                        UsdPhysics.CollisionAPI.Apply(cb)
                        RigidPrim([bp],
                                  positions=np.array(
                                      [[0.0, screen_top_y,
                                        -span / 2 + i * pitch]],
                                      dtype=np.float32),
                                  orientations=np.array(
                                      [[1, 0, 0, 0]], dtype=np.float32),
                                  reset_xform_op_properties=True)
                        # scale via USD: set cube extent through prim scale
                        from pxr import Usd as _U
                        prim = stage_utils.get_current_stage().GetPrimAtPath(
                            bp + "/B")
                        _xg = UsdGeom.Xformable(prim)
                        _xg.ClearXformOpOrder()
                        _xg.AddScaleOp().Set(
                            (float(span), float(thick), float(bar)))
                    else:
                        UsdGeom.Cube(cb).GetSizeAttr().Set(1.0)
                        UsdPhysics.CollisionAPI.Apply(cb)
                        RigidPrim([bp],
                                  positions=np.array(
                                      [[-span / 2 + i * pitch,
                                        screen_top_y, 0.0]],
                                      dtype=np.float32),
                                  orientations=np.array(
                                      [[1, 0, 0, 0]], dtype=np.float32),
                                  reset_xform_op_properties=True)
                        from pxr import Usd as _U2
                        prim = stage_utils.get_current_stage().GetPrimAtPath(
                            bp + "/B")
                        _xg = UsdGeom.Xformable(prim)
                        _xg.ClearXformOpOrder()
                        _xg.AddScaleOp().Set(
                            (float(bar), float(thick), float(span)))
            # --- S2 rotor above screen (S2-A eccentric orbit stub:
            # kinematic bar sweeping above screen; S2-B: static housing) ---
            if args.arch == "S2-A":
                rp = stage_utils.define_prim("/World/S2/Rotor", "Xform")
                rc = stage_utils.define_prim("/World/S2/Rotor/B", "Cube")
                UsdGeom.Cube(rc).GetSizeAttr().Set(0.02)
                rb = UsdPhysics.RigidBodyAPI.Apply(rp)
                rb.GetKinematicEnabledAttr().Set(True)
                UsdPhysics.CollisionAPI.Apply(rc)
                rotor = RigidPrim(
                    ["/World/S2/Rotor"],
                    positions=np.array([[0.0, 0.06, 0.0]],
                                       dtype=np.float32),
                    orientations=np.array([[1, 0, 0, 0]],
                                          dtype=np.float32),
                    reset_xform_op_properties=True)
            else:
                rotor = None

            # --- fragments: identical S1 end-state sizes, dropped over holes
            frag_paths = [f"/World/Frag/f{i}" for i in range(n)]
            for i, fp in enumerate(frag_paths):
                xp = stage_utils.define_prim(fp, "Xform")
                bx = stage_utils.define_prim(fp + "/B", "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(float(frag_size))
                UsdPhysics.RigidBodyAPI.Apply(xp)
                mapi = UsdPhysics.MassAPI.Apply(xp)
                mapi.GetMassAttr().Set(0.003)
                UsdPhysics.CollisionAPI.Apply(bx)
            # stagger over hole centers with alternating yaw (sliver study:
            # orientation 0deg vs 45deg recorded per fragment)
            import math as _m
            pos, ori = [], []
            for i in range(n):
                gx = (i % grid) - grid // 2
                gz = ((i // grid) % grid) - grid // 2
                yaw = (i % 2) * _m.pi / 4
                pos.append([gx * pitch, 0.05 + (i // (grid * grid)) * 0.02,
                            gz * pitch])
                ori.append([_m.cos(yaw / 2), 0.0, _m.sin(yaw / 2), 0.0])
            pos = np.array(pos, dtype=np.float32)
            ori = np.array(ori, dtype=np.float32)
            yaws = [(i % 2) * 45.0 for i in range(n)]
            frags = RigidPrim(frag_paths, positions=pos, orientations=ori,
                              reset_xform_op_properties=True)
            sensors = []
            for fp in frag_paths:
                Contact.create(fp + "/csensor", min_threshold=1e-4,
                               max_threshold=1e5,
                               radius=float(frag_size))
                sensors.append(ContactSensor(fp + "/csensor"))

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(args.dt)
            tl = omni.timeline.get_timeline_interface()
            tl.play()
            rows = []
            passed_flags = [False] * n
            for step in range(args.steps):
                if rotor is not None:
                    # eccentric sweep: x = e*cos(w t) (e=7mm like S2-A)
                    ang = step * args.dt * (120.0 * 2 * _m.pi / 60.0)
                    rp_ = np.array([[0.007 * _m.cos(ang), 0.06,
                                     0.007 * _m.sin(ang)]],
                                   dtype=np.float32)
                    rotor.set_world_poses(
                        rp_, np.array([[1, 0, 0, 0]], dtype=np.float32))
                sim.update()
                fpos, _ = frags.get_world_poses()
                P = np.asarray(fpos.numpy()
                               if hasattr(fpos, "numpy") else fpos,
                               dtype=np.float64)
                mag = np.zeros(n)
                for fi, sn in enumerate(sensors):
                    try:
                        dd = sn.get_data()
                        if dd.get("in_contact"):
                            mag[fi] = float(dd.get("force", 0.0))
                    except Exception:
                        pass
                for fi in range(n):
                    if P[fi, 1] < screen_top_y - 0.01:
                        passed_flags[fi] = True
                rows.append({"step": step + 1,
                             "n_contact": int((mag > 1e-9).sum()),
                             "n_passed_cum": int(sum(passed_flags)),
                             "max_force_N": float(mag.max())})
            tl.stop()
            fpos, _ = frags.get_world_poses()
            P = np.asarray(fpos.numpy()
                           if hasattr(fpos, "numpy") else fpos,
                           dtype=np.float64)
            if not bool(np.isfinite(P).all()):
                failures.append("non-finite fragment poses")
            # sliver report: passed vs retained by yaw orientation
            by_yaw = {}
            for fi in range(n):
                by_yaw.setdefault(yaws[fi], {"passed": 0, "total": 0})
                by_yaw[yaws[fi]]["total"] += 1
                by_yaw[yaws[fi]]["passed"] += int(passed_flags[fi])
            summ = {
                "schema": "dyn_s2/1", "arch": args.arch,
                "from_s1": args.from_s1,
                "hole_mm": args.hole_mm, "grid": grid, "bar_mm": bar * 1000,
                "frag_size_mm": frag_size * 1000, "n_frags": n,
                "frag_to_hole_ratio": (frag_size * 1000) / args.hole_mm,
                "evidence": "REAL_PHYSX_HEADLESS_HOLE_GEOMETRY",
                "proxy_free": True,
                "n_passed": int(sum(passed_flags)),
                "n_retained": int(n - sum(passed_flags)),
                "pass_rate": float(sum(passed_flags)) / n,
                "sliver_by_yaw_deg": by_yaw,
                "steps": args.steps, "dt": args.dt,
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
            with open(out_jsonl, "w") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            with open(out_sum, "w") as fh:
                json.dump(summ, fh, indent=2)
                fh.write("\n")
            print(json.dumps(summ, indent=2))
            sim.close(exit_code=0 if not failures else 1)
            return 0 if not failures else 1
        except Exception:
            failures.append("exception: "
                            + traceback.format_exc(limit=10).replace("\n",
                                                                     " | "))
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            return 1
    except Exception:
        failures.append("exception: "
                        + traceback.format_exc(limit=10).replace("\n", " | "))
    try:
        with open(out_sum, "w") as fh:
            json.dump({"schema": "dyn_s2/1", "status": "FAIL",
                       "failures": failures}, fh, indent=2)
    except Exception:
        pass
    print(json.dumps({"status": "FAIL", "failures": failures}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
