# Interchangeable shredder drive interface — compact-single-path-v0.3

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

`DRV-01` plate에는 motor-specific standard angle/saddle만 추가한다. Motor torque는 #35 chain의 교환 가능한 12T input과 18T/24T output sprocket을 거쳐 right CUT-05 shaft로 전달한다. `DRV-02`는 Ø20 key shaft와 PCD36 four-bolt sprocket blank를 분리하므로 shaft diameter가 다른 donor에는 motor-side hub만 교체한다. 두 cutter shaft의 counter-rotation/phase는 특정 공급사 대신 M3 Z16, 20°, face>=18 mm steel gear functional specification으로 조달하거나 `DRV-03` 3-lamination/gear를 사용한다.

Chain efficiency 0.85 screening에서 12T:18T는 motor output continuous/3 s peak가 최소 11.0/18.8 N·m, 12T:24T는 최소 8.3/14.2 N·m여야 한다. 각각 motor speed 30–60/40–80 rpm이 cutter 20–40 rpm을 만든다. 24 V label power는 150 W 이상을 screening 시작점으로 쓰되 합격은 label watt가 아니라 Gate-1 torque/current/RPM/temperature 결과로 정한다. 후보별 기록표는 `bom/donor_drive_acceptance.csv`다.

Chain guard, 20 A fuse, E-stop/lid/service hard inhibit, current+RPM jam detection과 20–24 N·m sacrificial brass key는 유지한다. Donor 확인과 Gate-1 전 full quantity 발주 금지다.
