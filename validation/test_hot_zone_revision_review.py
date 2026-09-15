#!/usr/bin/env python3
"""Independent textbook checks on the new delta-screen solvers."""
import copy
import math
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.final_validation.hot_zone_revision_review import (
    ASSUMPTIONS, beam_screen, thermal_screen, read_geometry)


class HotZoneRevisionTest(unittest.TestCase):
    def test_simply_supported_uniform_beam(self):
        length, od, bore = 0.280, 0.034, 0.0162
        area = math.pi*(od**2-bore**2)/4
        inertia = math.pi*(od**4-bore**4)/64
        ei = ASSUMPTIONS['young_pa']*inertia
        mass_per_length = ASSUMPTIONS['steel_density_kg_m3']*area
        expected_mm = 5*mass_per_length*9.80665*length**4/(384*ei)*1000
        expected_hz = math.pi/(2*length**2)*math.sqrt(ei/mass_per_length)
        result = beam_screen([0,length],od,bore,56,0)
        self.assertAlmostEqual(result['max_deflection_mm']/expected_mm,1,places=5)
        self.assertAlmostEqual(result['first_bending_hz']/expected_hz,1,places=5)
        self.assertLess(result['reaction_error_n'],1e-5)

    def test_current_overhang_equilibrium(self):
        result = beam_screen([0.016,0.110],0.034,0.0162)
        self.assertLess(result['reaction_error_n'],1e-5)
        self.assertLess(abs(result['moment_residual_nm']),1e-5)
        self.assertLess(result['reactions_n'][0],0)

    def test_invalid_geometry(self):
        for stations,od,bore in [([0.1,0.1],0.034,0.0162),
                ([0.1,0.3],0.034,0.0162),([0.016,0.110],0.0162,0.034)]:
            with self.assertRaises(ValueError): beam_screen(stations,od,bore)

    def test_unpowered_thermal_equilibrium(self):
        base,_ = read_geometry(); base = copy.deepcopy(base)
        base['heater_zone_power_w'] = [0,0,0]; base['die_heater_power_w'] = 0
        result = thermal_screen(base,[0.016,0.110],
            base['heater_zone_axial_ranges_from_barrel_rear_mm'],200,8,0.05)
        self.assertAlmostEqual(result['barrel_peak_c'],25,places=6)
        self.assertAlmostEqual(result['die_peak_c'],25,places=6)
        self.assertEqual(result['heat_input_j'],0)
        self.assertLess(result['max_step_energy_residual_j'],1e-7)


if __name__ == '__main__': unittest.main()
