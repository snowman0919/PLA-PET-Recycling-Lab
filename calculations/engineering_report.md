# 공학 계산 통합 보고 — implementation-crosssolver-v0.6

- release: `IMPLEMENTATION_BASELINE`, `VIRTUAL_PHYSICS_VALIDATED`, `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- envelope: 470 × 700 × 930 mm
- screw profiles: PLA 16 rpm / PET 18 rpm; analytical nominal 99.4/97.5 g/h
- 200 g/h: nominal 미입증 stretch target
- torque hierarchy: 14 < 18 < 22 < 34 < 48 N·m, PASS
- 24 V phase power: maximum 490.0 W ≤500 W, reserve 110.0 W ≥100 W, PASS
- thermocouple bore: blind5.5 / ligament 3.4 mm / trip SF 2.15, PASS
- die heater fit: Ø6.05 H7, clearance 0.070–0.122 mm
- frame: local 2040 Option B, relative displacement 0.438 mm, total profile 14.668 m
- EX-DIE-04 first-yield screen: 4.32 MPa; empirical coupon is optional evidence but procurement/commissioning remains approval-gated

OpenModelica dynamic peak는 `simulation/openmodelica/results/summary.json`에서 구조 load case로 전달하며, 해석은 실제 chip size·wear·melt quality를 증명하지 않는다.
