# Arduino Mega 2560 controller wiring contract — v0.8 GGM override

Revision: `final-design-fabrication-closure-v0.8`
State: `DIGITAL_WIRING_CONTRACT / PHYSICAL_NOT_RUN / ENERGIZATION_NOT_AUTHORIZED`

The filename is retained for repository compatibility, but the controlling field pin map is the v0.8 generated release: `exports/final/electrical/pin_schedule.csv`, `wire_schedule.csv`, and `exports/final/firmware/source/arduino_mega/src/board_config.h`. The base development header under `firmware/arduino_mega/src` is not a field-wiring authority by itself. `electronics/io_schedule.csv` defines signal safe-state and verification intent.

Mega ground is the protected logic reference. MAX6675 T- channels share electronics reference only with verified ungrounded probes. Heater/motor current must not return through logic wiring.

## Safety chain

E-stop, lid, service guard and independent thermal chain remove hazardous branch permission in hardware through K0. Mega reads their feedback but cannot assert permission around an open contact. Command/feedback mismatch latches a fault. Fault clear requires de-energized cause removal, physical lockout/restart conditions and the applicable user approval; software/Serial alone cannot clear a hardware safety condition.

## GGM motor outputs and feedback

- Shredder BTS7960: `D5 RPWM`, `D4 LPWM`, `D32 ENABLE`; `A0` is the bidirectional motor-lead current input and `D2` is the tach input.
- Extruder BTS7960: `D6 RPWM`, `D33 LPWM`, `D34 ENABLE`; `A9` is the bidirectional motor-lead current input and `A13` is the screw tach input.
- The runtime guard prohibits extruder reverse even though D33 is a physical LPWM output required by the BTS7960 interface.
- Legacy shredder D30/D31 DIR/reverse wiring and legacy A8/A9 shredder/screw fault inputs are not field-wired in this GGM variant. Auxiliary driver fault inputs remain for subsystems that actually expose them.
- A0 and A9 are each calibrated with an independent 0–6 A reference; U95-inclusive current error must be <=0.10 A. P3 maps current to gearbox torque with <=0.40 N.m holdout error. Software gearbox limit is 8.0 N.m and the separate mechanical protection is 8.8–9.3 N.m.

## Other outputs

- Puller/spooler retain separate PWM/direction/enable paths and their released feedback/fault channels. Puller external-interrupt tach is used by the inner speed loop; A15 spool tach is used by dancer/radius/jam logic.
- Traverse uses STEP/DIR/enable and A5/A6 left/right limits; loss of spool permission or missed-limit timeout disables the drive.
- Cooling uses PWM, A4 current feedback and the A14 fan-tach mux. Cooling electrical feedback does not prove airflow; blocked-flow validation remains a separate physical check.
- Heaters are four machine branches only: Z1/Z2/Z3/die, each with branch protection and independent thermal cutoff. Hopper pre-dry is external and has no active machine heater branch.

## Inputs and commissioning

T1/T2/T3/Tdie/Thopper use five thermocouple channels with shared digital bus lines as released. Gauge X/Y, dancer, GGM current, cooling current, tach and auxiliary driver-fault signals use their generated pin assignments. Do not infer a pin from this prose if the final pin schedule disagrees.

Before powered commissioning, record wire ID, terminal, conductor gauge, fuse, sensor supply/range, measured polarity and the exact received component identity. GGM A0/A9 calibration, current-to-torque mapping and mechanical-protection coupons belong to P3. First motor power is one branch at a time and requires a separate explicit user approval.

## Cooling feedback commissioning hold

`COOLING_CURRENT` proves electrical consumption and fan tach proves rotation only. Normal current/RPM, connector-open, blade-stall and fan1/fan2 cases must be recorded before production extrusion. Duct blockage is not proven by those signals and still requires airflow/pressure evidence. Purchase, wiring energization and physical commissioning remain user-approval gates.
