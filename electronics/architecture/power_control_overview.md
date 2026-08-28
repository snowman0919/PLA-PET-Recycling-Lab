# 학부 MVP 전력·제어 개요

```text
AC input → main disconnect/fuse → 24 V donor PSU
  ├─ protected logic branch → Arduino Mega + monitor PCB
  └─ latching E-stop NC contact → KACT common contactor coil
       └─ switched actuator bus
            ├─ Stage 1 / Stage 2 granulator motor branches
            ├─ dryer, extruder, puller/spooler branches
            └─ four heater branches → fuse → thermal fuse → default-OFF driver
```

KACT 한 개가 두 tower의 위험 액추에이터 전력을 함께 차단한다. E-stop NC 접점은 Arduino를 거치지 않고 coil과 직렬 연결하며, Arduino는 auxiliary contact만 읽는다. 안전 릴레이, tower별 이중 contactor, Raspberry Pi와 자동 분류 전원은 MVP에서 제거했다.

10개 branch fuse 위치, PCB `190×130 mm`, Arduino Mega 실물 envelope, 고전류·안전·logic·PE wire duct, 아직 선정하지 않은 main fuse/terminal은 `electronics/architecture/control_enclosure_layout.csv`에 서로 다른 placement state로 기록한다. 실제 fuse link, contactor pole, wire gauge와 connector 정격은 PSU label과 branch current 측정 후 확정한다.

`24 V 600 W = 25 A`는 명목 산술값이며 label·derating·온도 조건 확인 전 설계 정격으로 사용하지 않는다. Dryer와 extruder full heat-up은 동시에 허용하지 않는다.
