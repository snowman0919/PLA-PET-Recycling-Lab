# v0.8 calibration guide

모든 값은 donor label, 계측기 ID, 날짜, 단위, 범위, revision, 원시 증거와 함께 EEPROM v4 CRC로 기록한다. Reference/simulation은 verified가 아니다.

1. Tach: shredder 6 PPR, screw 12 PPR, puller/spooler 20 PPR 후보를 실회전/pulse로 각각 확인한다.
2. GGM/BTS7960 drive/current: shredder A0와 extruder A9 motor-lead current를 각각 traceable reference와 최소 5점(0~4.6 A 이상, 전체 검증범위 0~6.0 A)에서 ADC 교정하고 no-load current를 3회 이상 기록한다. Torque arm은 8.0 N·m software limit 아래의 fit sample과 독립 holdout sample을 분리하며, holdout 오차+U95가 0.4 N·m 이하여야 한다. Shredder는 F/R, extruder는 F만 검증한다.
3. Mechanical protection pin: software current/torque calibration과 별개로 8.8–9.3 N·m release torque를 각 허용 방향 3개 독립 coupon으로 확인한다. 실측 전 blank Ø3 pin을 release pin으로 간주하지 않는다.
4. Fan: 0/25/50/100%의 A4 current와 fan1/2 tach, open/stall/one-fan-only를 시험한다. Tach는 airflow 증거가 아니다.
5. Gauge/dancer: traceable pin으로 X/Y/U95/ovality를, 전각도 sweep으로 0.32 rad warning, 0.36 rad stop, 0.4363 rad hard-stop을 확인한다.
6. Traverse: 좌우 limit, steps/mm, 2 mm backoff, 68 mm usable width를 확인한다. Explicit HOME 전 이동 금지다.
7. Purge: waste path, 최소 120 s, verified screw tach 32 revolutions, temperature band, 육안 확인이 모두 필요하다. 80/120 g은 estimate다.
8. Fault clear: 원인 제거, energy isolation, guard close, physical lockout key와 operator confirmation 후 수행하며 자동 재시작하지 않는다.

교정 전 production enable 금지. Hardwired safety 시험은 별도 수행한다.
