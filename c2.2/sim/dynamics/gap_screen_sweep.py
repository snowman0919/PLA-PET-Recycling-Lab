"""Gate F: real gap x screen sweep on survivors (thin driver).

S1 gap sweep: shaft center distance 59.2/60.0/60.8mm around nominal 60
(engagement +/-0.8mm within the 0.4-1.2 sweep spirit; cutters r=40mm so
nominal overlap is deep). Screen sweep: hole 3.0/4.0/5.5mm via s2_screen.
Cases: W1/seed7 + W4/seed11 (one W1 + one W4). S2 arch: S2-A and S2-B.

Writes c2.2/results/dyn_gap_screen_sweep.json.
"""
import itertools
import json
import os
import subprocess

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(C22, "results", "dyn_gap_screen_sweep.json")
PY = os.path.expanduser("~/env_isaacsim-c22/bin/python")
CENTERS = [59.2, 60.0, 60.8]
HOLES = [3.0, 4.0, 5.5]
CASES = [("W1", 7), ("W4", 11)]
ARCHS = ["S2-A", "S2-B"]
STEPS = 240
DT = 0.005


def run(cmd):
    env = dict(os.environ)
    env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def main() -> int:
    s1rec, s2rec = [], []
    failures: list[str] = []
    for (wc, seed), c in itertools.product(CASES, CENTERS):
        tag = f"s1_{wc}_{seed}_dt{DT}_n{STEPS}_c{c}"
        r = run([PY, os.path.join(C22, "sim", "dynamics", "s1_physx.py"),
                 "--class", wc, "--seed", str(seed), "--steps", str(STEPS),
                 "--dt", str(DT), "--center-mm", str(c)])
        try:
            s = json.load(open(os.path.join(C22, "results", "dyn_s1",
                                            tag + ".summary.json")))
            s1rec.append({"class": wc, "seed": seed, "center_mm": c,
                          "exit": r.returncode, "status": s.get("status"),
                          "bond_breaks": s.get("bond_breaks"),
                          "torque_impulse_Nms": s.get("torque_impulse_Nms"),
                          "contact_steps": s.get("contact_steps"),
                          "tag": tag})
            if r.returncode != 0:
                failures.append(f"{tag}: exit {r.returncode}")
        except Exception as exc:
            failures.append(f"{tag}: unreadable: {exc}")
    for (wc, seed), hole, arch in itertools.product(CASES, HOLES, ARCHS):
        base = f"s1_{wc}_{seed}_dt{DT}_n{STEPS}"
        # prefer center-60 run as S1 source; fall back to no-suffix legacy
        import glob as _g
        cands = sorted(_g.glob(os.path.join(
            C22, "results", "dyn_s1", base + "_c60*.summary.json")))
        if not cands:
            cands = sorted(_g.glob(os.path.join(
                C22, "results", "dyn_s1", base + ".summary.json")))
        if not cands:
            failures.append(f"s2 {arch} hole {hole}: no S1 source for "
                            f"{base}")
            continue
        src = os.path.basename(cands[0]).replace(".summary.json", "")
        r = run([PY, os.path.join(C22, "sim", "dynamics", "s2_screen.py"),
                 "--from-s1", src, "--arch", arch, "--hole-mm", str(hole),
                 "--steps", str(STEPS), "--dt", str(DT)])
        stag = f"s2_{arch}_{src}_hole{hole}"
        try:
            s = json.load(open(os.path.join(C22, "results", "dyn_s2",
                                            stag + ".summary.json")))
            s2rec.append({"from_s1": src, "arch": arch, "hole_mm": hole,
                          "exit": r.returncode, "status": s.get("status"),
                          "pass_rate": s.get("pass_rate"),
                          "n_passed": s.get("n_passed"),
                          "n_frags": s.get("n_frags")})
            if r.returncode != 0:
                failures.append(f"{stag}: exit {r.returncode}")
        except Exception as exc:
            failures.append(f"{stag}: unreadable: {exc}")
    rec = {"schema": "dyn_gap_screen_sweep/1", "centers_mm": CENTERS,
           "holes_mm": HOLES, "s1": s1rec, "s2": s2rec,
           "status": "PASS" if not failures else "FAIL",
           "failures": failures}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    print(json.dumps(rec, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
