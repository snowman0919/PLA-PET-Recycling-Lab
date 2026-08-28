# Mega realtime core

`MaterialProfile::PLA`와 `MaterialProfile::PET`는 동일 actuator path의 setpoint만 바꾼다. RUN 중 profile은 잠기며 다른 재질을 요청하면 purge -> screen clean -> hopper clean -> confirmation 순서를 모두 통과해야 한다.

Home UI 항목은 PLA, PET, Maintenance, Calibration이다. 운전 화면은 material/state, screw RPM, shredder load, zone/die temperature, feeder, `d_x/d_y/d_mean/ovality/U95`, spool progress와 latched fault를 표시해야 한다. 이 repository의 host core는 state/safety invariant를 검증하며 TFT driver·pin map은 donor model 확인 뒤 추가한다.

E-stop, lid/service interlock, branch fuse와 thermal fuse는 이 firmware와 독립된 hardware cut chain이다.
