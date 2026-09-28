# C2.3-A CONTRACT — Numerical Reliability Closure (IMMUTABLE)

> Authorized phase: **C2.3-A only**. Executor: Muse Spark 1.3 / OMP Vibe.
> Executor holds NO determination authority. Terminal phase judgment rests
> solely with the reviewer. Executor final reported values are restricted to
> IMPLEMENTED / BLOCKED / FAILED only.

## 1. Authorized scope

- Phase C2.3-A = numerical reliability closure: Isaac/PhysX timestep
  convergence + mechanical energy accounting.
- Required backend: **Isaac Sim 6.1.0.0 via `$HOME/env_isaacsim-c22`
  (PhysX)**. Any non-PhysX substitute is a proxy and is banned (§4).

## 2. Reviewer policy

- Reviewer holds sole authority for terminal phase judgment.
- Executor never self-assigns terminal standing and never declares
  completion/acceptance language for the phase or its artifacts.

## 3. Frozen baseline (BASELINE ONLY — never optimal)

- S1-A: twin-shaft hook shear, 40 rpm counter-rotating.
- S2-A: q=8, e=7 mm, input +120 rpm / output −15 rpm, phi = −theta/q.
- Cutter gap 0.8 mm — BASELINE ONLY (never optimal, no optimization).
- Screen aperture 4.0 mm — BASELINE ONLY (never optimal, no optimization).
- Waste cases (frozen):
  - FDM = W1 PLA seed 7.
  - PURGE = W4 PLA seed 11.
  - WRAP = P0 seed 7 — S1-only, no S2 fracture claim.
- impulse_scale = 0.02 N·s — UNCALIBRATED assumption, frozen for A-phase.
- Friction / gravity / solver iterations: frozen at C2.2 dynamics defaults;
  any change requires a contract amendment by the reviewer before use.
- Initial poses: frozen per-case (S1 nip-drop placement; S2 drop above
  screen plane); identical handoff states feed S2-A/S2-B comparisons.

## 4. Proxy ban

- No analytic / surrogate / size-comparison substitute for contact,
  breakage, passage, residence, or energy quantities.
- S2 passage determined by rigid-body contact against real hole geometry
  only. `impulse_scale` stays UNCALIBRATED throughout C2.3-A.

## 5. dt ladder

- Ladder: [0.01, 0.005, 0.0025, 0.00125] s.
- Primary convergence pair: 0.0025 / 0.00125.
- Same steps-per-run within a comparison; fixed seeds; fixed backend.

## 6. Convergence metrics

- Continuous: shaft work, contact impulse, residence time,
  output/screen mass.
- Discrete: break/fragment count, jam flag, wrap flag.

## 7. Thresholds (goal §18, frozen)

- shaft work: 5%.
- contact impulse: 5%.
- residence time: 10%.
- mass conservation: relative mass_error <= 1e-6 (goal §13; if the fracture representation makes this mathematically impossible, STOP + BLOCKED, do not change the threshold).
- jam / wrap flags: identical across primary pair.
- fragment / bond-break count: 10%.

**Thresholds frozen after first commit; contract mistake → STOP + BLOCKED.**
No threshold edit after the A1 commit without reviewer authorization
recorded as a new contract revision. If this contract misstates goal §18
or any frozen baseline value, the executor MUST STOP and report BLOCKED
instead of proceeding.

## 8. Required artifacts

- `c2.3/CONTRACT.md` (this file), `c2.3/STATE.json`, `c2.3/NEXT.md`.
- `c2.3/configs/baseline.json`, `c2.3/configs/cases.json`.
- `c2.3/results/baseline_manifest.json` (run hashes appended at A3).
- dt-ladder run summaries + telemetry, energy-accounting record (A2/A3).

## 9. Forbidden in C2.3-A

- Commencing phases B / C / D.
- gap / screen optimization, motor selection, ML training/selection,
  architecture change or re-ranking.
- Any physical-test or calibration claim; physical_runs stays 0.
