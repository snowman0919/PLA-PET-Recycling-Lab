"""I6 surrogate + Pareto + robustness regressions (stdlib+numpy+unittest).

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. Pins grouped-split hygiene,
Pareto dominance logic, robustness bounds, schema, invalid inputs, and
determinism — never calibrated physics.
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[1]
sys.path.insert(0, str(C22 / "sim" / "optimization"))

from i6_surrogate import (TEST_SEEDS, TRAIN_SEEDS, VAL_SEEDS, SurrogateInputError,  # noqa: E402
                          bo_search, dominates, features, pareto_front,
                          predict_ensemble, predict_mean, robustness_grid)


class TestGroupedSplit(unittest.TestCase):
    def test_seed_sets_disjoint_and_covering(self):
        tr, va, te = set(TRAIN_SEEDS), set(VAL_SEEDS), set(TEST_SEEDS)
        self.assertEqual(tr, {7, 11, 23})
        self.assertEqual(va, {37})
        self.assertEqual(te, {51})
        self.assertFalse(tr & va or tr & te or va & te)


class TestParetoDominance(unittest.TestCase):
    def _obj(self, **kw):
        base = {"yield_frac": 0.0, "throughput": 10.0, "robustness": 0.9,
                "peak_torque": 0.005, "specific_energy": 0.5,
                "jam_prob": 0.0, "wrap_metric": 0.0, "sliver_frac": 0.8,
                "oversize_frac": 1.0}
        base.update(kw)
        return base

    def test_strictly_better_dominates(self):
        a = self._obj(yield_frac=0.1)
        b = self._obj()
        self.assertTrue(dominates(a, b))
        self.assertFalse(dominates(b, a))

    def test_tradeoff_nondominated(self):
        a = self._obj(yield_frac=0.1, peak_torque=0.009)
        b = self._obj()
        self.assertFalse(dominates(a, b))
        self.assertFalse(dominates(b, a))

    def test_front_filters_dominated(self):
        objs = [self._obj(yield_frac=0.0), self._obj(yield_frac=0.1),
                self._obj(yield_frac=0.05, peak_torque=0.003)]
        front = pareto_front(objs)
        self.assertEqual(len(front), 2)


class TestRobustnessBounds(unittest.TestCase):
    def test_grid_samples_and_sensitivity_shape(self):
        p = C22 / "results" / "pareto_candidates.json"
        par = json.loads(p.read_text())
        for name, rob in par["robustness"].items():
            self.assertGreaterEqual(rob["samples"], 50,
                                    f"{name} below 50 samples")
            self.assertLessEqual(rob["samples"], 100,
                                 f"{name} above 100 samples")
            for k, sv in rob["sensitivity"].items():
                self.assertGreaterEqual(sv["range"], 0.0)
                self.assertGreaterEqual(sv["rel_range"], 0.0)
            self.assertIn("manufacturing_note", rob)
            self.assertIn("SIMULATION RANGE ONLY",
                          rob["manufacturing_note"])


class TestSchema(unittest.TestCase):
    def test_surrogate_schema(self):
        s = json.loads((C22 / "results" / "i6_surrogate.json").read_text())
        self.assertEqual(s["evidence_level"],
                         "UNCALIBRATED_DIGITAL_SENSITIVITY")
        for o, m in s["metrics_test"].items():
            self.assertIn("R2", m)
            self.assertIn("MAE", m)
        self.assertEqual(len(s["bo_top12"]), 12)

    def test_pareto_schema_and_picks(self):
        par = json.loads(
            (C22 / "results" / "pareto_candidates.json").read_text())
        self.assertGreaterEqual(par["front_size"], 1)
        for name in ("best_nominal", "robust", "low_energy", "purge",
                     "typical_fdm"):
            self.assertIn(name, par["picks"])
            for k in ("s1", "s2", "class"):
                self.assertIn(k, par["picks"][name])

    def test_no_validated_language(self):
        for f in ("i6_surrogate.json", "pareto_candidates.json",
                  "i5_benchmark.json", "i4_screen.json", "i3_summary.json"):
            t = (C22 / "results" / f).read_text()
            self.assertNotIn("VALIDATED", t, f)


class TestInvalidInput(unittest.TestCase):
    def test_bad_gap_screen_arch_rejected(self):
        with self.assertRaises(SurrogateInputError):
            features("S1-A", "S2-A", "W1", 7, 2.5, 4.0)
        with self.assertRaises(SurrogateInputError):
            features("S1-A", "S2-A", "W1", 7, 0.8, 9.0)
        with self.assertRaises(SurrogateInputError):
            features("S9-Z", "S2-A", "W1", 7, 0.8, 4.0)


class TestDeterminism(unittest.TestCase):
    def test_ensemble_and_bo_deterministic(self):
        f = features("S1-A", "S2-A", "W1", 7, 0.8, 4.0)
        e1, e2 = predict_ensemble(f), predict_ensemble(f)
        self.assertEqual(json.dumps(e1, sort_keys=True),
                         json.dumps(e2, sort_keys=True))
        b1, b2 = bo_search(8), bo_search(8)
        self.assertEqual(json.dumps(b1, sort_keys=True),
                         json.dumps(b2, sort_keys=True))
        m1, m2 = predict_mean(f), predict_mean(f)
        self.assertEqual(m1, m2)


if __name__ == "__main__":
    unittest.main()
