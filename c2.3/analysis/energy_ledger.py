"""A2 partial mechanical energy ledger (NEVER claims closure).

  residual = W_in - (dKE_trans + dKE_rot + dPE_grav + E_bond + E_diss)

E_bond is UNAVAILABLE: bond-break thresholds are nominal strengths x
IMPULSE_SCALE (UNCALIBRATED), with no stored-energy model attached.
E_diss is UNAVAILABLE: PhysX contact dissipation is not exposed on the
ContactSensor path. KE/PE deltas come from telemetry first/last steps.
"""
import json

UNAVAILABLE = "UNAVAILABLE"


def ledger(telemetry_rows, meta):
    if not telemetry_rows:
        raise ValueError("empty telemetry")
    mass_per = float(meta["mass_per_fragment_kg"])
    g = 9.81
    first, last = telemetry_rows[0], telemetry_rows[-1]
    dKE_t = float(last["ke_trans_J"]) - float(first["ke_trans_J"])
    dKE_r = float(last["ke_rot_J"]) - float(first["ke_rot_J"])
    dPE = float(last["pe_grav_J"]) - float(first["pe_grav_J"])
    W_in = float(last["work_cum_J"])
    n = int(meta["n_fragments"])
    accounted = dKE_t + dKE_r + dPE  # bond + dissipation unavailable
    residual = W_in - accounted
    denom = abs(W_in) if abs(W_in) > 0 else 1.0
    return {
        "schema": "c2.3_energy_ledger/1",
        "closure_claim": False,
        "work_in_J": W_in,
        "dKE_trans_J": dKE_t,
        "dKE_rot_J": dKE_r,
        "dPE_grav_J": dPE,
        "bond_energy_J": UNAVAILABLE,
        "bond_energy_note": ("no stored-energy model attached to nominal "
                             "strength x IMPULSE_SCALE thresholds"),
        "dissipation_J": UNAVAILABLE,
        "dissipation_note": ("PhysX contact dissipation not exposed on "
                             "ContactSensor path"),
        "accounted_J": accounted,
        "residual_J": residual,
        "residual_over_work": residual / denom,
        "n_fragments": n,
        "mass_per_fragment_kg": mass_per,
        "gravity_m_s2": g,
    }


def load_run(run_dir):
    rows = [json.loads(l) for l in
            open(run_dir + "/telemetry.jsonl") if l.strip()]
    asset = json.load(open(run_dir + "/asset_manifest.json"))
    meta = {"mass_per_fragment_kg": asset["mass_per_fragment_kg"],
            "n_fragments": asset["lattice"]["kept_cells"]}
    return ledger(rows, meta)


if __name__ == "__main__":
    import sys
    print(json.dumps(load_run(sys.argv[1]), indent=2))
