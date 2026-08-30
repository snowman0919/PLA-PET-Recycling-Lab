# 현금비용 value engineering — virtual-physics-closure-v0.5.1

## 결론

Compact single-path architecture와 E-stop, guard interlock, branch fuse, 독립 thermal fuse를 유지하면서 360 W 공정가열계와 T1–T5를 포함한 조건부 계획액을 **173,729 KRW**, 20,000 KRW 견적변동 예비비 포함 절대 계획액을 **193,729 KRW**로 낮췄다. 조건부 여유는 **6,271 KRW**다.

이 값은 견적·영수증이 아니다. `VERIFIED_PROCUREMENT_BUDGET`은 아직 `NOT_ESTABLISHED`이며, 미확인 donor motor와 project-lab stock은 0원으로 확정하지 않았다. 실물의 모델·수량·상태와 공급사 견적이 없으므로 구매 release는 계속 `BLOCKED`다. 특히 donor가 합격하지 않거나 heater/CNC 견적이 allowance를 넘으면 budget gate는 재실행해야 하며, 안전부품이나 heater wattage를 삭제해서 차이를 흡수하지 않는다.

## v0.5.1 bottom-up allowance reconciliation

|버킷|금액 KRW|포함 범위와 잠금|
|---|---:|---|
|CNC/process coupon/RFQ|57,000|CUT/barrel/screw/die/thrust target allowance; 전 항목 quote 미확정|
|Safety/gauge/thermal stock/hardware|35,000|E-stop/interlock, branch+thermal fuse, gauge, shield, 표준 hardware; 안전 삭제 금지|
|Shredder drive/interface|14,000|donor 우선 driver/current feedback + #35/DRV interface; donor 0원 미확정|
|360 W heater/T1–T5/MOSF|49,500|3× band, die cartridge, PTC, ungrounded probe+MAX6675 5ch, MOSF 5ch|
|Print package|18,229|PrusaSlicer 904.20 g + 12% reserve = 1,012.70 g|
|합계|173,729|`CONDITIONAL_PLANNING_BUDGET`; quote/receipt가 아님|

Optional empirical Gate-1 metrology 7,500 KRW와 jig print 4,400 KRW(합계 11,900 KRW)는 design-release machine 합계에서 분리했다. 이는 시험을 생략해 부품 비용을 숨긴 것이 아니라, 선택적 실험 비용과 제작 기준선 비용을 독립 표시한 것이다.

## Drive interchangeability

`DRV-01` Ø65 common-pass-through universal plate, motor-specific `DRV-Axx`, motor-side `DRV-F01` shear element, #35 12T:30T, cutter-side `DRV-02`, 6 mm key를 가진 generic M3 Z16 face18 `DRV-03` phase pair를 경계로 삼는다. MY1016Z, 특정 elastomer coupling, 특정 gear 제조사에 종속하지 않는다. DRV-03의 M4/dowel은 적층 위상만 재현하고 실제 shaft torque는 공통 key가 전달한다.

정확한 digital reference는 TT Motor `GMP60-60127-2460 ratio 47`이다. 공개 정격 70 rpm/100 kg·cm(9.80665 N·m)를 12T:30T, 효율 0.85에 적용하면 cutter 28 rpm/20.84 N·m다. 요청된 `GMP42-775PM ratio 51`은 90 rpm/26 kg·cm(2.5497 N·m)이고 같은 감속 후 5.42 N·m라 14 N·m 연속기준에 불합격한다. `DRV-A42`는 다른 고토크 42GP 변형을 위한 호환도면으로만 유지한다.

현금 0원 donor 합격은 `bom/donor_drive_acceptance.csv`와 `exports/drive_interface/donor_measurement_form.csv`의 label, 상태, 축, 무부하전류/RPM, backlash, 30분 온도, Gate-1 torque 결과가 모두 닫혀야 한다. Reference motor도 사용자 승인과 수령검사 없이 구매품으로 승격하지 않는다.

## Gate-1 target allocation reconciliation

`exports/jigs/gate1/bom.csv`의 제작 항목은 `cash_budget.csv` CNC/drive bucket 안에서만 배분한다: CUT-01 coupon 2장 4,000, CUT-03/CUT-08 3,000, CUT-05 pair 7,000, CUT-04 screen 1장 4,000, keyed DRV-03 3,000, DRV-F01/02/#35 3,000 KRW다. Metrology 7,500 KRW와 jig print 4,400 KRW는 `OPTIONAL_EMPIRICAL` 별도 버킷이다. 모두 공급사 견적이 아닌 **design-to-cost ceiling**이다.

Gate-1 coupon-jig 수량은 사용자 승인 후에만 RFQ할 수 있다. Full cutter stack, 두 번째 screen, full screw/barrel도 동일하게 `PROCUREMENT_APPROVAL_GATE=USER_APPROVAL_REQUIRED`이며, optional Gate-1 미수행 자체는 design/fabrication readiness 차단 근거가 아니다.

## Release lock

- CUT-01 전체 12장: 사용자의 명시적 full-fabrication 승인 전 발주 금지. Optional Gate-1 결과는 의사결정 자료이지 main/design release 필수조건이 아님.
- EX-SCR-01/EX-BAR-01 full part: process coupon, 공급사 DFM과 Gate-3 전 발주 금지.
- Heater, motor, bearing, sprocket, driver, thermal safety품: `USER_APPROVAL_REQUIRED`.
- Gate-1 raw evidence는 optional empirical 자료이며 `main` 승격 조건이 아니다. Budget cap과 구매 승인은 독립 gate다.
