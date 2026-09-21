# C2.3-A-R1 수렴 재실행 핸드오프 (판정 요청)

> 실행자: Muse Spark 1.3 / OMP Vibe (Goal mode). 판정 권한 없음.
> 최종값 IMPLEMENTED / BLOCKED / FAILED만. 본 문서는 판정 선언을
> 포함하지 않으며, 리뷰어의 검토를 위한 증거 보고다.

## 1. 구현

- 등시간 러너 `c2.3/revisions/r1/convergence/run_r1.py`:
  CONTRACT_R1 §5 준수 (dt ladder [0.01, 0.005, 0.0025, 0.00125],
  substeps 240/480/960/1920, 공통 측정 물리시간 2.4 s, 엔진 관측 시간).
- 워밍업: 물리 0.3 s를 모든 dt에서 동일하게 제외, t0 상태 포함.
- 진단 픽스처 DIAGNOSTIC_FIXTURE: kinematic S1-A 쌍축(40 rpm 역회전) +
  waste 클러스터 강체 프래그먼트 + PhysicsFixedJoint 본드 (R0 D3의
  기계적 결합 경로). literal 생산 CAD 아님 — 명시.
- 집계 `aggregate_r1.py`: 임계값은 CONTRACT_R1 §8에서 파싱 (하드코딩
  없음). 관측가능성 매트릭스 적용.
- 아티팩트 매니페스트 `artifact_manifest.json` (112 파일 sha256).

## 2. 실행

- 12/12 RUN_OK (FDM/PURGE/WRAP × 4 dt), backend ISAAC_PHYSX,
  Isaac 6.1.0.0 (build 6.1.0-rc.26), venv $HOME/env_isaacsim-c22.
- 관측 물리시간: 전 런 2.4 s (허용 1e-6 s 내, dt 0.0025는
  2.4000000000000004로 float32 양자화 범위 내).
- 씬 export + sha256 런별 기록 (R6). 참조 CAD 해시와 분리.

## 3. 수렴 (주 쌍 0.0025 vs 0.00125)

- break_count: 3 케이스 전부 epsilon 0.0 (11 = 11), 임계값 10% 내.
- connected_components_final: 3 케이스 전부 epsilon 0.0, 내.
- mass bookkeeping: 전 런 상대오차 0.0 <= 1e-6 (버킷 분리, 강제 0 없음).
- work_boundary: NOT_EVALUABLE — 접촉→샤프트 분류가 이 빌드의 raw
  contact 기록(int 핸들)에서 불가, boundary work 미산출.
- impulse: NOT_EVALUABLE — 런타임 ContactSensor 프레임이 케이던스 게이트:
  dt 0.00125에서 1920스텝 중 12 이벤트만 캡처 (0.0025는 960 중 247).
  크기 합은 케이던스 의존이며 물리적 임펄스 적분이 아님.
- residence / wrap / screen_passage / jam: 전부 NOT_EVALUABLE
  (RIGHT_CENSORED / NOT_IMPLEMENTED / NOT_APPLICABLE / NOT_OBSERVABLE).

## 4. 수렴하지 않은 항목 (정직 기록)

- v1 실행에서 break count가 dt별 6/12/24/48로 달랐다. 원인: 스케줄이
  스텝 인덱스(i % 40) 기반이어서 파단 수가 dt의 함수였다 — 스케줄링
  아티팩트. 목표 §23에 따라 물리 시간 기반 스케줄(0.2 s 간격, 전 런
  동일)로 전역 수정하고 전 사다리를 재실행했다 (버전 v2 기록).
- v2에서 impulse 지표가 위 케이던스 결핍으로 비교 불가 판정.

## 5. overall_numerically_converged = True의 의미

- 평가 가능한 지표(break_count, connected_components, mass
  bookkeeping)만으로의 수렴이다. work/impulse/residence가
  NOT_EVALUABLE이므로 이는 부분 수렴이다. 리뷰어는 이 범위 제한을
  감안해 판정해야 한다.

## 6. 미해결 (리뷰어 승인 필요)

1. per-physics-step 임펄스 적분 경로 (센서 케이던스 비의존) — impulse
   지표 재평가에 필요.
2. 접촉→샤프트 분류 (body handle → prim 경로) — signed 토크 및
   boundary work 산출에 필요.
3. 실제 스크린/퇴출구가 있는 픽스처에서 residence/.screen_passage 측정.
4. 12-run 전체 폐기물 사다리는 여전히 미실행 (별도 승인 필요).

## 7. 실행자 결론 불가

- 부분 수렴의 수용 여부, impulse 경로 재설계 승인, 다음 단계(B/C/D)
  진입 여부.

REVIEWER DECISION REQUIRED.
