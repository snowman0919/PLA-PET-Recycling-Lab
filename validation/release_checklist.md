# Release checklist — technical-blocker-closure-v0.6.2.1

## TECHNICAL_CLOSURE_RELEASE_GATE — `FUSION_DEFERRED_POLICY_ACTIVE`

- [x] source v0.6.2 `f9fde47359ef84744daf1a9279040c507ef60497` archive branch/tag 고정
- [x] main은 source의 ancestor이므로 추가 merge 불필요
- [x] P0-A hybrid tach, 6/12/20/20 PPR와 실제 timestamp pulse adapter
- [x] P0-B~F 저속 actuator contract, 4-drive PI, spool radius, explicit traverse homing, 독립 calibration v4
- [x] P0-G~H passive recirculation과 positive auger/agitator feed 가상 검증
- [x] P0-I 독립 fan feedback와 fan-loss controlled rundown; airflow 수치는 실측 아님
- [x] P0-J combined production-controller hardware-adapter 37/37 host scenario evidence
- [x] P0-K OpenModelica 1.27.0 DASSL shadow 24/24와 Fusion delta 분류
- [x] P0-L을 사용자 결정으로 `DEFERRED_USER_DECISION` 분류; package integrity와 present-result fail-closed gate 유지
- [x] 최종 engineering source `a22f06ea534cad9e99949872e550d2789d49ef9f`에 Fusion handoff STEP/load/material/contact/constraint/worker 계약 결박
- [ ] final exact HEAD CI-LIGHT/CI-FULL와 artifact reproducibility
- [ ] PR review 및 merge

가격은 `PRICE_STATUS=INFORMATIONAL`, `PRICE_RELEASE_BLOCKING=false`이다. 현재 조건부 178,729 KRW, reserve 포함 198,729 KRW지만 이 값의 증감은 기술 release를 차단하지 않는다. 견적 미확정과 구매는 `PROCUREMENT_APPROVAL_GATE=USER_APPROVAL_REQUIRED`로 계속 잠긴다.

현재 Fusion 정책은 `DEFERRED`이며 solver PASS가 아니다. P0-A~K와 로컬 deterministic gate가 모두 통과하면 `TECHNICAL_CLOSURE_BASELINE`을 사용할 수 있지만, `CROSS_SOLVER_VALIDATED`와 `FUSION_VALIDATED`는 실제 결과 전까지 금지한다. 최종 exact HEAD와 PR/merge 항목은 아직 별도 확인 대상이다.

---

## 동결 v0.6.1 checklist (historical reference)

## SAFETY_ORCHESTRATION_RELEASE_GATE

- [x] `release_state=SAFETY_ORCHESTRATION_BASELINE`, `implementation_state=IMPLEMENTATION_BASELINE`
- [x] v0.6 SHA `60ccd92fe9a7df35b550a2a57649b1263da09d10` archive branch/tag 보존
- [x] 현재 main을 한 번 merge했고 v0.6 tree를 되돌린 항목 없음
- [x] `MachineSupervisor`가 process/material/forming/calibration/start/clear/purge/spool 권한을 소유
- [x] atomic all-subsystem fault clear; 실패 rollback과 clear 후 no-restart
- [x] transactional shredder start; fan-first preheat/purge start; explicit extrusion arm
- [x] cold boot material `NONE`; drive/gauge/current/cooling/temperature readiness 분리
- [x] EEPROM v2 version/CRC와 invalid-record zero-sanitize
- [x] 실제 `MAINTENANCE_PURGE`: feed 승인과 waste 확인 분리, previous profile, motion gate, 120 s/32 command-derived revolution, ordered cleaning
- [x] purge STOP/PAUSE와 정상 완료의 hot `COOLDOWN`; E-stop은 별도 all-zero
- [x] A4 fan-current production backend; start proof 1.5 s, timeout 3.0 s, 운전 fault dwell 1.5 s
- [x] 공통 forming-chain rundown/thermal hold/cooling recovery/requalification
- [x] gauge 20 samples, U95 0.03 mm, 직경/ovality 0.05 mm 10 s, transport delay, fresh manual rethread
- [x] quality transient 동안 same-cycle spool/traverse off와 waste mode
- [x] dancer warning/controlled stop/hard stop = 0.32/0.36/0.4363 rad; 정상 jam은 hard stop 비접촉
- [x] 8개 동적 power phase peak <=500 W, reserve >=100 W; 최대 477.2 W, 최소 reserve 122.8 W
- [x] firmware/Modelica generated contract drift 검사: 11 process phases, 8 power phases
- [x] production-linked runtime 43 scenarios/116 traces, invariant failure 0
- [x] bounded sequence 4 fixed seeds x 최대 64 events
- [x] false-PASS red-team mutation 14/14 검출
- [x] firmware host tests 7/7, Arduino Mega 2560 compile PASS
- [x] closed B-Rep, manifold mesh, slicer, collision, CalculiX와 analytical structure 기준 유지
- [x] 기계 geometry는 v0.6 exact SHA와 동일; binary CAD revision-only rewrite 없음
- [ ] 최종 release commit의 clean-clone CI-LIGHT/CI-FULL 증거 — commit 후 외부 evidence로 기록
- [ ] 실제 Autodesk Fusion solve/correlation — `PENDING_EXTERNAL_EXECUTION`, safety-orchestration gate와 독립

OpenModelica mandatory 111/111은 PASS했고 failure는 0이다. Clean-clone CI-FULL이 저장 결과를 다시 실행해 검증한다.

## CROSS_SOLVER_GATE — `CROSS_SOLVER_VALIDATION_PENDING`

- [x] FreeCAD controlling STEP 9개와 LC01–LC10 hash-bound package 준비
- [x] v0.6.1 engineering source SHA lock과 v0.6 supersession binding
- [x] LC01–LC10 모두 `rerun_required=true`, result cell 비움
- [ ] 실제 Fusion 실행 결과와 OpenModelica/CalculiX correlation

## PROCUREMENT_APPROVAL_GATE — `USER_APPROVAL_REQUIRED`

- [ ] `VERIFIED_PROCUREMENT_BUDGET` 확립 — 현재 `NOT_ESTABLISHED`
- [ ] cooling-feedback exact shunt/amplifier/fan window와 donor 정격 확인
- [ ] CNC/cutter/screw-barrel/motor/heater/safety hardware 구매 또는 가공 승인
- [ ] donor label, 전압/전류/축경/토크/센서 형식과 재고 확인

조건부 계획 175,729 KRW, contingency 포함 195,729 KRW, 계획 여유 4,271 KRW다. 이 값은 quote/receipt가 아니다.

## COMMISSIONING_GATE — `USER_APPROVAL_REQUIRED`

- [ ] heater energization과 최초 powered commissioning 승인
- [ ] 물리 lockout, E-stop, lid/service interlock, branch/thermal fuse 실물 확인
- [ ] fan-current open/stall 분리, puller tach pulse 형식, gauge와 temperature channel 물리 교정

Gate-1…5는 `OPTIONAL_EMPIRICAL_VALIDATION`이며 현재 `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`이다. 이 릴리스는 실제 성능·안전·생산 인증이 아니다.
