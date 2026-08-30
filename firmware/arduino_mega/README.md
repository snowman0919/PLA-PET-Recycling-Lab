# Mega realtime core

`MachineSupervisor`가 process, shredder, heater, gauge/diameter, forming-chain을 단일 순수 C++ 경로에서 조정한다. `.ino`는 물리 입력을 `InputSnapshot`으로 옮기고 반환된 `ActuatorCommands`를 적용하는 adapter다. 부팅 재질은 반드시 `MaterialProfile::NONE`이며 PLA/PET를 명시적으로 선택하기 전에는 운전을 시작할 수 없다.

Drive, gauge, current-sensor, cooling-feedback calibration readiness는 서로 독립이다. EEPROM record v2는 version과 CRC가 일치하지 않으면 전체를 거부하며, 재질 선택은 어떤 calibration도 암시하지 않는다. Shredding start와 extrusion arm은 subsystem 승인이 끝난 뒤에만 process phase를 commit한다. Fault clear는 모든 subsystem의 `canClearFaults` preflight가 통과한 뒤 한 번에 commit하며 clear 자체가 actuator를 재시작하지 않는다.

재질 변경은 `PURGE_PREHEAT_REQUIRED -> PURGE_READY_CONFIRM_REQUIRED -> PURGE_RUNNING -> SCREEN_CLEAN_REQUIRED -> HOPPER_CLEAN_REQUIRED -> TEMPERATURE_TRANSITION_REQUIRED -> FINAL_CONFIRM_REQUIRED` 순서를 강제한다. Purge 전에 작업자가 물리 `START`로 purge feed를 승인하고 별도 `CONFIRM`으로 기존 waste tray/manual waste path를 확인해야 한다. 80 g/120 g은 명목 engineering estimate일 뿐 측정 질량이 아니며, 완료 증거는 최소 120초, command-derived screw 32회전, 온도 band 유지, drive/heater 정상 및 육안 확인이다. 중단·E-stop·fault clear 뒤에는 pending material을 활성화하지 않고 `PURGE_PREHEAT_REQUIRED`로 돌아간다.

Forming-chain fault는 공통 `RUNDOWN -> THERMAL_HOLD -> REQUALIFYING -> READY_TO_RETHREAD` 정책을 사용한다. Feeder와 production winding은 즉시 꺼지고 screw는 10초 bounded rundown을 수행한다. Gauge 20개 연속 유효 sample(200 ms cadence), U95/diameter/ovality 10초 안정, PLA/PET transport delay, cooling feedback, puller 비포화가 모두 충족되어도 spool은 계속 금지된다. 작업자의 explicit rethread 확인 이후에만 `spool_eligible=true`가 된다. Dancer 0.32 rad는 warning, 0.36 rad는 controlled stop이며 0.4363 rad hard-stop 접촉은 정상 정지가 아니라 physical-lockout clear가 필요한 latched fault다. 일반 FAULT는 feedback-valid cooling만 잔열 제거를 위해 유지하고 cooling-failure reason 및 E-stop은 cooling도 0으로 만든다. COOLDOWN은 T1–Tdie valid/60 °C 이하와 cooling 정상 조건에서만 IDLE로 끝나며 자동 재시작하지 않는다.

Cooling health는 command PWM으로 추정하지 않는다. Production adapter는 독립 `CAL COOLING <zero_adc> <amps_per_count>` EEPROM calibration이 있을 때만 A4 fan-current feedback을 읽고 계약의 0.2–2.0 A window 및 dwell을 적용한다. PREHEAT/PURGE 요청은 IDLE에서 fan-only startup probe를 먼저 명령하고 healthy feedback이 1.5초 연속 확인된 뒤에만 phase를 commit한다. 3초 timeout 전에는 heater/screw/feed/puller/spool/traverse가 모두 금지되며 실패는 FAULT로 끝나고 자동 재시작하지 않는다. Fan-off FAULT clear에는 live current를 요구하지 않지만 다음 explicit start가 새 probe를 강제한다. Calibration 누락, sensor 미장착/단선은 healthy가 아니다. Process-state별 heater aggregate cap과 rotating priority arbitration은 다른 peak load를 포함한 500 W 한계와 100 W reserve를 보존하면서 특정 heater channel starvation을 막는다.

현재 donor screw tach는 확인되지 않았다. 따라서 Mega adapter의 purge revolution 값은 실제 측정값이 아니라 command와 시간으로 적분한 `estimated screw revolutions`이며 view의 `purge_screw_revolutions_measured=false`로 공개된다. Driver fault가 발생하면 purge phase가 fault로 전이하지만, 이 estimate만으로 stall 부재를 실측했다고 주장하지 않는다. 실제 commissioning에서 verified tach가 추가되면 `InputSnapshot::screw_speed_is_measured` backend로 교체하고 calibration/배선 증거를 남겨야 한다.

Home UI 항목은 PLA, PET, Maintenance, Calibration이다. 물리 PAUSE 또는 material-change 화면의 BACK은 cooling probe와 purge를 안전 중단한다. Serial text status는 UI/process/material/forming 상태, 개별 calibration readiness, cooling feedback/probe dwell, purge approval/completion과 invariant 결과를 노출한다. TFT 화면은 material/state, screw RPM, shredder load, zone/die temperature, feeder, `d_x/d_y/d_mean/ovality/U95`, spool progress와 latched fault를 표시해야 한다. 이 repository의 host core는 state/safety invariant를 검증하며 TFT driver·pin map은 donor model 확인 뒤 추가한다.

E-stop, lid/service interlock, branch fuse와 thermal fuse는 이 firmware와 독립된 hardware cut chain이다.

`shredder_control`은 DRV-01/#35 chain interchangeable geared-DC interface를 대상으로 PLA/PET 32/24 rpm을 사용한다. 전류의 고정 A값을 토크로 간주하지 않고, donor별 no-load current, motor torque/A, 감속비, 효율을 Gate-1에서 calibration한 뒤에만 시작한다. Profile의 18 N·m jam 한계, 명령속도 대비 35% 이상 RPM drop, profile별 reverse duration과 최대 3회 retry를 처리한다. 세 번째 reverse 종료 뒤 fault를 latch하며, heater 또는 screw enable과 shredder enable은 상호 배제한다. `REFERENCE_DRIVE_CALIBRATION`은 디지털 sensitivity용이며 `verified=false`라서 실제 운전에 사용할 수 없다.

`src/generated_profiles.h`는 `generate_config.py`가 `cad/parameters/baseline.json`, `control/process_contract.json`, `control/fault_response_contract.json`에서 생성한다. Modelica `GeneratedControl.mo`의 유일 writer는 `control/generate_contract_artifacts.py`이며 두 generator가 같은 파일을 덮어쓰지 않는다. Screw setpoint는 PLA 16 rpm/PET 18 rpm, shredder는 PLA 32 rpm/PET 24 rpm이며, 외부 pre-dry는 현재 둘 다 `UNQUALIFIED_EXTERNAL_PROCESS`다.

실제 Mega target은 repository root sketch `arduino_mega.ino`다. `src/board_config.h`가 pin mapping을, compile-time display abstraction이 reference serial/text backend를 제공한다.

```bash
python3 generate_config.py
make test
make arduino   # arduino-cli + arduino:avr core 필요
```
