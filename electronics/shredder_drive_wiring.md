# Shredder geared-DC drive wiring — v0.3

## 기준 actuator

- Motor: `MY1016Z-24V-250W-75RPM`, brushed geared DC, 24 V, 250 W, rated current 13.4–14.8 A, S2:60, IP33
- Driver: BTS7960-class bidirectional H-bridge candidate, **module 입고 후 20 A/60 s thermal load test 필수**
- Current feedback: isolated 50 A Hall sensor 우선, 대안은 calibrated low-side shunt + differential amplifier
- Speed feedback: cutter driven shaft에 6-pole magnet ring + Hall switch 1개. Motor supply current만 torque로 간주하지 않고 cutter RPM drop과 함께 판정한다.

## Hardwired power path

```text
24 V PSU+
  -> main DC fuse
  -> latching E-stop controlled DC cut relay / verified high-current switch
  -> 20 A shredder branch fuse
  -> service/lid interlock hard inhibit contact
  -> H-bridge B+
  -> MY1016Z motor

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
| Current threshold | 16 A | 18 A |
| Overload duration | 650 ms | 850 ms |
| Reverse | 800 ms | 1100 ms |
| Retry | 3 | 3 |

세 번째 retry에서 latched fault다. 또한 명령 대비 cutter speed가 35% 아래로 500 ms 이상 내려가면 current가 threshold 아래여도 jam으로 처리한다. Reset은 E-stop release만으로 되지 않고, 전원 차단·guard open·jam 제거·guard close·작업자 확인이 모두 필요하다.

## 600 W PSU arbiter

Shredder branch의 software peak는 24 V x 18 A = 432 W다. Shredder enable 중 barrel heater와 screw motor enable을 금지한다. 반대로 barrel heater 또는 screw motor가 켜져 있으면 H-bridge hardware-enable을 내린다. 이 mutual exclusion은 batch flake bin 운전과 일치하며 전체 peak를 PSU 아래로 제한한다.

## 입고검사와 calibration

1. Label에서 model, 24 V, 250 W, 75 rpm variant를 촬영한다.
2. Shaft Ø17 x 44 mm, key, mount spacing 20/73.5 mm와 motor envelope를 측정한다.
3. Guard 안 무부하로 12/18/24 V speed와 current, 방향을 기록한다.
4. Torque arm + load cell로 5/10/15/20 N·m에서 current와 RPM을 기록한다.
5. H-bridge heatsink 온도가 20 A/60 s에서 80 °C 미만인지 확인한다.
6. 20 A branch fuse, E-stop, lid/service contact를 각각 열어 motor energy가 제거되는지 확인한다.

입고 또는 calibration이 하나라도 실패하면 `CUT-05`, coupling/hub, full `CUT-01` stack을 발주하지 않는다.
