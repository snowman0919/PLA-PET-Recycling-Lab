"""Reviewer scenes for the PPR VP1 full machine (c2.2 acceptance item 2).

Renders four reviewer-readable PNG views of the actual simulated assembly
(c2.2/sim/assets/usd/full_machine.usda):

  (a) full assembly 3/4 view
  (b) drivetrain close-up, mid-rotation (posed at input theta = pi using
      the documented ideal gear/chain ratios)
  (c) transfer/chute view with probe spheres at recorded final positions
      from the newest connected run matching the rendered STEP and USD hashes
  (d) puller/winder view

Renderer policy (assignment): Isaac offscreen capture at modest resolution
FIRST.  The ollama llama-server holds ~7.6 GB of this GPU's 10.2 GB and is
NEVER killed; an earlier full run logged RTX
VkResult ERROR_OUT_OF_DEVICE_MEMORY while merely pumping kit frames at the
1280x720 default.  This script therefore:
  1. tries Isaac RTX offscreen at 640x480 (Replicator rgb annotator)
     unless PPR_FORCE_SOFTWARE_SCENES=1;
  2. on ANY render failure falls back to a deterministic software render
     (painter's algorithm, numpy + PIL) of the USDA collision meshes
     themselves — the exact triangle geometry the simulation collides
     against — with moving bodies posed at the same mid-rotation state
     and probe spheres at their recorded final positions.

The producing tool per scene is recorded in index.json together with the
USD sha.  Output: c2.2/results/full_machine/reviewer_scenes/.

Usage:
  OMNI_KIT_ACCEPT_EULA=YES $HOME/env_isaacsim-c22/bin/python \
    c2.2/sim/render_reviewer_scenes.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve()
SIM = HERE.parent
C22 = SIM.parent
REPO = C22.parent
sys.path.insert(0, str(SIM))

from full_machine import PIVOTS_MM  # noqa: E402

USDA = C22 / "sim" / "assets" / "usd" / "full_machine.usda"
BODIES = C22 / "sim" / "assets" / "out" / "full" / "bodies.json"
RUNS = C22 / "results" / "full_machine"
OUTDIR = C22 / "results" / "full_machine" / "reviewer_scenes"

W, H = 640, 480

# --- scene table (world mm; F0 frame: x machine length, y across, z up) ---
# half_span_mm: orthographic view width shown across the image width.
SCENES = [
    {"id": "a_full_assembly",
     "title": "PPR VP1 full machine - assembly 3/4 view",
     "eye": (1750.0, 1700.0, 1150.0),
     "target": (400.0, 204.0, 240.0),
     "half_span_mm": 620.0},
    {"id": "b_drivetrain_mid_rotation",
     "title": "Drivetrain close-up - mid-rotation (input theta=pi)",
     "eye": (-260.0, 760.0, 520.0),
     "target": (230.0, 383.0, 200.0),
     "half_span_mm": 260.0},
    {"id": "c_transfer_chute_probes",
     "title": "Transfer/chute - probe spheres at recorded final positions",
     "eye": (700.0, 880.0, 700.0),
     "target": (190.0, 250.0, 330.0),
     "half_span_mm": 260.0},
    {"id": "d_puller_winder",
     "title": "Puller/winder end of the line",
     "eye": (1450.0, 1000.0, 560.0),
     "target": (700.0, 180.0, 150.0),
     "half_span_mm": 320.0},
]

# mid-rotation state for scene (b) (identical formulas to verify_full.py)
THETA_MID = math.pi
Q = 8
GEAR_RATIO = -15.0 / 40.0
CHAIN_B = GEAR_RATIO * (24 / 12)
ECC_MM = 7.0
S2_PIVOT = PIVOTS_MM["S2_ECC"]

BODY_ANGLE = {
    "IN_SHAFT": THETA_MID,
    "S1A": GEAR_RATIO * (24 / 24) * THETA_MID,
    "S1B": -GEAR_RATIO * (24 / 24) * THETA_MID,
    "S2_ECC": CHAIN_B * THETA_MID,
    "S2_CARRIER": -(CHAIN_B * THETA_MID) / Q,
    # paddle transfer: 1:1 with the measured S2Ecc angle
    "PADDLE": CHAIN_B * THETA_MID,
    "AUGER": CHAIN_B * THETA_MID / 8.0,
    "CROSS_FEED": CHAIN_B * THETA_MID,
    "CROSS_FEED_IDLER": -CHAIN_B * THETA_MID,
}


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_positions():
    """Use only a connected probe run for this exact STEP and USD."""
    step_sha = json.loads(BODIES.read_text())["source_step_sha256"]
    usd_sha = sha256_file(USDA)
    candidates = sorted(RUNS.glob("run_vp1_final*/results.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        result = json.loads(path.read_text())
        if (result.get("step_sha256") != step_sha
                or result.get("usd_sha256") != usd_sha
                or result.get("steps", 0) < 3200):
            continue
        probes = result["probe_test"]
        pts = [(tuple(s["final_pos_mm"]), s["class"])
               for s in probes["sample_final_positions"]]
        return pts, probes["total"], str(path.relative_to(REPO))
    raise RuntimeError("no connected >=3200-step probe result matches "
                       "the current STEP and USD hashes")


def write_index(scenes_meta, tool, note, probe_pts, probe_total, probe_source):
    index = {
        "schema": "reviewer_scenes/1",
        "machine_usd": "c2.2/sim/assets/usd/full_machine.usda",
        "usd_sha256": sha256_file(USDA),
        "source_step_sha256": json.loads(
            BODIES.read_text())["source_step_sha256"],
        "resolution": "640x480",
        "scene_list": [s["id"] for s in SCENES],
        "scenes": scenes_meta,
        "note": note,
        "probe_spheres": {
            "count_rendered": sum(
                1 for p, _c in probe_pts if p[2] > -50.0),
            "of_total_dropped": probe_total,
            "positions_source": (probe_source + " probe_test."
                                 "sample_final_positions"),
            "render_mode": (
                "projected always-visible overlay discs (white rim) at "
                "the exact recorded final positions; occlusion against "
                "near geometry disabled so the 3mm/1.5mm fragments stay "
                "visible at 640x480"),
        },
    }
    (OUTDIR / "index.json").write_text(json.dumps(index, indent=2) + "\n")


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    probe_pts, probe_total, probe_source = probe_positions()

    tool = ""
    note = ""
    rtx_ok = False
    scenes_meta = []
    if os.environ.get("PPR_FORCE_SOFTWARE_SCENES"):
        scenes_meta, tool = software_capture(probe_pts, probe_total)
        note = ("Isaac RTX capture skipped (PPR_FORCE_SOFTWARE_SCENES); "
                "GPU memory is committed to the ollama llama-server, "
                "~7.6/10.2 GB, never killed.")
    else:
        try:
            scenes_meta, tool, rtx_ok, note = isaac_capture(
                probe_pts, probe_total, probe_source)
            # on rtx_ok False the in-session fallback has already run and
            # written the fallback PNGs + index BEFORE sim.close(); the
            # returned scenes_meta/tool/note already describe the fallback
        except Exception:
            # close() survived but returned a failure, or the session
            # died before any fallback: pure software render (no kit)
            traceback.print_exc()
            note = ("Isaac RTX session did not produce scenes (GPU "
                    "memory committed to the ollama llama-server, "
                    "~7.6/10.2 GB, never killed); fell back to "
                    "deterministic software render of the USDA "
                    "collision meshes.")
            scenes_meta, tool = software_capture(probe_pts, probe_total)
            rtx_ok = False

    if not scenes_meta:
        return 1
    if rtx_ok:
        note = ""
    write_index(scenes_meta, tool, note, probe_pts, probe_total, probe_source)
    print(json.dumps({"scenes": [s["id"] for s in scenes_meta],
                      "tool": tool}, indent=2))
    ok = all(s.get("status") == "ok" for s in scenes_meta)
    return 0 if ok else 1


# --------------------------------------------------------------------------
# Path 1: Isaac RTX offscreen capture
# --------------------------------------------------------------------------

def isaac_capture(probe_pts, probe_total, probe_source):
    """RTX attempt with a disk heartbeat.

    Kit quirk on this host: exceptions raised inside a try block are
    SWALLOWED when sim.close() runs (process exits 0, traceback never
    surfaces).  Nothing here relies on exception propagation: the
    per-scene status is written to OUTDIR/.isaac_status.json on disk
    before every risky step and after every scene, and main() falls back
    to the software renderer whenever the file is missing or says ok
    false after close.
    """
    import faulthandler
    faulthandler.enable()
    status_path = OUTDIR / ".isaac_status.json"
    tool = (f"isaacsim 6.1 RTX offscreen (SimulationApp headless, {W}x{H}, "
            f"Replicator rgb annotator), produced by "
            f"c2.2/sim/render_reviewer_scenes.py")

    def record(ok, scenes, phase):
        status_path.write_text(json.dumps(
            {"ok": ok, "phase": phase, "scenes": scenes,
             "tool": tool}, indent=2) + "\n")

    record(False, [], "starting")
    from isaacsim import SimulationApp
    sim = SimulationApp({"headless": True, "width": W, "height": H})
    scenes_meta = []
    rtx_ok = False
    note = ""
    try:
        import numpy as np
        import omni.timeline
        import omni.physx
        from PIL import Image
        from pxr import Gf, UsdGeom
        from isaacsim.core.experimental.utils import stage as stage_utils
        from isaacsim.core.simulation_manager import SimulationManager

        stage_utils.open_stage(str(USDA))
        stage = stage_utils.get_current_stage(backend="usd")
        stage_id = stage_utils.get_stage_id(stage)
        omni.physx.get_physx_simulation_interface().attach_stage(stage_id)
        SimulationManager.set_physics_sim_device("cpu")
        omni.timeline.get_timeline_interface().play()
        for _ in range(5):
            sim.update()  # pump kit+physics so the tensor backend binds

        import omni.physics.tensors as pt
        sv = pt.create_simulation_view("numpy")
        av = sv.create_articulation_view(["/World/F0/Machine"])
        kv = sv.create_rigid_body_view(
            ["/World/F0/S2_ROTOR"] +
            [f"/World/F0/S2_ROLLER_{k}" for k in range(1, 7)])
        # NO exceptions inside the kit session: this build hard-exits
        # (exit 0, nothing after) once any exception has been raised
        # before sim.close(), caught or not.  Every failure below is
        # recorded via record(False, ...) and the loop skips gracefully.
        if av is None or kv is None:
            record(False, scenes_meta,
                   "failed:tensor views unavailable "
                   "(no sim.update pumps / backend not bound)")
        else:
            th = THETA_MID
            dof = [th,
                   GEAR_RATIO * (24 / 24) * th,
                   -GEAR_RATIO * (24 / 24) * th,
                   CHAIN_B * th,
                   -(CHAIN_B * th) / Q]
            av.set_dof_positions(np.array([dof], dtype=np.float32),
                                 np.arange(5, dtype=np.int32))
            bodies = json.loads(BODIES.read_text())
            roller_offsets = {}
            for s in bodies["solids"]:
                if s["body"].startswith("S2_ROLLER"):
                    b = s["part_bbox"]
                    roller_offsets[s["body"]] = (
                        (b[0] + b[3]) / 2, (b[1] + b[4]) / 2,
                        (b[2] + b[5]) / 2)
            a = -th / Q
            qa = (0.0, math.sin(a / 2), 0.0, math.cos(a / 2))
            pos = (S2_PIVOT[0] - ECC_MM * math.cos(th), S2_PIVOT[1],
                   S2_PIVOT[2] + ECC_MM * math.sin(th))
            kin = np.zeros((7, 7), dtype=np.float32)
            kin[0, :3] = pos
            kin[0, 3:] = qa
            for k in range(1, 7):
                d = roller_offsets[f"S2_ROLLER_{k}"]
                dx = d[0] - S2_PIVOT[0]
                dz = d[2] - S2_PIVOT[2]
                ca, sa = math.cos(a), math.sin(a)
                kin[k, 0] = S2_PIVOT[0] + ca * dx + sa * dz
                kin[k, 1] = d[1]
                kin[k, 2] = S2_PIVOT[2] - sa * dx + ca * dz
                kin[k, 3:] = qa
            kv.set_kinematic_targets(kin, np.arange(7, dtype=np.int32))
            sv.step(1.0 / 60.0)
        record(False, scenes_meta, "posed")

        # probe spheres at recorded final positions (scene c)
        for i, (pos_mm, cls) in enumerate(probe_pts):
            x, y, z = pos_mm
            p = stage.DefinePrim(f"/World/SceneProbe/p{i}", "Sphere")
            UsdGeom.Sphere(p).GetRadiusAttr().Set(
                3.0 if cls == "d3" else 1.5)
            xf = UsdGeom.Xformable(p)
            xf.ClearXformOpOrder()
            xf.AddTranslateOp().Set(Gf.Vec3d(float(x), float(y), float(z)))

        import omni.replicator.core as rep
        for sc in SCENES:
            record(False, scenes_meta, f"rendering:{sc['id']}")
            try:
                cam_path = f"/Session/{sc['id']}_cam"
                cam = stage.DefinePrim(cam_path, "Camera")
                xf = UsdGeom.Xformable(cam)
                xf.ClearXformOpOrder()
                xf.AddTransformOp().Set(
                    look_at_matrix(sc["eye"], sc["target"]))
                rp = rep.create.render_product(cam_path, (W, H))
                ann = rep.AnnotatorRegistry.get_annotator("rgb")
                ann.attach(rp)
                rep.orchestrator.step(rt_subframes=32)
                data = np.asarray(ann.get_data())
                img_path = OUTDIR / f"{sc['id']}.png"
                if data.dtype != np.uint8 or data.size < 16:
                    # no raise — record and continue
                    scenes_meta.append(
                        {"id": sc["id"], "title": sc["title"],
                         "image": f"{sc['id']}.png",
                         "producing_tool": tool,
                         "status": "RENDER_FAILED: no RTX pixels "
                                   "(GPU out of memory)"})
                else:
                    Image.fromarray(
                        data.reshape(data.shape[0], data.shape[1], -1)
                        [:, :, :3]).save(img_path)
                    ann.detach()
                    rep.create.destroy_render_product(rp)
                    scenes_meta.append(
                        {"id": sc["id"], "title": sc["title"],
                         "image": img_path.name, "producing_tool": tool,
                         "status": "ok"})
            except Exception as exc:
                scenes_meta.append({"id": sc["id"], "title": sc["title"],
                                    "image": f"{sc['id']}.png",
                                    "producing_tool": tool,
                                    "status": f"RENDER_FAILED: "
                                              f"{type(exc).__name__}: "
                                              f"{exc}"[:200]})
            record(False, scenes_meta, f"done:{sc['id']}")
        rtx_ok = bool(scenes_meta) and all(
            s["status"] == "ok" for s in scenes_meta)
        if not rtx_ok:
            # fallback BEFORE close: the software render needs no kit, and
            # the index written here survives even if close() hard-exits
            # (this build exits 0 and skips everything after close once
            # any in-session exception occurred, caught or not)
            fails = [s["status"] for s in scenes_meta
                     if s["status"] != "ok"]
            rtx_note = ("Isaac RTX offscreen render failed: "
                        + "; ".join(fails)[:300]
                        + " (GPU memory committed to the ollama "
                          "llama-server, ~7.6/10.2 GB, never killed); "
                          "fell back to deterministic software render "
                          "of the USDA collision meshes.")
            scenes_meta, tool = software_capture(probe_pts, probe_total)
            note = rtx_note
            write_index(scenes_meta, tool, rtx_note, probe_pts,
                        probe_total, probe_source)
            record(True, scenes_meta, "fallback_done")
    except Exception as exc:  # noqa: BLE001 - never reach sim.close
        # an exception that propagates past the finally below is
        # swallowed by the kit (process exits 0, nothing runs after) —
        # record the failure and fall back HERE, before close
        record(False, scenes_meta,
               f"failed:{type(exc).__name__}: {str(exc)[:150]}")
        try:
            rtx_note = (f"Isaac RTX session failed "
                        f"({type(exc).__name__}: {str(exc)[:120]}); "
                        f"fell back to deterministic software render of "
                        f"the USDA collision meshes.")
            scenes_meta, tool = software_capture(probe_pts, probe_total)
            note = rtx_note
            write_index(scenes_meta, tool, rtx_note, probe_pts,
                        probe_total, probe_source)
            record(True, scenes_meta, "fallback_done_after_exception")
        except Exception:
            pass
    finally:
        sim.close()
    # normal completion path (only reached when the session closed
    # cleanly); the in-memory scenes_meta already reflects any in-session
    # fallback
    return scenes_meta, tool, rtx_ok, note


def look_at_matrix(eye, target):
    """USD camera world matrix (camera looks down -Z, up = +Z world)."""
    from pxr import Gf
    eye = Gf.Vec3d(*[float(v) for v in eye])
    fwd = Gf.Vec3d(*[float(t - e) for t, e in zip(target, eye)])
    fwd = fwd.GetNormalized()
    xax = Gf.Cross(fwd, Gf.Vec3d(0.0, 0.0, 1.0)).GetNormalized()
    yax = Gf.Cross(Gf.Vec3d(-fwd), xax)
    zax = Gf.Vec3d(-fwd)
    return Gf.Matrix4d(
        xax[0], xax[1], xax[2], 0.0,
        yax[0], yax[1], yax[2], 0.0,
        zax[0], zax[1], zax[2], 0.0,
        eye[0], eye[1], eye[2], 1.0)


# --------------------------------------------------------------------------
# Path 2: deterministic software render of the USDA collision meshes
# --------------------------------------------------------------------------

def rot_y_about(v, ang):
    """Rotate Nx3 points about the +Y axis through the origin."""
    import numpy as np
    c, s = math.cos(ang), math.sin(ang)
    out = v.copy()
    dx = out[:, 0]
    dz = out[:, 2]
    out[:, 0] = c * dx + s * dz
    out[:, 2] = -s * dx + c * dz
    return out

def rot_x_about(v, ang):
    """Rotate Nx3 points about the +X axis through the origin."""
    import numpy as np
    c, s = math.cos(ang), math.sin(ang)
    out = v.copy()
    out[:, 1] = c * v[:, 1] - s * v[:, 2]
    out[:, 2] = s * v[:, 1] + c * v[:, 2]
    return out


def software_capture(probe_pts, probe_total):
    import numpy as np
    from pxr import Usd, UsdGeom

    tool = (f"deterministic software render (painter's algorithm, "
            f"numpy+PIL, {W}x{H}) of the USDA collision meshes, produced "
            f"by c2.2/sim/render_reviewer_scenes.py")
    stage = Usd.Stage.Open(str(USDA))
    bodies_json = json.loads(BODIES.read_text())
    roller_rest = {}
    for s in bodies_json["solids"]:
        if s["body"].startswith("S2_ROLLER"):
            b = s["part_bbox"]
            roller_rest[s["body"]] = (
                (b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2)

    th = THETA_MID
    a = -th / Q  # kinematic rotor/roller rotation about +Y

    meshes = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Mesh):
            continue
        gm = UsdGeom.Mesh(prim)
        pts = gm.GetPointsAttr().Get()
        idx = gm.GetFaceVertexIndicesAttr().Get()
        cnt = gm.GetFaceVertexCountsAttr().Get()
        if not cnt or pts is None or len(pts) == 0:
            continue
        path = str(prim.GetPath())
        v = np.asarray(pts, dtype=np.float64)
        if path.startswith("/World/F0/") and "/Static/" not in path \
                and "/Probe/" not in path:
            body = path.split("/")[3]
            if body == "S2_ROTOR":
                # authored rest pose = orbit position at theta=0 (body
                # origin at axis - e*x-hat); at theta the origin sits at
                # pos(th) and the local points spin by a about +Y
                origin = (S2_PIVOT[0] - ECC_MM * math.cos(th),
                          S2_PIVOT[1],
                          S2_PIVOT[2] + ECC_MM * math.sin(th))
                v = rot_y_about(v, a) + np.array(origin)
            elif body.startswith("S2_ROLLER"):
                rest = roller_rest.get(body)
                if rest is None:
                    rest = (v[:, 0].mean(), v[:, 1].mean(), v[:, 2].mean())
                cd = (rest[0] - S2_PIVOT[0], rest[2] - S2_PIVOT[2])
                ca, sa = math.cos(a), math.sin(a)
                origin = (S2_PIVOT[0] + ca * cd[0] + sa * cd[1],
                          rest[1],
                          S2_PIVOT[2] - sa * cd[0] + ca * cd[1])
                v = rot_y_about(v, a) + np.array(origin)
            elif body in BODY_ANGLE:
                piv = PIVOTS_MM[body]
                rotated = (rot_x_about(v, BODY_ANGLE[body]) if body == "AUGER"
                           else rot_y_about(v, BODY_ANGLE[body]))
                v = rotated + np.array(piv)
            # else: authored pose
        else:
            m = np.array(UsdGeom.Xformable(prim)
                         .ComputeLocalToWorldTransform(0.0),
                         dtype=np.float64)
            v = v @ m[:3, :3].T + m[:3, 3]
        meshes.append((path, v, list(idx), list(cnt)))

    scenes_meta = render_all(meshes, probe_pts, tool)
    return scenes_meta, tool


def render_all(meshes, probe_pts, tool):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)

    # probe spheres at recorded positions — rendered as a projected
    # OVERLAY (small filled discs with a white rim, always drawn on top)
    # so the 3mm/1.5mm fragments stay visible through near geometry; the
    # disc centre is the exact projected recorded position and the
    # overlay choice is documented in index.json.  Probes that fell
    # through the world floor (z << 0) are skipped (they would land far
    # outside the ortho window anyway).
    probe_marks = []
    for k, (pos_mm, cls) in enumerate(probe_pts):
        x, y, z = pos_mm
        if z < -50.0:
            continue
        probe_marks.append((np.array([x, y, z]), cls))

    scenes_meta = []
    light = np.array([-0.2, -0.6, 0.775])
    light /= np.linalg.norm(light)
    for sc in SCENES:
        eye = np.array(sc["eye"])
        tgt = np.array(sc["target"])
        fwd = tgt - eye
        fwd /= np.linalg.norm(fwd)
        right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)

        scale = W / (2.0 * sc["half_span_mm"])
        ys_span = sc["half_span_mm"] * H / W
        cx = float((tgt - eye) @ right)
        cy = float((tgt - eye) @ up)

        tris = []
        for path, verts, idx, cnt in meshes:
            if len(verts) == 0 or not idx or not cnt:
                continue  # degenerate authored prim
            if path.startswith("/Probe"):
                color = (204, 92, 58)
            elif "CHUTE_" in path or "AUG_" in path or "CROSS_FEED" in path:
                color = (211, 152, 70)
            elif "/Static/" in path:
                color = (174, 182, 190)
            elif "S2_ROTOR" in path or "S2_ROLLER" in path:
                color = (92, 156, 170)
            else:
                color = (90, 134, 164)
            rel = verts - eye
            px = rel @ right
            py = rel @ up
            dep = rel @ fwd
            j = 0
            for c in cnt:
                c = int(c)
                if c < 3:
                    j += c
                    continue
                if j + 3 > len(idx):
                    continue  # malformed tail window
                tri = np.asarray(idx[j:j + 3], dtype=int)
                if len(tri) < 3:
                    continue
                j += c
                p0 = verts[tri[0]]
                n = np.cross(verts[tri[1]] - p0, verts[tri[2]] - p0)
                ln = float(np.linalg.norm(n))
                if ln < 1e-12:
                    continue
                n /= ln
                if float(n @ fwd) > 1e-9:  # backface w.r.t. view dir
                    continue
                xs3 = px[tri]
                if xs3.max() < cx - sc["half_span_mm"] or \
                        xs3.min() > cx + sc["half_span_mm"]:
                    continue
                ys3 = py[tri]
                if ys3.max() < cy - ys_span or ys3.min() > cy + ys_span:
                    continue
                shade = 0.62 + 0.38 * max(0.0, float(n @ light))
                col = tuple(min(255, int(vv * shade)) for vv in color)
                tris.append((float(dep[tri].mean()), xs3, ys3, col))
        # painter's algorithm: depth along the view dir grows with
        # distance, so draw far (large depth) first
        tris.sort(key=lambda q: -q[0])
        im = Image.new("RGB", (W, H), (250, 250, 248))
        dr = ImageDraw.Draw(im)
        for _d, xs3, ys3, col in tris:
            pts2 = [(W / 2 + (x - cx) * scale,
                     H / 2 - (y - cy) * scale) for x, y in zip(xs3, ys3)]
            dr.polygon(pts2, fill=col)
        dr.text((12, 10), sc["title"], font=font, fill=(35, 48, 55))
        dr.text((12, 30),
                "orthographic | mm | collision meshes from "
                "full_machine.usda",
                font=font, fill=(120, 128, 134))
        # probe overlay: exact projected positions, always on top
        rr = 9 if sc["id"] == "c_transfer_chute_probes" else 0
        if probe_marks:
            shown = 0
            for pos, cls in probe_marks:
                rel = pos - eye
                sx = float(rel @ right)
                sy = float(rel @ up)
                if abs(sx - cx) > sc["half_span_mm"] or \
                        abs(sy - cy) > ys_span:
                    continue
                x2 = W / 2 + (sx - cx) * scale
                y2 = H / 2 - (sy - cy) * scale
                dr.ellipse([x2 - rr, y2 - rr, x2 + rr, y2 + rr],
                           fill=(222, 62, 30), outline=(255, 255, 255),
                           width=2)
                shown += 1
            if sc["id"] == "c_transfer_chute_probes":
                dr.text((12, 48),
                        f"orange discs: recorded probe final positions "
                        f"({shown}/{len(probe_marks)} shown)",
                        font=font, fill=(222, 62, 30))
        out = OUTDIR / f"{sc['id']}.png"
        im.save(out)
        scenes_meta.append({"id": sc["id"], "title": sc["title"],
                            "image": out.name, "producing_tool": tool,
                            "status": "ok"})
    return scenes_meta


if __name__ == "__main__":
    raise SystemExit(main())