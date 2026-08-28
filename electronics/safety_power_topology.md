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

Shredder 기준은 특정 MPN이 아닌 18–30 V reversible brushed geared-DC donor functional interface, 20 A branch fuse, reversible H-bridge와 isolated 50 A current feedback이다. Cutter 14 N·m continuous와 20–40 rpm을 donor label·실측·Gate-1으로 확인한다. Current를 직접 torque로 보지 않고 donor calibration으로 PLA/PET 11/13 N·m continuous 및 공통 18 N·m jam trip을 계산하며 Hall RPM drop을 함께 쓴다. DRV-02 motor-input hub의 replaceable fuse는 22 N·m에서 34 N·m phase/48 N·m shaft보다 먼저 분리한다. Shredder enable 중 heater/screw enable을 차단하고 heater/screw enable 중 shredder hardware-enable을 차단한다. 상세 wiring과 입고시험은 `electronics/shredder_drive_wiring.md`를 따른다.

Melt blockage 방호는 open 3 mm die와 7 x 2 mm breaker flow area, removable screen, calibrated screw torque trip, guarded sacrificial die-retainer feature의 조합이다. Pressure sensor가 있으면 계측을 추가하지만 sensor/firmware 하나에 safety를 맡기지 않는다.

PET 기준 hot path는 metal, 300 °C thermal fuse candidate, temperature-rated wire/sleeve, 25 mm insulation과 grounded sheet shield를 사용한다. First-hot-test는 remote stop/guard 뒤에서 low feed로 수행한다.
