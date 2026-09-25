"""R1.4 aggregation + convergence evaluation (reads runs, never reruns).

Convergence thresholds from CONTRACT_R1 section 8 (parsed): work 5%,
impulse 5%, residence 10%, mass 1e-6, discrete 10%. Observability rules
per goal R1 sections 17-20: wrap null/NOT_IMPLEMENTED, screen
null/NOT_APPLICABLE, residence null/RIGHT_CENSORED, jam
null/NOT_OBSERVABLE -> all NOT_EVALUABLE for this fixture.

Primary pair: dt 0.0025 vs 0.00125. A metric is evaluated only when
observable==True and comparable==True; otherwise NOT_EVALUABLE.
"""
import glob
import json
import os
import re

HERE = os.path.abspath(__file__)
R1 = os.path.dirname(os.path.dirname(HERE))
CONV = os.path.join(R1, "convergence")
RUNS = os.path.join(CONV, "runs")
CASES = ("FDM", "PURGE", "WRAP")
LADDER = [0.01, 0.005, 0.0025, 0.00125]
PRIMARY = (0.0025, 0.00125)


def load_thresholds():
    text = open(os.path.join(R1, "CONTRACT_R1.md")).read()
    th = {}
    m = re.search(r"Shaft work: (\d+)%", text)
    th["work"] = int(m.group(1)) / 100.0
    m = re.search(r"Contact impulse: (\d+)%", text)
    th["impulse"] = int(m.group(1)) / 100.0
    m = re.search(r"Residence time: (\d+)%", text)
    th["residence"] = int(m.group(1)) / 100.0
    m = re.search(r"relative error <= ([0-9.e-]+)", text)
    th["mass"] = float(m.group(1))
    m = re.search(r"Fragment / bond-break count: (\d+)%", text)
    th["discrete"] = int(m.group(1)) / 100.0
    return th


def rel_change(fine, coarse, eps=1e-12):
    denom = max(abs(fine), abs(coarse), eps)
    return abs(fine - coarse) / denom


