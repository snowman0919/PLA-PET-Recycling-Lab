# v0.6.1 safety-orchestration 완료 감사

Revision: `safety-orchestration-closure-v0.6.1`

이 문서는 디지털 구현과 가상 검증의 완료 범위를 기록한다. 실제 fan airflow, 절단 토크, purge 질량, filament 품질, E-stop/guard/thermal fuse의 물리 동작, Autodesk Fusion 결과 또는 안전 인증을 대신하지 않는다.

## 기준선과 형상

- v0.6 기준 SHA: `60ccd92fe9a7df35b550a2a57649b1263da09d10`
- 보존 branch/tag: `archive/implementation-crosssolver-v0.6-final`, `implementation-crosssolver-v0.6-final`
- v0.6.1 시작 뒤 현재 `origin/main`의 `c00b4c83b07e9aa84b4d2d080ee0d940cfc7b6ea`를 한 번 merge했다.
- 기계 형상은 v0.6 기준과 동일하다. FCStd/STEP/STL/3MF/PNG binary를 revision 문자열 때문에 다시 쓰지 않았고, 경량 metadata만 갱신했다.
- 외형 470 x 700 x 930 mm, 출력품 각 축 210 mm 이하, 계획 질량 1,012.70 g 기준을 유지한다.

## 구현 감사

|항목|구현 근거|디지털 판정|
|---|---|---|
|단일 orchestration|`MachineSupervisor`와 thin Arduino I/O adapter|PASS|
|원자적 fault clear|전체 subsystem preflight 뒤 무조건 commit, 실패 시 latch 불변|PASS|
|트랜잭션형 start|shredder subsystem 성공 뒤 phase commit, extrusion 별도 arm|PASS|
|교정 readiness|drive/gauge/current/cooling/temperature 분리, EEPROM v2 CRC와 invalid zero-sanitize|PASS|
|fan-first start|IDLE fan-only, healthy 1.5 s, timeout 3.0 s, proof 전 heater/motion 0|PASS|
|maintenance purge|feed 승인과 waste 확인 분리, 120 s/32 command-derived revolution, ordered cleaning|PASS|
|고온 purge 종료|정상 중단은 `PURGE_PREHEAT_REQUIRED`, 완료는 `SCREEN_CLEAN_REQUIRED`; 모두 60 °C 이하까지 `COOLDOWN`|PASS|
|forming rundown|gauge/cooling/puller/spooler/dancer/traverse 공통 response contract와 개별 reason|PASS|
|품질·재자격|직경/ovality/saturation same-cycle winding off, 20 samples/U95/10 s/transport/manual rethread|PASS|
|dancer|warning 0.32, controlled stop 0.36, hard stop 0.4363 rad|PASS|
|fail-closed|최종 invariant false이면 FAULT latch와 all-zero|PASS|

## 검증 증거

- Firmware host suite: 7/7 PASS.
- Arduino Mega 2560 compile: PASS.
- Production-linked runtime: 43 scenarios, 116 trace events, invariant failure 0.
- Bounded deterministic sequence: 4 fixed seeds x 최대 64 events, PASS.
- Red-team: 14/14 false-PASS mutation 검출.
- Firmware/Modelica contract: 11 process phases와 8 power phases 동등성 PASS.
- OpenModelica mandatory 111/111 PASS, failure 0. Common rundown response latency는 gauge/cooling/spool 모두 0.1 s고 quality requalification entry→READY는 27.8 s다.
- 독립 component-summed power: 모든 8개 phase PASS, 최대 peak 477.2 W, 최소 PSU reserve 122.8 W.
- Artifact count와 mismatch count는 최종 clean-clone `validation/evidence/exact_head_evidence.json`에 기록한다. 이 증거 파일은 자기 자신으로 HEAD를 바꾸지 않도록 release commit 밖에서 생성한다.

## Purge와 계측 경계

Purge screw revolution은 별도 verified tach 측정이 아니라 command/RPM 적분인 `COMMAND_DERIVED_ESTIMATE_NOT_MEASURED`다. 80 g/120 g은 nominal engineering estimate이며 측정된 purge 질량이 아니다. A4 fan-current path는 전기적 소비전류 feedback이지 airflow 또는 tach의 직접 측정이 아니다. 정확한 shunt/gain/window와 donor fan의 open/stall 분리는 commissioning 전 물리 교정 대상이다.

## 독립 gate

|Gate|상태|경계|
|---|---|---|
|`SAFETY_ORCHESTRATION_RELEASE_GATE`|최종 exact-head CI-LIGHT/CI-FULL 증거에서 판정|디지털 구현·가상 검증만|
|`VIRTUAL_PHYSICS`|`VIRTUAL_PHYSICS_VALIDATED`|선택한 모델·가정 안의 결과|
|`CROSS_SOLVER_GATE`|`CROSS_SOLVER_VALIDATION_PENDING`|실제 Fusion 결과 없음|
|`PROCUREMENT_APPROVAL_GATE`|`USER_APPROVAL_REQUIRED`|주문·가공 미수행|
|`COMMISSIONING_GATE`|`USER_APPROVAL_REQUIRED`|통전·물리 시험 미수행|
|경험 검증|`EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`|Gate-1…5 결과 없음|

따라서 이 릴리스는 `SAFETY_CERTIFIED`, `EMPIRICALLY_VALIDATED`, `PRODUCTION_CERTIFIED`, `CROSS_SOLVER_VALIDATED`가 아니다.
