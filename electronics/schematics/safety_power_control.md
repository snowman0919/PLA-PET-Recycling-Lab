# 학부 MVP 안전·전력 배선 기준도

상태: `DESIGN BASELINE — NOT AUTHORIZED FOR ENERGIZATION`

```text
AC inlet
  ├─ PE → PSU chassis + two frames + dryer/extruder shields
  └─ disconnect + main fuse → 24 V PSU (label not verified)
       ├─ always-on logic fuse → Arduino Mega + monitor PCB
       └─ S0 latching E-stop NC ── KACT 24 V coil
            └─ common switched bus
                 ├─ F01 Stage 1 drive
                 ├─ F02 Stage 2 screen granulator drive
                 ├─ F03 dryer blower/feeder
                 ├─ F04 extruder drive
                 ├─ F05 puller/spooler/cooling
                 ├─ F06..F08 extruder heater Z1/Z2/die → thermal fuse → SSR
                 ├─ F09 dryer heater → thermal fuse → SSR
                 └─ F10 control/auxiliary reserve (assignment pending)
```

S0를 누르거나 NC loop가 끊기면 KACT coil이 무전원으로 떨어진다. Arduino `CONTACTOR_REQUEST`는 재시작 허가에만 쓰며 S0 접점을 우회할 수 없다. KACT auxiliary contact는 격리된 monitor PCB를 거쳐 Arduino가 진단한다. 용착 시 자동 재시작을 금지하고 main disconnect를 연 뒤 정비한다.

Heater driver가 붙어도 각 zone의 one-shot thermal fuse와 KACT가 별도로 에너지를 제거해야 한다. 최종 contactor는 실측 총전류에 맞춰 축소 선정하며, DC utilization·pole 구성·coil suppression·용착 시험은 `TBD`다.

## 배선 영역

- `PCB_RESERVED`: 190×130 mm monitor PCB와 4개 M3 hole. 제작 승인 전 HOLD.
- `USER_INVENTORY`: Arduino Mega 102×54 mm nominal envelope. 실물과 connector overhang 확인.
- `PLACEHOLDER_TBD`: main fuse link, terminals, 최종 KACT 정격처럼 아직 주문할 수 없는 항목.
- `WIRE_ROUTE_*`: high-current, hardwired E-stop, 5 V logic/sensor, PE duct. 부품과 겹치면 안 된다.

PE는 profile 접촉에 의존하지 않고 crimp lug와 star washer로 각 금속부에 연결한다. 고전류와 sensor cable은 별도 duct를 사용하며 교차는 90°로 한다.
