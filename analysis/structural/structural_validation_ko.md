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

## Frame configuration audit (v0.5, digital screening)

현 구성은 Option A(2020 only)이며 cut list 총량은 `15.10 m`이다(`exports/fabrication/frame_cut_list.csv`). 하중 기준은 coupled envelope(cutter 21.99 N·m, bearing 1.797 kN, chain 0.603 kN)이다.

|Option|구성|강성 경향|질량/비용 영향|판정|
|---|---|---|---|---|
|A (현재)|2020 15.1 m|기준|기준|스크리닝 응력 9/9 PASS, 유지|
|B|2020 공통 + 2040 shredder rails 2본|shredder bay 국부 굽힘 강성 약 8배(단면 h³ 스케일, REFERENCE_ESTIMATE)|약 +0.9 kg, 견적 필요|Gate-3 트리거 예비 설계|
|C|2020 공통 + 4040 또는 donor plate 로컬 load loop|국부 강성 최대(약 16배, REFERENCE_ESTIMATE)|중량·통합 난도 최대, donor는 0원 취급 금지|기각(예산·통합)|

### 변위 스크리닝과 cutter clearance 예산

- hook-screen 최소 회전 간격은 `2.48 mm`이고 shim 조립 기준 하한은 `1.9 mm`이다(`simulation/cad_clearance.json`, CUT-04).
- CalculiX bearing plate 국부 변위는 envelope에서 `0.264 mm`이다.
- Bay rail 등분산 추정은 k≈2·48EI/L³, L=0.35 m, 2020 I=0.87 cm⁴(REFERENCE_ESTIMATE, 카탈로그 확인 필요), 분산 질량 약 6 kg(cutter rotor 2×1.175 kg + motor cluster)으로 k≈1.34 MN/m, fused peak 1.797 kN에서 rail 변위 약 1.34 mm, 상시 13.5 N·m(hook 7×28 rpm)에서 약 0.56 mm이다.
- 합계 추정: fused peak 약 1.6 mm, 상시 약 0.83 mm — screen clearance 2.48 mm 대비 접촉 예측은 없으나 fused peak 기준 마진은 약 0.9 mm로 얇다.
- 판정: v0.5는 Option A를 유지하고, Gate-3에서 dial indicator로 bearing center 상대변위를 실측해 `>1.2 mm` 또는 hook-screen 접촉 흔적이 있으면 Option B로 2040 rail 교체한다. Bearing plate bolt pattern은 Option B에서도 불변이도록 유지된다.

### T-nut slip과 모드 스크리닝

- T-nut slip은 clamp torque·마찰계수에 지배된다. 마찰계수 0.15 가정 시 M5 clamp 1등급 preconditioning과 접촉면 deburr를 요구하며, Gate-3 torque witness mark 절차로 검증한다. 해석값은 REFERENCE_ESTIMATE다.
- 1차 모드 추정 f≈(1/2π)√(k/m)≈75 Hz(k 위 값, m≈6 kg)이며 hook passing 7×28 rpm≈3.3 Hz 및 cutter rpm 0.45-0.55 Hz와 충분히 분리된다(REFERENCE_ESTIMATE, Gate-3 tap test로 확인).
- frame 사용량 절감은 별도 value engineering 과제로 남기고, 본 revision에서는 envelope·기준 변경 없이 유지한다.
