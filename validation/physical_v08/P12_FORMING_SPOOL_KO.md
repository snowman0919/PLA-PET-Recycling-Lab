# P12 forming/spool full-path validation

P12 is the final physical gate in the ordered P10 -> P11 -> P12 sequence. Final-pass evidence must use the PET lot bound to an exact `P11_STAGE_RELEASE_VALIDATED` artifact; a dummy filament or a different lot may be used only for non-release setup work.

## Entry contract

1. Revalidate the exact P11 stage release. Its material-run result must be PET and expose a nonblank released lot ID.
2. Record that same lot ID in every row of `templates/p12_forming_spool.csv`.
3. Record a separate full-path approval evidence file with scope `P12_FULL_PATH_RUN`.
4. Every evidence row carries timezone-aware time, operator, independent reviewer, repository evidence path and SHA-256. Numeric rows also require instrument and calibration references.

## Acceptance

1. Puller slip + U95 is <=1.0 percent during the released stable strand interval.
2. Traverse usable width - U95 is >= the firmware forming width, currently 68 mm, with no end collision or jam.
3. Dancer controlled-stop angle + U95 is below the firmware controlled-stop threshold and peak angle + U95 remains below the mechanical hard-stop threshold.
4. A 1 kg nominal load path completes without spill, guard contact, leak, pressure symptom or hard-stop contact.
5. Diameter mean error + U95 and maximum ovality + U95 are <=0.05 mm; recorded diameter U95 remains <=0.03 mm.
6. Extruder gearbox torque + U95 remains <8.0 N.m and GGM motor current + U95 remains <=6.0 A.

`analyze_p12_records.py RECORD --p11-release ...` produces only `P12_RECORD_CHECK_PASS`. It does not set `stage_p12_pass`, production authority, continuing-power authority, machine release, or safety certification. A separate reviewed P12 stage release is required before the evidence set can be called a physical-validation completion candidate.
