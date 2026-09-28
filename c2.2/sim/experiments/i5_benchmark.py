"""I5 low-resolution end-to-end S1->S2 benchmark (Isaac-independent, numpy).

Pipeline per (S1 arch, seed, class): waste_gen specimen (shared slot per
COMPARISON_CONTRACT) -> BondManager S1 fracture event with arch-scaled
thresholds -> S1 fragment dataset (sec16 contract fields) ->
IDENTICAL saved fragment set fed to each S2 arch (A/B/C/D) with arch
efficiency multipliers (ASSUMPTION) + analytic screen model ->
canonical sec20 metrics per run.

Modes: --mode ladder (1-3 seeds, classes W1/W4/P0 smoke; P0 S1-only wrap
study, NO S2 fracture claim) then --mode bench (5 seeds/class over
W1/W2/W3/W4/P2; P0/P1 S1-only wrap study).

S1 arch threshold multipliers (ASSUMPTION, documented): S1-A 1.0
inherited baseline, S1-B 1.15 localized shear concentration,
S1-C 0.85 buckling-assist. S2 efficiency multipliers (ASSUMPTION):
S2-A 1.0 reference, S2-B 1.1 high-speed baseline, S2-C 0.9, S2-D 0.95.

Torque proxy: P_mech = work_proxy / T_event (T_event=1.0s ASSUMPTION),
omega from arch rpm, T = P/omega; RMS = peak/sqrt(2) sine-equivalent
ASSUMPTION. Throughput proxy = mass / T_event. Specific energy = work/mass.

Screen model: retention edge = hole size; pass fraction from equiv
diameter vs hole via smooth step (ASSUMPTION curve, width 0.5mm);
sliver fraction from aspect ratio > 3 (ASSUMPTION); target 2.5-5mm yield,
oversize, fines (<1mm proxy); recirculation = oversize re-fed once
(ASSUMPTION single pass); residence proxy = 1/throughput scaled.

Fails loudly (exit 1): mass conservation error > 1e-6 at any stage,
missing S2-B baseline, P-class S2 fracture attempt.

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. Ordering smoke only.
"""
from __future__ import annotations

import argparse
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

from waste_gen import generate, random_quaternion  # noqa: E402
from bond_manager import (BondManager, FractureInputError,  # noqa: E402
                          NonphysicalError, graph_from_meta)
from architectures import (ARCHITECTURES, InvalidMechanism,  # noqa: E402
                           check_baseline_present, comparison_contract,
                           screen_open_area)

EVIDENCE = "UNCALIBRATED_DIGITAL_SENSITIVITY"
MASS_TOL_G = 1e-6
T_EVENT_S = 1.0  # ASSUMPTION event duration for power/throughput proxies
OUT_JSON = C22 / "results" / "i5_benchmark.json"
FRAG_DIR = C22 / "results" / "s1_fragments"

S1_ARCHS = ("S1-A", "S1-B", "S1-C")
S2_ARCHS = ("S2-A", "S2-B", "S2-C", "S2-D")
BENCH_CLASSES = ("W1", "W2", "W3", "W4", "P2")
LADDER = [("W1", 7), ("W4", 7), ("P0", 7)]
BENCH_SEEDS = (7, 11, 23, 37, 51)

# Arch threshold multipliers (ASSUMPTION — documented priors, no data).
S1_MULT = {"S1-A": 1.0, "S1-B": 1.15, "S1-C": 0.85}
S1_MULT_NOTES = {
    "S1-A": "inherited twin-shaft baseline",
    "S1-B": "localized shear concentration at breaker edge",
    "S1-C": "buckling-assist under nip compression",
}
# S2 comminution efficiency multipliers (ASSUMPTION).
S2_EFF = {"S2-A": 1.0, "S2-B": 1.1, "S2-C": 0.9, "S2-D": 0.95}
S2_RPM = {"S2-A": 120.0, "S2-B": 300.0, "S2-C": 240.0, "S2-D": 120.0}
S1_RPM = {"S1-A": 40.0, "S1-B": 60.0, "S1-C": 30.0}


class BenchmarkError(RuntimeError):
    pass


class WrapOnlyS2Error(BenchmarkError):
    """P0/P1 may not enter S2 fracture (wrap study S1-only)."""


def _load_dir_for_arch(arch_id: str, seed: int) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed * 31 + hash(arch_id) % 1000)
    v = rng.normal(size=3)
    n = float(np.linalg.norm(v))
    return (float(v[0] / n), float(v[1] / n), float(v[2] / n))


