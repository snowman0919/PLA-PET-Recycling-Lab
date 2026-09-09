# 실용적 제작·재사용 기준 — 2026-09-09

사용자 결정은 policy.json에 고정한다. 기본 뼈대는2020, 외장과 저온 출력부는ABS, 체결은 보유M2~M6를 우선한다. CNC는 절삭형상·압력경계·정밀 끼워맞춤을 만족하는 데 필요한 범위로 제한한다.
이 폴더는 새 제작 목표와 현재 산출물의 차이를 관리한다. 기존 CAD/도면/STL/3MF를 새 설계로 조용히 승격하지 않는다. 현재 machine_release=HOLD, physical_validation=NOT_RUN이다.

## 기본 제작 방법
- 프레임: 재고2020 절단·T너트·금속 코너브래킷. 분쇄기/추력부는 짧은 지지 간격과 금속 거싯으로 하중을 전달한다. 기존2040 보강2개는 치수 이름만 바꾸지 않고 강성·접합을 재검토한다.
- ABS: 외장 패널, 덮개, 가이드, 전자부 bezel을 분할 출력한다. 별도 print envelope220mm 안에 부품210mm 기준을 유지한다. 외장과 비상시 파편/용융물/고온을 막는 내부 금속 장벽은 구분한다.
- 나사: 외장M3/M4 우선, 프로파일은 실제 슬롯/T너트에 맞춘다. 와셔·captured nut·금속 spacer를 활용한다. 보유 직경 범위는 길이/피치/등급/너트/와셔의 모든 수량을 보증하지 않는다.
- 금속판: 브래킷/커버/스크린은 판재 절단·드릴·절곡을 우선하고, 베어링 좌면 등 기능부만 국부 정밀가공한다. 모든 평판을 CNC 밀링품으로 발주하지 않는다.
- 축/기어/압출부: 규격품과 donor를 우선 검토하되 cutter, keyseat, 위상기어, screw/barrel/die의 실제 기능 요구를 삭제하지 않는다. 선택되지 않은 모터 어댑터와 assembly/reference 항목을 중복 발주하지 않는다.

## 프린터 재사용
현재 사용자 진술은 MCU만 고장 난 프린터1대의 보유 사실이다. 이 자산을 과거 bed 고장 프린터와 같은 기계라고 가정하지 않는다. 개별 donor 수량·모델·정격·작동 상태는 아직 미확인이다.
재사용 우선순위는 rod/rail, lead screw, belt/pulley, motor, endstop, fan, display, bracket/cable이다. donor_register.csv의 간단한 라벨/치수 확인으로 adapter와 BOM을 맞춘다. 모든 소형 부품에 고가 시험을 추가하지 않는다.
프린터 stepper가 분쇄·screw 토크를 낸다고 가정하거나, hotend를 flake용 screw/barrel과 동등화하지 않는다. heater/sensor/fan/driver는 전압·출력·interface를 확인하고 existing firmware 계약과 연결한다.
기존 별도24V600W PSU와 Arduino Mega 기준은 유지한다. 고장 MCU 보드를 제어기로 배정하지 않는다.

## ABS 전환
현재 출력물의 재질 표기와 슬라이서 증거를 분리한다. PLA에서ABS로 선택이 바뀌면 재슬라이스·작은 fit 확인이 필요하다. 사용자의 기존0.1mm 맞춤 경험은 유지하되 ABS에서 같은 결과라고 간주하지 않는다. 자동으로 전체 모델을1~2% 확대하지 않는다.
Prusa는 ABS의 휨/수축과 enclosure·환기를 안내한다: https://help.prusa3d.com/article/abs_2058
UltiMaker ABS의 HDT 예시는 약86.6°C(0.455MPa)이며 모든 ABS의 연속사용온도나 선정 재료의 보증값은 아니다: https://ultimaker.com/materials/abs/
따라서 ABS 외장이 있어도 기존 고온부 금속 차폐, 보호접지와 독립 과열/전력 차단은 유지한다. 제작을 위해 쓰는 ABS 폐기물은 PLA/PET 재활용 feed와 분리한다.

## 재생성과 검증
`python3 bom/practical_mvp/build_plan.py`는 현재119행 등 BOM 스냅샷으로부터 generated/의 가공경로·ABS전환·프레임전환 표를 생성한다. 행수는 실행 시 읽으며 구매 부품수나 비용으로 해석하지 않는다.
`python3 bom/practical_mvp/test_plan.py`는 정책의 오판 방지 시험이다. 물리강성, ABS 치수, donor 성능을 시험한 것이 아니다.
현재 도면이나 BOM을 수정할 때 이 목표와 generated/summary.json의 미반영 항목을 확인하고, 실제 변경된 module만 재생성·재검증한다. 전체 프로젝트를 새로 설계하는 지시가 아니다.
