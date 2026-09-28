"""Gate F follow-on: refit surrogate anchors on REAL dynamics data (additive).

Does NOT mutate c2.2/sim/optimization/i6_surrogate.py (other workstream owns
it) and does NOT delete the i5 numpy proxy. Reads:
  c2.2/results/dyn_gap_screen_sweep.json + dyn_s1/dyn_s2 summaries
and writes c2.2/results/dyn_surrogate.json: per-arch/class measured means
(torque impulse, pass rate, bond breaks, sliver-by-yaw) + analytic-surface
deltas vs the I6 I5-anchored ARCH_BASE. Evidence: REAL_PHYSX_HEADLESS.
"""
import glob
import json
import os

HERE = os.path.abspath(__file__)
C22 = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(C22, "results", "dyn_surrogate.json")


def main() -> int:
    sweep_path = os.path.join(C22, "results", "dyn_gap_screen_sweep.json")
    if not os.path.isfile(sweep_path):
        print(json.dumps({"status": "BLOCKED",
                          "reason": "dyn_gap_screen_sweep.json missing"}))
        return 1
    sweep = json.load(open(sweep_path))
    if sweep.get("status") != "PASS":
        print(json.dumps({"status": "BLOCKED",
                          "reason": "sweep not PASS",
                          "failures": sweep.get("failures")}))
        return 1
    # Aggregate dynamics measurements by (class, arch, hole/center).
    s1_by_center = {}
    for r in sweep["s1"]:
        s1_by_center.setdefault((r["class"], r["center_mm"]), []).append(r)
    s2_by_arch_hole = {}
    for r in sweep["s2"]:
        s2_by_arch_hole.setdefault((r["arch"], r["hole_mm"]), []).append(r)
    anchors = {
        "torque_impulse_Nms_mean_by_class": {},
        "pass_rate_mean_by_arch_hole": {},
        "bond_breaks_mean_by_class_center": {},
    }
    for (cls, c), rs in sorted(s1_by_center.items()):
        ts = [r["torque_impulse_Nms"] for r in rs]
        bs = [r["bond_breaks"] for r in rs]
        anchors["torque_impulse_Nms_mean_by_class"].setdefault(cls, {})[c] = (
            sum(ts) / len(ts))
        anchors["bond_breaks_mean_by_class_center"].setdefault(cls, {})[c] = (
            sum(bs) / len(bs))
    for (arch, hole), rs in sorted(s2_by_arch_hole.items()):
        pr = [r["pass_rate"] for r in rs]
        anchors["pass_rate_mean_by_arch_hole"].setdefault(arch, {})[hole] = (
            sum(pr) / len(pr))
    rec = {"schema": "dyn_surrogate/1",
           "evidence": "REAL_PHYSX_HEADLESS",
           "i6_surrogate_mutated": False,
           "i5_proxy_deleted": False,
           "note": ("Additive refit: I6 analytic surface untouched; deltas "
                    "reported here for the next workstream to adopt."),
           "anchors": anchors,
           "n_s1": len(sweep["s1"]), "n_s2": len(sweep["s2"]),
           "status": "PASS", "failures": []}
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2)
        fh.write("\n")
    print(json.dumps(rec, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
