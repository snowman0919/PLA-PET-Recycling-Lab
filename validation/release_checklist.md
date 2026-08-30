# Release checklist — coupled-digital-validation-v0.5

## v0.5 digital gate (DIGITAL_FABRICATION_BASELINE)

- [x] `validation/run_all.py` 전체 통과 (2026-08-30, stale manifest 재생성 후 재검증 포함)
- [x] nominal envelope 470×700×930 mm; hard `500 × 750 × 1000 mm`, target `480 × 720 × 950 mm` 이내
- [x] heater 360 W 포함 조건부 target cash 170,629 KRW ≤180,000; reserve 포함 190,629 KRW ≤200,000 (계획 여유 9,371 KRW)
- [x] GMP60 기준모터(digital reference), DRV-A60 adapter/F01 shear fuse, 3× band/die cartridge/PTC spreader/T1–T5 포함 active CAD 재생성·간섭검사 PASS
- [x] active STL watertight/manifold, zero-area/non-manifold 0
- [x] PrusaSlicer 2.9.6 actual toolpath: support 포함 904.20 g, reserve 포함 1,012.70 g ≤ 1.5 kg target
- [x] OpenModelica flange-connected coupled motor/thermal/flow/spool 32 scenario acceptance PASS (전류∧속도비∧dwell jam 판정, one-shot shear fuse, rotor-angle tooth engagement)
- [x] 새 OpenModelica load envelope이 구조 screening/CalculiX 입력과 trace 가능 (analysis/load_cases/openmodelica_dynamic_envelope.json → 9/9 screening PASS)
- [x] 시간기반 legacy surrogate 제거(4 system + 14 component), sensor-coupled state machine만 유지
- [x] Firmware config가 baseline에서 생성되고 unverified drive calibration을 거부
- [x] Gate-1 evidence package가 preflight/drive/25 torque/6 jam/2 chip/evidence-hash 전용 CSV로 분리되고 release lock 유지
- [x] README/requirements/baseline/BOM/PDF/manifest revision·release state 일치 (`DIGITAL_FABRICATION_BASELINE` / `PHYSICAL_VALIDATION_PENDING`)
- [x] 전체 재생성 후 normalized artifact hash gate PASS (`CLEAN_CLONE_REPRODUCIBILITY`, 566 artifacts)
- [x] stale architecture/current-source 검사 PASS (legacy 시간기반 모델 0)
- [x] current drive/thermal/assembly render 생성과 parent multimodal visual review 기록 (`validation/visual_review/2026-08-30-coupled-digital-validation-v0.5.md`)
- [x] remote branch push 후 clean clone 전체 재생성 및 normalized hash 재현 PASS (commit `f828750`, 2026-08-30, `validation/results/clean_clone_validation.json`)

## Procurement / physical-phase 항목 (digital gate와 분리)

- [ ] `VERIFIED_PROCUREMENT_BUDGET` 확립 — 현재 `NOT_ESTABLISHED`; supplier 견적, shipping, donor 실물 라벨/전류/RPM 증거 필요. 구매 자체는 USER_APPROVAL_REQUIRED.
- [ ] Gate-1 cutter coupon: `NOT_RUN` (jig READY, 실행은 사용자 승인 후)
- [ ] Gate-2 flake/feed coupon: `NOT_RUN`
- [ ] Gate-3 cold mechanical proof: `NOT_RUN`
- [ ] Gate-4 hot extrusion: `NOT_RUN`
- [ ] Gate-5 diameter/full spool: `NOT_RUN`

현재 release state는 `DIGITAL_FABRICATION_BASELINE`, physical state는 `PHYSICAL_VALIDATION_PENDING`이다. 이는 제작·견적 검토 가능한 디지털 package이며 성능·안전 인증이 아니다.

Gate-1 signed raw CSV와 photo/video hash가 PASS가 아니므로 full CUT-01 stack, full EX-SCR-01/EX-BAR-01 발주와 `main` fast-forward는 모두 금지한다. 구매·CNC·heater energization에는 별도 사용자 승인이 필요하다.
