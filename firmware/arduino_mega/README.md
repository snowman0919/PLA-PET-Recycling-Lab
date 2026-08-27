# Arduino Mega 펌웨어

`filament_recycler_mega.ino`가 Arduino integration source이고 `src/control_core.*`, `src/protocol.*`, `src/ui_core.*`는 host에서도 시험 가능한 안전·제어·UI core다.

구현 범위:

- `SAFE_OFF→SELF_TEST→READY→RUNNING/PAUSED→FAULT/ESTOP_LATCHED` FSM
- 750 ms Pi heartbeat timeout, sequence replay/CRC/길이 검사
- E-stop, lid, service, thermal chain, pressure와 airflow local interlock
- contactor aux feedback의 welded-open/close-timeout 감시
- PLA/PET별 4-zone bounded PI와 상호배제 dryer branch PI, sensor range/rate와 no-rise thermal-runaway 검사
- phase 상호배제와 provisional 480 W software ceiling의 heater power scaling
- current RMS/peak/derivative + tach speed ratio + vibration 기반 feed limit, 300 ms stop, 800 ms reverse, 최대 3회 retry
- AVR 2 s hardware watchdog와 모든 출력 safe-low 초기화
- TFT-independent 9-page view model, fault 강제화면, startup 금지원료/환기 확인, rotary/button debounce
- material/color/batch 요청, calibration/maintenance energy gate와 material-change purge latch

Host core test:

```bash
make -C firmware/arduino_mega test
```

## 의도된 commissioning lock

`src/configuration.h`의 sensor qualification flag는 모두 `false`다. 따라서 현재 `.ino`는 온도/압력/current/airflow와 shredder motion feedback이 미선정인 상태에서 self-test를 통과하지 않는다. 실제 part number, 전압변환, open/short signature, tach PPR, 교정계수와 fault-injection 결과를 확보한 뒤 해당 conversion을 구현하고 flag를 하나씩 연다. 임시 상수나 Pi telemetry로 local safety sensor를 우회하지 않는다.

고전류 출력은 Mega pin에서 직접 구동하지 않는다. Opto-isolated/logic-compatible driver, gate pulldown, branch fuse와 독립 thermal chain을 거치며 E-stop safety relay가 driver enable/high-current bus를 firmware 밖에서 끊는다. `kProvisionalDeratedPowerLimitW=480`은 600 W 사용자 진술의 80% 계산값일 뿐 wire/fuse/PSU 정격이 아니다.

## Build 상태

Portable core와 전체 `.ino` integration은 Arduino API stub 아래 `g++ -std=c++17 -Wall -Wextra -Werror`로 검증한다. UI test는 모든 필수 화면, fault preemption, 입력 debounce, startup/purge run gate를 확인한다. 실제 Arduino AVR core/board compile은 board package version이 release 환경에 고정될 때 추가한다. TFT controller/logic level이 확인되기 전에는 CS를 deselect하고 reset을 assert한 채 `UiFrame` renderer adapter만 비워 둔다. 실제 TFT driver, sensor front-end, motor driver pulse timing과 high-PPR tach ISR은 donor inventory 이후 pin-compatible adapter에서 완성해야 하며 현재 물리 운전 승인을 뜻하지 않는다.
