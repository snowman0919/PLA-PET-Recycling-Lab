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
- PULL_COOL_MOUNT: welded steel tube rack fixed to the rear Al upright.
  It carries the puller frame directly, with a separate underside ledge for
  the sheet cooling tray. Bolts, tube welds and tray attachment remain HOLD.

Winder (axis Y at x=700, z=220; north of the cooling fans):
- WIND_MOUNT: a steel cantilever from the front aluminium upright's y=60
  face to both bearing seats and the motor bed; two clearance holes mark
  an M5 candidate interface. Profile slot, fasteners, joint strength and
  vibration/guard qualification remain HOLD.
- WIND_SPOOL_SHAFT supported in bearings BOTH ends; WIND_SPOOL_DRUM is
  a hollow steel tube with two internal end webs, loose on the shaft and
  joined to the flanges (weld/joint rating HOLD).
- WIND_CLUTCH_REF: shaft key -> keyed collar -> wave-spring envelope ->
  friction pad against the left flange. Two groove-backed external rings
  and a loose-flange thrust washer close the axial reaction path geometrically.
  Spring preload, groove/ring ratings, torque and wear remain unqualified;
  70 Nmm in the model is only a sensitivity.
- WIND_MOTOR_REF drives the shaft; winding is through the friction clutch,
  not through a fictitious rigid bond from the loose drum bore to the shaft.
- WIND_TRAVERSE_SCREW + rider eyelet lays the filament.
- WIND_TENSIONER adds a path buffer; spring and torque setting remain HOLD.
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
PULL = dict(x=829.0, y0=264.0, y1=286.0, roller_r=10.0, line_z=125.0,
            nip_stop_min=1.5, nip_open_max=3.0, spring_rate_N_mm=8.0,
            spring_free_len=18.0, spring_solid_len=12.0)
PULL_ROLLER_Z = (PULL["line_z"] - (PULL["roller_r"] + PULL["nip_stop_min"] / 2.0),
                 PULL["line_z"] + (PULL["roller_r"] + PULL["nip_stop_min"] / 2.0))
WIND = dict(x=700.0, z=220.0, drum_r=35.0, flange_r=100.0, shaft_r=8.0,
            y0=100.0)


def pull_frame():
    """Fixed-roller seats at both axle ends, braced to the base.

    The +Y bearing boss has a web to its east plate; both bores clear the
    Ø8 axle. These are interface shapes, not selected bearing hardware.
    """
    y0, y1 = PULL["y0"] - 3.0, PULL["y1"] + 3.0
    side_a = _box(824.0, 827.0, y0, y0 + 3.0, 100.0, 150.0)
    side_b = _box(843.0, 846.0, y1 - 3.0, y1, 100.0, 150.0)
    base = _box(824.0, 846.0, y0, y1, 100.0, 104.0)
    bridge = _box(829.0, 846.0, y1 - 3.0, y1, 108.0, 120.0)
    seat_a = _cyl(7.0, 3.0, PULL["x"], y0, PULL_ROLLER_Z[0])
    seat_b = _cyl(7.0, 3.0, PULL["x"], y1 - 3.0, PULL_ROLLER_Z[0])
    frame = side_a.fuse(side_b).fuse(base).fuse(bridge).fuse(seat_a).fuse(seat_b)
    for y in (y0, y1 - 3.0):
        frame = frame.cut(_cyl(4.2, 3.0, PULL["x"], y, PULL_ROLLER_Z[0]))
    for y in (268.0, 282.0):
        frame = frame.cut(_cyl(2.25, 6.0, 833, y, 99, axis=(0, 0, 1)))
    return frame.clean()


def pull_cool_mount():
    """Rear-profile rack carries the thin cooling tray and puller separately.

    Face x=630 mates FR-2040-400_002; the 20x20x2 boom and 18x16x2
    transverse tube are steel candidates. The 8 mm tray ledge touches
    its 2 mm underside, not the moving strand. Profile slots/fasteners,
    welded joints, puller countersunk bolt heads and tray joint are HOLD.
    """
    plate = _box(630, 634, 365, 395, 75, 115)
    boom = _box(634, 836, 365, 385, 80, 100)
    boom = boom.cut(_box(634, 836, 367, 383, 82, 98))
    pull_tube = _box(824, 842, 260, 385, 84, 100)
    pull_tube = pull_tube.cut(_box(826, 840, 260, 385, 86, 98))
    tray_ledge = _box(545, 820, 300, 315, 95, 103)
    tray_spur = _box(630, 650, 310, 380, 95, 103)
    rack = plate.fuse(boom).fuse(pull_tube).fuse(tray_ledge)
    rack = rack.fuse(tray_spur)
    for y in (370, 390):
        for z in (85, 105):
            rack = rack.cut(_cyl(2.75, 6, 629, y, z, axis=(1, 0, 0)))
    for y in (268, 282):
        rack = rack.cut(_cyl(2.25, 4, 833, y, 97, axis=(0, 0, 1)))
    return rack.clean()

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
    """Fixed underside seat at the minimum 1.5 mm nip.

    The seat touches the carriage bottom at z=roller_center-4 and the
    frame's +Y plate at y=y1+3; neither solid penetrates the other.
    A different cam/guide setting can lift the roller for threading.
    """
    z = PULL_ROLLER_Z[1]
    return _box(823.0, 846.0, PULL["y1"] + 3.0, PULL["y1"] + 6.0,
                z - 7.75, z - 4.0)


