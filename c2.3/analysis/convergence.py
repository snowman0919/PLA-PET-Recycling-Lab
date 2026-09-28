"""A2 convergence evaluator. Thresholds are parsed, NEVER hardcoded.

Sources: c2.3/configs/baseline.json thresholds block (percent values +
mass_conservation_relative_error_max) and CONTRACT.md section 7 (jam/wrap
identical rule). evaluate() takes coarse->fine aggregate pairs and returns
per-metric epsilon + within-tolerance verdicts.
"""
import json
import os
import re

HERE = os.path.abspath(__file__)
C23 = os.path.dirname(os.path.dirname(HERE))


def load_thresholds(c23dir=C23):
    base = json.load(open(os.path.join(c23dir, "configs", "baseline.json")))
    th = base["thresholds"]
    contract = open(os.path.join(c23dir, "CONTRACT.md")).read()
    m = re.search(r"jam / wrap flags: ([^\n]+)", contract)
    discrete_rule = m.group(1).strip() if m else th.get("jam_wrap")
    return {
        "work": th["shaft_work_pct"] / 100.0,
        "impulse": th["contact_impulse_pct"] / 100.0,
        "residence": th["residence_time_pct"] / 100.0,
        "mass_rel": th["mass_conservation_relative_error_max"],
        "fragment": th["fragment_bond_count_pct"] / 100.0,
        "jam_wrap_rule": discrete_rule,
    }


def epsilon(new, old):
    denom = abs(old) if abs(old) > 0 else 1.0
    return abs(new - old) / denom


def _frag_count(agg):
    return agg["fragments"]["breaks"]


def evaluate(coarse, fine, c23dir=C23):
    th = load_thresholds(c23dir)
    out = {"thresholds_source": "baseline.json + CONTRACT.md §7",
           "thresholds": th, "metrics": {}}
    pairs = [
        ("work", coarse["work"]["shaft_work_J"],
         fine["work"]["shaft_work_J"], th["work"]),
        ("impulse", coarse["impulse"]["J_total_Ns"],
         fine["impulse"]["J_total_Ns"], th["impulse"]),
        ("fragment", float(_frag_count(coarse)),
         float(_frag_count(fine)), th["fragment"]),
    ]
    rc, rf = coarse["residence"]["residence_time_s"], \
        fine["residence"]["residence_time_s"]
    if rc is None or rf is None:
        out["metrics"]["residence"] = {
            "epsilon": None, "tol": th["residence"],
            "within_tol": rc == rf,
            "note": "no-contact runs: residence undefined on both sides "
                    "only if both None"}
    else:
        pairs.append(("residence", rc, rf, th["residence"]))
    for name, c, f, tol in pairs:
        e = epsilon(f, c)
        out["metrics"][name] = {"epsilon": e, "tol": tol,
                                "within_tol": e <= tol,
                                "coarse": c, "fine": f}
    # Mass: absolute relative-error values evaluated against the cap
    # (goal section 13), not an adjacent-dt epsilon.
    mc, mf = coarse["mass"]["rel_error"], fine["mass"]["rel_error"]
    out["metrics"]["mass"] = {
        "coarse_rel_error": mc, "fine_rel_error": mf,
        "cap": th["mass_rel"],
        "within_tol": mc <= th["mass_rel"] and mf <= th["mass_rel"]}
    jc, jf = coarse["flags"]["jam"], fine["flags"]["jam"]
    wc, wf = coarse["flags"]["wrap"], fine["flags"]["wrap"]
    out["metrics"]["jam"] = {"coarse": jc, "fine": jf,
                             "identical": jc == jf,
                             "within_tol": jc == jf}
    out["metrics"]["wrap"] = {"coarse": wc, "fine": wf,
                              "identical": wc == wf,
                              "within_tol": wc == wf}
    verdicts = [v["within_tol"] for v in out["metrics"].values()]
    out["converged"] = all(verdicts)
    return out


if __name__ == "__main__":
    import sys
    c = json.load(open(sys.argv[1]))
    f = json.load(open(sys.argv[2]))
    print(json.dumps(evaluate(c, f), indent=2))
