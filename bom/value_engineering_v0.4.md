# 현금비용 value engineering — solid-manifold-openmodelica-v0.4

## 결론

Compact single-path architecture와 모든 안전 기능을 유지했다. 특정 `MY1016Z` motor, elastomer coupling, 특정 phase gear MPN에 종속하지 않는 DRV-01/DRV-Axx/DRV-F01/DRV-02/DRV-03 functional interface, donor flat stock 우선, 실제 PrusaSlicer 산출량을 반영하여 조건부 target 계획액은 **179,434 KRW**다. 20,000 KRW 견적변동 예비비를 포함한 절대 계획액은 **199,434 KRW**다.

이는 견적이나 재고 확인 결과가 아니라 target allowance다. Donor 증거와 RFQ가 없으므로 현재 구매 release는 `BLOCKED`이며, 안전부품을 삭제해서 차이를 흡수하지 않는다.

## 변경 근거

|종속/낭비|v0.4 방법|설계 영향|
|---|---|---|
|특정 geared motor|18–30 V, cutter 14 N·m continuous, 20–40 rpm을 만족하는 donor + DRV-01 slotted plate|축/bolt pattern은 motor-side bracket만 변경|
|특정 coupling|DRV-Axx donor adapter + motor-side DRV-F01 + #35 chain 12T:18/24/30T + cutter-side DRV-02|alignment 흡수와 ratio 선택; guard 유지; motor adapter만 교체|
|특정 phase gear|generic M3 Z16 face≥18 mm 또는 동일 DXF 3×6 mm laminate|34 N·m allowable 유지; motor-side DRV-F01이 22 N·m cutter-equivalent에서 먼저 작동|
|새 metal plate|project-lab donor sheet/plate 우선|critical bearing bore만 finish machining|
|CAD mass allowance|필요 part에 support를 활성화한 PrusaSlicer 2.9.6 toolpath 968.97 g + 실패 reserve 12%|계획 질량 1,085.25 g, 1.5 kg target 이내|
|full cutter/screw 일괄|CUT-01 2장, EX-CPN-SCR/EX-CPN-BAR 최소 coupon 선행|물리 결과 전 full order는 금지|

## Budget hierarchy

- Target total: 179,434 KRW (`CONDITIONAL_TARGET_PASS`, 목표 180,000 이하)
- Quote contingency: 20,000 KRW (기능 추가용이 아님)
- Absolute total: 199,434 KRW (`CONDITIONAL_CAP_PASS`, 절대 200,000 이하; 여유 566 KRW)
- CNC/fabrication target: 76,000 KRW
- 신규 non-CNC/interface/safety target: 72,000 KRW
- Final-machine print planning: 19,534 KRW
- Gate-1 test allowance: 11,900 KRW (jig print 실계산 4,228 KRW + metrology 7,500 KRW)

## Release lock

- Donor motor 0원 확정: exact model, 수량, 상태, label, 축, 무부하 전류/RPM, 30분 온도와 Gate-1 calibration record 필요.
- CUT-01: Gate-1에서는 정확히 2장만 견적 대상. 나머지 full stack는 Gate-1 PASS 전 `HOLD`.
- Screw/barrel: process coupon과 제조성 audit는 견적용일 뿐, full EX-SCR-01/EX-BAR-01은 Gate-1과 Gate-3 전 `HOLD`.
- 구매·CNC 주문은 사용자 승인 없이는 진행하지 않는다.
- 물리 Gate-1 결과가 없으므로 release status는 `DIGITAL_FABRICATION_BASELINE`, 물리 상태는 `PHYSICAL_VALIDATION_PENDING`/`PHYSICAL_NOT_RUN`이다.
