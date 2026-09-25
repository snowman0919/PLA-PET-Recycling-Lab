# C2.2 핸드오프 — 2층 구조: (a) I0–I6 numpy 프록시 + (b) C2.2b headless PhysX 동역학 Gates A–F

상태: `UNCALIBRATED_DIGITAL_SENSITIVITY` 전역. 성능 게이트 `BLOCKED_PERFORMANCE_DATA`.
구매·가공·통전·병합 모두 HOLD. M1 미선정. 예산 soft limit 100,000원.
어떤 수치도 보정된 파쇄 성능·토크·수율 예측이 아니다. 본 문서는 보정 완료 선언 표현을 사용하지 않는다.

이 문서는 두 층으로 구성된다. (a) I0–I6 numpy 프록시 벤치마크 — 순서확인용
UNCALIBRATED ordering smoke로 유지한다 (삭제하지 않음). (b) C2.2b 실제 headless
PhysX 동역학 Gates A–F — `c2.2/results/dyn_*` 증거. 프록시를 동역학으로
재라벨하지 않는다: 모든 PASS 판정은 해당 층의 JSON/로그 아티팩트에 근거한다.
이전 단일층 서술(프록시층 결과만을 근거로 전체를 갈음하던 프레이밍)은 본 2층 구조로 대체한다.

## 리비전

- 작업 디렉토리: `/home/monad/develop/PPR-c2.1-codex-20260921` (clean clone).
  `/home/monad/develop/PPR`은 읽기 전용으로만 참조하고 수정하지 않았다.
- 브랜치 `codex/c2.1-s2-transmission-20260921`, PR #5 OPEN. 브랜치 생성·커밋·푸시 없음.
- C2.1 소스는 읽기 전용. C2.1 패키지 상태
  `DIGITAL_P0_P6_PACKAGE_PASS_PHYSICAL_RELEASE_HOLD`를 그대로 상속한다.

## (a) I0–I6 numpy 프록시층 (유지, UNCALIBRATED ordering smoke)

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
  프록시층 당시 pxr 부재로 USD 쓰기 불가였음 — 아래 (b) Gate A에서 해소.
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

## (b) C2.2b 실제 headless PhysX 동역학 Gates A–F (Isaac 6.1.0.0, `c2.2/results/dyn_*`)

venv `$HOME/env_isaacsim-c22` (python 3.12, isaacsim 6.1.0.0, pxr Usd/UsdGeom/
UsdPhysics 확인; `PhysxSchema`는 SimApp 내부에서만; SimApp import는
`OMNI_KIT_ACCEPT_EULA=YES` 필요). 디스크 98%이므로 신규 설치 없음.

- Gate A (USD): `c2.2/sim/assets/emit_usd.py` → `c2.2/sim/assets/usd/machine.usda`
  + `machine.sidecar.json` (`dyn_usd_manifest/1`, PASS, mm authored,
  metersPerUnit 0.001, F0 identity): Hopper concave 16v/32f, ShaftA concave
  246v/488f, CutterA00 convexHull 42v/80f, S2 Rotor convexHull 248v/492f
  (hull cap 256 = PhysX convex limit), DERIVED transfer box 4종.
  `c2.2/sim/bootstrap/load_machine.py` → `c2.2/results/dyn_usd_load.json`
  PASS (24 prims, 8 meshes, 584 verts, 10 physics steps).
- Gate B (PhysX S1): `c2.2/sim/dynamics/s1_physx.py` — S1-A 쌍축 역회전
  kinematic 샤프트 (r 40 mm, ±30 mm, 40 rpm) + waste_gen BondGraph 기반
  fragment cluster (≤24 rigid box) + fragment별 `IsaacContactSensor` 실측 +
  물리 루프 내부 bond-break (nominal strength × impulse_scale 0.02 N·s,
  ASSUMPTION_UNCALIBRATED — 측정된 파단법칙 아님). JSONL + summary를
  `c2.2/results/dyn_s1/`에 기록. W1/s7 (239 contact steps, 46 breaks,
  torque-impulse 0.0586 N·m·s), W4/s11 (233/46/0.0455), W1/s11, P0/s7 전부
  PASS (exit 0). 질량오차 0.0. `get_net_contact_forces` 단독은 None을
  반환하므로 ContactSensor prim이 필수이며, `use_backend("tensor")` 스코프는
  센서 캐시를 0에 고정시키므로 사용하지 않는다 (코드 주석 기록).
