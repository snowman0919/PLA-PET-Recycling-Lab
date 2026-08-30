# 교정

## Cutter load

Gate 1 coupon shaft에 torque reference와 encoder를 설치한다. DC gearmotor는 shaft torque 대 current를 회귀한다. NEMA17은 phase telemetry/diagnostic와 RPM drop을 조합하고 PSU current 단독 threshold를 금지한다.

## X/Y diameter gauge

0.50, 1.00, 1.50, 1.70, 1.75, 1.80, 2.00 mm traceable pin/wire를 각 축에 5회 삽입한다. 각 채널의 threshold, offset, scale, repeatability, hysteresis를 저장하고 `U95 = 2*sqrt(reference^2 + repeatability^2 + fit_residual^2)`로 보고한다. `d_mean=(d_x+d_y)/2`, `ovality=abs(d_x-d_y)`다.

Initial use gate는 U95 <=0.05 mm, improvement gate는 <=0.03 mm다. 물리 교정 전 목표 달성을 주장하지 않는다.

Mega는 gauge offset/scale/U95와 drive current zero, A/count, no-load current/RPM, torque/A, ratio, efficiency를 versioned EEPROM record에 저장한다. Magic/version/CRC가 불일치하거나 measured calibration의 `verified`가 false이면 gauge quality release와 shredder 구동을 금지한다. 기본 reference profile은 simulation sensitivity용이며 실제 donor calibration record가 아니다.

MAX6675 T1–T5는 open-circuit, -20…300 °C range, ice/boiling-point comparison, ungrounded sheath isolation을 채널별 기록한다. Heater not-heating/unexpected-rise 시험은 실제 heater branch fuse와 independent thermal chain을 설치한 shielded bench에서만 수행한다.

## Puller/spooler

Puller encoder를 1 m traceable length와 비교하고 nip slip을 3–15 N 범위에서 기록한다. Dancer endstop/center와 full sweep, traverse 80 mm 양끝, empty/full spool torque를 각각 교정한다.
