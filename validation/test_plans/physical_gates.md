# 저비용 물리 Gate

## Gate 1 Cutter coupon

- 부품: CUT-01 정확히 2개, CUT-04 5 mm screen coupon 1개, CUT-05 shaft 2개, CUT-03 plate 2개, 6004 4개, DRV-03 lamination 6개, G1J-01–10/P01–P03, calibrated 0–200 N gauge/load-cell, 50 A current sensor와 Hall RPM. G1J-07 metal upright가 3 mm polycarbonate guard를 유지하고 S0/S1→K0→K1 hard-cut 회로를 구성한다. Motor 시험은 functional interface를 통과한 donor만 연결한다.
- 입력: PET body/four-layer folded seam, PLA wall 1.2/2.0/3.0 mm 각 5개.
- 측정: torque/current/RPM drop, capture/reverse, 조각 sieve mass.
- 합격: PLA/PET body max<=14 N·m, PET folded seam max<=24 N·m, 영구변형/guard breach 0, bounded reverse 3회 뒤 latch, 3–6 mm>=55%, >20 mm PET strip<=10%, fines<=15%, recovery>=95%와 torque-current-RPM curve 확보. 상세 절차는 `exports/jigs/gate1/test_procedure_ko.md`가 controlling이다.

## Gate 2 Flake/feed coupon

- 부품: 4/5/6 mm screen coupon, removable bin, sealed hopper/feeder.
- 측정: 3–6 mm mass fraction, oversize/fines/긴 PET strip, bridge와 30 min feed CV.
- 합격: 5 mm 기준 3–6 mm fraction >=70% 또는 recirculation 1회 후 >=85%, long strip <=2%, feed CV <=10%. 실패 시에만 별도 granulator ADR 재개.

## Gate 3 Extruder cold/mechanical proof

- 부품: screw/barrel/thrust plate/bearing/drive, heater 미장착 또는 분리.
- 합격: hand rotation 전 길이 binding 0, radial rub 0, shaft alignment <=0.10 mm TIR, thrust path가 metal/profile에 닫힘, 30 min heater-off load에서 fastener 이동 0.

Gate 3 전에는 EX-CPN-SCR 3-pitch와 EX-CPN-BAR 60 mm 공정 coupon만 허용한다. Drawing limit radial clearance 0.14–0.16 mm, hardness/case depth/Ra/TIR report와 공급사 DFM이 닫히기 전 full screw/barrel 발주를 승인하지 않는다.

## Gate 4 Hot extrusion

- 부품: metal shield, remote E-stop, branch/thermal fuse, thermocouple logger, low-feed PLA.
- 합격: runaway/open-sensor에서 independent cut, jam에서 torque trip/guard containment, shield <=55 °C와 adjacent polymer <=45 °C, PLA 30 min 안정 후에만 dry PET 시험. Pressure sensor 유무와 관계없이 blockage test를 기록한다.

## Gate 5 Diameter/spool

- 부품: traceable pin/wire, gauge, puller, dancer/traverse, full 1 kg spool dummy.
- 합격: installed 285 mm duct 끝 strand temperature가 PLA <=48 °C/PET <=65 °C, U95 <=0.05 mm initial, 30 min mean 1.75 ±0.05 mm와 ovality <=0.08 mm, puller slip <=1%, dancer/endstop collision 0, full traverse spill 0. 200 g/h에서 온도 Gate 실패 시 장치를 키우지 않고 처리량을 낮춰 최대 안정값을 보고한다. Improvement target은 U95/diameter ±0.03 mm다.

각 Gate 실행 전 사용자가 exact 부품과 절차를 승인해야 한다. 이 문서는 시험 결과가 아니다.
