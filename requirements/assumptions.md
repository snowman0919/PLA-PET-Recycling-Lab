# 가정과 확인 대기 항목 — solid-manifold-openmodelica-v0.4

|항목|디지털 입력|상태/필요 증거|
|---|---|---|
|PLA/PET flake bulk density|200–350 kg/m³|Gate-2 sieve/bulk measurement|
|Cutter shaft|20 mm keyed S45C|Gate-1 torque pulse 후 구조 재검토|
|Torque hierarchy|14/18/22/34/48 N·m|22 N·m mechanical fuse 실물 calibration 필요|
|Shredder motor|18–30 V geared brushed DC, cutter 20–40 rpm|exact donor/label/shaft/current/RPM/temperature 미확정|
|Reference motor calibration|1.8 A no-load, 1.35 N·m/A, ratio 2, η 0.72|sensitivity 전용, `verified=false`, 운전 불가|
|Screw drive|15 N·m continuous, 22 N·m trip|donor reducer와 torque calibration 필요|
|PET pre-dry|온도·시간 미지정|`UNQUALIFIED_EXTERNAL_PROCESS`; dryer/moisture coupon 필요|
|PLA pre-dry|온도·시간 미지정|`UNQUALIFIED_EXTERNAL_PROCESS`; dryer/moisture coupon 필요|
|Gauge uncertainty|목표 U95 ≤0.03 mm|traceable pin/wire 교정 전 미달성|
|Cash target|179,434 KRW + 20,000 KRW reserve = 199,434 KRW|donor/RFQ 전 conditional only; 절대 cap 여유 566 KRW|
|Throughput|PLA 18 rpm 111.8, PET 20 rpm 108.4 g/h nominal model|Gate-4 전 실제 claim 금지; 200 g/h stretch|
