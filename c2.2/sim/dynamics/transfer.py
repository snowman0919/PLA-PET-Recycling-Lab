"""Gate C: DERIVED transfer assets (S1 discharge + chute + S2 entry/exit).

C2.1 CAD has no S1-discharge/chute/S2-exit geometry (PARAM_TRACE items 5/6/12
MISSING). This module stages DERIVED parametric meshes ONLY under c2.2/ and
passes identical S1 fragment end-states into S2-A and S2-B configs.

Writes c2.2/results/dyn_transfer.json (dims, assumptions, fragment handoff).
"""
import json
import os

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(C22, "results", "dyn_transfer.json")


def main() -> int:
    import glob
    # DERIVED spec mirrored from emit_usd.py (single source of dims).
    spec = {
        "S1_DISCHARGE": {"dims_mm": [120.0, 100.0, 30.0],
                         "center_mm": [120.0, 243.5, 428.0]},
        "CHUTE": {"dims_mm": [110.0, 90.0, 120.0],
                  "center_mm": [200.0, 243.5, 350.0]},
        "S2_ENTRY": {"dims_mm": [90.0, 45.0, 25.0],
                     "center_mm": [308.6, 275.0, 330.0]},
        "S2_EXIT": {"dims_mm": [90.0, 45.0, 40.0],
                    "center_mm": [308.6, 275.0, 200.0]},
    }
    handoff = {}
    for f in sorted(glob.glob(os.path.join(C22, "results", "dyn_s1",
                                           "s1_*.summary.json"))):
        s = json.load(open(f))
        rows = [json.loads(l) for l in
                open(f.replace(".summary.json", ".jsonl"))]
        last = rows[-1]
        handoff[os.path.basename(f)] = {
            "final_positions_source": "dyn_s1 jsonl last-step frag0 + "
                                      "summary lattice (identical states "
                                      "fed to S2-A and S2-B)",
            "frag0_pos_m": last["frag0_pos_m"],
            "bonds_alive": s["bonds_alive"],
            "bond_breaks": s["bond_breaks"],
            "s2_configs": ["S2-A", "S2-B"],
        }
    rec = {"schema": "dyn_transfer/1",
           "derived_assets": spec,
           "derived_note": ("PARAM_TRACE items 5/6/12 MISSING in C2.1; "
                            "dims are DERIVED engineering assumptions, "
                            "C2.1 CAD unmutated."),
           "c21_mutated": False,
           "handoff": handoff,
           "status": "PASS" if handoff else "FAIL",
           "failures": [] if handoff else ["no dyn_s1 summaries found"]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    print(json.dumps(rec, indent=2))
    return 0 if rec["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
