"""I3 single-event fracture smoke benchmark (Isaac-independent, numpy-only).

12 combos: classes W1/W2/W3/W4 x orientations 0/45/90 deg. One shear edge
(unit probe in the specimen XY plane) + one FDM coupon (I2 lattice rebuilt
from waste_gen metadata). Idealized edge load via BondManager; outputs per
run: peak contact-force proxy, work proxy, bond failures, failure
orientation, fragment count, mass conservation error, stability flag.

P0/P1 strand bundles are REFUSED (wrap-only, NO fracture claim).

Fails loudly (exit 1) on: mass error > 1e-6 g, NaN/non-finite peak or work,
INTACT-with-bonds paradox, COM outside specimen AABB (tunneling guard), or
nonphysical class ordering (fixed-lattice probe: W4 >= W3 >= W2 >= W1 peak
at every orientation, W1 Z-first under z-load).

Evidence: UNCALIBRATED_FRACTURE. Peak/work are nominal ordering proxies,
NEVER calibrated force/energy predictions. Zero physical tests.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
C22 = HERE.parents[2]
sys.path.insert(0, str(HERE.parent.parent / "generators"))
sys.path.insert(0, str(HERE.parent.parent / "fracture"))

from waste_gen import generate  # noqa: E402
from bond_manager import (BondManager, FractureInputError, NonphysicalError,  # noqa: E402
                          graph_from_meta)

EVIDENCE = "UNCALIBRATED_FRACTURE"
MASS_TOL_G = 1e-6
CLASSES = ("W1", "W2", "W3", "W4")
ORIENTATIONS_DEG = (0, 45, 90)
SEED = 7
OUT_DIR = C22 / "results" / "i3_coupons"
SUMMARY = C22 / "results" / "i3_summary.json"


class WrapOnlyError(RuntimeError):
    """P0/P1 strand bundles carry no fracture claim (wrap risk only)."""


class OrderingError(RuntimeError):
    """Nominal class ordering violated — nonphysical configuration."""


def load_dir_for(deg: float) -> tuple[float, float, float]:
    a = math.radians(deg)
    return (math.cos(a), math.sin(a), 0.0)


def run_combo(cls: str, deg: float, seed: int = SEED) -> dict:
    if cls in ("P0", "P1"):
        raise WrapOnlyError(
            f"class {cls} is wrap-risk only; fracture coupons refused")
    meta = generate(cls, seed)
    graph = graph_from_meta(meta)
    bm = BondManager(graph, seed, meta["solid_fraction"])
    direction = load_dir_for(deg)
    res = bm.run_event(direction)
    if res.peak_load_proxy is not None and not math.isfinite(
            res.peak_load_proxy):
        raise NonphysicalError("non-finite peak")
    if not math.isfinite(res.work_proxy) or math.isnan(res.work_proxy):
        raise NonphysicalError("NaN work")
    if res.mass_error_g > MASS_TOL_G:
        raise NonphysicalError(f"mass error {res.mass_error_g} > {MASS_TOL_G}")
    if res.peak_load_proxy is None and res.n_bonds_total > 0:
        raise NonphysicalError("INTACT result despite breakable bonds")
    # Tunneling guard: every fragment COM must lie inside the specimen AABB.
    d = meta["dims_mm"]
    com_ok = all(0.0 <= f.com_mm[0] <= d["dx"]
                 and 0.0 <= f.com_mm[1] <= d["dy"]
                 and 0.0 <= f.com_mm[2] <= d["dz"] for f in res.fragments)
    if not com_ok:
        raise NonphysicalError("fragment COM outside specimen AABB")
    nfrag = len(res.fragments)
    stability = ("CLEAN_SPLIT" if nfrag == 2 else
                 "MULTI_FRAGMENT" if nfrag > 2 else "INTACT")
    return {
        "run_id": f"I3-{cls}-{int(deg):03d}-s{seed:05d}",
        "object_id": meta["object_id"], "class": cls,
        "orientation_deg": deg, "seed": seed,
        "load_dir": list(direction),
        "dims_mm": meta["dims_mm"], "mass_g": meta["mass_g"],
        "solid_fraction": meta["solid_fraction"],
        "cells": len(graph.cells), "bonds_total": res.n_bonds_total,
        "peak_proxy": res.peak_load_proxy,
        "work_proxy": res.work_proxy,
        "bonds_failed": len(res.failed_bond_indices),
        "first_failure_kind": res.first_failure_kind,
        "fragments": nfrag,
        "fragment_masses_g": [round(f.mass_g, 6) for f in res.fragments],
        "mass_error_g": res.mass_error_g,
        "stability": stability,
        "evidence_level": EVIDENCE,
    }


def check_ordering(seed: int = SEED) -> dict:
    """Fixed-lattice probe: identical geometry+seed, class strengths vary.

    Elementwise W4 >= W3 >= W2 >= W1 thresholds (same jitter) imply
    peak_W4 >= peak_W3 >= peak_W2 >= peak_W1 at every orientation; W1
    under z-load must fail inter_layer_z first. Violations are
    nonphysical -> OrderingError.
    """
    from bonds import lattice_graph, strengths_for_class  # noqa: E402

    probe: dict[str, dict[str, float]] = {}
    for deg in ORIENTATIONS_DEG:
        peaks: dict[str, float] = {}
        for cls in CLASSES:
            g = lattice_graph(6, 5, 4, 60.0, 50.0, 20.0, 50.0,
                              strengths_for_class(cls))
            bm = BondManager(g, seed, 0.5)
            r = bm.run_event(load_dir_for(deg))
            if r.peak_load_proxy is None:
                raise OrderingError(f"{cls}/{deg}: unexpected INTACT")
            peaks[cls] = r.peak_load_proxy
        chain = [peaks[c] for c in CLASSES]
        if not all(b >= a for a, b in zip(chain, chain[1:])):
            raise OrderingError(f"orientation {deg}: peak chain {peaks} "
                                "violates W4>=W3>=W2>=W1")
        probe[str(deg)] = peaks
    gz = lattice_graph(6, 5, 4, 60.0, 50.0, 20.0, 50.0,
                       strengths_for_class("W1"))
    rz = BondManager(gz, seed, 0.5).run_event((0.0, 0.0, 1.0))
    if rz.first_failure_kind != "inter_layer_z":
        raise OrderingError(
            f"W1 z-load first failure {rz.first_failure_kind}, "
            "expected inter_layer_z")
    probe["W1_z_first"] = rz.first_failure_kind
    return probe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        ordering = check_ordering(args.seed)
    except OrderingError as exc:
        print(json.dumps({"result": "NONPHYSICAL_ORDERING",
                          "reason": str(exc),
                          "evidence_level": EVIDENCE}, indent=2))
        return 1
    runs: list[dict] = []
    try:
        for cls in CLASSES:
            for deg in ORIENTATIONS_DEG:
                rec = run_combo(cls, deg, args.seed)
                (out / f"{rec['run_id']}.json").write_text(
                    json.dumps(rec, indent=2) + "\n")
                runs.append(rec)
    except (NonphysicalError, FractureInputError, WrapOnlyError) as exc:
        print(json.dumps({"result": "FAILED",
                          "reason": f"{type(exc).__name__}: {exc}",
                          "completed_runs": len(runs),
                          "evidence_level": EVIDENCE}, indent=2))
        return 1
    summary = {"evidence_level": EVIDENCE, "seed": args.seed,
               "combos": len(runs), "ordering_probe": ordering,
               "runs": [{k: r[k] for k in
                         ("run_id", "class", "orientation_deg", "peak_proxy",
                          "work_proxy", "bonds_failed", "first_failure_kind",
                          "fragments", "mass_error_g", "stability")}
                        for r in runs]}
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
