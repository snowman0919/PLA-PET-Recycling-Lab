# PPR v0.8 safety and power topology

Revision: `final-design-fabrication-closure-v0.8`
State: `DIGITAL_TOPOLOGY / PHYSICAL_NOT_RUN / ENERGIZATION_NOT_AUTHORIZED`

## Power envelope

The user-reported available supply is a 24 V 800 W unit, approximately 33.3 A nameplate capability, but its exact label, terminals and condition remain a P1 receipt item. The machine envelope remains protected by `F-MAIN = 30 A DC`; available PSU current is not permission to raise branch or software limits.

Released branch fuses are `F-LOGIC 3 A`, `F-SAFE 1 A`, `F-SH 20 A`, `F-SCREW 10 A`, `F-FEED 5 A`, `F-PULL 5 A`, `F-SPOOL 5 A`, `F-FAN 3 A`, and `F-H1..H4 5 A` each. Exact DC interrupt rating and received fuse-holder compatibility must be verified before power.

For the two GGM axes, F-SH/F-SCREW are conductor/branch protection only. Each K9DG60N2 is rated 4.6 A and the released control ceiling is 6.0 A. Shredder current is A0; extruder current is A9. Neither axis uses the former 50 A calibration contract.

## Hardwired safety authority

Hazardous motion/heater permission is removed in hardware by the normally-safe chain:

`E-stop NC -> lid positive-opening NC -> service positive-opening NC -> independent thermal cutoff -> K0 safety contactor/relay chain`.

The Mega reads feedback but cannot energize around an open safety contact. K0 auxiliary feedback is compared with commanded state; a mismatch latches a fault. Reset requires the physical cause to be removed and the released restart/lockout procedure. Serial/software commands alone are never safety reset authority.

The first logic-only test keeps motor/heater branch fuses removed or otherwise positively isolated. Motor commissioning is one branch at a time. Heater commissioning is a later P9 stage with motors inhibited for the first heat cycle. Each transition needs separate explicit user approval.

## GGM protection hierarchy

The active GGM criteria are:

- calibrated current range: 0–6.0 A, U95-inclusive error <=0.10 A;
- software gearbox torque limit: 8.0 N.m;
- mechanical protection release: 8.8–9.3 N.m including U95;
- current-to-torque holdout error: <=0.40 N.m;
- extruder reverse: forbidden.

The former donor-drive 14/18/22 N.m hierarchy is superseded and must not be used as a physical acceptance target for v0.8 GGM hardware.

## Heater and aggregate power

The active hot zone has four machine heater branches: barrel Z1/Z2/Z3 and die. Hopper pre-dry is external and has no active machine heater branch. Software power arbitration limits commanded heater/motion combinations but cannot replace fuses, conductor sizing, K0 or independent thermal cutoff. The currently released arbitration basis is 360 W heater budget during preheat, 300 W heater budget during running, and 500 W aggregate running cap.

## Grounding and signal separation

Protective earth uses a dedicated frame/enclosure/hot-shield bond path and must not share logic return conductors. Motor/heater current returns stay out of the logic reference. Current/tach/thermocouple/gauge wiring is routed separately from PWM/high-current conductors where practical, with shield termination only as specified by the final wire schedule.

The detailed GGM axis wiring is `electronics/shredder_drive_wiring.md`; the final field schedules under `exports/final/electrical/` remain the generated wiring source of truth.
