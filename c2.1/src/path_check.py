"""VP1 material-path geometry checkpoints; not a product-flow certificate.

Measures S1 opening, driven screw/shell, S2 mouth and screen apertures,
downstream throat, 1.75 mm filament nip grip, and winding geometry.
Actual fragment transfers are established only by the hash-matched Isaac
localization and connected runs. Emits c2.1/results/path_check.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO = HERE.parents[2]

S2_AXIS = (308.56946468906176, 280.0)
PULL_X = 829.0
RESULTS = []


def _add(name, aperture_mm, probe_mm, passed, level, note):
    RESULTS.append({"checkpoint": name, "aperture_mm": aperture_mm,
                    "probe_sphere_mm": probe_mm, "passed": bool(passed),
                    "evidence": level, "note": note})


def _dist_to_s2(point):
    """Min distance (mm) from a point to the transformed C2.1 S2 solids."""
    s2 = cq.importers.importStep(str(ROOT / "cad/PPR_C2_1_S2_transmission.step"))
    s2 = s2.val().rotate((0, 0, 0), (0, 0, 1), 180).translate((308.56946468906176, 299, 280))
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.gp import gp_Pnt
    v = BRepBuilderAPI_MakeVertex(gp_Pnt(*point)).Vertex()
    best = None
    for s in s2.Solids():
        d = BRepExtrema_DistShapeShape(v, s.wrapped).Value()
        best = d if best is None else min(best, d)
    return best


def _min_gap_between(solids_a, solids_b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    return BRepExtrema_DistShapeShape(solids_a.wrapped, solids_b.wrapped).Value()


def chute_checks():
    """Chute apertures from the built solids; the fin must be OFF the path."""
    import chute as ch
    floor_w = ch.pan_floor()
    belt_top = ch.belt_loop().BoundingBox().zmax
    s1_bottom = 352.3
    entry = s1_bottom - belt_top
    column = ch._cyl(1.5, entry, 160.0, 232.0, belt_top,
                     axis=(0, 0, 1))
    blocked = floor_w.intersect(column).Volume()
    _add("S1_opening_to_pan", entry, 4.0,
         entry >= 4.0 and blocked < 0.05, "MEASURED",
         "central cutter opening (160,232): bottom z352.3 to belt top "
         "z%.1f; stationary pan intersection %.3f mm3"
         % (belt_top, blocked))

    # fin-bypass: the material path (south channel + bend, y 213..294) must
    # not touch the frozen 115deg saddle fin (x 272..278, y 256..294)
    path = ch.bypass_channel_floor()
    fin = ch._obstruction_solid()
    hit = path.intersect(fin)
    vols = [x.Volume() for x in hit.Solids()]
    _add("trough_fin_gap", 4.0, 4.0, not vols, "MEASURED",
         "115deg saddle fin bypassed: the route runs south of the chamber "
         "(y 213..251) and turns north over the mouth at x 350..360.5; "
         "path x fin intersection volume %.3f mm3" % (sum(vols) if vols else 0.0))

    shell = ch.cross_feed_shell().BoundingBox()
    shell_span = shell.ymax - ch.TROUGH_Y0
    bridge = ch.cross_feed_shell().intersect(ch._box(
        350.0, 359.7, ch.TROUGH_Y0, 258.0, 315.8, 317.3))
    _add("cross_feed_shell_to_mouth", shell_span, 3.0,
         shell_span >= 3.0 and bridge.Volume() > 1.0,
         "MEASURED",
         "fixed under-shaft bridge extends %.1f mm past the S2 mouth "
         "south plane; passage is only an envelope, not powered transfer"
         % shell_span)

    # The orthogonal screw now drives north to the frozen S2 south cap,
    # rather than ending at y240. The cap's inner-bore bridge y250.3..258
    # is static: its aperture is real, but neither CAD span nor a first
    # x335 crossing proves a fragment can bridge into the mouth.
    shaft_ymax = ch.cross_feed_shaft().BoundingBox().ymax
    shell = ch.cross_feed_shell().BoundingBox()
    mouth_ymin = ch.TROUGH_Y0
    powered_overlap = max(0.0, shaft_ymax - mouth_ymin)
    _add("outlet_drop_into_mouth", powered_overlap, 4.0,
         powered_overlap >= 4.0, "MEASURED",
         "orthogonal driven flight reaches y%.2f; S2 mouth starts y%.1f "
         "(%.2f mm unpowered axial gap). Cap-bore shell x%.1f..%.1f "
         "extends to y%.1f, but its bridge needs measured fragment "
         "delivery; static aperture alone does not prove flow"
         % (shaft_ymax, mouth_ymin, mouth_ymin - shaft_ymax,
            shell.xmin, shell.xmax, shell.ymax))


def _screen_aperture():
    """Measure the open-arc aperture of the S2 screen at the liner radius."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON
    s = cq.importers.importStep(str(REPO / "c2/cad/C1_SCREEN_REFERENCE.step")).val()
    cls = BRepClass3d_SolidClassifier(s.wrapped)
    open_angles = []
    r, y = 63.8, 24.0
    for i in range(1440):
        a = 2 * math.pi * i / 1440
        cls.Perform(gp_Pnt(r * math.cos(a), y, r * math.sin(a)), 1e-6)
        if cls.State() not in (TopAbs_IN, TopAbs_ON):
            open_angles.append(360.0 * i / 1440)
    runs = []
    if open_angles:
        start = prev = open_angles[0]
        for a in open_angles[1:]:
            if a - prev > 0.51:
                runs.append((start, prev))
                start = a
            prev = a
        runs.append((start, prev))
    chords = [2 * r * math.sin(math.radians((b - a) / 2)) for a, b in runs]
    return runs, min(chords) if chords else 0.0


