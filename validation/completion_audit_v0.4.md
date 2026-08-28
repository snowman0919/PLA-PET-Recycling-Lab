# v0.4 요구사항 완료 감사

Revision: `solid-manifold-openmodelica-v0.4`

## 디지털 제작 기준선

|요구사항|근거|상태|
|---|---|---:|
|Compact single path와 470×700×930 mm 외형|`cad/generation/assembly_metadata.json`, `validation/results/full_motion.json`|PASS|
|Closed positive-volume manufactured solids|`validation/results/solid_topology.json`|PASS|
|12 print family의 실제 체결부·벽·치수도|`exports/print/PPR-Cxx`, `validation/results/print_interfaces.json`|PASS|
|Watertight STL/3MF와 실제 slicing|`validation/results/mesh_manifold.json`, `slicer_results.json`|PASS|
|사람이 검토 가능한 slicing preview|12 plate + PPR-TC01 첫 extrusion layer SVG, raw G-code는 재생성 제외물|PASS|
|Tolerance coupon|`exports/print/coupons/PPR-TC01`|PASS_DIGITAL / PHYSICAL_NOT_RUN|
|Cutter 360°+±1° solid phase sweep|1° 간격 360자세×3 phase error = 1,080조건|PASS|
|Dancer/traverse full motion|51 dancer자세, 41 traverse자세|PASS|
|Interchangeable geared-DC drive|DRV-01/DRV-Axx/DRV-F01/#35/DRV-02/DRV-03 contract와 ratio calibration 표|PASS_DIGITAL / DONOR_UNVERIFIED|
|Gate-1 jig 최소수량 package|FreeCAD/STEP/STL/DXF/BOM/체결표/배선/절차/원시기록 template|PASS_DIGITAL / PHYSICAL_NOT_RUN|
|16×16 L/D screw/barrel RFQ|재료·공차·GD&T·Ra·열처리·route·coupon HOLD가 있는 drawing/PDF|PASS_DIGITAL / SUPPLIER_DFM_PENDING|
|CAD mass/inertia to OpenModelica|revision/hash/unit/COM/inertia/shaft·bearing 좌표 bridge|PASS|
|MSL system dynamics|Rotational/Translational/MultiBody, 18 scenario, 6 sweep|PASS_DIGITAL|
|Analytic/CalculiX coupling|OpenModelica dynamic envelope를 입력으로 사용|PASS_DIGITAL|
|안전·firmware lock|E-stop/lid/service hard cut, thermal/branch fuse, bounded retry, uncalibrated inhibit|PASS_DIGITAL / PHYSICAL_NOT_RUN|
|Conditional budget|179,951 KRW target, 199,951 KRW reserve 포함, 절대 cap 여유 49 KRW|PASS_CONDITIONAL|
|Verified procurement budget|견적·영수증·donor 증거 부재|NOT_ESTABLISHED|

## 의도적으로 잠긴 항목

- Gate-1 실제 PLA/PET torque, jam, chip-size: `NOT_RUN`.
- Donor motor identity/shaft/current/torque calibration: `UNVERIFIED`.
- Screw/barrel process coupon 및 공급사 DFM: `NOT_RUN`/`PENDING`.
- Full CUT-01 stack과 full EX-SCR-01/EX-BAR-01 발주: `HOLD`.
- `main` fast-forward: Gate-1 signed raw CSV와 photo/video hash가 없으므로 `LOCKED`.
- 구매·CNC 주문·heater energization: 사용자 승인 전 금지.

따라서 이 revision은 제작 검토 가능한 `DIGITAL_FABRICATION_BASELINE`이지만 물리적으로 검증되었거나 안전 인증된 장치가 아니다.

## 원문 목표 항목별 completion audit

판정어는 `PROVEN_DIGITAL`, `PENDING_PHYSICAL`, `PENDING_EXTERNAL`, `LOCKED_BY_USER`로 제한한다. 자동 PASS가 실제 성능을 뜻하지 않는다.

### 제약·구성관리

