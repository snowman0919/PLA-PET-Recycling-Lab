# 시스템 요구사항 — safety-orchestration-closure-v0.6.1

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
|SYS-BATCH-01|RUN 중 material profile 변경 금지; 실제 `MAINTENANCE_PURGE`가 waste-path 확인, 시간·회전·온도·fault·시각조건을 만족한 뒤 screen→hopper→temperature→explicit final confirm 순서 강제|firmware runtime trace + OpenModelica|
|SYS-SAFE-01|E-stop, lid/service interlock, thermal fuse, branch fuse는 software 독립 hard cut|wiring review + physical gate|
|SYS-TORQUE-01|14 continuous <18 electrical <22 mechanical fuse <34 phase <48 shaft/cutter|baseline/Modelica/firmware sync|
|SYS-RATE-01|200 g/h는 stretch target; nominal 계산 및 물리 결과를 분리|RPM sensitivity + Gate-4|
|SYS-RELEASE-01|geometry/fabrication/virtual physics/empirical 상태를 독립 기록; empirical 미수행은 release 비차단|manifest/release validator|
|SYS-FW-01|Mega 2560 실제 I/O, T1–T5, 분리된 drive/gauge/current/cooling calibration CRC, atomic clear, transactional start, explicit extrusion arm과 common forming-chain rundown 구현|Arduino compile + production-class runtime tests|
|SYS-XSV-01|FreeCAD STEP와 OpenModelica LC를 Git/STEP/load hash로 결박; Fusion 미실행은 PENDING|neutral-package/result validator|
|SYS-PURGE-01|Pending material은 purge 및 ordered cleaning/final confirm 완료 전 active가 될 수 없고 생산 spool은 purge 중 비활성|contract equivalence + PLA↔PET scenarios|
|SYS-COOL-01|Cooling PWM 명령과 독립된 A4 current feedback을 교정하고 feedback 부재/범위이탈 dwell은 extrusion/requalification에서 controlled rundown, purge/preheat/cooldown에서 phase-appropriate latched containment를 유발|wiring review + firmware/Modelica fault injection|
|SYS-SPOOL-01|forming fault 뒤 연속 gauge·U95·직경·ovality·puller·cooling·transport-delay requalification 및 operator rethread 전 spooler/traverse 금지|runtime trace + OpenModelica transient metrics|
|SYS-DANCER-01|warning < controlled stop < 0.4363 rad mechanical hard stop이며 정상 spool jam은 hard-stop 접촉 전에 정지|dancer scenario + hard-stop sensitivity 분리|
|SYS-COOLDOWN-01|COOLDOWN은 T1–Tdie valid/≤60 °C와 cooling feedback 정상 후에만 IDLE로 완료되고 어떤 actuator도 자동 재시작하지 않음|runtime transition trace + Modelica scenario|

## 기능 baseline

- 공용 dual-shaft asymmetric cycloidal-inspired hook cutter, removable 5 mm screen, lockout 후 수동 oversize recirculation.
- Interchangeable shredder drive: 18–30 V donor geared brushed-DC, DRV-01/DRV-Axx, motor-side DRV-F01, #35 chain 12T:18/24/30T, cutter-side DRV-02, M3 Z16 phase pair. 특정 motor/coupling/gear MPN 금지.
- Digital reference는 GMP60-60127-2460 ratio 47이며 12:30에서 28 rpm/20.84 N·m rated-point screening이다. GMP42-775PM ratio 51은 5.42 N·m로 연속기준 불합격이며 둘 다 donor 승인이나 구매 release가 아니다.
- 공정 heater는 barrel 3×100 W + die 60 W, T1–T5, independent thermal fuse를 포함하며 extrusion active peak는 490 W 이하로 제한한다.
- Donor current는 직접 torque가 아니다. No-load current, torque/A, ratio, efficiency, speed/temperature를 calibration하고 firmware가 verified record 없이는 start를 거부한다.
- External pre-dry + sealed maintenance hopper. PLA/PET pre-dry 조건은 현재 모두 `UNQUALIFIED_EXTERNAL_PROCESS`; 임의 온도·시간을 qualified recipe로 표시하지 않는다.
- 공용 16 mm×16 L/D single screw, common barrel/breaker/open die. Default profile은 PLA 16 rpm/99.4 g/h, PET 18 rpm/97.5 g/h, fan 100%다.
- 2축 LED/photodiode shadow gauge, puller diameter control, dancer-follow spooler, cabinet 내부 1 kg spool.
- Arduino Mega 2560 realtime controller. Serial text UI backend, MAX6675 5채널, motor/fan/heater/traverse outputs, A4 cooling-current feedback, versioned EEPROM calibration CRC와 host-testable `MachineSupervisor`가 selected material, purge, actuator transaction, atomic clear, rundown과 spool eligibility를 소유한다.

## 물리 미확정 입력

Donor motor/fan/switch/PSU/dryer는 사진·label·실측 전 확정하지 않는다. Shredder donor의 exact model, 수량, 상태, shaft, no-load current/RPM, 30분 온도와 Gate-1 torque record 전 0원 claim과 full cutter release를 금지한다. Cooling current path의 shunt·증폭기·fan normal/open/stall window도 실측 전 `valid=false`다. Digital simulation은 실제 cutting, flake size, melt flow, filament quality 또는 safety certification을 입증하지 않는다.
