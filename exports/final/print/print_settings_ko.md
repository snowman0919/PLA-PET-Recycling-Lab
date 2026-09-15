# v0.8 3D 출력 설정

- 기준: PrusaSlicer 2.9.6, 0.4 mm nozzle, `exports/print/slicer_profiles/PPR_PrusaSlicer_2.9.6.ini`.
- 내부 release envelope는 각 축 210 mm 이하이며, plate 배치는 220 × 220 × 220 mm를 초과하지 않는다.
- part별 재료·방향·layer·wall·top/bottom·infill·support·후처리는 `print_manifest.csv`가 지배한다.
- `orientation_renders/`는 실제 released G-code의 first-layer 경로다. 3MF plate 수량과 bed bounds를 생성기가 검사한다.
- PPR-TC01 coupon을 먼저 출력하고 실제 bore/shaft/insert 보정을 기록한 뒤 critical fit을 ream/후처리한다.
- ABS 지정 PPR-C05/C06/C07도 hot-zone 내부 구조재로 쓰지 않는다. 조립 후 표면온도와 shield clearance 확인 전 가열 금지.
- STL/3MF manifold 및 디지털 수량 검사는 PASS이나 `physical_fit_status`는 실제 출력 전까지 `HOLD_NOT_RUN`이다.
