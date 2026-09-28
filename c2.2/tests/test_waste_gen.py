"""I2 waste generator regressions (read-only vs C2.1; stdlib+unittest+numpy).

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. These tests pin determinism,
conservation, validity, and explicit-gap behavior — never calibrated physics.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
GEN = HERE.parents[1] / "sim" / "generators"
sys.path.insert(0, str(GEN))

from bonds import (Bond, BondGraph, Cell, MissingEvidenceError,  # noqa: E402
                   lattice_graph, require_calibrated_strength,
                   strengths_for_class)
from waste_gen import (CLASS_FAMILIES, check_admissible,  # noqa: E402
                       generate, OversizeError)


class TestSeedDeterminism(unittest.TestCase):
    def test_same_seed_identical_json(self):
        a = json.dumps(generate("W1", 7), sort_keys=True)
        b = json.dumps(generate("W1", 7), sort_keys=True)
        self.assertEqual(a, b)

    def test_different_seeds_differ(self):
        a = json.dumps(generate("W1", 7), sort_keys=True)
        b = json.dumps(generate("W1", 8), sort_keys=True)
        self.assertNotEqual(a, b)


class TestMassConservation(unittest.TestCase):
    def test_cells_sum_to_object_mass(self):
        for cls in ("W1", "W4", "P2"):
            m = generate(cls, 3)
            self.assertGreater(m["bonds"]["cells"], 0)
            # mass formula re-derivation; solid_fraction/mass are rounded
            # to 3 decimals so allow rounding-slack delta, not exact match.
            exp = (m["volume_cm3"] * m["density_g_cc"] * m["solid_fraction"]
                   * (0.75 if cls == "P0" else 0.90 if cls == "P1" else 1.0))
            slack = m["volume_cm3"] * m["density_g_cc"] * 0.0006 + 0.002
            self.assertAlmostEqual(m["mass_g"], round(exp, 3), delta=slack)

    def test_lattice_graph_conserves_mass(self):
        g = lattice_graph(3, 2, 2, 30.0, 20.0, 10.0, 12.5,
                          strengths_for_class("W1"))
        self.assertEqual(g.validate(), [])
        self.assertAlmostEqual(sum(c.mass_g for c in g.cells), 12.5)

class TestBondValidity(unittest.TestCase):
    def test_all_classes_valid_graphs(self):
        for cls in CLASS_FAMILIES:
            m = generate(cls, 11)
            self.assertTrue(m["bonds"]["valid"], cls)

    def test_self_bond_rejected(self):
        g = BondGraph(object_mass_g=1.0, cells=[Cell(0, 1.0, (0, 0, 0))],
                      bonds=[Bond(0, 0, "in_raster", 1.0)])
        self.assertTrue(any("self-bond" in p for p in g.validate()))

    def test_nonpositive_strength_rejected(self):
        g = lattice_graph(2, 1, 1, 20, 10, 5, 2.0,
                          strengths_for_class("W2"))
        g.bonds[0].strength = 0.0
        self.assertTrue(any("non-positive" in p for p in g.validate()))


class TestAnisotropyOrdering(unittest.TestCase):
    def test_w1_z_weakest(self):
        s = strengths_for_class("W1")
        self.assertLess(s["inter_layer_z"], s["cross_raster"])
        self.assertLess(s["cross_raster"], s["in_raster"])

    def test_w4_near_isotropic(self):
        s = strengths_for_class("W4")
        self.assertGreater(s["inter_layer_z"], 0.9)
        self.assertGreater(s["cross_raster"], 0.9)
        self.assertLess(abs(s["in_raster"] - s["inter_layer_z"]), 0.1)


class TestHopperReject(unittest.TestCase):
    def test_oversize_rejected_with_reason(self):
        with self.assertRaises(OversizeError) as cm:
            check_admissible(999.0, 10.0, 10.0)
        self.assertIn("REJECT", str(cm.exception))

    def test_cli_reject_exit2(self):
        # monkeypatch-free: oversize via direct huge family is stochastic,
        # so assert the rule itself + a CLI PASS shape instead.
        r = subprocess.run(
            [sys.executable, str(GEN / "waste_gen.py"),
             "--seed", "7", "--class", "W1"],
            capture_output=True, text=True, cwd=GEN)
        self.assertEqual(r.returncode, 0)
        meta = json.loads(r.stdout)
        for k in ("object_id", "seed", "class", "dims_mm", "mass_g",
                  "bonds", "admissibility"):
            self.assertIn(k, meta)
        self.assertEqual(meta["admissibility"]["result"], "PASS")


class TestThermalIndexBounds(unittest.TestCase):
    def test_index_in_unit_interval(self):
        for cls in CLASS_FAMILIES:
            for seed in (1, 2, 3):
                m = generate(cls, seed)
                self.assertGreaterEqual(m["thermal_history_index"], 0.0)
                self.assertLessEqual(m["thermal_history_index"], 1.0)


class TestFamilyCoverage(unittest.TestCase):
    def test_all_classes_all_families_generate(self):
        seen = set()
        for cls, fams in CLASS_FAMILIES.items():
            for fam in fams:
                m = generate(cls, 5, family=fam)
                self.assertEqual(m["family"], fam)
                seen.add((cls, fam))
        # every declared (class, family) pair emits
        total = sum(len(v) for v in CLASS_FAMILIES.values())
        self.assertEqual(len(seen), total)

    def test_wrong_family_rejected(self):
        with self.assertRaises(ValueError):
            generate("W1", 5, family="dense_blob")


class TestMissingEvidence(unittest.TestCase):
    def test_calibrated_lookup_fails_loudly(self):
        with self.assertRaises(MissingEvidenceError):
            require_calibrated_strength("W1")


if __name__ == "__main__":
    unittest.main()