def pull_motor_ref():
    """Small gearmotor reference (not-owned) belt-driving the fixed roller
    from the north side of the frame (nose axis z 127, 13.25 mm from the
    roller axle: nose r8 + axle r4 = 12 < 13.25, no contact)."""
    body = _box(834.0, 847.0, 202.0, 236.0, 112.0, 142.0)
    nose = _cyl(8.0, 16.0, PULL["x"], 232.0, 127.0)
    return body.fuse(nose).clean()


def spool_shaft():
    """Supported driven shaft with a clutch key and two retaining-ring grooves.

    Candidate 1 mm grooves at y96..97 and y168..169 have root radius 7.2 mm;
    selected ring/groove tolerances, shaft fatigue and bearing thrust HOLD.
    """
    shaft = _cyl(WIND["shaft_r"], 98.0, WIND["x"], 87.0, WIND["z"])
    for y in (96.0, 168.0):
        groove = _cyl(8.1, 1.0, WIND["x"], y, WIND["z"]).cut(
            _cyl(7.2, 1.0, WIND["x"], y, WIND["z"]))
        shaft = shaft.cut(groove)
    key = _box(698.5, 701.5, 97.0, 100.0, 227.0, 229.5)
    return shaft.fuse(key).clean()

def spool_bearing_blocks():
    """Two bearing blocks supporting the spool shaft at both ends (the east
    block rides the shaft clear of the motor reference body at y >= 187)."""
    b0 = (_box(688.0, 712.0, 88.0, 96.0, 208.0, 232.0)
          .cut(_cyl(WIND["shaft_r"] + 0.5, 10.0, WIND["x"], 87.0, WIND["z"])))
    b1 = (_box(688.0, 712.0, 170.0, 178.0, 208.0, 232.0)
          .cut(_cyl(WIND["shaft_r"] + 0.5, 12.0, WIND["x"], 169.0, WIND["z"])))
    return b0.fuse(b1).clean()


def winder_mount():
    """Steel bearing/motor load path to the front 20 mm Al upright.

    The flange sweeps through y=103..167, so the two narrow bearing rails
    flank it and join outside its x=600 radial extremity. The motor bed
    stays above the adjacent cooling fan. Attachment holes are only
    candidate Ø5.5 clearances; the owned profile slot and fasteners must
    be measured/selected before fabrication.
    """
    # Face at y=60 bears on FR-2020-400_001 (x610..630, z20..420).
    foot = _box(610, 630, 60, 64, 177, 208)
    reach = _box(590, 630, 64, 88, 200, 208)
    outer_tie = _box(590, 600, 88, 178, 200, 208)
    left = _box(590, 712, 88, 96, 200, 208)
    right = _box(590, 712, 170, 178, 200, 208)
    tab = _box(680, 712, 174, 178, 196, 201)
    motor_bed = _box(680, 720, 174, 212, 196, 200)
    mount = foot.fuse(reach).fuse(outer_tie).fuse(left).fuse(right)
    mount = mount.fuse(tab).fuse(motor_bed)
    for z in (185, 200):
        mount = mount.cut(_cyl(2.75, 6, 620, 59, z))
    return mount.clean()


def spool_drum():
    """Ø70×58 steel tube, 2 mm wall, with two 3 mm internal steel webs.

    The Ø17 web bores clear the Ø16 shaft. The unselected web/tube and
    flange welds, runout and dynamic balance are not strength-qualified.
    """
    x, y, z = WIND["x"], WIND["y0"] + 6.0, WIND["z"]
    tube = _cyl(35.0, 58.0, x, y, z).cut(_cyl(33.0, 58.0, x, y, z))
    for web_y in (y + 3.0, y + 52.0):
        web = _cyl(33.0, 3.0, x, web_y, z)
        web = web.cut(_cyl(WIND["shaft_r"] + 0.5, 3.0, x, web_y, z))
        tube = tube.fuse(web)
    return tube.clean()


def _flange(y):
    # 3 mm steel, not a 6 mm solid disc. Radial cantilever screening at
    # assumed 20 N gives 43 MPa / 0.194 mm; hub bolts and balance remain HOLD.
    thickness = 3.0
    f = _cyl(WIND["flange_r"], thickness, WIND["x"], y, WIND["z"])
    bore = _cyl(WIND["shaft_r"] + 0.5, thickness + 2.0,
                WIND["x"], y - 1.0, WIND["z"])
    return f.cut(bore).clean()


def spool_flange_l():
    return _flange(WIND["y0"] + 3.0)


def spool_flange_r():
    return _flange(WIND["y0"] + 64.0)


