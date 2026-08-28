# UI와 profile lock

첫 화면은 `PLA`, `PET`, `Maintenance`, `Calibration` 네 항목이다. PLA/PET를 선택하면 외부 pre-dry 온도/시간, contamination checklist와 sealed transfer 확인을 보여준다. START 시 material을 잠그고 PAUSE 상태에서도 다른 material 직접 선택은 금지한다.

운전 화면에는 selected material, process state, screw speed, shredder load/telemetry, zone/die temperature, feeder rate, `d_x`, `d_y`, `d_mean`, ovality, calibration U95, spool progress, fault, purge/cleaning requirement를 표시한다.

재질 전환은 feed stop -> 현재 재질 purge 최소량 확인 -> 0 V lockout -> screen/breaker inspection -> hopper/bin clean -> 온도 transition -> 다음 재질 확인 순서다. 어느 단계든 BACK은 안전 정지로 돌아가며 wizard를 건너뛰지 못한다.

NEMA17 current-chopping driver의 PSU 입력전류만 torque로 표시하지 않는다. 가능한 driver phase telemetry/diagnostic, encoder RPM drop, missed step/StallGuard, supply power를 Gate 1에서 실제 shaft torque와 교정한다.
