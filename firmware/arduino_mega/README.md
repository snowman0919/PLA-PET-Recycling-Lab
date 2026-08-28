# Arduino Mega MVP 펌웨어

`filament_recycler_mega.ino`가 integration source이고 `src/control_core.*`, `src/protocol.*`, `src/ui_core.*`는 host 시험 가능한 core다. Raspberry Pi나 외부 컴퓨터는 운전에 필요하지 않으며 USB serial은 firmware upload·service log용이다.

현재 구현/검증 범위:

- `SAFE_OFF→SELF_TEST→READY→RUNNING/PAUSED→FAULT/ESTOP_LATCHED` FSM
- latching E-stop과 공통 KACT auxiliary feedback 감시; 물리 NC 차단경로를 firmware가 우회하지 않음
- `SHRED`, `DRY_PREHEAT`, `EXTRUDE_SPOOL`, `COOLDOWN_CLEAN` phase와 power arbitration
- Stage 1/Stage 2 구동, bounded jam stop/reverse 최대 3회
- 압출 heater 3채널 + dryer heater 1채널의 default-off 제어
- pressure·airflow·thermal chain·센서 plausibility 및 AVR watchdog
- 수동 PLA/PET·색상·batch UI, dual-axis diameter 표시와 purge latch
- optional serial frame의 sequence/CRC/길이 검사

```bash
make -C firmware/arduino_mega test
```

## Commissioning lock

`src/configuration.h`의 sensor qualification flag는 모두 `false`다. 실제 MPN, 전압변환, open/short signature, tach PPR, 교정계수와 fault-injection 결과가 없으므로 현재 sketch는 물리 self-test를 통과하지 않게 설계했다. 임시 상수로 이 lock을 열지 않는다.

Mega pin은 접촉기·모터·heater를 직접 구동하지 않는다. 외부 driver, pulldown, branch fuse와 thermal fuse를 사용하고, latching NC E-stop이 KACT coil과 직렬로 연결되어 actuator bus를 하드웨어로 끊는다. 현재 host compile 통과는 실제 Arduino 보드·TFT·센서·고전류 부품의 commissioning 승인이 아니다.
