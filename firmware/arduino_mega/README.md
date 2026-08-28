# Mega realtime core

`MaterialProfile::PLA`와 `MaterialProfile::PET`는 동일 actuator path의 setpoint만 바꾼다. RUN 중 profile은 잠기며 다른 재질을 요청하면 purge -> screen clean -> hopper clean -> confirmation 순서를 모두 통과해야 한다.

Home UI 항목은 PLA, PET, Maintenance, Calibration이다. 운전 화면은 material/state, screw RPM, shredder load, zone/die temperature, feeder, `d_x/d_y/d_mean/ovality/U95`, spool progress와 latched fault를 표시해야 한다. 이 repository의 host core는 state/safety invariant를 검증하며 TFT driver·pin map은 donor model 확인 뒤 추가한다.

E-stop, lid/service interlock, branch fuse와 thermal fuse는 이 firmware와 독립된 hardware cut chain이다.

`shredder_control`은 DRV-01/#35 chain interchangeable geared-DC interface를 대상으로 PLA/PET 32/24 rpm, 16/18 A 지속 과부하, 명령속도 대비 35% 이상 RPM drop, profile별 reverse duration과 최대 3회 retry를 처리한다. Donor별 current-to-torque와 encoder pulse/rev는 Gate-1에서 calibration한다. 세 번째 reverse 종료 뒤 fault를 latch하며, heater 또는 screw enable과 shredder enable은 상호 배제한다. 이 host core는 BTS7960 board의 실제 PWM pin driver나 current calibration을 대신하지 않는다.
