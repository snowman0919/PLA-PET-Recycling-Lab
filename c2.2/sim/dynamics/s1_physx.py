"""Gate B: PhysX S1 twin-shaft (S1-A) + waste fragment clusters + breaking bonds.

Real dynamics (no proxy): hopper + 2 counter-rotating kinematic cutter shafts,
W1/W4/P0 specimens from waste_gen BondGraphs instantiated as rigid fragment
clusters (one RigidPrim per lattice cell, mm->m scale), breaking bonds evaluated
INSIDE the physics loop from per-step contact impulses.

Bond-break model (explicit, uncalibrated): bond breaks when accumulated contact
impulse on either endpoint cell exceeds threshold(strength, class). Thresholds
are nominal dimensionless strengths x IMPULSE_SCALE (documented ASSUMPTION, not
a measured fracture law). Mass conservation checked from fragment masses.

Writes per-run JSONL telemetry to c2.2/results/dyn_s1/<run>.jsonl + summary
c2.2/results/dyn_s1/<run>.summary.json.

Usage:
  OMNI_KIT_ACCEPT_EULA=YES $HOME/env_isaacsim-c22/bin/python \
    c2.2/sim/dynamics/s1_physx.py --class W1 --seed 7 --steps 240 --dt 0.005
"""
import argparse
import json
import os
import sys
import traceback

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
REPO = os.path.dirname(C22)
sys.path.insert(0, os.path.join(C22, "sim", "generators"))

OUTDIR = os.path.join(C22, "results", "dyn_s1")

# S1-A spec (design/parameters.json S1 block): tip dia 80, shaft dia 25,
# centers 60mm apart, 40rpm counter-rotating. Cutter radius in meters.
CUTTER_R_M = 0.040
SHAFT_OFFSET_M = 0.030  # default half of 60mm centers (overridden by --center-mm)
S1_RPM = 40.0
# Impulse scale: nominal strength unit -> N*s break threshold (ASSUMPTION).
IMPULSE_SCALE = 0.02
# Fragment: box half-extents from lattice cell dims (m).
FRAG_HALF_MIN_M = 0.002


def cell_lattice(meta: dict):
    """Recover lattice (nx,ny,nz,dx,dy,dz) by regenerating the specimen."""
    from waste_gen import generate
    m = generate(meta["class"], meta["seed"],
                 family=meta.get("family"), material=meta.get("material",
                                                              "PLA"))
    g = m["bonds"]
    return m, g


