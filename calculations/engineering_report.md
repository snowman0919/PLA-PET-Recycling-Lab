# 공학 계산 통합 보고 — solid-manifold-openmodelica-v0.4

- release: `DIGITAL_FABRICATION_BASELINE`, `PHYSICAL_VALIDATION_PENDING`
- envelope: 470 × 700 × 930 mm
- screw profiles: PLA 18 rpm / PET 20 rpm; nominal 111.8/108.4 g/h
- 200 g/h: nominal 미입증 stretch target
- torque hierarchy: 14 < 18 < 22 < 34 < 48 N·m, PASS
- 24 V power arbiter: 500.0 W < 600 W, PASS
- EX-DIE-04 first-yield screen: 4.32 MPa, physical relief coupon `NOT_RUN`
- physical cutter/feed/melt/cooling/dimension tests: `PHYSICAL_NOT_RUN`

OpenModelica dynamic peak는 `simulation/openmodelica/results/summary.json`에서 구조 load case로 전달하며, 해석은 실제 chip size·wear·melt quality를 증명하지 않는다.
