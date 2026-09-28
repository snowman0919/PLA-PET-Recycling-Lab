"""I3 fracture regressions: determinism, conservation, orderings, gaps.

Evidence: UNCALIBRATED_FRACTURE. Tests pin nominal-ordering behavior and
explicit-gap failure modes — never calibrated physics.
"""
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[1]
sys.path.insert(0, str(C22 / "sim" / "generators"))
sys.path.insert(0, str(C22 / "sim" / "fracture"))
sys.path.insert(0, str(C22 / "sim" / "experiments"))

from bonds import lattice_graph, strengths_for_class  # noqa: E402
from bond_manager import (BondManager, FractureInputError, NonphysicalError,  # noqa: E402
                          graph_from_meta)
from waste_gen import generate  # noqa: E402
from i3_coupon import (OrderingError, WrapOnlyError, check_ordering,  # noqa: E402
                       load_dir_for, run_combo)


def fixed_lattice(cls: str):
    return lattice_graph(6, 5, 4, 60.0, 50.0, 20.0, 50.0,
                         strengths_for_class(cls))


class TestDeterminism(unittest.TestCase):
    def test_same_seed_identical_event(self):
        g1, g2 = fixed_lattice("W2"), fixed_lattice("W2")
        r1 = BondManager(g1, 7, 0.5).run_event((1, 0, 0))
        r2 = BondManager(g2, 7, 0.5).run_event((1, 0, 0))
        self.assertEqual(r1.peak_load_proxy, r2.peak_load_proxy)
        self.assertEqual(r1.failed_bond_indices, r2.failed_bond_indices)
        self.assertEqual([f.cells for f in r1.fragments],
                         [f.cells for f in r2.fragments])


class TestMassConservation(unittest.TestCase):
    def test_fragments_partition_mass(self):
        for cls in ("W1", "W2", "W3", "W4"):
            m = generate(cls, 7)
            bm = BondManager(graph_from_meta(m), 7, m["solid_fraction"])
            r = bm.run_event((1, 0, 0))
            self.assertLessEqual(r.mass_error_g, 1e-6, cls)
            cell_ids = sorted(c for f in r.fragments for c in f.cells)
            self.assertEqual(cell_ids, list(range(len(bm.graph.cells))))


class TestW1ZFirst(unittest.TestCase):
    def test_w1_z_load_fails_inter_layer_first(self):
        r = BondManager(fixed_lattice("W1"), 7, 0.5).run_event((0, 0, 1))
        self.assertEqual(r.first_failure_kind, "inter_layer_z")


class TestW4Isotropy(unittest.TestCase):
    def test_w4_z_x_ratio_near_one_w1_weak(self):
        rw1x = BondManager(fixed_lattice("W1"), 7, 0.5).run_event((1, 0, 0))
        rw1z = BondManager(fixed_lattice("W1"), 7, 0.5).run_event((0, 0, 1))
        rw4x = BondManager(fixed_lattice("W4"), 7, 0.5).run_event((1, 0, 0))
        rw4z = BondManager(fixed_lattice("W4"), 7, 0.5).run_event((0, 0, 1))
        self.assertAlmostEqual(rw4z.peak_load_proxy / rw4x.peak_load_proxy,
                               0.95, places=2)
        self.assertAlmostEqual(rw1z.peak_load_proxy / rw1x.peak_load_proxy,
                               0.25, places=2)
        self.assertGreater(rw4z.peak_load_proxy, rw1z.peak_load_proxy)


class TestOrientationDependence(unittest.TestCase):
    def test_peak_varies_with_orientation(self):
        peaks = [BondManager(fixed_lattice("W1"), 7, 0.5)
                 .run_event(load_dir_for(d)).peak_load_proxy
                 for d in (0, 45, 90)]
        self.assertGreater(max(peaks) - min(peaks), 0.05 * max(peaks))


class TestWrapOnly(unittest.TestCase):
    def test_p0_p1_refused(self):
        with self.assertRaises(WrapOnlyError):
            run_combo("P0", 0)
        with self.assertRaises(WrapOnlyError):
            run_combo("P1", 45)


class TestInvalidInput(unittest.TestCase):
    def test_zero_load_dir_rejected(self):
        with self.assertRaises(FractureInputError):
            BondManager(fixed_lattice("W1"), 7, 0.5).run_event((0, 0, 0))

    def test_bad_solid_fraction_rejected(self):
        with self.assertRaises(FractureInputError):
            BondManager(fixed_lattice("W1"), 7, 0.0)

    def test_negative_seed_rejected(self):
        with self.assertRaises(FractureInputError):
            BondManager(fixed_lattice("W1"), -1, 0.5)

    def test_unknown_class_rejected(self):
        with self.assertRaises(ValueError):
            run_combo("W9", 0)


class TestSummarySchema(unittest.TestCase):
    def test_summary_files_and_fields(self):
        p = C22 / "results" / "i3_summary.json"
        self.assertTrue(p.is_file(), "run i3_coupon.py first")
        s = json.loads(p.read_text())
        self.assertEqual(s["evidence_level"], "UNCALIBRATED_FRACTURE")
        self.assertEqual(s["combos"], 12)
        runs = s["runs"]
        self.assertEqual(len(runs), 12)
        got = {(r["class"], r["orientation_deg"]) for r in runs}
        want = {(c, d) for c in ("W1", "W2", "W3", "W4")
                for d in (0, 45, 90)}
        self.assertEqual(got, want)
        for r in runs:
            for k in ("peak_proxy", "work_proxy", "bonds_failed",
                      "first_failure_kind", "fragments", "mass_error_g",
                      "stability"):
                self.assertIn(k, r)
            self.assertTrue(math.isfinite(r["peak_proxy"]))
            self.assertTrue(math.isfinite(r["work_proxy"]))
            self.assertLessEqual(r["mass_error_g"], 1e-6)
            self.assertEqual(r["stability"], "CLEAN_SPLIT")


class TestOrderingGate(unittest.TestCase):
    def test_fixed_lattice_chain_passes(self):
        probe = check_ordering(7)
        chain = [probe["0"][c] for c in ("W1", "W2", "W3", "W4")]
        self.assertTrue(all(b >= a for a, b in zip(chain, chain[1:])))
        self.assertEqual(probe["W1_z_first"], "inter_layer_z")


if __name__ == "__main__":
    unittest.main()
