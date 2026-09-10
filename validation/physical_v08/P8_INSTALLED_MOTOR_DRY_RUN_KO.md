# P8 설치 후 motor dry-run

P8은 P3에서 교정한 GGM 구동계를 실제 machine load path에 장착한 뒤 재료·히터 없이 저속으로 구동해 방향, tach, stop, bearing/coupling 상태를 확인한다. P7 PASS와 별도 motor 통전 승인이 선행되어야 한다.

## 순서

1. Fan → puller/spooler/traverse → feeder → screw → guarded shredder 순으로 한 branch씩만 구동한다. 동시에 여러 hazardous branch를 처음부터 올리지 않는다.
2. Shredder는 실제 cutter-shaft rpm을 기록하고 selected 40 rpm gearbox + 2.5:1 chain의 약 16 rpm 기대값과 비교한다. 편차가 있으면 sprocket ratio/tach PPR부터 확인하고 임의 보정하지 않는다.
3. Screw commissioning은 10 rpm 이하에서 시작하며 어떤 시험에서도 20 rpm hard limit를 넘기지 않는다. Reverse는 금지한다.
4. 각 branch에서 current, rpm, bearing/coupling temperature trend, vibration/abnormal noise를 기록한다.
5. Normal stop, E-stop, tach-loss를 각각 강제한다. 모든 경우 hazardous command가 제거되고 전원/신호 복구만으로 자동 재시작하지 않아야 한다.

`templates/p8_motor_dry_run.csv`에 실제 측정값과 evidence를 기록하고 `analyze_p8_records.py`로 판정한다. Shredder의 16 rpm은 비교 기준이며 새로운 임의 허용 band를 만들지 않는다.
