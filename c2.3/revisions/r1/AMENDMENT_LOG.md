# Amendment Log — CONTRACT (superseded) → CONTRACT_R1 (Goal R0 §2)

> The file `c2.3/CONTRACT.md` is SUPERSEDED as a normative document and preserved
> unmodified as a historical record. Normative authority moves to
> `c2.3/revisions/r1/CONTRACT_R1.md` on reviewer authorization.
> No threshold was relaxed: all numeric thresholds are unchanged. R1 narrows
> *applicability* to valid + observable + comparable quantities and replaces
> unenforceable or confounded clauses with implementable ones.

| # | Old CONTRACT clause | R1 clause | Reason |
|---|---------------------|-----------|--------|
| A1 | §5 equal steps-per-run (240 steps at every dt; physics duration 2.4 / 1.2 / 0.6 / 0.3 s varies by dt) | CONTRACT_R1 §5: equal MEASURED 2.4 s; per-dt substeps 240 / 480 / 960 / 1920; engine-reported time + callback step ID/dt required (R1) | Equal steps confound resolution with duration, so cross-dt comparison was inadmissible. The legacy equal-steps 12-run ladder is superseded and MUST NOT be reused as convergence evidence. |
| A2 | §6 metrics shaft work / contact impulse computed from tau = CUTTER_R_M × sum\|F_contact\| (CONTACT_DERIVED_MOMENT_ARM, UNCALIBRATED) | R2: correctly typed raw contact/joint telemetry as the only admissible source; legacy scalar estimates diagnostic-only (CONTRACT_R1 §4, §6, §7) | Derived torque was never measured; unmeasured estimates cannot ground evidence. Work/impulse thresholds (5%) now apply only to integrals from raw typed telemetry. |
| A3 | §7 mass conservation as an algebraic identity (relative mass_error <= 1e-6) with a STOP-if-impossible escape | R4: runtime actor/material accounting with buckets active / output / removed / missing; unexplained-deficit forced-zero prohibited; 1e-6 relative tolerance with explicit float handling (CONTRACT_R1 §7, §8) | An algebraic identity without runtime accounting is unenforceable and invites forced closure. Threshold value unchanged. |
| A4 | Missing-event handling by default flags, incl. §7 "jam/wrap identical across primary pair" | R3: null + observability status — wrap null / NOT_IMPLEMENTED, screen transit null / NOT_APPLICABLE, residence right-censored, jam NOT observable (CONTRACT_R1 §7, §8) | Defaults fabricate observability; an "identical" verdict on unobserved flags is vacuous. The flag-identity rule is retired, not relaxed: there is no observed pair to compare. |
| A5 | `configs/baseline.json` reference_assets STEP/USD hashes standing as scene provenance | R6: scene export + hash mandatory per run; reference CAD hash is provenance-only, never run evidence (CONTRACT_R1 §9, §10) | Reference hashes attest inputs, never the executed scene. |
| A6 | Break/fragment accounting via bare cumulative counters (breaks_cum / bonds_alive) feeding the §7 10% rule | R5: minimal mechanically-coupled bond diagnostic only — joint- or conservative-force-coupled representation, conditions intact / disconnected / timed-disable; counter-only prohibited (CONTRACT_R1 §6, §7) | Bare counters carry no mechanical coupling. The 10% value is unchanged and now applies only to coupled diagnostic counts that are observable and comparable. |
| A7 | §7–§8 thresholds stated without applicability conditions | CONTRACT_R1 §8 + REQUIREMENTS_EVIDENCE.md: thresholds apply ONLY to valid + observable + comparable quantities; null / censored / NOT_IMPLEMENTED / NOT_APPLICABLE / diagnostic-only data excluded | Prevents vacuous or misleading comparisons on data that was never observed. No numeric change. |
