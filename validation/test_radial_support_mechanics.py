"""Independent statics, circle geometry and thermal seating regression checks."""
import math,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from analysis.radial_support_v08.mechanics import (
    reactions,capture_lift,axis_at,concave_hertz,seated_thermal_shift)


class RadialSupportTests(unittest.TestCase):
    def test_end_supported_uniform_load(self):
        value=reactions(280,0,280,20,0)
        self.assertAlmostEqual(value['rear_n'],10)
        self.assertAlmostEqual(value['front_n'],10)

    def test_tip_load_at_front_support(self):
        value=reactions(280,0,280,0,25)
        self.assertAlmostEqual(value['rear_n'],0)
        self.assertAlmostEqual(value['front_n'],25)

    def test_current_overhang_has_negative_reaction(self):
        value=reactions(280,16,110,15,25)
        self.assertLess(value['rear_n'],0)
        self.assertAlmostEqual(value['force_residual_n'],0)
        self.assertAlmostEqual(value['moment_residual_nmm'],0)

    def test_longer_span_removes_nominal_uplift(self):
        value=reactions(280,16,246,15,25)
        self.assertGreater(value['rear_n'],0)
        self.assertGreater(value['front_n'],0)

    def test_excess_tip_load_can_still_lift_rear(self):
        self.assertLess(reactions(280,16,246,15,100)['rear_n'],0)

    def test_nonfinite_and_reversed_inputs_rejected(self):
        for inputs in ((280,110,16,15,25),(280,16,300,15,25),
                       (280,16,110,15,float('nan')),(True,0,1,1,1)):
            with self.assertRaises(ValueError): reactions(*inputs)

    def test_capture_matches_circle_intersection(self):
        lift=capture_lift(17.125,17,16)
        half=math.sqrt(17.125**2-16**2)
        self.assertAlmostEqual(half**2+(16-lift)**2,17**2)
        self.assertTrue(.133 < lift < .135)

    def test_open_or_inverted_capture_rejected(self):
        for args in ((17.125,6,16),(17.125,17,18),(17,17.125,16)):
            with self.assertRaises(ValueError): capture_lift(*args)

    def test_axis_linear_and_constant(self):
        self.assertAlmostEqual(axis_at(200,16,246,-.125,-.125),-.125)
        self.assertAlmostEqual(axis_at(110,16,110,.13,-.3),-.3)
        self.assertLess(axis_at(280,16,110,.13,-.3),-1)

    def test_cold_state_has_no_thermal_shift(self):
        self.assertEqual(seated_thermal_shift(42,17.125,17,20,20,12e-6,17e-6),0)

    def test_support_expands_from_foot_not_only_bore(self):
        shift=seated_thermal_shift(42,17.125,17,200,20,12e-6,17e-6)
        self.assertAlmostEqual(shift,(42-17.125)*12e-6*180)

    def test_hertz_force_integral_and_scaling(self):
        low=concave_hertz(25,8,17,17.125);high=concave_hertz(100,8,17,17.125)
        self.assertAlmostEqual(high['half_width_mm']/low['half_width_mm'],2)
        self.assertAlmostEqual(high['peak_pressure_mpa']/low['peak_pressure_mpa'],2)
        integrated=math.pi/2*high['peak_pressure_mpa']*high['half_width_mm']*8
        self.assertAlmostEqual(integrated,100)

    def test_hertz_invalid_curvature_or_tension_rejected(self):
        for args in ((-25,8,17,17.125),(25,8,17,17),(25,0,17,17.125)):
            with self.assertRaises(ValueError): concave_hertz(*args)


if __name__=='__main__': unittest.main()
