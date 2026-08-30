# 동적 하중 연계 구조 검토

- revision: `coupled-digital-validation-v0.5`
- 판정: **PASS**
- 물리 상태: `PHYSICAL_VALIDATION_PENDING`
- 하중 원본: `analysis/load_cases/openmodelica_dynamic_envelope.json`

|부품|등가응력 MPa|허용 MPa|안전율|판정|
|---|---:|---:|---:|---:|
|CUT-01 cutter tooth/root|57.950|350.0|6.04|PASS|
|SH-SHAFT-01 20 mm cutter shaft|72.816|177.5|2.44|PASS|
|SH-PLATE-01 bearing plate|4.793|137.5|28.69|PASS|
|PH-KEY-01 phase gear key|31.481|120.0|3.81|PASS|
|CH-SPROCKET-01 overhang|33.444|177.5|5.31|PASS|
|DRV-03 motor adapter plate|5.662|75.0|13.25|PASS|
|EX-THR-01 screw thrust plate|3.077|137.5|44.68|PASS|
|SP-SHAFT-01 spool shaft|35.916|100.0|2.78|PASS|
|FR-ANCHOR-01 M8 table anchor|43.792|320.0|7.31|PASS|

## 해석 의미

각 계산의 source_load는 동일 OpenModelica envelope 또는 그보다 낮은 것이 아니라 명시된 mechanical cap이다. 따라서 upstream 22 N·m torque fuse가 34 N·m phase drivetrain과 48 N·m shaft/cutter보다 먼저 작동해야 한다. Gate-1에서 토크 pulse와 jam 하중을 얻으면 이 파일을 다시 생성해야 한다.

CalculiX deck는 `generated/bearing_plate.inp`, `generated/cutter_shaft.inp`이며 선형 탄성 global screening이다. 상세 notch/contact 검토 및 물리 coupon을 대체하지 않는다.