- Gate C (S1→S2): `c2.2/sim/dynamics/transfer.py` →
  `c2.2/results/dyn_transfer.json` PASS. S1_DISCHARGE 120×100×30 @
  (120,243.5,428), CHUTE 110×90×120 @ (200,243.5,350), S2_ENTRY 90×45×25 @
  (308.6,275,330), S2_EXIT 90×45×40 @ (308.6,275,200) — 전부 DERIVED
  파라메트릭 박스이며 C2.1 CAD는 불변 (`c21_mutated: false`). 동일 S1
  end-state를 S2-A와 S2-B에 그대로 전달.
- Gate D (screen): `c2.2/sim/dynamics/s2_screen.py` — `if deq<hole: pass`
  프록시 없음. 스크린 = bar-grid 사이 실개구 (pitch−bar=hole) 강체 충돌로만
  통과/잼 판정 (PhysX 안착 높이 기준). S2-A 정통 pass율 0.42–0.50
  (hole 3.0→5/12, 4.0→5/12, 5.5→6/12), S2-B 0.17–0.29
  (3.0→3/12, 4.0→2/12, 5.5→2/12). Sliver: 45° yaw가 0° 대비 동등 이상 통과
  (4/5 케이스), S2-A 로터 스위프가 S2-B 고정 하우징을 전 구간 상회.
- Gate E (dt 민감도): `c2.2/sim/dynamics/dt_sweep.py` →
  `c2.2/results/dyn_dt_sweep.json` PASS (6/6 exit 0, jam 없음, 질량오차 0).
  W1/s7: dt 0.0025→43 breaks/0.0202, 0.005→46/0.0586, 0.01→46/0.0963.
  W4/s11: 전 dt에서 46 breaks, torque 0.0212→0.0455→0.0948.
  파단 수는 dt-안정, torque-impulse는 dt에 비례 상승한다 (force×dt 적산
  구조의 아티팩트 — 보정 토크가 아님, flagged).
- Gate F (sweep + refit): `c2.2/sim/dynamics/gap_screen_sweep.py` →
  `c2.2/results/dyn_gap_screen_sweep.json` PASS (S1 6 + S2 12, 전부 exit 0).
  **Gap축 한계 (명시): gap축은 shaft-center engagement 59.2/60.0/60.8 mm이며
  리터럴 0.4–1.2 mm 커터 간극이 아니다 — r=40 mm 강체 실린더가 공칭 60 mm
  중심거리에 배치된 본 장면에서는 sub-mm 간극을 표현할 수 없으므로
  (unrepresentable), 0.4–1.2 mm 범위에 대한 주장으로 읽어서는 안 된다.**
  Torque는 engagement 증가에 따라 상승 (W1: 0.0495→0.0586→0.0634).
  `c2.2/sim/dynamics/retrain_surrogate.py` → `c2.2/results/dyn_surrogate.json`
  PASS (`REAL_PHYSX_HEADLESS`, additive — `i6_surrogate.py` 불변,
  `i5_benchmark.py` 프록시 유지).

## 게이트 테이블

`c2.2/results/validation_summary.json` 참조 (I0–I6 PASS 유지 + C2.2b Gates
A–F PASS 추가 — 각 층의 JSON/로그 아티팩트 근거, 물리 적합성 선언 아님).
회귀: c2.2 73/73 (test_dynamics.py 8 포함), c2.1 11/11, c2 (/tmp 사본) 59/59.
아키텍처별 평균 `c2.2/results/architecture_comparison.json`,
미해결 항목 `c2.2/results/open_actions.json`,
전체 파일·해시 `c2.2/results/run_manifest.json`.

## HOLD / 미해결 (승인 없이 진행 금지)

- SimulationApp headless smoke PASSED (fast workstream, director 직접 검증: i0_smoke.json 60 steps, z_drop 1.7336, clean_shutdown true).
- C2.1 CAD의 S1 discharge / S1→S2 chute / S2 exit 덕트 형상은 여전히 MISSING —
  C2.2b는 DERIVED 파라메트릭 박스로만 대체했으며 C2.1을 변경하지 않았다.
- 물리 파쇄 시험 0건 — 보정 DEM·토크·수율·잼·에너지 데이터 없음. C2.2b의
  impulse_scale 0.02 N·s, torque-impulse, pass율은 모두 UNCALIBRATED 실측
  민감도이며 보정값이 아니다.
- 모터 미선정 (200W 최저가 110,200원이 soft limit 100,000원 초과),
  BOM 124/135 원가 미상, 베어링/가드/스크린/센서/열통합 HOLD,
  7단계 물리 시험 DID_NOT_RUN.
- 구매·외주·가공·통전·구동·펌웨어 flash·main 병합 금지.
