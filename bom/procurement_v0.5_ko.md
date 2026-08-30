# v0.5 구매처·제품 확정 (구매 실행 전 단계)

Revision: `coupled-digital-validation-v0.5` / 작성일: 2026-08-30

## 확정 원칙

- 이 문서는 **구매처(vendor)와 제품(product)을 확정**한 것이며, **구매 실행, 발주, 결제는 포함하지 않는다**.
- 구매 승인 대상(USER_APPROVAL_REQUIRED): heater, motor, bearing/sprocket, driver, thermal safety item, CNC 가공.
- 모든 가격은 2026-08-30 공개 페이지 기준이며 배송비·환율 변동과 최종 견적 전까지 `CONDITIONAL_PLANNING_BUDGET`이다. 영수증이 생기기 전까지 `VERIFIED_PROCUREMENT_BUDGET=NOT_ESTABLISHED`를 유지한다.

## 구매처·제품 확정 목록

|품번|제품|구매처|수량|예상 단가|납기|상태|
|---|---|---|---|---:|---|---|
|HT-CART-01|24 V 60 W Ø6 카트리지 히터 (3D 프린터 호환 stock)|AliExpress item 1005007292681977|1|~3,000 KRW|2-4주|구매처·제품 확정, 사용자 승인 대기|
|HT-PTC-01|24 V 절연 알루미늄 쉘 PTC 35×21×5 class (80–110 °C class)|AliExpress 24V PTC heater element 카테고리|4(→4-8)|~2,500 KRW|2-4주|구매처·제품 확정, 1개 실측 후 수량 확정|
|HT-BAND-01|custom mica band 24 V 100 W ID34 W45|1순위 한국전자전열 heater1.co.kr(대전), 2순위 한일전열엔지니어링 han-il.com, 대안 AliExpress custom|3|견적 필요|국내 1-3주 예상|구매처 확정, 견적 대기 (bucket 15,000 KRW)|
|TEMP-TC-01|MAX6675 K-type 열전대 모듈 SZH-CH031|디바이스마트 devicemart.co.kr|5|~4,500 KRW|재고 1-3일|구매처·제품 확정, 사용자 승인 대기|
|ELEC-MOSFET-01|D4184-class 옵토 아이솔 MOSFET 1ch 모듈|디바이스마트/엘레파츠|5|~2,500 KRW|재고 1-3일|구매처 확정, 10 A bench test 후 채택|
|ELEC-FUSE-01|SF139E-class thermal fuse + branch fuse holder|국내 부품몰(디바이스마트/엘레파츠)|1 lot|6,500 allowance|재고|정격은 heater RFQ 수령검사계약 따름|
|SH-DRIVER|BTS7960 43 A 모듈|ICBanq P014373686|1|4,620 KRW|재고|구매처·제품 확정, bench test 전 BUY 유지|
|SH-CHAIN|#35 스프로킷 12T/30T(보어 가공) + #35 chain|한국미스미 경제형 스프로켓 35 (ISO 06A/ANSI 35)|1 set|9,000-15,000|4일-1주|구매처 확정, 견적 대기|
|SH-MOTOR-REFERENCE|GMP60-60127-2460 ratio47|TT Motor 공장 직접 RFQ (ttmotor.com)|1|공장 견적|3-6주 예상|디지털 기준모터, baseline cash 제외|
|SH-MOTOR-DONOR|기존 무료 donor 기어드 모터|project-lab 실물 확인|1|0 (증거 필요)|-|DONOR_VERIFY_HOLD 유지|

## 기각 기록

- Omega MBH mica band: 단품 14.5만 KRW~, 납기 11주 → HEAT-BAND bucket(15,000 KRW/3개) 대비 과다, 기각.
- GMP42-775PM ratio51: 공개 정격 2.55 N·m → cutter 환산 5.42 N·m < 14 N·m 연속 요구, 기각 (datasheet 확인).
- 신용모터 GGM 웜기어드 24 V 60 W: 국내 대안이나 약 56,100 KRW로 baseline cash 초과 → `NON_BASELINE_QUOTE_ONLY` 유지.
- PT100/MAX31865: 비용 증가 대비 반복성 이득이 MVP 요구를 초과, 미채택.

## 예산 영향 (바닥에서 재계산한 예상 델타, 2026-08-30)

|항목|bucket|확정 가격 기준 예상|델타|
|---|---:|---:|---:|
|HEAT-DIE|4,000|~3,000|-1,000|
|HEAT-PTC|3,000|6,000-10,000|+3,000~+7,000|
|HEAT-BAND|15,000|견적 전 (AliExpress 대안 시 24,000-45,000)|0~+30,000 (최대 리스크)|
|TEMP-SENSE|7,500|20,000-30,000|+12,500~+22,500|
|HEAT-MOSFET|5,000|10,000-15,000|+5,000~+10,000|
|SH-INTERFACE|6,000|9,000-15,000|+3,000~+9,000|
|SH-DRIVE|8,000|4,620-8,000|-3,380~0|

예상 합계 델타: **+20,000 ~ +77,000 KRW** → 조건부 총액이 190,629 KRW(예비비 포함)를 초과해 **200,000 KRW 절대 상한을 침범할 가능성이 높다**.

## 상한 준수 옵션 (사용자 결정 필요 — 안전 삭제·와트 축소·donor 0원 조작 없이)

1. **donor 재사용 확대**: T1-T5 probe 일부·MOSFET 모듈·50 A Hall을 project-lab donor에서 확보하면 +20,000~+35,000 상쇄. 단, donor 실물 라벨/실측 증거 필요.
2. **묶음 발주**: AliExpress 히터·PTC·카트리지를 단일 주문으로 묶어 배송비 절감 (~5,000-10,000 상쇄).
3. **단계 구매**: Gate-1 먼저(cutter coupon + metrology), thermal 패키지는 Gate-1 통과 후 발주로 총 지출 시점을 분산.
4. **Misumi 경제형 유지 + HT-BAND 국내 견적 회신 후 재판단**: 국내 custom 견적이 25,000/3개 이하면 총액 유지 가능.

## 설계 반영

- `bom/bom.csv`: EX-03/EX-04/EX-05/FH-02/SF-03/SH-05 notes에 확정 구매처·제품 반영 완료.
- `bom/purchase_candidates.csv`: 6개 신규 row(HT/TEMP/ELEC) + SH-DRIVER/SH-CHAIN/SH-MOTOR-REFERENCE 상태 갱신.
- 기하·사양 변경 없음: 확정 제품은 기존 RFQ 계약(export/thermal/heater_rfq_ko.md)의 치수·저항·절감 수령검사 기준과 동일하므로 CAD/BOM 수치 변경 불요.
- 구매 승인 시에도 Gate-1 signed 증거 없이 full cutter stack/screw/barrel 발주 잠금과 `main` 승격 잠금은 유지된다.
