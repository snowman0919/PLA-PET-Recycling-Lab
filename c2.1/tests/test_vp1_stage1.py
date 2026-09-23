"""VP1 Stage 1: real drivetrain geometry + S1->S2 chute tests.

CAD-dependent tests skip when cadquery is unavailable (the pure-kinematics
tests always run).
"""
import json
import math
import sys
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "src"))

import drive_kinematics as dk  # pure math: no cadquery dependency

try:
    import cadquery  # noqa: F401
    HAVE_CQ = True
except ImportError:
    HAVE_CQ = False

if HAVE_CQ:
    import drive_teeth as dt
    import chute as chute_mod


class GearRatioKinematics(unittest.TestCase):
    """Tooth-count kinematics recomputed from design/parameters.json."""

    @classmethod
    def setUpClass(cls):
        cls.params = json.loads((R.parent / "design" / "parameters.json").read_text())

    def test_center_distance_from_parameters(self):
        d = self.params["drive"]
        mn, beta = d["normal_module"], math.radians(d["helix_deg"])
        c = (d["pinion_teeth"] + d["gear_teeth"]) * mn / (2.0 * math.cos(beta))
        # instance datum: input shaft x=80, jackshaft x=136.94018992255457
        self.assertAlmostEqual(c, 136.94018992255457 - 80.0, places=9)

    def test_chain_ratios_and_s1_counter_rotation(self):
        d = self.params["drive"]
        rpm = self.params["M1"]["rated_rpm"]
        r = dk.ratio_chain(rpm)
        self.assertAlmostEqual(r["jackshaft_rpm"],
                               -rpm * d["pinion_teeth"] / d["gear_teeth"])
        self.assertAlmostEqual(r["s1_shaft_A_rpm"], r["jackshaft_rpm"])
        # S1-SYNC is a 30T/30T external mesh at center distance 60 mm
        # (shafts at x=130 and x=190, module 2): shaft B counter-rotates.
        self.assertEqual(r["s1_shaft_B_rpm"], -r["s1_shaft_A_rpm"])
        # The jackshaft, not the M1 input shaft, drives both chains.
        self.assertAlmostEqual(r["s2_input_rpm"],
                               r["jackshaft_rpm"] *
                               d["chain_B_teeth"][0] / d["chain_B_teeth"][1])
        self.assertAlmostEqual(r["s2_ecc_rpm"], r["s2_input_rpm"])
        self.assertAlmostEqual(r["s2_output_rpm"],
                               -r["s2_ecc_rpm"] / self.params["S2"]["guide_lobes"])
        self.assertAlmostEqual(r["worm_shaft_rpm"], r["s2_ecc_rpm"])
        self.assertAlmostEqual(r["auger_rpm"],
                               r["worm_shaft_rpm"] * dk.WORM_WHEEL_RATIO)


@unittest.skipUnless(HAVE_CQ, "cadquery not available")
class GearGeometry(unittest.TestCase):
    def test_replacement_solids_single_and_valid(self):
        for inst in dt.INSTANCE_PART:
            s = dt.replacement_local_solid(inst)
            self.assertEqual(len(s.Solids()), 1, inst)
            self.assertTrue(s.isValid(), inst)

    def test_tooth_counts_counted_from_solids(self):
        for inst in dt.INSTANCE_PART:
            part = dt.INSTANCE_PART[inst]
            if part in dt.GEAR_PARTS:
                z = dt.GEAR_SPECS[part]["z"]
                r = dt.gear_pitch_radius(z)
                y = 12.5
            else:
                z = dt.SPROCKET_TEETH[part]
                r = dt.sprocket_pitch_radius(z)
                y = 4.0
            self.assertEqual(dt.count_teeth(dt.replacement_local_solid(inst),
                                            r, y=y, samples=1440), z, inst)

    def test_mesh_phase_no_interference(self):
        records = dt._mesh_check(samples=4)
        for rec in records:
            self.assertLess(rec["overlap_mm3"], 0.05, rec)


@unittest.skipUnless(HAVE_CQ, "cadquery not available")
class ChainGeometry(unittest.TestCase):
    def test_tangent_lines_touch_pitch_circles(self):
        for chain in (dt.CHAIN_A, dt.CHAIN_B):
            lines, phi, dist = dt._tangent_data(
                chain["p1"], dt.sprocket_pitch_radius(chain["z1"]),
                chain["p2"], dt.sprocket_pitch_radius(chain["z2"]))
            for (x1, z1, x2, z2) in lines:
                vx, vz = x2 - x1, z2 - z1
                L = math.hypot(vx, vz)
                for (cx, cz), r in ((chain["p1"], dt.sprocket_pitch_radius(chain["z1"])),
                                    (chain["p2"], dt.sprocket_pitch_radius(chain["z2"]))):
                    d = abs((cx - x1) * (vz / L) - (cz - z1) * (vx / L))
                    self.assertAlmostEqual(d, r, places=6)

    def test_chain_length_matches_link_count(self):
        for chain in (dt.CHAIN_A, dt.CHAIN_B, dt.CHAIN_P):
            comp = dt.chain_length_mm(chain)
            nominal = chain["links"] * dt.CHAIN_PITCH
            self.assertLessEqual(abs(comp - nominal), 1.0,
                                 "nominal #35 chain must fit the routed pitch loop")

    def test_chain_solids_single_valid_right_y(self):
        for name, solid in dt.chain_components():
            self.assertEqual(len(solid.Solids()), 1, name)
            self.assertTrue(solid.isValid(), name)
            bb = solid.BoundingBox()
            y0 = dt.CHAIN_A["y0"] if name.endswith("A") else dt.CHAIN_B["y0"]
            self.assertAlmostEqual(bb.ymin, y0, places=6)
            self.assertAlmostEqual(bb.ymax, y0 + dt.CHAIN_AXIAL, places=6)


