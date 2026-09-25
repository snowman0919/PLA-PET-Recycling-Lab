# R0 §2 Requirements-to-Evidence Table (R1, checkpoint R0.1)

> Scope: Goal R0 §2 amendments R1–R6. No threshold is relaxed: numeric values are
> unchanged; R1 narrows *applicability*.
> Thresholds (work 5%, impulse 5%, residence 10%, discrete-count 10%, mass 1e-6
> relative) apply ONLY to valid + observable + comparable quantities.
> Quantities that are null, censored, NOT_IMPLEMENTED, NOT_APPLICABLE, or
> diagnostic-only are excluded from threshold comparison entirely: they are
> neither within-threshold nor outside-threshold; no comparison is evaluated.
> Executor terminal labels: IMPLEMENTED / BLOCKED / FAILED only.
> `c2.3/STATE.json` is a progress file, never a baseline constant.

| ID | Requirement (R0 §2 as amended) | Evidence artifact | Verifier check | Threshold applicability |
|----|--------------------------------|-------------------|----------------|-------------------------|
| R1 | Equal MEASURED physics duration: 2.4 s shared by every ladder dt [0.01, 0.005, 0.0025, 0.00125]; per-dt substeps 240 / 480 / 960 / 1920; engine-reported sim time plus per-callback step ID and dt recorded in telemetry. | Per-run config {dt_s, substeps, measured_duration_s}; telemetry columns {engine_time_s, callback_step_id, callback_dt_s}; run summary sim_time_s. | substeps × dt == 2.4 s per run; engine_time_s monotone non-decreasing with terminal == 2.4 s within the documented float handling; callback_step_id dense 1..substeps with matching callback_dt_s. | None: protocol condition, not a compared quantity. Cross-dt metric comparison is admissible only while this row holds. |
| R2 | Contact/joint evidence is correctly typed raw telemetry from the engine path. Legacy scalar R×sum\|F\| torque/impulse estimates are diagnostic-only and inadmissible as evidence. | Typed telemetry schema doc + per-step raw contact force vectors / joint effort readings with source + unit + type labels; any legacy derived series kept under diagnostics/ only. | Schema type check per column; work/impulse integrals in the evidence path reference raw typed columns only; convergence inputs contain no legacy-derived series. | Work 5% and impulse 5% apply only to integrals accumulated from raw typed telemetry on comparable runs. Legacy-derived values receive no threshold evaluation. |
| R3 | Missing events default to null plus an observability status: wrap → null / NOT_IMPLEMENTED; screen transit → null / NOT_APPLICABLE where no screen claim exists (e.g. S1-only); residence → right-censored value with censor flag, never a point value; jam → NOT observable, no flag emitted. | Events file with null payloads + status enum column; schema doc defining the four statuses. | Every null payload carries a status; no default false/zero event flags in evidence; residence rows carry the censor flag; no jam column in the evidence schema. | Residence 10% and discrete-count 10% apply only to observed, uncensored, comparable events. Censored / null rows are excluded from comparison. |
| R4 | Mass closure by runtime actor/material accounting with separated buckets active / output / removed / missing. Forcing unexplained deficit to zero is prohibited. Relative tolerance 1e-6 with explicit float handling (dtype, summation order, comparison form). | Per-run mass ledger {m_initial, m_active, m_output, m_removed, m_missing, m_unexplained, rel_error} + float-handling note. | Recompute rel_error = \|m_initial − accounted\| / m_initial; buckets reconcile to accounted; m_unexplained row present and unforced (may be nonzero — the threshold judges it, the writer does not erase it). | Mass 1e-6 relative applies only when all four buckets are present on comparable runs. |
| R5 | Only a minimal mechanically-coupled bond diagnostic is admitted: joint- or conservative-force-coupled representation; bond condition in {intact, disconnected, timed-disable}. Bare counters are inadmissible. | Bond diagnostic record with coupling declaration + per-bond condition labels + transition log. | Condition enum check; coupling declared and joint-typed or conservative-force-typed; bare counter series absent from evidence inputs. | Discrete-count 10% applies only to mechanically-coupled diagnostic counts that are observable and comparable. Bare counters receive no threshold evaluation. |
| R6 | Scene export + hash mandatory per run (or per frozen-case scene). A reference CAD hash attests inputs only and is not run evidence. | Exported scene file + sha256 recorded in the run manifest; reference hashes labeled provenance-only. | Recompute scene sha256 and compare with the manifest; confirm no convergence or threshold input cites a reference CAD hash. | None: provenance condition, not a compared quantity. |

## Notes

- N1. The legacy equal-steps ladder (240 steps at every dt; physics duration varying
  2.4 / 1.2 / 0.6 / 0.3 s) is superseded. Its runs are not comparable evidence under
  R1 and MUST NOT be reused for convergence claims.
- N2. The old "jam/wrap identical across primary pair" rule is retired as a
  consequence of R3: jam is NOT observable and wrap is null / NOT_IMPLEMENTED, so
  there is no observed flag pair to compare. This retires a vacuous comparison; it
  relaxes nothing.
- N3. Normative contract: `c2.3/revisions/r1/CONTRACT_R1.md`. Clause history:
  `c2.3/revisions/r1/AMENDMENT_LOG.md`. The file `c2.3/CONTRACT.md` is superseded
  as a normative document and preserved unmodified as a historical record.
