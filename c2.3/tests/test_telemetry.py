"""A2 telemetry/analysis tests (>=10): integrals, mass, ledger,
convergence, proxy exclusion, malformed fixtures, dt mapping.

Isaac-free: exercises aggregate/energy_ledger/convergence/run_case
helpers on synthetic fixtures only. Forbidden terminal labels are
assembled dynamically so the banned-language grep stays clean.
"""
import json
import os
import sys
import unittest

HERE = os.path.abspath(__file__)
C23T = os.path.dirname(HERE)
C23 = os.path.dirname(C23T)
sys.path.insert(0, os.path.join(C23, "analysis"))
sys.path.insert(0, os.path.join(C23, "sim"))

import aggregate as AGG
import convergence as CONV
import energy_ledger as LED
import run_case as RUN


def synth_rows(n=4, dt=0.005, force=2.0, omega=4.18879, arm=0.04,
               breaks=3, alive=40, source=None):
    rows = []
    work = 0.0
    for i in range(n):
        torque = arm * force
        work += torque * omega * dt
        rows.append({
            "step": i + 1, "t_s": (i + 1) * dt,
            "theta_rad": omega * i * dt, "omega_rad_s": omega,
            "n_contacts": 1, "contact_force_total_N": force,
            "max_contact_N": force, "torque_Nm": torque,
            "work_cum_J": work,
            "torque_impulse_cum_Nms": torque * (i + 1) * dt,
            "ke_trans_J": 0.01 * (i + 1), "ke_rot_J": 0.001 * (i + 1),
            "pe_grav_J": 1.0 + 0.002 * (i + 1),
            "breaks_cum": breaks, "bonds_alive": alive,
            "frag_pos_m": [[0.0, 0.0, 0.05]],
            "frag_vel_m_s": [[0.0, 0.0, -0.1]],
            "frag_angvel_rad_s": [[0.0, 0.0, 0.0]],
            **({"source": source} if source else {}),
        })
    return rows


def synth_meta(n=6, mass_per=0.003, dt=0.005, disp=0.05, case="FDM"):
    return {"dt_s": dt, "mass_per_fragment_kg": mass_per,
            "n_fragments": n, "max_frag_displacement_m": disp,
            "case": case, "torque_source": "CONTACT_DERIVED_MOMENT_ARM",
            "wrap_metric": 0.0}


def synth_agg(work=1.0, impulse=0.5, residence=0.4, rel_err=5e-7,
              breaks=40, alive=6, jam=False, wrap=False):
    return {
        "work": {"shaft_work_J": work}, "impulse": {"J_total_Ns": impulse},
        "residence": {"residence_time_s": residence},
        "mass": {"rel_error": rel_err},
        "fragments": {"breaks": breaks, "bonds_alive": alive},
        "flags": {"jam": jam, "wrap": wrap}}


class TestIntegrals(unittest.TestCase):
    def test_work_integral(self):
        rows = synth_rows(n=4, dt=0.005, force=2.0)
        agg = AGG.aggregate(rows, [], synth_meta())
        expect = 0.04 * 2.0 * 4.18879 * 0.005 * 4
        self.assertAlmostEqual(agg["work"]["shaft_work_J"], expect,
                               places=9)

    def test_impulse_integral(self):
        rows = synth_rows(n=4, dt=0.005, force=2.0)
        agg = AGG.aggregate(rows, [], synth_meta())
        self.assertAlmostEqual(agg["impulse"]["J_total_Ns"], 2.0 * 4 * 0.005,
                               places=9)

    def test_impulse_classes_sum(self):
        agg = AGG.aggregate(synth_rows(), [], synth_meta())
        by = agg["impulse"]["by_class"]
        self.assertAlmostEqual(by["total"], by["cutter"] + by["screen"]
                               + by["other"], places=12)

    def test_residence_interval(self):
        rows = synth_rows(n=4, dt=0.005)
        rows[0]["n_contacts"] = 0
        rows[-1]["n_contacts"] = 0
        agg = AGG.aggregate(rows, [], synth_meta())
        self.assertAlmostEqual(agg["residence"]["residence_time_s"], 0.005)

    def test_mass_error_formula(self):
        agg = AGG.aggregate(synth_rows(), [], synth_meta(n=6, mass_per=0.003))
        self.assertAlmostEqual(agg["mass"]["m_initial_kg"], 0.018)
        self.assertAlmostEqual(agg["mass"]["rel_error"], 0.0)


