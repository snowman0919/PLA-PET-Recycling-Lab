# UI와 profile lock

Revision: `safety-orchestration-closure-v0.6.1`

첫 화면은 `Home`, `Run`, `Material change`, `Calibration`, `Maintenance`, `Fault` 의미를 갖는 최소 text backend다. Cold boot는 material `NONE`과 `CALIBRATION_REQUIRED`를 표시한다. PLA/PET를 선택하면 외부 pre-dry와 contamination/sealed-transfer 확인을 보여주지만 material 선택만으로 calibration ready가 되지 않는다. START 시 material을 잠그고 PAUSE에서도 직접 변경을 금지한다. LCD/TFT는 이후 backend를 바꿀 수 있지만 navigation state와 safety intent는 production `MachineSupervisor`의 view state가 지배한다.

운전 화면에는 selected/pending material, process phase, material session, forming-chain state, screw speed, shredder load/telemetry, zone/die temperature, feeder rate, cooling feedback, `d_x`, `d_y`, `d_mean`, ovality, calibration U95, `spool_eligible`, `waste_mode`, requalification progress, dancer level, fault reason과 purge/cleaning requirement를 표시한다.

최소 view state는 `CALIBRATION_REQUIRED`, `READY_TO_PREHEAT`, `COOLING_STARTUP_PROBE`, `READY_TO_EXTRUDE`, `MAINTENANCE_PURGE`, `FORMING_CHAIN_RUNDOWN`, `REQUALIFYING`, `READY_TO_RETHREAD`, `FAULT_CLEAR_BLOCKED`를 포함한다. `COOLING_STARTUP_PROBE`는 fan-only 명령·healthy dwell·timeout을 보여 입증 전 heater/motion이 0임을 명시한다. `READY_TO_EXTRUDE`는 온도 준비가 extrusion 시작을 뜻하지 않음을 보여주고 operator arm을 요구한다. `READY_TO_RETHREAD`도 현재 strand가 이미 spool-qualified됐다는 뜻이 아니며 수동 threading 확인을 요구한다.

재질 전환은 IDLE/feed stop/screw stop 확인 → `PURGE_PREHEAT_REQUIRED` → `PURGE_READY_CONFIRM_REQUIRED` → `PURGE_RUNNING` → `SCREEN_CLEAN_REQUIRED` → `HOPPER_CLEAN_REQUIRED` → `TEMPERATURE_TRANSITION_REQUIRED` → `FINAL_CONFIRM_REQUIRED` 순서다. `PURGE_READY_CONFIRM_REQUIRED`에서는 물리 `START`가 feed 승인을, 그 다음 별도 `CONFIRM`이 waste-path 준비 확인을 뜻하며 두 intent를 합치지 않는다. Purge 화면의 screw revolution evidence는 verified A13 tach timestamp pulse로 적분한 actual revolution만 인정하며 timeout/mismatch 때 무효다. 질량 sensor는 없으므로 measured grams로 표시하지 않는다. 최종 단계는 별도 explicit confirmation을 요구하며 어느 단계든 wizard를 건너뛰지 못한다.

Fault 화면은 서로 분리된 fault reason, latched subsystem, actual permission feedback, rundown/thermal-hold 상태와 `PHYSICAL_LOCKOUT_KEY_REQUIRED`를 표시한다. Clear preflight 하나라도 실패하면 `FAULT_CLEAR_BLOCKED`와 차단 원인을 표시하며 다른 latch가 사라진 것처럼 보이면 안 된다. Clear 성공은 자동 restart가 아니다. 주기 상태 log와 Serial 명령 `MATERIAL PLA|PET`, `SHRED`, `PREHEAT`, `ARM`, `HOME_TRAVERSE`, `PURGE_PREHEAT`, `PURGE_FEED_APPROVED`, `PURGE_WASTE_READY`, `PURGE_COMPLETE_VISUAL`, `ACK`, `RETHREAD`, `STOP`, `CAL ...`, `CLEAR`는 commissioning backend이며 무인 원격 운전 권한이 아니다.

NEMA17 current-chopping driver의 PSU 입력전류만 torque로 표시하지 않는다. 가능한 driver phase telemetry/diagnostic, encoder RPM drop, missed step/StallGuard, supply power를 Gate 1에서 실제 shaft torque와 교정한다.
