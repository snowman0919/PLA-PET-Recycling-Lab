# 동적 하중 연계 구조 검토

- revision: `safety-orchestration-closure-v0.6.1`
- 판정: **PASS**
- 가상 물리 상태: `VIRTUAL_PHYSICS_VALIDATED`
- 경험적 검증 상태: `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`
- 하중 원본: `analysis/load_cases/openmodelica_dynamic_envelope.json`

|부품|등가응력 MPa|허용 MPa|안전율|판정|
|---|---:|---:|---:|---:|
|CUT-01 cutter tooth/root|57.950|350.0|6.04|PASS|
|SH-SHAFT-01 20 mm cutter shaft|74.947|177.5|2.37|PASS|
|SH-PLATE-01 bearing plate|4.951|137.5|27.77|PASS|
|PH-KEY-01 phase gear key|31.481|120.0|3.81|PASS|
|CH-SPROCKET-01 overhang|33.444|177.5|5.31|PASS|
|DRV-03 motor adapter plate|5.848|75.0|12.82|PASS|
|EX-THR-01 screw thrust plate|3.077|137.5|44.68|PASS|
|SP-SHAFT-01 spool shaft|35.916|100.0|2.78|PASS|
|FR-ANCHOR-01 M8 table anchor|45.231|320.0|7.07|PASS|
|EX-BAR-01 thermocouple blind-bore ligament|83.500|180.0|2.16|PASS|

## 해석 의미

각 계산의 source_load는 동일 OpenModelica envelope 또는 명시된 mechanical cap이다. 따라서 upstream 22 N·m torque fuse가 34 N·m phase drivetrain과 48 N·m shaft/cutter보다 먼저 작동해야 한다. Optional empirical Gate-1 데이터를 얻으면 model-correlation 자료로 갱신할 수 있지만 design release의 필수조건은 아니다.

프레임은 local 2040 Option B를 채택했다. Bearing-center relative displacement는 0.438 mm, screen-clearance margin은 1.462 mm, phase center-distance variation은 0.219 mm다. Profile은 15.098 m에서 14.668 m로 감소한다.

CalculiX deck는 coarse/medium/fine 3단계로 실제 실행되며 medium-to-fine 전역 변위 차이 5% 이하를 합격 기준으로 한다. `generated/bearing_plate.inp`, `generated/cutter_shaft.inp`는 검토용 medium mesh다. 고정단 최대응력은 특이점에 민감하므로 수렴 판정에서 제외하고 폐형식 응력과 함께 판단한다. 상세 notch/contact 검토 및 물리 coupon을 대체하지 않는다.
