# Purge 실제 motion evidence

Screw shaft Hall sensor(A13 PCINT21) pulse로 actual RPM과 cumulative revolutions를 계산한다. 완료 조건은 actual revolutions ≥32, elapsed ≥120 s, temperature stable, screw motion fault 없음, cooling/guard fresh preflight, 작업자 visual confirmation이다.

Commanded RPM은 purge evidence로 사용하지 않는다. command 대비 actual RPM이 35% 미만이 1.5 s 지속되거나 tach timeout이면 mismatch fault다. coupling slip/intermittent tach/zero motion은 completion을 거부한다. mass-per-revolution calibration이 없으므로 80/120 g 표기는 nominal estimate이며 purge mass로 보고하지 않는다.