|ID|요구사항|권위 있는 증거|판정|
|---|---|---|---|
|G-01|PLA/PET 공용 single path 유지|`requirements/architecture_contract.md`, full assembly STEP/render|PROVEN_DIGITAL|
|G-02|500×750×1000 hard / 480×720×950 target|`assembly_metadata.json`, `full_motion.json`: 470×700×930|PROVEN_DIGITAL|
|G-03|각 출력품 210 mm 이하|12-row print manifest와 `print_interfaces.json`|PROVEN_DIGITAL|
|G-04|출력 계획질량 1.5 kg target|support 포함 PrusaSlicer 994.61 g + 12% = 1,113.96 g|PROVEN_DIGITAL|
|G-05|조건부 180k / 절대 200k|179,951 / 199,951 KRW rollup|PROVEN_DIGITAL|
|G-06|검증 구매예산 별도 표시|`verified_budget.csv`: NOT_ESTABLISHED|PENDING_EXTERNAL|
|G-07|v0.3 archive tag/branch와 기존 archive 보존|annotated tags, archive refs, `configuration_control.py`|PROVEN_DIGITAL|
|G-08|v0.4 작업 branch와 원격 이력|`solid-manifold-openmodelica-v0.4`, clean-clone record|PROVEN_DIGITAL|
|G-09|Gate-1 전 main 승격 금지|`physical_gate_status.json`, origin/main 불변|LOCKED_BY_USER|

### Solid CAD와 출력 패키지

|ID|요구사항|권위 있는 증거|판정|
|---|---|---|---|
|C-01|active part closed positive-volume B-Rep|135 object `solid_topology.json`|PROVEN_DIGITAL|
|C-02|keep-out 격리 및 제조 export 제외|`cad/review_keepouts`, review count 4|PROVEN_DIGITAL|
|C-03|metal primary load path|assembly classification, structure report, build manual|PROVEN_DIGITAL|
|C-04|panel/guard 실제 두께·체결 interface|FreeCAD Python, section/exploded views, interface checks|PROVEN_DIGITAL|
|C-05|print family별 Python/FCStd/STEP/STL/3MF/note/dimension sheet|12개 `exports/print/PPR-Cxx` package|PROVEN_DIGITAL|
|C-06|watertight/manifold/connected mesh|12 parts + PPR-TC01 mesh report|PROVEN_DIGITAL|
|C-07|실제 slicer plate와 mass/time/support 기록|12 3MF, G-code metrics, support volume|PROVEN_DIGITAL|
|C-08|사람이 검토 가능한 slicing preview|12 plate + coupon first-layer SVG|PROVEN_DIGITAL|
|C-09|hole/insert/slide tolerance coupon|PPR-TC01 CAD/plate/result template|PENDING_PHYSICAL|
|C-10|dancer/traverse/full spool motion|51 + 41 samples, motion render|PROVEN_DIGITAL|

### Cutter·구동·Gate-1

|ID|요구사항|권위 있는 증거|판정|
|---|---|---|---|
|S-01|비대칭 cycloidal-derived hook|CUT-01 Python/STEP/DXF/profile render|PROVEN_DIGITAL|
|S-02|정확 solid 360°와 phase-error sweep|360×3=1,080 configuration, 0.5 mm minimum|PROVEN_DIGITAL|
|S-03|특정 MY1016Z/coupling/gear 비종속|DRV-01/Axx/F01/#35/DRV-02/DRV-03 contract|PROVEN_DIGITAL|
|S-04|donor motor 합격조건과 calibration 분리|donor acceptance/measurement form, firmware lock|PENDING_EXTERNAL|
|S-05|14<18<22<34<48 N·m 보호계층|engineering summary, firmware, Modelica fuse scenario|PROVEN_DIGITAL|
|S-06|motor-side relief 후 phase 유지|InputFuseOperation + phase model|PROVEN_DIGITAL|
|S-07|Gate-1 최소수량 jig 제조·증거 package|2×CUT-01, G1J-01–10/P01–P03, CAD/STEP/STL/DXF/BOM/PDF와 분리된 25 torque/6 jam/2 chip template|PROVEN_DIGITAL|
|S-08|PLA/PET torque·jam·chip-size 측정|procedure/raw templates만 존재|PENDING_PHYSICAL|
|S-09|full cutter order 잠금|`full_cutter_order_release=false`|LOCKED_BY_USER|

