# R0.1 checkpoint — Goal R0 §2 revision R1 (draft, reviewer authorization pending)

- Normative draft: `c2.3/revisions/r1/CONTRACT_R1.md`; evidence table
  `c2.3/revisions/r1/REQUIREMENTS_EVIDENCE.md`; history
  `c2.3/revisions/r1/AMENDMENT_LOG.md`.
- `c2.3/CONTRACT.md` is superseded as a normative document; preserved unmodified
  as a historical record (never edit).
- R0 status tracked in `c2.3/STATE.json` field `r0_status`; frozen baseline values
  unchanged. STATE.json is a progress file, never a baseline constant.
- Legacy equal-steps 12-run ladder (240 steps every dt) is superseded as evidence;
  MUST NOT be reused for convergence claims. Next implementation step: R1 §5 equal
  measured 2.4 s ladder (substeps 240/480/960/1920) with typed raw telemetry.

# C2.3-A NEXT — A2 / A3 / A4 only

## A2 — telemetry + work/impulse/energy accounting implementation

- Implement `c2.3/sim/run_case.py`: frozen-case PhysX runner with fixed
  seeds, fixed dt per invocation, frozen initial poses, real hole-geometry
  screen; per-step telemetry (shaft angle/torque, per-fragment contact
  force, bond-break events, fragment poses/velocities, screen passage
  events, residence timers) per goal §12.
- Implement `c2.3/sim/aggregate.py`, `c2.3/sim/convergence.py`,
  `c2.3/sim/energy_ledger.py`: shaft-work integration, contact-impulse
  accumulation, mass accounting with relative mass_error
  (goal §13), mechanical energy ledger, primary-pair convergence ratios.
- Implement `c2.3/tests/` unit tests for telemetry schema, work/impulse
  integrators, ledger closure, and threshold evaluators on fixtures.
- No threshold, baseline, or case edits during A2; any defect in frozen
  values → STOP + BLOCKED per CONTRACT.md §7.

## A3 — fixed-state timestep sweep execution + convergence evaluation

- Execute the frozen-state dt ladder [0.01, 0.005, 0.0025, 0.00125] s on
  FDM (W1/PLA/seed 7), PURGE (W4/PLA/seed 11), WRAP (P0/seed 7, S1-only).
- Evaluate the primary pair 0.0025/0.00125 against frozen thresholds:
  shaft work 5%, contact impulse 5%, residence 10%, relative mass_error
  <= 1e-6 (goal §13), jam/wrap identical, fragment/bond 10%.
- Append per-run sha256 hashes to `c2.3/results/baseline_manifest.json`;
  record energy-ledger closure per run. Executor reports
  IMPLEMENTED / BLOCKED / FAILED only.

## A4 — independent verifier + evidence package + review handoff

- Implement and run the independent verifier (recompute hashes, re-check
  convergence ratios, confirm no proxy inputs, confirm no forbidden
  B/C/D content) over the A2/A3 artifacts.
- Assemble the evidence package: frozen manifests, run summaries,
  telemetry, convergence and energy-ledger records.
- Write `c2.3/REVIEW_HANDOFF_KO.md` for reviewer determination.
  Executor reports IMPLEMENTED / BLOCKED / FAILED only.

## FUTURE / REVIEWER AUTHORIZATION REQUIRED

- Phase B (calibration/physical tests), Phase C (optimization incl.
  gap/screen/motor), Phase D (architecture/ML changes): NOT authorized.
  Commence only with explicit reviewer authorization.
