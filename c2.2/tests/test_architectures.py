"""I4 architecture + screening regressions (Isaac-independent).

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. Pins direction law, baseline
presence, envelope/hopper gates, sampler determinism, contract equality,
and loud invalid-mechanism failures — never calibrated physics.
"""
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[1]
sys.path.insert(0, str(C22 / "sim" / "mechanisms"))
sys.path.insert(0, str(C22 / "sim" / "experiments"))

from architectures import (ARCHITECTURES, InvalidMechanism,  # noqa: E402
                           check_baseline_present, check_clearance,
                           check_direction, check_envelope,
                           comparison_contract, get, s2a_direction_phi,
                           screen_open_area, validate_all)
from i4_screen import sample_candidates, screen_candidate  # noqa: E402
from i4_screen import validate_mechanisms


class TestS2ADirection(unittest.TestCase):
    def test_phi_minus_theta_over_q(self):
        for th in (0.0, 0.5, 1.0, math.pi, 2 * math.pi):
            self.assertAlmostEqual(s2a_direction_phi(th, 8), -th / 8)
        self.assertEqual(ARCHITECTURES["S2-A"].direction_sign, -1)
        check_direction(ARCHITECTURES["S2-A"])


class TestBaselinePresent(unittest.TestCase):
    def test_s2b_baseline_exists(self):
        self.assertIn("S2-B", ARCHITECTURES)
        self.assertTrue(ARCHITECTURES["S2-B"].baseline)
        check_baseline_present()
        validate_all()


class TestEnvelope(unittest.TestCase):
    def test_all_fit_body_and_bay(self):
        for a in ARCHITECTURES.values():
            check_envelope(a)  # raises on violation

    def test_oversize_rejected(self):
        bad = get("S2-A")
        import dataclasses
        big = dataclasses.replace(bad, footprint_mm=(999.0, 10.0, 10.0))
        with self.assertRaises(InvalidMechanism):
            check_envelope(big)


class TestHopperGate(unittest.TestCase):
    def test_oversize_dims_fail_gate(self):
        c = {"cand_id": "T", "arch": "S2-A", "class": "W1",
             "gap_mm": 0.8, "screen_mm": 4.0,
             "dims_mm": {"dx": 999.0, "dy": 10.0, "dz": 10.0}, "extra": {}}
        self.assertFalse(screen_candidate(c)["gates"]["hopper"])

    def test_nominal_passes(self):
        c = {"cand_id": "T", "arch": "S2-B", "class": "W2",
             "gap_mm": 0.8, "screen_mm": 4.0,
             "dims_mm": {"dx": 60.0, "dy": 50.0, "dz": 20.0}, "extra": {}}
        s = screen_candidate(c)
        self.assertTrue(s["gates"]["hopper"])
        self.assertTrue(s["survived"])


class TestSamplerDeterminism(unittest.TestCase):
    def test_same_seed_identical(self):
        a = sample_candidates(200, 7)
        b = sample_candidates(200, 7)
        self.assertEqual(json.dumps(a, sort_keys=True),
                         json.dumps(b, sort_keys=True))

    def test_arch_ids_cover_all_seven(self):
        cands = sample_candidates(500, 7)
        self.assertEqual({c["arch"] for c in cands}, set(ARCHITECTURES))


class TestContractEquality(unittest.TestCase):
    def test_contract_shared_slots(self):
        c = comparison_contract()
        self.assertEqual(c["seed_set"], [7, 11, 23])
        self.assertIn("S2-B", set(ARCHITECTURES))
        for a in ARCHITECTURES.values():
            self.assertIn("gap_mm", a.ranges)


class TestInvalidGap(unittest.TestCase):
    def test_out_of_range_gap_fails_gate(self):
        c = {"cand_id": "T", "arch": "S1-A", "class": "W1",
             "gap_mm": 2.5, "screen_mm": 4.0,
             "dims_mm": {"dx": 60.0, "dy": 50.0, "dz": 20.0}, "extra": {}}
        self.assertFalse(screen_candidate(c)["gates"]["ranges"])

    def test_zero_clearance_rejected(self):
        import dataclasses
        bad = dataclasses.replace(get("S1-A"), clearance_mm=0.0)
        with self.assertRaises(InvalidMechanism):
            check_clearance(bad)

    def test_unknown_arch_rejected(self):
        with self.assertRaises(InvalidMechanism):
            get("S9-Z")


class TestScreenArea(unittest.TestCase):
    def test_open_area_sane(self):
        oa = screen_open_area(4.0)
        self.assertGreater(oa, 0.01)
        self.assertLess(oa, 0.30)

    def test_bad_screen_rejected(self):
        with self.assertRaises(InvalidMechanism):
            screen_open_area(0.0)


class TestScreenOutput(unittest.TestCase):
    def test_results_file_schema(self):
        p = C22 / "results" / "i4_screen.json"
        self.assertTrue(p.is_file(), "run i4_screen.py first")
        r = json.loads(p.read_text())
        self.assertEqual(r["evidence_level"],
                         "UNCALIBRATED_DIGITAL_SENSITIVITY")
        self.assertTrue(200 <= r["candidates"] <= 500)
        self.assertEqual(len(r["screened"]), r["candidates"])
        self.assertEqual(len(r["survivor_ids"]), r["survivors"])
        for s in r["screened"][:5]:
            for k in ("gates", "survived", "open_area", "flags"):
                self.assertIn(k, s)


if __name__ == "__main__":
    unittest.main()
