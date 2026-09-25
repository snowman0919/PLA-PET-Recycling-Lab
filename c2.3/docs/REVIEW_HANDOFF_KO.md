# C2.3-A 리뷰 핸드오프 (REVIEW HANDOFF)

> 실행자(Muse Spark 1.3 / OMP Vibe)는 판정 권한이 없음.
> 최종값은 IMPLEMENTED / BLOCKED / FAILEDのみ. 아래 수치는 보고이며,
> 수렴·합격 여부의 판단은 리뷰어의 몫임.

## 구현 내용

- A1: CONTRACT.md + STATE.json + NEXT.md + configs/baseline.json +
  cases.json + results/baseline_manifest.json(config_hashes) +
  tests/test_contract.py(17).
- A2: sim/run_case.py(단일 케이스 Isaac 헤드리스 러너, 동결 해시 게이트,
  케이스당·dt당 run dir 8파일) + analysis/aggregate.py +
  analysis/energy_ledger.py + analysis/convergence.py(임계값 파싱,
  하드코딩 없음) + tests/test_telemetry.py(19).
- A3: 12런(dt 4 × 케이스 3) + aggregate_summary.json +
  convergence_summary.json + energy_summary.json + run_hashes 12건 추가.
- A4: verify/verify_contract.py(아티팩트 전용 읽기 검증) +
  results/validation_summary.json + results/run_manifest.json(113파일) +
  tests/test_verify.py + 본 문서.

## 실제 실행 내용

- 백엔드 ISAAC_PHYSX(Isaac Sim 6.1.0.0, `$HOME/env_isaacsim-c22`,
  RTX 3080 10GB cc8.6, driver 595.84), physics device cpu,
  `SimulationManager.set_physics_dt(dt)` 호출 1회/런, steps 240 고정.
- 케이스: FDM(W1/PLA/seed 7), PURGE(W4/PLA/seed 11),
  WRAP(P0/seed 7, S1-only, S2 파쇄 주장 없음).
- 12/12 RUN_OK, 초기상태 해시 케이스 내 dt 4종 동일(FDM e5de1248…,
  PURGE 5cc33218…, WRAP d1307698…), dt 간 파라미터 튜닝 없음.
- 검증기: exit 0, `EVIDENCE_CONSISTENT_CONVERGENCE_false`
  (exit 0은 일관성이지 수렴이 아님).

## 수렴한 항목

- 질량: 12런 전부 rel_error 0.0 <= 1e-6 (goal §13 상한 충족).
- jam/wrap 동일성: 주 쌍(0.0025/0.00125) 3케이스 전부 identical
  (전부 False; WRAP 포함).

## 수렴하지 않은 항목 (주 쌍 0.0025/0.00125, tol work 0.05 /
impulse 0.05 / residence 0.10 / fragment 0.10)

- FDM: converged=false. work eps 0.510435, impulse 0.510435,
  residence 0.506276, fragment 0.720930(breaks 43→12).
  work 0.08479705→0.04151369 J, impulse 0.50609511→0.24776656 Ns.
- PURGE: converged=false. work eps 0.404656, impulse 0.404656,
  residence 0.480435, fragment 0.891304(breaks 46→5).
  work 0.08868090→0.05279567 J, impulse 0.52927512→0.31510094 Ns.
- WRAP: converged=false. work eps 0.530224, impulse 0.530224,
  residence 0.497881, fragment 0.25(breaks 16→12).
  work 0.03147391→0.01478568 J, impulse 0.18784605→0.08824555 Ns.

## 미해결 사항

- duration-vs-resolution confound + CONTRACT §5 한계: steps 240 고정
  탓에 물리 시간이 dt별로 2.4/1.2/0.6/0.3 s로 다름. 인접-dt epsilon은
  해상도와 지속시간을 함께 섞음. CONTRACT §5가 동일 steps를 명시하므로
  계약대로 실행했고, 이는 CONTRACT 설계 한계로 리뷰어 판단에 맡김
  (계약 미수정 — goal §6: 오류 시 STOP + 문서화).
- WRAP wrap 플래그: 12런 전부 False. S1 러너에 strand 메트릭이
  미배선(wrap_metric 0.0 고정)된 한계이며, 감김 없음의 판정이 아님.
- 토크: CONTACT_DERIVED_MOMENT_ARM 추정치
  (tau=CUTTER_R_M×Σ|F_contact|, W=Σtau·ω·dt). 샤프트가 키네마틱
  pose 구동이라 측정 토크는 UNAVAILABLE. C2.2b torque_impulse 누적과
  동일 근거이나 보정된 토크가 아님.
- summary isaac_version "6.1.0.0 (unqueried)": isaacsim 패키지가
  `__version__`을 노출하지 않아 조회 불가. 실행 바이너리는 동결 venv.
- 에너지: 전 런 PARTIAL ledger, closure_claim false. bond/dissipation
  UNAVAILABLE. residual/work_in이 미세 dt에서 증가(FDM 4.63→8.89,
  PURGE 11.97→32.48, WRAP 7.41→21.91). 클로저 주장 없음.

## 실행자가 결론내릴 수 없는 항목

- 주 쌍 수렴 여부(3케이스 전부 converged=false 보고 — 판정은 리뷰어).
- duration confound 하의 수치 해석(해상도 효과 vs 지속시간 효과 분리).
- WRAP 감김 위험, 에너지 잔차의 물리적 의미, 후속 단계(B/C/D) 착수 여부.

## 임계값·베이스라인 무수정 선언

- CONTRACT.md 임계값, baseline.json 동결값, C2/C2.1/c2.2 파일 무수정.
- A3 런 아티팩트 무수정(검증은 읽기 전용). 임계값·베이스라인 변경은
  리뷰어 승인 없이는 불가.

REVIEWER DECISION REQUIRED.
