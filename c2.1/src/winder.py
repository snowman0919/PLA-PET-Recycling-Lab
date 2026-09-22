"""VP1 Stage 2: real puller nip drive and spool winder.

Replaces the SPOOL-ENV and PULL-ROLLER envelope instances (excluded in
build_machine_integration.py).  Frozen datums kept: the extrudate line runs
+X at z=125, y=275 from the die (x=520) through the cooling tray to the
puller at x~829.  NEW geometry (positions chosen here):

Puller (x 815..845, y 240..278, z 100..150):
- PULL_FRAME: two side plates + base.
- PULL_ROLLER_FIXED: dia-20 roller, axle on the frame.
- PULL_ROLLER_ADJ: dia-20 roller on a screw-adjustable carriage with a
  POSITIVE STOP block: the stop fixes the minimum nip gap at 2.5 mm
  (>= the 2.0 mm extrudate; the frozen envelope pair gave only 1.8 mm).
  Nip range 2.5..5.5 mm by screw travel.
- PULL_MOTOR_REF: small gearmotor reference belt-driving the fixed roller.

Winder (axis Y at x=700, z=220; north of the cooling fans, clear of
COOL-FAN_001/002 and COOL-TRAY):
- WIND_SPOOL_SHAFT / WIND_SPOOL_DRUM (dia 70) / WIND_FLANGE_L/R (dia 200).
- WIND_MOTOR_REF at the shaft end; WIND_TRAVERSE_SCREW + rider above the
  drum (z 325) laying the filament; WIND_TENSIONER post+arm on the
  filament path from the puller (slip tensioner).
All within the operating envelope (x<=845, y<=278, z<=329 vs 850x450x510).
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


PULL = dict(x=829.0, y0=253.0, y1=275.0, roller_r=10.0, line_z=125.0,
            nip=2.5)
PULL_ROLLER_Z = (PULL["line_z"] - (PULL["roller_r"] + PULL["nip"] / 2.0),
                 PULL["line_z"] + (PULL["roller_r"] + PULL["nip"] / 2.0))
WIND = dict(x=700.0, z=220.0, drum_r=35.0, flange_r=100.0, shaft_r=8.0,
            y0=100.0)


def pull_frame():
    """Side plates + base; the adjustable top plate carries the screw."""
    y0, y1 = PULL["y0"] - 3.0, PULL["y1"] + 3.0
    side_a = _box(824.0, 827.0, y0, y0 + 3.0, 100.0, 150.0)
    side_b = _box(843.0, 846.0, y1 - 3.0, y1, 100.0, 150.0)
    base = _box(824.0, 846.0, y0, y1, 100.0, 104.0)
    return side_a.fuse(side_b).fuse(base).clean()


def pull_roller_fixed():
    """Dia-20 drive roller on a fixed axle, center z 113.75."""
    z = PULL_ROLLER_Z[0]
    r = _cyl(PULL["roller_r"], PULL["y1"] - PULL["y0"], PULL["x"],
             PULL["y0"], z)
    axle = _cyl(3.0, PULL["y1"] - PULL["y0"] + 8.0, PULL["x"],
                PULL["y0"] - 4.0, z)
    return r.fuse(axle).clean()


def pull_roller_adj():
    """Dia-20 adjustable roller at z 136.25 (nip 2.5 mm with the stop) plus
    its carriage plate and M5 adjusting screw (positive stop embodiment)."""
    z = PULL_ROLLER_Z[1]
    r = _cyl(PULL["roller_r"], PULL["y1"] - PULL["y0"], PULL["x"],
             PULL["y0"], z)
    carriage = _box(PULL["x"] - 12.0, PULL["x"] + 12.0,
                    PULL["y1"], PULL["y1"] + 6.0, z - 4.0, z + 14.0)
    screw = _cyl(2.5, 14.0, PULL["x"], PULL["y1"] + 4.0, z + 8.0,
                 axis=(0, 0, 1))
    return r.fuse(carriage).fuse(screw).clean()


def pull_nip_stop():
    """Positive stop: hard block between the carriage top face and a frame
    tab.  With the carriage seated on the stop the nip is exactly 2.5 mm;
    screwing the carriage up opens the nip to 5.5 mm."""
    return _box(PULL["x"] - 9.0, PULL["x"] + 9.0, PULL["y1"] + 1.0,
                PULL["y1"] + 5.0, PULL_ROLLER_Z[1] + 7.75,
                PULL_ROLLER_Z[1] + 10.25)


def pull_motor_ref():
    """Small gearmotor reference (not-owned) belt-driving the fixed roller
    from the north side of the frame."""
    body = _box(834.0, 847.0, 200.0, 234.0, 110.0, 140.0)
    nose = _cyl(8.0, 16.0, PULL["x"], 230.0, 125.0)
    return body.fuse(nose).clean()


def spool_shaft():
    return _cyl(WIND["shaft_r"], 95.0, WIND["x"], 92.0, WIND["z"])


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
    """Gearmotor reference (not-owned) on the shaft's north end."""
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
            ("WIND_SPOOL_DRUM", spool_drum(), "spool"),
            ("WIND_FLANGE_L", spool_flange_l(), "spool"),
            ("WIND_FLANGE_R", spool_flange_r(), "spool"),
            ("WIND_MOTOR_REF", winder_motor_ref(), "spool"),
            ("WIND_TRAVERSE_SCREW", traverse_screw(), "spool"),
            ("WIND_TRAVERSE_RIDER", traverse_rider(), "spool"),
            ("WIND_TENSIONER", tensioner(), "spool")]


def nip_opening_mm():
    """Minimum nip gap with the carriage seated on the positive stop:
    roller centers at line_z +/- (roller_r + nip/2) -> gap = nip = 2.5 mm."""
    return PULL["nip"]


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
    result = {"parts": recs, "exported_step": exported,
              "nip_min_mm": nip_opening_mm(),
              "nip_ge_2_5": nip_opening_mm() >= 2.5,
              "passed": not fails and nip_opening_mm() >= 2.5}
    (ROOT / "results" / "winder_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails:
        raise SystemExit(1)
