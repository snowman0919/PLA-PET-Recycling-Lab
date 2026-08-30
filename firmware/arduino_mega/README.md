# Mega realtime core

`MaterialProfile::PLA`와 `MaterialProfile::PET`는 동일 actuator path의 setpoint만 바꾼다. RUN 중 profile은 잠기며 다른 재질을 요청하면 purge -> screen clean -> hopper clean -> confirmation 순서를 모두 통과해야 한다.

Home UI 항목은 PLA, PET, Maintenance, Calibration이다. 운전 화면은 material/state, screw RPM, shredder load, zone/die temperature, feeder, `d_x/d_y/d_mean/ovality/U95`, spool progress와 latched fault를 표시해야 한다. 이 repository의 host core는 state/safety invariant를 검증하며 TFT driver·pin map은 donor model 확인 뒤 추가한다.

E-stop, lid/service interlock, branch fuse와 thermal fuse는 이 firmware와 독립된 hardware cut chain이다.

`shredder_control`은 DRV-01/#35 chain interchangeable geared-DC interface를 대상으로 PLA/PET 32/24 rpm을 사용한다. 전류의 고정 A값을 토크로 간주하지 않고, donor별 no-load current, motor torque/A, 감속비, 효율을 Gate-1에서 calibration한 뒤에만 시작한다. Profile의 18 N·m jam 한계, 명령속도 대비 35% 이상 RPM drop, profile별 reverse duration과 최대 3회 retry를 처리한다. 세 번째 reverse 종료 뒤 fault를 latch하며, heater 또는 screw enable과 shredder enable은 상호 배제한다. `REFERENCE_DRIVE_CALIBRATION`은 디지털 sensitivity용이며 `verified=false`라서 실제 운전에 사용할 수 없다.

`src/generated_profiles.h`와 Modelica `GeneratedControl.mo`는 `cad/parameters/baseline.json` 및 `control/process_contract.json`에서 함께 생성한다. Screw setpoint는 PLA 16 rpm/PET 18 rpm, shredder는 PLA 32 rpm/PET 24 rpm이며, 외부 pre-dry는 현재 둘 다 `UNQUALIFIED_EXTERNAL_PROCESS`다.

실제 Mega target은 repository root sketch `arduino_mega.ino`다. `src/board_config.h`가 pin mapping을, compile-time display abstraction이 reference serial/text backend를 제공한다.

```bash
python3 generate_config.py
make test
make arduino   # arduino-cli + arduino:avr core 필요
```
