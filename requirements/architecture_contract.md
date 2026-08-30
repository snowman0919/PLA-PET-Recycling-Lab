# 아키텍처 계약 — safety-orchestration-closure-v0.6.1

## 잠긴 결정

1. Material은 `PLA` 또는 `PET`이며 RUN 진입 때 잠긴다.
2. 동일 hopper, cutter, screen, bin, sealed feed hopper, feeder, screw/barrel/die, cooling, gauge, puller, dancer/traverse/spool을 공유한다.
3. 외부 pre-dry를 채택하며 machine hopper heater는 재흡수 방지용이다.
4. 470×700×930 mm vertical forming cabinet을 유지하며 새 tower/rail/path를 만들지 않는다.
5. Die 출구부터 puller까지 soft filament는 직선이고 첫 bend는 puller 뒤 solid strand에만 적용한다.
6. Candidate A single compact dual-shaft repeated hook cutter + removable screen을 유지한다.
7. Shredder drive는 DRV-01/DRV-Axx/DRV-F01/#35 chain/cutter-side DRV-02/generic M3 Z16 interface다. 특정 MY1016Z/coupling/phase gear에 종속하지 않는다.
8. Active manufacturing assembly와 review keep-out를 별도 package로 유지한다. Keep-out volume은 부품이나 mass로 집계하지 않는다.
9. Raspberry Pi, 자동 재질/색상 분류, network dashboard는 active scope가 아니다.

## 안전 불변조건

- E-stop과 lid/service switch는 Mega와 독립적으로 motor/heater branch enable을 차단한다.
- Heater branch fuse, one-shot thermal fuse, grounded metal shield를 삭제하지 않는다.
- Cutter/screw 힘 경로는 metal shaft → bearing/thrust plate → metal plate → profile → four-point M8 table anchor다.
- 최대 3회 bounded reverse 후 latched fault. Lockout와 원인 제거 확인 없이 clear 금지.
- Calibrated electrical trip 18 N·m equivalent와 upstream mechanical relief 22 N·m equivalent가 34 N·m phase 및 48 N·m shaft/cutter보다 먼저 작동한다. 모든 hierarchy 값은 cutter-shaft reference이며 motor-side DRV-F01 설정값은 ratio로 환산한다.
- Melt pressure sensor가 없어도 open die, replaceable screen, torque trip, sacrificial relief, guard, remote first-hot-test를 유지한다.
- Material change는 process phase와 직교하는 session state다. `MAINTENANCE_PURGE`에서 이전 material thermal profile, waste path 확인, 최소 시간·screw 회전수·온도 안정·fault 없음·시각 확인을 강제하고 ordered screen/hopper/temperature/final confirmation 전 pending material을 active로 만들지 않는다. 80 g/120 g은 추정치이며 측정 purge 질량으로 주장하지 않는다.
- Gauge uncertainty, cooling, puller, spooler, dancer 또는 안전상 중요한 traverse permission loss는 공통 forming-chain supervisor를 거쳐 controlled rundown으로 전환한다. Feeder와 production winding은 즉시 stop, screw/puller는 fault별 bounded waste discharge 후 stop, heater는 bounded safe hold 뒤 cooldown한다.
- `spool_eligible=false`이면 spooler와 traverse는 항상 off다. Fault 뒤 gauge 20개 연속 valid, U95 ≤0.03 mm, 직경 오차 ≤0.05 mm와 ovality ≤0.05 mm가 10 s 유지되고 puller 비포화, cooling feedback 정상, die-to-gauge transport delay 경과 후에도 operator rethread 확인 전 production winding을 재개하지 않는다.
- Fault clear는 모든 subsystem이 `canClear`를 통과한 뒤에만 한 cycle에서 commit한다. 실패한 clear는 어떤 latch도 바꾸지 않고, 성공 clear도 actuator를 재시작하지 않는다.
- Shredder와 extrusion start는 transactional이다. Subsystem start가 실패하면 process phase를 commit하지 않고 모든 hazardous output은 0을 유지한다. Preheat 완료만으로 extrusion을 자동 시작하지 않으며 `READY_TO_EXTRUDE`에서 operator arm을 요구한다.
- Cooling command는 건강 증거가 아니다. A4 fan-current feedback이 정상 window에서 검증되지 않으면 production extrusion을 허용하지 않으며 1.5 s bounded dwell 뒤 `COOLING_FAILURE`를 latch한다.
- 일반 `FAULT`에서는 유효한 cooling feedback과 active material이 있을 때 잔열 제거용 fan만 유지할 수 있다. `COOLING_FAILURE`와 E-stop에서는 fan도 off다. `COOLDOWN`은 T1–Tdie valid/≤60 °C와 cooling feedback 정상 후에만 IDLE로 완료되며 자동 restart하지 않는다.

## Claim·발주 경계

Release target `SAFETY_ORCHESTRATION_BASELINE`은 기존 closed-solid CAD와 구조 기준선을 바꾸지 않고, Arduino Mega/host runtime/OpenModelica가 동일한 purge·fault-response·rundown·requalification 계약을 실행하며 exact-head CI와 재현성 증거가 일치한 상태다. 독립 상태는 `implementation_state=IMPLEMENTATION_BASELINE`, `virtual_physics_state=VIRTUAL_PHYSICS_VALIDATED`, `cross_solver_state=CROSS_SOLVER_VALIDATION_PENDING`, `empirical_state=EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`이다. 실제 Fusion solve 전 cross-solver PASS를 주장하지 않는다. `VERIFIED_PROCUREMENT_BUDGET`는 supplier 견적과 donor 실물 증거 전 `NOT_ESTABLISHED`로 유지한다.

Gate-1…5는 `OPTIONAL_EMPIRICAL_VALIDATION`이다. 미수행은 `main`을 차단하지 않는다. 다만 CUT-01 full stack, EX-SCR-01/EX-BAR-01, motor/heater/safety hardware의 구매·가공과 최초 통전은 별도 `PROCUREMENT_APPROVAL_GATE`/`COMMISSIONING_GATE`에서 사용자 승인을 요구한다.
