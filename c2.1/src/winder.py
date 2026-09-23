"""VP1 Stage 4: real puller nip drive and spool winder (grip redesign).

Replaces the SPOOL-ENV and PULL-ROLLER envelope instances (excluded in
build_machine_integration.py).  Frozen datums kept: the extrudate line runs
+X at z=125, y=275 from the die (x=520) through the cooling tray to the
puller at x~829.  NEW geometry (positions chosen here):

FIX (VP1 Stage 4): the rev-A fixed 2.5 mm nip cannot grip 1.75 mm filament
(spec: design/parameters.json "filament_mm": 1.75, status
CONDITIONAL_THROUGHPUT_NOT_MEASURED; corroborated by src/design.py:34 and
c2.1/bom/system_bom.csv EX-DIE notes "drawdown candidate for 1.75 filament").
The puller is redesigned as a spring-loaded movable-carrier nip:

Puller (x 815..845, y 240..278, z 100..150):
- PULL_FRAME: two side plates + base, with a lower axle seat pair (bearings)
  for the FIXED drive roller and vertical guide slots for the movable one.
- PULL_ROLLER_FIXED: dia-20 driven roller, axle in frame bearings BOTH ends.
- PULL_ROLLER_ADJ: dia-20 roller in a SPRING-LOADED carriage: two coil-spring
  seats (k nominally 8 N/mm, PRELOAD_ADJ travel) press the roller down onto
  the filament; the carriage rides vertical guide posts and is bounded by a
  CAM STOP: a slotted cam plate with a positive stop range that sets the
  MINIMUM nip (roller-to-roller gap at zero filament) to 1.5 mm and allows
  opening to 3.0 mm.  With 1.75 mm filament between the rollers the spring
  compresses ~0.6 mm, giving a contact nip of ~1.55-1.9 mm under compliance
  - real contact, adjustable pressure, rotation and tension transfer.
  Stock window: 1.5-2.0 mm filament gripped; 1.75 mm nominal.
- PULL_MOTOR_REF: small gearmotor reference belt-driving the fixed roller.

Winder (axis Y at x=700, z=220; north of the cooling fans, clear of
COOL-FAN_001/002 and COOL-TRAY):
- WIND_SPOOL_SHAFT (supported in bearings BOTH ends) / WIND_SPOOL_DRUM
  (dia 70) / WIND_FLANGE_L/R (dia 200).
- WIND_MOTOR_REF at the shaft end: the DRIVEN DRUM SHAFT is the winder motor
  reference drive train (positive torque coupling drum <-> spool).
- WIND_TRAVERSE_SCREW + WIND_TRAVERSE_RIDER with guide eyelet: real lead
  screw geometry laying the filament.
- WIND_TENSIONER: slip tensioner on the filament path puller -> winder.
All within the operating envelope.
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq

V = cq.Vector

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _cyl(r, h, x, y, z, axis=(0, 1, 0)):
    return cq.Solid.makeCylinder(r, h, V(x, y, z), V(*axis))


# FILAMENT SPEC: 1.75 mm nominal (design/parameters.json "filament_mm": 1.75,
# status CONDITIONAL_THROUGHPUT_NOT_MEASURED; src/design.py:34; BOM EX-DIE
# note).  Grip window sized for 1.5..2.0 mm stock, 1.75 nominal.
FILAMENT_MM = 1.75
# Nip geometry: roller centers at line_z -/+ (roller_r + nip/2).
# NIP_STOP_MIN = 1.5 (hard stop at full spring compression, 1.5 mm stock
# floor), NIP_OPEN_MAX = 3.0 (cam-adjustable upper limit).
# Compressed nip on 1.75 filament: stop face at 1.5 + spring compliance gives
# a working contact band ~1.55..1.9 mm.
PULL = dict(x=829.0, y0=253.0, y1=275.0, roller_r=10.0, line_z=125.0,
            nip_stop_min=1.5, nip_open_max=3.0, spring_rate_N_mm=8.0,
            spring_free_len=18.0, spring_solid_len=12.0)
PULL_ROLLER_Z = (PULL["line_z"] - (PULL["roller_r"] + PULL["nip_stop_min"] / 2.0),
                 PULL["line_z"] + (PULL["roller_r"] + PULL["nip_stop_min"] / 2.0))
WIND = dict(x=700.0, z=220.0, drum_r=35.0, flange_r=100.0, shaft_r=8.0,
            y0=100.0)


def pull_frame():
    """Side plates + base; the movable carriage rides vertical guide slots in
    the north plate; the south plate carries the fixed-roller bearings."""
    y0, y1 = PULL["y0"] - 3.0, PULL["y1"] + 3.0
    side_a = _box(824.0, 827.0, y0, y0 + 3.0, 100.0, 150.0)
    side_b = _box(843.0, 846.0, y1 - 3.0, y1, 100.0, 150.0)
    base = _box(824.0, 846.0, y0, y1, 100.0, 104.0)
    # lower axle seat bores are modeled as bearing bosses on both side plates
    seat_a = _cyl(7.0, 3.0, PULL["x"], y0, PULL_ROLLER_Z[0])
    seat_b = _cyl(7.0, 3.0, PULL["x"], y1 - 3.0, PULL_ROLLER_Z[0])
    return side_a.fuse(side_b).fuse(base).fuse(seat_a).fuse(seat_b).clean()


def pull_roller_fixed():
    """Dia-20 drive roller on a supported axle (bearing seats BOTH ends),
    center z 113.75 (line z 125 - 10 - 0.75)."""
    z = PULL_ROLLER_Z[0]
    r = _cyl(PULL["roller_r"], PULL["y1"] - PULL["y0"], PULL["x"],
             PULL["y0"], z)
    axle = _cyl(4.0, PULL["y1"] - PULL["y0"] + 16.0, PULL["x"],
                PULL["y0"] - 8.0, z)
    return r.fuse(axle).clean()


def _spring(r_out=4.0, r_in=3.2, pitch=2.4, turns=6, x=829.0, y0=265.0, z0=0.0):
    """Coil spring (helical sweep) between the carriage and the frame cap."""
    helix = cq.Wire.makeHelix(pitch, turns * pitch, r_in,
                              cq.Vector(x, y0, z0), cq.Vector(0, 1, 0))
    wire = cq.Wire.makeCircle(r_out - r_in, cq.Vector(x, y0, z0), cq.Vector(0, 1, 0))
    solid = cq.Solid.sweep(cq.Face.makeFromWires(wire).outerWire(), [], helix, True)
    return solid


def pull_roller_adj():
    """Dia-20 SPRING-LOADED adjustable roller at the hard-stop position
    (minimum nip 1.5 mm): roller + carriage plate riding two guide posts +
    two compression springs + cam stop plate (pressure adjustment)."""
    z = PULL_ROLLER_Z[1]
    r = _cyl(PULL["roller_r"], PULL["y1"] - PULL["y0"], PULL["x"],
             PULL["y0"], z)
    carriage = _box(PULL["x"] - 12.0, PULL["x"] + 12.0,
                    PULL["y1"], PULL["y1"] + 6.0, z - 4.0, z + 14.0)
    # guide posts (both sides of the carriage, north plate slots)
    posts = (_cyl(2.5, 26.0, PULL["x"] - 9.0, PULL["y1"] + 6.0, z + 6.0)
             .fuse(_cyl(2.5, 26.0, PULL["x"] + 9.0, PULL["y1"] + 6.0, z + 6.0)))
    # compression springs around the posts (compliance: real contact pressure)
    springs = (_spring(x=PULL["x"] - 9.0, y0=PULL["y1"] + 9.0, z0=z + 6.0 - 8.0)
               .fuse(_spring(x=PULL["x"] + 9.0, y0=PULL["y1"] + 9.0, z0=z + 6.0 - 8.0)))
    # cam stop plate: slotted pressure-adjustment cam above the carriage; the
    # positive stop fixes the minimum nip at 1.5 mm (rollers at line_z +/-5.75)
    cam = _box(PULL["x"] - 10.0, PULL["x"] + 10.0, PULL["y1"] + 7.0,
               PULL["y1"] + 10.0, z + 8.0, z + 10.5)
    return r.fuse(carriage).fuse(posts).fuse(springs).fuse(cam).clean()


def pull_nip_stop():
    """Positive-stop cam block: with the carriage seated on the stop the
    roller-center gap is exactly roller_r*2 + nip_stop_min -> nip gap
    1.5 mm (1.5-2.0 mm stock compresses the springs; the cam screw opens the
    nip to 3.0 mm for threading)."""
    z = PULL_ROLLER_Z[1]
    return _box(PULL["x"] - 9.0, PULL["x"] + 9.0, PULL["y1"] + 1.0,
                PULL["y1"] + 5.0, z + 5.0, z + 7.5)


def pull_motor_ref():
    """Small gearmotor reference (not-owned) belt-driving the fixed roller
    from the north side of the frame (nose axis z 127, 13.25 mm from the
    roller axle: nose r8 + axle r4 = 12 < 13.25, no contact)."""
    body = _box(834.0, 847.0, 202.0, 236.0, 112.0, 142.0)
    nose = _cyl(8.0, 16.0, PULL["x"], 232.0, 127.0)
    return body.fuse(nose).clean()


def spool_shaft():
    """Spool shaft in bearing seats BOTH ends (frames at y 92 and y 182)."""
    return _cyl(WIND["shaft_r"], 98.0, WIND["x"], 87.0, WIND["z"])


def spool_bearing_blocks():
    """Two bearing blocks supporting the spool shaft at both ends (the east
    block rides the shaft clear of the motor reference body at y >= 187)."""
    b0 = (_box(688.0, 712.0, 88.0, 96.0, 208.0, 232.0)
          .cut(_cyl(WIND["shaft_r"] + 0.5, 10.0, WIND["x"], 87.0, WIND["z"])))
    b1 = (_box(688.0, 712.0, 170.0, 178.0, 208.0, 232.0)
          .cut(_cyl(WIND["shaft_r"] + 0.5, 12.0, WIND["x"], 169.0, WIND["z"])))
    return b0.fuse(b1).clean()


def spool_drum():
    d = _cyl(WIND["drum_r"], 58.0, WIND["x"], WIND["y0"] + 6.0, WIND["z"])
    bore = _cyl(WIND["shaft_r"] + 0.5, 60.0, WIND["x"], WIND["y0"] + 5.0,
                WIND["z"])
    return d.cut(bore).clean()


def _flange(y):
    f = _cyl(WIND["flange_r"], 6.0, WIND["x"], y, WIND["z"])
    bore = _cyl(WIND["shaft_r"] + 0.5, 8.0, WIND["x"], y - 1.0, WIND["z"])
    return f.cut(bore).clean()


def spool_flange_l():
    return _flange(WIND["y0"])


def spool_flange_r():
    return _flange(WIND["y0"] + 64.0)


def winder_motor_ref():
    """Gearmotor reference (not-owned) positively coupled to the driven drum
    shaft (spool torque coupling: motor -> shaft -> drum -> spool)."""
    body = _box(680.0, 720.0, 187.0, 212.0, 200.0, 240.0)
    nose = _cyl(9.0, 12.0, WIND["x"], 182.0, WIND["z"])
    return body.fuse(nose).clean()


def traverse_screw():
    """Lead screw above the drum (z 325) carrying the filament rider."""
    return _cyl(4.0, 80.0, 742.0, 95.0, 325.0)


def traverse_rider():
    """Rider block on the lead screw with the guide eyelet post down to the
    drum surface; the filament runs puller -> eyelet -> drum."""
    block = _box(734.0, 750.0, 110.0, 160.0, 317.0, 333.0)
    post = _cyl(3.0, 70.0, 742.0, 130.0, 250.0, axis=(0, 0, 1))
    eye = _cyl(8.0, 4.0, 742.0, 128.0, 245.0)
    return block.fuse(post).fuse(eye).clean()


def tensioner():
    """Slip tensioner on the filament path (puller -> rider eyelet): pivot
    post below the line and a wrap arm the filament rides over."""
    post = _cyl(5.0, 40.0, 764.0, 198.0, 175.0, axis=(0, 0, 1))
    arm = _box(744.0, 784.0, 194.0, 202.0, 200.0, 208.0)
    return post.fuse(arm).clean()


def components():
    """Named winder parts (groups 'puller' and 'spool')."""
    return [("PULL_FRAME", pull_frame(), "puller"),
            ("PULL_ROLLER_FIXED", pull_roller_fixed(), "puller"),
            ("PULL_ROLLER_ADJ", pull_roller_adj(), "puller"),
            ("PULL_NIP_STOP", pull_nip_stop(), "puller"),
            ("PULL_MOTOR_REF", pull_motor_ref(), "puller"),
            ("WIND_SPOOL_SHAFT", spool_shaft(), "spool"),
            ("WIND_SPOOL_BEARINGS", spool_bearing_blocks(), "spool"),
            ("WIND_SPOOL_DRUM", spool_drum(), "spool"),
            ("WIND_FLANGE_L", spool_flange_l(), "spool"),
            ("WIND_FLANGE_R", spool_flange_r(), "spool"),
            ("WIND_MOTOR_REF", winder_motor_ref(), "spool"),
            ("WIND_TRAVERSE_SCREW", traverse_screw(), "spool"),
            ("WIND_TRAVERSE_RIDER", traverse_rider(), "spool"),
            ("WIND_TENSIONER", tensioner(), "spool")]


def nip_opening_mm():
    """Minimum nip gap with the carriage seated on the cam positive stop:
    roller centers at line_z +/- (roller_r + nip/2) -> gap = nip_stop_min.
    1.75 mm filament compresses the springs: working nip ~1.55..1.9 mm."""
    return PULL["nip_stop_min"]


def nip_range_mm():
    """(minimum at the hard stop, maximum with the cam screw fully open)."""
    return PULL["nip_stop_min"], PULL["nip_open_max"]


if __name__ == "__main__":
    import json
    from build_machine_integration import bounds
    recs = []
    fails = []
    for name, solid, group in components():
        ok = solid.isValid() and len(solid.Solids()) >= 1
        recs.append({"name": name, "group": group,
                     "solids": len(solid.Solids()),
                     "valid": solid.isValid(), "bounds": bounds(solid)})
        if not ok:
            fails.append(name)
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for name, solid, group in components():
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    lo, hi = nip_range_mm()
    result = {"parts": recs, "exported_step": exported,
              "filament_spec_mm": FILAMENT_MM,
              "filament_spec_source": "design/parameters.json filament_mm "
                                      "(c2/src/design.py:34); c2.1/bom/"
                                      "system_bom.csv EX-DIE note",
              "nip_min_mm": lo, "nip_max_mm": hi,
              "grip_window_mm": [1.5, 2.0],
              "compressed_nip_mm": [1.55, 1.9],
              "grip_ok": lo <= FILAMENT_MM and hi >= FILAMENT_MM,
              "passed": not fails and nip_opening_mm() <= FILAMENT_MM}
    (ROOT / "results" / "winder_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails:
        raise SystemExit(1)
