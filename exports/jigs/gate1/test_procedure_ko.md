# Gate-1 CUT-01 coupon 시험 절차와 합격기준

## 시험 전 부품과 계측

- CUT-01 coupon 2개와 CUT-04 5 mm screen coupon 1개만 사용한다. Full 12-disc stack과 screw/barrel 발주는 금지한다.
- PLA wall 1.2/2.0/3.0 mm: 25 x 80 mm, 각 5개.
- PET body single layer와 four-layer folded seam: 25 x 80 mm, 각 5개. Cap/neck/label/adhesive 제거.
- 0–200 N calibrated handheld force gauge(또는 load cell), M8 clevis + 독립 safety tether, arm radius 250.0 mm, driven-shaft Hall RPM, 50 A current sensor, 3/6/20 mm sieve, 0.1 g scale, video.
- Force gauge는 0/49.05/98.10/147.15 N에서 오차 <=2%, arm radius 오차 <=0.5 mm여야 한다.

## A. Lockout와 dry mechanical

1. Main disconnect OFF/0 V, shaft block, guard open 상태에서 fastener torque와 shim을 기록한다.
2. Hand rotation 20회: cutter/plate/gear/screen 접촉 0, shaft TIR <=0.10 mm, phase error <=1.0°, CUT-08/collar 이탈 0, DRV-03 key 상대 slip 0.
3. G1J-12 roof를 포함한 polycarbonate guard의 unguarded opening이 6 mm 이하인지 확인한다. S0 E-stop과 S1 positive-opening switch가 K0/K1을 drop하여 motor bus energy를 실제 제거하는지 각각 continuity/voltage test한다. 전원 복귀 후 S2 START 없이 K1이 자동 재투입되면 FAIL이다.

## B. Quasi-static 절단토크

1. Coupon을 push stick으로 capture point에 놓고 guard를 닫는다.
2. Force gauge를 arm 운동평면에서 각도 편차 2° 이하로 유지하고 3–5 rpm 상당으로 당겨 peak force `F_peak`를 기록한다. `T_peak=F_peak x r`, `r=0.2500 m`다.
3. 각 specimen 5회 후 median, maximum, failure mode(capture/buckle/shear/slip)를 기록한다.
4. PLA 세 두께와 PET body의 max <=14 N·m, folded seam max <=24 N·m이어야 한다. 24 N·m 전에 shaft/gear/plate 영구변형, tooth crack 또는 key damage가 있으면 FAIL이다.

## C. Motor/current와 jam recovery

1. Main disconnect/shaft lockout 상태에서 G1J-02 torque arm을 제거하고 `gate1_powered_assembly.step`대로 합격 donor motor와 DRV-01/Axx/F01/02/#35 경로를 연결한다. PLA 32 rpm/PET 24 rpm에서 no-load current/RPM, 별도 calibration arm/load-cell torque 대비 current-to-torque slope, 실제 sprocket ratio와 효율을 기록한다. `verified` calibration record 없이는 powered cutter를 시작하지 않는다.
2. 14/18/22/34/48 N·m는 모두 cutter-shaft reference다. Motor-side `DRV-F01`을 구동모터 분리 상태에서 quasi-static calibration한다. 효율 0.85 기준 시작 setting은 12:18 = 17.25 N·m, 12:24 = 12.94 N·m, 12:30 = 10.35 N·m이며, 실제 ratio/효율/측정 불확도를 기록해 22 N·m cutter-equivalent에서 분리되도록 보정한다. DRV-02·chain·phase pair는 분리 또는 영구변형되면 FAIL이다.
3. Controlled jam을 각 재질 3회 만든다. Calibrated cutter torque 18 N·m에서 PLA 650 ms/PET 850 ms 또는 command 대비 RPM 35% drop/500 ms에서 reverse가 시작돼야 한다. 고정 A값은 donor 공통 torque 기준으로 사용하지 않는다.
4. Reverse는 PLA 800 ms/PET 1100 ms, 최대 3회다. 세 번째 실패 뒤 enable=0과 latched fault가 유지돼야 한다.
5. Guard를 열고 lockout/jam 제거 확인 없이는 reset되면 FAIL이다.

## D. Chip-size

1. CUT-04 5 mm screen과 동일 5 s screen dwell, oversize 재투입 1회 이하로 재질별 최소 30 g을 시험하고 chip을 20/6/3 mm sieve로 분류한다.
2. `3–6 mm`, `6–20 mm`, `>20 mm long strip`, `<3 mm fines` 질량과 총 회수율을 기록한다.
3. 초기 합격: 3–6 mm >=55%, >20 mm PET strip <=10%, fines <=15%, 회수율 >=95%. 미달이면 CUT-01 전체 수량을 발주하지 않고 hook/screen coupon만 수정한다.

## 기록과 release

`preflight_inspection_template.csv`, `calibration_log_template.csv`, `drive_calibration_template.csv`, `gate1_results_template.csv`, `jam_recovery_results_template.csv`, `chip_size_results_template.csv`, `evidence_manifest_template.csv`를 각각 작성한다. 하나의 specimen 행에 서로 다른 시험을 합쳐 쓰지 않는다. Gate-1 PASS는 실제 서명된 raw CSV, calibration, 사진/영상 경로와 `gate1_release_record_ko.md`의 hash가 있어야 하며 simulation 값으로 대체할 수 없다.
