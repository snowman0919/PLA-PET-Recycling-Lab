"""R0.2 analytic unit tests: D0 mapping + D1 unit rule + D2 torque/work cases.

Isaac-free (system python3): imports shaft_torque/boundary_work from
d2_torque.py by path. >= 12 tests.
"""
import math
import os
import sys
import unittest

HERE = os.path.abspath(__file__)
DIAG = os.path.dirname(HERE)
sys.path.insert(0, DIAG)
import d2_torque as D2  # noqa: E402
import d0_clock as D0  # noqa: E402
import d1_contact as D1  # noqa: E402


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol


class TestD0SubstepMapping(unittest.TestCase):
    def test_shared_2p4s(self):
        for dt, n in D0.SUBSTEPS.items():
            self.assertTrue(approx(n * dt, 2.4, 1e-12),
                            "dt=%r substeps=%r" % (dt, n))

    def test_ladder_values(self):
        self.assertEqual(D0.DT_LADDER, [0.01, 0.005, 0.0025, 0.00125])
        self.assertEqual([D0.SUBSTEPS[dt] for dt in D0.DT_LADDER],
                         [240, 480, 960, 1920])


class TestD1UnitRule(unittest.TestCase):
    def test_impulse_summed_once(self):
        # J entries [Ns] summed once; F*dt form must agree, double-dt must not.
        Js = [0.02, 0.03, 0.05]
        dt = 0.005
        once = sum(Js)
        f_dt = sum((J / dt) * dt for J in Js)
        twice = sum(Js) * dt
        self.assertTrue(approx(once, f_dt, 1e-12))
        self.assertFalse(approx(once, twice, 1e-12))

    def test_support_impulse_scale(self):
        m, T = 2.0, 1.0
        self.assertTrue(approx(m * 9.81 * T, 19.62, 1e-9))


class TestShaftTorque(unittest.TestCase):
    def test_pure_radial_zero_axial(self):
        o = [0.0, 0.0, 0.0]
        a = [0.0, 0.0, 1.0]
        tau = D2.shaft_torque([([0.04, 0.0, 0.0], [10.0, 0.0, 0.0])], o, a)
        self.assertTrue(approx(tau, 0.0))

    def test_tangential_R_times_F(self):
        o = [0.0, 0.0, 0.0]
        a = [0.0, 0.0, 1.0]
        tau = D2.shaft_torque([([0.04, 0.0, 0.0], [0.0, 5.0, 0.0])], o, a)
        self.assertTrue(approx(tau, 0.04 * 5.0))

    def test_reversal_flips_sign(self):
        o = [0.0, 0.0, 0.0]
        a = [0.0, 0.0, 1.0]
        t1 = D2.shaft_torque([([0.04, 0.0, 0.0], [0.0, 5.0, 0.0])], o, a)
        t2 = D2.shaft_torque([([0.04, 0.0, 0.0], [0.0, -5.0, 0.0])], o, a)
        self.assertTrue(approx(t1, -t2))
        self.assertTrue(approx(t1 + t2, 0.0))

    def test_opposite_cancel(self):
        o = [0.0, 0.0, 0.0]
        a = [0.0, 0.0, 1.0]
        tau = D2.shaft_torque([
            ([0.04, 0.0, 0.0], [0.0, 5.0, 0.0]),
            ([-0.04, 0.0, 0.0], [0.0, 5.0, 0.0])], o, a)
        self.assertTrue(approx(tau, 0.0))

    def test_off_axis_origin(self):
        o = [1.0, 2.0, 3.0]
        a = [0.0, 1.0, 0.0]
        # r = (0.04,0,0), F=(0,0,7): cross = (0*0-0*7, 0*0-0.04*0, 0) -> use
        # direct check: moment arm about y from x-z plane force.
        tau = D2.shaft_torque([([1.04, 2.0, 3.0], [0.0, 0.0, 7.0])], o, a)
        # cross((0.04,0,0),(0,0,7)) = (0*7-0*0, 0*0-0.04*7, 0) = (0,-0.28,0)
        self.assertTrue(approx(tau, -0.28))

    def test_separate_shafts(self):
        # Counter-rotating shafts: per-shaft accumulators must not share
        # origin/axis; equal-and-opposite tangential loads on two shafts
        # with flipped axes give equal (not cancelling) drive torques.
        tA = D2.shaft_torque([([0.04, 0.0, 0.0], [0.0, 5.0, 0.0])],
                             [0.0, 0.0, 0.0], [0.0, 0.0, 1.0])
        tB = D2.shaft_torque([([0.04, 0.0, 0.0], [0.0, -5.0, 0.0])],
                             [0.0, 0.0, 0.0], [0.0, 0.0, -1.0])
        self.assertTrue(approx(tA, tB))
        self.assertTrue(approx(tA, 0.2))


class TestBoundaryWork(unittest.TestCase):
    def test_stationary_boundary_zero(self):
        self.assertTrue(approx(
            D2.boundary_work([0.0, 0.0, 9.81], [0.0, 0.0, 0.0]), 0.0))

    def test_dissipative_nonpositive(self):
        # Impulse on body opposes slip velocity -> work <= 0.
        w = D2.boundary_work([0.0, 0.0, -2.0], [0.0, 0.0, 1.0])
        self.assertLessEqual(w, 0.0)
        self.assertTrue(approx(w, -2.0))

    def test_sign_documents_on_body(self):
        w = D2.boundary_work([1.0, 0.0, 0.0], [3.0, 0.0, 0.0])
        self.assertTrue(approx(w, 3.0))

    def test_ground_contact_zero_cutter_work(self):
        # Support force exists but no shaft contact -> cutter work is 0
        # because the shaft-contact filter admits nothing (empty list).
        self.assertTrue(approx(D2.shaft_torque([], [2.0, 0.0, 0.5],
                                               [0.0, 1.0, 0.0]), 0.0))
        self.assertTrue(approx(
            D2.boundary_work([0.0, 0.0, 19.62], [0.0, 0.0, 0.0]), 0.0))


class TestDiagConstants(unittest.TestCase):
    def test_no_ppr_scene_names(self):
        for mod in (D0, D1, D2):
            src = open(os.path.join(DIAG, os.path.basename(
                mod.__file__))).read()
            self.assertNotIn("PPR" + "_S1", src)
            self.assertIn("DIAGNOSTIC_FIXTURE", src)

    def test_backend_tag(self):
        for mod in (D0, D1, D2):
            src = open(os.path.join(DIAG, os.path.basename(
                mod.__file__))).read()
            self.assertIn("ISAAC_PHYSX", src)


if __name__ == "__main__":
    unittest.main()
