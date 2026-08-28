# 안전·전력·제어 배선 기준도

상태: `DESIGN_BASELINE — NOT AUTHORIZED FOR ENERGIZATION`. 실제 mains/24 V 고전류 배선은 선택 부품의 정격·단자·차단용량을 반영한 최종 schematic과 자격 있는 감독의 continuity/insulation/earth 시험 전 수행하지 않는다.

```text
AC inlet
  │
  ├─ PE ────────────────┬─ PSU chassis
  │                     ├─ aluminum frame bonded studs
  │                     └─ dryer/extruder metal shields
  │
  └─ main disconnect + fuse
       └─ 24 V PSU (600 W user statement; LABEL NOT VERIFIED)
            ├─ always-on fused logic branch
            │    ├─ qualified 24→5 V buck ── Raspberry Pi 4
            │    └─ protected Mega supply ── Arduino Mega
            │
            └─ dual-channel latching E-stop safety relay
                 ├─ monitored manual reset
                 ├─ lid/service NC drive-enable chain
                 ├─ K2A Tower A safety-contactor coil
                 │    └─ Tower A switched bus
                 │         ├─ FBR-A1 ─ shredder driver
                 │         └─ FBR-A2 ─ sorter/feeder hazardous motion
                 └─ K2B Tower B safety-contactor coil
                      └─ Tower B switched bus
                           ├─ FBR-B1 ─ extruder driver
                           ├─ FBR-B2 ─ puller/spooler/traverse
                           ├─ FBR-B3..B6 ─ zone fuse ─ thermal fuse ─ Z1/Z2/Z3/die driver/heater
                           ├─ FBR-B7 ─ dryer blower/agitator/feeder
                           ├─ FBR-B8 ─ desiccant regeneration branch
                           ├─ FBR-B9 ─ cooling fans
                           └─ hardware exclusive selector
                                ├─ FBR-B10 ─ PLA trip/fuse ─ PLA dryer heater
                                └─ FBR-B11 ─ PET trip/fuse ─ PET dryer heater
```

K2A/K2B의 mirror NC 보조접점은 safety relay의 EDM/reset feedback loop에 직렬 연결한다. 어느 한 접촉기라도 용착·미복귀하면 수동 reset을 금지한다. Mega `CONTACTOR_REQUEST`는 safety relay의 허가 입력 중 하나일 뿐 E-stop contact를 우회하지 않는다. 모든 driver enable에는 hardware pulldown을 두어 Mega reset, cable open과 unpowered MCU에서 off가 된다. Heater MOSFET/SSR가 welded-on이어도 independent high-limit/thermal fuse와 K2B가 에너지를 제거해야 한다. 후보 AFS30의 24 VDC 부하 차단에는 ABB가 지정한 DC-1 series-pole 구성을 사용해야 하며, 정확한 pole 수와 branch 정격은 실측 전 `TBD`다.

## 안전 입력 논리

Safety relay와 독립 trip의 isolated auxiliary contact는 Mega `INPUT_PULLUP`에 연결해 closed/healthy일 때 LOW, wire open·unpowered optocoupler·open contact에서 HIGH/fault가 되게 한다. 24 V field signal을 Mega pin에 직접 넣지 않는다. E-stop은 dual channel safety function이고 D22는 진단용 단일 aux만 읽는다.

| 하드웨어 기능 | firmware 진단 | 단일 고장 시 기대 상태 |
|---|---|---|
| E-stop safety relay가 K2A/K2B 두 zone bus 차단 | D22 aux + D23 series mirror feedback | MCU stuck-high여도 양 tower의 heater/위험 motor 무전원; 한 접촉기 용착 시 reset 금지 |
| Lid/service NC chain이 shredder enable 차단 | D24/D25 | switch wire open에서 drive 불능 |
| Zone thermal fuse/high-limit relay가 heater 차단 | D26 + zone temperatures | MOSFET welded-on에서도 branch/contact 차단 |
| Mechanical/discrete pressure trip | D27 + A7 transducer | analog firmware fault와 독립 차단 |
| Airflow proof | D28 + A6 diagnostic | dryer/extrusion arm 거부/latched stop |
| Forming guard | D29 | puller/spooler enable 제거 |

## 접지·배선 분리

- PE는 전류 귀환선이 아니며 frame/profile의 산화막 접촉만 믿지 않고 각 enclosure에 crimp lug와 star washer를 쓴다.
- 24 V high-current return과 logic/sensor return은 PSU 인근 단일 star point에서만 결합하고 heater PWM·motor current가 sensor cable을 공유하지 않게 한다.
- Thermocouple/RTD, pressure, current와 encoder cable은 motor/heater cable과 별도 duct로 보내고 교차는 90°로 한다.
- Cable shield는 승인된 한쪽 bonding point에 연결하고 moving cable에는 bend radius·strain relief·abrasion sleeve를 둔다.
- Connector는 keyed·touch-safe이며 양쪽에 harness ID, 전압, pin 1, fuse ID와 모듈명을 표시한다.

## 아직 고정할 수 없는 값

Main/branch fuse, wire gauge, contactor DC utilization category, heater driver, buck, sensor conditioner와 connector current rating은 PSU/donor label과 실제 branch peak가 없으므로 `TBD`다. `24 V×25 A` 산술값이나 `480 W` software cap을 fuse/wire 선정 근거로 사용하지 않는다.
