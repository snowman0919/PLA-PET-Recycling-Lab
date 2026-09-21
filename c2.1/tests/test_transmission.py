import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/"src"))
from transmission import (Transmission, cad_positive_y_rotation_xz,
                          cad_y_degrees_for_xz, coupling, external_mesh_sign,
                          ideal_virtual_work, pose, rotation, rotor_force_virtual_work,
                          rotor_point, rotor_point_velocity, validate_case)


class TransmissionContracts(unittest.TestCase):
    def test_inherited_machine_constraints(self):
        r = json.loads((R/"design/requirements.json").read_text())
        self.assertEqual(r["power"], {"psu_V": 24, "psu_rated_W": 800, "operational_cap_W": 500})
        self.assertEqual(r["motors"], {"shared_shredder_M1": 1, "extruder_M2": 1, "M1_selected": False})
        self.assertEqual(r["materials"], ["PLA", "PET", "TPU"])
        self.assertEqual(r["body_limit_mm"], [700, 420, 520])
        self.assertEqual(r["nominal_geometry"]["process_reference_width_mm"], 40)
        compartments = r["nominal_geometry"]["axial_compartments_mm"]
        self.assertEqual(compartments["process"], [4, 44])
        self.assertGreater(compartments["process"][0]-compartments["cycloid_reaction"][1], 0)
        self.assertGreater(compartments["coupling"][0]-compartments["process"][1], 0)

    def test_signed_speeds_and_full_labeled_repeat(self):
        for e in (7, 10, 14):
            for q in (6, 8, 16):
                r = validate_case(Transmission(eccentric_mm=e, q=q,
                                               chamber_diameter_mm=110+2*(e+0.8)))
                self.assertTrue(r["passed"])
                self.assertEqual(r["full_labeled_cycle_input_turns"], q)
                self.assertAlmostEqual(r["signed_speed_rpm"]["rotor_self"], -120/q)
                self.assertGreater(r["one_orbit_labeled_point_displacement_mm"], 1)
                self.assertLessEqual(r["parameters"]["chamber_diameter_mm"], 155)
        with self.assertRaises(ValueError):
            Transmission(eccentric_mm=10, chamber_diameter_mm=125.6)

    def test_external_mesh_parity_and_idler(self):
        self.assertEqual(external_mesh_sign(1), -1)
        self.assertEqual(external_mesh_sign(2), 1)
        self.assertNotEqual(external_mesh_sign(1), external_mesh_sign(2))

    def test_coupling_stroke_and_engagement(self):
        c = Transmission()
        for theta in np.linspace(0, 16*math.pi, 513):
            r = coupling(float(theta), c)
            self.assertAlmostEqual(r["center_excursion_mm"], c.eccentric_mm)
            self.assertAlmostEqual(r["diametral_stroke_mm"], 2*c.eccentric_mm)
            self.assertGreaterEqual(r["nominal_radial_clearance_mm"], c.coupling_radial_clearance_mm-1e-12)
            self.assertTrue(r["loaded_contact_transfer_status"].startswith("HOLD"))

    def test_coupling_relative_speed_finite_difference(self):
        c = Transmission()
        theta = 0.731
        dt = 1e-6
        h = c.omega_in*dt
        before = np.array(coupling(theta-h, c)["relative_center_rotor_frame_mm"])
        after = np.array(coupling(theta+h, c)["relative_center_rotor_frame_mm"])
        speed = np.linalg.norm((after-before)/(2*dt))
        expected = c.eccentric_mm*c.omega_in*(1+1/c.q)
        self.assertAlmostEqual(speed, expected, places=6)
        self.assertAlmostEqual(coupling(theta, c)["relative_center_speed_mm_s"], expected)
        self.assertAlmostEqual(abs(coupling(theta, c)["ideal_roller_spin_relative_carrier_rpm"]), 189.0)
        self.assertNotEqual(coupling(theta, c)["ideal_roller_spin_relative_carrier_rpm"],
                            coupling(theta, c)["ideal_roller_absolute_spin_rpm"])

    def test_cad_xz_sign_and_quarter_orbit(self):
        c = Transmission()
        theta = math.pi/2
        phi = pose(theta, c)["rotor_angle_rad"]
        expected = rotation(phi) @ np.array([50.0, 0.0])
        actual = cad_positive_y_rotation_xz([50.0, 0.0], cad_y_degrees_for_xz(phi))
        np.testing.assert_allclose(actual, expected, atol=1e-12)
        self.assertAlmostEqual(pose(theta, c)["orbit_center_mm"][0], 0, places=12)
        self.assertAlmostEqual(pose(theta, c)["orbit_center_mm"][1], c.eccentric_mm)
        self.assertLess(expected[1], 0)

    def test_contact_velocity_independent_finite_difference(self):
        c = Transmission()
        p = np.array([55.0, 3.0])
        theta = 1.234
        dt = 1e-6
        h = c.omega_in*dt
        fd = (rotor_point(p, theta+h, c)-rotor_point(p, theta-h, c))/(2*dt)
        np.testing.assert_allclose(fd, rotor_point_velocity(p, theta, c), rtol=0, atol=1e-5)

    def test_virtual_work_and_fixed_reaction(self):
        r = ideal_virtual_work(Transmission(), 8)
        self.assertAlmostEqual(r["power_residual_W"], 0, places=12)
        self.assertAlmostEqual(r["torque_balance_residual_Nm"], 0, places=12)
        self.assertEqual(r["power_on_mechanism_W"]["fixed_ring_W"], 0)
        self.assertLess(r["omega_rad_s"]["output_carrier"], 0)

    def test_orbiting_rotor_force_virtual_work(self):
        c = Transmission()
        force = np.array([-120.0, 35.0])
        point = np.array([55.0, 4.0])
        theta = 0.71
        moment = 2.0
        r = rotor_force_virtual_work(force, point, theta, c, moment)
        dt = 1e-6
        h = c.omega_in*dt
        fd_v = (rotor_point(point, theta+h, c)-rotor_point(point, theta-h, c))/(2*dt)/1000
        fd_power = float(force@fd_v + moment*(-c.omega_in/c.q))
        self.assertAlmostEqual(r["load_power_W"], fd_power, places=7)
        self.assertAlmostEqual(r["power_residual_W"], 0, places=12)

    def test_performance_and_hardware_gates_stay_honest(self):
        r = json.loads((R/"design/requirements.json").read_text())
        self.assertEqual(r["performance_gate"], "BLOCKED_PERFORMANCE_DATA")
        self.assertTrue(all(r["deployment"][x] == "HOLD" for x in ("procurement", "fabrication", "energization")))
        self.assertEqual(r["ratings"]["coupling"], "HOLD")
        self.assertEqual(r["ratings"]["bearings"], "HOLD")
        self.assertEqual(r["ratings"]["perforated_screen_sensor_thermal_integration"], "HOLD")


if __name__ == "__main__":
    unittest.main()