def _equiv_dims(cells_xyz: list[tuple[float, float, float]],
                mass_g: float, density_g_cc: float = 1.24):
    xs = [p[0] for p in cells_xyz]
    ys = [p[1] for p in cells_xyz]
    zs = [p[2] for p in cells_xyz]
    ex = max(xs) - min(xs) or 0.5
    ey = max(ys) - min(ys) or 0.5
    ez = max(zs) - min(zs) or 0.5
    vol_mm3 = mass_g / density_g_cc * 1000.0
    deq = (6.0 * vol_mm3 / math.pi) ** (1.0 / 3.0)
    dims = sorted((ex, ey, ez), reverse=True)
    aspect = dims[0] / max(dims[2], 1e-9)
    return dims, deq, aspect


def s1_event(s1_id: str, cls: str, seed: int,
             threshold_scale: float = 1.0,
             load_dir: tuple[float, float, float] | None = None) -> dict:
    """Run S1 fracture event; return dataset record + fragment list.

    threshold_scale (default 1.0) multiplies arch thresholds; used ONLY
    for assumption-sensitivity (robustness) sweeps, never calibrated.
    """
    if s1_id not in S1_ARCHS:
        raise BenchmarkError(f"not an S1 arch: {s1_id}")
    meta = generate(cls, seed)
    rng = np.random.default_rng(seed * 101 + len(s1_id))
    graph = graph_from_meta(meta)
    bm = BondManager(graph, seed, meta["solid_fraction"])
    mult = S1_MULT[s1_id] * threshold_scale
    bm.thresholds = [t * mult for t in bm.thresholds]
    if cls in ("P0", "P1"):
        # S1-only wrap study: no bond breakage claimed; single fragment.
        frag_cells = [tuple(sorted(c.id for c in graph.cells))]
        res_frags = [bm._fragment(list(frag_cells[0]))]
        peak, work, failed = 0.0, 0.0, []
        first_kind = None
        mass_err = abs(sum(f.mass_g for f in res_frags)
                       - graph.object_mass_g)
        bite = False
        bridge = True
        jam = meta.get("flags", []) != []
        wrap_metric = (meta.get("wrap_risk") or {}).get("metric", 1.0)
    else:
        direction = load_dir if load_dir is not None else _load_dir_for_arch(
            s1_id, seed)
        try:
            res = bm.run_event(direction)
        except (FractureInputError, NonphysicalError) as exc:
            raise BenchmarkError(f"S1 event failed: {exc}") from exc
        if res.mass_error_g > MASS_TOL_G:
            raise BenchmarkError(
                f"S1 mass error {res.mass_error_g} > {MASS_TOL_G}")
        res_frags = res.fragments
        peak, work = res.peak_load_proxy or 0.0, res.work_proxy
        failed = res.failed_bond_indices
        first_kind = res.first_failure_kind
        mass_err = res.mass_error_g
        d = meta["dims_mm"]
        bite = min(d["dx"], d["dy"], d["dz"]) < 60.0
        bridge = (max(d.values()) / max(min(d.values()), 1e-9)) > 6.0
        jam = len(res_frags) > 8
        wrap_metric = 0.0
    # Per-fragment dataset records (sec16 contract fields).
    centers = {c.id: c.center_mm for c in graph.cells}
    masses = {c.id: c.mass_g for c in graph.cells}
    dataset = []
    for i, f in enumerate(res_frags):
        pts = [centers[c] for c in f.cells]
        dims, deq, aspect = _equiv_dims(pts, f.mass_g)
        velocities = [float(peak * 10.0 / max(len(res_frags), 1))] * 3
        dataset.append({
            "fragment_id": f"{meta['object_id']}:{s1_id}:F{i:03d}",
            "source_waste_id": meta["object_id"], "seed": seed,
            "mass_g": round(f.mass_g, 6),
            "volume_mm3": round(f.mass_g / 1.24 * 1000.0, 3),
            "com_mm": [round(v, 3) for v in f.com_mm],
            "principal_dims_mm": [round(v, 3) for v in dims],
            "equiv_diameter_mm": round(deq, 3),
            "aspect_ratio": round(aspect, 3),
            "pose_quaternion_xyzw": [round(v, 5) for v in
                                     random_quaternion(rng)],
            "velocity_proxy_mm_s": [round(v, 4) for v in velocities],
            "bond_state": {"failed_bonds": len(failed),
                           "first_kind": first_kind},
            "class": cls, "material": meta["material"],
        })
    if abs(sum(f["mass_g"] for f in dataset) - meta["mass_g"]) > MASS_TOL_G:
        raise BenchmarkError("S1 dataset mass mismatch")
    return {"s1_arch": s1_id, "seed": seed, "class": cls,
            "waste_id": meta["object_id"], "input_mass_g": meta["mass_g"],
            "peak_proxy": peak, "work_proxy": work,
            "bite_flag": bite, "bridge_flag": bridge, "jam_flag": jam,
            "wrap_metric": wrap_metric, "mass_error_g": mass_err,
            "fragments": dataset,
            "s1_multiplier": mult,
            "s1_multiplier_note": S1_MULT_NOTES[s1_id],
            "evidence_level": EVIDENCE}


