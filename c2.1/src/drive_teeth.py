"""VP1 Stage 1: real tooth geometry for the C1 common-drive layout.

Replaces the toothless DRV-SH15/SH40 gear discs and DRV-SP24/SP12 sprocket
discs with real toothed solids under the SAME part ids and instance names as
design/assembly.json, so the C1 master instance contract stays untouched.

Basis (recomputed from design/parameters.json + design/assembly.json):
- Helical gears: drive block (normal_module=2, helix_deg=15, 15T/40T,
  half_face=25, half_hub=10, central_gap=2). Pressure angle 20 deg (KHK SH2
  stock assumption; parameters.json does not state alpha). Existing stand-in
  OD/2 17.529142706151248 (15T) / 43.41104721640332 (40T) are exactly the
  helical tip radii rp=mn*z/(2cos15deg)+mn, and the instance center distance
  |136.94018992255457-80| = 56.94018992255457 equals rp15+rp40, so the meshing
  center distance is preserved by construction.
- Sprockets: ANSI35 roller chain, pitch p=9.525, roller dia 5.08. Existing
  stand-in cylinders are the ANSI max-OD envelopes r=p/2*(0.6+cot(pi/z))
  (39.032 for 24T, 20.631 for 12T); the existing r2.54 pitch-circle holes mark
  roller seats at the pitch radius, so gap centers keep those same angles and
  the shaft/key datum is unchanged.
- Chain loop solids DRV-CHAIN-A / DRV-CHAIN-B (new parts): tangent-line +
  pitch-arc envelope of a #35 chain, radial +/-5.5 mm, 5 mm wide.
- Chain A vs S1-ROOF-R_001 collides in the frozen C1 layout; this module only
  reports it (build_machine_integration known_contacts), it moves no legacy
  part.

Angles are computed in part-local XZ (the frame the assembly.json instance
transforms act on). Positive local angle maps +X toward +Z.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]

V = cq.Vector

from drive_kinematics import (BACKLASH_MM, CHAIN_A, CHAIN_AXIAL,
                              CHAIN_B, CHAIN_PITCH, CHAIN_RADIAL_ENV,
                              HELIX_DEG, MODULE_N, PRESSURE_DEG, ROLLER_R,
                              chain_length_mm, gear_center_distance,
                              gear_pitch_radius, ratio_chain,
                              sprocket_pitch_radius, _tangent_data)

GEAR_PARTS = ("DRV-SH15R", "DRV-SH15L", "DRV-SH40R", "DRV-SH40L")
SPROCKET_PARTS = ("DRV-SP24-B20", "DRV-SP24-B25", "DRV-SP24-B12", "DRV-SP12-B12")
SPROCKET_TEETH = {"DRV-SP24-B20": 24, "DRV-SP24-B25": 24,
                  "DRV-SP24-B12": 24, "DRV-SP12-B12": 12}
SPROCKET_OD = {"DRV-SP24-B20": 39.032278961853535, "DRV-SP24-B25": 39.032278961853535,
               "DRV-SP24-B12": 39.032278961853535, "DRV-SP12-B12": 20.631391971046778}
SPROCKET_BORE = {"DRV-SP24-B20": 10.0, "DRV-SP24-B25": 12.5,
                 "DRV-SP24-B12": 6.0, "DRV-SP12-B12": 6.0}
SPROCKET_FACE = {"DRV-SP24-B20": 8.0, "DRV-SP24-B25": 8.0,
                 "DRV-SP24-B12": 8.0, "DRV-SP12-B12": 8.0}
HUB_R = {"DRV-SH15R": 12.0, "DRV-SH15L": 12.0, "DRV-SH40R": 30.0, "DRV-SH40L": 30.0,
         "DRV-SP24-B20": 20.0, "DRV-SP24-B25": 20.0, "DRV-SP24-B12": 20.0,
         "DRV-SP12-B12": 12.880620893564727}

# Gear parts: teeth, hand sign, phase (profile-space deg), bore, keyway
# (w, d, z0), matching the cuts of the original parts verbatim.
GEAR_SPECS = {
    "DRV-SH15R": dict(z=15, hand=+1, phase_deg=0.0, bore_r=6.0,
                      keyway=(4.0, 2.5, 5.8)),
    "DRV-SH15L": dict(z=15, hand=+1, phase_deg=0.0, bore_r=6.0,
                      keyway=(4.0, 2.5, 5.8)),
    "DRV-SH40R": dict(z=40, hand=-1, phase_deg=175.5, bore_r=10.0,
                      keyway=(6.0, 3.0, 9.8)),
    "DRV-SH40L": dict(z=40, hand=-1, phase_deg=175.5, bore_r=10.0,
                      keyway=(6.0, 3.0, -12.8)),
}

# Instance -> part id (assembly.json names; 8 replaced instances)
INSTANCE_PART = {
    "DRV-SH15R_001": "DRV-SH15R", "DRV-SH15L_001": "DRV-SH15L",
    "DRV_SH40L_lower": "DRV-SH40L", "DRV_SH40R_upper": "DRV-SH40R",
    "DRV-SP24-B20_001": "DRV-SP24-B20", "DRV-SP24-B25_001": "DRV-SP24-B25",
    "DRV-SP24-B12_001": "DRV-SP24-B12", "DRV-SP12-B12_001": "DRV-SP12-B12",
}

REPLACED_PART_IDS = set(INSTANCE_PART.values())


def _inv(a):
    return math.tan(a) - a


def _gear_flank_pts(z, n=7):
    """Right-flank involute points (r, angle-from-tooth-center) in profile XY.

    Standard zero-shift involute: angle(r) = pi/(2z) + inv(at) - inv(a_r),
    a_r = acos(rb/r), rb = rp*cos(at). Angle shrinks toward the tip.
    """
    rp = gear_pitch_radius(z)
    at = math.atan(math.tan(math.radians(PRESSURE_DEG)) / math.cos(math.radians(HELIX_DEG)))
    rb = rp * math.cos(at)
    ra = rp + MODULE_N
    rf = rp - 1.25 * MODULE_N
    r_start = max(rb, rf)
    # thin each tooth by j/2 per flank: half-thickness angle at pitch drops
    # by (j/2)/rp so the pair assembles with tangential backlash j
    back = (BACKLASH_MM / 2.0) / rp
    pts = []
    for i in range(n):
        r = r_start + (ra - r_start) * i / (n - 1)
        a_r = math.acos(min(1.0, rb / r))
        ang = math.pi / (2.0 * z) - back + _inv(at) - _inv(a_r)
        pts.append((r, ang))
    return pts, rb, ra, rf, r_start


def _gear_profile_xy(z, phase_deg=0.0, flank_n=7):
    """Closed tooth profile polygon in profile-XY, tooth center at local 0deg.

    Mirrored instance (180deg about X) maps profile angle a to -a, so one
    profile serves both the identity and flipped instances of a mesh pair:
    tooth-center phases chosen at 0deg (pinions) / space at 180deg (gears).
    """
    flank, rb, ra, rf, r_start = _gear_flank_pts(z, flank_n)
    p = 2.0 * math.pi / z
    ang_start = flank[0][1]              # flank angle at r_start
    ang_tip = flank[-1][1]
    pts = []
    for k in range(z):
        c = k * p + math.radians(phase_deg)
        # left flank root->tip (angles increasing: c-ang_start -> c-ang_tip)
        for r, ang in flank:
            pts.append((r * math.cos(c - ang), r * math.sin(c - ang)))
        # tip arc: left tip -> right tip through the tooth center (CCW)
        for i in range(1, 4):
            a = c - ang_tip + (2.0 * ang_tip) * i / 4.0
            pts.append((ra * math.cos(a), ra * math.sin(a)))
        # right flank tip->root (angles increasing: c+ang_tip -> c+ang_start)
        for r, ang in reversed(flank):
            pts.append((r * math.cos(c + ang), r * math.sin(c + ang)))
        # root: taper from the involute start down to the root circle so the
        # tooth narrows below the base circle (radial drop would self-cross:
        # ang_start > pitch/2 for z=15), then the root arc between teeth
        ang_f = ang_start * rf / r_start if r_start > rf else ang_start
        next_start = (k + 1) * p + math.radians(phase_deg) - ang_f
        for i in range(1, 4):
            a = (c + ang_f) + (next_start - (c + ang_f)) * i / 4.0
            pts.append((rf * math.cos(a), rf * math.sin(a)))
    return pts


def _twist_deg(z, face):
    """Total twist over the face width for a helix of HELIX_DEG at pitch r."""
    return math.degrees(face * math.tan(math.radians(HELIX_DEG)) / gear_pitch_radius(z))


def _gear_local_solid(part_id):
    """Part-local gear solid: toothed blank y 0..25 + hub y 25..35 + original
    bore/keyway cuts (dims from the original part, hand per mesh pairing)."""
    s = GEAR_SPECS[part_id]
    pts = _gear_profile_xy(s["z"], s["phase_deg"])
    blank = (cq.Workplane("XY").polyline(pts).close()
             .twistExtrude(25.0, s["hand"] * _twist_deg(s["z"], 25.0)).val())
    blank = blank.rotate(V(1, 0, 0), V(0, 0, 0), 90)  # profile +Z -> part +Y
    hub = cq.Solid.makeCylinder(HUB_R[part_id], 11.0, V(0, 24, 0), V(0, 1, 0))
    solid = blank.fuse(hub)
    solid = solid.cut(cq.Solid.makeCylinder(s["bore_r"], 37.0, V(0, -1, 0), V(0, 1, 0)))
    w, d, z0 = s["keyway"]
    solid = solid.cut(cq.Solid.makeBox(w, 37.0, d, V(-w / 2.0, -1, z0)))
    return solid.clean()


def _sprocket_profile_xz(z, r_od, n_root=5, n_flank=4, n_tip=3):
    """Closed sprocket profile in XZ (part-local, axis +Y).

    Gap centers at local angles k*360/z (matching the roller-seat holes of the
    original stand-ins); seated gaps of radius ROLLER_R+0.3 at r_root, straight
    flanks to the ANSI max-OD tip circle (r_od kept from the original part).
    """
    r_p = sprocket_pitch_radius(z)
    r_root = r_p - ROLLER_R
    half_gap = math.asin((ROLLER_R + 0.3) / r_p)
    half_tip = half_gap / 2.0
    p = 2.0 * math.pi / z
    pts = []
    for k in range(z):
        g = k * p  # gap center
        for i in range(n_root):  # gap arc through the gap center (CCW)
            a = g - half_gap + 2.0 * half_gap * i / (n_root - 1)
            pts.append((r_root * math.cos(a), r_root * math.sin(a)))
        # flank: gap edge -> tip edge (linear in (angle, radius))
        a0, r0 = g + half_gap, r_root
        a1, r1 = g + p / 2.0 - half_tip, r_od
        for i in range(1, n_flank):
            t = i / n_flank
            pts.append(((r0 + (r1 - r0) * t) * math.cos(a0 + (a1 - a0) * t),
                        (r0 + (r1 - r0) * t) * math.sin(a0 + (a1 - a0) * t)))
        # tip arc between the two flank tops
        for i in range(1, 2 * n_tip):
            a = a1 + (g + p - half_tip - a1) * i / (2 * n_tip)
            pts.append((r_od * math.cos(a), r_od * math.sin(a)))
    return pts


def _sprocket_local_solid(part_id):
    s = SPROCKET_TEETH[part_id]
    pts = _sprocket_profile_xz(s, SPROCKET_OD[part_id])
    wire = cq.Wire.makePolygon([V(x, 0.0, z) for x, z in pts], close=True)
    blank = cq.Solid.extrudeLinear(wire, [], V(0, SPROCKET_FACE[part_id], 0))
    face_h = SPROCKET_FACE[part_id]
    hub = cq.Solid.makeCylinder(HUB_R[part_id], 11.0, V(0, face_h - 1.0, 0), V(0, 1, 0))
    solid = blank.fuse(hub)
    solid = solid.cut(cq.Solid.makeCylinder(SPROCKET_BORE[part_id], 20.0,
                                            V(0, -1, 0), V(0, 1, 0)))
    return solid.clean()


def _rect_prism(t1, t2, normal, y0):
    """Straight chain run: 11 mm radial x 5 mm axial prism from t1 to t2."""
    n = cq.Vector(normal[0], 0.0, normal[1])
    u = cq.Vector(0, 1, 0)
    corners = []
    for sr in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            base = cq.Vector(t1[0], 0.0, t1[1]) + n * (CHAIN_RADIAL_ENV * sr) \
                + u * (y0 + CHAIN_AXIAL / 2.0 * (1.0 + sy))
            corners.append(base)
    wire = cq.Wire.makePolygon([corners[0], corners[1], corners[3], corners[2]],
                               close=True)
    face = cq.Face.makeFromWires(wire)
    direction = cq.Vector(t2[0] - t1[0], 0.0, t2[1] - t1[1])
    return cq.Solid.extrudeLinear(face.outerWire(), [], direction)


def _sector_prism(center, r_in, r_out, a0, a1, y0, n=48):
    """Wrap tube: extrusion of an annular sector (XZ) along +Y."""
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((center[0] + r_out * math.cos(a), center[1] + r_out * math.sin(a)))
    for i in range(n, -1, -1):
        a = a0 + (a1 - a0) * i / n
        pts.append((center[0] + r_in * math.cos(a), center[1] + r_in * math.sin(a)))
    wire = cq.Wire.makePolygon([V(x, y0, z) for x, z in pts], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, CHAIN_AXIAL, 0))



def _chain_loop(chain):
    """Closed #35 chain envelope around two sprockets (single fused solid)."""
    p1, p2 = chain["p1"], chain["p2"]
    r1 = sprocket_pitch_radius(chain["z1"])
    r2 = sprocket_pitch_radius(chain["z2"])
    lines, phi, dist = _tangent_data(p1, r1, p2, r2)
    (t1a_x, t1a_z, t2a_x, t2a_z) = lines[0]
    (t1b_x, t1b_z, t2b_x, t2b_z) = lines[1]
    y0 = chain["y0"]

    def run(x1, z1, x2, z2):
        L = math.hypot(x2 - x1, z2 - z1)
        ux, uz = (x2 - x1) / L, (z2 - z1) / L
        e = 3.0  # overshoot past each tangent point so sectors fuse solidly
        return _rect_prism((x1 - ux * e, z1 - uz * e), (x2 + ux * e, z2 + uz * e),
                           (-uz, ux), y0)

    parts = [run(t1a_x, t1a_z, t2a_x, t2a_z),
             run(t1b_x, t1b_z, t2b_x, t2b_z)]
    # absolute angles of the two normals (differ by exactly 2*phi)
    ang1 = math.atan2((t1a_z - p1[1]) / r1, (t1a_x - p1[0]) / r1)
    ang2 = ang1 - 2.0 * phi
    if ang2 > ang1:
        ang2 -= 2.0 * math.pi
    # wrap at p2: short sector (span 2*phi) from ang2 to ang1; extended 1.5deg
    # past each tangent so the prisms fuse volumetrically
    ext = math.radians(1.5)
    parts.append(_sector_prism(p2, r2 - CHAIN_RADIAL_ENV, r2 + CHAIN_RADIAL_ENV,
                               ang2 - ext, ang1 + ext, y0))
    # wrap at p1: long sector (span 2*pi - 2*phi) from ang1 to ang2 + 2*pi
    parts.append(_sector_prism(p1, r1 - CHAIN_RADIAL_ENV, r1 + CHAIN_RADIAL_ENV,
                               ang1 - ext, ang2 + 2.0 * math.pi + ext, y0))
    solid = parts[0]
    for s in parts[1:]:
        solid = solid.fuse(s)
    return solid.clean()


