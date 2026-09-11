# PPR v0.8 물리 검증·제작 준비 기준

이 디렉터리는 디지털 설계를 실제 제작으로 넘기기 위한 controlling handoff다. 최종 release ZIP을 만들기 위한 문서가 아니며, 이 파일의 존재는 구매·가공·통전을 승인하지 않는다.

## 현재 진입 상태

`simulation_prerequisite.py`는 `validation/v08_full_compliance.py`를 다시 실행한 뒤 release package와 remote policy 두 항목만 제외한다. 나머지 23개 기술 gate가 모두 PASS해야 `simulation_prerequisite.json`이 PASS가 된다. 현재 PASS는 물리행동 승인과 별개다.

## 비용을 줄이는 제작 전략

전체 기계를 한 번에 만들지 않는다. 먼저 프로젝트실 재고를 조사하고, GGM 모터를 수령해 실제 치수를 측정한 다음 장착부를 확정한다. 분쇄기는 CUT-01 12장 중 2장만 coupon으로 먼저 가공한다. screw/barrel은 본품 전에 EX-CPN-SCR/EX-CPN-BAR만 동일 공정으로 만들고 경도·질화층·Ra·치수/간극을 확인한다. 실패하면 나머지 수량을 발주하지 않는다.

현재 frame cut list 합계는 2020 profile 13.348 m/26 pieces, 2040 profile 1.320 m/2 pieces다. 보유 프로파일의 실측 usable length를 먼저 적고 부족분만 구매한다. GGM CAD의 reference profile LOD를 이 길이에 중복 가산하지 않는다.

## 구동부의 현재 물리 기준

분쇄기는 GGM K9DG60N2 + K9G75C, 압출기는 K9DG60N2 + K9G150C를 기준으로 한다. BTS7960 두 개는 보유품을 각각 한 축에 사용한다. 소프트웨어 gearbox torque limit은 8.0 N·m이며 기계식 보호부의 실측 목표는 8.8–9.3 N·m다. 과거 Gate-1 문서의 18 N·m trip/22 N·m shear 또는 24 N·m PET acceptance는 현 GGM 설계의 물리 합격기준으로 사용하지 않는다.

250 mm torque arm에서는 8.0 N·m = 32.0 N, 8.8 N·m = 35.2 N, 9.3 N·m = 37.2 N이므로 기존 0–200 N force gauge 범위로 충분하다. 전류센서는 motor lead에서 독립 기준으로 교정하며 0–6 A 사용 범위에서 U95 포함 오차 <=0.10 A, torque holdout error <=0.40 N·m를 목표로 한다.

분쇄기 chain output은 구형 DRV-02 bolt-on hub가 아니라 direct-keyed `GGM_SH_12T/GGM_SH_30T`다. 4x4/6x6 key가 토크를 전달하고 수령 sprocket의 maker retention feature가 축방향 위치만 유지한다. 각 sprocket radial TIR는 U95 포함 <=0.10 mm, total axial shift는 U95 포함 <=0.20 mm이며, 이 retention 사양을 수령품에서 확인하지 못하면 P4 powered coupon으로 진행하지 않는다.

## 고온부의 현재 물리 기준

Rear datum/collar bore는 Ø34.25, front guide는 Ø34.60이며 cold axial free travel은 1.50 mm 이상이다. Screw/barrel matched diametral clearance는 0.28–0.32 mm다. Die SYS-04는 M4x45 class 10.9 stock screw를 42.5±0.1 mm로 절단·디버링하고 dry 1.50 N·m를 사용한다. 첫 thermal cycle과 실제 누설은 아직 NOT_RUN이다.

## 전기/안전 기준

24 V 800 W PSU는 보유 자산이지만 machine protected envelope는 30 A main branch와 기존 운전 power cap을 유지한다. E-stop 버튼 보유만으로 K0 contactor, positive-opening lid/service switch, thermal cutoff, branch fuse가 확보된 것으로 간주하지 않는다. 첫 통전은 logic branch만 current-limited로 수행하고 motor/heater branches는 분리한다.

## 파일 역할

- `simulation_prerequisite.json`: 최신 기술 gate 상태.
- `physical_gate_contract.json`: 단계별 진입/합격 기준.
- `inventory_confirmation.csv`: 프로젝트실 재고 및 구매 전 확인표.
- `measurement_equipment.csv`: 필요한 계측 능력. 구매 목록이 아니라 lab borrowing/공급사 측정을 포함한다.
- `fabrication_sequence.csv`: 최소수량 제작 순서와 사용자 승인 지점.
- `stage_minimum_bom.csv`: P1/P3/P4/P5/P9에서 실제로 준비할 최소 수량. 시험용 consumable과 최종 기계 부품을 구분한다.
- GGM 실제 raw measurement 형식은 `analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json`을 사용한다.

물리시험 수치는 simulation 값을 복사해 채우지 않는다. 모든 실제 값은 측정 장비 ID, 측정시각, 원시 CSV/사진/로그의 hash와 함께 기록한다.

## MVP와 smoke 검증 정책

이 프로젝트의 MVP는 별도 프로토타입이 아니라 최종 제품 자체다. `MVP_SMOKE_VALIDATION_KO.md`와 `mvp_smoke_contract.json`의 S0~S5를 P1~P9와 병행하고, 실패한 checkpoint는 downstream 작업을 HOLD한다. raw evidence를 보존한 뒤 repository 설계를 수정하고 영향을 받는 release artifact와 stage release를 다시 검증한다. smoke 결과를 이유로 acceptance limit을 현장에서 완화하지 않는다.
