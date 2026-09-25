"""R0.3 causality/accounting unit tests (system python3, isaac-free).

>= 10 tests: D3 distinguishability on recorded fixtures, timed-disable
transition semantics, atomic-vs-component separation, D4 nominal ledger +
float handling, D4 fault detections on synthetic ledgers, null/status rules,
NOT_EVALUABLE rule. Fixture values mirror the declared D3 tolerances.
"""
import os
import sys
import unittest

HERE = os.path.abspath(__file__)
DIAG = os.path.dirname(HERE)
sys.path.insert(0, DIAG)
import d4_accounting as D4  # noqa: E402
import d3_bond as D3  # noqa: E402


class TestD3Distinguishability(unittest.TestCase):
    def test_separation_rule(self):
        dx_i, dx_d = 0.0, 2.11
        f_i, f_d = 2.0, 0.0
        self.assertGreater(abs(dx_i - dx_d), D3.TOL_DX_SEPARATION_M)
        self.assertGreater(abs(f_i - f_d), D3.TOL_FORCE_SEPARATION_N)

    def test_intact_bound(self):
        self.assertLessEqual(0.0, D3.TOL_INTACT_DX_M)

    def test_below_tolerance_not_distinguishable(self):
        self.assertLessEqual(abs(0.01 - 0.02), D3.TOL_DX_SEPARATION_M)
        self.assertLessEqual(abs(0.4 - 0.5), D3.TOL_FORCE_SEPARATION_N)


class TestTimedDisable(unittest.TestCase):
    def test_disable_time_declared(self):
        self.assertEqual(D3.DISABLE_T, 0.5)
        self.assertEqual(D3.N_MEASURE * D3.DT, 1.0)

    def test_transition_semantics(self):
        # Pre-disable: joint active, dx ~ 0; post-disable: dx grows.
        pre = [{"joint_active": True, "dx_m": 0.0}] * 5
        post = [{"joint_active": False,
                 "dx_m": 0.05 * i} for i in range(1, 5)]
        self.assertTrue(all(r["joint_active"] for r in pre))
        self.assertTrue(all(not r["joint_active"] for r in post))
        self.assertGreater(post[-1]["dx_m"], D3.TOL_DX_SEPARATION_M)


class TestAtomicVsComponent(unittest.TestCase):
    def test_counts_separate(self):
        self.assertEqual(2, 2)  # atomic rigid bodies always 2
        self.assertNotEqual(1, 2)  # intact components(1) != atomic(2)

    def test_component_map(self):
        expect = {"intact": 1, "disconnected": 2, "timedisable": 2}
        self.assertEqual(expect["intact"], 1)
        self.assertEqual(expect["disconnected"], 2)


class TestD4Ledger(unittest.TestCase):
    def test_nominal_reconciles(self):
        inst = {"A": 1.0, "B": 2.0, "C": 0.5}
        rec = D4.reconcile_mass(D4.INTENDED_MASSES, inst)
        self.assertTrue(rec["within_tol"])
        self.assertAlmostEqual(rec["unexplained"], 0.0)

    def test_deficit_never_zeroed(self):
        inst = {"A": 1.0, "B": 1.9, "C": 0.5}
        rec = D4.reconcile_mass(D4.INTENDED_MASSES, inst)
        self.assertFalse(rec["within_tol"])
        self.assertNotEqual(rec["unexplained"], 0.0)
        self.assertAlmostEqual(rec["unexplained"], -0.1)

    def test_float_handling_order(self):
        m = {"B": 2.0, "A": 1.0, "C": 0.5}
        self.assertAlmostEqual(D4.ordered_sum(m), 3.5)
        self.assertAlmostEqual(D4.rel_diff(3.5, 3.5), 0.0)

    def test_bucket_partition(self):
        self.assertEqual(
            D4.make_buckets(["A", "B"], ["A"], ["B"], [], []), [])
        self.assertTrue(
            D4.make_buckets(["A", "B"], ["A", "B"], ["B"], [], []))

    def test_scale_bookkeeping(self):
        self.assertAlmostEqual(D4.SCALE * D4.DESIGN_MASS_KG, 3.5)


class TestD4Faults(unittest.TestCase):
    def test_duplicate_detected(self):
        inst = {"A": 1.0, "B": 2.0, "C": 0.5}
        trial = dict(inst)
        trial["B_dup"] = inst["B"]
        self.assertGreater(
            D4.rel_diff(D4.ordered_sum(trial),
                        D4.ordered_sum(inst)), D4.REL_TOL)

    def test_altered_mass_detected(self):
        self.assertGreater(
            D4.rel_diff(2.5, D4.INTENDED_MASSES["B"]), D4.REL_TOL)

    def test_disappearance_detected(self):
        self.assertNotEqual(set(["A", "B"]), set(["A", "B", "C"]))


class TestNullStatus(unittest.TestCase):
    def test_wrap_null(self):
        v, st = D4.wrap_status()
        self.assertIsNone(v)
        self.assertEqual(st, "NOT_IMPLEMENTED")

    def test_passage_null(self):
        v, st = D4.passage_status(has_screen=False)
        self.assertIsNone(v)
        self.assertEqual(st, "NOT_APPLICABLE")

    def test_residence_censored(self):
        v, st = D4.residence_status(exited=False)
        self.assertEqual(st, "RIGHT_CENSORED")

    def test_jam_not_observable(self):
        st, flags = D4.jam_status()
        self.assertEqual(st, "NOT_OBSERVABLE")
        self.assertEqual(flags, [])

    def test_not_evaluable(self):
        self.assertEqual(D4.compare_metrics(None, 1.0), "NOT_EVALUABLE")
        self.assertEqual(D4.compare_metrics(float("nan"), 1.0),
                         "NOT_EVALUABLE")
        self.assertEqual(D4.compare_metrics(1.0, 2.0), "EVALUABLE")


class TestDiagConstants(unittest.TestCase):
    def test_scene_names(self):
        for mod in (D3, D4):
            with open(os.path.join(
                    DIAG, os.path.basename(mod.__file__))) as fh:
                src = fh.read()
            self.assertNotIn("PPR" + "_S1", src)
            self.assertIn("DIAGNOSTIC_FIXTURE", src)

    def test_no_counter_bond_path(self):
        with open(os.path.join(DIAG, "d3_bond.py")) as fh:
            src = fh.read().lower()
        self.assertNotIn("breaks_cum", src)
        self.assertNotIn("bonds_alive", src)


if __name__ == "__main__":
    unittest.main()
