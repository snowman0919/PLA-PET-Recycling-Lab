# Interchangeable shredder drive interface — solid-manifold-openmodelica-v0.4

공정 경로와 dual-shaft cutter는 변경하지 않는다. 특정 MY1016Z, KTR coupling, KHK gear의 part number는 요구조건이 아니다.

## 합격 가능한 donor motor

- 18–30 V brushed DC gearmotor, reversible
- cutter 환산 continuous torque >=14 N·m, 3 s peak >=24 N·m
- interface ratio 선택 후 cutter 20–40 rpm continuous, no-load <=80 rpm
- shaft 10–20 mm이며 key, D-flat 또는 clamping hub 사용 가능
- 20 A branch 안에서 실제 current/torque calibration 가능
- S2 60 min 이상 또는 30분 coupon에서 winding/gearcase <=80 °C
- label, 수량 1, 정상 회전, backlash, shaft 치수, 무부하 전류가 기록된 project-lab/donor만 현금 0원 인정

우선순위는 (1) project-lab wheelchair/conveyor geared DC motor, (2) 검증된 24 V scooter/e-bike geared motor, (3) 기존 MY1016Z급 donor다. NEMA17은 full shredder actuator로 합격하지 않는다.

## 기계 interface

`DRV-01` plate에는 motor-specific standard angle/saddle과 `DRV-Axx` donor adapter만 추가한다. Motor torque는 `DRV-F01` replaceable motor-side shear element와 #35 chain의 12T input, 교환 가능한 18T/24T/30T output sprocket을 거쳐 right CUT-05 shaft로 전달한다. `DRV-02`는 cutter-side Ø20 shaft와 PCD36 sprocket blank를 분리하는 output hub이며 sacrificial element가 아니다. Shaft가 다른 donor에는 `DRV-Axx`만 바꾼다. 두 cutter shaft의 counter-rotation/phase는 특정 공급사 대신 M3 Z16, 20°, face>=18 mm steel gear functional specification으로 조달하거나 `DRV-03` 3-lamination/gear를 사용한다. DRV-03 각 lamination은 PCD30의 2x M4 clamp hole과 1x Ø3 H7 dowel hole로 위상을 재현하며, 치면 맞물림만으로 정렬하지 않는다.

Chain efficiency 0.85 screening에서 12T:18T, 12T:24T, 12T:30T의 motor output continuous/3 s capability는 각각 최소 11.0/18.8, 8.3/14.2, 6.6/11.3 N·m여야 한다. Motor speed 30–60/40–80/50–100 rpm이 cutter 20–40 rpm을 만든다. 24 V label power는 150 W 이상을 screening 시작점으로 쓰되 합격은 label watt가 아니라 Gate-1 torque/current/RPM/temperature 결과로 정한다. 후보별 기록표는 `bom/donor_drive_acceptance.csv`와 `donor_measurement_form.csv`다.

14/18/22/34/48 N·m hierarchy는 모두 **cutter-shaft equivalent torque**다. 따라서 `DRV-F01`의 실제 motor-side mechanical setting은 efficiency 0.85에서 12:18=17.25, 12:24=12.94, 12:30=10.35 N·m다. DRV-F01이 작동해도 DRV-02, chain, phase pair의 위상 경로는 유지되어야 한다. Chain guard, 20 A fuse, E-stop/lid/service hard inhibit와 calibrated torque+RPM jam detection을 유지한다. Shear 재료·직경·groove는 Gate-1 quasi-static calibration으로 확정한다. Donor 확인과 Gate-1 전 full quantity 발주 금지다.

## 치수 근거가 있는 reference variant

Parvalux `781096-735901` BRx70-60 24 V + GB12 30:1 PMDC gearmotor를 구매 의존성이 없는 envelope reference로만 둔다. 공식 공개값은 100 rpm, 9.8 N·m S1, 17.2 N·m intermittent, 270 x 81 x 138 mm다. 12T:30T에서 cutter 40 rpm이며 계산상 capability는 충분하지만 가격이 예산을 크게 넘으므로 선정품/BOM/0원 donor가 아니다. Assembly의 red box는 이 공식 overall envelope이며 proprietary body 형상을 가장하지 않는다. Source URL과 확인일은 `reference_variant.json`에 고정한다.
