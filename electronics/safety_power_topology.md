# 24 V safety/power topology

```text
AC inlet/main switch -> verified 24 V 600 W PSU -> main fuse
  -> protected logic branch -> Mega + gauge
  -> hardwired E-stop/lid/service permission chain -> branch enables
       -> shredder fuse + driver
       -> feeder/screw fuse + drivers
       -> heater branch fuses + MOSFETs + one-shot thermal fuse in series
       -> puller/spooler branch
```

Mega는 permission chain feedback을 읽지만 chain을 우회할 수 없다. E-stop 또는 guard open은 heater enable과 모든 hazardous motion을 hardware에서 제거한다. PSU, MOSFET, fuse, switch, connector의 exact model/current/temperature rating은 donor inspection 전 미확정이다.

Cooling fan PWM command는 fan 동작 증거가 아니다. Fan branch return의 검증된 low-side shunt/보호 증폭 경로를 Mega A4 `COOLING_CURRENT`에 연결하고 donor fan별 normal/open/stall window를 교정한다. Command threshold 이상에서 feedback이 정상 window 밖으로 1.5 s 지속되면 firmware와 virtual model은 `COOLING_FAILURE` forming-chain rundown으로 전환한다. 교정 전에는 fail-safe invalid이며 이 current feedback을 airflow 또는 tach 측정으로 표시하지 않는다.

Process heater의 설치 정격은 360 W지만 active motion과 동시에 네 채널을 무제한 ON하지 않는다. Machine-readable phase power contract가 PREHEATING과 EXTRUSION/PURGE/RUNDOWN/HOLD/REQUALIFYING의 heater aggregate cap을 정의하고 `MachineSupervisor`가 요청 channel을 공정하게 time-slot arbitration한다. 실제 command의 독립 component 합이 500 W 이하이고 600 W PSU reserve가 100 W 이상이어야 한다. 이 software power arbitration은 branch fuse, independent thermal fuse와 hardware permission chain을 대체하지 않는다.

v0.6 Mega wiring은 `controller_wiring_v0.6.md`, exact pins는 `board_config.h`, safe-state/시험은 `io_schedule.csv`가 지배한다. Command와 heater permission feedback 불일치는 latch되며 physical lockout key 없이 clear되지 않는다. EEPROM calibration이 유효하지 않으면 shredder와 gauge quality release를 inhibit한다.

Shredder 기준은 특정 MPN이 아닌 18–30 V reversible brushed geared-DC donor functional interface, 20 A branch fuse, reversible H-bridge와 isolated 50 A current feedback이다. Cutter 14 N·m continuous와 20–40 rpm을 donor label·실측·Gate-1으로 확인한다. Current를 직접 torque로 보지 않고 donor calibration으로 PLA/PET 11/13 N·m continuous 및 공통 18 N·m jam trip을 계산하며 Hall RPM drop을 함께 쓴다. Cutter-equivalent 22 N·m relief는 motor-side DRV-F01에서 ratio별 17.25/12.94/10.35 N·m로 설정하며 cutter-side DRV-02와 34 N·m phase/48 N·m shaft 경로는 sacrificial element가 아니다. Shredder enable 중 heater/screw enable을 차단하고 heater/screw enable 중 shredder hardware-enable을 차단한다. 상세 wiring과 입고시험은 `electronics/shredder_drive_wiring.md`를 따른다.

Melt blockage 방호는 open 3 mm die와 7 x 2 mm breaker flow area, removable screen, calibrated screw torque trip, guarded sacrificial die-retainer feature의 조합이다. Pressure sensor가 있으면 계측을 추가하지만 sensor/firmware 하나에 safety를 맡기지 않는다.

PET 기준 hot path는 metal, 300 °C thermal fuse candidate, temperature-rated wire/sleeve, 25 mm insulation과 grounded sheet shield를 사용한다. First-hot-test는 remote stop/guard 뒤에서 low feed로 수행한다.
