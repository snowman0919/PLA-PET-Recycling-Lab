# 시스템 요구사항 — compact-single-path-v0.3

## Hard constraint

| ID | 요구 | 검증 |
|---|---|---|
| SYS-ENV-01 | 정상 운전 전체가 500 x 750 x 1000 mm 이하 | FreeCAD assembly bounding box 자동검사 |
| SYS-ENV-02 | 설계 목표 480 x 720 x 950 mm 이하 | baseline 및 자동검사 |
| SYS-COST-01 | 신규 현금비용 200,000 KRW 이하 | `bom/cash_budget.csv` rollup |
| SYS-PRINT-01 | 각 출력품 각 축 210 mm 이하 | FCStd shape bounding box 검사 |
| SYS-PRINT-02 | 출력품 총 질량 목표 1.5 kg, 2.0 kg review threshold | CAD volume 기반 manifest |
| SYS-PATH-01 | PLA/PET가 hopper부터 spooler까지 동일 기계 경로 사용 | architecture contract/CAD/UI review |
| SYS-BATCH-01 | batch 도중 material profile 변경 금지 | firmware host test |
| SYS-CHANGE-01 | 전환 시 feed stop, purge, hopper/screen 청소, 확인 강제 | firmware host test/manual |
| SYS-SAFE-01 | E-stop, lid/service interlock, thermal fuse, branch fuse가 독립 hardware cut path 보유 | wiring review와 물리 Gate 4 |
| SYS-RATE-01 | 200 g/h 이상을 stretch target으로 유지 | 계산과 30분 실측을 분리 보고 |

## 기능 baseline

- 재료: 사용자가 확인한 순수 PLA 또는 세척·label/cap/neck-ring 제거 PET만 사용한다.
- Hopper: sliding lid, anti-reach baffle, nominal usable 1.0 kg, refill 허용.
- Cutter: 한 개의 compact dual-shaft asymmetric cycloidal-derived hook cutter, removable 5 mm screen, oversize 수동 recirculation.
- Shredder actuator 기준선: `MY1016Z-24V-250W-75RPM` brushed geared-DC direct drive, KTR ROTEX19 98ShA bore17/20 coupling, hardened M3 Z16 1:1 phase gear pair. PLA/PET cutter 명령은 32/24 rpm이고 16/18 A profile trip, 20 A branch fuse를 사용한다. 한 phase gear의 6 x 6 x 4 mm brass key가 24 N·m nominal sacrificial relief이며 coupon으로 실제 전단 torque를 확인한다.
- Drying: 외부 qualified dryer 후 sealed hopper; 장치 내 45/60 °C maintenance heating만 제공.
- Extruder: 16 mm, 16 L/D 공용 single screw, common breaker/screen과 open die.
- Forming: 금속 90 degree down-die 후 굽힘 없는 vertical cooling/gauge/puller, 그 뒤에만 guide roller로 방향 전환.
- Gauge: 2축 LED/photodiode shadow gauge. 출력은 `d_x`, `d_y`, `d_mean`, ovality, calibration uncertainty.
- Spooler: puller가 직경을 결정하고 spooler는 dancer를 추종한다. 일반 1 kg spool을 cabinet 안에 둔다.
- Controller: Arduino Mega 2560. 첫 화면은 PLA/PET/Maintenance/Calibration이다.

## 물리적으로 미확정인 입력

Donor extruder/puller/spooler motor와 fan, switch, PSU 상태는 사진·label·실측 전 확정하지 않는다. Shredder motor는 위 신규 구매 후보를 기준으로 CAD와 cash BOM에 포함하되, 같은 모델명 제품의 shaft/감속 사양 변동 때문에 입고검사 전 coupling hole과 full cutter 발주를 금지한다. `bom/reuse_inventory.csv`의 `UNVERIFIED` 품목은 0원 확정 재고로 계산하지 않는다.
