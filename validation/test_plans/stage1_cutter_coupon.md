# Stage 1 cutter coupon test plan

## Protected requirement or failure mode

REQ-FUNC-005, REQ-PERF-001, REQ-SAFE-005와 Stage 1 torque/geometry assumptions. 잘못된 cutter geometry 또는 과소평가한 torque가 motor stall, shaft damage와 파편 방출로 이어지는 위험을 보호한다.

## Why this test changes a decision

실측 peak/energy가 40~50 N·m trip envelope를 넘으면 drive, shaft, cutter bite, feed gate 또는 허용 PLA 두께를 변경한다. PET가 포획되지 않으면 hook profile을 변경한다. 이 시험 전에는 cutter CNC batch를 주문하지 않는다.

## Input

- PET body flat coupon: 실제 세척·건조 bottle body, 두께 측정
- PET folded coupon: 2겹 및 seam/neck 인접부는 별도 표시
- PLA printed shells: 동일 재료로 1.2, 2.0, 3.0 mm wall, infill/print orientation 기록
- 금속·label·adhesive·보강재가 없는지 검사

## Method

1. full-width cutter보다 한 tooth와 replaceable counter-edge를 사용하는 shielded manual fixture를 제작한다.
2. torque transducer 또는 calibrated lever-arm + load cell을 사용한다. motor supply current만으로 torque를 추정하지 않는다.
3. shield를 닫고 remote actuation한다. face shield는 containment 대체물이 아니다.
4. 각 sample 최소 5회 peak torque, displacement와 failure mode를 기록한다.
5. cut/tear/buckle/escape/jam을 구분하고 파편 containment를 확인한다.

## Expected evidence

원시 force/torque-displacement CSV, sample 치수·질량·사진, fixture calibration, 파손 후 cutter edge 사진.

## Pass/fail threshold

- 정상 허용 sample의 95th percentile peak가 bounded drive envelope 안에 있어야 한다.
- 40 N·m 이전에 feed-limit 가능한 징후가 없거나 50 N·m를 넘는 sample은 허용 입력에서 제외하거나 cutter/drive를 재설계한다.
- cutter permanent deformation, crack, fastener slip 또는 containment failure는 즉시 Fail이다.

## Result

미실시 — 실제 coupon, fixture와 사용자 물리 작업 필요.
