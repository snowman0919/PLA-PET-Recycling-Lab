# PPR-TC01 — fastener/insert/fit tolerance coupon

- revision: `virtual-physics-closure-v0.5.1`
- status: `REQUIRED_BEFORE_PRODUCTION_PRINTS`; coupon mass is excluded from machine print total
- material/profile: same spool, nozzle and slicer profile as the target PLA parts
- orientation: flat; 0.4 mm nozzle; 0.20 mm layer; 4 perimeters; no support
- through-hole ladders: M3 Ø3.2/3.4/3.6, M4 insert Ø4.2/4.4/4.6, M5 Ø5.3/5.5/5.7
- square-nut pockets: M3 5.6/5.8/6.0 and M4 7.0/7.2/7.4 mm
- male gauges: Ø7.8/8.0/8.2 and Ø11.8/12.0/12.2 mm
- acceptance: select the smallest hole/pocket that accepts the actual hardware without splitting; select the male gauge producing the documented slide/ream allowance. Record selection in `tolerance_coupon_results.csv`.
- limitation: slicer success does not qualify fit; the coupon must be physically printed and measured for each printer/material batch.
