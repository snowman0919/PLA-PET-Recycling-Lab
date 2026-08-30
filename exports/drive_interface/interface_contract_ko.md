# 교환식 분쇄기 구동 인터페이스 — virtual-physics-closure-v0.5.1

공정 경로와 dual-shaft cutter는 변경하지 않는다. 특정 MY1016Z, KTR coupling, KHK gear의 part number는 요구조건이 아니다.

## 선정 기준과 기준모터

- 18–30 V brushed DC gearmotor, reversible
- cutter 환산 continuous torque >=14 N·m, 3 s peak >=24 N·m
- interface ratio 선택 후 cutter 20–40 rpm continuous, no-load <=80 rpm
- shaft 10–20 mm이며 key, D-flat 또는 clamping hub 사용 가능
- 정상 운전전류가 20 A branch 안에 있고 실제 current/torque calibration 가능
- S2 60 min 이상 또는 30분 coupon에서 winding/gearcase <=80 °C
- label, 수량 1, 정상 회전, backlash, shaft 치수, 무부하 전류가 기록된 project-lab/donor만 현금 0원 인정

우선순위는 (1) project-lab wheelchair/conveyor geared DC motor, (2) 검증된 24 V scooter/e-bike geared motor, (3) 검증된 60 mm급 신규 gearmotor다. MY1016Z, 특정 coupling, 특정 phase gear 제조사는 요구조건이 아니다. NEMA17과 정격토크가 부족한 42GP-775는 full shredder actuator로 합격하지 않는다.

치수와 동역학의 정확한 digital reference는 `TT Motor GMP60-60127-2460`, 24 V, ratio 47이다. 제조사 공개값은 no-load 95 rpm, rated 70 rpm, rated 100 kg·cm(9.80665 N·m), rated current 8.2 A, stall current 31 A다. 12T:30T와 screening efficiency 0.85에서 cutter 정격점은 28 rpm, 20.84 N·m다. 이는 구매 승인이 아니며 수령품 라벨·축·전류·온도와 Gate-1을 통과해야 한다.

요청된 42GP-775 계열용 `DRV-A42`도 남기지만, 공식 `GMP42-775PM ratio 51` 값(90 rpm, 26 kg·cm=2.5497 N·m)은 같은 12T:30T에서 cutter 환산 5.42 N·m뿐이라 14 N·m 기준에 불합격한다. 다른 42GP 변형은 공급자가 6.59 N·m 이상의 연속 출력축 토크와 열정격을 문서로 증명할 때만 재평가한다.

## 기계 interface

`DRV-01` plate에는 motor-specific standard angle/saddle과 `DRV-Axx` donor adapter만 추가한다. 공통 plate의 Ø65 관통부는 60 mm급 gearcase가 plate와 충돌하지 않게 하고, 실제 face pilot와 bolt pattern은 DRV-Axx가 담당한다. Motor torque는 `DRV-F01` replaceable motor-side shear element와 #35 chain의 12T input, 교환 가능한 18T/24T/30T output sprocket을 거쳐 right CUT-05 shaft로 전달한다. `DRV-02`는 cutter-side Ø20 shaft와 PCD36 sprocket blank를 분리하는 output hub이며 sacrificial element가 아니다. Shaft가 다른 donor에는 `DRV-Axx`만 바꾼다. 두 cutter shaft의 counter-rotation/phase는 특정 공급사 대신 M3 Z16, 20°, face>=18 mm steel gear functional specification으로 조달하거나 `DRV-03` 3-lamination/gear를 사용한다. DRV-03 각 lamination은 공통 6 mm keyway로 CUT-05 torque를 전달하고, PCD30의 2x M4 clamp hole과 1x Ø3 H7 dowel hole로 적층 위상을 재현한다. 치면 맞물림이나 clamp friction만으로 torque/phase를 전달하지 않는다.

Chain efficiency 0.85 screening에서 12T:18T, 12T:24T, 12T:30T의 motor output continuous/3 s capability는 각각 최소 11.0/18.8, 8.3/14.2, 6.6/11.3 N·m여야 한다. Motor speed 30–60/40–80/50–100 rpm이 cutter 20–40 rpm을 만든다. 24 V label power는 150 W 이상을 screening 시작점으로 쓰되 합격은 label watt가 아니라 Gate-1 torque/current/RPM/temperature 결과로 정한다. 후보별 기록표는 `bom/donor_drive_acceptance.csv`와 `donor_measurement_form.csv`다.

14/18/22/34/48 N·m hierarchy는 모두 **cutter-shaft equivalent torque**다. 따라서 `DRV-F01`의 실제 motor-side mechanical setting은 efficiency 0.85에서 12:18=17.25, 12:24=12.94, 12:30=10.35 N·m다. DRV-F01이 작동해도 DRV-02, chain, phase pair의 위상 경로는 유지되어야 한다. Chain guard, 20 A fuse, E-stop/lid/service hard inhibit와 calibrated torque+RPM jam detection을 유지한다. Shear 재료·직경·groove는 Gate-1 quasi-static calibration으로 확정한다. Donor 확인과 Gate-1 전 full quantity 발주 금지다.

## 형상과 발주 잠금

Active assembly의 red body는 GMP60-60127 공개 치수인 motor Ø60.5×127, gearbox Ø60×59, front pilot Ø32×4.85, shaft Ø12×25.8을 모델링한다. `DRV-A60`은 Ø32.2 pilot와 4×M5 PCD45를 제공한다. 다른 donor에는 이 모터 솔리드를 억지로 재사용하지 않고 `DRV-Axx`와 수령검사표만 바꾼다. Source URL과 확인일은 `reference_variant.json`에 고정한다. Donor 실측과 Gate-1 전에는 motor, full cutter stack, screw/barrel 발주를 승인하지 않는다.