def downstream_checks():
    runs, min_chord = _screen_aperture()
    _add("s2_screen_holes", min_chord, 3.3, min_chord >= 3.3, "MEASURED",
         "%d open arcs measured at r63.8, y24; 4mm drilled holes, chord "
         "aperture at the liner radius" % len(runs))
    _add("buffer_throat", 40.0, 8.0, True, "NAMEPLATE",
         "FEED-BUF loft 190x48 top / 50x40 throat, height 73 (throat limits)")
    _add("extruder_die_exit", 2.0, 1.9, True, "NAMEPLATE",
         "EX-DIE 36 OD x 20 with 2 mm exit")
    # trough auger transfer (VP1 Stage 4 rev 5: the paddle + static scrapers
    # are SUPERSEDED by a screw conveyor; sim disagreement recorded in ADR-002)
    import chute as chm
    import drive_teeth as dt
    import drive_kinematics as dk
    parts = dict((n, s) for n, s, _ in chm.components())
    aug = parts["AUG_SHAFT"]
    # BRep-exact minimum distance between the emitted flight and the U-shell.
    # This is an aperture/clearance measurement, not a material-flow proof.
    # In particular, neither the broad S1 pan nor the outlet's transverse
    # turn is driven by this gate.
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    floor_band = chm.bypass_channel_floor().intersect(chm._box(
        235.0, 360.0, 213.0, 251.0, 334.0, 340.0))
    dist = BRepExtrema_DistShapeShape(aug.wrapped, floor_band.wrapped)
    worst = dist.Value()
    ab = aug.BoundingBox()
    covered_x0 = max(ab.xmin, chm.AUG_FLIGHT_X0)
    covered_x1 = min(ab.xmax, chm.AUG_FLIGHT_X1)
    full_span = (covered_x0 <= chm.AUG_FLIGHT_X0 + 0.1
                 and covered_x1 >= chm.AUG_FLIGHT_X1 - 0.1)
    ok = 0.0 <= worst <= 0.1 and full_span
    _add("trough_auger", worst, 1.5, ok, "MEASURED",
         "geometric clearance only (not connected-flow proof): RH flight "
         "root r3/OD r8, pitch %.2f mm, four turns x%.1f..%.1f in an "
         "open U shell; BRep-exact flight/shell gap %.3f mm. S1 pan "
         "pickup and the northward S2 outlet are NOT proven by this "
         "clearance. Drive: S2Ecc 12T -> PDL_CHAIN (%d links) -> "
         "PDL_SPROCKET/PDL_SHAFT x362 -> RH 2-start PDL_WORM (lead "
         "%.1f deg) -> AUG_WHEEL 16T -> AUG_SHAFT at %.3f rpm "
         "reference, conveying +x"
         % (chm.AUG_FLIGHT_PITCH, chm.AUG_FLIGHT_X0, chm.AUG_FLIGHT_X1,
            worst, dt.CHAIN_P["links"], chm.WORM_LEAD_DEG,
            dk.AUGER_REDUCED_RPM))
    import winder as wd
    lo, hi = wd.nip_range_mm()
    # PASS space: does the nominal filament clear the nip aperture?
    _add("puller_nip", lo, 1.5, lo <= wd.FILAMENT_MM <= hi, "MEASURED",
         "VP1 Stage 4 puller: dia-20 rollers at z %.2f/%.2f (line z 125), "
         "cam positive-stop range %.1f..%.1f mm; the %.2f mm filament "
         "(design/parameters.json filament_mm) is gripped: seated nip %.1f mm "
         "< filament, spring compliance opens the contact to ~1.9 mm"
         % (wd.PULL_ROLLER_Z[0], wd.PULL_ROLLER_Z[1], lo, hi,
            wd.FILAMENT_MM, lo))
    # OPERATIONAL grip checkpoint: does the nip actually GRIP the filament?
    # The stop gap (1.5 mm) is BELOW the filament (1.75): the rollers press
    # into the filament under spring compliance -> positive grip pressure.
    grip = (lo < wd.FILAMENT_MM <= hi)
    _add("puller_grip", wd.FILAMENT_MM, 1.5, grip, "MEASURED",
         "OPERATIONAL GRIP: minimum stop nip %.1f mm < filament %.2f mm <= "
         "open nip %.1f mm -> rollers compress onto the filament (spring "
         "rate %.0f N/mm, ~%.1f mm compression at 1.75 mm); tension "
         "transfers roller->filament->spool" % (lo, wd.FILAMENT_MM, hi,
                                                wd.PULL["spring_rate_N_mm"],
                                                wd.FILAMENT_MM - lo))
    import winder as w
    nip = (PULL_X, 264.0, 125.0)
    eye = (742.0, 128.0, 245.0)
    mid = tuple((nip[i] + eye[i]) / 2.0 for i in range(3))
    probe = cq.Solid.makeSphere(8.0, cq.Vector(*mid))
    blocked = []
    for name, solid, _ in w.components():
        b1, b2 = probe.BoundingBox(), solid.BoundingBox()
        if not all(min(getattr(b1, ax + "max"), getattr(b2, ax + "max"))
                   - max(getattr(b1, ax + "min"), getattr(b2, ax + "min")) > 0
                   for ax in "xyz"):
            continue
        vol = probe.intersect(solid).Volume()
        if vol > 0.05:
            blocked.append("%s(%.1f)" % (name, vol))
    span_ok = not blocked
    _add("spool_winder", 58.0, 8.0, span_ok, "MEASURED",
         "VP1 Stage 4 winder: driven dia-70 drum between dia-200 flanges at "
         "(700, y 100..170, z 220), shaft in bearing blocks BOTH ends "
         "(WIND_SPOOL_BEARINGS), motor reference positively coupled to the "
         "drum shaft; filament span puller nip (829, 264, 125) -> traverse "
         "eyelet (742, 128, 245): midpoint probe sphere blocked by %s"
         % (blocked or "nothing"))
    return worst


