# C2.3-R1 Diagnostic Summary — Goal R0 D0–D4 (diagnostics, NOT convergence)

> Scope: Goal R0 §4 D0–D4 + §5 scene/asset evidence + §6 handoff inputs.
> R0 is diagnostics: executor terminal labels IMPLEMENTED / BLOCKED / FAILED
> only. D0–D4 verdicts below are diagnostic outcomes, never phase acceptance.
> Thresholds frozen at R1 (work 5%, impulse 5%, residence 10%, discrete 10%,
> mass 1e-6 relative) apply ONLY to valid + observable + comparable
> quantities; threshold values unchanged throughout R0.
> Backend: ISAAC_PHYSX, Isaac Sim 6.1.0.0 via `$HOME/env_isaacsim-c22`
> (python 3.12). Runtime `__version__` query → UNKNOWN (attribute absent, no
> error); build `6.1.0-rc.26+release.49347.2d230af4.gl` from VERSION file +
> pip metadata `isaacsim-core 6.1.0.0`. All scenes DIAGNOSTIC_FIXTURE with
> export + sha256 per run (R6).

## Outcomes table (exact numbers from `c2.3/revisions/r1/runs/`)

| ID | Diagnostic | Outcome (exact) |
|----|------------|-----------------|
| D0 | Clock + 2.4 s horizon (`diag/d0_clock.py`, aggregate `runs/d0_clock.json`) | 4/4 IMPLEMENTED. Observed durations: 2.4 / 2.4 / 2.4000000000000004 / 2.4 s; substeps 240 / 480 / 960 / 1920 dense (n0+1..n1 contiguous, dedup by physics step); callback dt readbacks [0.009999999776] / [0.004999999888] / [0.002499999944] / [0.001249999972] s (float32-quantized, within 1e-6 relative). Warmup 120 steps excluded identically, t0 included. Advance path: `SimulationManager.step(steps=1)` = exactly 1 physics step/call; `sim.update()` is render-driven (3–5 steps/call) and not used as clock. |
| D1 | Contact units + isolation (`diag/d1_contact.py`, aggregate `runs/d1_contact.json`) | 8/8 IMPLEMENTED. Support (m = 2 kg, T = 1.0 s, mgT = 19.62 N·s): J = 19.61999943 / 19.61999966 / 19.61999886 / 19.61999863 N·s; rel err 2.88e-08 / 1.71e-08 / 5.82e-08 / 6.98e-08 (≪ 5% after settling, per-step callback capture). No-contact: 0.0 N·s at all 4 dts (≤ 1e-6). Unit rule: raw impulse = VECTOR [N·s], sum \|J\| ONCE; F[N] = \|J\|/dt_contact; never × dt twice. Invalid/stale/missing/overflow invalidates (never except-to-zero). Ground forces labeled support_*, never cutter. |
| D2 | Torque/work semantics (`diag/d2_torque.py`, `diag/test_r02_units.py`, aggregate `runs/d2_torque.json`) | Analytic 16/16 IMPLEMENTED (radial→0, tangential→R·F, reversal flips, opposites cancel, off-axis origin, separate shafts, stationary→0, dissipative ≤ 0, sign-on-body, ground-zero-cutter). Isaac negative control 4/4 IMPLEMENTED: cutter/shaft work exactly 0.0 J at every dt with J_support ≈ 19.62 N·s. tau_contact = dot(Σ cross(p−o, F_on_shaft), a), shaft contacts only, action-reaction signs, counter-rotating shafts separate. Dynamic-shaft drive torque UNAVAILABLE (no joint/drive readout — stated, not estimated). PARTIAL ledger, residual_unclassified (never heat/fracture). |
| D3 | Two-body coupling causality (`diag/d3_bond.py`, aggregate `runs/d3_bond.json`) | IMPLEMENTED. SAME differential loading (B-only +4 N x, dt 0.005, T = 1.0 s): intact dx_final = 0.0 m / Fmean ≈ 2.0 N / 1 component; disconnected dx_final = 2.756498 m / Fmean ≈ 0.0 N / 2 components; timed-disable (SetActive(False) step 66 @ 0.5 s) dx_final = 0.917998 m / Fmean ≈ 0.65 N / 2 components. Separations: \|dx\| 2.756 > 0.05 m; \|F\| 2.0 > 0.5 N. Atomic count (2) separate from components. Constraint: USD PhysicsFixedJoint; NOT a fracture law, no PLA fitting. No counter-based bond code path. |
| D4 | Observability/accounting (`diag/d4_accounting.py`, aggregates `runs/d4_accounting.json`) | IMPLEMENTED. Nominal: intended 3.5 (= 0.5 × design 7.0 kg) vs instantiated 3.5 kg; unexplained 0.0; rel 0.0 ≤ 1e-6 (float64, sorted-ID sequential sum, \|a−b\|/max(\|a\|,1e-30)). Fault injection 3/3 DETECTED: disappearance (enabled [A,B] ≠ [A,B,C]), duplicate (B-twice beyond 1e-6), altered mass (B 2.0→2.5 kg readback mismatch). Statuses: wrap (null, NOT_IMPLEMENTED); passage (null, NOT_APPLICABLE); residence (null, RIGHT_CENSORED); motor-jam (NOT_OBSERVABLE, no flag); unavailable comparison → NOT_EVALUABLE. Buckets disjoint, deficit never zeroed. |

