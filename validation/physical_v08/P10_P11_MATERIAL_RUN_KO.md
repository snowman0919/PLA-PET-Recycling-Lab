# P10/P11 PLA/PET low-feed physical validation

P10/P11 are the first material-feed gates. P10 is PLA only; P11 is PET only and remains blocked until a validated P10 stage release exists. Each bounded run requires a separate material-feed approval evidence file.

## Evidence contract

1. Copy `templates/p10_p11_material_run.csv` for exactly one material/run.
2. Keep `lot_id`, drying-record path/hash, feed-approval path/hash/scope, operator and independent reviewer constant across the run.
3. Every sample carries timezone-aware `measured_at`, raw evidence path/SHA-256, temperature logger calibration, diameter gauge calibration, torque calibration and current calibration references.
4. P10 approval scope is `P10_BOUNDED_PLA_RUN`; P11 scope is `P11_BOUNDED_PET_RUN`.
5. P10 requires validated P4, P6, P8 and P9 stage releases. P11 requires a validated P10 stage release.

## Bounded run acceptance

1. Screw starts at 8-10 rpm. Higher speed is approached only from measured torque/current/diameter behavior.
2. Temperature mean +/- U95 stays inside the current generated firmware profile target +/-5 C for all four zones.
3. Every stable candidate requires gearbox torque + U95 < 8.0 N.m and motor current + U95 <= 6.0 A.
4. Leak, uncontrolled pressure symptom, guard contact or torque trip excludes that sample from the stable window. More than one torque trip rejects the run as repeated-trip control.
5. A valid window is 20 consecutive stable samples with mean diameter error <=0.05 mm, sample ovality <=0.05 mm and diameter U95 <=0.03 mm.
6. Stable throughput is computed from measured cumulative mass and elapsed time. 200 g/h is not a forced pass criterion.

P10 analysis uses `analyze_material_run.py RECORD --stage P10 --p4-release ... --p6-release ... --p8-release ... --p9-release ...`. P11 uses `--stage P11 --p10-release ...`. `MATERIAL_RUN_RECORD_CHECK_PASS` never sets `stage_pass`, downstream entry, material-feed authority, continuing-power authority or machine release; a separate reviewed stage release is required. P10 then requires `validate_p10_stage_release.py`; P11 then requires `validate_p11_stage_release.py`. A validated P11 release opens only P12 entry review and never authorizes continued material feed.
