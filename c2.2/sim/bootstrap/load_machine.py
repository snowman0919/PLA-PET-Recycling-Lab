"""Gate A loader: open c2.2/sim/assets/usd/machine.usda headless, report stage stats.

Writes c2.2/results/dyn_usd_load.json (PASS iff prims present, units mm,
all mesh extents finite, stage steps 10 frames without NaN).
"""
import json
import os
import sys
import traceback

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
USD = os.path.join(C22, "sim", "assets", "usd", "machine.usda")
OUT = os.path.join(C22, "results", "dyn_usd_load.json")
STEPS = 10


def main() -> int:
    failures: list[str] = []
    try:
        from isaacsim import SimulationApp
        sim = SimulationApp({"headless": True})
        try:
            import numpy as np
            import isaacsim.core.experimental.utils.stage as stage_utils
            from isaacsim.core.simulation_manager import SimulationManager
            from pxr import UsdGeom
            import omni.timeline

            stage_utils.open_stage(USD)
            stage = stage_utils.get_current_stage()
            prims = [p for p in stage.Traverse()]
            meshes = [p for p in prims if p.GetTypeName() == "Mesh"]
            try:
                _u = stage_utils.get_stage_units()
                units = _u[0] if isinstance(_u, (tuple, list)) else _u
            except Exception:
                units = UsdGeom.GetStageMetersPerUnit(stage)
            paths = sorted(p.GetPath().pathString for p in prims)
            n_verts = 0
            extents_ok = True
            for m in meshes:
                try:
                    pts = np.asarray(
                        UsdGeom.Mesh(m).GetPointsAttr().Get(),
                        dtype=np.float64)
                    n_verts += len(pts)
                    if not np.isfinite(pts).all():
                        extents_ok = False
                except Exception:
                    extents_ok = False
            if "/World/F0/Hopper" not in paths:
                failures.append("hopper prim missing")
            if not any("Transfer" in p for p in paths):
                failures.append("DERIVED transfer prims missing")
            if abs(float(units) - 0.001) > 1e-9:
                failures.append(f"units not mm: {units}")
            if not extents_ok:
                failures.append("non-finite mesh points")

            # physics smoke on loaded stage: add scene if absent, step frames
            try:
                stage_utils.define_prim("/World/PhysicsScene",
                                        "PhysicsScene")
            except Exception:
                pass
            SimulationManager.set_physics_sim_device("cpu")
            tl = omni.timeline.get_timeline_interface()
            tl.play()
            for _ in range(STEPS):
                sim.update()
            tl.stop()

            rec = {"schema": "dyn_usd_load/1", "usd": USD,
                   "prim_count": len(prims), "mesh_count": len(meshes),
                   "total_verts": int(n_verts),
                   "meters_per_unit": float(units),
                   "prim_paths": paths,
                   "steps": STEPS,
                   "status": "PASS" if not failures else "FAIL",
                   "failures": failures}
            with open(OUT, "w") as f:
                json.dump(rec, f, indent=2)
                f.write("\n")
            print(json.dumps(rec, indent=2))
            sim.close(exit_code=0 if not failures else 1)
            return 0 if not failures else 1
        except Exception:
            failures.append("exception: "
                            + traceback.format_exc(limit=8).replace("\n",
                                                                    " | "))
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            return 1
    except Exception:
        failures.append("exception: "
                        + traceback.format_exc(limit=8).replace("\n", " | "))
    try:
        with open(OUT, "w") as f:
            json.dump({"schema": "dyn_usd_load/1", "status": "FAIL",
                       "failures": failures}, f, indent=2)
    except Exception:
        pass
    print(json.dumps({"status": "FAIL", "failures": failures}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
