# v0.6.2.1 하드웨어 어댑터 검증

이 검증은 host에서 생산 C++ class와 Arduino Mega sketch를 연결한 digital validation이다. 실제 motor, sensor, cutter, heater 또는 전원 인가 시험은 아니다.

- Tach PPR: shredder 6, screw 12, puller 20, spooler 20.
- Hybrid estimator: 저속 reciprocal period, 고속 window count, timeout, debounce, outlier, low-pass, 가속도 제한, `uint32_t micros()` rollover.
- 최대 nominal RPM 오차: shredder 0.8952%, screw 0.9430%, puller 0.9310%, spooler 0.9612%.
- Timeout 기준 최소 측정 RPM: 4.0, 0.7692, 0.75, 0.4 RPM.
- 네 critical drive는 `target -> tach PI -> bounded PWM` 경로를 사용한다. direct linear RPM-to-PWM 경로는 제거했다.
- Arduino Mega 2560 실제 sketch compile과 supervisor 43 scenario/116 trace가 통과했다.
- v4 calibration record는 channel별 source, verified, range, units, revision, CRC를 독립 저장하며 v3를 무효화한다.

P0-J combined harness는 production `MachineSupervisor`, calibration v4, tach estimator, 네 drive controller, cooling/gauge/traverse 상태기를 한 실행 경계에 묶었다. timestamp pulse, integer ADC, quantized PWM/dead-zone, timer rollover를 거쳐 필수 37/37 scenario와 powered phase E-stop 8종이 통과했다. 결과는 `HOST_SIMULATION_PASS`이며 실제 donor ratio, dead zone, loaded curve, tach target, fan airflow 및 limit switch는 commissioning 전 미확정이다.

재현:

```bash
python3 validation/hardware_adapter_v0621.py
python3 validation/hardware_adapter_e2e_v0621.py
python3 validation/runtime_supervisor.py
python3 validation/arduino_compile.py
```
