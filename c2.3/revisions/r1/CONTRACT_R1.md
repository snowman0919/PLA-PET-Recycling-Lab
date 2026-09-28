# C2.3 CONTRACT R1 — Numerical Reliability Closure (Goal R0 §2, full implementation)

> Status: draft revision R1 under checkpoint R0.1; normative on reviewer authorization.
> Supersedes `c2.3/CONTRACT.md` as the normative document; that file is preserved
> unmodified as a historical record and is no longer normative.
> Authorized phase: **R0 only**. Executor: Muse Spark 1.3 / OMP Vibe.
> Executor holds NO determination authority. Terminal phase judgment rests solely
> with the reviewer. Executor terminal labels are restricted to
> IMPLEMENTED / BLOCKED / FAILED only; any other terminal-standing vocabulary for
> the phase or its artifacts is prohibited.
> Thresholds frozen at R1 — no threshold edit without reviewer authorization
> recorded as a new revision. If this contract misstates Goal R0 §2 or any frozen
> baseline value, the executor MUST STOP and report BLOCKED instead of proceeding.

## 1. Authorized scope

- Phase R0 = Goal R0 §2 numerical reliability closure: Isaac/PhysX timestep
  convergence + mechanical energy accounting. No other phase is authorized.
- Required backend: **ISAAC_PHYSX** — Isaac Sim 6.1.0.0 via `$HOME/env_isaacsim-c22`
  (PhysX). Any non-PhysX substitute is a proxy and is banned (§4).

## 2. Reviewer policy

- Reviewer holds sole authority for terminal judgment and acceptance.
- Executor never self-assigns terminal standing.

## 3. Frozen baseline (BASELINE ONLY — never optimal)

- S1-A: twin-shaft hook shear, 40 rpm counter-rotating.
- S2-A: q=8, e=7 mm, input +120 rpm / output −15 rpm, phi = −theta/q.
- Cutter gap 0.8 mm — BASELINE ONLY (never optimal, no optimization).
- Screen aperture 4.0 mm — BASELINE ONLY (never optimal, no optimization).
- Waste cases (frozen):
  - FDM = W1 PLA seed 7.
  - PURGE = W4 PLA seed 11.
  - WRAP = P0 seed 7 — S1-only, no S2 fracture claim.
- impulse_scale = 0.02 N·s — UNCALIBRATED assumption, frozen for R0.
- Friction / gravity / solver iterations: frozen at C2.2 dynamics defaults;
  any change requires a contract amendment by the reviewer before use.
- Initial poses: frozen per-case (S1 nip-drop placement; S2 drop above
  screen plane); identical handoff states feed S2-A/S2-B comparisons.
- `c2.3/STATE.json` is a progress file (head / r0_status fields only), never a
  baseline constant. Frozen values live in `c2.3/configs/baseline.json`,
  `c2.3/configs/cases.json`, and this contract.

## 4. Proxy ban

- No analytic / surrogate / size-comparison substitute for contact,
  breakage, transit, residence, or energy quantities.
- Screen transit determined by rigid-body contact against real hole geometry
  only. `impulse_scale` stays UNCALIBRATED throughout R0.
- Legacy scalar R×sum|F| torque/impulse estimates are diagnostic-only (R2) and
  inadmissible as evidence.

## 5. dt ladder (R1 amendment)

- Ladder (values unchanged): [0.01, 0.005, 0.0025, 0.00125] s.
- Primary convergence pair: 0.0025 / 0.00125.
- Equal MEASURED physics duration: 2.4 s shared by every ladder dt (R1).
- Per-dt substeps: 240 / 480 / 960 / 1920 for dt
  0.01 / 0.005 / 0.0025 / 0.00125.
- The legacy equal-steps ladder (240 steps at every dt) is superseded; its runs
  are not comparable evidence and MUST NOT be reused as convergence evidence.
- Telemetry MUST record engine-reported sim time plus per-callback step ID and dt.
- Fixed seeds; fixed backend; identical handoff states.

## 6. Diagnostics D0–D4 (diagnostic-only; none is acceptance evidence)

- D0 run-freeze diagnostics: config / case / backend descriptors, input hashes.
- D1 raw telemetry diagnostics: typed per-step contact / joint / kinematic rows.
- D2 derived work/impulse diagnostics: integrals accumulated from D1 raw columns.
- D3 mass/energy accounting diagnostics: actor/material buckets + energy ledger.
- D4 convergence-evaluation diagnostics: primary-pair ratios against thresholds.
- D0–D4 support review only. Acceptance rests on the evidence artifacts in §9
  plus reviewer judgment (§2).

## 7. Convergence metrics

- Continuous: shaft work, contact impulse (both from raw typed telemetry only),
  residence time (observed uncensored values only), output/screen mass
  (accounted buckets only).
- Discrete: break/fragment count from the mechanically-coupled bond diagnostic
  only (R5); bare counters inadmissible.
- Jam is NOT observable: no flag emitted, no comparison evaluated. Wrap is
  null / NOT_IMPLEMENTED: no comparison evaluated. The old flag-identity rule is
  retired (see AMENDMENT_LOG.md A4).

## 8. Thresholds (frozen; no relaxation)

- Shaft work: 5%.
- Contact impulse: 5%.
- Residence time: 10%.
- Mass conservation: relative error <= 1e-6 with explicit float handling
  (dtype, summation order, comparison form); forcing unexplained deficit to zero
  is prohibited (R4).
- Fragment / bond-break count: 10% (mechanically-coupled diagnostic only, R5).
- Applicability: thresholds apply ONLY to valid + observable + comparable
  quantities (see REQUIREMENTS_EVIDENCE.md). Null / censored / NOT_IMPLEMENTED /
  NOT_APPLICABLE / diagnostic-only quantities are excluded from comparison.
- **Thresholds frozen at R1; contract mistake → STOP + BLOCKED.** No threshold
  edit without reviewer authorization recorded as a new contract revision. On any
  contradiction between this contract and Goal R0 §2 or the frozen baseline, the
  executor MUST STOP and report BLOCKED instead of proceeding.

## 9. Required artifacts

- `c2.3/revisions/r1/CONTRACT_R1.md` (this file),
  `c2.3/revisions/r1/REQUIREMENTS_EVIDENCE.md`,
  `c2.3/revisions/r1/AMENDMENT_LOG.md`.
- `c2.3/configs/baseline.json`, `c2.3/configs/cases.json` (frozen inputs, unchanged).
- Scene export + sha256 per run (R6), recorded in the run manifest.
- dt-ladder run summaries + typed raw telemetry (engine time + callback step
  ID/dt), events with null + observability status (R3), mass ledger with four
  buckets active/output/removed/missing (R4), bond diagnostic record with
  condition labels (R5), energy-accounting record.
- Independent verifier recomputation + evidence package for review handoff.

## 10. Forbidden in R0

- Commencing any phase outside R0 (including B / C / D).
- Reusing the legacy equal-steps 12-run ladder as convergence evidence.
- Gap / screen optimization, motor selection, ML training/selection,
  architecture change or re-ranking.
- Any physical-test or calibration claim; physical_runs stays 0.
- Fabrication, purchase, energization, or merging of hardware.
- Citing reference CAD hashes as run evidence (R6).
- Forcing unexplained mass deficit to zero (R4); emitting default false/zero
  event flags (R3); bare-counter bond counts as evidence (R5).