def spool_clutch_ref():
    """Reference friction path from keyed shaft to freely riding spool.

    3 mm keyed collar, 1 mm spring envelope, 2 mm friction washer.
    Axial stops are separate; no actual spring force or torque limit established.
    The collar's radial keyslot clears the separate shaft key.
    """
    bore = _cyl(8.1, 7.0, WIND["x"], 96.5, WIND["z"])
    slot = _box(698.4, 701.6, 96.5, 100.1, 227.0, 230.0)
    collar = _cyl(15.0, 3.0, WIND["x"], 97.0, WIND["z"]).cut(bore).cut(slot)
    spring = _cyl(13.0, 1.0, WIND["x"], 100.0, WIND["z"]).cut(bore)
    pad = _cyl(30.0, 2.0, WIND["x"], 101.0, WIND["z"]).cut(bore)
    return collar.fuse(spring).fuse(pad).clean()

def spool_retention():
    """Candidate groove-backed split rings and right loose-flange thrust washer.

    Axial chain: left ring -> keyed collar -> spring/pad -> left flange ->
    welded drum/right flange -> washer -> right ring -> shaft. At nominal
    position all faces touch; a measured spring compression, a selected ring
    specification, axial clearance stack and bearing thrust path are HOLD.
    """
    rings = []
    for y in (96.0, 168.0):
        ring = _cyl(12.0, 1.0, WIND["x"], y, WIND["z"]).cut(
            _cyl(7.2, 1.0, WIND["x"], y, WIND["z"]))
        # Open split allows radial installation without sliding over the key.
        ring = ring.cut(_box(699.0, 701.0, y, y + 1.0, 227.0, 233.0))
        rings.append(ring.clean())
    washer = _cyl(15.0, 1.0, WIND["x"], 167.0, WIND["z"]).cut(
        _cyl(8.5, 1.0, WIND["x"], 167.0, WIND["z"]))
    return rings[0], rings[1], washer.clean()


def spool_retention_parts():
    return cq.Compound.makeCompound(spool_retention())


def winder_motor_ref():
    """Unselected motor envelope drives the shaft. A friction washer between
    the keyed collar and loose spool flange is the intended torque path."""
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
            ("PULL_COOL_MOUNT", pull_cool_mount(), "puller"),
            ("PULL_MOTOR_REF", pull_motor_ref(), "puller"),
            ("WIND_SPOOL_SHAFT", spool_shaft(), "spool"),
            ("WIND_SPOOL_BEARINGS", spool_bearing_blocks(), "spool"),
            ("WIND_MOUNT", winder_mount(), "spool"),
            ("WIND_SPOOL_DRUM", spool_drum(), "spool"),
            ("WIND_CLUTCH_REF", spool_clutch_ref(), "spool"),
            ("WIND_SPOOL_RETENTION", spool_retention_parts(), "spool"),
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
    solids = components()
    recs = []
    fails = []
    for name, solid, group in solids:
        ok = solid.isValid() and len(solid.Solids()) >= 1
        recs.append({"name": name, "group": group,
                     "solids": len(solid.Solids()),
                     "valid": solid.isValid(), "bounds": bounds(solid)})
        if not ok:
            fails.append(name)
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for name, solid, group in solids:
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    lo, hi = nip_range_mm()
    by_name = {name: solid for name, solid, _ in solids}
    density_g_mm3 = 0.00785  # candidate steel, not measured material grade
    old_solid_annulus = (_cyl(35, 58, WIND["x"], 106, WIND["z"])
                         .cut(_cyl(8.5, 58, WIND["x"], 106, WIND["z"])))
    rotating = ("WIND_SPOOL_DRUM", "WIND_FLANGE_L", "WIND_FLANGE_R")
    old_rotating_g = (old_solid_annulus.Volume()
                      + sum(by_name[n].Volume() for n in rotating[1:])) * density_g_mm3
    new_rotating_g = sum(by_name[n].Volume() for n in rotating) * density_g_mm3
    result = {"parts": recs, "exported_step": exported,
              "filament_spec_mm": FILAMENT_MM,
              "filament_spec_source": "design/parameters.json filament_mm "
                                      "(c2/src/design.py:34); c2.1/bom/"
                                      "system_bom.csv EX-DIE note",
              "nip_min_mm": lo, "nip_max_mm": hi,
              "grip_window_mm": [1.5, 2.0],
              "compressed_nip_mm": [1.55, 1.9],
              "grip_ok": lo <= FILAMENT_MM and hi >= FILAMENT_MM,
              "steel_mass_screen_g": {
                  "density_g_mm3": density_g_mm3,
                  "old_solid_annulus_and_flange_g": round(old_rotating_g, 2),
                  "hollow_tube_web_and_flange_g": round(new_rotating_g, 2),
                  "mount_g": round(by_name["WIND_MOUNT"].Volume()
                                   * density_g_mm3, 2),
                  "pull_cool_mount_g": round(by_name["PULL_COOL_MOUNT"].Volume()
                                             * density_g_mm3, 2),
                  "retention_ring_and_washer_g": round(
                      by_name["WIND_SPOOL_RETENTION"].Volume() * density_g_mm3, 2),
                  "cost_and_weld_rating": "HOLD: no quotes or measured joints"},
              "passed": not fails and nip_opening_mm() <= FILAMENT_MM}
    (ROOT / "results" / "winder_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails:
        raise SystemExit(1)
