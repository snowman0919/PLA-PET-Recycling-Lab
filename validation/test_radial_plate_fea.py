"""Checks on mesh topology and independent force/moment rejection."""
import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from analysis.radial_support_v08.plate_fea import exterior_faces, equilibrium, load_patch


class GuideFEATest(unittest.TestCase):
    def test_tetra_has_four_exterior_faces(self):
        self.assertEqual(len(exterior_faces(['1,1,2,3,4'])),4)

    def test_shared_face_not_loaded_twice(self):
        faces=exterior_faces(['1,1,2,3,4','2,1,3,2,5'])
        self.assertEqual(len(faces),6)
        self.assertNotIn((1,2,3),[tuple(sorted(f)) for f in faces])

    def test_degenerate_element_rejected(self):
        with self.assertRaises(ValueError): exterior_faces(['1,1,2,2,4'])

    def test_nonmanifold_rejected(self):
        with self.assertRaises(ValueError):
            exterior_faces(['1,1,2,3,4','2,1,3,2,5','3,1,2,3,6'])

    def test_zero_resultant_is_balanced(self):
        a={'force_n':[0,0,-75],'moment_nm':[-9.675,24,0]}
        r={'force_n':[0,0,75],'moment_about_origin_nm':[9.675,-24,0]}
        self.assertTrue(equilibrium(a,r)['passed'])


if __name__ == '__main__':
    unittest.main()
