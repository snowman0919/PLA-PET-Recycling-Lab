# Hot-zone guard and nearby-polymer thermal gate

상태: **SENSITIVITY GATE — PHYSICAL THERMOCOUPLE VALIDATION OPEN**

압출기/건조기 hot node→단열재→금속 shield→인접 polymer의 정상상태 열저항망이다. 원통 측면과 양단 전도, shield 대류·복사, polymer 복사·plume 결합을 동시에 푼다. Clamp·seam·penetration은 thermal-bridge factor로만 묶었으므로 실제 hotspot을 승인하지 않는다.

| Case | Hot °C | Shield °C | Polymer °C | 판정 |
|---|---:|---:|---:|---|
| extruder_pet_ventilated | 280 | 48.8 | 27.2 | NORMAL_PASS |
| extruder_design_max_baffled | 310 | 70.7 | 40.5 | FAULT_COOLDOWN_REQUIRED |
| extruder_design_max_direct_view | 310 | 77.8 | 48.6 | PROHIBITED_DIRECT_VIEW |
| dryer_pet_ventilated | 160 | 37.9 | 26.2 | NORMAL_PASS |
| dryer_trip_direct_view | 170 | 53.4 | 37.0 | FAULT_COOLDOWN_REQUIRED |

## 설계 결정

- 기존 압출기 40 mm 단열은 PET 정상 case에서 shield 약 54 °C로 50 °C 목표를 넘었다. Baseline과 CAD 실두께를 50 mm로 변경하면 동일 case가 약 48.8 °C다.
- 압출기 310 °C, 열교 1.5배, 낮은 대류, 고방사율 fault envelope에서는 metal baffle로 shield→polymer 유효 view factor를 0.60 이하로 제한해야 45 °C polymer limit 아래다.
- 직접 시야(view factor 1.0)는 약 48.6 °C로 실패하므로 hot zone의 PLA/ABS cover, bracket, cable carrier와 sensor mount를 금지한다. 해당 영역은 접지 금속 또는 정격 무기 절연물만 쓴다.
- Fault/cooldown에서 shield는 50 °C를 넘을 수 있으므로 guard sensor 실측값이 release threshold 아래가 될 때까지 RUN과 service access를 금지한다.

## 물리 시험 gate

최대 setpoint와 independent-trip fault에서 seam, clamp, slot, cable penetration, 가장 가까운 polymer point에 열전대를 설치한다. 정상 shield ≤50 °C, 인접 PLA/ABS 후보 ≤45 °C를 확인하고, 모델보다 높은 지점이 하나라도 있으면 insulation/baffle/airflow를 재설계한다. 본 계산만으로 heater를 인가하지 않는다.

상세 수치와 에너지수지는 `simulation/thermal/hot_zone_guard.json`에 있다.
