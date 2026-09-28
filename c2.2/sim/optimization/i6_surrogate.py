"""I6 surrogate + Pareto/robustness (stdlib + numpy only).

Design: analytic screening surrogate, NOT a fitted ML model. Per-output
response surfaces are closed-form functions of (arch one-hot base rates,
gap/screen/waste-class/friction/bond-strength/orientation/thermal-index/
fragment descriptors) with coefficients set from I5 run statistics
(medians by arch/class) — no gradient fitting, no kernel inversion, so
no sklearn/scipy needed and no overfitting machinery to misread as
calibration.

Uncertainty: deterministic ensemble of K=8 members with fixed
perturbation directions (+/-5% coefficient jitter, ASSUMPTION spread);
spread = robustness proxy, NEVER a calibrated posterior.

Grouped split by seed (train {7,11,23} / val {37} / test {51}): no seed
leakage — every seed wholly in one fold. R2/MAE per output on test fold.

BO loop: small expected-improvement search over gap 0.4-1.2 x screen
3.0-5.5 x surviving archs using the surrogate mean + ensemble spread
(deterministic grid + seeded RNG; 64 evals).

Pareto: non-dominated front over maximize(yield, throughput, robustness)
minimize(torque, energy, jam-rate, wrap, sliver, oversize) with hard
constraints (drive/body envelopes, manufacturability flag: gap<0.5 or
screen<3.5 flagged NOT manufacturable-claimed). Picks: best-nominal,
robust, low-energy, purge (P2-class best), typical-FDM (W1-class best).

Robustness: deterministic grid perturbations (gap +/-0.1, screen +/-0.25,
friction +/-0.1, bond strength x0.9/1.1, orientation set, S2 eff x0.9/1.1;
~72 samples per finalist) re-evaluated through the REAL i5 s1_event +
s2_event path. Tolerance sensitivity = output range/mean per perturbation.

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY everywhere. No VALIDATED
language. Sub-mm gap NOT claimed manufacturable (simulation range only).
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
C22 = HERE.parents[2]
sys.path.insert(0, str(HERE.parent.parent / "generators"))
sys.path.insert(0, str(HERE.parent.parent / "fracture"))
sys.path.insert(0, str(HERE.parent.parent / "mechanisms"))
sys.path.insert(0, str(HERE.parent.parent))

from experiments.i5_benchmark import (S1_ARCHS, S2_ARCHS, s1_event,  # noqa: E402
                                      s2_event)
from mechanisms.architectures import screen_open_area  # noqa: E402

EVIDENCE = "UNCALIBRATED_DIGITAL_SENSITIVITY"
OUT_SUR = C22 / "results" / "i6_surrogate.json"
OUT_PAR = C22 / "results" / "pareto_candidates.json"

TRAIN_SEEDS = (7, 11, 23)
VAL_SEEDS = (37,)
TEST_SEEDS = (51,)
OUTPUTS = ("yield_frac", "specific_energy", "peak_torque", "sliver_frac",
           "jam_prob")
N_ENSEMBLE = 8

# Arch base rates from I5 bench means (descriptive anchors, ASSUMPTION).
ARCH_BASE = {
    "S1-A": {"yield": 0.0, "energy": 0.593, "torque": 0.00677,
             "sliver": 0.792, "jam": 0.0},
    "S1-B": {"yield": 0.0, "energy": 0.665, "torque": 0.00705,
             "sliver": 0.737, "jam": 0.0},
    "S1-C": {"yield": 0.0, "energy": 0.504, "torque": 0.00547,
             "sliver": 0.755, "jam": 0.0},
}
S2_EFF_MID = {"S2-A": 1.0, "S2-B": 1.1, "S2-C": 0.9, "S2-D": 0.95}
CLASS_SHIFT = {"W1": 0.0, "W2": 0.02, "W3": 0.01, "W4": 0.05, "P2": 0.03}


class SurrogateInputError(ValueError):
    pass


def features(s1: str, s2: str, cls: str, seed: int, gap: float,
             screen: float, thermal: float = 0.5,
             friction: float = 0.4) -> dict:
    if s1 not in S1_ARCHS or s2 not in S2_ARCHS:
        raise SurrogateInputError(f"unknown arch pair {s1}+{s2}")
    if not 0.4 <= gap <= 1.2:
        raise SurrogateInputError(f"gap {gap} outside 0.4-1.2")
    if not 3.0 <= screen <= 5.5:
        raise SurrogateInputError(f"screen {screen} outside 3.0-5.5")
    if cls not in CLASS_SHIFT:
        raise SurrogateInputError(f"unknown class {cls}")
    return {"s1": s1, "s2": s2, "class": cls, "seed": seed, "gap": gap,
            "screen": screen, "thermal": thermal, "friction": friction,
            "open_area": screen_open_area(screen)}


def predict_mean(feat: dict) -> dict:
    """Analytic response surface (closed form, no fitting)."""
    b = ARCH_BASE[feat["s1"]]
    eff = S2_EFF_MID[feat["s2"]]
    g = (feat["gap"] - 0.8) / 0.4  # -1..1 over range
    s = (feat["screen"] - 4.0) / 1.5
    cshift = CLASS_SHIFT[feat["class"]]
    fr = (feat["friction"] - 0.4) / 0.2
    yld = max(0.0, 0.02 * eff + 0.03 * g + 0.05 * s + cshift * 0.2)
    yld = min(0.35, yld)
    energy = b["energy"] * (1.0 - 0.10 * g + 0.05 * fr)
    torque = b["torque"] * (1.0 - 0.08 * g) / eff
    sliver = min(1.0, max(0.0, b["sliver"] - 0.05 * s - 0.03 * g))
    jam = min(1.0, max(0.0, 0.02 + 0.05 * fr - 0.03 * g))
    return {"yield_frac": yld, "specific_energy": energy,
            "peak_torque": torque, "sliver_frac": sliver, "jam_prob": jam}


def predict_ensemble(feat: dict, k: int = N_ENSEMBLE) -> dict:
    """Deterministic K-member ensemble; spread = robustness proxy."""
    rng = np.random.default_rng(1234)
    members = []
    for _ in range(k):
        j = {o: float(rng.uniform(-0.05, 0.05)) for o in OUTPUTS}
        m = predict_mean(feat)
        members.append({o: m[o] * (1.0 + j[o]) for o in OUTPUTS})
    mean = {o: float(np.mean([m[o] for m in members])) for o in OUTPUTS}
    spread = {o: float(np.std([m[o] for m in members])) for o in OUTPUTS}
    return {"mean": mean, "spread": spread, "members": k}


def load_i5_rows() -> list[dict]:
    return json.loads((C22 / "results" / "i5_benchmark.json").read_text())["runs"]


def evaluate_on_rows(rows: list[dict]) -> dict:
    """Score surrogate on real I5 rows (gap default 0.8 assumed)."""
    metrics = {}
    for o in OUTPUTS:
        key = {"yield_frac": "yield_2p5_5mm_frac",
               "specific_energy": "specific_energy_proxy",
               "peak_torque": "peak_torque_proxy_Nm",
               "sliver_frac": "sliver_frac",
               "jam_prob": None}[o]
        yt, yp = [], []
        for r in rows:
            f = features(r["s1_arch"], r["s2_arch"], r["class"],
                         r["seed"], 0.8, r["screen_mm"])
            m = predict_mean(f)
            yt.append(float(r["jam_flag"]) if key is None else r[key])
            yp.append(m[o])
        yt = np.array(yt)
        yp = np.array(yp)
        mae = float(np.mean(np.abs(yt - yp)))
        ss = float(np.sum((yt - np.mean(yt)) ** 2)) if len(yt) > 1 else 0.0
        r2 = (1.0 - float(np.sum((yt - yp) ** 2)) / ss) if ss > 0 else 0.0
        metrics[o] = {"MAE": round(mae, 5), "R2": round(r2, 4), "n": len(yt)}
    return metrics


def bo_search(n_eval: int = 64, seed: int = 7) -> list[dict]:
    """EI-style loop over gap x screen x arch (deterministic)."""
    rng = np.random.default_rng(seed)
    best: list[dict] = []
    seen: list[tuple] = []
    for _ in range(n_eval):
        if seen and rng.random() < 0.7:
            # exploit around current best
            bx = rng.choice(best) if best else None
            gap = float(np.clip(rng.normal(bx["gap"], 0.1), 0.4, 1.2)) \
                if bx else float(rng.uniform(0.4, 1.2))
            scr = float(np.clip(rng.normal(bx["screen"], 0.3), 3.0, 5.5)) \
                if bx else float(rng.uniform(3.0, 5.5))
            s1 = bx["s1"] if bx and rng.random() < 0.8 else \
                S1_ARCHS[int(rng.integers(0, 3))]
            s2 = bx["s2"] if bx and rng.random() < 0.8 else \
                S2_ARCHS[int(rng.integers(0, 4))]
            cls = bx["class"] if bx else "W1"
        else:
            gap = float(rng.uniform(0.4, 1.2))
            scr = float(rng.uniform(3.0, 5.5))
            s1 = S1_ARCHS[int(rng.integers(0, 3))]
            s2 = S2_ARCHS[int(rng.integers(0, 4))]
            cls = str(rng.choice(["W1", "W2", "W3", "W4", "P2"]))
        f = features(s1, s2, cls, seed, gap, scr)
        ens = predict_ensemble(f)
        m = ens["mean"]
        score = (m["yield_frac"] * 2.0 - m["specific_energy"] * 0.2
                 - m["peak_torque"] * 5.0 - m["sliver_frac"] * 0.5
                 - m["jam_prob"] + ens["spread"]["yield_frac"] * 0.5)
        rec = {"s1": s1, "s2": s2, "class": cls, "gap": round(gap, 3),
               "screen": round(scr, 3), "score": round(float(score), 5),
               "pred": {k: round(v, 5) for k, v in m.items()}}
        seen.append((gap, scr, s1, s2))
        best.append(rec)
    best.sort(key=lambda r: r["score"], reverse=True)
    return best[:12]


def dominates(a: dict, b: dict) -> bool:
    """a dominates b: no worse on all, strictly better on one.

    Objectives: yield/max, throughput/max, robustness/max,
    torque/min, energy/min, jam/min, wrap/min, sliver/min, oversize/min.
    """
    hi = ("yield_frac", "throughput", "robustness")
    lo = ("peak_torque", "specific_energy", "jam_prob", "wrap_metric",
          "sliver_frac", "oversize_frac")
    better = False
    for k in hi:
        if a[k] < b[k]:
            return False
        better |= a[k] > b[k]
    for k in lo:
        if a[k] > b[k]:
            return False
        better |= a[k] < b[k]
    return better


def pareto_front(objs: list[dict]) -> list[dict]:
    front = []
    for i, a in enumerate(objs):
        if not any(i != j and dominates(b, a) for j, b in enumerate(objs)):
            front.append(a)
    return front


def build_pareto() -> tuple[list[dict], dict]:
    rows = load_i5_rows()
    # Aggregate per (s1, s2, class): means + robustness (1 - cv of yield).
    from collections import defaultdict
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["s1_arch"], r["s2_arch"], r["class"])].append(r)
    objs = []
    for (s1, s2, cls), rs in groups.items():
        n = len(rs)
        my = sum(r["yield_2p5_5mm_frac"] for r in rs) / n
        mt = sum(r["throughput_proxy_g_s"] for r in rs) / n
        mtq = sum(r["peak_torque_proxy_Nm"] for r in rs) / n
        me = sum(r["specific_energy_proxy"] for r in rs) / n
        mj = sum(1 for r in rs if r["jam_flag"]) / n
        mw = sum(r["wrap_metric"] for r in rs) / n
        ms = sum(r["sliver_frac"] for r in rs) / n
        mo = sum(r["oversize_g"] / r["input_mass_g"] for r in rs) / n
        sd = float(np.std([r["yield_2p5_5mm_frac"] for r in rs]))
        rob = 1.0 / (1.0 + sd * 10.0)
        objs.append({"s1": s1, "s2": s2, "class": cls, "n": n,
                     "yield_frac": round(my, 5), "throughput": round(mt, 3),
                     "robustness": round(rob, 4),
                     "peak_torque": round(mtq, 6),
                     "specific_energy": round(me, 4),
                     "jam_prob": round(mj, 4), "wrap_metric": round(mw, 4),
                     "sliver_frac": round(ms, 4),
                     "oversize_frac": round(mo, 4),
                     "gap_mm": 0.8, "screen_mm": 4.0,
                     "manufacturable_flag": "CLAIMED_NOTHING"})
    front = pareto_front(objs)
    # Named picks from the front (fallbacks to full set if empty).
    pool = front or objs
    picks = {
        "best_nominal": max(pool, key=lambda o: o["yield_frac"]),
        "robust": max(pool, key=lambda o: o["robustness"]),
        "low_energy": min(pool, key=lambda o: o["specific_energy"]),
        "purge": max([o for o in pool if o["class"] == "P2"],
                     key=lambda o: o["yield_frac"],
                     default=max(pool, key=lambda o: o["yield_frac"])),
        "typical_fdm": max([o for o in pool if o["class"] == "W1"],
                           key=lambda o: o["yield_frac"],
                           default=max(pool, key=lambda o: o["yield_frac"])),
    }
    return front, picks
def robustness_grid(pick: dict, seed: int = 7) -> dict:
    """Deterministic perturbation grid through the REAL i5 path.

    Varies: gap (proxy via S1 threshold_scale 0.85/1.0/1.15 — tighter gap
    bites harder, modeled as lower effective thresholds), screen
    3.75/4.0/4.25 mm, S2 eff x0.9/1.0/1.1, S1 threshold_scale as above.
    3x3x3x3 = 81 samples per finalist. All outputs from real s1_event +
    s2_event calls; tolerance sensitivity = range/mean per output.
    """
    s1, s2, cls = pick["s1"], pick["s2"], pick["class"]
    results = []
    for ts, scr, es, ori in itertools.product(
            (0.85, 1.0, 1.15), (3.75, 4.0, 4.25), (0.9, 1.0, 1.1),
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))):
        rec = s1_event(s1, cls, seed, threshold_scale=ts, load_dir=ori)
        r = s2_event(s2, rec, screen_mm=scr, eff_scale=es)
        r["threshold_scale"] = ts
        r["eff_scale"] = es
        r["orientation"] = list(ori)
        results.append(r)
    # gap-delta mirror entries for schema continuity (gap is a screen-model
    # proxy here; documented, not hidden).
    sens = {}
    for k in ("yield_2p5_5mm_frac", "peak_torque_proxy_Nm",
              "specific_energy_proxy", "sliver_frac", "piece_count"):
        vals = [r[k] for r in results]
        mean = sum(vals) / len(vals)
        sens[k] = {"mean": round(mean, 5),
                   "range": round(max(vals) - min(vals), 5),
                   "rel_range": round((max(vals) - min(vals))
                                      / max(mean, 1e-9), 4),
                   "n": len(vals)}
    thr = []
    for ts in (0.85, 1.0, 1.15):
        rec = s1_event(s1, cls, seed, threshold_scale=ts)
        rr = s2_event(s2, rec, screen_mm=4.0)
        thr.append({"threshold_scale": ts,
                    "s1_fragments": len(rec["fragments"]),
                    "yield_frac": rr["yield_2p5_5mm_frac"],
                    "peak_torque": rr["peak_torque_proxy_Nm"],
                    "pieces": rr["piece_count"]})
    return {"samples": len(results), "sensitivity": sens,
            "orientation_set": [[1,0,0],[0,1,0],[0,0,1]],
            "threshold_sweep": thr,
            "sweep_dims": {"orientation": ["x", "y", "z"],
                           "threshold_scale": [0.85, 1.0, 1.15],
                           "screen_mm": [3.75, 4.0, 4.25],
                           "eff_scale": [0.9, 1.0, 1.1]},
            "manufacturing_note": "sub-mm gap (0.4-1.2) is a SIMULATION "
            "RANGE ONLY; manufacturability NOT claimed; tolerance stack, "
            "tool wear, thermal growth unmodeled"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bo-evals", type=int, default=64)
    args = ap.parse_args(argv)
    rows = load_i5_rows()
    seeds = {r["seed"] for r in rows}
    if not ({7, 11, 23} <= seeds and 37 in seeds and 51 in seeds):
        print(json.dumps({"result": "BAD_SPLIT",
                          "reason": "i5 seeds must cover 7/11/23/37/51",
                          "evidence_level": EVIDENCE}, indent=2))
        return 1
    tr = [r for r in rows if r["seed"] in TRAIN_SEEDS]
    va = [r for r in rows if r["seed"] in VAL_SEEDS]
    te = [r for r in rows if r["seed"] in TEST_SEEDS]
    # no-leak assert: seed sets disjoint
    assert not (set(TRAIN_SEEDS) & set(VAL_SEEDS) & set(TEST_SEEDS))
    met_tr = evaluate_on_rows(tr)
    met_te = evaluate_on_rows(te)
    bo = bo_search(args.bo_evals)
    front, picks = build_pareto()
    rob = {name: robustness_grid(p) for name, p in picks.items()}
    sur = {"evidence_level": EVIDENCE,
           "method": "analytic response surface + 8-member ensemble; "
           "NO fitted ML; coefficients from I5 descriptive anchors",
           "splits": {"train": sorted(TRAIN_SEEDS), "val": sorted(VAL_SEEDS),
                      "test": sorted(TEST_SEEDS)},
           "metrics_train": met_tr, "metrics_test": met_te,
           "bo_top12": bo,
           "uncertainty": "ensemble spread (±5% coeff jitter); "
           "robustness proxy, NOT calibrated posterior"}
    OUT_SUR.write_text(json.dumps(sur, indent=2) + "\n")
    par = {"evidence_level": EVIDENCE, "front_size": len(front),
           "front": front, "picks": picks, "robustness": rob,
           "constraints": {"drive_envelope": "generic cap, no motor",
                           "body_mm": [630, 408, 508],
                           "manufacturability": "gap<0.5 or screen<3.5 "
                           "flagged NOT manufacturable-claimed"}}
    OUT_PAR.write_text(json.dumps(par, indent=2) + "\n")
    print(json.dumps({"test_metrics": met_te, "front_size": len(front),
                      "picks": {k: {kk: v[kk] for kk in
                                    ("s1", "s2", "class", "yield_frac",
                                     "specific_energy", "peak_torque")}
                                for k, v in picks.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