@unittest.skipUnless(HAVE_CQ, "cadquery not available")
class ChuteGeometry(unittest.TestCase):
    def test_valid_parts_clear_cutter_sweep(self):
        parts = chute_mod.components()
        sweeps = chute_mod.cutter_sweep_solids()
        for name, solid, group in parts:
            self.assertTrue(solid.isValid(), name)
        # The active screw and its mechanical drive are present, while the
        # failed paddle/scraper design is absent. Every part, not merely the
        # final loop variable, must clear the cutter sweep.
        names = [n for n, _, _ in parts]
        for required in ("AUG_SHAFT", "AUG_WHEEL", "PDL_WORM"):
            self.assertIn(required, names)
        self.assertNotIn("PDL_WHEEL", names)
        self.assertNotIn("PDL_SCRAPER", names)
        for name, solid, _ in parts:
            for i, sw in enumerate(sweeps):
                b1, b2 = solid.BoundingBox(), sw.BoundingBox()
                overlap = all(min(getattr(b1, a + "max"), getattr(b2, a + "max"))
                              - max(getattr(b1, a + "min"), getattr(b2, a + "min")) > 0
                              for a in "xyz")
                if overlap:
                    self.assertLessEqual(solid.intersect(sw).Volume(), 1e-6,
                                         "%s vs cutter sweep %d" % (name, i))

    def test_support_plate_clearance(self):
        floor = chute_mod.pan_floor()
        # no floor material in the support-plate band beyond the chamfer
        # line (plate material exists where z-x <= 96.43; keep >= 4 mm margin)
        band = chute_mod.cq.Solid.makeBox(
            52.0, 8.0, 30.0, chute_mod.cq.Vector(248.0, 203.0, 340.0))
        hit = floor.intersect(band)
        vols = [x.Volume() for x in hit.Solids()]
        self.assertLessEqual(max(vols) if vols else 0.0, 0.05)
        self.assertGreaterEqual(348.0 - 245.5 - 96.43, 4.0)

    def test_fin_dam_defect_is_measured_not_hidden(self):
        # the frozen 115deg saddle fin protrudes through the trough channel;
        # the checker must report it (material-path FAIL), never silently pass
        fin = chute_mod._obstruction_solid()
        band = chute_mod.cq.Solid.makeBox(7.0, 34.0, 20.0,
                                          chute_mod.cq.Vector(271.5, 258.0, 344.0))
        blocked = band.intersect(fin)
        self.assertGreater(blocked.Volume(), 1000.0)


class MaterialPathApertures(unittest.TestCase):
    """Aperture continuity from path_check.json (runs after path_check.py)."""

    @classmethod
    def setUpClass(cls):
        p = R / "results" / "path_check.json"
        if not p.exists():
            raise unittest.SkipTest("run c2.1/src/path_check.py first")
        cls.data = json.loads(p.read_text())

    def test_every_checkpoint_reported(self):
        names = [c["checkpoint"] for c in self.data["checkpoints"]]
        for need in ("S1_opening_to_pan", "trough_fin_gap",
                     "cross_feed_shell_to_mouth", "outlet_drop_into_mouth",
                     "s2_screen_holes", "buffer_throat", "extruder_die_exit",
                     "puller_nip", "puller_grip", "spool_winder"):
            self.assertIn(need, names)

    def test_downstream_apertures_pass(self):
        for c in self.data["checkpoints"]:
            if c["checkpoint"] in ("s2_screen_holes", "buffer_throat",
                                   "extruder_die_exit", "puller_nip"):
                self.assertTrue(c["passed"], c)

    def test_stage2_fixes_hold(self):
        # addendum: the fin-dam was engineered out (bypass route) and the
        # winder is real; both checkpoints must now PASS
        by_name = {c["checkpoint"]: c for c in self.data["checkpoints"]}
        self.assertTrue(by_name["trough_fin_gap"]["passed"])
        self.assertTrue(by_name["spool_winder"]["passed"])

    def test_pass_grip_split(self):
        # VP1 Stage 4: PASS-space and OPERATIONAL-GRIP checkpoints are
        # distinct classes; the grip checkpoint must prove positive nip
        # engagement (stop gap < filament <= open gap), not just clearance.
        by_name = {c["checkpoint"]: c for c in self.data["checkpoints"]}
        self.assertIn("checkpoint_class", by_name["puller_grip"])
        self.assertEqual(by_name["puller_grip"]["checkpoint_class"],
                         "operational_grip")
        self.assertEqual(by_name["puller_nip"]["checkpoint_class"],
                         "pass_space")
        self.assertTrue(by_name["puller_grip"]["passed"])
        self.assertTrue(self.data["all_grip_checkpoints_pass"])
