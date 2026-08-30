# 시스템 요구사항 — coupled-digital-validation-v0.5

## Hard constraint

|ID|요구|검증|
|---|---|---|
|SYS-ENV-01|정상운전 전체 ≤500×750×1000 mm, 목표 ≤480×720×950 mm|FreeCAD assembly bounding box|
|SYS-COST-01|conditional target ≤180,000 KRW, contingency 포함 absolute ≤200,000 KRW|`bom/cash_budget.csv` rollup|
|SYS-PRINT-01|각 출력품 각 축 ≤210 mm|FCStd/STL 검사|
|SYS-PRINT-02|출력 toolpath 질량 목표 ≤1.5 kg, review ≤2.0 kg|PrusaSlicer 2.9.6 결과|
|SYS-SOLID-01|active manufacturing CAD는 valid closed solid; keep-out은 review 전용 격리|B-Rep topology audit|
|SYS-MESH-01|모든 active STL은 watertight 2-manifold, zero-area triangle 0, 1 component|mesh parser|
|SYS-PATH-01|PLA/PET가 hopper부터 spooler까지 동일 기계 경로 사용|architecture/CAD/UI review|
|SYS-BATCH-01|RUN 중 material profile 변경 금지; purge/clean 확인 강제|firmware host test|
|SYS-SAFE-01|E-stop, lid/service interlock, thermal fuse, branch fuse는 software 독립 hard cut|wiring review + physical gate|
|SYS-TORQUE-01|14 continuous <18 electrical <22 mechanical fuse <34 phase <48 shaft/cutter|baseline/Modelica/firmware sync|
|SYS-RATE-01|200 g/h는 stretch target; nominal 계산 및 물리 결과를 분리|RPM sensitivity + Gate-4|
|SYS-RELEASE-01|digital release와 physical proof를 분리; physical 전 `PHYSICAL_NOT_RUN`|manifest/release validator|

## 기능 baseline

- 공용 dual-shaft asymmetric cycloidal-inspired hook cutter, removable 5 mm screen, lockout 후 수동 oversize recirculation.
- Interchangeable shredder drive: 18–30 V donor geared brushed-DC, DRV-01/DRV-Axx, motor-side DRV-F01, #35 chain 12T:18/24/30T, cutter-side DRV-02, M3 Z16 phase pair. 특정 motor/coupling/gear MPN 금지.
- Digital reference는 GMP60-60127-2460 ratio 47이며 12:30에서 28 rpm/20.84 N·m rated-point screening이다. GMP42-775PM ratio 51은 5.42 N·m로 연속기준 불합격이며 둘 다 donor 승인이나 구매 release가 아니다.
- 공정 heater는 barrel 3×100 W + die 60 W, T1–T5, independent thermal fuse를 포함하며 extrusion active peak는 490 W 이하로 제한한다.
- Donor current는 직접 torque가 아니다. No-load current, torque/A, ratio, efficiency, speed/temperature를 calibration하고 firmware가 verified record 없이는 start를 거부한다.
- External pre-dry + sealed maintenance hopper. PLA/PET pre-dry 조건은 현재 모두 `UNQUALIFIED_EXTERNAL_PROCESS`; 임의 온도·시간을 qualified recipe로 표시하지 않는다.
- 공용 16 mm×16 L/D single screw, common barrel/breaker/open die. Profile screw RPM은 PLA 18, PET 20이다.
- 2축 LED/photodiode shadow gauge, puller diameter control, dancer-follow spooler, cabinet 내부 1 kg spool.
- Arduino Mega 2560 realtime controller. 첫 화면 PLA/PET/Maintenance/Calibration, selected material lock.

## 물리 미확정 입력

Donor motor/fan/switch/PSU/dryer는 사진·label·실측 전 확정하지 않는다. Shredder donor의 exact model, 수량, 상태, shaft, no-load current/RPM, 30분 온도와 Gate-1 torque record 전 0원 claim과 full cutter release를 금지한다. Digital simulation은 실제 cutting, flake size, melt flow, filament quality 또는 safety certification을 입증하지 않는다.
