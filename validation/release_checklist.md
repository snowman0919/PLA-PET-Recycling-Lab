# Release checklist — implementation-crosssolver-v0.6

## DESIGN_RELEASE_GATE

- [x] `release_state=IMPLEMENTATION_BASELINE`
- [x] `geometry_validation=PASS`, `fabrication_validation=PASS`
- [x] `virtual_physics_state=VIRTUAL_PHYSICS_VALIDATED`
- [x] `empirical_state=EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- [x] nominal envelope 470×700×930 mm; hard 500×750×1000 mm 이내
- [x] closed B-Rep, manifold mesh, real slicer toolpath, interface catalog, motion/collision checks
- [x] explicit IDLE/SHREDDING/PREHEATING/EXTRUSION/COOLDOWN/FAULT/ESTOP arbitration
- [x] normal phase peak ≤500 W 및 PSU reserve ≥100 W
- [x] canonical controller contract와 Modelica/Arduino/generated configuration hash 일치
- [x] 독립 safety invariant 10개와 각각의 mutation-failure regression
- [x] startup grace, production-config three-retry FSM, ideal broken shear fuse, speed-control metrics
- [x] closed screw pressure-flow-torque-current model 및 hot operating jam
- [x] coupled cooling/forming/diameter control 및 explicit spool length-balance jam
- [x] OpenModelica mandatory scenario 74개 PASS
- [x] shaft/bearing plate/thrust/local 2040 frame/thermocouple-bore 구조 screening PASS
- [x] ungrounded K-type + MAX6675 common-reference architecture와 Ø6.05 H7 cartridge fit 정합

최종 clean-clone SHA, artifact count와 reproducibility 결과는 branch 최종 commit에서 재생성한 뒤 이 checklist와 manifest에 기록한다.

## PROCUREMENT_APPROVAL_GATE — `USER_APPROVAL_REQUIRED`

- [ ] `VERIFIED_PROCUREMENT_BUDGET` 확립 — 현재 `NOT_ESTABLISHED`
- [ ] CNC/cutter/screw-barrel/motor/heater/safety hardware 구매 또는 가공 승인
- [ ] donor identity, 라벨, 전압/전류/축경/토크 및 재고 확인

## COMMISSIONING_GATE — `USER_APPROVAL_REQUIRED`

- [ ] heater energization과 최초 powered commissioning 승인
- [ ] 물리 lockout, E-stop, lid/service interlock, branch/thermal fuse 실물 확인

Gate-1…5는 `OPTIONAL_EMPIRICAL_VALIDATION` 절차로 유지한다. 미수행은 main promotion을 차단하지 않으며, 수행 결과가 생기면 model-correlation/commissioning 증거로 기록한다. 이 릴리스는 `SAFETY_CERTIFIED`, `EMPIRICALLY_VALIDATED`, `PRODUCTION_CERTIFIED`가 아니다.
