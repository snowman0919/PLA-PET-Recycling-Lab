# 가정과 확인 대기 항목 — safety-orchestration-closure-v0.6.1

|항목|디지털 입력|상태/필요 증거|
|---|---|---|
|PLA/PET flake bulk density|200–350 kg/m³|Gate-2 sieve/bulk measurement|
|Cutter shaft|20 mm keyed S45C|OpenModelica envelope+CalculiX/closed-form; optional Gate-1 data는 model correlation|
|Torque hierarchy|14/18/22/34/48 N·m|22 N·m mechanical fuse 실물 calibration 필요|
|Shredder motor|18–30 V geared brushed DC, cutter 20–40 rpm|exact donor/label/shaft/current/RPM/temperature 미확정|
|Reference motor|GMP60-60127-2460 ratio 47, 24 V, 70 rpm, 9.80665 N·m, 8.2 A rated|공개 datasheet 기반 digital reference; 수령검사/Gate-1 전 `verified=false`|
|Screw drive|15 N·m continuous, 22 N·m trip|donor reducer와 torque calibration 필요|
|PET pre-dry|온도·시간 미지정|`UNQUALIFIED_EXTERNAL_PROCESS`; dryer/moisture coupon 필요|
|PLA pre-dry|온도·시간 미지정|`UNQUALIFIED_EXTERNAL_PROCESS`; dryer/moisture coupon 필요|
|Gauge uncertainty|목표 U95 ≤0.03 mm|traceable pin/wire 교정 전 미달성|
|Cooling feedback|Mega A4 fan-current input, command threshold + 1.5 s dwell|shunt/증폭기 정격과 donor fan normal/open/stall window 실측 전 `valid=false`; 직접 tach claim 아님|
|Traverse permission|software state permission + 공통 hardwired guard/driver chain|현재 별도 traverse-driver fault/tach feedback 없음; production adapter의 `traverse_permission_ok`는 motor-health 측정값이 아니며 전용 diagnostic 채택 시에만 별도 fault 입력으로 승격|
|Cash target|178,729 KRW + 20,000 KRW reserve = 198,729 KRW|cooling fan tach mux, screw/puller/spool tach와 traverse limits 최소 allowance 포함; donor/RFQ 전 conditional only; 절대 cap 여유 1,271 KRW|
|Heater|barrel 3×100 W + die 60 W, T1–T5, extrusion peak 490 W|supplier/stock 확인과 physical thermal test 전 surrogate|
|Throughput|PLA 16 rpm 99.4, PET 18 rpm 97.5 g/h virtual default|실제 측정 claim 금지; 200 g/h `DIGITAL_STRETCH_TARGET`|
|Fusion solver|STEP 9개, LC01–LC10과 7개 study 계약|실제 Autodesk Fusion 결과 미제공; `PENDING_EXTERNAL_EXECUTION`|
|Project-lab 재고/RFQ|검사용 빈 evidence/register|사진·라벨·실측·업체 회신 전 `NOT_VERIFIED`/`NOT_RECEIVED`|
