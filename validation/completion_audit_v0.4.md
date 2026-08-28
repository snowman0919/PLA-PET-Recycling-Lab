# v0.4 요구사항 완료 감사

Revision: `solid-manifold-openmodelica-v0.4`

## 디지털 제작 기준선

|요구사항|근거|상태|
|---|---|---:|
|Compact single path와 470×700×930 mm 외형|`cad/generation/assembly_metadata.json`, `validation/results/full_motion.json`|PASS|
|Closed positive-volume manufactured solids|`validation/results/solid_topology.json`|PASS|
|12 print family의 실제 체결부·벽·치수도|`exports/print/PPR-Cxx`, `validation/results/print_interfaces.json`|PASS|
|Watertight STL/3MF와 실제 slicing|`validation/results/mesh_manifold.json`, `slicer_results.json`|PASS|
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
|Conditional budget|179,954 KRW target, 199,954 KRW reserve 포함|PASS_CONDITIONAL|
|Verified procurement budget|견적·영수증·donor 증거 부재|NOT_ESTABLISHED|

## 의도적으로 잠긴 항목

- Gate-1 실제 PLA/PET torque, jam, chip-size: `NOT_RUN`.
- Donor motor identity/shaft/current/torque calibration: `UNVERIFIED`.
- Screw/barrel process coupon 및 공급사 DFM: `NOT_RUN`/`PENDING`.
- Full CUT-01 stack과 full EX-SCR-01/EX-BAR-01 발주: `HOLD`.
- `main` fast-forward: Gate-1 signed raw CSV와 photo/video hash가 없으므로 `LOCKED`.
- 구매·CNC 주문·heater energization: 사용자 승인 전 금지.

따라서 이 revision은 제작 검토 가능한 `DIGITAL_FABRICATION_BASELINE`이지만 물리적으로 검증되었거나 안전 인증된 장치가 아니다.
