"""A4 verifier tests (>=8): tamper detection, recompute checks.

Forbidden terminal labels are assembled dynamically so the
banned-language grep stays clean. Uses tmp copies of c2.3/ fixtures,
never mutates the real evidence.
"""
import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.abspath(__file__)
C23T = os.path.dirname(HERE)
C23 = os.path.dirname(C23T)
sys.path.insert(0, os.path.join(C23, "verify"))
sys.path.insert(0, os.path.join(C23, "analysis"))

import convergence as CONV
import verify_contract as VC


def _copy_tree(dst_parent):
    dst = os.path.join(dst_parent, "c23")
    shutil.copytree(C23, dst, ignore=shutil.ignore_patterns("__pycache__"))
    for case in ("FDM", "PURGE", "WRAP"):
        for dt in ("0.01", "0.005", "0.0025", "0.00125"):
            d = os.path.join(dst, "results", case, "dt_%s" % dt)
            assert os.path.isdir(d), d
    return dst


class TestVerifier(unittest.TestCase):
    def test_clean_tree_is_consistent(self):
        problems = VC.verify(C23)
        self.assertEqual(problems, [])

    def test_tampered_config_hash(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            man_p = os.path.join(dst, "results", "baseline_manifest.json")
            man = json.load(open(man_p))
            man["config_hashes"]["baseline.json"] = "0" * 64
            json.dump(man, open(man_p, "w"))
            problems = VC.verify(dst)
            self.assertTrue(any("config_hash baseline.json" in p
                                for p in problems))

    def test_tampered_backend_label(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            sp = os.path.join(dst, "results", "FDM", "dt_0.005",
                              "summary.json")
            s = json.load(open(sp))
            s["backend"] = "ANALYTIC_DIAGNOSTIC" + "_ONLY"
            json.dump(s, open(sp, "w"))
            problems = VC.verify(dst)
            self.assertTrue(any("backend tampered" in p for p in problems))

    def test_shrunk_dt_ladder(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            bp = os.path.join(dst, "configs", "baseline.json")
            b = json.load(open(bp))
            b["frozen_run"]["dt_ladder_s"] = [0.01, 0.005, 0.0025]
            json.dump(b, open(bp, "w"))
            problems = VC.verify(dst)
            self.assertTrue(any("dt ladder" in p for p in problems))

    def test_proxy_record_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            tp = os.path.join(dst, "results", "FDM", "dt_0.005",
                              "telemetry.jsonl")
            lines = open(tp).read().splitlines()
            row = json.loads(lines[0])
            row["source"] = "ANALYTIC_DIAGNOSTIC" + "_ONLY"
            lines[0] = json.dumps(row)
            open(tp, "w").write("\n".join(lines) + "\n")
            problems = VC.verify(dst)
            self.assertTrue(any("proxy record" in p for p in problems))

    def test_threshold_verdict_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            cp = os.path.join(dst, "results", "convergence_summary.json")
            conv = json.load(open(cp))
            m = conv["FDM"]["0.0025->0.00125"]["metrics"]["work"]
            m["within_tol"] = not m["within_tol"]
            json.dump(conv, open(cp, "w"))
            problems = VC.verify(dst)
            self.assertTrue(any("verdict mismatch" in p or "epsilon" in p
                                for p in problems))

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            os.remove(os.path.join(dst, "results", "PURGE", "dt_0.01",
                                   "events.jsonl"))
            problems = VC.verify(dst)
            self.assertTrue(any("missing file" in p for p in problems))

    def test_mass_recompute(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            ap = os.path.join(dst, "results", "aggregate_summary.json")
            agg = json.load(open(ap))
            agg["FDM"]["0.005"]["mass"]["rel_error"] = 0.5
            json.dump(agg, open(ap, "w"))
            problems = VC.verify(dst)
            self.assertTrue(any("mass recompute" in p for p in problems))

    def test_epsilon_recompute(self):
        agg = json.load(open(os.path.join(C23, "results",
                                          "aggregate_summary.json")))
        expect = CONV.evaluate(agg["WRAP"]["0.0025"], agg["WRAP"]["0.00125"],
                               c23dir=C23)
        conv = json.load(open(os.path.join(
            C23, "results", "convergence_summary.json")))
        got = conv["WRAP"]["0.0025->0.00125"]
        self.assertAlmostEqual(expect["metrics"]["work"]["epsilon"],
                               got["metrics"]["work"]["epsilon"], places=9)
        self.assertEqual(expect["converged"], got["converged"])
        self.assertFalse(got["converged"])

    def test_banned_scan_distinction(self):
        with tempfile.TemporaryDirectory() as td:
            dst = _copy_tree(td)
            hp = os.path.join(dst, "NEXT.md")
            with open(hp, "a") as fh:
                fh.write("\nstatus: " + "PA" + "SS executor judgment\n")
            hits = VC.scan_banned(dst)
            self.assertTrue(any("NEXT.md" in h for h in hits))
        hits = VC.scan_banned(C23)
        run_ok_hits = [h for h in hits if "RUN_OK" in h]
        self.assertEqual(run_ok_hits, [])


if __name__ == "__main__":
    unittest.main()
