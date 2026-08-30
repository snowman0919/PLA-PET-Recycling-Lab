# 현금비용 value engineering — coupled-digital-validation-v0.5

## 결론

Compact single-path architecture와 E-stop, guard interlock, branch fuse, 독립 thermal fuse를 유지하면서 360 W 공정가열계와 T1–T5를 포함한 조건부 계획액을 **170,629 KRW**, 20,000 KRW 견적변동 예비비 포함 절대 계획액을 **190,629 KRW**로 낮췄다. 조건부 여유는 **9,371 KRW**다.

이 값은 견적·영수증이 아니다. `VERIFIED_PROCUREMENT_BUDGET`은 아직 `NOT_ESTABLISHED`이며, 미확인 donor motor와 project-lab stock은 0원으로 확정하지 않았다. 실물의 모델·수량·상태와 공급사 견적이 없으므로 구매 release는 계속 `BLOCKED`다. 특히 donor가 합격하지 않거나 heater/CNC 견적이 allowance를 넘으면 budget gate는 재실행해야 하며, 안전부품이나 heater wattage를 삭제해서 차이를 흡수하지 않는다.

## v0.4 대비 VE

|항목|기존 allowance|v0.5 allowance|근거와 잠금|
|---|---:|---:|---|
|CUT-01/CUT-03/CUT-05 flat·shaft|28,000|20,000|동일 CUT-01 nesting, donor plate, 표준 S45C h6 stock; Gate-1은 cutter 2장만|
|Screw/barrel/die/thrust CNC|44,000|33,000|process coupon과 full-part 견적 분리, 동일 SCM440 lot; 초과 견적은 blocker|
|Shredder driver/current|22,000|8,000|보유 BTS7960-class와 project-lab Hall 또는 50 A/75 mV shunt 우선, 20 A bench-test; torque safety를 current 하나에 의존하지 않음. 16,748 KRW genuine ACS758은 driver와 합쳐 21,368 KRW이므로 baseline에서 제외|
|Chain/phase interface|8,000|6,000|표준 #35 12T/30T blank, DRV-02, 동일 DRV-03 lamination nesting|
|Gauge/thermal stock/hardware|23,500|16,500|PCB-free optics, donor grounded sheet, M4/M5 표준화|
|신규 360 W heater/T1–T5/MOSF|0|34,500|3× custom band, die cartridge, 4× PTC 시작품, 5 probe, 5 MOSF channel을 명시적으로 추가|

가열계를 누락한 v0.4 합계와 단순 비교하면 순감액은 7,500 KRW지만, v0.5에는 이전에 현금행으로 잡히지 않았던 heater·sensor·switching hardware 34,500 KRW가 새로 포함됐다.

## Drive interchangeability

`DRV-01` Ø65 common-pass-through universal plate, motor-specific `DRV-Axx`, motor-side `DRV-F01` shear element, #35 12T:30T, cutter-side `DRV-02`, 6 mm key를 가진 generic M3 Z16 face18 `DRV-03` phase pair를 경계로 삼는다. MY1016Z, 특정 elastomer coupling, 특정 gear 제조사에 종속하지 않는다. DRV-03의 M4/dowel은 적층 위상만 재현하고 실제 shaft torque는 공통 key가 전달한다.

정확한 digital reference는 TT Motor `GMP60-60127-2460 ratio 47`이다. 공개 정격 70 rpm/100 kg·cm(9.80665 N·m)를 12T:30T, 효율 0.85에 적용하면 cutter 28 rpm/20.84 N·m다. 요청된 `GMP42-775PM ratio 51`은 90 rpm/26 kg·cm(2.5497 N·m)이고 같은 감속 후 5.42 N·m라 14 N·m 연속기준에 불합격한다. `DRV-A42`는 다른 고토크 42GP 변형을 위한 호환도면으로만 유지한다.

현금 0원 donor 합격은 `bom/donor_drive_acceptance.csv`와 `exports/drive_interface/donor_measurement_form.csv`의 label, 상태, 축, 무부하전류/RPM, backlash, 30분 온도, Gate-1 torque 결과가 모두 닫혀야 한다. Reference motor도 사용자 승인과 수령검사 없이 구매품으로 승격하지 않는다.

## Gate-1 target allocation reconciliation

`exports/jigs/gate1/bom.csv`의 현금계획은 `cash_budget.csv` bucket 안에서만 배분한다: CUT-01 coupon 2장 4,000, CUT-03/CUT-08 3,000, CUT-05 pair 7,000, CUT-04 screen 1장 4,000, keyed DRV-03 3,000, DRV-F01/02/#35 3,000, metrology 7,500, jig print 4,400 KRW다. 이는 공급사 견적이 아니라 **design-to-cost ceiling**이다. `bom/cnc_quote_package.csv`도 같은 금액과 release 수량을 사용하며, 초과 견적은 임의 축소나 안전 삭제가 아니라 budget blocker로 기록한다.

Gate-1 조립에 반드시 필요한 CUT-03 2장, CUT-05 2축, CUT-08 2장, CUT-04 1장, DRV-03 6장은 사용자 승인 후 coupon-jig 수량만 RFQ할 수 있다. 반면 CUT-01은 최대 2장만 허용하고 나머지 10장, 두 번째 screen과 full screw/barrel은 실제 물리 Gate 결과 전 계속 HOLD다.

## Release lock

- CUT-01 전체 12장: Gate-1 실제 PLA/PET torque, jam, chip-size PASS 전 발주 금지.
- EX-SCR-01/EX-BAR-01 full part: process coupon, 공급사 DFM과 Gate-3 전 발주 금지.
- Heater, motor, bearing, sprocket, driver, thermal safety품: `USER_APPROVAL_REQUIRED`.
- Gate-1 raw evidence가 없으므로 budget 문서가 일치해도 `main` 승격 금지.
