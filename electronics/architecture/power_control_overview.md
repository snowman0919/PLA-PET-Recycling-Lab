# 전력·제어 개요

```text
AC input
  -> main disconnect / fuse
  -> 24 V donor PSU
       -> E-stop controlled high-current bus
            -> fused shredder branch
            -> fused extruder motor branch
            -> fused puller/spooler branch
            -> fused heater branches + independent thermal fuses
       -> protected always-on 24 V branch
            -> 5 V buck -> Raspberry Pi 4
            -> Arduino Mega logic / interlock monitoring
```

실제 fuse, contactor, MOSFET, wire gauge와 connector 정격은 branch current와 donor PSU terminal 확인 후 선택한다. `24 V 600 W = 25 A`는 nominal 산술값일 뿐 label/derating/온도 조건 확인 전 설계 정격으로 확정하지 않는다.

Mega는 안전 FSM과 power arbiter를 실행한다. Pi command에는 sequence number와 heartbeat를 요구하고, Mega는 local interlock이 불일치하면 command를 거부한다.

현재 firmware의 provisional software ceiling은 사용자 진술 600 W의 80%인 480 W다. `EXTRUDE_SPOOL` worst-case non-heater reserve 396 W에서는 heater를 84 W까지 비례 제한한다. 이 값은 설계 동작의 보수적 시작점이며 PSU label, 배선·단자 온도상승과 branch peak 측정 후 더 낮은 값으로 바뀔 수 있다. Dryer PLA/PET branch는 software뿐 아니라 hardware selector로 상호배제하고, dryer heater와 extruder full preheat를 동시에 허용하지 않는다.

상세 net과 harness는 `electronics/schematics/safety_power_control.md`, `electronics/wiring/harness_schedule.csv`, pin assignment는 `electronics/pinout/mega_pinout.csv`를 따른다.
