"""Gate E: 3-level dt sweep on one W1 + one W4 case (thin driver over s1_physx).

Runs s1_physx as subprocess at dt in {0.0025, 0.005, 0.01} for W1/seed7 and
W4/seed11; collates fragment count (bond_breaks), torque impulse, jam proxy
(max displacement < 2mm AND zero breaks = jam), mass error vs dt.

Writes c2.2/results/dyn_dt_sweep.json. Driver itself runs headless PhysX.
"""
import json
import os
import subprocess
import sys

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(C22, "results", "dyn_dt_sweep.json")
PY = os.path.expanduser("~/env_isaacsim-c22/bin/python")
CASES = [("W1", 7), ("W4", 11)]
DTS = [0.0025, 0.005, 0.01]
STEPS = 240


def main() -> int:
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    rows = []
    failures: list[str] = []
    for wc, seed in CASES:
        for dt in DTS:
            nsteps = STEPS
            cmd = [PY, os.path.join(C22, "sim", "dynamics", "s1_physx.py"),
                   "--class", wc, "--seed", str(seed), "--steps",
                   str(nsteps), "--dt", str(dt)]
            r = subprocess.run(cmd, capture_output=True, text=True, env=env)
            tag = f"s1_{wc}_{seed}_dt{dt}_n{nsteps}"
            spath = os.path.join(C22, "results", "dyn_s1", tag
                                 + ".summary.json")
            try:
                s = json.load(open(spath))
            except Exception as exc:
                failures.append(f"{tag}: summary unreadable: {exc}")
                continue
            jam = (s.get("max_frag_displacement_m", 1.0) < 0.002
                   and s.get("bond_breaks", 0) == 0)
            rows.append({"class": wc, "seed": seed, "dt": dt,
                         "exit": r.returncode,
                         "status": s.get("status"),
                         "bond_breaks": s.get("bond_breaks"),
                         "bonds_alive": s.get("bonds_alive"),
                         "torque_impulse_Nms": s.get("torque_impulse_Nms"),
                         "jam": jam,
                         "mass_error_kg": s.get("mass_error_kg"),
                         "contact_steps": s.get("contact_steps")})
            if r.returncode != 0:
                failures.append(f"{tag}: exit {r.returncode}")
    rec = {"schema": "dyn_dt_sweep/1", "dts": DTS, "rows": rows,
           "status": "PASS" if not failures else "FAIL",
           "failures": failures}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    print(json.dumps(rec, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
