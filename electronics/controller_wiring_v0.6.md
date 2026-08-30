# Arduino Mega 2560 controller wiring contract

Revision: `safety-orchestration-closure-v0.6.1`

Exact pin assignment is controlled by `firmware/arduino_mega/src/board_config.h`; `io_schedule.csv` defines safe state and acceptance. Mega ground is the protected logic reference. MAX6675 T- channels share electronics reference only with verified ungrounded probes. Heater/motor current must not return through logic wiring.

## Safety chain

E-stop, lid, service guard and thermal chain remove hazardous branch permission in hardware. Mega reads their feedback but cannot assert permission. `HEATER_PERMISSION_FEEDBACK` command mismatch latches a fault. Fault clear requires de-energized cause removal, physical lockout key and restart permission; software/Serial alone cannot clear it.

## Outputs

- Shredder: PWM + DIR + reverse + enable to reversible H-bridge; 50 A current input and shaft tach close the calibrated torque/RPM loop.
- Screw, puller, spooler: separate PWM/DIR/enable and active-low driver faults. Puller has tach; spooler follows dancer only.
- Traverse: STEP/DIR/enable; loss of spool permission disables it.
- Cooling: PWM fan output와 A4 `COOLING_CURRENT` analog feedback를 함께 사용한다. Fan branch return의 저항값·전력정격이 검증된 low-side shunt와 절연/보호된 증폭 경로를 A4에 연결한다. PREHEAT/PURGE start는 IDLE에서 fan만 먼저 명령하고, feedback이 healthy window에 1.5 s 연속 존재한 뒤에만 heater/motion phase를 commit한다. 연속성이 깨지면 dwell을 0으로 reset하고, 3.0 s 내에 입증하지 못하면 `COOLING_FAILURE`/all-zero다. 운전 중 명령이 threshold 이상인데 교정된 feedback이 정상 window 밖에서 1.5 s 지속되면 동일 fault를 latch하고 forming-chain controlled rundown을 시작한다. 교정 record가 없거나 ADC가 단선/범위 밖이면 production에서는 fail-safe fault이며 always-healthy 대체 backend를 사용하지 않는다.
- Heaters: four time-proportion outputs (Z1/Z2/Z3/die), each with branch fuse and independent thermal cutoff. Hopper PTC is maintenance-only.

## Inputs and commissioning

T1/T2/T3/Tdie/Thopper use five CS lines with shared SCK/SO. Gauge X/Y, dancer, shredder current, cooling current와 fault lines occupy separate analog inputs. Cooling feedback는 fan 전원 branch만 측정하며 shredder 50 A channel과 공유하지 않는다. Encoder/button signals use pull-ups and edge detection. Wire label, terminal, conductor gauge, fuse rating, shunt 발열, ADC 최대전압과 measured polarity must be recorded against the exact purchased/donor components before powered commissioning.

## Cooling feedback commissioning hold

`COOLING_CURRENT`는 fan이 실제 회전한다는 직접 tach 증거가 아니라 전기적 소비전류 feedback이다. 따라서 정상 fan의 0/25/50/100% command current window, connector-open, blade-stall current를 shielded bench에서 각각 기록하고 firmware calibration을 `valid=true`로 만들기 전 production extrusion을 허용하지 않는다. Stall current가 정상 window와 분리되지 않으면 검증된 tach fan으로 교체하거나 별도 tach feedback을 추가해야 하며, software threshold만으로 정상 운전을 주장하지 않는다. 구매·배선·통전은 계속 사용자 승인 대상이다.
