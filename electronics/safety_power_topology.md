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

Melt blockage 방호는 open 3 mm die와 7 x 2 mm breaker flow area, removable screen, calibrated screw torque trip, guarded sacrificial die-retainer feature의 조합이다. Pressure sensor가 있으면 계측을 추가하지만 sensor/firmware 하나에 safety를 맡기지 않는다.

PET 기준 hot path는 metal, 300 °C thermal fuse candidate, temperature-rated wire/sleeve, 25 mm insulation과 grounded sheet shield를 사용한다. First-hot-test는 remote stop/guard 뒤에서 low feed로 수행한다.
