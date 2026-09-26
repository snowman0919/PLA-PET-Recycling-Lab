"""VP1 Stage 6: unit tests for downstream modules and process model.

Verifies:
1. downstream CAD parts validity and mutual non-interference
2. station interface datums (filament line y=275, z=125, delay=20mm)
3. process model mass-balance invariants and cooling monotonicity
4. quality accounting excluding unmeasured length
"""
import math
import sys
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "src"))

try:
    import cadquery  # noqa: F401
    HAVE_CQ = True
except ImportError:
    HAVE_CQ = False

if HAVE_CQ:
    import downstream as dd
    import winder as w

import process_model as pm
import route_comparison as rc


class DownstreamGeometryTests(unittest.TestCase):
    """BRep validity and non-interference for downstream modules."""

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_production_components_valid_and_single(self):
        parts = dd.components()
        self.assertEqual(len(parts), 6)
        names = [name for name, solid, group in parts]
        self.assertIn("GAUGE_FRAME", names)
        self.assertIn("GAUGE_GUIDES", names)
        self.assertIn("GAUGE_CONTACT_A", names)
        self.assertIn("GAUGE_OPTICAL_B", names)
        self.assertIn("GAUGE_REF_STANDARD", names)
        self.assertIn("COOL-DUCT", names)
        for name, solid, group in parts:
            self.assertTrue(solid.isValid(), f"{name} is invalid")
            self.assertGreaterEqual(len(solid.Solids()), 1, f"{name} has no solids")

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_swap_parts_valid(self):
        swaps = dd.swap_parts()
        self.assertEqual(len(swaps), 1)
        name, solid, group = swaps[0]
        self.assertEqual(name, "SERVICE-HOPPER")
        self.assertTrue(solid.isValid())
        bb = solid.BoundingBox()
        # mounts onto FEED-BUF saddle interface at z=145
        self.assertAlmostEqual(bb.zmin, 142.0, delta=1.0)
        self.assertAlmostEqual(bb.zmax, 221.0, delta=1.0)

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_gauge_internal_clearances(self):
        parts = {
            "frame": dd.gauge_frame(),
            "guides": dd.gauge_guides(),
            "contact": dd.gauge_contact_a(),
            "optical": dd.gauge_optical_b(),
            "refstd": dd.gauge_ref_standard(),
        }
        names = list(parts)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                overlap = parts[a].intersect(parts[b]).Volume()
                self.assertLess(
                    overlap, 0.001,
                    f"Gauge internal interference between {a} and {b}: {overlap:.4f} mm3",
                )

    @unittest.skipUnless(HAVE_CQ, "cadquery unavailable")
    def test_gauge_vs_puller_clearances(self):
        frame = dd.gauge_frame()
        adj = w.pull_roller_adj()
        fixed = w.pull_roller_fixed()
        pull_frame = w.pull_frame()
        self.assertLess(frame.intersect(adj).Volume(), 0.001)
        self.assertLess(frame.intersect(fixed).Volume(), 0.001)
        self.assertLess(frame.intersect(pull_frame).Volume(), 0.001)

    def test_station_interfaces_datums(self):
        ifaces = dd.station_interfaces()
        self.assertEqual(ifaces["filament_line"]["y_mm"], 275.0)
        self.assertEqual(ifaces["filament_line"]["z_mm"], 125.0)
        self.assertEqual(ifaces["filament_line"]["gauge_x_mm"], 809.0)
        self.assertEqual(ifaces["filament_line"]["puller_nip_x_mm"], 829.0)
        self.assertAlmostEqual(
            ifaces["gauge_to_puller_delay"]["distance_mm"], 20.0, places=3
        )
        self.assertEqual(ifaces["reference_pins_mm"], [1.50, 1.75, 2.00])


class ProcessModelPhysicsTests(unittest.TestCase):
    """Mass balance, delay, cooling and quality accounting invariants."""

    def test_mass_balance_pla_nominal(self):
        # 1.75 mm strand at 12 mm/s in PLA (1240 kg/m3) requires ~0.0358 g/s
        d = pm.steady_diameter_mm(0.0358, 1240.0, 12.0)
        self.assertAlmostEqual(d, 1.75, delta=0.01)

    def test_mass_balance_speed_drawdown(self):
        # Doubling line speed quarters cross section -> halves diameter by sqrt(2)
        d1 = pm.steady_diameter_mm(0.0358, 1240.0, 12.0)
        d2 = pm.steady_diameter_mm(0.0358, 1240.0, 24.0)
        self.assertAlmostEqual(d1 / d2, math.sqrt(2.0), places=3)

    def test_cooling_convection_monotonicity(self):
        p1 = pm.LineParams(material="PLA", ducted_mm=50.0, fans_on=1)
        p2 = pm.LineParams(material="PLA", ducted_mm=250.0, fans_on=3)
        h1 = pm.h_effective(p1)
        h2 = pm.h_effective(p2)
        self.assertGreater(h2, h1)
        # Cooling rate should be more negative with stronger convection
        rate1 = pm.cooling_rate_C_s(180.0, p1, pm.MATERIALS["PLA"])
        rate2 = pm.cooling_rate_C_s(180.0, p2, pm.MATERIALS["PLA"])
        self.assertLess(rate2, rate1)

    def test_quality_summary_unmeasured_exclusion(self):
        # Synthetic samples with a 2-sample dropout
        samples = [
            {"t_s": 0.0, "v_eff_mm_s": 12.0, "d_major_mm": 1.75,
             "d_minor_mm": 1.75, "ovality_mm": 0.0, "d_meas_mm": 1.75},
            {"t_s": 0.1, "v_eff_mm_s": 12.0, "d_major_mm": 1.75,
             "d_minor_mm": 1.75, "ovality_mm": 0.0, "d_meas_mm": None},
            {"t_s": 0.2, "v_eff_mm_s": 12.0, "d_major_mm": 1.75,
             "d_minor_mm": 1.75, "ovality_mm": 0.0, "d_meas_mm": 1.75},
        ]
        q = pm.quality_summary(samples, target_mm=1.75, tol_mm=0.05)
        self.assertGreater(q["unmeasured_length_mm"], 0.0)
        self.assertEqual(q["in_spec_length_mm"], q["total_length_mm"])


class ControllerSafetyTests(unittest.TestCase):
    """Controller safety bounds and robust dropout handling."""

    def test_controller_handles_none_without_exception(self):
        ctrl = rc.PIController(v_nominal=12.0, kp=1.2, ki=0.06)
        v = ctrl(None, 10.0)
        self.assertEqual(v, 12.0)

    def test_controller_clamps_anti_windup(self):
        ctrl = rc.PIController(v_nominal=12.0, v_min=4.0, v_max=30.0)
        # Massive persistent error
        for _ in range(500):
            v = ctrl(3.5, 0.0)
        self.assertLessEqual(v, 30.0)
        self.assertGreaterEqual(v, 4.0)


if __name__ == "__main__":
    unittest.main()
