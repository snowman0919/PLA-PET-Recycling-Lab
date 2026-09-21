# C2.2 핸드오프 — 헤드리스 파쇄 벤치마크 I0–I6 완료 (디지털 순서확인, 물리 HOLD)

상태: `UNCALIBRATED_DIGITAL_SENSITIVITY` 전역. 성능 게이트 `BLOCKED_PERFORMANCE_DATA`.
구매·가공·통전·병합 모두 HOLD. M1 미선정. 예산 soft limit 100,000원.
이 문서는 Isaac Sim 없이 numpy-only로 수행한 순서확인용 벤치마크의 최종 인수인계다.
어떤 수치도 보정된 파쇄 성능·토크·수율 예측이 아니다.

## 리비전

- 작업 디렉토리: `/home/monad/develop/PPR-c2.1-codex-20260921` (clean clone).
  `/home/monad/develop/PPR`은 읽기 전용으로만 참조하고 수정하지 않았다.
- 브랜치 `codex/c2.1-s2-transmission-20260921`, HEAD `d42f32f915555f00d5ac97021f97ecfb1a6fbb98`,
  PR #5 OPEN. 브랜치 생성·커밋·푸시 없음 (`git status`는 `?? c2.2/`만 표시).
- C2.1 소스는 읽기 전용. C2.1 패키지 상태
  `DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD`를 그대로 상속한다.

## 단계별 상태 (I0–I6, 증거 경로 포함)

- I0 환경: `c2.2/results/i0_environment.json`, `i0_smoke.json`,
  `c2.2/logs/i0_smoke.log` (+ `c2.2/sim/bootstrap/smoke.py` 212 lines) —
  Isaac Sim venv 호환성 검사 PASSED + SimulationApp headless smoke PASSED
  (fast workstream, director 직접 검증: schema i0_smoke/1, Isaac 6.1.0.0,
  seed 20260921, 60 steps, z_drop 1.7336, final z 0.25, clean_shutdown true).
  호스트: Ubuntu 24.04.4, Ryzen 7 9700X 16T, RAM 30Gi, RTX 3080 10GB cc8.6
  driver 595.84 / CUDA-driver 13.2, nvcc·torch 없음, python 3.12.3/3.14.7.
- I1 에셋: `c2.2/results/i1_asset_manifest.json` — STEP SHA 4/4 일치
  (integration `e1756cac…` 66.75MB, S2 assembly `fbba8932…` 22.96MB,
  exploded `f05277f3…` 22.97MB, FCStd `b0041499…` 4.03MB).
  `c2.2/sim/assets/out/` STL 2종 + sidecar (traceability 필드 포함).
  pxr 부재로 USD 쓰기 불가 — STL을 USD 변환 입력으로 staged.
  파라미터 추적 `c2.2/sim/assets/PARAM_TRACE.md`,
  호퍼 허용박스 `c2.2/configs/hopper_admissibility.json`
  (내부 최소 148×134, 허용 박스 144×130×57.5mm, 여유 2mm ASSUMPTION).
- I2 폐기물 분류: `c2.2/sim/generators/waste_gen.py` + `bonds.py` —
  7 classes (W1 저밀도積層 / W2 고밀도 / W3 purge tower / W4 near-bulk worst-case /
  P0 spaghetti wrap-risk / P1 fused bundle / P2 dense lump) × 8 families,
  seed 결정적, 호퍼 초과 REJECT. 질량 PLA 1.24 (PET 1.38 / TPU 1.21) ASSUMPTION.
  방향성 본드 in-raster / cross-raster / inter-layer-Z + thermal_history_index
  (UNCERTAINTY, 결정질화 아님).
- I3 쿠폰: `c2.2/results/i3_summary.json` + `i3_coupons/` 12종
  (W1/W2/W3/W4 × 0/45/90°, seed 7). 전부 CLEAN_SPLIT, 질량오차 ≤2.9e-14g.
  W1 Z-방향 첫파단 inter_layer_z, W4 z/x 비 0.95 (W1 0.25) near-isotropic.