def aggregate_run(case, dt):
    d = os.path.join(RUNS, "%s_dt_%s" % (case, dt))
    s = json.load(open(os.path.join(d, "summary.json")))
    tel = [json.loads(l) for l in
           open(os.path.join(d, "telemetry.jsonl")) if l.strip()]
    evs = [json.loads(l) for l in
           open(os.path.join(d, "events.jsonl")) if l.strip()]
    # Break count from CONSTRAINT STATE events (mechanically causal),
    # cross-checked against summary bonds block.
    ev_breaks = sum(1 for e in evs
                    if e.get("event") == "constraint_disable")
    last = tel[-1]
    first = tel[0]
    ke_d = last["ke_trans_J"] + last["ke_rot_J"] \
        - (first["ke_trans_J"] + first["ke_rot_J"])
    pe_d = last["pe_grav_J"] - first["pe_grav_J"]
    agg = {
        "case": case, "dt_s": dt,
        "run_status": s["status"],
        "observed_duration_s": s["observed_duration_s"],
        "duration_ok": s["duration_within_tol"],
        "substeps": s["substeps_expected"],
        "scene_sha256": s["scene_sha256"],
        "mass": {
            "initial_kg": s["mass_accounting"]["m_initial_kg"],
            "active_kg": s["mass_accounting"]["m_active_kg"],
            "output_kg": s["mass_accounting"]["m_output_kg"],
            "removed_kg": s["mass_accounting"]["m_intentionally_removed_kg"],
            "unexplained_kg":
                s["mass_accounting"]["m_unexplained_missing_kg"],
            "rel_error": s["mass_accounting"]["relative_error"],
            "observable": True, "comparable": True,
        },
        "impulse": {
            "J_shaft_magnitude_sum_Ns":
                s["impulse"]["J_shaft_magnitude_sum_Ns"],
            "classification": s["impulse"]["classification_status"],
            # R1 finding: the runtime ContactSensor frame is cadence-
            # gated — at dt=0.00125 it captured 12 contact events over
            # 1920 steps vs 247/960 at dt=0.0025. The magnitude sum is
            # therefore NOT a physical impulse integral comparable
            # across dt. comparable=False (NOT_EVALUABLE) until a per-
            # physics-step impulse path (e.g. direct PhysX contact
            # stream) replaces the sensor-cadence source.
            "observable": True, "comparable": False,
            "sensor_rows_captured": s.get("contact_rows"),
            "signed_tau_shaftA_Nms": s["impulse"]["signed_tau_shaftA_Nms"],
            "signed_tau_shaftB_Nms": s["impulse"]["signed_tau_shaftB_Nms"],
        },
        "bonds": {
            "breaks": s["bonds"]["breaks"],
            "breaks_from_events": ev_breaks,
            "connected_components_final":
                s["bonds"]["connected_components_final"],
            "atomic_bodies": s["bonds"]["atomic_bodies"],
            "constraint_state_changed": s["bonds"]["constraint_state_changed"],
            "observable": True, "comparable": True,
        },
        "energy": {
            "ke_delta_J": ke_d, "pe_delta_J": pe_d,
            "work_boundary_J": None,
            "work_status": s["energy_ledger"]["work_boundary_status"],
            "ledger_status": s["energy_ledger"]["status"],
            "observable": False, "comparable": False,
        },
        "residence": {"value": None, "status": "RIGHT_CENSORED",
                      "observable": False, "comparable": False},
        "wrap": {"value": None, "status": "NOT_IMPLEMENTED",
                 "observable": False, "comparable": False},
        "screen_passage": {"value": None, "status": "NOT_APPLICABLE",
                           "observable": False, "comparable": False},
        "jam": {"value": None, "status": "NOT_OBSERVABLE",
                "observable": False, "comparable": False},
        "telemetry_rows": len(tel),
    }
    return agg


