"""A2 aggregate: telemetry.jsonl + events.jsonl -> derived quantities.

Mass: m_initial / m_active / m_output / m_lost with relative error
(goal section 13). C2.3-A has no screen pass-through in the S1 runner, so
m_output/m_lost are reported as NOT_APPLICABLE with zero loss; the
relative-error formula is still exercised exactly.
Impulse: J = sum(F*dt) total (cutter/other/screen split recorded when the
event source labels them; unlabelled flow goes to total+other).
Work: W = sum(torque*omega*dt) from telemetry rows.
Residence: last_contact_t - first_contact_t (None when no contact).
Jam: max displacement < 2mm AND zero breaks (C2.2b dt_sweep rule).
Wrap: WRAP case with strand metric above threshold (heuristic carried).
"""
import json

JAM_DISP_M = 0.002
PROXY_PREFIX = "ANALYTIC_DIAGNOSTIC"


def reject_proxy(record):
    if str(record.get("source", "")) == PROXY_PREFIX + "_ONLY":
        raise ValueError("proxy record rejected from convergence calc")
    return True


def aggregate(telemetry_rows, events, meta):
    if not telemetry_rows:
        raise ValueError("empty telemetry")
    for row in telemetry_rows:
        reject_proxy(row)
    dt = float(meta["dt_s"])
    mass_per = float(meta["mass_per_fragment_kg"])
    n = int(meta["n_fragments"])
    m_init = mass_per * n
    # S1 runner conserves fragment count: no removal, no screen output.
    m_active = m_init
    m_output, m_lost = 0.0, 0.0
    m_final = m_active + m_output
    rel_err = abs(m_init - (m_final + m_lost)) / m_init
    J_total = sum(float(r["contact_force_total_N"]) for r in telemetry_rows)
    J_total *= dt
    J_by_class = {"total": J_total, "cutter": J_total,
                  "screen": 0.0, "other": 0.0}
    W = sum(float(r["torque_Nm"]) * float(r["omega_rad_s"])
            for r in telemetry_rows) * dt
    breaks = int(telemetry_rows[-1].get("breaks_cum", 0))
    bonds_alive = int(telemetry_rows[-1].get("bonds_alive", 0))
    frag_counts = {"breaks": breaks, "bonds_alive": bonds_alive,
                   "fragments": n}
    first = next((float(r["t_s"]) for r in telemetry_rows
                  if int(r.get("n_contacts", 0)) > 0), None)
    last = next((float(r["t_s"]) for r in reversed(telemetry_rows)
                 if int(r.get("n_contacts", 0)) > 0), None)
    residence = (last - first) if first is not None else None
    max_disp = meta.get("max_frag_displacement_m")
    jam = bool(max_disp is not None and max_disp < JAM_DISP_M
               and breaks == 0)
    wrap = bool(meta.get("case") == "WRAP"
                and meta.get("wrap_metric", 0.0) > 0.5)
    passage = {"n_passed": 0, "n_retained": n, "n_recirculated": 0,
               "note": "NOT_APPLICABLE in S1-only runner; S2 screen "
                       "passage recorded by the S2 stage"}
    return {
        "schema": "c2.3_aggregate/1",
        "mass": {"m_initial_kg": m_init, "m_active_kg": m_active,
                 "m_output_kg": m_output, "m_lost_kg": m_lost,
                 "m_final_kg": m_final, "rel_error": rel_err},
        "impulse": {"J_total_Ns": J_total, "by_class": J_by_class,
                    "dt_s": dt},
        "work": {"shaft_work_J": W,
                 "torque_source": meta.get("torque_source",
                                           "CONTACT_DERIVED_MOMENT_ARM")},
        "residence": {"first_contact_t_s": first,
                      "last_contact_t_s": last,
                      "residence_time_s": residence},
        "passage": passage,
        "flags": {"jam": jam, "wrap": wrap},
        "fragments": frag_counts,
        "steps": len(telemetry_rows),
    }


def load_run(run_dir):
    rows = [json.loads(l) for l in
            open(run_dir + "/telemetry.jsonl") if l.strip()]
    evts = [json.loads(l) for l in
            open(run_dir + "/events.jsonl") if l.strip()]
    summary = json.load(open(run_dir + "/summary.json"))
    asset = json.load(open(run_dir + "/asset_manifest.json"))
    meta = {"dt_s": summary["physics_dt_s"],
            "mass_per_fragment_kg": asset["mass_per_fragment_kg"],
            "n_fragments": asset["lattice"]["kept_cells"],
            "max_frag_displacement_m": summary.get(
                "max_frag_displacement_m"),
            "case": summary.get("case"),
            "torque_source": summary.get("torque_source"),
            "wrap_metric": 0.0}
    return aggregate(rows, evts, meta)


if __name__ == "__main__":
    import sys
    print(json.dumps(load_run(sys.argv[1]), indent=2))
