"""Observable mass-path invariants without CAD/Isaac startup."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim/assets"))
sys.path.insert(0, str(ROOT / "sim"))
from materials import mass_properties, specification  # noqa: E402
from full_machine import aggregate_body_mass  # noqa: E402


class MaterialMassTest(unittest.TestCase):
    def test_real_part_names_and_mass_ratio(self):
        bbox = (0., 0., 0., 100., 100., 100.)
        volume = 1_000_000.
        steel = mass_properties("S1-SHAFT-A_001", volume, bbox)
        pc = mass_properties("HOPPER_PANEL_L", volume, bbox)
        al = mass_properties("FR-2040-630_001", volume, bbox)
        abs_drum = mass_properties("WIND_SPOOL_DRUM", volume, bbox)
        self.assertEqual([specification(n)["material"] for n in
                          ("HOPPER_PANEL_L", "HOPPER_PANEL_R")],
                         ["PC_FDM"] * 2)
        self.assertEqual([specification(n)["material"] for n in
                          ("HOP-LID_001", "FEED-BUF_001")],
                         ["PC_SHEET"] * 2)
        self.assertEqual([specification(n)["material"] for n in
                          ("HOPPER_SEAM_FRONT", "HOPPER_SEAM_REAR")],
                         ["STEEL"] * 2)
        self.assertEqual(steel["material"], "STEEL")
        self.assertEqual(al["material"], "AL_PROFILE")
        self.assertEqual(abs_drum["material"], "ABS_FDM")
        self.assertAlmostEqual(steel["mass_kg"], 7.85)
        self.assertAlmostEqual(pc["mass_kg"], 1.2)
        self.assertAlmostEqual(al["mass_kg"], 2.7)
        self.assertAlmostEqual(abs_drum["mass_kg"], .676)
        self.assertGreater(steel["mass_kg"] / pc["mass_kg"], 6.)
        for item in (steel, pc, al, abs_drum):
            self.assertGreater(item["mass_kg"], 0)
            self.assertTrue(all(math.isfinite(x) and x > 0
                                for x in item["inertia_kg_mm2"]))
            self.assertTrue(all(upper >= estimate for upper, estimate in zip(
                item["inertia_upper_bound_kg_mm2"], item["inertia_kg_mm2"])))
            self.assertTrue(item["material_source"])
        for item in (pc, al, abs_drum):
            self.assertEqual(item["mass_material_status"], "BOUNDED_PROXY_UNRATED")
            self.assertLess(item["mass_bounds_kg"][0], item["mass_kg"])
            self.assertGreater(item["mass_bounds_kg"][1], item["mass_kg"])
            self.assertTrue(item["bounds_basis"])
        self.assertAlmostEqual(al["mass_bounds_kg"][0], 1.35)
        self.assertAlmostEqual(al["mass_bounds_kg"][1], 4.05)

    def test_purchased_boundary_is_not_solid_steel(self):
        bearing = mass_properties("BR-6001_001", 1_000_000., (0, 0, 0, 100, 100, 100))
        motor = mass_properties("PULL_MOTOR_REF", 1_000_000., (0, 0, 0, 100, 100, 100))
        for part in (bearing, motor):
            self.assertEqual(part["mass_material_status"], "BOUNDED_PROXY_UNRATED")
            self.assertLess(part["mass_bounds_kg"][0], part["mass_kg"])
            self.assertGreater(part["mass_bounds_kg"][1], part["mass_kg"])
            self.assertLess(part["mass_kg"], 7.85)

    def test_body_com_and_parallel_axis_depend_on_distribution(self):
        a = mass_properties("HOPPER_PANEL_L", 1000., (0, 0, 0, 10, 10, 10))
        b = mass_properties("HOPPER_PANEL_R", 1000., (20, 0, 0, 30, 10, 10))
        body = aggregate_body_mass([a, b])
        self.assertEqual(body["center_of_mass_mm"], [15., 5., 5.])
        self.assertAlmostEqual(body["mass_kg"], 2*a["mass_kg"])
        self.assertAlmostEqual(body["inertia_kg_mm2"][1],
                               2*a["inertia_kg_mm2"][1] + 2*a["mass_kg"]*100.)
        self.assertGreater(body["inertia_upper_bound_kg_mm2"][1],
                           body["inertia_kg_mm2"][1])
        with self.assertRaises(ValueError):
            specification("UNKNOWN_STEEL_THING")
        with self.assertRaises(ValueError):
            specification("HOPPER_001")


if __name__ == "__main__":
    unittest.main()
