# 공학 계산 통합 보고 — safety-orchestration-closure-v0.6.1

- final fabrication release: `HOLD`; 아래 값은 개별 명목 screening이며 전체 v0.8 제작 승인 또는 물리 검증이 아니다.
- envelope: 470 × 700 × 930 mm
- screw profiles: PLA 16 rpm / PET 18 rpm; analytical nominal 99.4/97.5 g/h
- 200 g/h: nominal 미입증 stretch target
- torque hierarchy: 14 < 18 < 22 < 34 < 48 N·m, PASS
- 24 V phase power: independent maximum 477.2 W ≤500 W, reserve 122.8 W ≥100 W, `PASS`
- thermocouple bore: blind5.5 / nominal radial-subtraction ligament 3.4 mm / assumed trip SF 2.15, `HOLD`; 실제 최소 잔여 두께·고온 국부 응력 미검증
- die heater fit: Ø6.55 H7 / Ø6.500±0.013 CG, diametral clearance 0.037–0.078 mm, conservative watt density 12.45 W/cm²
- frame: local 2040 Option B, relative displacement 0.42 mm, total profile 14.668 m
- EX-DIE-04 first-yield screen: 4.32 MPa; empirical coupon is optional evidence but procurement/commissioning remains approval-gated

OpenModelica dynamic peak는 `simulation/openmodelica/results/summary.json`에서 구조 load case로 전달하며, 해석은 실제 chip size·wear·melt quality를 증명하지 않는다.
