"""Observable mass-path invariants without CAD/Isaac startup."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim/assets"))
sys.path.insert(0, str(ROOT / "sim"))
from materials import mass_properties, specification  # noqa: E402
from full_machine import aggregate_body_mass  # noqa: E402


class MaterialMassTest(unittest.TestCase):

    def test_unselected_nip_spring_space_cannot_add_fictitious_mass(self):
        bbox = (0., 0., 0., 9., 9., 8.5)
        spring_space = mass_properties("PULL_IDLER_SPRINGS", 500., bbox)
        axle = mass_properties("PULL_ROLLER_ADJ", 500., bbox)
        with_spring = aggregate_body_mass([axle, spring_space])
        self.assertEqual(spring_space["mass_kg"], 0)
        self.assertEqual(spring_space["inertia_kg_mm2"], [0., 0., 0.])
        self.assertEqual(spring_space["mass_bounds_kg"][0], 0)
        self.assertGreater(spring_space["mass_bounds_kg"][1], 0)
        self.assertAlmostEqual(with_spring["mass_kg"], axle["mass_kg"])
        self.assertGreater(with_spring["mass_bounds_kg"][1],
                           axle["mass_bounds_kg"][1])

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
