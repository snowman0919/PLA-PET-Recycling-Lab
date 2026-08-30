# 교정

Revision: `safety-orchestration-closure-v0.6.1`

Readiness는 `drive_calibration_valid`, `current_sensor_calibration_valid`, `gauge_calibration_valid`, temperature-channel validity와 cooling-feedback calibration으로 분리한다. 한 record의 일부가 유효하다고 다른 subsystem을 ready로 표시하지 않는다. EEPROM magic/schema version/CRC가 불일치하는 stale record는 즉시 zero-sanitize한 뒤 전체 거부하며, 그 후 한 domain만 교정해 저장해도 다른 domain은 ready가 되지 않는다. Cold boot material은 항상 `NONE`이다.

## Cutter load

Gate 1 coupon shaft에 torque reference와 encoder를 설치한다. DC gearmotor는 shaft torque 대 current를 회귀한다. NEMA17은 phase telemetry/diagnostic와 RPM drop을 조합하고 PSU current 단독 threshold를 금지한다.

## X/Y diameter gauge

0.50, 1.00, 1.50, 1.70, 1.75, 1.80, 2.00 mm traceable pin/wire를 각 축에 5회 삽입한다. 각 채널의 threshold, offset, scale, repeatability, hysteresis를 저장하고 `U95 = 2*sqrt(reference^2 + repeatability^2 + fit_residual^2)`로 보고한다. `d_mean=(d_x+d_y)/2`, `ovality=abs(d_x-d_y)`다.

Initial use gate는 U95 <=0.05 mm, improvement gate는 <=0.03 mm다. 물리 교정 전 목표 달성을 주장하지 않는다.

Mega는 gauge offset/scale/U95, drive no-load RPM·torque/A·ratio·efficiency, current-sensor zero/A-per-count를 구분된 validity flag와 함께 versioned EEPROM record에 저장한다. Magic/version/CRC가 불일치하거나 해당 measured calibration의 `verified`가 false이면 그 기능을 금지한다. Gauge가 valid여도 drive/current가 invalid면 shredding할 수 없고, drive가 valid여도 gauge가 invalid면 extrusion/spool qualification을 할 수 없다. 기본 reference profile은 simulation sensitivity용이며 실제 donor calibration record가 아니다.

MAX6675 T1–T5는 open-circuit, -20…300 °C range, ice/boiling-point comparison, ungrounded sheath isolation을 채널별 기록한다. Heater not-heating/unexpected-rise 시험은 실제 heater branch fuse와 independent thermal chain을 설치한 shielded bench에서만 수행한다.

## Puller/spooler

Puller encoder를 1 m traceable length와 비교하고 nip slip을 3–15 N 범위에서 기록한다. Dancer endstop/center와 full sweep, traverse 80 mm 양끝, empty/full spool torque를 각각 교정한다.

## Cooling current feedback

Mega A4의 zero ADC, A/count, 정상 fan의 0/25/50/100% command window, connector-open 값과 blade-stall 값을 기록한다. Shunt resistance·허용오차·전력정격, 증폭기 gain/offset, ADC 최대전압과 fan branch connector를 함께 식별한다. 정상과 stall window가 검증 가능하게 분리되지 않으면 `cooling_feedback_valid=false`로 유지하고 production extrusion을 허용하지 않는다. 이 current path는 fan tach가 아니며 airflow 자체를 측정했다고 주장하지 않는다.
