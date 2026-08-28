# Shredder geared-DC drive wiring — solid-manifold-openmodelica-v0.4

## 기준 actuator

- Motor: interchangeable 18–30 V reversible brushed geared-DC donor. #35 12T:18T/24T/30T를 선택해 cutter 20–40 rpm, cutter 환산 continuous 14 N·m을 만족해야 한다. `DRV-F01`은 motor side에 있고 `DRV-02`는 cutter-side output hub다.
- Project-lab/donor 우선순위: wheelchair/conveyor geared motor → scooter/e-bike geared motor → 동급 24 V geared motor. Exact model, label, 수량, 상태, 축경, 무부하 전류·RPM, 30 min 온도를 확인하기 전에는 현금 0원으로 확정하지 않는다.
- Driver: BTS7960-class bidirectional H-bridge candidate, **module 입고 후 20 A/60 s thermal load test 필수**
- Current feedback: isolated 50 A Hall sensor 우선, 대안은 calibrated low-side shunt + differential amplifier
- Speed feedback: cutter driven shaft에 6-pole magnet ring + Hall switch 1개. Motor supply current만 torque로 간주하지 않는다. Donor별 no-load current, torque/A, ratio와 efficiency를 torque arm으로 calibration하고 cutter RPM drop과 함께 판정한다.

## Hardwired power path

```text
24 V PSU+
  -> main DC fuse
  -> latching E-stop controlled DC cut relay / verified high-current switch
  -> 20 A shredder branch fuse
  -> service/lid interlock hard inhibit contact
  -> H-bridge B+
  -> accepted donor geared-DC motor

Motor return -> 50 A Hall current sensor -> H-bridge B-
Mega PWM/DIR  -> opto/logic interface -> H-bridge inputs
Mega ENABLE   -> hard-inhibit series gate (logic command only, not sole safety layer)
Driven-shaft Hall -> Mega interrupt input
```

E-stop과 lid/service interlock은 firmware가 멈춰도 H-bridge의 motor energy를 제거한다. Reverse command는 contact가 닫히고 current가 2 A 아래로 떨어진 뒤 150 ms dead-time 후에만 허용한다.

## Profile과 fault

| 항목 | PLA | PET |
|---|---:|---:|
| Cutter command | 32 rpm | 24 rpm |
| Calibrated continuous torque | 11 N·m | 13 N·m |
| Calibrated jam trip torque | 18 N·m | 18 N·m |
| Overload duration | 650 ms | 850 ms |
| Reverse | 800 ms | 1100 ms |
| Retry | 3 | 3 |

Reference sensitivity current는 donor 공통 threshold가 아니다. `verified=true` calibration record가 없으면 start를 거부한다. 세 번째 retry에서 latched fault다. 또한 명령 대비 cutter speed가 35% 아래로 500 ms 이상 내려가면 torque estimate가 threshold 아래여도 jam으로 처리한다. Reset은 E-stop release만으로 되지 않고, 전원 차단·guard open·jam 제거·guard close·작업자 확인이 모두 필요하다.

## 600 W PSU arbiter

Shredder branch의 power-budget sensitivity peak는 24 V x 18 A = 432 W다. 이 18 A는 reference driver/PSU envelope이며 universal torque threshold가 아니다. Shredder enable 중 barrel heater와 screw motor enable을 금지한다. 반대로 barrel heater 또는 screw motor가 켜져 있으면 H-bridge hardware-enable을 내린다. 이 mutual exclusion은 batch flake bin 운전과 일치하며 전체 peak를 PSU 아래로 제한한다.

## 입고검사와 calibration

1. Label에서 exact model, rated voltage/power/current/speed, duty와 시리얼을 촬영한다.
2. Shaft diameter/length, key or D-flat, mount pattern, rotation, motor/gearbox envelope를 측정하고 `bom/donor_drive_acceptance.csv`에 기록한다.
3. Guard 안 무부하로 12/18/24 V speed와 current, 방향을 기록한다.
4. Torque arm + load cell로 cutter-equivalent 5/10/15/18/22 N·m에서 current와 RPM을 기록하고 no-load subtraction/ratio/efficiency를 포함한 calibration record를 만든다.
5. 14/18/22/34/48 N·m는 cutter-shaft reference다. DRV-F01 motor-side shear setting을 12:18/24/30에서 각각 17.25/12.94/10.35 N·m로 quasi-static calibration하고, 22 N·m cutter-equivalent에서 분리되며 DRV-02/phase path는 그대로 동기화되는지 확인한다.
6. H-bridge heatsink 온도가 20 A/60 s에서 80 °C 미만인지 확인한다.
7. 20 A branch fuse, E-stop, lid/service contact를 각각 열어 motor energy가 제거되는지 확인한다. Gate-1은 `exports/jigs/gate1/wiring_24v_hardcut.svg`의 S0/S1→K0→K1 manual-reset 회로를 추가로 따른다.

입고 또는 calibration이 하나라도 실패하면 motor-side adapter/hub와 full `CUT-01` stack을 발주하지 않는다. `CUT-05`는 Gate-1 실제 jig의 축으로 필요하므로 최소 수량 2개만 별도 사용 승인 후 가공할 수 있다.