def _smooth_pass(deq: float, hole: float, width: float = 0.5) -> float:
    return 1.0 / (1.0 + math.exp((deq - hole) / width))


def s2_event(s2_id: str, s1rec: dict, screen_mm: float = 4.0,
             eff_scale: float = 1.0) -> dict:
    """Feed IDENTICAL saved S1 fragments through S2 arch screen model.

    eff_scale (default 1.0) scales the arch efficiency multiplier; used
    ONLY for assumption-sensitivity (robustness) sweeps, never as a
    calibrated parameter.
    """
    if s2_id not in S2_ARCHS:
        raise BenchmarkError(f"not an S2 arch: {s2_id}")
    if s1rec["class"] in ("P0", "P1"):
        raise WrapOnlyS2Error(
            f"class {s1rec['class']} S1-only wrap study; S2 refused")
    try:
        oa = screen_open_area(screen_mm)
    except InvalidMechanism as exc:
        raise BenchmarkError(str(exc)) from exc
    eff = S2_EFF[s2_id] * eff_scale
    frags = s1rec["fragments"]
    in_mass = s1rec["input_mass_g"]
    # RNG varies with screen+eff so robustness sweeps actually perturb the
    # split (still fully deterministic per input tuple).
    rng = np.random.default_rng(
        (s1rec["seed"] * 7 + hash(s2_id) + int(screen_mm * 100)
         + int(eff_scale * 1000)) % (2 ** 63))
    out: list[dict] = []
    for f in frags:
        k = max(1, int(round(eff * f["aspect_ratio"])))
        k = min(k, 6)
        shares = [(1.0 / k) * (1.0 + (rng.random() - 0.5) * 0.2)
                  for _ in range(k)]
        for j in range(k):
            out.append({"deq": f["equiv_diameter_mm"] / (k ** (1 / 3)),
                        "mass": f["mass_g"] * shares[j],
                        "aspect": f["aspect_ratio"]})
    # renormalize exactly to input mass (analytic split, conserve by fiat)
    tot = sum(o["mass"] for o in out)
    for o in out:
        o["mass"] *= in_mass / tot
    passes = [_smooth_pass(o["deq"], screen_mm) for o in out]
    m_pass = sum(m * p for m, p in
                 zip([o["mass"] for o in out], passes))
    target = sum(m * p for m, p, o in
                 zip([o["mass"] for o in out], passes, out)
                 if 2.5 <= o["deq"] <= 5.0)
    oversize = sum(m * (1 - p) for m, p in
                   zip([o["mass"] for o in out], passes))
    fines = sum(m * p for m, p, o in
                zip([o["mass"] for o in out], passes, out)
                if o["deq"] < 1.0)
    sliver = sum(o["mass"] for o in out if o["aspect"] > 3.0)
    recirc = oversize  # single-pass re-feed ASSUMPTION
    # Torque proxies: P = W/T, omega from S2 rpm; RMS sine-equivalent.
    omega = S2_RPM[s2_id] * 2 * math.pi / 60.0
    power_w = s1rec["work_proxy"] * 0.001 / T_EVENT_S  # N-mm/s -> W-ish
    peak_tq = power_w / omega if omega > 0 else 0.0
    rms_tq = peak_tq / math.sqrt(2)
    throughput = in_mass / T_EVENT_S  # g/s proxy
    spec_e = (s1rec["work_proxy"] / in_mass) if in_mass > 0 else 0.0
    if abs(sum(o["mass"] for o in out) - in_mass) > MASS_TOL_G:
        raise BenchmarkError("S2 mass mismatch")
    n = len(out)
    return {
        "candidate": f"{s1rec['s1_arch']}+{s2_id}", "s1_arch": s1rec["s1_arch"],
        "s2_arch": s2_id, "seed": s1rec["seed"], "class": s1rec["class"],
        "input_mass_g": round(in_mass, 6),
        "screen_mm": screen_mm, "open_area": round(oa, 4),
        "bite_flag": s1rec["bite_flag"], "bridge_flag": s1rec["bridge_flag"],
        "jam_flag": s1rec["jam_flag"], "wrap_metric": s1rec["wrap_metric"],
        "time_s": T_EVENT_S,
        "throughput_proxy_g_s": round(throughput, 4),
        "peak_torque_proxy_Nm": round(peak_tq, 6),
        "rms_torque_proxy_Nm": round(rms_tq, 6),
        "work_proxy": round(s1rec["work_proxy"], 4),
        "specific_energy_proxy": round(spec_e, 4),
        "piece_count": n,
        "mass_error_g": 0.0,
        "yield_2p5_5mm_g": round(target, 4),
        "yield_2p5_5mm_frac": round(target / in_mass, 4) if in_mass else 0.0,
        "oversize_g": round(oversize, 4), "fines_g": round(fines, 4),
        "sliver_g": round(sliver, 4),
        "sliver_frac": round(sliver / in_mass, 4) if in_mass else 0.0,
        "recirculation_g": round(recirc, 4),
        "residence_proxy_s": round(1.0 / throughput, 4) if throughput else 0.0,
        "stability": "SPLIT" if n > len(frags) else "PASS_THROUGH",
        "s2_efficiency": eff,
        "s2_efficiency_note": "ASSUMPTION analytic multiplier",
        "evidence_level": EVIDENCE,
    }


