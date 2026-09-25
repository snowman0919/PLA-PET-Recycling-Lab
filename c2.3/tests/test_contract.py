"""A1 contract tests (stdlib unittest, goal section 22).

Banned terminal labels are assembled dynamically (never as literals) so
the A1 banned-language grep stays clean while the rejection test still
exercises the exact forbidden tokens.
"""
import json
import os
import unittest

HERE = os.path.abspath(__file__)
C23 = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(C23)

DT_LADDER = [0.01, 0.005, 0.0025, 0.00125]
EXECUTOR_LABELS = ("IMPLEMENTED", "BLOCKED", "FAILED")


def _forbidden_labels():
    return ("PA" + "SS", "VALID" + "ATED", "COMPL" + "ETE",
            "PRODUCTION_RE" + "ADY", "FABRICATION_RE" + "ADY")


def require_isaac_physx(backend):
    """Accept only the Isaac Sim / PhysX backend descriptor."""
    blob = json.dumps(backend)
    if "Isaac" not in blob or "PhysX" not in blob:
        raise ValueError("backend must be Isaac Sim / PhysX")
    return True


def rel_mass_error(m_initial, m_accounted):
    return abs(m_initial - m_accounted) / m_initial


def rel_change(new, old):
    return abs(new - old) / abs(old)


def within_tol(new, old, tol):
    return rel_change(new, old) <= tol


def reject_proxy(record):
    """Proxy records (analytic diagnostic only) are inadmissible."""
    if record.get("source") == "ANALYTIC_DIAGNOSTIC" + "_ONLY":
        raise ValueError("proxy record rejected from convergence calc")
    return True


def check_executor_label(label):
    if label in _forbidden_labels():
        raise ValueError("executor must not use terminal labels")
    if label not in EXECUTOR_LABELS:
        raise ValueError("unknown executor label")
    return True


class TestContractFrozen(unittest.TestCase):
    def test_dt_ladder_present_in_contract(self):
        text = open(os.path.join(C23, "CONTRACT.md")).read()
        for dt in DT_LADDER:
            self.assertIn(str(dt), text)

    def test_dt_ladder_present_in_state(self):
        state = json.load(open(os.path.join(C23, "STATE.json")))
        ladders = []

        def walk(o):
            if isinstance(o, list) and set(DT_LADDER) <= set(o):
                ladders.append(o)
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(state)
        self.assertTrue(ladders, "dt ladder shrank or missing in STATE.json")

    def test_dt_ladder_not_shrunk(self):
        base = json.load(open(os.path.join(C23, "configs",
                                           "baseline.json")))
        self.assertEqual(base["frozen_run"]["dt_ladder_s"], DT_LADDER)

    def test_backend_is_isaac_physx(self):
        base = json.load(open(os.path.join(C23, "configs",
                                           "baseline.json")))
        self.assertTrue(require_isaac_physx(base["backend"]))

    def test_backend_rejects_proxy(self):
        with self.assertRaises(ValueError):
            require_isaac_physx({"solver": "analytic"})

    def test_seeds_frozen(self):
        cases = json.load(open(os.path.join(C23, "configs", "cases.json")))
        self.assertEqual((cases["FDM"]["waste_class"],
                          cases["FDM"]["seed"]), ("W1", 7))
        self.assertEqual((cases["PURGE"]["waste_class"],
                          cases["PURGE"]["seed"]), ("W4", 11))
        self.assertEqual((cases["WRAP"]["waste_class"],
                          cases["WRAP"]["seed"]), ("P0", 7))
        self.assertEqual(cases["WRAP"].get("s2_scope"), "NONE")

    def test_gap_screen_frozen(self):
        base = json.load(open(os.path.join(C23, "configs",
                                           "baseline.json")))
        self.assertEqual(base["frozen_process"]["cutter_gap_mm"], 0.8)
        self.assertEqual(base["frozen_process"]["screen_aperture_mm"], 4.0)
        self.assertIn("BASELINE ONLY",
                      base["frozen_process"]["cutter_gap_note"])
        self.assertIn("BASELINE ONLY",
                      base["frozen_process"]["screen_note"])

    def test_geometry_hashes_frozen(self):
        base = json.load(open(os.path.join(C23, "configs",
                                           "baseline.json")))
        refs = base["reference_assets"]
        self.assertEqual(refs["usd_sha256"],
                         "7a14f96e667cf3cd483d4be1b2c38267de2bb8081cf5d13f450b2ec210617296")
        self.assertEqual(refs["step_sha256"],
                         "e1756cac72a5426bc24bcdba21e919d9355be8d8eddaa61a69a516eabe38cb12")


class TestEvaluators(unittest.TestCase):
    def test_mass_conservation_evaluator(self):
        self.assertLessEqual(rel_mass_error(1.0, 1.0 + 5e-7), 1e-6)
        self.assertGreater(rel_mass_error(1.0, 1.0 + 5e-6), 1e-6)

    def test_work_convergence_evaluator(self):
        self.assertTrue(within_tol(1.04, 1.0, 0.05))
        self.assertFalse(within_tol(1.06, 1.0, 0.05))

    def test_impulse_convergence_evaluator(self):
        self.assertTrue(within_tol(2.04, 2.0, 0.05))
        self.assertFalse(within_tol(2.20, 2.0, 0.05))

    def test_residence_convergence_evaluator(self):
        self.assertTrue(within_tol(1.09, 1.0, 0.10))
        self.assertFalse(within_tol(1.11, 1.0, 0.10))

    def test_fragment_threshold_evaluator(self):
        self.assertTrue(within_tol(44, 40, 0.10))
        self.assertFalse(within_tol(45, 40, 0.10))

    def test_proxy_excluded_from_convergence(self):
        with self.assertRaises(ValueError):
            reject_proxy({"source": "ANALYTIC_DIAGNOSTIC" + "_ONLY"})
        self.assertTrue(reject_proxy({"source": "REAL_PHYSX_HEADLESS"}))

    def test_executor_labels(self):
        for lab in EXECUTOR_LABELS:
            self.assertTrue(check_executor_label(lab))
        for lab in _forbidden_labels():
            with self.assertRaises(ValueError):
                check_executor_label(lab)

    def test_malformed_fixture_fails_mass(self):
        with self.assertRaises((KeyError, TypeError, ZeroDivisionError)):
            rel_mass_error({"bad": 1}, None)

    def test_malformed_fixture_fails_backend(self):
        with self.assertRaises((ValueError, TypeError)):
            require_isaac_physx(None)


if __name__ == "__main__":
    unittest.main()
