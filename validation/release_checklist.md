# Release checklist — solid-manifold-openmodelica-v0.4

## Digital fabrication baseline gate

- [x] `validation/run_all.py` 전체 통과
- [x] nominal envelope 470×700×930 mm; hard/target limit 이내
- [x] target cash 178,420 KRW ≤180,000; reserve 포함 198,420 KRW ≤200,000
- [x] active CAD valid closed-solid topology; review keep-out 격리
- [x] active STL watertight/manifold, zero-area/non-manifold 0
- [x] PrusaSlicer 2.9.6 actual toolpath: 913.67 g, reserve 포함 1,023.31 g
- [x] OpenModelica MSL 4.0.0 check/simulation/sweep 및 acceptance PASS
- [x] OpenModelica load envelope가 구조 screening/CalculiX 입력과 trace 가능
- [x] Firmware config가 baseline에서 생성되고 unverified drive calibration을 거부
- [x] README/requirements/baseline/BOM/PDF/manifest revision·수치 일치
- [x] stale architecture/current-source 검사 PASS
- [x] current render와 parent visual review 기록
- [x] clean clone 재현 PASS (`edb1790`)

## Physical gate — digital release와 분리

- [ ] Gate-1 cutter coupon: `NOT_RUN`
- [ ] Gate-2 flake/feed coupon: `NOT_RUN`
- [ ] Gate-3 cold mechanical proof: `NOT_RUN`
- [ ] Gate-4 hot extrusion: `NOT_RUN`
- [ ] Gate-5 diameter/full spool: `NOT_RUN`

현재 release state는 `DIGITAL_FABRICATION_BASELINE`, physical state는 `PHYSICAL_NOT_RUN`이다. 이는 제작 검토용 digital package이며 성능·안전 인증이 아니다.

Gate-1 signed raw CSV와 photo/video hash가 PASS가 아니므로 full CUT-01 stack, full EX-SCR-01/EX-BAR-01 발주와 `main` fast-forward는 모두 금지한다. 구매와 CNC 주문에는 별도 사용자 승인이 필요하다.
