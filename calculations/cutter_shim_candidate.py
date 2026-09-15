#!/usr/bin/env python3
"""12 disc 교차 스택의 순차 metal-shim 조립 후보. 출시 형상/실측 인증 아님."""
import hashlib
import json
import math
import random
from pathlib import Path


def assemble(thicknesses, spacers, measurement_errors=None, shim_errors=None):
    measurement_errors = [0.] * 11 if measurement_errors is None else measurement_errors
    shim_errors = [0.] * 10 if shim_errors is None else shim_errors
    assert len(thicknesses) == 12 and len(spacers) == 10
    assert len(measurement_errors) == 11 and len(shim_errors) == 10
    assert all(abs(e) <= .01 for e in measurement_errors) and all(abs(e) <= .005 for e in shim_errors)
    positions = [0., thicknesses[0] + .375 + measurement_errors[0]]
    shims = []
    for i in range(2, 12):
        # Measure the previous opposite-shaft face, not accumulated nominal pitch.
        target = positions[i-1] + thicknesses[i-1] + .375 + measurement_errors[i-1]
        bare = positions[i-2] + thicknesses[i-2] + spacers[i-2]
        shim = round((target-bare) / .01) * .01
        assert .05 - 1e-9 <= shim <= .25 + 1e-9
        positions.append(bare + shim + shim_errors[i-2])
        shims.append(shim)
    gaps = [positions[i+1] - positions[i] - thicknesses[i] for i in range(11)]
    assert all(.355 - 1e-9 <= gap <= .395 + 1e-9 for gap in gaps)
    return gaps, shims


def main():
    rng = random.Random(8)
    cases = [( [t]*12, [s]*10) for t in (5.97, 6.03) for s in (6.58, 6.62)]
    cases += [([rng.choice((5.97,6.03)) for _ in range(12)],
               [rng.choice((6.58,6.62)) for _ in range(10)]) for _ in range(1000)]
    outcomes = [assemble(*case) for case in cases]
    imperfect = [assemble(t, s, [rng.choice((-.01,.01)) for _ in range(11)],
                          [rng.choice((-.005,.005)) for _ in range(10)]) for t,s in cases]
    # Analytic bound: spacer required = opposite disc + two adjacent gaps.
    required_shim = [5.97 + 2*.370 - 6.62, 6.03 + 2*.380 - 6.58]
    assert math.isclose(required_shim[0], .09) and math.isclose(required_shim[1], .21)
    commanded_shim_bound = [5.97 + .355 + .375 - .01 - .005 - 6.62,
                            6.03 + .395 + .375 + .01 + .005 - 6.58]
    assert .05 <= commanded_shim_bound[0] and commanded_shim_bound[1] <= .25
    root = Path(__file__).resolve().parents[1]
    result = {"status": "HOLD", "physical_validation_state": "NOT_RUN",
              "candidate": "Spacer6.60±0.02; measured sequential0.01-mm metal shim selection; first opposite-shaft datum set to actual first-disc thickness+0.375.",
              "nominal_spacer_with_shim_mm": 6.75, "nominal_pitch_mm": 12.75,
              "nominal_stagger_mm": 6.375, "proposed_shim_stock_mm": [.05,.25],
              "analytic_required_shim_range_mm": required_shim,
              "tested_cases": len(cases), "gaps_per_case": 11,
              "minimum_gap_mm": min(min(x[0]) for x in outcomes),
              "maximum_gap_mm": max(max(x[0]) for x in outcomes),
              "measurement_shim_error_candidate": {"maximum_net_face_measurement_error_mm": .01,
                  "maximum_total_selected_shim_error_mm": .005, "selection_increment_mm": .01,
                  "analytic_gap_bound_mm": [.355,.395], "tested_cases": len(imperfect),
                  "commanded_shim_bound_mm": commanded_shim_bound,
                  "tested_min_gap_mm": min(min(x[0]) for x in imperfect), "tested_max_gap_mm": max(max(x[0]) for x in imperfect),
                  "remaining_margin_to_0p25_0p50_mm": .105,
                  "scope": "Proposed error budgets, not demonstrated instrument/shim capabilities. Net measurement error includes both measured faces; shim error is total pack error, not per leaf."},
              "limitations": ["Face parallelism, rotation runout and collar seating remain excluded; proposed measurement/shim budgets require qualification.",
                              "Current7.00-mm spacers cannot be corrected by adding positive shims to this6.75-mm target.",
                              "Requires changed CAD pitch/stagger/spacers, assembly drawing and all11 actual gap checks; not adopted."],
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / "calculations/cutter_shim_candidate.json").write_text(json.dumps(result, indent=2) + "\n")
    print("CUTTER_SHIM_CANDIDATE_CHECK_PASS status=HOLD cases=1004 gaps=11")


if __name__ == "__main__":
    main()
