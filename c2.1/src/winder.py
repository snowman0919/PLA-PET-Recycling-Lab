"""VP1 Stage 4: real puller nip drive and spool winder (grip redesign).

Replaces the SPOOL-ENV and PULL-ROLLER envelope instances (excluded in
build_machine_integration.py).  Frozen datums kept: the extrudate line runs
+X at z=125, y=275 from the die (x=520) through the cooling tray to the
puller at x~829.  NEW geometry (positions chosen here):

The old 2.5 mm fixed nip could not engage a 1.75 mm strand. A later
"adjustable roller" BRep fused roller, carriage, springs and lateral posts
into one rigid solid; it could not both spin and translate. This candidate
separates those kinematic roles without assigning unselected spring force.

Puller (x 819..847, y 202..303, z 100..153.5):
- PULL_FRAME: two side plates and base, with Ø8 driven-axle seats and
  vertical clearance slots for the idler axle; fixed guide rods and caps.
- PULL_ROLLER_FIXED: dia-20 driven roller, axle in frame bearings BOTH ends.
- PULL_ROLLER_ADJ: dia-20 freely rotating idler and Ø6 axle. Separate
  PULL_IDLER_CARRIAGE has two end bearing seats sliding 1.5 mm vertically
  on fixed Ø5 guides; separate PULL_IDLER_SPRINGS are axial space envelopes
  between the carrier and frame caps. PULL_NIP_STOP defines lower/upper
  positive travel limits (1.5..3.0 mm roller gap). Bearings, spring rate,
  preload, axle retention and traction remain unselected/unrated.
  The reference position is the 1.5 mm minimum opening; a 1.75 mm strand
  displaces the carrier, so contact force cannot be inferred from this pose.
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
- WIND_CLUTCH_REF: shaft key -> keyed collar -> unselected spring envelope ->
  friction pad against the left flange. Two groove-backed external-ring
  envelopes and a loose-flange thrust washer limit axial escape, but catalog
  ring clearance prevents a claim of spring preload. Groove/ring ratings,
  torque and wear remain unqualified; 70 Nmm is only a model sensitivity.
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


# FILAMENT SPEC: 1.75 mm nominal (design/parameters.json "filament_mm").
# Nip 1.5..3.0 mm is a travel envelope, not an achieved grip force or
# a qualified stock/diameter range.
FILAMENT_MM = 1.75
# Nip geometry: fixed drive roller below the line; idler rises by up to
# 1.5 mm between the minimum stop and the fully open stop. Spring force and
# filament contact deformation are unqualified, not assigned by the CAD.
PULL = dict(x=829.0, y0=264.0, y1=286.0, roller_r=10.0, line_z=125.0,
            nip_stop_min=1.5, nip_open_max=3.0)
PULL_ROLLER_Z = (PULL["line_z"] - (PULL["roller_r"] + PULL["nip_stop_min"] / 2.0),
                 PULL["line_z"] + (PULL["roller_r"] + PULL["nip_stop_min"] / 2.0))
WIND = dict(x=700.0, z=220.0, drum_r=35.0, flange_r=100.0, shaft_r=8.0,
            y0=100.0)

# Dimensional candidates, not procurement or rated spring/ring selections.
# ES-16: https://www.smalley.com/ring/es-16 (2-turn external Spirolox).
# SSB-0087: https://www.smalley.com/wave-spring/ssb-0087
ES16 = dict(groove_r_mm=15.02 / 2, groove_w_mm=1.00,
            ring_thick_mm=0.89, radial_wall_mm=1.40)
SSB0087_WORK_HEIGHT_MM = 1.57
CLUTCH_SPRING_SEAT_MM = 1.0


def pull_frame():
    """Two metal side plates carry the driven axle and a slotted idler axle.

    The Ø5 vertical guide rods are fixed between the frame cap and a
    separate positive stop. Sliding carrier bores, not the idler roller,
    constrain the translation. Plate slots clear the full 1.5 mm stroke.
    Bearing inserts, side-plate joints and guide alignment remain HOLD.
    """
    y0, y1 = 259.0, 287.0
    base = _box(824, 846, y0, y1 + 4, 100, 104)
    frame = base
    for y in (y0, y1):
        plate = _box(824, 836, y, y + 4, 100, 150)
        plate = plate.cut(_cyl(4.2, 4, PULL["x"], y, PULL_ROLLER_Z[0]))
        plate = plate.cut(_box(825.8, 832.2, y, y + 4, 132.5, 140.5))
        frame = frame.fuse(plate)
    for y, cap_y in ((253.5, 249.0), (296.5, 287.0)):
        frame = frame.fuse(_box(823, 846, cap_y,
                                cap_y + 15, 149.5, 153.5))
        frame = frame.fuse(_cyl(2.5, 18.5, 839, y, 131,
                                axis=(0, 0, 1)))
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
    """Ø20 driven roller and Ø8 axle supported at both frame side plates."""
    z = PULL_ROLLER_Z[0]
    roller = _cyl(PULL["roller_r"], PULL["y1"] - PULL["y0"],
                  PULL["x"], PULL["y0"], z)
    axle = _cyl(4.0, 38.0, PULL["x"], 256.0, z)
    return roller.fuse(axle).clean()


def _idler_z(opening_mm):
    lo, hi = nip_range_mm()
    if not lo <= opening_mm <= hi:
        raise ValueError("idler opening must stay between both positive stops")
    return PULL_ROLLER_Z[1] + opening_mm - lo


def pull_roller_adj(opening_mm=1.5):
    """Freely rotating Ø20 idler on a Ø6 axle, separate from its carrier."""
    z = _idler_z(opening_mm)
    roller = _cyl(PULL["roller_r"], 22, PULL["x"], PULL["y0"], z)
    axle = _cyl(3.0, 52, PULL["x"], 249, z)
    return roller.fuse(axle).clean()


def pull_idler_carriage(opening_mm=1.5):
    """Two translating axle seats joined behind the roller, on Ø5 guides.

    Nominal Ø6.04 axle bores are bearing-envelope dimensions only;
    inserts, running clearance, tolerance and end retention remain HOLD.
    """
    z = _idler_z(opening_mm)
    carrier = _box(823, 846, 249, 259, z - 4.75, z + 5.25)
    carrier = carrier.fuse(_box(823, 846, 291, 301, z - 4.75, z + 5.25))
    carrier = carrier.fuse(_box(842, 846, 259, 291, z - 4.75, z + 5.25))
    for y in (249, 291):
        carrier = carrier.cut(_cyl(3.02, 10, PULL["x"], y, z))
    for y in (253.5, 296.5):
        carrier = carrier.cut(_cyl(2.6, 12, 839, y, z - 5,
                                    axis=(0, 0, 1)))
    return carrier.clean()


def pull_idler_springs(opening_mm=1.5):
    """Two *unselected* axial spring space envelopes, not rated springs.

    At full opening the available installed height falls from 8.5 to 7 mm;
    neither a free length nor a spring force follows from this envelope.
    """
    seat_z = _idler_z(opening_mm) + 5.25
    springs = []
    for y in (253.5, 296.5):
        height = 149.5 - seat_z
        spring = _cyl(4.5, height, 839, y, seat_z, axis=(0, 0, 1))
        springs.append(spring.cut(
            _cyl(2.6, height, 839, y, seat_z, axis=(0, 0, 1))))
    return cq.Compound.makeCompound(springs)


def pull_nip_stop():
    """Separate metal lower and upper seats at the 1.5/3.0 mm nip limits."""
    stops = []
    for y in (249, 291):
        stops.append(_box(823, 841, y, y + 10, 127, 131))
        stops.append(_box(823, 834, y, y + 10, 142.5, 146))
    return cq.Compound.makeCompound(stops)


def pull_motor_ref():
    """Unselected motor envelope driving the fixed roller by a belt.

    Its Ø16 nose ends at y248, leaving only 1 mm nominal axial clearance
    to the movable idler axle/carrier. Selected motor and tolerances HOLD.
    """
    body = _box(834.0, 847.0, 202.0, 236.0, 112.0, 142.0)
    nose = _cyl(8.0, 16.0, PULL["x"], 232.0, 127.0)
    return body.fuse(nose).clean()


def spool_shaft():
    """Driven shaft with ES-16 dimensional-candidate retaining-ring grooves.

    Ø15.02 root / 1.00 mm nominal grooves at y96..97 and y168..169;
    supplier groove tolerances, shaft fatigue and bearing thrust HOLD.
    """
    shaft = _cyl(WIND["shaft_r"], 98.0, WIND["x"], 87.0, WIND["z"])
    for y in (96.0, 168.0):
        groove = _cyl(8.1, ES16["groove_w_mm"], WIND["x"], y, WIND["z"]).cut(
            _cyl(ES16["groove_r_mm"], ES16["groove_w_mm"],
                 WIND["x"], y, WIND["z"]))
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

    3 mm keyed collar, 1 mm *unselected* spring envelope, 2 mm pad.
    The SSB-0087 catalog spring clears Ø16, but its published work height
    is 1.57 mm. Whether it can safely compress to this 1 mm seat is unknown;
    no catalog load or torque is assigned. The keyslot clears the shaft key.
    """
    bore = _cyl(8.1, 7.0, WIND["x"], 96.5, WIND["z"])
    slot = _box(698.4, 701.6, 96.5, 100.1, 227.0, 230.0)
    collar = _cyl(15.0, 3.0, WIND["x"], 97.0, WIND["z"]).cut(bore).cut(slot)
    spring = _cyl(13.0, CLUTCH_SPRING_SEAT_MM, WIND["x"], 100.0, WIND["z"]).cut(bore)
    pad = _cyl(30.0, 2.0, WIND["x"], 101.0, WIND["z"]).cut(bore)
    return collar.fuse(spring).fuse(pad).clean()

