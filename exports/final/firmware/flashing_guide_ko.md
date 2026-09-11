# ATmega2560 flashing guide

Target `arduino:avr:mega`; source `base:64f260eb851b3451563228cf56419e8b4bda7c7b; variant-builder:2c154dbbef0d61927dd41d83ec98448d52ba7191`; generation base `b287f07f7a55ba61e39c0a5cbe8e45515c9e53ec`. 먼저 `python3 reproducible_build/build_and_verify.py`로 clean build/HEX 일치를 확인한다.

1. Main 24 V, heater와 motor branch를 물리 lockout하고 USB만 연결한다.
2. 보드/포트를 확인하고 `arduino-cli upload -p <PORT> --fqbn arduino:avr:mega source/arduino_mega`로 기록한다.
3. verify/read-back 후 boot material `NONE`과 모든 actuator safe-state를 확인한다.
4. Branch power는 별도 사용자 승인과 pre-power 검사 전 연결하지 않는다.

Flash는 safety chain이 아니다. E-stop, lid/service, thermal cutoff, K0와 fuse는 firmware 독립이다.