def chain_components():
    """New-part chain solids in absolute machine coordinates."""
    return [("DRV-CHAIN-A", _chain_loop(CHAIN_A)),
            ("DRV-CHAIN-B", _chain_loop(CHAIN_B))]


def replacement_local_solid(instance_name):
    """Part-local replacement solid for a replaced legacy instance."""
    part_id = INSTANCE_PART[instance_name]
    if part_id in GEAR_PARTS:
        return _gear_local_solid(part_id)
    return _sprocket_local_solid(part_id)


def count_teeth(shape, sample_radius, center=(0.0, 0.0), y=12.5, samples=2880):
    """Count material runs on a circle inside the solid (teeth == gaps+1)."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON
    cls = BRepClass3d_SolidClassifier(shape.wrapped)
    inside = []
    for i in range(samples):
        a = 2.0 * math.pi * i / samples
        p = gp_Pnt(center[0] + sample_radius * math.cos(a), y,
                   center[1] + sample_radius * math.sin(a))
        cls.Perform(p, 1e-6)
        inside.append(cls.State() in (TopAbs_IN, TopAbs_ON))
    runs = 0
    for i in range(samples):
        if inside[i] and not inside[i - 1]:
            runs += 1
    return runs


def _mesh_check(samples=4):
    """Rotate the 15T/40T pair through part of a tooth pitch at the frozen
    instance axes; BRep intersection must stay ~zero (conjugate contact)."""
    pin = replacement_local_solid("DRV-SH15L_001")
    gear = replacement_local_solid("DRV_SH40R_upper")
    pin = pin.translate((80.0, 313.0, 65.0))
    gear = gear.translate((136.94018992255457, 313.0, 65.0))
    records = []
    for k in range(samples):
        deg = 24.0 * k / samples / 3.0  # third-tooth-pitch steps (15T: 24deg)
        p = pin.rotate((80.0, 0.0, 65.0), (80.0, 1.0, 65.0), deg)
        g = gear.rotate((136.94, 0.0, 65.0), (136.94, 1.0, 65.0), -deg * 15.0 / 40.0)
        v = p.intersect(g).Volume()
        records.append({"pinion_deg": deg, "overlap_mm3": v})
    return records


def main():
    import json
    result = {"revision": "VP1-STAGE1", "module": "c2.1/src/drive_teeth.py"}
    result["center_distance_mm"] = {
        "computed": gear_center_distance(15, 40),
        "instance_datum": 136.94018992255457 - 80.0,
    }
    result["sprocket_pitch_radii"] = {str(z): sprocket_pitch_radius(z) for z in (12, 24)}
    result["chain_lengths"] = {
        "A": {"computed": chain_length_mm(CHAIN_A), "links": CHAIN_A["links"],
              "nominal": CHAIN_A["links"] * CHAIN_PITCH},
        "B": {"computed": chain_length_mm(CHAIN_B), "links": CHAIN_B["links"],
              "nominal": CHAIN_B["links"] * CHAIN_PITCH},
    }
    result["ratio_chain"] = ratio_chain()
    result["mesh_samples"] = _mesh_check()
    parts = {}
    for inst in INSTANCE_PART:
        s = replacement_local_solid(inst)
        part = INSTANCE_PART[inst]
        z = (GEAR_SPECS[part]["z"] if part in GEAR_PARTS
             else SPROCKET_TEETH[part])
        y = 12.5 if part in GEAR_PARTS else 4.0
        r = (gear_pitch_radius(z) if part in GEAR_PARTS
             else sprocket_pitch_radius(z))
        parts[inst] = {"solids": len(s.Solids()), "valid": s.isValid(),
                       "teeth_counted": count_teeth(s, r, y=y),
                       "teeth_expected": z}
    result["replacements"] = parts
    chains = {}
    for name, solid in chain_components():
        chains[name] = {"solids": len(solid.Solids()), "valid": solid.isValid()}
    result["chains"] = chains
    ok = (abs(result["center_distance_mm"]["computed"]
              - result["center_distance_mm"]["instance_datum"]) < 1e-6
          and all(v["teeth_counted"] == v["teeth_expected"] and v["valid"]
                  and v["solids"] == 1 for v in parts.values())
          and all(v["solids"] == 1 and v["valid"] for v in chains.values())
          and all(s["overlap_mm3"] < 0.05 for s in result["mesh_samples"]))
    result["passed"] = ok
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for inst in INSTANCE_PART:
        s = replacement_local_solid(inst)
        path = out_dir / (INSTANCE_PART[inst] + ".step")
        cq.exporters.export(cq.Compound.makeCompound([s]), str(path))
        exported.append(str(path.relative_to(REPO)))
    for name, solid in chain_components():
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    result["exported_step"] = exported
    (ROOT / "results" / "drive_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
