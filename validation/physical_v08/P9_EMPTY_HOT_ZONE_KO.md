# P9 빈 hot-zone 가열 검증

P9는 plastic을 투입하지 않은 상태에서 heater channel, thermocouple mapping, 독립 thermal cut, 열팽창 여유를 확인하는 단계다. 모든 motor는 disable하고 grounded metal shield와 원격 정지를 준비한다.

## 순서

1. T1–T5를 reference probe와 대조해 channel mapping을 확인하고 open/short fault를 강제한다.
2. Zone별 저출력 step으로 heater-to-sensor 대응을 확인한다. 잘못 매핑된 channel은 즉시 FAIL이다.
3. PLA profile 180/195/205 °C barrel + 200 °C die를 각각 ±5 °C band에서 기록한다.
4. 냉각 후 별도 PET profile 245/260/270 °C barrel + 265 °C die를 각각 ±5 °C band에서 기록한다.
5. Hot run 중 sliding mount가 hard stop에 닿지 않는지 확인한다. P6/P2에서 cold available travel은 1.50 mm 이상이어야 한다.
6. Independent thermal chain을 forced-open해 heater energy가 hardware에서 제거되는지 확인한다.
7. SYS-04 die fastener는 수령검사된 M4×45 class10.9 stock을 42.5±0.1 mm로 절단/deburr한 뒤 dry 1.50 N·m setting으로만 조립한다.

P9에서는 polymer가 없으므로 melt leak-tightness를 판정하지 않는다. 누설은 P10 최초 PLA low-feed에서 처음 평가한다. `templates/p9_thermal_profile.csv`와 `templates/p9_hot_safety.csv`를 기록하고 `analyze_p9_records.py`로 판정한다.
