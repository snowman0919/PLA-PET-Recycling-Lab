"""I0 SimulationApp smoke: headless stage + one rigid cube, 60 physics steps.

Gate rule: nonzero exit on invalid results (NaN/inf, no motion under gravity,
cube fell through ground, unclean shutdown). Writes c2.2/results/i0_smoke.json.
"""

import json
import os
import sys
import traceback

SEED = 20260921
STEPS = 60
CUBE_PATH = "/World/A"
CUBE_SIZE = 0.5
START_Z = 2.0
OUT_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ),
    "results",
    "i0_smoke.json",
)

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def main() -> dict:
    import numpy as np

    np.random.seed(SEED)

    from isaacsim import SimulationApp

    simulation_app = SimulationApp({"headless": True})
    print("SMOKE: app constructed", flush=True)
    try:
        # --- imports only valid after SimulationApp instantiation ---
        import omni.timeline
        from isaacsim.core.experimental.objects import GroundPlane
        from isaacsim.core.experimental.prims import RigidPrim
        from isaacsim.core.experimental.utils.backend import use_backend
        import isaacsim.core.experimental.utils.stage as stage_utils
        from isaacsim.core.simulation_manager import SimulationManager
        from pxr import Gf, UsdPhysics

        # --- stage: /World + PhysicsScene (mirrors installed test helper) ---
        print("SMOKE: building stage", flush=True)
        stage_utils.create_new_stage()
        stage_utils.define_prim("/World", "Xform")
        stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
        GroundPlane("/World/ground_plane")

        # --- rigid cube: Xform (rigid body + mass) + Cube geom (collision) ---
        xform_prim = stage_utils.define_prim(f"{CUBE_PATH}", "Xform")
        cube_prim = stage_utils.define_prim(f"{CUBE_PATH}/B", "Cube")
        from pxr import UsdGeom as _UsdGeom

        _UsdGeom.Cube(cube_prim).GetSizeAttr().Set(CUBE_SIZE)
        UsdPhysics.RigidBodyAPI.Apply(xform_prim)
        mass_api = UsdPhysics.MassAPI.Apply(xform_prim)
        mass_api.GetMassAttr().Set(1.0)
        # solid-cube inertia (1/6)*m*s^2 for s=0.5, m=1
        inertia = (1.0 / 6.0) * 1.0 * CUBE_SIZE**2
        mass_api.GetDiagonalInertiaAttr().Set(Gf.Vec3f(inertia, inertia, inertia))
        mass_api.GetCenterOfMassAttr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
        UsdPhysics.CollisionAPI.Apply(cube_prim)
        body = RigidPrim(
            CUBE_PATH,
            positions=np.array([[0.0, 0.0, START_Z]], dtype=np.float32),
            orientations=np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
            reset_xform_op_properties=True,
        )

        # --- simulate on CPU, tensor backend reads (mirrors installed tests) ---
        SimulationManager.set_physics_sim_device("cpu")
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        print("SMOKE: timeline playing", flush=True)

        frames: list[dict] = []
        with use_backend("tensor", raise_on_unsupported=True, raise_on_fallback=True):
            for step in range(STEPS):
                if step == 0 or (step + 1) % 20 == 0:
                    print(f"SMOKE: step {step + 1}/{STEPS}", flush=True)
                simulation_app.update()
                positions, orientations = body.get_world_poses()
                lin_vel, ang_vel = body.get_velocities()
                frames.append(
                    {
                        "step": step + 1,
                        "position": [float(v) for v in positions.numpy()[0]],
                        "orientation_wxyz": [float(v) for v in orientations.numpy()[0]],
                        "linear_velocity": [float(v) for v in lin_vel.numpy()[0]],
                        "angular_velocity": [float(v) for v in ang_vel.numpy()[0]],
                    }
                )
        timeline.stop()

        # --- validation (nonzero exit on any failure) ---
        pos = np.array([f["position"] for f in frames], dtype=np.float64)
        lin = np.array([f["linear_velocity"] for f in frames], dtype=np.float64)
        ang = np.array([f["angular_velocity"] for f in frames], dtype=np.float64)
        ori = np.array([f["orientation_wxyz"] for f in frames], dtype=np.float64)

        if not (
            np.isfinite(pos).all()
            and np.isfinite(lin).all()
            and np.isfinite(ang).all()
            and np.isfinite(ori).all()
        ):
            fail("non-finite (NaN/inf) transform or velocity recorded")
        z0, zf = float(pos[0, 2]), float(pos[-1, 2])
        if not (zf < z0 - 0.5):
            fail(f"no motion under gravity: z_initial={z0:.4f} z_final={zf:.4f}")
        if zf < -0.05:
            fail(f"cube fell through ground plane: z_final={zf:.4f}")
        if abs(float(lin[-1, 2])) > 2.0:
            fail(f"final vertical velocity unstable: vz={float(lin[-1, 2]):.4f}")
        if abs(zf - CUBE_SIZE / 2.0) > 0.15:
            fail(f"cube did not settle on ground: z_final={zf:.4f} expected~{CUBE_SIZE / 2.0}")

        result = {
            "schema": "i0_smoke/1",
            "isaac_version": "6.1.0.0",
            "seed": SEED,
            "steps": STEPS,
            "physics_dt": float(SimulationManager.get_physics_dt()),
            "device": "cpu",
            "cube_path": CUBE_PATH,
            "cube_size": CUBE_SIZE,
            "start_position": [0.0, 0.0, START_Z],
            "final_position": [float(v) for v in pos[-1]],
            "final_orientation_wxyz": [float(v) for v in ori[-1]],
            "final_linear_velocity": [float(v) for v in lin[-1]],
            "final_angular_velocity": [float(v) for v in ang[-1]],
            "z_drop": float(z0 - zf),
            "all_finite": bool(
                np.isfinite(pos).all()
                and np.isfinite(lin).all()
                and np.isfinite(ang).all()
                and np.isfinite(ori).all()
            ),
            "frames": frames,
            "clean_shutdown": True,
            "status": "PASS" if not failures else "FAIL",
            "failures": list(failures),
        }

        # NOTE: close() os._exit()s via fast shutdown on success, so the JSON
        # print below is the durable pre-close record ("pending-close" marks
        # that close() was entered but cannot report back; exit code is the
        # shutdown verdict). The rewrite after close() only runs on paths
        # where Kit returns instead of _exit()ing.
        os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
        with open(OUT_PATH, "w") as f:
            json.dump(
                {**result, "clean_shutdown": "pending-close"},
                f,
                indent=2,
            )
            f.write("\n")
        print(
            json.dumps({k: v for k, v in result.items() if k != "frames"}, indent=2),
            flush=True,
        )
        simulation_app.close(exit_code=0 if result["status"] == "PASS" else 1)
        clean_shutdown = True
        result["clean_shutdown"] = True
        with open(OUT_PATH, "w") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        return result
    except Exception:  # noqa: BLE001 - gate must report, never hang
        fail("exception: " + traceback.format_exc(limit=8).replace("\n", " | "))
        record = {
            "schema": "i0_smoke/1",
            "isaac_version": "6.1.0.0",
            "seed": SEED,
            "steps": STEPS,
            "clean_shutdown": "pending-close",
            "status": "FAIL",
            "failures": list(failures),
        }
        try:
            os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
            with open(OUT_PATH, "w") as f:
                json.dump(record, f, indent=2)
                f.write("\n")
        except Exception:  # noqa: BLE001
            print("SMOKE: failed to write output file", flush=True)
        print(json.dumps(record, indent=2), flush=True)
        try:
            simulation_app.close(exit_code=1)
            clean_shutdown = True
        except Exception:  # noqa: BLE001
            clean_shutdown = False
        return record


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    res = main()
    with open(OUT_PATH, "w") as f:
        json.dump(res, f, indent=2)
        f.write("\n")
    print(json.dumps({k: v for k, v in res.items() if k != "frames"}, indent=2))
    sys.exit(0 if res["status"] == "PASS" else 1)
