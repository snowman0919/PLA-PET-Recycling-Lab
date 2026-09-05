# v0.8 calibration guide

모든 값은 donor label, 계측기 ID, 날짜, 단위, 범위, revision, 원시 증거와 함께 EEPROM v4 CRC로 기록한다. Reference/simulation은 verified가 아니다.

1. Tach: shredder 6 PPR, screw 12 PPR, puller/spooler 20 PPR 후보를 실회전/pulse로 각각 확인한다.
2. Drive/current: no-load를 빼고 torque arm 5/10/15/18/22 N·m에서 shredder torque/A, ratio, efficiency를 교정한다. Screw/puller/spooler는 별도 방향·RPM·stall/tach-loss 시험을 한다.
3. Fan: 0/25/50/100%의 A4 current와 fan1/2 tach, open/stall/one-fan-only를 시험한다. Tach는 airflow 증거가 아니다.
4. Gauge/dancer: traceable pin으로 X/Y/U95/ovality를, 전각도 sweep으로 0.32 rad warning, 0.36 rad stop, 0.4363 rad hard-stop을 확인한다.
5. Traverse: 좌우 limit, steps/mm, 2 mm backoff, 68 mm usable width를 확인한다. Explicit HOME 전 이동 금지다.
6. Purge: waste path, 최소 120 s, verified screw tach 32 revolutions, temperature band, 육안 확인이 모두 필요하다. 80/120 g은 estimate다.
7. Fault clear: 원인 제거, energy isolation, guard close, physical lockout key와 operator confirmation 후 수행하며 자동 재시작하지 않는다.

교정 전 production enable 금지. Hardwired safety 시험은 별도 수행한다.