## Root causes fixed from C2.3-A (→ R1 clauses)

- Equal-steps confound (240 steps every dt → durations 2.4/1.2/0.6/0.3 s) → R1 equal MEASURED 2.4 s, substeps 240/480/960/1920; legacy 12-run ladder superseded, not reused (R1 §5; D0 proves the mapping).
- Scalar R×Σ\|F\| torque/impulse as evidence → R2 raw typed telemetry only; legacy series diagnostics-only (D1 unit rule + D2 negative control).
- Missing-event defaults (incl. vacuous jam/wrap-identity) → R3 null + status; jam NOT observable; residence right-censored (D4 statuses).
- Algebraic mass identity → R4 runtime actor/material buckets, forced-zero prohibited, 1e-6 + float handling (D4 ledger).
- Bare-counter bonds → R5 mechanically-coupled diagnostic only, intact/disconnected/timed-disable (D3 FixedJoint triple).
- Reference CAD hash as evidence → R6 scene export + hash per run (all 16 D0–D2 + 4 D3/D4 runs carry scene.usda + scene.sha256).

## Remaining blockers (reviewer authorization required — executor cannot clear)

1. The frozen-state 12-run convergence ladder was NOT rerun under R1 (equal measured 2.4 s + typed telemetry + R3/R4/R5 evidence path). A3 artifacts remain legacy equal-steps evidence and MUST NOT be cited for convergence. Rerun needs reviewer authorization.
2. WRAP strand sensing: no strand metric exists (wrap stays null / NOT_IMPLEMENTED until a sensing path is authorized).
3. Dynamic-shaft effort readout: no joint/drive torque path on the kinematic-pose rig (EffortSensor on fixed joint reads invalid); drive torque stays UNAVAILABLE.
4. `import isaacsim; __version__` → UNKNOWN (attribute absent). Version pinned via pip metadata + VERSION file + per-run module paths instead.
5. Pre-existing A4 verifier scope: `c2.3/verify/verify_contract.py` + `c2.3/tests/test_verify.py::test_clean_tree_is_consistent` check the A1 baseline_manifest hashes of `c2.3/STATE.json` + `c2.3/NEXT.md`, which the authorized R0.1 progress update changed (hash mismatch, verifier exit 1). This is a stale-scope finding, not an R1 defect; the verifier still checks all A3 run hashes, mass/work recomputes, ladder, and banned labels. No threshold, baseline, or run artifact was touched.
