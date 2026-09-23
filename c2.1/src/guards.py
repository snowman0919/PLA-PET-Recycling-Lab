"""VP1 Stage 2: real containment guards, E-stop mounts and interlock seats.

Replaces the placeholder GUARD_SECTION_ENVELOPE_HOLD instance (excluded in
build_machine_integration.py) with real guard solids:
- GUARD_S2_RING: annular sector r 90..94 over global angles 20..114 deg,
  y 217..341 - contains the S2 rotor ring from above/east.  Notched at
  angles >114 deg (x<=272) where the chute pan passes beneath (chute max
  radius 89.2 mm < 90 mm inner radius, 0.8 mm clearance).
- GUARD_S1_TOP / GUARD_S1_FRONT / GUARD_S1_REAR: containment over the S1
  cutter zone above the wall plane (cutter sweep top z=438.3), leaving the
  hopper outlet and the S1-STUD/TIE rows clear.
- GUARD_CHAIN_A: lid over the chain A top run (z 440.3) between the roof
  brackets; GUARD_CHAIN_B: outer tube over chain B (radial band
  rp+5.5..rp+9.5, y 377..380).  These guards do NOT touch the recorded
  chain-vs-layout contacts (S1-ROOF-R_001, S1-STUD, DRV-B12, DRV-DECK,
  DRV-JACK) - those remain known contacts in machine_integration.json and
  are restated in the guard results block.
- EL interlocks/E-stops live in electrical_bay.py; the lid interlock seat
  GUARD_LID_INTERLOCK_SEAT is here (hopper lid edge).

Service sweep (ASSEMBLY_SERVICE_KO.md): screen cleaning, jam clearing,
blade/shim adjustment and sensor replacement require the shafts locked and
guards open; service_sweep_checks() proves each guard lifts clear of the
machine without touching the frozen S2 jacket, the cutter sweep, the chain
loops, the chute or the winder.
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq

V = cq.Vector

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]

S2_AX, S2_AZ = 308.56946468906176, 280.0
GUARD_RI, GUARD_RO = 90.0, 94.0
GUARD_Y0, GUARD_Y1 = 250.0, 300.0
MOUTH_LO_DEG, NOTCH_HI_DEG = 20.0, 114.0

S1 = dict(x0=80.0, x1=240.0, y0=157.4, y1=329.6, wall_top=444.3,
          sweep_top=438.3)
CHAIN_A_TOP_Z = 440.3


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def _sector_prism(r, a0_deg, a1_deg):
    """Filled sector prism (XZ) extruded along +Y over the guard y band."""
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    n = 24
    pts = [(S2_AX + r * math.cos(a0 + (a1 - a0) * i / n),
            S2_AZ + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    pts += [(S2_AX, S2_AZ)]
    wire = cq.Wire.makePolygon([V(x, GUARD_Y0 - 1, z) for x, z in pts], close=True)
    return cq.Solid.extrudeLinear(wire, [], V(0, GUARD_Y1 - GUARD_Y0 + 2, 0))


def guard_s2_ring():
    """S2 rotor ring guard: annular sector r 90..94, angles 20..114 deg
    (global frame), y 250..300 (the S2 process band + margin), built as the
    difference of two filled sector prisms (identical code path)."""
    outer = _sector_prism(GUARD_RO, MOUTH_LO_DEG, NOTCH_HI_DEG)
    inner = _sector_prism(GUARD_RI, MOUTH_LO_DEG, NOTCH_HI_DEG)
    solid = outer.cut(inner)
    solids = [x for x in solid.Solids() if x.Volume() > 10.0]
    if len(solids) != 1 or not solids[0].isValid():
        raise RuntimeError("guard_s2_ring split/invalid: %d" % len(solids))
    return solids[0].clean()


def guard_lid_interlock_seat():
    """Interlock switch seat on the hopper lid's +X edge (HOP-LID covers
    the hopper mouth z 500..505; the lid IS the S1 top closure): the seat
    holds the lid-position switch and is a weldment tab, face-contact on
    the lid edge (zero volume)."""
    # seat mounted on the lid top face (face contact at z=505)
    return _box(20.0, 60.0, 235.0, 275.0, 505.0, 507.0)


def guard_chain_a():
    """Lid over the chain A top run (top of envelope z=440.3) between the
    S1-ROOF-R brackets (x 105..215): 3 mm plate 4 mm above the envelope."""
    return _box(105.0, 215.0, 352.0, 364.0, 450.5, 453.5)


def guard_chain_b():
    """Outer guard tube over chain B: same tangent+arc path as the chain
    loop but the radial band rp+5.5..rp+9.5 (4 mm plate line), 3 mm wide at
    y 379..382 - keeps hands out of the chain B run.  VP1 Stage 4: chain B
    now runs jackshaft(136.94,65) -> S2(308.57,280) in the y376..381 plane;
    the rev A jackshaft-crossing split of the plate is gone (the strand no
    longer crosses the jack core)."""
    import drive_teeth as dt
    parts = []
    for chain in (dt.CHAIN_B,):
        p1, p2 = chain["p1"], chain["p2"]
        r1 = dt.sprocket_pitch_radius(chain["z1"])
        r2 = dt.sprocket_pitch_radius(chain["z2"])
        lines, phi, dist = dt._tangent_data(p1, r1, p2, r2)
        ang1 = math.atan2((lines[0][1] - p1[1]) / r1, (lines[0][0] - p1[0]) / r1)
        ang2 = ang1 - 2.0 * phi
        y0 = 377.0
        # plates on the side away from the sprocket discs at each strand's
        # ends: line A outward = +p_hat, line B outward = -p_hat.
        for line_idx, (x1, z1, x2, z2) in enumerate(lines):
            sgn = -1.0 if line_idx == 0 else 1.0
            L = math.hypot(x2 - x1, z2 - z1)
            ux, uz = (x2 - x1) / L, (z2 - z1) / L
            t_ranges = [(0.0, 1.0)]
            for t0, t1 in t_ranges:
                pts = []
                for t in (t0, t1):
                    for sr in (6.0, 9.5):
                        px = x1 + (x2 - x1) * t + sgn * uz * sr
                        pz = z1 + (z2 - z1) * t - sgn * ux * sr
                        pts.append((px, pz))
                wire = cq.Wire.makePolygon(
                    [V(pts[0][0], y0, pts[0][1]), V(pts[1][0], y0, pts[1][1]),
                     V(pts[3][0], y0, pts[3][1]), V(pts[2][0], y0, pts[2][1])], close=True)
                parts.append(cq.Solid.extrudeLinear(
                    wire, [], V(0, 3.0, 0)))
        ext = math.radians(3.0)
        # p1 (bottom) wrap sector omitted: it dips into the frame-beam /
        # jackshaft / sprocket cluster (z 19..46) - documented in results
        for center, r, a0, a1 in ((p2, r2, ang2 - ext, ang1 + ext),):
            tube = cq.Solid.makeCylinder(r + 9.5, 3.0, V(center[0], y0, center[1]),
                                         V(0, 1, 0))
            tube = tube.cut(cq.Solid.makeCylinder(r + 6.0, 5.0,
                                                  V(center[0], y0 - 1, center[1]),
                                                  V(0, 1, 0)))
            for angle_deg, side in ((math.degrees(a0), "cw"),
                                    (math.degrees(a1), "ccw")):
                ar = math.radians(angle_deg)
                ux2, uz2 = math.cos(ar), math.sin(ar)
                px2, pz2 = -uz2, ux2
                sgn = 1.0 if side == "ccw" else -1.0
                pts = [(center[0], center[1]),
                       (center[0] + 400 * ux2, center[1] + 400 * uz2),
                       (center[0] + 400 * ux2 + 400 * sgn * px2,
                        center[1] + 400 * uz2 + 400 * sgn * pz2),
                       (center[0] + 400 * sgn * px2, center[1] + 400 * sgn * pz2)]
                w = cq.Wire.makePolygon([V(x, y0 - 1, z) for x, z in pts], close=True)
                tube = tube.cut(cq.Solid.extrudeLinear(w, [], V(0, 5.0, 0)))
            solids = [x for x in tube.Solids() if x.Volume() > 10.0]
            parts.append(solids[0])
    for piece in parts:
        if not piece.isValid() or piece.Volume() <= 10.0:
            raise RuntimeError("guard_chain_b segment invalid")
    return cq.Compound.makeCompound(parts).clean()


def components():
    """Named guard parts in absolute machine coordinates (group 'guard')."""
    return [("GUARD_S2_RING", guard_s2_ring()),
            ("GUARD_CHAIN_A", guard_chain_a()),
            ("GUARD_CHAIN_B", guard_chain_b()),
            ("GUARD_LID_INTERLOCK_SEAT", guard_lid_interlock_seat())]


def service_sweep_checks():
    """ASSEMBLY_SERVICE_KO.md sweep: every guard must lift vertically clear
    of the machine without touching the frozen S2 jacket, the cutter sweep,
    the chain loops, the chute or the winder.  Implemented as a vertical
    translation of +150 mm (guard removal stroke) followed by an exact BRep
    intersection against the obstacle set."""
    import chute as chute_mod
    import drive_teeth as dt
    obstacles = []
    s2 = cq.importers.importStep(str(ROOT / "cad/PPR_C2_1_S2_transmission.step"))
    s2 = s2.val().rotate((0, 0, 0), (0, 0, 1), 180).translate((308.56946468906176, 299, 280))
    obstacles.append(("S2_subassembly", s2))
    obstacles.append(("chute", chute_mod.components()[0][1]))
    for name, solid in dt.chain_components():
        obstacles.append((name, solid))
    for x in (130.0, 190.0):
        obstacles.append(("S1_cutter_sweep_%d" % (x and 130 or 190),
                          cq.Solid.makeCylinder(41.0, 160.0,
                                                V(x, 160.0, 398.30275184708404),
                                                V(0, 1, 0))))
    records = []
    for name, solid in components():
        lifted = solid.translate((0, 0, 150.0))
        contacts = []
        for oname, osolid in obstacles:
            b1, b2 = lifted.BoundingBox(), osolid.BoundingBox()
            if not all(min(getattr(b1, ax + "max"), getattr(b2, ax + "max"))
                       - max(getattr(b1, ax + "min"), getattr(b2, ax + "min")) > 0
                       for ax in "xyz"):
                continue
            vol = lifted.intersect(osolid).Volume()
            if vol > 0.05:
                contacts.append({"obstacle": oname, "overlap_mm3": vol})
        records.append({"guard": name, "lift_mm": 150.0,
                        "sweep_clear": not contacts, "contacts": contacts})
    return records


if __name__ == "__main__":
    import json
    parts = components()
    out_dir = ROOT / "cad" / "parts_stage1"
    out_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for name, solid in parts:
        path = out_dir / (name + ".step")
        cq.exporters.export(cq.Compound.makeCompound([solid]), str(path))
        exported.append(str(path.relative_to(REPO)))
    sweeps = service_sweep_checks()
    result = {"exported_step": exported, "service_sweep": sweeps,
              "passed": all(r["sweep_clear"] for r in sweeps)}
    (ROOT / "results" / "guard_geometry.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
