"""I4 cheap geometric/kinematic screening (Isaac-independent, numpy LHS).

Samples N candidates (default 300, range 200-500): architecture, waste
class, gap_mm (0.4-1.2), screen_mm (3.0-5.5), specimen AABB, arch-specific
params. Gates (all geometric/kinematic, no physics):

1. hopper admissibility (c2.2/configs box)
2. capture pocket fit (specimen min-dim < pocket opening; max-dim > 25% of
   pocket so it is not a pass-through fine)
3. screen open-area fraction within [0.01, 0.30]
4. mechanism ratio sanity (sampled values inside arch ranges)
5. gap/screen range sanity (inside 0.4-1.2 / 3.0-5.5)

Flags (recorded, not fatal): bridging risk, wrap risk (P0/P1), dead-zone
fraction (arch prior, ASSUMPTION).

Fails loudly (exit 1): invalid mechanism (zero clearance, S2-A direction
sign != -1, S2-B baseline missing), zero survivors is a WARNING not fatal
(exit 0 with empty survivors + reason).

Evidence: UNCALIBRATED_DIGITAL_SENSITIVITY. Screening prunes geometry;
it predicts no throughput, torque, yield, or jam.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
C22 = HERE.parents[2]
sys.path.insert(0, str(HERE.parent.parent / "mechanisms"))
sys.path.insert(0, str(HERE.parent.parent / "generators"))

from architectures import (ARCHITECTURES, InvalidMechanism,  # noqa: E402
                           check_baseline_present, check_clearance,
                           check_direction, screen_open_area)

EVIDENCE = "UNCALIBRATED_DIGITAL_SENSITIVITY"
OUT = C22 / "results" / "i4_screen.json"

_ADM = json.loads((C22 / "configs" / "hopper_admissibility.json").read_text())
BOX = [float(v) for v in
       _ADM["max_admissible_bounding_dims_mm"].values()]

GAP_RANGE = (0.4, 1.2)
SCREEN_RANGE = (3.0, 5.5)
OPEN_AREA_RANGE = (0.01, 0.30)
WASTE_CLASSES = ("W1", "W2", "W3", "W4", "P0", "P1", "P2")

# Capture pocket opening per arch (mm, ASSUMPTION geometric priors):
# twin-shaft nip ~ shaft_center - tip/2 ... use nominal openings.
POCKET_OPENING = {
    "S1-A": 60.0, "S1-B": 55.0, "S1-C": 40.0,
    "S2-A": 45.6, "S2-B": 50.0, "S2-C": 35.0, "S2-D": 45.0,
}
# Dead-zone volume fraction prior per arch (ASSUMPTION, recorded only).
DEAD_ZONE = {
    "S1-A": 0.10, "S1-B": 0.15, "S1-C": 0.12,
    "S2-A": 0.08, "S2-B": 0.05, "S2-C": 0.18, "S2-D": 0.12,
}
# Family footprint ranges shared with waste_gen (dx,dy,dz mm).
FOOTPRINT = {
    "dx": (30.0, 140.0), "dy": (25.0, 120.0), "dz": (4.0, 57.0),
}


class ScreenInputError(ValueError):
    pass


def validate_mechanisms() -> None:
    check_baseline_present()
    for a in ARCHITECTURES.values():
        check_clearance(a)
        check_direction(a)


def lhs(n: int, dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cut = (np.arange(n)[:, None] + rng.random((n, dim))) / n
    for j in range(dim):
        rng.shuffle(cut[:, j])
    return cut


def sample_candidates(n: int, seed: int) -> list[dict]:
    if not 200 <= n <= 500:
        raise ScreenInputError(f"n={n} outside 200-500 screening window")
    ids = sorted(ARCHITECTURES)
    u = lhs(n, 8, seed)
    cands = []
    for i in range(n):
        arch = ARCHITECTURES[ids[int(u[i, 0] * len(ids)) % len(ids)]]
        cls = WASTE_CLASSES[int(u[i, 1] * len(WASTE_CLASSES)) % len(WASTE_CLASSES)]
        gap = GAP_RANGE[0] + u[i, 2] * (GAP_RANGE[1] - GAP_RANGE[0])
        screen = SCREEN_RANGE[0] + u[i, 3] * (SCREEN_RANGE[1] - SCREEN_RANGE[0])
        dx = FOOTPRINT["dx"][0] + u[i, 4] * (FOOTPRINT["dx"][1] - FOOTPRINT["dx"][0])
        dy = FOOTPRINT["dy"][0] + u[i, 5] * (FOOTPRINT["dy"][1] - FOOTPRINT["dy"][0])
        dz = FOOTPRINT["dz"][0] + u[i, 6] * (FOOTPRINT["dz"][1] - FOOTPRINT["dz"][0])
        # arch-specific sampled param (first non-gap/screen range key)
        extra_name, extra_val = None, None
        for k, (lo, hi) in arch.ranges.items():
            if k in ("gap_mm", "screen_mm"):
                continue
            extra_name = k
            if isinstance(lo, int) and isinstance(hi, int):
                extra_val = int(lo + u[i, 7] * (hi - lo + 1))
                extra_val = min(extra_val, hi)
            else:
                extra_val = float(lo + u[i, 7] * (hi - lo))
            break
        cands.append({"cand_id": f"I4-{i:04d}", "arch": arch.id,
                      "class": cls, "gap_mm": round(float(gap), 3),
                      "screen_mm": round(float(screen), 3),
                      "dims_mm": {"dx": round(float(dx), 2),
                                  "dy": round(float(dy), 2),
                                  "dz": round(float(dz), 2)},
                      "extra": {extra_name: extra_val} if extra_name else {}})
    return cands


def screen_candidate(c: dict) -> dict:
    arch = ARCHITECTURES[c["arch"]]
    gates: dict[str, bool] = {}
    d = c["dims_mm"]
    gates["hopper"] = (d["dx"] <= BOX[0] and d["dy"] <= BOX[1]
                       and d["dz"] <= BOX[2])
    pocket = POCKET_OPENING[arch.id]
    mind, maxd = min(d["dx"], d["dy"], d["dz"]), max(d["dx"], d["dy"], d["dz"])
    gates["pocket"] = (mind < pocket) and (maxd > 0.25 * pocket)
    try:
        oa = screen_open_area(c["screen_mm"])
    except InvalidMechanism:
        oa = float("nan")
    import math
    gates["open_area"] = (math.isfinite(oa) and OPEN_AREA_RANGE[0] <= oa
                          <= OPEN_AREA_RANGE[1])
    gates["ranges"] = (GAP_RANGE[0] <= c["gap_mm"] <= GAP_RANGE[1]
                       and SCREEN_RANGE[0] <= c["screen_mm"]
                       <= SCREEN_RANGE[1])
    aspect = maxd / max(mind, 1e-9)
    bridging = (aspect > 6.0) or (c["class"] == "W1" and aspect > 4.0)
    wrap = c["class"] in ("P0", "P1")
    survived = all(gates.values())
    return {"cand_id": c["cand_id"], "arch": c["arch"], "class": c["class"],
            "gap_mm": c["gap_mm"], "screen_mm": c["screen_mm"],
            "dims_mm": d, "extra": c["extra"],
            "gates": gates, "survived": survived,
            "open_area": round(oa, 4) if oa == oa else None,
            "dead_zone_prior": DEAD_ZONE[arch.id],
            "flags": {"bridging_risk": bool(bridging),
                      "wrap_risk": bool(wrap)},
            "evidence_level": EVIDENCE}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    try:
        validate_mechanisms()
    except InvalidMechanism as exc:
        print(json.dumps({"result": "INVALID_MECHANISM",
                          "reason": str(exc),
                          "evidence_level": EVIDENCE}, indent=2))
        return 1
    try:
        cands = sample_candidates(args.n, args.seed)
    except ScreenInputError as exc:
        print(json.dumps({"result": "BAD_INPUT", "reason": str(exc),
                          "evidence_level": EVIDENCE}, indent=2))
        return 1
    screened = [screen_candidate(c) for c in cands]
    surv = [s["cand_id"] for s in screened if s["survived"]]
    by_arch: dict[str, dict[str, int]] = {}
    for s in screened:
        b = by_arch.setdefault(s["arch"], {"n": 0, "survivors": 0})
        b["n"] += 1
        b["survivors"] += int(s["survived"])
    result = {"evidence_level": EVIDENCE, "seed": args.seed,
              "candidates": len(screened), "survivors": len(surv),
              "survivor_ids": surv, "by_arch": by_arch,
              "contracts": {
                  "hopper_box_mm": BOX,
                  "gap_range_mm": list(GAP_RANGE),
                  "screen_range_mm": list(SCREEN_RANGE),
                  "open_area_range": list(OPEN_AREA_RANGE)},
              "screened": screened}
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("candidates", "survivors", "by_arch",
                       "survivor_ids")}, indent=2))
    if not surv:
        print("WARNING: zero survivors (geometry too strict?)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
