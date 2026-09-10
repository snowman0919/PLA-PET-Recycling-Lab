# P10/P11 PLA·PET low-feed 물리 검증

P10과 P11은 처음으로 polymer를 hot path에 투입하는 gate다. P10 PLA PASS 후에만 P11 PET를 수행한다. 각 material마다 별도 사용자 feed 승인이 필요하다.

## 공통 절차

1. Lot ID, 세척/건조 기록을 먼저 고정한다. Screw는 8–10 rpm에서 시작한다.
2. PLA는 180/195/205 °C barrel + 200 °C die, PET는 245/260/270 °C + 265 °C die를 사용한다. 각 sample에서 실제 온도를 기록한다.
3. 10 s 단위로 screw rpm, gearbox torque/current, X/Y diameter, gauge U95, puller/spool rpm, cumulative mass와 이상상태를 기록한다.
4. 실제 melt leak, uncontrolled pressure symptom, guard contact가 있으면 즉시 해당 run을 FAIL로 종료한다. 반복적인 torque-trip을 정상 제어로 사용하지 않는다.
5. 연속 20개 stable sample에서 전체 mean diameter의 1.75 mm 대비 error가 0.05 mm 이하, 각 sample ovality가 0.05 mm 이하, gauge U95가 0.03 mm 이하여야 한다.
6. PET는 18 rpm을 안전값으로 가정하지 않는다. 실제 gearbox torque가 8.0 N·m limit 아래에 여유를 유지할 때만 단계적으로 접근한다.

`templates/p10_p11_material_run.csv`을 run별로 복사해 기록하고 `analyze_material_run.py`로 분석한다. 실제 mass/time에서 안정 throughput을 보고하며 200 g/h는 강제 합격기준이 아니다.
