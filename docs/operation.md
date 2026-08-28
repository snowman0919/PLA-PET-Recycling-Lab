# 운전 개념 — 물리 승인 전 사용 금지

이 문서는 Undergraduate MVP의 설계 sequence다. 실제 cutter·heater·고전류 bus 운전 절차는 donor 정격 확인과 물리 release 시험 뒤 확정한다.

## 허용 입력

- 한 batch에는 수동 확인한 순수 PLA 또는 세척·건조한 PET 한 재질만 사용한다.
- 색상도 한 색 또는 사용자가 의도한 혼합색 한 batch로 관리한다.
- 입력은 금속·라벨·접착제·음식물을 제거하고 120×120 mm 이하로 사전 절단한다.
- PVC, PETG, TPU, ABS, 나일론, PC, 미확인·복합·도장 재질은 투입하지 않는다.

## Startup

1. 주전원을 lockout한 상태에서 두 타워 고정, anti-reach hopper, 공구식 service cover, hot shield, PE와 branch fuse를 검사한다.
2. PLA/PET recipe, 색상, batch ID를 Arduino UI에서 직접 선택한다. batch 중 recipe 변경은 허용하지 않는다.
3. 환기와 금지재질 경고를 확인한 뒤 물리 START 버튼으로 시작한다.
4. latching E-stop을 해제하고 공통 actuator contactor가 떨어져 있음을 보조접점으로 확인한 후 수동 reset한다.
5. 센서·thermal chain·airflow·압력·contactor feedback이 정상일 때만 READY가 된다.

## 2단 파쇄

1. 1차 twin-shaft가 사전 절단물을 저속 파쇄한다.
2. 고정 chute가 2차 screen granulator로 이송하며 5 mm screen 통과분을 3 L batch bin에 받는다.
3. oversize는 전원 lockout 후 회수해 2차에 다시 투입한다. 별도 자동 sorter는 없다.
4. 과부하는 FEED_LIMIT→STOP→제한 reverse→RETRY 순으로 최대 3회 처리하고 이후 latched FAULT로 전환한다.
5. 막힘 제거는 E-stop, main disconnect, 0 V 확인, 공구식 cover 분리 뒤 수행한다.

## 건조·압출·권취

1. 최대 0.5 kg batch를 dryer에 넣고 선택 재질 recipe로 건조한다. 실제 온도·시간은 resin 공급자 자료와 coupon 결과로 확정한다.
2. 100~150 g/h 범위로 정량 공급하고 3개 heater channel의 압출기/다이 구간을 예열한다.
3. 충분한 purge 뒤 strand를 700 mm 직선 rail의 냉각·X/Y shadow gauge·puller·spooler로 통과시킨다.
4. gauge 교정 전에는 closed-loop 제품 합격 판정을 사용하지 않는다. 초기 목표는 1.75±0.05 mm, ovality ≤0.05 mm다.
5. 정상 정지는 feed off→purge→heater off→저속 배출→cooldown→압력 0·안전온도 확인 순서다.

## 비상정지

사람 접근, guard 파손, 불꽃·연기, 비정상 냄새, 압력 이상 또는 통제되지 않은 움직임에는 물리 E-stop을 누른다. NC 접점이 KACT coil을 직접 열어 위험 actuator bus를 끊으며 Arduino 신호는 이 경로를 우회할 수 없다. 원인 조사와 수동 reset 전 재가동하지 않는다.