### Extrusion·열·forming

|ID|요구사항|권위 있는 증거|판정|
|---|---|---|---|
|E-01|16 mm×16D 공용 screw 선택과 throughput 일관성|engineering summary/sensitivity table|PROVEN_DIGITAL|
|E-02|200 g/h 미달을 숨기지 않음|PLA 111.8/PET 108.4 g/h nominal, stretch 명시|PROVEN_DIGITAL|
|E-03|screw/barrel RFQ 재료·GD&T·Ra·열처리·route|RFQ PDF/SVG/audit/template|PROVEN_DIGITAL|
|E-04|flight-tip leakage/clearance sensitivity|engineering calculation report|PROVEN_DIGITAL|
|E-05|process coupon 선행과 full pair HOLD|EX-CPN package, physical gate status|PENDING_PHYSICAL|
|E-06|external pre-dry 미검증 표시|`UNQUALIFIED_EXTERNAL_PROCESS`|PENDING_EXTERNAL|
|E-07|24 V 600 W state power budget|500 W allowed-state peak, 100 W margin|PROVEN_DIGITAL|
|E-08|hot-zone shield/thermal screening|52 °C shield/42 °C polymer screening|PENDING_PHYSICAL|
|E-09|50/100/150/200 g/h cooling screen|PLA/PET cooling table와 required air velocity|PROVEN_DIGITAL|
|E-10|직경 loop transport delay와 spool independence|control simulation, FormingSpool scenarios|PROVEN_DIGITAL|

### OpenModelica·구조·firmware

|ID|요구사항|권위 있는 증거|판정|
|---|---|---|---|
|M-01|MSL Rotational/Translational/MultiBody 실제 사용|component source와 library check|PROVEN_DIGITAL|
|M-02|CAD mass/COM/inertia/coordinate bridge|generated JSON/MO revision/hash/unit check|PROVEN_DIGITAL|
|M-03|요구 시나리오 18개|scenario metrics와 summary|PROVEN_DIGITAL|
|M-04|friction/inertia/backlash/efficiency/Kt/load sweep|6 sensitivity rows|PROVEN_DIGITAL|
|M-05|동적 하중을 구조해석에 전달|동일 load-envelope JSON hash/content|PROVEN_DIGITAL|
|M-06|9개 구조 screening + 2 CalculiX deck|structural JSON/report; 최신 수치 문서 동기화 gate|PROVEN_DIGITAL|
|M-07|Material lock/calibration/retry/E-stop/gauge dropout firmware|공유 baseline header + host tests|PROVEN_DIGITAL|
|M-08|실제 wiring hard-cut와 thermal protection|회로도/절차는 완성, 물리 continuity·trip 미실행|PENDING_PHYSICAL|

### 문서·release

|ID|요구사항|권위 있는 증거|판정|
|---|---|---|---|
|R-01|README/requirements/BOM/PDF/manifest revision 일치|stale/revision gate|PROVEN_DIGITAL|
|R-02|한국어 build/design/digital release PDF|Typst source, A4 PDF, parent page review|PROVEN_DIGITAL|
|R-03|opaque/exploded/section/tool/motion/support/cutter/jig render|18-image render package와 visual review|PROVEN_DIGITAL|
|R-04|working-tree 전체 gate|`ALL_DIGITAL_VALIDATIONS_OK`|PROVEN_DIGITAL|
|R-05|remote clean-clone 전체 재생성과 산출물 동일성|`clean_clone_validation.json`, `artifact_reproducibility.json`; STEP/FCStd/3MF normalized hash gate|PROVEN_DIGITAL|
|R-06|구매/CNC/energization 사용자 승인|실행하지 않음; 모든 order release false|LOCKED_BY_USER|

## 결론

남은 항목은 디지털 산출물 누락이 아니라 exact donor/견적, tolerance·cutter·thermal·diameter의 물리 증거다. 특히 Gate-1 signed raw CSV와 photo/video hash가 없으므로 full cutter, full screw/barrel, `main` 승격은 완료로 판정하지 않는다.
