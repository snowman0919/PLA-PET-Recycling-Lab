# v0.5 요구사항 완료 감사 — HISTORICAL ARCHIVE

> 이 문서는 `coupled-digital-validation-v0.5` 아카이브 시점의 이력이다. 현재 release 판정에 사용하지 않으며, v0.5.1 현황은 `completion_audit_v0.5.1.md`를 따른다.

Revision: `coupled-digital-validation-v0.5`
Release: `DIGITAL_FABRICATION_BASELINE` / Physical: `PHYSICAL_VALIDATION_PENDING`

## 디지털 완료 범위

|요구|증거|상태|
|---|---|---|
|compact-single-path-v0.3 유지|architecture contract, 470×700×930 mm assembly|PASS_DIGITAL|
|특정 motor/coupling/gear 종속 제거|DRV-01/A42/A60/F01/02/03, 32-row interface catalog|PASS_DIGITAL|
|정확 기준모터 비교|GMP42 불합격, GMP60 28 rpm/20.84 N·m 기준|PASS_DIGITAL_REFERENCE|
|360 W heater와 T1–T5|thermal CAD/RFQ/channel schedule, 490 W active peak|PASS_DIGITAL|
|Gate-1 최소 cutter coupon jig|2×CUT-01, 15 jig part, manual/powered CAD·BOM·assembly·wiring·procedure·templates|READY_NOT_RUN|
|16 mm×16D screw/barrel RFQ|SCM440, clearance/runout/concentricity/Ra/열처리/공정/검사|RFQ_READY_ORDER_HOLD|
|연성 동역학|OpenModelica flange-connected electrical/mechanical/thermal/flow/spool 32 scenario PASS, legacy 시간기반 surrogate 제거|PASS_COUPLED|
|현금 cap|170,629 target / 190,629 reserve 포함|PASS_CONDITIONAL|
|출력 제한|12 family, 각 축 210 mm 이하, planning mass 1,012.70 g ≤1.5 kg|PASS_DIGITAL|
|interface catalog|mismatch 0 (28 PASS_DIGITAL, 4 verify/coupon-pending 표기)|PASS_DIGITAL|
|구조 screening|load envelope→CalculiX/공식 screening 9/9 PASS|PASS_DIGITAL|
|재생성 정합성|CLEAN_CLONE_REPRODUCIBILITY 566 artifact PASS|PASS_DIGITAL|

## 미완료 물리/조달 Gate

- Gate-1 cutter torque/current/RPM/jam/chip-size: `NOT_RUN` (jig READY, 사용자 승인 대기).
- Donor label/shaft/no-load/RPM/temperature/calibration: `UNVERIFIED`.
- Screw/barrel process coupon 및 supplier DFM: `NOT_RUN`.
- Gate-2~5: `NOT_RUN`.
- Verified procurement budget: `NOT_ESTABLISHED`.

따라서 full cutter stack, full screw/barrel, 구매/CNC 실행과 `main` 승격은 잠겨 있다. `DIGITAL_FABRICATION_BASELINE`은 제작·견적 검토 가능한 디지털 기준선이며 실제 절단 성능, melt flow, filament 품질 또는 안전 인증이 아니다.
