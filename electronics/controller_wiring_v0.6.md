# Arduino Mega 2560 controller wiring contract

Revision: `parallel-actuation-hardening-v0.6.2` (Fusion geometry/load baseline remains v0.6.1)

Exact pin assignment is controlled by `firmware/arduino_mega/src/board_config.h`; `io_schedule.csv` defines safe state and acceptance. Mega ground is the protected logic reference. MAX6675 T- channels share electronics reference only with verified ungrounded probes. Heater/motor current must not return through logic wiring.

## Safety chain

E-stop, lid, service guard and thermal chain remove hazardous branch permission in hardware. Mega reads their feedback but cannot assert permission. `HEATER_PERMISSION_FEEDBACK` command mismatch latches a fault. Fault clear requires de-energized cause removal, physical lockout key and restart permission; software/Serial alone cannot clear it.

## Outputs

- Shredder: PWM + DIR + reverse + enable to reversible H-bridge; 50 A current input and shaft tach close the calibrated torque/RPM loop.
- Screw, puller, spooler: separate PWM/DIR/enable and active-low driver faults. Puller external interrupt tach는 inner speed PI, A13 screw tach는 actual purge revolutions, A15 spool tach는 dancer/radius/jam loop에 사용한다.
- Traverse: STEP/DIR/enable와 A5/A6 left/right limit; spool turns×pitch를 따르며 loss of spool permission 또는 missed-limit timeout이 disable/fault한다.
- Cooling: PWM fan output, A4 `COOLING_CURRENT`, fan1/fan2 tach 2:1 mux를 함께 사용한다. Mux select는 pin 49, tach edge는 A14 PCINT22다. PREHEAT/PURGE start는 IDLE에서 fan만 먼저 명령하고 두 fan tach와 current가 1.5 s 연속 healthy인 뒤에만 heater/motion phase를 commit한다. 한 fan stop, 두 fan stop, command-off implausible tach는 구분하되 tach를 airflow로 간주하지 않는다.
- Heaters: four time-proportion outputs (Z1/Z2/Z3/die), each with branch fuse and independent thermal cutoff. Hopper PTC is maintenance-only.

## Inputs and commissioning

T1/T2/T3/Tdie/Thopper use five CS lines with shared SCK/SO. Gauge X/Y, dancer, shredder current, cooling current와 fault lines occupy separate analog inputs. Cooling feedback는 fan 전원 branch만 측정하며 shredder 50 A channel과 공유하지 않는다. Encoder/button signals use pull-ups and edge detection. Wire label, terminal, conductor gauge, fuse rating, shunt 발열, ADC 최대전압과 measured polarity must be recorded against the exact purchased/donor components before powered commissioning.

## Cooling feedback commissioning hold

`COOLING_CURRENT`는 전기적 소비전류, fan tach는 회전 증거다. 정상 fan의 0/25/50/100% current와 RPM, connector-open, blade-stall, fan1-only/fan2-only를 shielded bench에서 기록하고 calibration을 valid로 만들기 전 production extrusion을 허용하지 않는다. Duct blockage는 이 신호로 검출되지 않으며 별도 airflow/pressure coupon이 필요하다. 구매·배선·통전은 계속 사용자 승인 대상이다.
