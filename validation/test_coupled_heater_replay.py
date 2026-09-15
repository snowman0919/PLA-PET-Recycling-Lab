"""Production PI/allocation components exercised against an offline thermal plant."""
import json
import copy
import subprocess
from pathlib import Path
import sys
import unittest
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analysis.thermal_revision_v08.power_loop import PowerLoop, build_library, DEPENDENCIES, SOURCES, SOURCE
from analysis.thermal_revision_v08.coupled_replay import run_case


class CoupledReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = build_library()
        cls.base = json.loads((ROOT/'cad/parameters/baseline.json').read_text())['extruder']
        cls.mount = json.loads((ROOT/'cad/parameters/final_v08.json').read_text())['hot_zone_mount']
        cls.supports = [(375-cls.mount[k]-cls.mount['plate_thickness_mm']/2)/1000
                        for k in ('rear_fixed_plate_x_mm', 'front_sliding_plate_x_mm')]

    def case(self, **kwargs):
        return run_case(self.base, self.supports,
            self.base['heater_zone_axial_ranges_from_barrel_rear_mm'], self.library,
            duration=10, **kwargs)

    def test_compiler_dependencies_are_declared(self):
        used = set()
        for source in SOURCES:
            listing = subprocess.check_output(['g++','-std=c++17','-MM',
                '-I'+str(SOURCE),str(source)],text=True,timeout=30)
            files = listing.split(':',1)[1].replace('\\\n',' ').split()
            used.update(Path(name).resolve() for name in files)
        self.assertEqual(used, {p.resolve() for p in DEPENDENCIES})

    def test_compiled_profile_drift_rejected(self):
        base = copy.deepcopy(self.base)
        base['pet_zone_c'][0] += 1
        with self.assertRaisesRegex(ValueError, 'compiled PET'):
            run_case(base, self.supports, base['heater_zone_axial_ranges_from_barrel_rear_mm'],
                     self.library, duration=1)

    def test_zero_power_equilibrium(self):
        result = self.case(permit_off_s=0)
        self.assertEqual(result['energy_input_j'], 0)
        self.assertAlmostEqual(result['barrel_peak_c'], 25, places=6)
        self.assertTrue(all(result['checks'].values()))

    def test_energy_balance_with_real_switching(self):
        result = self.case()
        self.assertGreater(result['energy_input_j'], 0)
        self.assertTrue(all(result['checks'].values()))

    def test_last_channel_fault_cancels_earlier_channels(self):
        with PowerLoop(self.library) as loop:
            duty, on = loop.step([25]*3+[float('nan')], [245,260,270,265], 1)
            self.assertNotEqual(loop.faults, 0)
            self.assertEqual(on, [False]*4)
            self.assertEqual(duty, [0]*4)
            self.assertEqual(loop.step([25]*4, [245,260,270,265], 251)[1], [False]*4)

    def test_extrusion_power_cap_and_rotation(self):
        watts = np.array([100,100,100,60]); patterns = set()
        with PowerLoop(self.library) as loop:
            self.assertEqual(loop.cap(True), 300)
            for ms in range(1, 2001, 50):
                duty, on = loop.step([25]*4, [245,260,270,265], ms, extrusion=True)
                self.assertLessEqual(float(watts@on), 300)
                self.assertLessEqual(float(watts@np.asarray(duty)/100), 300.0001)
                patterns.add(tuple(on))
        self.assertGreater(len(patterns), 1)

    def test_chain_loss_is_latched_without_power(self):
        result = self.case(chain_open_s=1)
        self.assertEqual(result['first_fault_s'], 1)
        self.assertEqual(result['after_fault_peak_power_w'], 0)
        self.assertTrue(all(result['checks'].values()))

    def test_nan_after_sensor_sampling(self):
        result = self.case(sensor_nan_s=1)
        self.assertEqual(result['first_fault_s'], 1)
        self.assertFalse(result['process_targets_held'])
        self.assertEqual(result['after_fault_peak_power_w'], 0)

    def test_numerical_and_firmware_clocks_stay_distinct(self):
        coarse = self.case(dt=0.05, sensor_tau_s=13)
        fine = self.case(dt=0.025, sensor_tau_s=13)
        self.assertEqual(coarse['sensor_sample_period_s'], fine['sensor_sample_period_s'])
        self.assertLess(abs(coarse['barrel_peak_c']-fine['barrel_peak_c']), 1)
        with self.assertRaises(ValueError):
            self.case(dt=0.04)


if __name__ == '__main__':
    unittest.main()