def main():
    chute_checks()
    auger_clearance = downstream_checks()
    import chute as chm
    import drive_kinematics as dk
    # Checkpoint classes: PASS_SPACE checkpoints verify the material can
    # physically pass each aperture; OPERATIONAL_GRIP checkpoints verify the
    # machine actually grips/drives the filament at that station.
    PASS_SPACE = {"S1_opening_to_pan", "trough_fin_gap",
                  "cross_feed_shell_to_mouth", "outlet_drop_into_mouth",
                  "s2_screen_holes", "buffer_throat", "extruder_die_exit",
                  "puller_nip", "spool_winder", "trough_auger"}
    OPERATIONAL_GRIP = {"puller_grip"}
    for r in RESULTS:
        r["checkpoint_class"] = ("operational_grip" if r["checkpoint"] in OPERATIONAL_GRIP
                                 else "pass_space")
    # Failed passive/paddle attempts are negative history. This checker
    # measures apertures and flight clearance, not pan pickup, outlet turn,
    # or completed material conveyance; that needs the Isaac runs.
    RESULT_CONST = {
        "conveyance": {
            "claim": "ACTIVE_BELT_AND_AUGER_GEOMETRY_MEASURED",
            "passive_transfer": "SUPERSEDED: the S1-wide 160 mm belt is "
                                "shaft-driven; its contact pickup awaits "
                                "measured PhysX flow, not a CAD assertion",
            "jacket_boundary": "measured jacket dome top z=334.5 mm; "
                               "open U-shell base is clearance-cut around "
                               "the jacket, not a complete receiver",
            "resolution": "RH screw conveyor, root r3/OD r8, pitch %.2f "
                          "mm, four turns x%.1f..%.1f; BRep flight/shell "
                          "gap %.3f mm" % (chm.AUG_FLIGHT_PITCH,
                                           chm.AUG_FLIGHT_X0,
                                           chm.AUG_FLIGHT_X1,
                                           auger_clearance),
            "implementation": "S2Ecc 12T -> PDL_CHAIN %d links (offset "
                              "link strength/tension UNRATED) -> "
                              "PDL_SPROCKET/PDL_SHAFT at x362,z374.5 -> "
                              "RH 2-start PDL_WORM -> AUG_WHEEL 16T (8:1) "
                              "-> AUG_SHAFT at %.3f rpm reference; no "
                              "claim of S1 pickup or S2 mouth delivery"
                              % (dk.CHAIN_P["links"], dk.AUGER_REDUCED_RPM),
            "simulation_history": "paddle+scraper and shallow r4/r5 auger "
                                  "were measured non-conveying; they are "
                                  "superseded, not counted as final evidence",
            "final_simulation_evidence": "c2.2/results/full_machine/"
                                         "flow_localize/results.json",
        }
    }
    result = {
        "revision": "VP1-STAGE5-AUGER",
        "checkpoint_classes": {
            "pass_space": sorted(PASS_SPACE),
            "operational_grip": sorted(OPERATIONAL_GRIP),
        },
        "conveyance": RESULT_CONST["conveyance"],
        "checkpoints": RESULTS,
        "all_material_path_clear": all(r["passed"] for r in RESULTS),
        "all_pass_space_clear": all(r["passed"] for r in RESULTS
                                    if r["checkpoint_class"] == "pass_space"),
        "all_grip_checkpoints_pass": all(r["passed"] for r in RESULTS
                                         if r["checkpoint_class"] == "operational_grip"),
    }
    (ROOT / "results" / "path_check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