- I4 스크리닝: `c2.2/results/i4_screen.json` — LHS 300 후보 → 259 survivors
  (S1-A 43/43, S1-B 41/43, S1-C 30/42, S2-A 39/43, S2-B 37/43, S2-C 32/43,
  S2-D 37/43). 7 아키텍처 (S1-A/B/C, S2-A/B/C/D, S2-B baseline 필수).
  S2-A 방향법칙 phi=-theta/q (역회전) 강제. gap 0.4–1.2 / screen 3.0–5.5 후보범위.
- I5 벤치마크: `c2.2/results/i5_benchmark.json` 324 runs
  (ladder 9 S1세트→24 runs, bench 75 S1세트→300 runs, 실패 0) +
  `c2.2/results/s1_fragments/` 84 S1 세트. S1→S2 동일 입력 파이프라인.
  클래스 커버리지 W1 72 / W4 72 / W2·W3·P2 각 60. 질량오차 0.
  목표수율 2.5–5mm는 전 조합 0.000 (이 해상도에서 S1 조각 deq ≫ 4mm 스크린 —
  I6 이전의 알려진 한계, 숨기지 않음). sliver ~0.74–0.79.
- I6 서로게이트·파레토·강건성: `c2.2/results/i6_surrogate.json`,
  `c2.2/results/pareto_candidates.json` (front 11) —
  해석적 응답면 + 8-멤버 앙상블 (적합된 ML 아님), seed grouped split
  train {7,11,23} / val {37} / test {51} (leakage 없음),
  BO 64회 (gap×screen×arch). 테스트 MAE/R2:
  yield 0.02415/0.0, energy 0.415/−0.549, torque 0.00287/−0.310,
  sliver 0.370/0.035, jam 0.02/0.0 — R2가 낮거나 음수인 것은
  서로게이트가 I5 데이터의 분산을 설명하지 못한다는 정직한 기록이며,
  파레토·강건성은 실측 i5 경로 재실행에 근거한다 (서로게이트 예측만으로
  순위를 주장하지 않음). 강건성 81 샘플 × 5 finalists
  (threshold ×0.85/1.0/1.15, screen 3.75/4.0/4.25, eff ×0.9/1.0/1.1,
  orientation x/y/z — 실제 s1_event+s2_event 경로).
  Picks: best_nominal S1-B+S2-B/W4, robust 동일, low_energy S1-C+S2-B/W1,
  purge S1-B+S2-B/P2, typical_fdm S1-C+S2-B/W1.
  sub-mm gap은 SIMULATION RANGE ONLY — 가공 가능성 주장 안 함.

## 게이트 테이블

`c2.2/results/validation_summary.json` 참조 (I0–I6 전부 PASS — 디지털
게이트 의미이며 물리 적합성 선언이 아님). 회귀: c2.2 65/65, c2.1 11/11.
아키텍처별 평균 `c2.2/results/architecture_comparison.json`,
미해결 항목 `c2.2/results/open_actions.json`,
전체 파일·해시 `c2.2/results/run_manifest.json` (142 files).

## HOLD / 미해결 (승인 없이 진행 금지)

- SimulationApp headless smoke PASSED (fast workstream, director 직접 검증: i0_smoke.json 60 steps, z_drop 1.7336, clean_shutdown true).
- Blast/pxr 부재 — USD·동역학 교체는 블록됨.
- S1→S2 chute / S1 discharge / S2 exit 덕트 형상 MISSING.
- 물리 파쇄 시험 0건 — 보정 DEM·토크·수율·잼·에너지 데이터 없음.
- 모터 미선정 (200W 최저가 110,200원이 soft limit 100,000원 초과),
  BOM 124/135 원가 미상, 베어링/가드/스크린/센서/열통합 HOLD,
  7단계 물리 시험 DID_NOT_RUN.
- 구매·외주·가공·통전·구동·펌웨어 flash·main 병합 금지.
