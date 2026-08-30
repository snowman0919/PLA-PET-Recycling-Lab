# Arduino Mega 2560 controller wiring contract

Revision: `implementation-crosssolver-v0.6`

Exact pin assignment is controlled by `firmware/arduino_mega/src/board_config.h`; `io_schedule.csv` defines safe state and acceptance. Mega ground is the protected logic reference. MAX6675 T- channels share electronics reference only with verified ungrounded probes. Heater/motor current must not return through logic wiring.

## Safety chain

E-stop, lid, service guard and thermal chain remove hazardous branch permission in hardware. Mega reads their feedback but cannot assert permission. `HEATER_PERMISSION_FEEDBACK` command mismatch latches a fault. Fault clear requires de-energized cause removal, physical lockout key and restart permission; software/Serial alone cannot clear it.

## Outputs

- Shredder: PWM + DIR + reverse + enable to reversible H-bridge; 50 A current input and shaft tach close the calibrated torque/RPM loop.
- Screw, puller, spooler: separate PWM/DIR/enable and active-low driver faults. Puller has tach; spooler follows dancer only.
- Traverse: STEP/DIR/enable; loss of spool permission disables it.
- Cooling: PWM fan output; cooling permission loss during extrusion initiates controlled pause.
- Heaters: four time-proportion outputs (Z1/Z2/Z3/die), each with branch fuse and independent thermal cutoff. Hopper PTC is maintenance-only.

## Inputs and commissioning

T1/T2/T3/Tdie/Thopper use five CS lines with shared SCK/SO. Gauge X/Y, dancer, current and fault lines occupy separate analog inputs. Encoder/button signals use pull-ups and edge detection. Wire label, terminal, conductor gauge, fuse rating and measured polarity must be recorded against the exact purchased/donor components before powered commissioning.
