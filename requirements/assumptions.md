# 가정과 확인 대기 항목 — virtual-physics-closure-v0.5.1

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
|Cash target|173,729 KRW + 20,000 KRW reserve = 193,729 KRW|donor/RFQ 전 conditional only; 절대 cap 여유 6,271 KRW|
|Heater|barrel 3×100 W + die 60 W, T1–T5, extrusion peak 490 W|supplier/stock 확인과 physical thermal test 전 surrogate|
|Throughput|PLA 16 rpm 99.4, PET 18 rpm 97.5 g/h virtual default|실제 측정 claim 금지; 200 g/h `DIGITAL_STRETCH_TARGET`|
