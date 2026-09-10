# PPR v0.8 물리 제작·검증 실행 인덱스

이 문서는 실제 제작/검증 단계의 **단일 탐색 시작점**이다. 상세 기준은 `physical_gate_contract.json`, 실행 파일 연결은 `physical_execution_registry.json`이 controlling이다. 실제 구매·가공·모터 통전·히터 가열은 각각 별도 사용자 승인 전 수행하지 않는다.

| Stage | 목적 | 실행 문서 | 자동 분석 | 현재 상태 |
|---|---|---|---|---|
| P0 | DIGITAL_TECHNICAL_ENTRY | `PHYSICAL_BUILD_READINESS_KO.md` | `simulation_prerequisite.py` | `RUNTIME_EVALUATED` |
| P1 | INVENTORY_AND_RECEIPT | `P1_EXECUTION_KO.md` | `analyze_p1_records.py` + GGM mount compatibility + `profile_nesting.py` | `NOT_RUN` |
| P2 | COLD_FRAME_AND_FIT | `P2_COLD_FIT_KO.md` | `analyze_p2_records.py` | `NOT_RUN` |
| P3 | GGM_DRIVE_BENCH | `P3_GGM_BENCH_KO.md` | preflight -> records -> packet/inspector -> stage release -> review-only firmware profile | `NOT_RUN` |
| P4 | SHREDDER_COUPON | `P4_SHREDDER_COUPON_KO.md` | validated P3 release -> records -> `validate_p4_stage_release.py` | `NOT_RUN` |
| P5 | SCREW_BARREL_PROCESS_COUPON | `P5_PROCESS_COUPON_KO.md` | `analyze_p5_records.py` | `NOT_RUN` |
| P6 | COLD_EXTRUDER_ASSEMBLY | `P6_COLD_EXTRUDER_KO.md` | `analyze_p6_records.py` | `NOT_RUN` |
| P7 | ELECTRICAL_SAFETY_AND_LOGIC | `P7_ELECTRICAL_SAFETY_KO.md` | `analyze_p7_records.py` | `NOT_RUN` |
| P8 | INSTALLED_MOTOR_DRY_RUN | `P8_INSTALLED_MOTOR_DRY_RUN_KO.md` | firmware calibration/readback gate -> `analyze_p8_records.py` | `NOT_RUN` |
| P9 | EMPTY_HOT_ZONE | `P9_EMPTY_HOT_ZONE_KO.md` | `analyze_p9_records.py` | `NOT_RUN` |
| P10 | PLA_LOW_FEED | `P10_P11_MATERIAL_RUN_KO.md` | `analyze_material_run.py` | `NOT_RUN` |
| P11 | PET_LOW_FEED | `P10_P11_MATERIAL_RUN_KO.md` | `analyze_material_run.py` | `NOT_RUN` |
| P12 | FORMING_AND_SPOOL | `P12_FORMING_SPOOL_KO.md` | `analyze_p12_records.py` | `NOT_RUN` |

## 실제 첫 행동

현재 바로 수행 가능한 가장 저위험 작업은 P1의 **무가공 재고·치수 조사**다. Profile은 절단하지 않고 각 bar의 usable length만 기록한다. Bearing/PSU/BTS7960/Mega/E-stop/safety switch/fuse/current sensor/chain은 라벨·치수·상태만 확인한다. GGM 두 세트가 아직 미수령이면 P1 전체는 PASS가 아니라 `PARTIAL_NOT_RUN`이다.

P1 결과가 들어오면 profile nesting으로 P2 절단계획을 확정하고, GGM 수령 후 P3 bench fixture 치수를 received data에 맞춰 확정한다. P4에서는 CUT-01 두 장만 먼저 제작하며 나머지 10장은 결과 전까지 잠근다. P5에서는 screw/barrel 본품보다 process coupon을 먼저 승인한다.

P12까지 PASS해도 상태는 `PHYSICAL_VALIDATION_REVIEW_CANDIDATE`일 뿐 자동 생산·안전 인증이 아니다.

## 현장 launch package

`build_physical_launch_package.py`는 P1~P12 실행 문서·빈 측정 template·P3 GGM 준비자료·P4 두-cutter coupon CAD·P5 process coupon CAD만 묶는다. Production `EX-SCR-01/EX-BAR-01`, legacy `DRV-01/Axx/F01`, `gate1_powered_assembly`는 의도적으로 제외한다. `validate_physical_launch_package.py`가 이 금지목록과 payload SHA-256 전수검사를 수행한다. 패키지 상태는 항상 `PREPARATION_ONLY_NOT_FABRICATION_AUTHORIZATION`이며 별도 사용자 승인 없이 구매·가공·통전·가열을 허용하지 않는다.
