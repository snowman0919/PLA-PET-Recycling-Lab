"""R2 aggregate + convergence evaluation (reads runs, never reruns).

Primary pair: dt 0.0025 vs 0.00125. Metrics from CONTRACT_R1 §8
(parsed): work 5%, impulse 5%, residence 10%, mass 1e-6, discrete 10%.
Observable/comparable rules per goal R1 §17-20.
"""
import glob
import json
import os
import re

HERE = os.path.abspath(__file__)
R2 = os.path.dirname(HERE)
CONV = os.path.dirname(R2)
R1 = os.path.dirname(CONV)
RUNS = os.path.join(R2, "runs")
# CONTRACT_R1.md lives at revisions/r1 root, not inside convergence/.
CONTRACT_R1_PATH = os.path.join(R1, "CONTRACT_R1.md")
CASES = ("FDM", "PURGE", "WRAP")
LADDER = [0.01, 0.005, 0.0025, 0.00125]
PRIMARY = (0.0025, 0.00125)


def load_thresholds():
    text = open(CONTRACT_R1_PATH).read()
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
    last = tel[-1]
    first = tel[0]
    imp_c = (abs(s["impulse"]["tau_shaftA_cum_Nms"])
             + abs(s["impulse"]["tau_shaftB_cum_Nms"]))
    agg = {
        "case": case, "dt_s": dt,
        "run_status": s["status"],
        "observed_duration_s": s["observed_duration_s"],
        "duration_ok": s["duration_within_tol"],
        "substeps": s["substeps_expected"],
        "scene_sha256": s["scene_sha256"],
        "mass": {
            "rel_error": s["mass_accounting"]["relative_error"],
            "observable": True, "comparable": True,
        },
        "impulse": {
            "signed_tau_shaftA_Nms": s["impulse"]["tau_shaftA_cum_Nms"],
            "signed_tau_shaftB_Nms": s["impulse"]["tau_shaftB_cum_Nms"],
            "abs_sum_Nms": imp_c,
            "observable": True, "comparable": True,
            "source": "subscribe_contact_report_events "
                      "(per-physics-step, typed impulse)",
        },
        "work": {
            "boundary_work_J": s["work"]["boundary_contact_work_J"],
            "observable": True, "comparable": True,
            "source": "typed impulse x kinematic boundary velocity "
                      "(NOT R*sum|F|)",
        },
        "bonds": {
            "breaks": s["bonds"]["breaks"],
            "break_schedule": s["bonds"]["break_schedule"],
            "connected_components_final":
                s["bonds"]["connected_components_final"],
            "constraint_state_changed": s["bonds"]["constraint_state_changed"],
            "observable": True, "comparable": True,
        },
        "energy": {
            "ke_rot_delta_J": s["energy_ledger"]["ke_rot_delta_J"],
            "ledger_status": s["energy_ledger"]["status"],
            "ke_rot_source": "rotational KE at t1 (R1 bug fixed)",
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
        "break_events": len(evs),
    }
    return agg


def main():
    th = load_thresholds()
    runs = {}
    for case in CASES:
        for dt in LADDER:
            runs["%s@%s" % (case, dt)] = aggregate_run(case, dt)
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

        eval_metric("boundary_work_J",
                    fine["work"]["boundary_work_J"],
                    coarse["work"]["boundary_work_J"], th["work"])
        eval_metric("impulse_abs_sum_Nms",
                    fine["impulse"]["abs_sum_Nms"],
                    coarse["impulse"]["abs_sum_Nms"], th["impulse"])
        eval_metric("break_count",
                    fine["bonds"]["breaks"], coarse["bonds"]["breaks"],
                    th["discrete"])
        eval_metric("connected_components_final",
                    float(fine["bonds"]["connected_components_final"]),
                    float(coarse["bonds"]["connected_components_final"]),
                    th["discrete"])
        metrics["residence"] = {
            "verdict": "NOT_EVALUABLE (no measured exit: RIGHT_CENSORED)",
            "observable": False, "comparable": False}
        metrics["mass"] = {
            "fine_rel": fine["mass"]["rel_error"],
            "coarse_rel": coarse["mass"]["rel_error"],
            "threshold": th["mass"],
            "observable": True, "comparable": True,
            "within_threshold": (fine["mass"]["rel_error"] <= th["mass"]
                                 and coarse["mass"]["rel_error"]
                                 <= th["mass"])}
        metrics["wrap"] = {"verdict": "NOT_EVALUABLE (NOT_IMPLEMENTED)",
                           "observable": False, "comparable": False}
        metrics["screen_passage"] = {
            "verdict": "NOT_EVALUABLE (NOT_APPLICABLE)",
            "observable": False, "comparable": False}
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
        "schema": "r2_convergence/1",
        "evidence_level": "UNCALIBRATED_DIGITAL_DYNAMICS",
        "experiment_valid": all_valid,
        "thresholds_source": "CONTRACT_R1.md section 8 (parsed)",
        "thresholds": th,
        "runs": runs,
        "convergence": convergence,
        "overall_numerically_converged": all(
            c["numerically_converged"] for c in convergence.values()),
        "notes": [
            "Per-physics-step contact stream (subscribe_contact_report_"
            "events + PhysxContactReportAPI threshold 0) replaces the "
            "R1 cadence-gated sensor path. Body identity via "
            "PhysicsSchemaTools.intToSdfPath; shaft contacts classified "
            "ShaftA/ShaftB; signed tau = a_hat . ((p-o) x J).",
            "Bond events are physics-driven: each inter-fragment joint "
            "accumulates |tau_shaft impulse|; threshold 0.02 N·m·s "
            "(UNCALIBRATED synthetic, declared in run_r2.py header); "
            "joint disabled when exceeded. NO scheduled breaks.",
            "R1 findings: break schedule was a step-index artifact "
            "(11/13 mismatch). R2 removes the scheduler entirely.",
            "R2 outcome: break/components converged (all 11/12); work "
            "and impulse do NOT converge within 5% — the metric is "
            "dominated by the initial drop transient whose per-step "
            "impulse magnitude is dt-dependent (contact phase at first "
            "shaft contact differs across dt; sign flips in tau_shaftA "
            "between coarse and fine dt confirm phase dependence, not "
            "integration error). Per goal §23 no tuning was applied.",
        ],
    }
    with open(os.path.join(R2, "convergence_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print(json.dumps({c: {"converged": v["numerically_converged"],
                          "metrics": {k: (round(m["epsilon"], 4),
                                          m["within_threshold"])
                                         for k, m in
                                         v["metrics"].items()
                                         if m.get("comparable")
                                         and m.get("epsilon")
                                         is not None}}
                     for c, v in convergence.items()}, indent=2))
    print("experiment_valid:", all_valid)
    print("overall_numerically_converged:",
          out["overall_numerically_converged"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
