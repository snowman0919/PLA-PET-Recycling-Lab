# UI와 profile lock

첫 화면은 `Home`, `Run`, `Material change`, `Calibration`, `Maintenance`, `Fault` 의미를 갖는 최소 text backend다. PLA/PET를 선택하면 외부 pre-dry와 contamination/sealed-transfer 확인을 보여준다. START 시 material을 잠그고 PAUSE에서도 직접 변경을 금지한다. LCD/TFT는 이후 backend를 바꿀 수 있지만 navigation state와 safety intent는 `ui_core`가 지배한다.

운전 화면에는 selected material, process state, screw speed, shredder load/telemetry, zone/die temperature, feeder rate, `d_x`, `d_y`, `d_mean`, ovality, calibration U95, spool progress, fault, purge/cleaning requirement를 표시한다.

재질 전환은 IDLE/feed stop/screw stop 확인 -> `PURGE_REQUIRED` -> `SCREEN_CLEAN_REQUIRED` -> `HOPPER_CLEAN_REQUIRED` -> `TEMPERATURE_TRANSITION_REQUIRED` -> `FINAL_CONFIRM_REQUIRED` 순서다. 최종 단계는 별도 explicit confirmation을 요구한다. 어느 단계든 BACK은 안전 정지로 돌아가며 wizard를 건너뛰지 못한다.

Fault 화면은 원인, latched 상태, actual permission feedback과 `PHYSICAL_LOCKOUT_KEY_REQUIRED`를 표시한다. Serial 명령 `STATUS`, `MATERIAL PLA|PET`, `ACK`, `CAL ...`, `CLEAR`는 commissioning backend이며 무인 원격 운전 권한이 아니다.

NEMA17 current-chopping driver의 PSU 입력전류만 torque로 표시하지 않는다. 가능한 driver phase telemetry/diagnostic, encoder RPM drop, missed step/StallGuard, supply power를 Gate 1에서 실제 shaft torque와 교정한다.
