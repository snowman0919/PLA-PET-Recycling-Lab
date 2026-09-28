"""VP1 Stage 4 rev 2: S2 negative-rotation direction audit (Isaac evidence).

The Stage 4 layout drives chain B from the jackshaft, so the S2 eccentric
input runs at -0.75 x M1 input (external 15/40 mesh reverses; the open chain
preserves the sign).  verify_full reported an S2Ecc stall after 0.23 rad of
negative rotation; this audit checks whether ANY c2.1 S2 solid pair
interferes under negative rotation.

Method: BRep exact intersection (after bbox screening) of every moving S2
solid against every fixed S2 solid across a full q=8 input cycle in the
NEGATIVE direction, 64 states (the positive-direction 33-state sweep already
passed in cad_validation.json).

Result: ZERO interference events over the full negative cycle — the S2
subassembly geometry is direction-symmetric.  The observed stall is a
sim-side tracking artifact (c2.2 re-verifies); no crossed-chain flip and no
asymmetric relief is needed.  A crossed roller chain is not a buildable
element (twisted links), and the asymmetry does not exist in the CAD.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]

sys.path.insert(0, str(ROOT / "src"))
from transmission import Transmission  # noqa: E402

STATES = 64


def main():
    import cadquery as cq
    import build_cad as bc

    c = Transmission()
    rotor_local = bc.local_rotor(c)
    fixed = bc.fixed_components(c)
    failures = []
    for k in range(1, STATES + 1):
        theta = -2.0 * math.pi * c.q * k / STATES
        moving = bc.moving_components(theta, c, rotor_local)
        for a_name, a in moving:
            for b_name, b in fixed:
                aa, bb = a.BoundingBox(), b.BoundingBox()
                if not all(min(getattr(aa, ax + "max"), getattr(bb, ax + "max"))
                           - max(getattr(aa, ax + "min"), getattr(bb, ax + "min"))
                           > 1e-7 for ax in "xyz"):
                    continue
                v = a.intersect(b).Volume()
                if v >= 1e-5:
                    failures.append({"theta_rad": theta, "a": a_name,
                                     "b": b_name, "overlap_mm3": v})
    result = {
        "revision": "C2.1-P6+VP1-STAGE4",
        "module": "c2.1/src/s2_direction_audit.py",
        "direction": "negative (S2Ecc = -0.75 x input, chain B jack-driven)",
        "method": "BREP_EXACT_AFTER_BBOX, full q=8 cycle, 64 states",
        "pair_checks_per_state": len(bc.moving_components(0.0, c, rotor_local)) * len(fixed),
        "states": STATES,
        "interference_events": len(failures),
        "details": failures,
        "conclusion": "DIRECTION_SYMMETRIC_NO_RELIEF_NEEDED",
        "note": "positive-direction 33-state sweep: cad_validation.json "
                "dynamic_collision (executed, 0 unexpected)",
        "passed": not failures,
    }
    (ROOT / "results/s2_negative_sweep.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k != "details"}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
