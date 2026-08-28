# 2단 파쇄·중소형 2타워 MVP 설계 기준

기준일 2026-08-28, revision `0.2.0-undergraduate-mvp`. 이 문서는 현행 구조·BOM·배치의 읽기 쉬운 기준이며 수치 source of truth는 `cad/parameters/baseline.json`이다.

## 공정과 크기

`수동 검사/사전절단 → Stage 1 twin-shaft → Stage 2 5 mm screen granulator → 3 L batch bin → 0.5 kg dryer/feeder → 18 mm single-screw extruder → 700 mm 냉각·X/Y gauge·puller → spooler`

| 구역 | 외형 | 배치 |
|---|---:|---|
| Tower A | 500×500×1100 mm | 아래에서 batch bin, Stage 2, Stage 1, anti-reach hopper |
| Tower gap | 200 mm | 열·진동 분리 및 서비스 접근 |
| Tower B | 850×500×1000 mm | dryer/feeder, extruder, 500×400×210 mm 제어함 후보 |
| Forming rail | 700 mm | Tower B 오른쪽 직선 냉각·측정·인장·권취 |
| 전체 | 2250×500×1100 mm | 두 타워와 rail 포함 |

목표는 시간당 100~150 g의 소량 필라멘트를 실제로 재활용하는 학부 프로젝트다. 완전한 병 자동투입, 자동 재질/색상 분류, 다중 bin routing, vibratory sorter, Raspberry Pi와 세 번째 파쇄기는 제외한다.

과거 추적성을 위해 granulator source/export 일부는 `stage3_*` 또는 `GRN-*` 이름을 유지하지만 현행 공정 역할은 **Stage 2 granulator**다.

## 제어함 배치 상태

| 상태 | 설계상 의미 | 현재 항목 |
|---|---|---|
| `PURCHASED_PART` | 치수가 알려진 실제 보드/부품 위치 | Arduino Mega 1대 |
| `PCB_RESERVED` | 제작 여부 결정 전 비워 두는 기판 공간 | 190×130 mm monitor/interface PCB, M3 4점 |
| `WIRE_ROUTE` | 부품이 침범하면 안 되는 배선 덕트 | 24 V power, heater, motor, sensor/logic 4경로 |
| `PLACEHOLDER` | MPN·방열·단자방향 확정 전 보수 envelope | KACT 1개, Stage 1/2 drive 2개 |

SSR 4개(압출 3 + dryer 1), branch fuse holder 10개, heat sink 2개는 BOM 추적 ID로 배치한다. 위치표는 `electronics/architecture/control_enclosure_layout.csv`, 배선은 `electronics/wiring/harness_schedule.csv`에 있다. 자동 검증은 PCB·구매부품·placeholder가 wire route와 겹치지 않는지 확인한다.

## 안전 범위

- 사용자가 누르는 latching NC mushroom E-stop 1개를 door에 둔다.
- E-stop NC 접점은 공통 24 V actuator contactor `KACT` coil을 직접 차단한다.
- Arduino는 E-stop/contactor auxiliary contact를 감시·표시할 뿐, 비상정지 권한을 갖지 않는다.
- cutter에는 anti-reach hopper와 공구식 고정 cover, heater에는 branch fuse·one-shot thermal fuse·금속 shield를 둔다.
- 이는 인증 safety relay나 이중 contactor architecture가 아니다. 선택 접촉기의 DC utilization category, 차단전류, coil 억제, fuse coordination은 구매 전 확인해야 한다.

비상정지 기능의 일반 설계 원칙은 ISO 13850을 참고하되, 실제 전기 구현과 지역 규정 적합성은 별도 검토가 필요하다.

## BOM 판정

- 시스템 BOM: 58행
- `BUY`: 23행
- `CRITICAL`: 43행
- 공개 가격 근거가 있는 target-budget planning floor: 148,321 KRW
- exact industrial 후보를 포함한 부분 engineering floor: 3,661,019 KRW

두 금액 모두 배송·세금·CNC와 다수 TBD 품목이 빠진 **부분 합계**이며 시스템 총액이나 구매 승인이 아니다. 부품 MPN/재고/정격이 없는 행은 placeholder 상태로 유지한다.

## 제작 전 남은 Gate

- donor motor/driver/PSU/heater/sensor의 라벨·치수·정격·상태 확인
- Stage 1 torque, Stage 2 screen 통과율·파편 containment 시험
- dryer 수분성능, extruder 압력·토크·100 g/h 질량수지 시험
- 접촉기 DC 차단정격, fuse/배선 굵기, PE 연속성, thermal fuse fault 시험
- X/Y gauge 교정과 30분 직경 안정성 시험
- 실제 구매·CNC 견적