def spool_retention():
    """ES-16 nominal annular envelopes and loose-flange thrust washer.

    Not the supplier's two-turn CAD. Rings are centered in their grooves:
    each has 0.055 mm face clearance at nominal dimensions, up to 0.24 mm
    total groove clearance per ring by catalog tolerances. The Ø16.2 washer
    bore improves overlap with the smaller ring while clearing Ø16 nominally.
    Axial clamp/preload, supplier fit/quote, washer eccentricity and bearing
    thrust still require validation.
    """
    rings = []
    for y in (96.0, 168.0):
        face_y = y + (ES16["groove_w_mm"] - ES16["ring_thick_mm"]) / 2
        outer_r = ES16["groove_r_mm"] + ES16["radial_wall_mm"]
        ring = _cyl(outer_r, ES16["ring_thick_mm"], WIND["x"], face_y,
                    WIND["z"]).cut(_cyl(ES16["groove_r_mm"],
                                      ES16["ring_thick_mm"], WIND["x"],
                                      face_y, WIND["z"]))
        # Cut is only an installation-clearance proxy, not a Spirolox spiral.
        ring = ring.cut(_box(699.0, 701.0, face_y,
                             face_y + ES16["ring_thick_mm"], 227.0, 233.0))
        rings.append(ring.clean())
    washer = _cyl(15.0, 1.0, WIND["x"], 167.0, WIND["z"]).cut(
        _cyl(8.1, 1.0, WIND["x"], 167.0, WIND["z"]))
    return rings[0], rings[1], washer.clean()


