# 시스템 요구사항

- 문서 상태: Undergraduate MVP v0.2
- 기준일: 2026-08-28
- 대상: 수동 선별 PLA/PET 기반 중소형 2타워 필라멘트 재생기
- 검증 표기: `A` 해석, `I` 검사, `T` 물리 시험, `D` 시연

실제 장치와 샘플을 사용하지 않은 항목은 `T/D 미검증`으로 남긴다. 계산이나 시뮬레이션 통과를 물리 시험 통과로 대체하지 않는다.

## 기능과 성능

| ID | 요구사항 | 합격 기준 | 검증 |
|---|---|---|---|
| REQ-FUNC-001 | 장치는 순수 PLA 출력 폐기물과 세척·건조된 PET 병/용기를 입력으로 지원한다. | 허용·금지 투입물 표시, 각 재질 batch 시연 | I,D |
| REQ-FUNC-002 | 사용자가 재질을 수동 확인하며 TPU·혼합·불명 재질은 투입하지 않는다. | 투입 체크리스트와 REJECT 용기 검사 | I,D |
| REQ-FUNC-003 | 사용자가 PLA/PET recipe를 직접 선택하고 batch 중 변경할 수 없다. | UI 선택·잠금·purge 전환 시연 | I,D |
| REQ-FUNC-004 | 색상은 자동 분류하지 않고 한 batch에 한 색 또는 혼합색을 사용자가 선택한다. | batch label과 완성 spool label 일치 | I,D |
| REQ-FUNC-005 | 파쇄는 1차 twin-shaft와 2차 screen granulator의 물리적 2단으로 구성한다. | 두 cutter stage와 단계별 입도 샘플 | I,T |
| REQ-FUNC-006 | 2차 granulator는 5 mm 기준 screen으로 3~6 mm 압출 feed를 만들고 oversize를 내부 재순환한다. | screen 통과율·fines·oversize 질량 기록 | I,T |
| REQ-FUNC-007 | PET와 PLA는 재질별 recipe로 건조하고 정량 공급한다. | 온·습도·시간·feed 로그 | T,D |
| REQ-FUNC-008 | 한 압출 session은 한 재질만 처리하며 재질 전환 시 purge를 강제한다. | UI interlock과 purge waste 경로 시연 | I,D |
| REQ-FUNC-009 | 단일 screw extruder가 PLA와 PET recipe를 지원한다. | 각 재질 안정 압출 시험 | T |
| REQ-FUNC-010 | 직경은 비접촉 방식으로 `d_x`, `d_y`, 평균과 ovality를 기록한다. | 기준봉 교정과 두 축 동시 log | T |
| REQ-FUNC-011 | 직경제어는 spooler가 아니라 encoder가 있는 puller가 수행한다. | 제어 블록 검사와 step-response | I,T |
| REQ-FUNC-012 | spooler는 dancer와 traverse를 사용해 일반 1 kg급 spool에 권취한다. | full-radius 권취와 장력 독립성 시연 | T,D |
| REQ-FUNC-013 | Arduino Mega 단독으로 sensor 감시·실시간 제어·사용자 UI를 수행하며 Raspberry Pi는 MVP에 포함하지 않는다. | 외부 컴퓨터 없이 startup·run·fault 시연 | I,T |
| REQ-FUNC-014 | Arduino serial log는 batch ID, recipe, 온도, 직경 평균과 fault만 저장한다. | 30분 운전 CSV export | I,T |
| REQ-PERF-001 | 안정 연속 처리량 목표는 100~150 g/h이며 명목값과 분리해 보고한다. | 30분 이상 질량 수지 시험; `>=100 g/h` | T |
| REQ-PERF-002 | 초기 직경 합격범위는 1.75 ± 0.05 mm이다. | 교정된 gauge의 30분 log 전 구간 판정 | T |
| REQ-PERF-003 | 개선 목표는 1.75 ± 0.03 mm, ovality 0.05 mm 이하이다. | 목표와 현재 달성값을 분리 보고 | T |
| REQ-PERF-004 | hopper 유효 적재량은 약 0.5 kg이며 batch 단위로 보충한다. | 질량 시험과 anti-reach 접근성 검사 | I,T |

## 기계·열·전기 인터페이스