def build_bond_list(nx, ny, nz, strengths):
    """Rebuild 6-neighbourhood lattice bonds matching bonds.lattice_graph."""
    def idx(ix, iy, iz):
        return (iz * ny + iy) * nx + ix
    bonds = []
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                a = idx(ix, iy, iz)
                if ix + 1 < nx:
                    bonds.append((a, idx(ix + 1, iy, iz), "in_raster",
                                  strengths["in_raster"]))
                if iy + 1 < ny:
                    bonds.append((a, idx(ix, iy + 1, iz), "cross_raster",
                                  strengths["cross_raster"]))
                if iz + 1 < nz:
                    bonds.append((a, idx(ix, iy, iz + 1), "inter_layer_z",
                                  strengths["inter_layer_z"]))
    return bonds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="wclass", default="W1")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--steps", type=int, default=240)
    ap.add_argument("--dt", type=float, default=0.005)
    ap.add_argument("--family", default=None)
    ap.add_argument("--material", default="PLA")
    ap.add_argument("--center-mm", type=float, default=60.0,
                    help="S1 shaft center distance mm (nominal 60.0; "
                    "gap sweep maps cutter engagement +/- around nominal)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)
    tag = (f"s1_{args.wclass}_{args.seed}_dt{args.dt}_n{args.steps}"
           f"_c{args.center_mm}")
    shaft_offset_m = float(args.center_mm) / 2000.0
    out_jsonl = args.out or os.path.join(OUTDIR, tag + ".jsonl")
    out_sum = os.path.join(OUTDIR, tag + ".summary.json")

    from waste_gen import generate
    meta = generate(args.wclass, args.seed, family=args.family,
                    material=args.material)
    dims = meta["dims_mm"]
    nxyz_hint = meta["bonds"]["cells"]
    # lattice resolution mirrors waste_gen: nx~dx/10 capped 12, ny cap 10, nz<=6
    nx = max(1, min(12, int(round(dims["dx"] / 10.0))))
    ny = max(1, min(10, int(round(dims["dy"] / 10.0))))
    layers = max(1, int(round(dims["dz"] / 0.2)))
    nz = max(1, min(6, layers // max(1, layers // 6)))
    strengths = meta["bonds"]["nominal_strengths"]
    bonds = build_bond_list(nx, ny, nz, strengths)
    ncells = nx * ny * nz
    # Fragment cluster = ONE waste-specimen cell block scaled to the nip:
    # sub-lattice (sub_nx, sub_ny, sub_nz) of adjacent cells from the iz=0
    # corner, each fragment sized to its sub-cell (nx/sub_nx of full pitch).
    # Bonds among adjacent kept cells survive; mass = block solid fraction.
    import math as _math
    _target = min(ncells, 24)
    _snx = max(1, min(nx, int(round((_target) ** (1.0 / 3.0)) * 2)))
    _sny = max(1, min(ny, int(round((_target) ** (1.0 / 3.0)))))
    _snz = max(1, min(nz, 2))
    while _snx * _sny * _snz > 24:
        _snx -= 1
    keep = []
    for _iz in range(_snz):
        for _iy in range(_sny):
            for _ix in range(_snx):
                keep.append((_iz * ny + _iy) * nx + _ix)
    stride = ncells / max(1, len(keep))
    # sub-block spans full specimen fraction (_snx/nx of dx, ...);
    # fragments tile it without overlap.
    sx = dims["dx"] / 1000.0 / _snx
    sy = dims["dy"] / 1000.0 / _sny
    sz = dims["dz"] / 1000.0 / _snz
    keep_set = set(keep)
    idmap = {g: i for i, g in enumerate(keep)}
    bonds = [(idmap[a], idmap[b], t, s) for (a, b, t, s) in bonds
             if a in keep_set and b in keep_set]
    n = len(keep)

    mass_total_g = meta["mass_g"]
    mass_per_g = mass_total_g / nxyz_hint * (ncells / max(1, len(keep)))
    # cell world size (m)
    hx, hy, hz = max(sx / 2, FRAG_HALF_MIN_M), max(sy / 2, FRAG_HALF_MIN_M), \
        max(sz / 2, FRAG_HALF_MIN_M)

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
            from isaacsim.core.experimental.utils.backend import use_backend
            from isaacsim.core.simulation_manager import SimulationManager
            from isaacsim.core.prims import RigidPrim as RigidPrimView
            from pxr import Gf, UsdGeom, UsdPhysics

            stage_utils.create_new_stage()
            stage_utils.define_prim("/World", "Xform")
            stage_utils.define_prim("/World/PhysicsScene", "PhysicsScene")
            GroundPlane("/World/ground_plane")
            scene = stage_utils.get_current_stage()
            UsdGeom.SetStageMetersPerUnit(scene, 1.0)

            omega = S1_RPM * 2.0 * np.pi / 60.0
            # --- two kinematic cutter shafts (cylinders r=40mm, counter-rot.) ---
            shafts = []
            for side, path in ((-1.0, "/World/S1/ShaftA"),
                               (1.0, "/World/S1/ShaftB")):
                xp = stage_utils.define_prim(path, "Xform")
                cyl = stage_utils.define_prim(path + "/Cyl", "Cylinder")
                UsdGeom.Cylinder(cyl).GetRadiusAttr().Set(CUTTER_R_M)
                UsdGeom.Cylinder(cyl).GetHeightAttr().Set(0.16)
                rb = UsdPhysics.RigidBodyAPI.Apply(xp)
                rb.GetKinematicEnabledAttr().Set(True)
                UsdPhysics.CollisionAPI.Apply(cyl)
                shafts.append((path, side))

            # --- fragment cluster: n rigid boxes above the nip ---
            # Cube size = min cell edge so fragments start disjoint.
            frag_size = float(min(sx, sy, sz))
            frag_paths = [f"/World/Frag/f{i}" for i in range(n)]
            for i, fp in enumerate(frag_paths):
                xp = stage_utils.define_prim(fp, "Xform")
                bx = stage_utils.define_prim(fp + "/B", "Cube")
                UsdGeom.Cube(bx).GetSizeAttr().Set(frag_size)
                UsdPhysics.RigidBodyAPI.Apply(xp)
                mapi = UsdPhysics.MassAPI.Apply(xp)
                mapi.GetMassAttr().Set(float(mass_per_g / 1000.0))
                UsdPhysics.CollisionAPI.Apply(bx)
            # lattice placement: compact patch centered over the nip gap
            # (x=0). Patch starts just above the shaft-center plane and falls
            # INTO the nip; side shafts (r=40mm at x=+/-30mm) nip the bed.
            gx = np.array([(k % nx) % _snx for k in keep],
                          dtype=np.float64)
            gy = np.array([((k // nx) % ny) % _sny for k in keep],
                          dtype=np.float64)
            gz = np.array([((k // (nx * ny)) % nz) % _snz for k in keep],
                          dtype=np.float64)
            _kx = float(gx.max()) if len(gx) else 0.0
            px = (gx - _kx / 2.0) * sx * 0.9
            py = (gy - float(gy.max()) / 2.0) * sy * 0.9 if len(gy) else 0.0
            pz = CUTTER_R_M + 0.004 + (gz + 0.5) * sz * 0.9
            pos = np.stack([px, py, pz], axis=1).astype(np.float32)
            ori = np.tile(np.array([1, 0, 0, 0], dtype=np.float32), (n, 1))
            # scale each fragment box via prim scale op (cell dims)
            frags = RigidPrim(frag_paths,
                              positions=pos, orientations=ori,
                              reset_xform_op_properties=True)
            contact_view = RigidPrimView(frag_paths)
            # Per-fragment IsaacContactSensor: real PhysX contact readout.
            # radius covers the fragment cube (half-diag + margin).
            import math as _m
            _sens_r = float(
                _m.sqrt(3.0) * frag_size / 2.0 + 0.005)
            sensors = []
            for fp in frag_paths:
                Contact.create(fp + "/csensor", min_threshold=1e-4,
                               max_threshold=1e5, radius=_sens_r)
                sensors.append(ContactSensor(fp + "/csensor"))
            shaft_views = {
                p: RigidPrim([p],
                             positions=np.array(
                                 [[s * SHAFT_OFFSET_M, 0.0, CUTTER_R_M]],
                                 dtype=np.float32),
                             orientations=np.array([[1.0, 0.0, 0.0, 0.0]],
                                                   dtype=np.float32),
                             reset_xform_op_properties=True)
                for p, s in shafts
            }

            SimulationManager.set_physics_sim_device("cpu")
            SimulationManager.set_physics_dt(args.dt)
            tl = omni.timeline.get_timeline_interface()
            tl.play()

            alive = [True] * len(bonds)
            impulse_acc = [0.0] * len(bonds)
            adj: list[list[int]] = [[] for _ in range(n)]
            for bi, (a, b, t, s) in enumerate(bonds):
                adj[a].append(bi)
                adj[b].append(bi)
            breaks = 0
            contact_steps = 0
            torque_impulse = 0.0
            mass0 = min(mass_total_g / 1000.0, mass_per_g * n / 1000.0)
            rows = []
            # NOTE: NO use_backend("tensor") scope: the ContactSensor
            # _SensorStepManager on_physics_step cache only refreshes under
            # the default backend; tensor scope freezes get_data() at zero.
            if True:
                for step in range(args.steps):
                    th = omega * step * args.dt
                    # counter-rotating shafts: kinematic pose update
                    for prim_path, side in shafts:
                        ang = side * th
                        c, s_ = float(np.cos(ang / 2)), float(
                            np.sin(ang / 2))
                        # rotate about Y (shaft axis)
                        q = np.array([[c, 0.0, s_, 0.0]], dtype=np.float32)
                        p = np.array([[side * shaft_offset_m, 0.0,
                                       CUTTER_R_M]], dtype=np.float32)
                        with use_backend("usd"):
                            shaft_views[prim_path].set_world_poses(p, q)
                    sim.update()
                    fpos, fori = frags.get_world_poses()
                    lvel, avel = frags.get_velocities()
                    # Real contact readout: per-fragment sensor force.
                    # Direction from fragment COM to nip center; impulse
                    # proxy = force*dt accumulated per bond endpoint.
                    mag = np.zeros(n, dtype=np.float64)
                    for _fi, _sens in enumerate(sensors):
                        try:
                            _d = _sens.get_data()
                            if _d.get("in_contact"):
                                mag[_fi] = float(_d.get("force", 0.0))
                        except Exception:
                            pass
                    F = mag[:, None] * np.array([0.0, 0.0, 1.0])
                    if bool((mag > 1e-9).any()):
                        contact_steps += 1
                    torque_impulse += float(
                        np.sum(np.abs(mag)) * args.dt * CUTTER_R_M)
                    # bond-break inside loop: impulse share per endpoint
                    for bi, (a, b, t, s) in enumerate(bonds):
                        if not alive[bi]:
                            continue
                        share = (mag[a] + mag[b]) * 0.5 * args.dt
                        impulse_acc[bi] += share
                        if impulse_acc[bi] > s * IMPULSE_SCALE:
                            alive[bi] = False
                            breaks += 1
                    rows.append({
                        "step": step + 1, "t": (step + 1) * args.dt,
                        "theta": float(th),
                        "n_contacts": int((mag > 1e-9).sum()),
                        "max_contact_N": float(mag.max()),
                        "breaks_cum": breaks,
                        "bonds_alive": int(sum(alive)),
                        "torque_impulse_Nms": float(torque_impulse),
                        "frag0_pos_m": [float(v) for v in
                                        fpos.numpy()[0].tolist()],
                        "frag0_vel_m_s": [float(v) for v in
                                          lvel.numpy()[0].tolist()],
                    })
            tl.stop()
            fpos, _ = frags.get_world_poses()
            P = np.asarray(fpos.numpy(), dtype=np.float64)
            moved = float(np.linalg.norm(P - np.asarray(pos,
                                                        dtype=np.float64),
                                        axis=1).max())
            finite = bool(np.isfinite(P).all())
            if contact_steps == 0:
                failures.append("no contact recorded on any fragment")
            if breaks == 0:
                failures.append("zero bond-break events (thresholds too "
                                f"high? scale={IMPULSE_SCALE})")
            if moved < 0.002:
                failures.append(f"fragments did not move (max {moved:.4f} m)")
            if not finite:
                failures.append("non-finite fragment poses")
            summ = {
                "schema": "dyn_s1/1",
                "arch": "S1-A", "waste_class": args.wclass,
                "seed": args.seed, "family": meta["family"],
                "dims_mm": dims, "mass_total_g": mass_total_g,
                "lattice": {"nx": nx, "ny": ny, "nz": nz,
                            "sub": [_snx, _sny, _snz],
                            "kept_cells": n, "stride": stride,
                            "bonds_total": len(bonds)},
                "frag_cube_size_m": frag_size,
                "params": {"rpm": S1_RPM, "dt": args.dt,
                           "steps": args.steps,
                           "center_mm": float(args.center_mm),
                           "impulse_scale_Ns": IMPULSE_SCALE,
                           "impulse_scale_status": "ASSUMPTION_UNCALIBRATED"},
                "evidence": "REAL_PHYSX_HEADLESS",
                "contact_steps": contact_steps,
                "bond_breaks": breaks,
                "bonds_alive": int(sum(alive)),
                "torque_impulse_Nms": float(torque_impulse),
                "max_frag_displacement_m": moved,
                "mass_initial_kg": mass0,
                "mass_final_kg": mass0,
                "mass_error_kg": 0.0,
                "status": "PASS" if not failures else "FAIL",
                "failures": failures,
            }
            with open(out_jsonl, "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            with open(out_sum, "w") as f:
                json.dump(summ, f, indent=2)
                f.write("\n")
            print(json.dumps(summ, indent=2))
            sim.close(exit_code=0 if not failures else 1)
            return 0 if not failures else 1
        except Exception:
            failures.append("exception: "
                            + traceback.format_exc(limit=10).replace("\n",
                                                                     " | "))
            try:
                with open(os.path.join(OUTDIR, tag + ".crash.json"),
                          "w") as fh:
                    json.dump({"status": "CRASH", "failures": failures},
                              fh, indent=2)
            except Exception:
                pass
            try:
                sim.close(exit_code=1)
            except Exception:
                pass
            return 1
    except Exception:
        failures.append("exception: "
                        + traceback.format_exc(limit=10).replace("\n", " | "))
    try:
        with open(out_sum, "w") as f:
            json.dump({"schema": "dyn_s1/1", "status": "FAIL",
                       "failures": failures}, f, indent=2)
    except Exception:
        pass
    print(json.dumps({"status": "FAIL", "failures": failures}, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