def main():
    th = load_thresholds()
    runs = {}
    for case in CASES:
        for dt in LADDER:
            runs["%s@%s" % (case, dt)] = aggregate_run(case, dt)
    # Validity gate: every run must be RUN_OK with duration + mass ok.
    all_valid = all(
        r["run_status"] == "RUN_OK" and r["duration_ok"]
        and r["mass"]["rel_error"] <= th["mass"]
        for r in runs.values())
    convergence = {}
    for case in CASES:
        coarse = runs["%s@%s" % (case, PRIMARY[0])]
        fine = runs["%s@%s" % (case, PRIMARY[1])]
        metrics = {}

        def eval_metric(name, fine_v, coarse_v, tol):
            metrics[name] = {
                "fine": fine_v, "coarse": coarse_v,
                "epsilon": rel_change(fine_v, coarse_v),
                "threshold": tol,
                "observable": True, "comparable": True,
                "within_threshold": rel_change(fine_v, coarse_v) <= tol,
            }

        # Impulse: comparable=False (sensor-cadence-gated capture — see
        # aggregate note); NOT_EVALUABLE until a per-physics-step
        # impulse path exists.
        metrics["impulse_magnitude_sum_Ns"] = {
            "fine": fine["impulse"]["J_shaft_magnitude_sum_Ns"],
            "coarse": coarse["impulse"]["J_shaft_magnitude_sum_Ns"],
            "epsilon": rel_change(
                fine["impulse"]["J_shaft_magnitude_sum_Ns"],
                coarse["impulse"]["J_shaft_magnitude_sum_Ns"]),
            "threshold": th["impulse"],
            "observable": True, "comparable": False,
            "verdict": "NOT_EVALUABLE (sensor cadence misses contacts at "
                       "fine dt: 12/1920 fires at 0.00125 vs 247/960 at "
                       "0.0025 — magnitude sum is cadence-gated, not "
                       "physical)",
        }
        eval_metric("break_count",
                    fine["bonds"]["breaks"], coarse["bonds"]["breaks"],
                    th["discrete"])
        eval_metric("connected_components_final",
                    float(fine["bonds"]["connected_components_final"]),
                    float(coarse["bonds"]["connected_components_final"]),
                    th["discrete"])
        metrics["work_boundary"] = {
            "epsilon": None, "threshold": th["work"],
            "observable": False, "comparable": False,
            "verdict": "NOT_EVALUABLE (boundary work classification "
                       "UNAVAILABLE in this fixture)",
        }
        metrics["residence"] = {
            "verdict": "NOT_EVALUABLE (no measured exit: RIGHT_CENSORED)",
            "observable": False, "comparable": False,
        }
        metrics["mass"] = {
            "fine_rel": fine["mass"]["rel_error"],
            "coarse_rel": coarse["mass"]["rel_error"],
            "threshold": th["mass"],
            "observable": True, "comparable": True,
            "within_threshold": (fine["mass"]["rel_error"] <= th["mass"]
                                 and coarse["mass"]["rel_error"]
                                 <= th["mass"]),
        }
        metrics["wrap"] = {"verdict": "NOT_EVALUABLE (NOT_IMPLEMENTED)",
                           "observable": False, "comparable": False}
        metrics["screen_passage"] = {"verdict": "NOT_EVALUABLE "
                                                "(NOT_APPLICABLE)",
                                     "observable": False,
                                     "comparable": False}
        metrics["jam"] = {"verdict": "NOT_EVALUABLE (NOT_OBSERVABLE)",
                          "observable": False, "comparable": False}
        evaluated = [m for m in metrics.values()
                     if m.get("comparable") and m.get("epsilon")
                     is not None]
        converged = bool(evaluated) and all(
            m["within_threshold"] for m in evaluated)
        convergence[case] = {
            "primary_pair": {"coarse_dt": PRIMARY[0],
                             "fine_dt": PRIMARY[1]},
            "metrics": metrics,
            "numerically_converged": converged,
        }
    out = {
        "schema": "r1_convergence/1",
        "evidence_level": "UNCALIBRATED_DIGITAL_DYNAMICS",
        "experiment_valid": all_valid,
        "thresholds_source": "CONTRACT_R1.md section 8 (parsed, not "
                             "hardcoded)",
        "thresholds": th,
        "runs": runs,
        "convergence": convergence,
        "overall_numerically_converged": all(
            c["numerically_converged"] for c in convergence.values()),
        "notes": [
            "Impulse metric is the typed per-step impulse magnitude sum "
            "over the cluster contact set (D1 unit rule: summed once). "
            "Per-shaft signed split is UNAVAILABLE in this Isaac build "
            "(raw body handles are ints, not path-resolvable); it does "
            "not affect cross-dt comparability because the contact set "
            "and geometry schedule are identical across dt.",
            "Break schedule is predeclared (every 40 steps) and is "
            "identical across dt in PHYSICAL time; break count "
            "differences across dt therefore reflect contact-impulse "
            "resolution at the shared measurement horizon.",
            "work_boundary is NOT_EVALUABLE: contact->shaft body-handle "
            "classification is not exposed by the installed API "
            "(diagnostic-only magnitude proxy is reported instead).",
            "residence/wrap/screen/jam are NOT_EVALUABLE per observability "
            "matrix; fixture has no screen, no exit, no wrap sensing, "
            "kinematic (non-stallable) shafts.",
        ],
    }
    with open(os.path.join(CONV, "convergence_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({c: {"converged": v["numerically_converged"],
                          "metrics": {k: (m.get("epsilon"),
                                          m.get("within_threshold"))
                                         for k, m in
                                         v["metrics"].items()
                                         if m.get("comparable")}}
                     for c, v in convergence.items()}, indent=2))
    print("experiment_valid:", all_valid)
    print("overall_numerically_converged:",
          out["overall_numerically_converged"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
