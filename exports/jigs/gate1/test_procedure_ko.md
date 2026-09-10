# Gate-1 CUT-01 coupon 시험 절차 — GGM v0.8 적용본

현재 controlling 상위 계약은 `validation/physical_v08/physical_gate_contract.json`이다. 기존 `gate1_powered_assembly.step`, DRV-01/Axx/F01 powered 경로와 18/22/24 N·m 합격기준은 **legacy**이며 현 GGM 구동 시험에 사용하지 않는다. 이 문서의 manual coupon geometry와 계측 양식은 계속 사용한다.

## 시험 전 부품과 계측

- CUT-01 coupon은 축당 1개, 총 2개만 제작한다. 나머지 10개는 Gate-1 PASS 전 제작하지 않는다.
- CUT-04 5 mm screen coupon 1개, CUT-05/CUT-05R 각 1개, CUT-03 plate 2개, 61905/6905 25×42×9 bearing 4개와 해당 metal retainer/seat를 사용한다.
- Powered 시험은 최종 GGM shredder path `K9DG60N2 + K9G75C → GGM protection coupling → 6201-supported jackshaft → #35 12T:30T`를 사용한다.
- PLA wall 1.2/2.0/3.0 mm와 cleaned PET body를 specimen ID별로 준비한다. 실제 폐출력물/PET 형태를 사진으로 남긴다.
- 0–200 N verified force gauge/load cell, 250.0 mm arm, 독립 tach, calibrated motor-lead current sensor, 3/6/20 mm sieve, 0.1 g scale를 사용한다.

## A. Lockout와 cold mechanical

1. Main power 0 V 상태에서 shaft/plate/bearing/gear/screen의 실제 part ID와 revision을 기록한다.
2. Hand rotation 20회에서 cutter/plate/gear/screen 접촉 0, shaft TIR ≤0.10 mm, phase error ≤1.0°, bearing/retainer axial release 0을 확인한다.
3. rotating-to-static clearance는 최소 1.90 mm다. Guard와 positive-opening interlock이 닫히지 않으면 powered 단계로 가지 않는다.
4. Manual torque arm과 powered GGM coupling은 동시에 장착하지 않는다.

## B. Quasi-static cutter demand

1. Coupon을 정해진 capture point에 놓고 guard를 닫은 뒤 250.0 mm torque arm을 3–5 rpm 상당의 낮은 속도로 당긴다.
2. `T_peak = F_peak × 0.2500 m`로 specimen별 peak/median과 capture/buckle/shear/slip mode를 기록한다.
3. 이 시험은 실제 PLA/PET cutter demand를 측정하기 위한 것이며 과거 14/18/22/24 N·m 숫자를 강제 합격점으로 쓰지 않는다.
4. 어떤 specimen에서도 shaft/gear/plate의 영구변형, tooth/key 손상, bearing release가 있으면 FAIL이다.

## C. GGM drive와 controlled jam

1. P3 GGM bench gate가 먼저 PASS해야 한다. 즉 current calibration, output torque holdout, software limit 8.0 N·m, mechanical protection 8.8–9.3 N·m가 실제 기록으로 확인되어야 한다.
2. Powered coupon은 legacy `gate1_powered_assembly.step` 대신 final GGM drive manufacturing/assembly 자료를 사용한다. Shredder cutter speed 목표는 약 16 rpm이며 실제값을 기록한다.
3. 정상 PLA/PET body 투입에서 8.0 N·m gearbox software limit가 반복적으로 동작하면 처리량/투입법을 낮추고 원인을 기록한다. 정상 처리 합격을 위해 protection threshold를 올리지 않는다.
4. Controlled jam은 guard closed 상태에서 소수의 정해진 specimen으로 수행한다. Guarded stop/reverse sequence와 tach-loss behavior가 현 GGM firmware contract대로 bounded하게 끝나야 하며 세 번째 실패 이후 latched fault가 유지되어야 한다.
5. Jam 제거 전 자동 재시작이 발생하거나, mechanical protection 뒤 구동계/chain/phase gear에 영구변형이 생기면 FAIL이다.

## D. Chip-size / 재순환

1. 재질별 최소 30 g을 CUT-04 5 mm screen으로 처리하고 20/6/3 mm sieve로 분류한다.
2. 1차 결과와 oversize 1회 재순환 결과를 분리해서 기록한다.
3. 최종 합격은 재순환 1회 이하에서 `3–6 mm ≥70%`, `>20 mm PET strip ≤2%`, `<3 mm fines ≤15%`, 총 회수율 `≥95%`다.
4. 미달이면 남은 CUT-01 10개를 제작하지 않고 hook/screen/feed strategy만 수정한다.

## 기록

기존 `preflight_inspection_template.csv`, `calibration_log_template.csv`, `drive_calibration_template.csv`, `gate1_results_template.csv`, `jam_recovery_results_template.csv`, `chip_size_results_template.csv`, `evidence_manifest_template.csv`를 계속 사용하되 GGM field mapping은 `validation/physical_v08`와 `analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json`이 우선한다. Simulation 값을 실제 measurement 칸에 복사하지 않는다.
