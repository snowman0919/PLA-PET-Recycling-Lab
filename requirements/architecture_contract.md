# 아키텍처 계약 — solid-manifold-openmodelica-v0.4

## 잠긴 결정

1. Material은 `PLA` 또는 `PET`이며 RUN 진입 때 잠긴다.
2. 동일 hopper, cutter, screen, bin, sealed feed hopper, feeder, screw/barrel/die, cooling, gauge, puller, dancer/traverse/spool을 공유한다.
3. 외부 pre-dry를 채택하며 machine hopper heater는 재흡수 방지용이다.
4. 470×700×930 mm vertical forming cabinet을 유지하며 새 tower/rail/path를 만들지 않는다.
5. Die 출구부터 puller까지 soft filament는 직선이고 첫 bend는 puller 뒤 solid strand에만 적용한다.
6. Candidate A single compact dual-shaft repeated hook cutter + removable screen을 유지한다.
7. Shredder drive는 DRV-01/#35 chain/DRV-02/generic M3 Z16 interface다. 특정 MY1016Z/coupling/phase gear에 종속하지 않는다.
8. Active manufacturing assembly와 review keep-out를 별도 package로 유지한다. Keep-out volume은 부품이나 mass로 집계하지 않는다.
9. Raspberry Pi, 자동 재질/색상 분류, network dashboard는 active scope가 아니다.

## 안전 불변조건

- E-stop과 lid/service switch는 Mega와 독립적으로 motor/heater branch enable을 차단한다.
- Heater branch fuse, one-shot thermal fuse, grounded metal shield를 삭제하지 않는다.
- Cutter/screw 힘 경로는 metal shaft → bearing/thrust plate → metal plate → profile → four-point M8 table anchor다.
- 최대 3회 bounded reverse 후 latched fault. Lockout와 원인 제거 확인 없이 clear 금지.
- Calibrated electrical trip 18 N·m equivalent와 upstream mechanical fuse 22 N·m가 34 N·m phase 및 48 N·m shaft/cutter보다 먼저 작동한다.
- Melt pressure sensor가 없어도 open die, replaceable screen, torque trip, sacrificial relief, guard, remote first-hot-test를 유지한다.

## Claim·발주 경계

Release state `DIGITAL_FABRICATION_BASELINE`은 closed-solid CAD, actual slicing, Modelica/CalculiX screening과 문서 일치를 뜻한다. 물리 상태는 `PHYSICAL_VALIDATION_PENDING`/`PHYSICAL_NOT_RUN`이다.

Gate-1 signed raw CSV와 photo/video hash가 PASS 전 CUT-01은 2장 coupon 외 발주하지 않는다. EX-CPN-SCR/EX-CPN-BAR와 supplier DFM 전 full EX-SCR-01/EX-BAR-01을 발주하지 않는다. 사용자의 명시적 조건에 따라 Gate-1 결과 없이 `main`으로 승격하지 않는다.
