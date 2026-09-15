# Runtime state machine — v0.8

Machine: `IDLE → SHREDDING | PREHEATING → EXTRUSION → COOLDOWN → IDLE`. Forming 이상은 `FORMING_CHAIN_RUNDOWN (10 s bounded) → THERMAL_HOLD → REQUALIFYING → READY_TO_RETHREAD` 뒤 explicit confirmation으로만 복귀한다. 모든 상태는 `FAULT/ESTOP`으로 전이하며 자동 재시작하지 않는다.

Material change: `PURGE_PREHEAT_REQUIRED → PURGE_READY_CONFIRM_REQUIRED → PURGE_RUNNING → SCREEN_CLEAN_REQUIRED → HOPPER_CLEAN_REQUIRED → TEMPERATURE_TRANSITION_REQUIRED → FINAL_CONFIRM_REQUIRED`. 중단/E-stop/fault clear는 시작 단계로 복귀한다.

Invalid EEPROM은 material NONE/calibration unverified/output inhibit다. Any safety input false면 command는 zero이며 K0가 독립적으로 energy를 제거한다. Shredder와 heater/screw enable은 상호 배제한다. Cooling command는 proof가 아니며 A4 current와 두 fan tach가 필요하다. Serial clear는 physical lockout을 우회하지 못한다. Exact predicates는 released `process_state.cpp`와 `machine_supervisor.cpp`가 지배한다. Physical validation은 NOT_RUN이다.