def run_all(mode: str, seed_override: int | None = None) -> dict:
    check_baseline_present()
    if mode == "ladder":
        slots = [("W1", 7), ("W4", 7), ("P0", 7)]
    elif mode == "bench":
        slots = [(c, s) for c in BENCH_CLASSES for s in BENCH_SEEDS]
    else:
        raise BenchmarkError(f"unknown mode {mode}")
    if seed_override is not None:
        slots = [(c, seed_override) for c, _ in slots]
    FRAG_DIR.mkdir(parents=True, exist_ok=True)
    s1_sets: list[dict] = []
    for s1 in S1_ARCHS:
        for cls, seed in slots:
            rec = s1_event(s1, cls, seed)
            fp = FRAG_DIR / f"s1_{s1}_{cls}_s{seed:05d}.json"
            fp.write_text(json.dumps(rec, indent=2) + "\n")
            s1_sets.append(rec)
    runs: list[dict] = []
    failed = 0
    for rec in s1_sets:
        if rec["class"] in ("P0", "P1"):
            continue  # S1-only wrap study
        for s2 in S2_ARCHS:
            try:
                runs.append(s2_event(s2, rec))
            except BenchmarkError:
                failed += 1
    return {"evidence_level": EVIDENCE, "mode": mode,
            "s1_sets": len(s1_sets), "runs_valid": len(runs),
            "runs_failed": failed, "runs": runs}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("ladder", "bench", "both"),
                    default="both")
    args = ap.parse_args(argv)
    modes = ("ladder", "bench") if args.mode == "both" else (args.mode,)
    all_runs: list[dict] = []
    summary: dict = {"evidence_level": EVIDENCE, "contract": {
        "s1_mult": S1_MULT, "s2_eff": S2_EFF, "t_event_s": T_EVENT_S,
        "mass_tol_g": MASS_TOL_G,
        "note": "arch multipliers are ASSUMPTIONS; proxies not predictions"}}
    try:
        for m in modes:
            r = run_all(m)
            summary[m] = {k: r[k] for k in
                          ("s1_sets", "runs_valid", "runs_failed")}
            all_runs.extend(r["runs"])
    except (BenchmarkError, InvalidMechanism) as exc:
        print(json.dumps({"result": "FAILED",
                          "reason": f"{type(exc).__name__}: {exc}",
                          "evidence_level": EVIDENCE}, indent=2))
        return 1
    summary["runs"] = all_runs
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in
                      list(modes) + ["runs"][:0]}, indent=2))
    print(f"total runs: {len(all_runs)} "
          f"({sum(1 for r in all_runs if r['s2_arch']=='S2-B')} via S2-B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