| ID | 요구사항 | 합격 기준 | 검증 |
|---|---|---|---|
| REQ-MECH-001 | 사용자가 세척·건조하고 120 x 120 mm 이하로 사전 절단한 입력을 받는다. 완전한 PET 병 자동 투입은 범위 밖이다. | 120 mm gauge와 금지 투입물 표기 | I,T |
| REQ-MECH-002 | cutter, screw 하중은 금속 축/베어링/plate를 거쳐 profile frame으로 전달한다. | 하중 경로 도면과 조립 검사 | A,I |
| REQ-MECH-003 | 출력 부품은 각 축 210 mm 이내이거나 나사·정렬핀을 쓰는 분할 구조다. | 자동 bounding-box report | I |
| REQ-MECH-004 | cutter/blade clearance는 금속 shim으로 조절하며 출력 공차에 의존하지 않는다. | shim stack와 측정 기록 | I,T |
| REQ-MECH-005 | shaft 최대 처짐 목표는 허용 cutter clearance의 1/3 이하이다. | analytic와 FEA 교차검증 | A |
| REQ-MECH-006 | 모듈은 M4/M5, 금속 nut/insert, 정렬 구조로 분리 정비할 수 있다. | 공구 접근·분리 경로 visual/physical review | I,D |
| REQ-THERM-001 | barrel과 die-end는 총 3개 heater channel로 나누고 재질별 profile을 독립 제어한다. | channel별 센서·heater·recipe trace | I,T |
| REQ-THERM-002 | hot zone은 금속 shield와 insulation을 사용하고 PLA/ABS 하우징을 연화 위험 온도 아래로 유지한다. | 최악조건 열해석 후 thermocouple 시험 | A,T |
| REQ-PWR-001 | 전원은 24 V, 600 W nominal PSU 한 대를 사용하되 donor label 확인 전 25 A를 확정값으로 쓰지 않는다. | label 기록, 실측/정격 power budget | I,A |
| REQ-PWR-002 | shredding, drying/preheat, extrusion/spooling, cooldown phase를 중재해 peak를 제한한다. | worst-case branch budget와 arbiter fault test | A,T |
| REQ-INT-001 | 분리 모듈은 keyed connector와 명시된 전압·신호·핀·접지 인터페이스를 갖는다. | interface control document와 continuity test | I,T |
| REQ-INT-002 | serial protocol은 version, checksum/CRC, heartbeat, bounded timeout을 포함한다. | malformed/dropout fault injection | I,T |

## 안전

| ID | 요구사항 | 합격 기준 | 검증 |
|---|---|---|---|
| REQ-SAFE-001 | latching E-stop은 heater와 위험 motor energy를 하드웨어로 차단한다. | controller fault 상태에서 차단 시험 | I,T |
| REQ-SAFE-002 | cutter는 고정 anti-reach hopper와 공구로만 열리는 service cover로 둘러싸고 정비 시 물리 lockout한다. | 접근 probe·공구 분리·0 V 확인 | I,T |
| REQ-SAFE-003 | 투입 경로는 손가락/손이 cutter에 도달하지 않는 anti-reach 구조와 파편 비산 방지를 갖는다. | 정해진 probe 검사와 visual review | I,T |
| REQ-SAFE-004 | heater branch는 독립 thermal fuse, branch fuse, software runaway detection을 모두 갖는다. | 각 보호계층 단독 fault test | I,T |
| REQ-SAFE-005 | jam reverse retry는 횟수와 시간이 제한되며 이후 latched FAULT로 전이한다. | FSM test와 물리 저부하 jam 시연 | I,T |
| REQ-SAFE-006 | sensor open/short와 Mega watchdog timeout에서 출력이 default-OFF가 되고 재시작 전 수동 reset을 요구한다. | fault injection matrix 전 항목 통과 | T |
| REQ-SAFE-007 | hot surface, rotating shaft, cutter, 고전류 단자에는 guard와 lockout 정비 절차를 제공한다. | guard inspection과 manual review | I,D |
| REQ-SAFE-008 | 실내 환기, 금지 재질, 오염·라벨·금속 제거 경고를 UI와 매뉴얼에 표시한다. | startup acknowledgement와 문서 검사 | I,D |

## 비용과 납품물

| ID | 요구사항 | 합격 기준 | 검증 |
|---|---|---|---|
| REQ-COST-001 | Target Budget Design의 신규 구매 목표는 200,000 KRW 이하이다. | 날짜·출처·shipping이 있는 BOM 합계 | I |
| REQ-COST-002 | Target Budget Design의 CNC 비용 목표는 100,000 KRW 이하이다. | quote-ready package와 실제 견적; 주문은 승인 후 | I |
| REQ-COST-003 | 목표 초과 시 Engineering Recommended Design을 별도 BOM으로 제시한다. | 기능·안전·비용 차이표 | I |
| REQ-DOC-001 | FreeCAD Python에서 FCStd/STEP/STL/DXF/drawing을 headless 재생성할 수 있어야 한다. | clean regeneration과 manifest checksum | I,T |
| REQ-DOC-002 | 한국어 조립 PDF, BOM, wiring/pinout, calibration, operation, maintenance, validation report를 제공한다. | release checklist와 제3자 문서 review | I |

## 현재 미검증 Gate

- donor motor, driver, PSU, heater, sensor의 라벨과 실측값
- PLA/PET 시편별 Stage 1 peak torque, Stage 2 granulator screen 통과율 및 허용 최대 PLA 실질 두께
- dryer의 실제 수분 제거 성능과 extrusion 품질
- 18 mm screw/barrel의 실제 flake solids conveying, melt pressure, torque, 100 g/h 질량수지와 rupture-element 작동
- 수동 batch 오염 방지, optical gauge 불확도, 30분 직경 안정성
- CNC 및 신규 구매의 실견적
