# REVIEW HANDOFF — C2.3-R1 진단 결과 (판정 요청)

> 범위: Goal R0 §4 D0–D4 + §5 scene/asset evidence + §6 handoff. R0는
> 진단 단계이며 수렴 판정이 아님. 실행자(Muse Spark 1.3 / OMP Vibe)는
> 판정 권한이 없고, 최종값은 IMPLEMENTED / BLOCKED / FAILED만 보고함.
> 임계값(R1 동결: work 5%, impulse 5%, residence 10%, discrete 10%,
> mass 1e-6)은 valid + observable + comparable 수량에만 적용되며,
> R0에서 임계값 변경은 없음. 백엔드 ISAAC_PHYSX, Isaac Sim 6.1.0.0.

## 1. 구현 (작성 파일 — 커밋 없음)

- 규범 초안: `c2.3/revisions/r1/CONTRACT_R1.md`, 근거표
  `c2.3/revisions/r1/REQUIREMENTS_EVIDENCE.md`, 변경이력
  `c2.3/revisions/r1/AMENDMENT_LOG.md` (R0.1, 리뷰어 승인 대기).
- 진단 스크립트: `c2.3/revisions/r1/diag/d0_clock.py`, `d1_contact.py`,
  `d2_torque.py`, `d3_bond.py`, `d4_accounting.py` + 분석 테스트
  `test_r02_units.py` (16개), `test_r03_causality.py` (22개).
- 실행 근거: `c2.3/revisions/r1/runs/` — D0 4런, D1 8런, D2 4런, D3 3런,
  D4 1런, 전부 scene.usda + scene.sha256 + 원시 계열 + summary.json +
  실제 stdout/stderr 포함. 집계: `d0_clock.json`, `d1_contact.json`,
  `d2_torque.json`, `d3_bond.json`, `d4_accounting.json`.
- 결과 요약: `c2.3/revisions/r1/DIAGNOSTIC_SUMMARY.md`.
- 무결성: `c2.3/revisions/r1/run_manifest.json` (r1 이하 전 파일 sha256).
- CI: `.github/workflows/c2.3-contract.yml` (CPU 분석 스위트만; GPU/Isaac
  실행은 CI에 없음).

## 2. 실행 (진단별 결과 — 수치)

- D0 시계 + 2.4 s 구간: 4/4 IMPLEMENTED. 관측 duration 2.4 s 전부,
  substep 240/480/960/1920 dense, 콜백 dt float32 양자화 내 1e-6 상대 일치.
- D1 접촉 단위 + 격리: 8/8 IMPLEMENTED. 지지 임펄스 상대오차
  2.88e-08 / 1.71e-08 / 5.82e-08 / 6.98e-08 (5% 대비 여유),
  무접촉 0.0 N·s 전 dt.
- D2 토크/일 의미론: 분석 16/16 IMPLEMENTED + 음성대조 4/4 IMPLEMENTED
  (cutter/shaft 일 정확히 0.0 J, 지지 임펄스 ≈ 19.62 N·s 존재).
- D3 2체 결합 인과성: IMPLEMENTED. intact dx 0.0 m / F ≈ 2.0 N / 1 component,
  disconnected dx 2.756 m / F ≈ 0 / 2 components,
  timed-disable step 66 (@0.5 s) 이후 발산 dx 0.918 m. 분리 기준
  (0.05 m, 0.5 N) 초과 달성. 파단 법칙 아님, PLA fitting 없음.
- D4 관측가능성/회계: IMPLEMENTED. nominal rel 0.0 ≤ 1e-6, fault 주입 3/3
  탐지 (소실/중복/질량변경). wrap null/NOT_IMPLEMENTED, passage
  null/NOT_APPLICABLE, residence RIGHT_CENSORED, motor-jam NOT_OBSERVABLE,
  불가 비교 NOT_EVALUABLE.

## 3. 수렴 (해당 없음 — R0는 진단, 수렴 판정 아님)

- R0 진단 단계에서는 수렴 판정을 수행하지 않음. 동결 임계값에 대한
  primary-pair 수렴 판정은 승인된 R1 §5 12-run ladder 재실행 이후에나
  가능하며, A3 legacy equal-steps 근거는 재사용 금지.

## 4. 미수렴 (해당 없음)

- 해당 없음 (사유는 §3과 동일).

## 5. 미해결 (리뷰어 승인 필요 — 실행자가 해소 불가)

1. R1 §5 ladder(동일 측정 2.4 s + typed telemetry + R3/R4/R5 근거 경로)로
   12-run 재실행이 필요함. A3 산출물은 legacy equal-steps 근거로 인용 금지.
2. WRAP strand sensing 경로 없음 (null / NOT_IMPLEMENTED 유지).
3. kinematic-pose rig에서 dynamic-shaft effort readout 없음 (UNAVAILABLE 유지).
4. `isaacsim.__version__` 조회 불가 (UNKNOWN) — pip metadata + VERSION 파일 +
   run별 module path로 대체 기록.
5. 기존 A4 verifier 범위: `baseline_manifest.json`의 A1 해시가 R0.1에서 승인된
   `STATE.json`/`NEXT.md` 진행 업데이트와 불일치 (verifier exit 1, 2건).
   R1 결함이 아니라 verifier 범위 노후화 소견. A3 run 해시·mass/work
   재계산·ladder·금지라벨 검사는 그대로 유효.

## 6. 실행자 결론 불가 항목

- R1 규범 전환 승인 여부 (CONTRACT_R1 → normative).
- R1 §5 12-run ladder 재실행 승인 여부.
- D0–D4 진단 근거의 R1 §6 증거 경로 충분성 판단.
- 미해결 5건(§5)의 해소 우선순위 및 방법 승인.
- C2.3-A/R0 단계 종료 또는 다음 단계 진입 여부.

REVIEWER DECISION REQUIRED.
