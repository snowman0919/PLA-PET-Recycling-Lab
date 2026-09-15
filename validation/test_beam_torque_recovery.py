"""Negative tests for measured B31 root torque recovery."""
import math
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis/final_validation'))
from beam_torque_recovery import expanded_root_torque, add_measured_root_torque

class TorqueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'model.frd'
        self.write()
    def write(self, count=4, force=True, sign=1.):
        yz=[(-.01,-.01),(-.01,.01),(.01,-.01),(.01,.01)]
        lines=['    2C']
        lines += [f' -1 {i} 0 {y} {z}' for i,(y,z) in enumerate(yz[:count],1)]
        lines += [' -3',' -4 FORC']
        if force:
            lines += [f' -1 {i} 0 {275*sign*(1 if z>0 else -1)} {-275*sign*(1 if y>0 else -1)}' for i,(y,z) in enumerate(yz[:count],1)]
        lines += [' -3'];self.path.write_text('\n'.join(lines))
    def test_measured_torque(self):
        self.assertAlmostEqual(expanded_root_torque(self.path,22.)['measured_torque_nm'],-22.)
    def test_opposite_sign(self):
        self.write(sign=-1.);self.assertAlmostEqual(expanded_root_torque(self.path,-22.)['measured_torque_nm'],22.)
    def test_wrong_input_torque(self):
        with self.assertRaises(ValueError): expanded_root_torque(self.path,21.)
    def test_missing_root_node(self):
        self.write(count=3)
        with self.assertRaises(ValueError): expanded_root_torque(self.path,22.)
    def test_missing_forces(self):
        self.write(force=False)
        with self.assertRaises(ValueError): expanded_root_torque(self.path,22.)
    def test_nan_input(self):
        with self.assertRaises(ValueError): expanded_root_torque(self.path,float('nan'))
    def test_preserve_non_torsional_moments(self):
        original={'moment_about_origin_nm':[0.,-200.,3.]}
        changed=add_measured_root_torque(original,self.path,22.)
        self.assertEqual(original['moment_about_origin_nm'],[0.,-200.,3.])
        self.assertEqual(changed['moment_about_origin_nm'],[-22.,-200.,3.])
        self.assertFalse(changed['assembly_load_path_qualified'])
    def test_no_double_count(self):
        with self.assertRaises(ValueError):
            add_measured_root_torque({'moment_about_origin_nm':[1.,0.,0.]},self.path,22.)
if __name__=='__main__':unittest.main(verbosity=2)
