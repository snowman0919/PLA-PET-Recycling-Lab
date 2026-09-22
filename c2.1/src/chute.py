"""VP1 Stage 1: real transfer chute from the S1 discharge opening to the
C2.1 S2 feed mouth, in absolute machine coordinates (new parts, group "feed").

Frozen datums (all measured from the existing geometry, none moved):
- S1 containment interior: x 83..237, y 162.4..324.6, bottom plane z=352.3
  (S1-WALL 160x5x92 at (80,157.4/324.6,352.3); S1-SIDE strips x 80..83 and
  237..240; shafts z=398.30275184708404, cutter sweep bottom z=358.3).
- S2 axis (308.56946468906176, z=280) via c2.1/design/machine_integration.json
  c2_subassembly_transform (180deg about Z + translation).
- S2 feed mouth: the only open arc of the chamber wall, global angles
  20.0..99.5 deg (measured by ray classification of the C2 STEP parts at
  r=64: shell-R2 covers 99.5..176, shell-R1+shear 176..220, screen
  220..320, shell-L 320..20). Chamber shells span y 255..295, r 62.8..65.8;
  outer apex z=345.8. End caps (r 65.6..76.5) occupy y 251..255 and
  295..299, so the chute throat must run inside y 255..295.
- The S1 bottom (352.3) is only 6.5 mm above the shell outer apex (345.8):
  a >=45 deg sliding path from S1 to the mouth is geometrically impossible
  with the frozen datums (a 45deg ramp from (240,352.3) hits the shell arc
  at x~268). This build therefore uses: 45deg intake lips on the S1 opening
  edges, a 45deg in-plan converging pair of guide walls, a flat collection
  pan, and a transfer trough crossing 1.2 mm above the shell outer apex
  with a down-facing outlet over the open mouth arc. The trough slope is a
  DOCUMENTED DEFECT (gravity spill + batch accumulation, no 45deg slide);
  see the Stage 1 report.

Parts (all group "feed", single solids): CHUTE_PAN_FLOOR, CHUTE_LIP_LEFT,
CHUTE_LIP_RIGHT, CHUTE_WALL_FRONT, CHUTE_WALL_REAR, CHUTE_GUIDE_L,
CHUTE_GUIDE_R, CHUTE_TROUGH_WALL_L, CHUTE_TROUGH_WALL_R, CHUTE_TROUGH_FLOOR.
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

V = cq.Vector

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]

S1 = dict(x0=83.0, x1=237.0, y0=162.4, y1=324.6, bottom=352.3,
          wall_y0=157.4, wall_y1=329.6, strip_x0=80.0, strip_x1=240.0)
S2_AX, S2_AZ = 308.56946468906176, 280.0
SHELL_RO = 65.8            # chamber shell outer radius (apex z=345.8)
MOUTH_LO, MOUTH_HI = 20.0, 99.5   # open arc, global degrees
PAN_Z0, PAN_Z1 = 344.5, 348.0   # pan/trough-west floor: 4.3 mm entry under S1 bottom
TROUGH_Z0, TROUGH_Z1 = 347.5, 351.8   # trough-east floor (saddle recess datums)
TROUGH_Y0, TROUGH_Y1 = 255.0, 295.0   # chamber width band (end-cap faces)
WALL_TOP = 352.3                      # flush with the S1 bottom plane
SADDLE_STEP = "c2/cad/C2_THERMAL_SADDLE_R.step"


def _c21_transform(shape):
    """Apply the frozen c2_subassembly_transform to a c2 local-frame part."""
    return (shape.rotate((0, 0, 0), (0, 0, 1), 180)
                 .translate((308.56946468906176, 299, 280)))


def _obstruction_solid():
    """Frozen S2 jacket solids that pierce the chute floor plane: the
    C2_THERMAL_SADDLE_R (body + six fins) and both C2_SADDLE_CAP_R end caps.
    The floor is cut with this compound so the frozen parts pass through by
    construction (zero-volume contact, collision-free)."""
    # c2_process_part imports with a local +4 y offset (process compartment
    # 4..44 -> global mouth band 255..295)
    s = cq.importers.importStep(str(REPO / SADDLE_STEP)).val().translate((0, 4, 0))
    out = _c21_transform(s)
    for y0 in (0.0, 44.0):
        cap = cq.importers.importStep(
            str(REPO / "c2/cad/C2_SADDLE_CAP_R.step")).val().translate((0, y0, 0))
        out = out.fuse(_c21_transform(cap))
    return out


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _prism_xz(points, y0, depth):
    wire = cq.Wire.makePolygon([V(x, y0, z) for x, z in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, depth, 0)).clean()


def _prism_xy(points, z0, height):
    wire = cq.Wire.makePolygon([V(x, y, z0) for x, y in points], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, 0, height)).clean()


def pan_floor():
    """Basin floor: full-width pan under the S1 opening plus the north
    slabs feeding the south-bypass channel.  Notched where the frozen S2
    support structure rises into the floor plane:
    - rear support plate band y 201..213 (plate x>=223.6, chamfer z-x=96.43)
      keeps the full-width slab only to x=245.5;
    - rear fixed ring plate band y 297.5..307.5 (annulus r 63.5..88 reaches
      x>=248.7 at these heights) keeps the slab only to x=246;
    - front fixed ring plate starts at y=327, slab stops at y=326.5.
    The 130deg saddle fin pierces the north slab and is cut out (top 2.1 mm
    below the floor surface)."""
    full = _box(S1["x0"], 245.5, S1["wall_y0"] + 2.0, 326.5, PAN_Z0, PAN_Z1)
    south = _box(244.0, 271.5, S1["wall_y0"] + 2.0, 201.0, PAN_Z0, PAN_Z1)
    north_a = _box(244.0, 271.5, 213.0, 297.5, PAN_Z0, PAN_Z1)
    north_b = _box(244.0, 271.5, 307.5, 326.5, PAN_Z0, PAN_Z1)
    north_a = north_a.cut(_obstruction_solid())
    solids = [x for x in north_a.Solids() if x.Volume() > 10.0]
    if len(solids) != 1:
        raise RuntimeError("pan floor north slab split: %d solids" % len(solids))
    return full.fuse(south).fuse(solids[0]).fuse(north_b).clean()


def bypass_channel_floor():
    """Fin-bypass route floor: y 213..251 (south of the chamber, north of
    the support plate band), x 250.5..360, then the north-turning bend
    block x 350..360.5 over y 244..294.  The 115deg saddle fin (x 272..278,
    y 256..294) is entirely OFF this path - material never crosses it."""
    channel = _box(250.5, 360.0, 213.0, 251.0, PAN_Z0, PAN_Z1)
    bend = _box(350.0, 360.5, 244.0, 294.0, PAN_Z0, PAN_Z1)
    return channel.fuse(bend).clean()


def bypass_wall_south():
    """South channel -Y wall (y 213..215.5, 2 mm clear of the support
    plate face at y=211); the guard envelope y-band starts at 217, so the
    real Stage-2 ring guard (r 90..94) stays clear here."""
    return _box(250.5, 360.0, 213.0, 215.5, PAN_Z0, WALL_TOP)


def bypass_wall_north_lower():
    """South channel +Y wall from the pan to the bend opening at x=348;
    flush against the frozen end-cap face at y=251 (zero-volume contact)."""
    return _box(250.5, 348.0, 248.5, 251.0, PAN_Z0, WALL_TOP)


def bypass_wall_bend_west():
    """Bend west wall: keeps the north turn inside the channel (y 251..294)."""
    return _box(350.0, 352.5, 251.0, 294.0, PAN_Z0, WALL_TOP)


def bypass_wall_bend_east():
    """Bend east dam (x 360..362.5): stops eastward flow; clears the frozen
    saddle L (x>=361.2 at r<=73) and end caps (r<=76.5) at these heights."""
    return _box(360.0, 361.0, 244.0, 294.0, PAN_Z0, WALL_TOP)


def intake_lip():
    """45deg intake lip under the S1 -X side strip (the opening's west edge);
    all other opening edges seal flush under the S1 walls/strips."""
    pts = [(S1["strip_x0"], S1["bottom"]), (87.5, 344.8), (87.5, S1["bottom"])]
    return _prism_xz(pts, S1["wall_y0"] + 2.0, S1["wall_y1"] - S1["wall_y0"] - 4.0)


def _guide(p0, p1):
    """Vertical in-plan guide wall, 3 mm thick, sealed to the S1 bottom."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * 1.5, dx / L * 1.5
    pts = [p0, p1, (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)]
    return _prism_xy(pts, PAN_Z0, WALL_TOP - PAN_Z0)


def guide_left():
    """45deg in-plan guide from the S1 front wall toward the pan throat."""
    return _guide((210.0, S1["y0"]), (248.0, 244.0))


def guide_right():
    """45deg in-plan guide from the S1 rear wall toward the pan throat."""
    return _guide((210.0, S1["y1"]), (248.0, 306.0))


def wall_front():
    """Sealed under the S1 front wall bottom face (y 157.4..162.4)."""
    return _box(S1["x0"], 248.0, S1["wall_y0"], S1["wall_y0"] + 5.0,
                PAN_Z0, WALL_TOP)


def wall_rear():
    """Sealed under the S1 rear wall bottom face (y 324.6..329.6)."""
    return _box(S1["x0"], 248.0, S1["wall_y1"] - 5.0, S1["wall_y1"],
                PAN_Z0, WALL_TOP)


def trough_floor():
    """Landing ledge over the mouth (x 278.5..310, y 255..295); cut where the
    frozen C2_THERMAL_SADDLE_R body pierces the slab.  Its top stays 0.6 mm
    below the ledge surface, so the jacket forms a smooth local recess."""
    slab = _box(278.5, 310.0, TROUGH_Y0, TROUGH_Y1, TROUGH_Z0, TROUGH_Z1)
    cut = slab.cut(_obstruction_solid())
    solids = [x for x in cut.Solids() if x.Volume() > 10.0]
    if len(solids) != 1:
        raise RuntimeError("trough_floor split: %d solids" % len(solids))
    return solids[0].clean()


def components():
    """The chute as welded fabrications: CHUTE_BODY (pan + intake lip +
    sealed walls + guides + fin-bypass channel/bend, fused, cut where the
    frozen S2 jacket passes through) and CHUTE_TROUGH_FLOOR_E retained as
    the bolted outlet section over the mouth (y 255..295, x 278.5..310):
    material leaves the bend at y=294 over the open mouth arc (global
    20..99.5deg) and the east section is the landing ledge beneath the
    spill line.  The 115deg fin is OFF the material path."""
    parts = [pan_floor(), bypass_channel_floor(), intake_lip(),
             wall_front(), wall_rear(), guide_left(), guide_right(),
             bypass_wall_south(), bypass_wall_north_lower(),
             bypass_wall_bend_west(), bypass_wall_bend_east()]
    body = parts[0]
    for s in parts[1:]:
        body = body.fuse(s)
    body = body.cut(_obstruction_solid())
    solids = [x for x in body.Solids() if x.Volume() > 10.0]
    if len(solids) != 1:
        raise RuntimeError("CHUTE_BODY split: %d solids" % len(solids))
    return [("CHUTE_BODY", solids[0].clean()),
            ("CHUTE_TROUGH_FLOOR_E", trough_floor())]


def cutter_sweep_solids():
    """Conservative S1 cutter sweep envelopes for clearance checks."""
    out = []
    for x in (130.0, 190.0):
        out.append(cq.Solid.makeCylinder(41.0, 160.0, V(x, 160.0, 398.30275184708404),
                                         V(0, 1, 0)))
    return out


if __name__ == "__main__":
    import json
    from build_machine_integration import bounds
    parts = components()
    recs = []
    fails = []
    for name, solid in parts:
        ok = solid.isValid() and len(solid.Solids()) == 1
        recs.append({"name": name, "solids": len(solid.Solids()),
                     "valid": solid.isValid(), "bounds": bounds(solid)})
        if not ok:
            fails.append(name)
    sweeps = cutter_sweep_solids()
    clearance = []
    for name, solid in parts:
        for i, sw in enumerate(sweeps, 1):
            b1, b2 = solid.BoundingBox(), sw.BoundingBox()
            overlap = all(min(getattr(b1, a + "max"), getattr(b2, a + "max"))
                          - max(getattr(b1, a + "min"), getattr(b2, a + "min")) > 0
                          for a in "xyz")
            if overlap:
                v = solid.intersect(sw).Volume()
                if v > 1e-6:
                    clearance.append({"part": name, "sweep": "S%d" % i,
                                      "volume_mm3": v})
    result = {"parts": recs, "cutter_sweep_intersections": clearance,
              "passed": not fails and not clearance}
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for name, solid in parts:
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    result["exported_step"] = exported
    (ROOT / "results" / "chute_geometry.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails or clearance:
        raise SystemExit(1)
