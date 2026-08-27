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