def spool_retention_parts():
    return cq.Compound.makeCompound(spool_retention())

def retention_fit_screen():
    """Catalog dimensional screen, not a ring load or clutch torque rating."""
    groove_width = ES16["groove_w_mm"]
    ring_thickness = ES16["ring_thick_mm"]
    groove_min_r = (15.02 - 0.075) / 2
    wall_min = 1.40 - 0.13
    return {
        "ring_candidate": "Smalley ES-16; two-turn detail not modeled",
        "ring_source": "https://www.smalley.com/ring/es-16",
        "groove_d_nominal_mm": 2 * ES16["groove_r_mm"],
        "groove_width_nominal_mm": groove_width,
        "ring_thickness_nominal_mm": ring_thickness,
        "axial_clearance_per_ring_mm": [
            round(groove_width - (ring_thickness + 0.05), 3),
            round((groove_width + 0.08) - (ring_thickness - 0.05), 3)],
        "max_two_ring_clearance_mm": round(
            2 * ((groove_width + 0.08) - (ring_thickness - 0.05)), 3),
        "washer_bore_nominal_mm": 16.2,
        "washer_overlap_catalog_ring_min_mm_at_nominal_bore_and_eccentricity_0_1":
            round(groove_min_r + wall_min - 8.1 - 0.1, 4),
        "spring_candidate": "SSB-0087; PUBLISHED_WORK_HEIGHT_INCOMPATIBLE",
        "spring_source": "https://www.smalley.com/wave-spring/ssb-0087",
        "spring_work_height_mm": SSB0087_WORK_HEIGHT_MM,
        "spring_seat_mm": CLUTCH_SPRING_SEAT_MM,
        "spring_height_shortfall_mm": round(
            SSB0087_WORK_HEIGHT_MM - CLUTCH_SPRING_SEAT_MM, 3),
        "status": "AXIAL_FLOAT_AND_PRELOAD_HOLD; unquoted and unrated",
    }


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
            ("PULL_IDLER_CARRIAGE", pull_idler_carriage(), "puller"),
            ("PULL_IDLER_SPRINGS", pull_idler_springs(), "puller"),
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
    """Minimum roller gap with the carrier against the lower hard stop."""
    return PULL["nip_stop_min"]


def nip_range_mm():
    """(minimum and maximum openings at the two positive stops)."""
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
              "nominal_diameter_within_travel": lo < FILAMENT_MM <= hi,
              "idler_stroke_mm": hi - lo,
              "motor_to_moving_idler_nominal_y_gap_mm": round(
                  min(by_name["PULL_ROLLER_ADJ"].BoundingBox().ymin,
                      by_name["PULL_IDLER_CARRIAGE"].BoundingBox().ymin)
                  - by_name["PULL_MOTOR_REF"].BoundingBox().ymax, 3),
              "spring_installed_height_mm": [7.0, 8.5],
              "grip_qualified": False,
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
              "retention_fit_screen": retention_fit_screen(),
              "status": "GEOMETRY_ONLY_NIP_FORCE_HOLD",
              "geometry_passed": not fails and lo < FILAMENT_MM <= hi}
    (ROOT / "results" / "winder_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if fails:
        raise SystemExit(1)