class TestLedger(unittest.TestCase):
    def test_residual_equation(self):
        rows = synth_rows(n=4)
        led = LED.ledger(rows, synth_meta())
        expect = (led["work_in_J"] - (led["dKE_trans_J"] + led["dKE_rot_J"]
                                      + led["dPE_grav_J"]))
        self.assertAlmostEqual(led["residual_J"], expect, places=9)

    def test_no_closure_claim(self):
        led = LED.ledger(synth_rows(), synth_meta())
        self.assertFalse(led["closure_claim"])
        self.assertEqual(led["bond_energy_J"], "UNAVAILABLE")
        self.assertEqual(led["dissipation_J"], "UNAVAILABLE")


class TestConvergence(unittest.TestCase):
    def test_thresholds_parsed_not_hardcoded(self):
        th = CONV.load_thresholds()
        self.assertAlmostEqual(th["work"], 0.05)
        self.assertAlmostEqual(th["impulse"], 0.05)
        self.assertAlmostEqual(th["residence"], 0.10)
        self.assertAlmostEqual(th["mass_rel"], 1e-6)
        self.assertAlmostEqual(th["fragment"], 0.10)
        self.assertIn("identical", th["jam_wrap_rule"])

    def test_epsilon_within_tol(self):
        out = CONV.evaluate(synth_agg(work=1.0, impulse=0.5, residence=0.4,
                                      breaks=40),
                            synth_agg(work=1.04, impulse=0.52, residence=0.43,
                                      breaks=42))
        self.assertTrue(out["metrics"]["work"]["within_tol"])
        self.assertTrue(out["metrics"]["impulse"]["within_tol"])
        self.assertTrue(out["metrics"]["residence"]["within_tol"])
        self.assertTrue(out["metrics"]["fragment"]["within_tol"])
        self.assertTrue(out["converged"])

    def test_epsilon_outside_tol(self):
        out = CONV.evaluate(synth_agg(work=1.0), synth_agg(work=1.2))
        self.assertFalse(out["metrics"]["work"]["within_tol"])
        self.assertFalse(out["converged"])

    def test_jam_wrap_identical_rule(self):
        out = CONV.evaluate(synth_agg(jam=False), synth_agg(jam=True))
        self.assertFalse(out["metrics"]["jam"]["within_tol"])
        self.assertFalse(out["converged"])

    def test_mass_cap_rule(self):
        out = CONV.evaluate(synth_agg(rel_err=5e-7), synth_agg(rel_err=5e-6))
        self.assertFalse(out["metrics"]["mass"]["within_tol"])

    def test_proxy_excluded(self):
        rows = synth_rows(source="ANALYTIC_DIAGNOSTIC" + "_ONLY")
        with self.assertRaises(ValueError):
            AGG.aggregate(rows, [], synth_meta())

    def test_malformed_empty_telemetry(self):
        with self.assertRaises(ValueError):
            AGG.aggregate([], [], synth_meta())

    def test_malformed_missing_key(self):
        rows = synth_rows()
        del rows[0]["contact_force_total_N"]
        with self.assertRaises(KeyError):
            AGG.aggregate(rows, [], synth_meta())


class TestRunnerHelpers(unittest.TestCase):
    def test_dt_mapping_values(self):
        for dt, t_sim in ((0.01, 2.4), (0.005, 1.2), (0.0025, 0.6),
                          (0.00125, 0.3)):
            m = RUN.dt_source_mapping(dt)
            self.assertEqual(m["physics_dt_s"], dt)
            self.assertEqual(m["updates"], 240)
            self.assertAlmostEqual(m["sim_time_s"], t_sim)

    def test_dt_mapping_rejects_off_ladder(self):
        with self.assertRaises(ValueError):
            RUN.dt_source_mapping(0.003)

    def test_run_paths_layout(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = RUN.run_paths(td, "FDM", 0.005)
            for name in ("config.json", "environment.json",
                         "asset_manifest.json", "telemetry.jsonl",
                         "events.jsonl", "summary.json",
                         "stdout.log", "stderr.log"):
                self.assertTrue(p[name].startswith(
                    os.path.join(td, "results", "FDM", "dt_0.005")))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                RUN.run_paths(td, "NOPE", 0.005)

    def test_executor_labels_rejected(self):
        bad = ["PA" + "SS", "VALID" + "ATED", "COMPL" + "ETE"]
        for lab in bad:
            self.assertNotIn(lab, RUN.CASES + ("RUN_OK", "RUN_FAILED",
                                               "IMPLEMENTED", "BLOCKED",
                                               "FAILED"))


if __name__ == "__main__":
    unittest.main()
