# GGM shredder drive wiring contract — v0.8

Revision: `final-design-fabrication-closure-v0.8`
State: `DIGITAL_WIRING_CONTRACT / PHYSICAL_NOT_RUN / ENERGIZATION_NOT_AUTHORIZED`

This file supersedes the former donor-motor/DRV-F01 electrical narrative. The active shredder drive is `GGM K9DG60N2 24 V + K9G75C`, one BTS7960 bridge, GGM keyed mechanical-protection coupling, 6201-supported jackshaft and #35 12T:30T chain path. Legacy 14/18/22 N.m acceptance values and a 50 A current channel are not v0.8 GGM criteria.

## Controlling sources

1. `control/ggm_drive_contract.json` controls GGM model, speed/current/torque and protection limits.
2. `exports/final/electrical/pin_schedule.csv`, `wire_schedule.csv` and `fuse_schedule.csv` control field wiring.
3. `exports/final/firmware/source/arduino_mega/src/board_config.h` controls the released Mega pin names.
4. `validation/physical_v08/P3_GGM_BENCH_KO.md` controls physical calibration evidence.

If this document conflicts with those generated schedules, stop and regenerate/review the handoff rather than improvising wiring.

## 24 V power path

`24 V protected bus -> F-SH 20 A DC branch fuse -> BTS7960 power input -> K9DG60N2 motor`.

The 20 A fuse protects the branch/conductor envelope; it is not the allowed motor operating current and is not a torque setpoint. The selected motor rated current is 4.6 A and the control current ceiling is 6.0 A. Current above the calibrated control envelope is a fault/hold condition even if the branch fuse has not opened.

## Mega/BTS7960 signals

- `D5`: shredder RPWM.
- `D4`: shredder LPWM.
- `D32`: shredder enable/permission output.
- `A0`: bidirectional shredder motor-lead current sensor.
- `D2`: shredder/jackshaft tach input used with the physically verified pulses-per-revolution value.
- Legacy `D30/D31` DIR/reverse wiring is not field-wired in the GGM variant.
- Legacy `A8 SHREDDER_FAULT_PIN` is not field-wired; the selected BTS7960 interface has no authoritative fault input in this design.

RPWM/LPWM are never a substitute for the hardwired safety chain. On reset, stale calibration, missing permission, tach/current invalidity or runtime fault, the software command returns to zero/disabled while K0 remains the hardware authority for hazardous branch power.

## Current and torque calibration

P3 calibrates A0 against an independent 0–6 A reference. The U95-inclusive current error must be <=0.10 A. Torque is not inferred from BTS7960 marketing current: a 250 mm torque arm and independent force reference create the current-to-gearbox-torque map, with holdout error <=0.40 N.m.

The software gearbox torque limit is 8.0 N.m. The independent mechanical-protection coupling is calibrated with nine lot-controlled brass coupons across the whole GGM system: 3 shredder-forward, 3 shredder-reverse and 3 extruder-forward. Each accepted release interval is 8.8–9.3 N.m including uncertainty, followed by free rotation and no hub/key damage. The final neck geometry is not fixed from calculation alone.

## Rotation and jam behavior

Nominal shredder gearbox output is 40 rpm and the 12T:30T path gives approximately 16 rpm at the cutter. Actual speed is measured, not assumed. P4 uses exactly two CUT-01 coupons before the remaining ten cutters are released for fabrication.

A controlled jam may use bounded reverse only under the released runtime policy. Maximum retry count is three; failure after the third attempt latches a fault and must not auto-restart. Repeated contact with the 8.0 N.m software limit during ordinary material processing is not permission to raise the threshold; feed/process conditions must be corrected.

## Pre-power physical requirements

Before any motor energization, the received GGM identity and geometry, mount-compatibility gate, mechanical key/guard fit, F-SH identity, A0 sensor polarity/range, K0 hardwired chain, E-stop and positive-opening service/lid interlocks must have physical evidence. First power is one motor branch at a time under a separate explicit user approval. This document itself never grants that approval.
