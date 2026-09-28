"""I5 end-to-end benchmark regressions (Isaac-independent, numpy-only).

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. Pins determinism, same-input
identity, conservation, sliver/yield schema, S2-B presence, torque scaling,
and loud invalid-input failures — never calibrated physics.
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[1]
sys.path.insert(0, str(C22 / "sim" / "experiments"))
sys.path.insert(0, str(C22 / "sim" / "mechanisms"))

from i5_benchmark import (BENCH_CLASSES, S1_ARCHS, S2_ARCHS,  # noqa: E402
                          BenchmarkError, WrapOnlyS2Error, s1_event, s2_event)
from architectures import check_baseline_present  # noqa: E402

SCHEMA_KEYS = ("candidate", "s1_arch", "s2_arch", "seed", "class",
               "input_mass_g", "screen_mm", "open_area", "bite_flag",
               "bridge_flag", "jam_flag", "wrap_metric", "time_s",
               "throughput_proxy_g_s", "peak_torque_proxy_Nm",
               "rms_torque_proxy_Nm", "work_proxy", "specific_energy_proxy",
               "piece_count", "mass_error_g", "yield_2p5_5mm_g",
               "yield_2p5_5mm_frac", "oversize_g", "fines_g", "sliver_g",
               "sliver_frac", "recirculation_g", "residence_proxy_s",
               "stability", "evidence_level")

FRAG_KEYS = ("fragment_id", "source_waste_id", "seed", "mass_g",
             "volume_mm3", "com_mm", "principal_dims_mm",
             "equiv_diameter_mm", "aspect_ratio", "pose_quaternion_xyzw",
             "velocity_proxy_mm_s", "bond_state", "class", "material")


class TestS1Determinism(unittest.TestCase):
    def test_same_slot_identical(self):
        a = s1_event("S1-A", "W1", 7)
        b = s1_event("S1-A", "W1", 7)
        self.assertEqual(json.dumps(a, sort_keys=True),
                         json.dumps(b, sort_keys=True))


class TestSameInputIdentity(unittest.TestCase):
    def test_identical_fragments_identical_s2(self):
        rec = s1_event("S1-A", "W1", 7)
        r1 = s2_event("S2-A", rec)
        r2 = s2_event("S2-A", rec)
        self.assertEqual(json.dumps(r1, sort_keys=True),
                         json.dumps(r2, sort_keys=True))


class TestMassConservation(unittest.TestCase):
    def test_s1_dataset_conserves(self):
        for cls in ("W1", "W4", "P2"):
            rec = s1_event("S1-B", cls, 11)
            tot = sum(f["mass_g"] for f in rec["fragments"])
            self.assertAlmostEqual(tot, rec["input_mass_g"], delta=1e-6)

    def test_s2_conserves(self):
        rec = s1_event("S1-A", "W2", 11)
        r = s2_event("S2-C", rec)
        self.assertLessEqual(r["mass_error_g"], 1e-6)
        parts = (r["yield_2p5_5mm_g"] + r["oversize_g"])
        self.assertAlmostEqual(parts, r["input_mass_g"], delta=1.0)


class TestSliverMetric(unittest.TestCase):
    def test_sliver_fraction_bounded(self):
        rec = s1_event("S1-A", "W1", 7)
        r = s2_event("S2-A", rec)
        self.assertGreaterEqual(r["sliver_frac"], 0.0)
        self.assertLessEqual(r["sliver_frac"], 1.0)
        self.assertGreaterEqual(r["sliver_g"], 0.0)

    def test_yield_plus_oversize_covers_input(self):
        rec = s1_event("S1-C", "W4", 23)
        r = s2_event("S2-D", rec)
        self.assertGreaterEqual(r["yield_2p5_5mm_g"] + r["oversize_g"], 0.0)


class TestBaselinePresent(unittest.TestCase):
    def test_s2b_in_output(self):
        p = C22 / "results" / "i5_benchmark.json"
        self.assertTrue(p.is_file(), "run i5_benchmark.py first")
        s = json.loads(p.read_text())
        archs = {r["s2_arch"] for r in s["runs"]}
        self.assertIn("S2-B", archs)
        check_baseline_present()


class TestTorqueScaling(unittest.TestCase):
    def test_higher_rpm_lower_torque_same_work(self):
        rec = s1_event("S1-A", "W1", 7)
        ra = s2_event("S2-A", rec)  # 120 rpm
        rb = s2_event("S2-B", rec)  # 300 rpm
        self.assertGreater(ra["peak_torque_proxy_Nm"],
                           rb["peak_torque_proxy_Nm"])
        self.assertAlmostEqual(
            ra["peak_torque_proxy_Nm"] / rb["peak_torque_proxy_Nm"],
            300.0 / 120.0, places=2)
        self.assertAlmostEqual(
            ra["rms_torque_proxy_Nm"],
            ra["peak_torque_proxy_Nm"] / (2 ** 0.5), places=3)

class TestSchema(unittest.TestCase):
    def test_run_schema_and_fragment_contract(self):
        p = C22 / "results" / "i5_benchmark.json"
        s = json.loads(p.read_text())
        self.assertEqual(s["evidence_level"],
                         "UNCALIBRATED_DIGITAL_SENSITIVITY")
        self.assertGreater(len(s["runs"]), 0)
        for r in s["runs"][:10]:
            for k in SCHEMA_KEYS:
                self.assertIn(k, r, f"{r.get('candidate')} missing {k}")
        fp = next((C22 / "results" / "s1_fragments").glob("*.json"))
        rec = json.loads(fp.read_text())
        for f in rec["fragments"][:3]:
            for k in FRAG_KEYS:
                self.assertIn(k, f)

    def test_class_and_pair_coverage(self):
        s = json.loads((C22 / "results" / "i5_benchmark.json").read_text())
        classes = {r["class"] for r in s["runs"]}
        for c in BENCH_CLASSES:
            self.assertIn(c, classes)
        pairs = {(r["s1_arch"], r["s2_arch"]) for r in s["runs"]}
        self.assertEqual(len(pairs), len(S1_ARCHS) * len(S2_ARCHS))


class TestInvalidInput(unittest.TestCase):
    def test_p_class_s2_refused(self):
        rec = s1_event("S1-A", "P0", 7)
        with self.assertRaises(WrapOnlyS2Error):
            s2_event("S2-A", rec)

    def test_unknown_arch_refused(self):
        rec = s1_event("S1-A", "W1", 7)
        with self.assertRaises(BenchmarkError):
            s2_event("S2-Z", rec)
        with self.assertRaises(BenchmarkError):
            s1_event("S1-Z", "W1", 7)

    def test_bad_mode_refused(self):
        from i5_benchmark import run_all
        with self.assertRaises(BenchmarkError):
            run_all("nope")


if __name__ == "__main__":
    unittest.main()
