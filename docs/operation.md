# 운전 절차 — 물리 승인 전 사용 금지

이 문서는 설계된 sequence와 UI 요구사항이다. Release checklist의 물리 항목과 사용자 안전 승인이 완료되기 전 cutter, heater, high-current bus를 energize하는 실제 운전지침이 아니다.

## 허용·금지 입력

허용: 단일재질 순수 PLA 출력 폐기물 또는 cap·neck ring·label·adhesive를 제거하고 세척한 PET bottle/body. 한 batch와 extrusion session에는 한 재질만 사용한다.

금지: PVC, PETG를 PET로 간주한 재료, TPU, ABS/나일론/PC, 미확인 플라스틱, 탄소/유리섬유 복합재, 도장·코팅품, 금속 screw/insert/magnet/bearing, 음식·음료·세정제 잔류물. 낮은 classifier confidence는 Reject가 기본이며 사용자 override도 물리 확인과 event log를 요구한다.

## Startup

1. 환기, 조명, 소화/비상 접근, 주변 비인가자 부재와 장치 고정을 확인한다.
2. Lockout 상태에서 guard, lid, service cover, shield, spool cage, purge catch, fines bin과 filter를 검사한다.
3. PE, fuse indicator, thermal fuse/high-limit, pressure relief discharge와 connector label을 확인한다.
4. 원료 batch ID, source object/batch, recycling generation, material/color truth와 금지물 검사 결과를 등록한다.
5. PSU label/branch current가 승인된 configuration과 일치하는지 확인한다.
6. E-stop을 release하고 monitored manual reset을 수행한다. Pi heartbeat와 local BACK/ABORT를 함께 사용해 Mega SELF_TEST를 시작한다.
7. SELF_TEST가 E-stop/contact mirror, lid/service/thermal chain, sensor open/short, pressure/airflow, encoder/limit 상태를 모두 통과해야 READY가 된다.

## 분류·파쇄·선별

1. UI에서 `SORT_SHRED`, 자동 material/color classification과 target bin을 선택한다.
2. 첫 물체는 빈 chamber에서 처리하고 camera frame, confidence, current RMS/peak, speed drop와 vibration trace를 확인한다.
3. START physical acknowledgement 후 feed gate를 연다. 손·도구로 원료를 밀지 않는다.
4. Load 증가 시 firmware가 FEED_LIMIT→STOP→REVERSE→RETRY를 수행하며 3회 뒤 fault가 latch된다.
5. Oversize는 이전 stage로, 3–6 mm acceptable은 선택 bin으로, <3 mm fines는 밀폐 waste bin으로 보낸다.
6. Jam/fault는 E-stop과 lockout 후 원인을 제거하고 fastener/tool count와 guard 복구 전 reset하지 않는다.

## 건조·batch 선택

PLA baseline은 45 °C 6 h, PET baseline은 140 °C 2 h+160 °C 4 h 계산 profile이다. 실제 resin supplier 자료와 물리 coupon이 우선한다. PET는 outlet moisture ≤50 ppm, 외부 dew point ≤−40 °C를 증명하지 못하면 extrusion하지 않는다.

PLA/PET heater branch는 hardware selector로 상호배제한다. Hopper batch가 선택한 material/color와 다르거나 이전 material purge 기록이 없으면 feeder가 열리지 않아야 한다.

## 압출·첫 strand

1. Material profile과 purge requirement를 확인하고 metal catch, screen pack와 die guard를 장착한다.
2. `DRY_PREHEAT`에서 heater를 올린 뒤 zone ±3 °C, pressure 0, feed-throat cooling/airflow와 bearing temperature를 확인한다.
3. `EXTRUDE_SPOOL`로 전환하고 low feed/20 rpm에서 purge한다. Pressure 3 MPa target, 5 MPa warning, 6.5 MPa automatic reduction, 8 MPa latched stop을 적용한다.
4. 충분한 purge mass와 색/기포/black-speck 검사를 통과한 strand만 cooling tunnel로 보낸다.
5. 사용자가 guard-open/drive-disabled 상태에서 strand를 puller, dancer, traverse와 spool start hole에 수동 threading한다. Guard를 닫고 interlock을 재확인한다.

## 직경 폐루프·권취

Gauge U95가 qualified되지 않으면 product acceptance/closed-loop를 켜지 않는다. 초기 acceptance는 1.75±0.05 mm, ovality ≤0.05 mm다. 5회 연속 직경/ovality 불량 또는 3회 오염 frame에서 Pi가 PAUSE하고, Pi/USB 상실은 Mega가 760 ms 이내 safe output으로 전환한다.

Puller가 diameter를 제어하고 spooler는 dancer 0.5 N을 따라간다. Core/full spool speed는 약 4.45→1.78 rpm이고 torque limit는 0.25 N·m다. Traverse는 70 mm 안에서만 움직이며 flange spill, dancer limit, slip >5%에서 중지한다.

## 정상 정지·비상 정지

정상 정지는 feed 차단→approved purge→heater off→저속 screw/puller 정지→cooldown fan→압력 0/안전온도 확인→batch 종료 통계 export 순서다. 생산 log에는 평균·표준편차·min/max·ovality·불량구간·길이/질량·fault가 남아야 한다.

사람 접근, guard 파손, 불꽃/연기, 비정상 냄새, pressure relief, 전기음 또는 통제되지 않은 움직임에는 UI PAUSE가 아니라 물리 E-stop을 누르고 main disconnect를 차단한다. 원인 조사와 자격 검사 전 재가동하지 않는다.
