# Arduino Mega 펌웨어

`filament_recycler_mega.ino`가 Arduino integration source이고 `src/control_core.*`와 `src/protocol.*`는 host에서도 시험 가능한 안전·제어 core다.

구현 범위:

- `SAFE_OFF→SELF_TEST→READY→RUNNING/PAUSED→FAULT/ESTOP_LATCHED` FSM
- 750 ms Pi heartbeat timeout, sequence replay/CRC/길이 검사
- E-stop, lid, service, thermal chain, pressure와 airflow local interlock
- contactor aux feedback의 welded-open/close-timeout 감시
- 4-zone bounded PI, sensor range/rate와 no-rise thermal-runaway 검사
- phase 상호배제와 provisional 480 W software ceiling의 heater power scaling
- current+speed 기반 feed limit, 300 ms stop, 800 ms reverse, 최대 3회 retry
- AVR 2 s hardware watchdog와 모든 출력 safe-low 초기화

Host core test:

```bash
make -C firmware/arduino_mega test
```

## 의도된 commissioning lock

`src/configuration.h`의 sensor qualification flag는 모두 `false`다. 따라서 현재 `.ino`는 온도/압력/airflow front-end가 미선정인 상태에서 self-test를 통과하지 않는다. 실제 part number, 전압변환, open/short signature, 교정계수와 fault-injection 결과를 확보한 뒤 해당 conversion을 구현하고 flag를 하나씩 연다. 임시 상수나 Pi telemetry로 local safety sensor를 우회하지 않는다.

고전류 출력은 Mega pin에서 직접 구동하지 않는다. Opto-isolated/logic-compatible driver, gate pulldown, branch fuse와 독립 thermal chain을 거치며 E-stop safety relay가 driver enable/high-current bus를 firmware 밖에서 끊는다. `kProvisionalDeratedPowerLimitW=480`은 600 W 사용자 진술의 80% 계산값일 뿐 wire/fuse/PSU 정격이 아니다.

## Build 상태

Portable core는 `g++ -std=c++17 -Wall -Wextra -Werror`로 검증한다. Arduino board compile은 Arduino AVR core/board package가 release 환경에 고정될 때 추가한다. TFT driver, 실제 sensor front-end, motor driver pulse timing과 encoder ISR은 donor inventory 이후 pin-compatible adapter에서 완성해야 하며 현재 물리 운전 승인을 뜻하지 않는다.
