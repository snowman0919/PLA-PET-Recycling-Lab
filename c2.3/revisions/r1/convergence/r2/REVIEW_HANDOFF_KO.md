# C2.3-A-R2 리뷰 핸드오프 (판정 요청)

> 실행자: Muse Spark 1.3 / OMP Vibe (Goal mode). 판정 권한 없음.
> 최종값 IMPLEMENTED / BLOCKED / FAILED만. 리뷰어 지시 6개 항목에 대한
> R2 결과 보고.

## 1. 구현 (R2)

- `run_r2.py`: per-physics-step contact stream
  (subscribe_contact_report_events + ContactEventHeaderVector +
  ContactDataVector) — 런타임 ContactSensor 케이던스 게이트 제거.
  접촉 대상 prim에 PhysxContactReportAPI(threshold=0) 적용.
- body identity: PhysicsSchemaTools.intToSdfPath로 actor0/actor1을
  Sdf.Path로 복호화 → ground / fragment / ShaftA / ShaftB 분리.
- signed shaft load: tau = a_hat · ((p − o) × J_impulse), 접촉별
  계산, ShaftA/B 각각 누적, 부호 유지.
- boundary work: dW = J · v_boundary(접촉점, 실제 kinematic 경계
  속도), R·sum|F| 사용 없음.
- physics-driven bond event: 각 inter-fragment joint는 |tau_shaft
  impulse| 누적; 임계값 0.02 N·m·s (UNCALIBRATED synthetic, 러너
  헤더에 선언) 초과 시 joint 비활성 (제약 상태 변화). 예약 파단 없음.
- energy ledger: ke_rot에 회전 KE (R1의 ke_t1 버그 수정). 미관측
  소산은 UNAVAILABLE. 클로저 주장 없음.

## 2. 실행 (v3, 12 런)

- v1: 리뷰어 지적대로 예약 파단 스케줄 → R2에서 완전 제거.
- v2: 누적기가 warmup 접촉까지 포함 (측정 윈도가 아님) → goal §9 위반.
- v3: 누적기를 t0에서 리셋 (측정 윈도 전용 적분). 전 런 RUN_OK,
  관측 2.4 s, substeps 240/480/960/1920, 질량오차 0.0 <= 1e-6.

## 3. 수렴 결과 (주 쌍 0.0025 vs 0.00125)

- break_count: 3 케이스 전부 eps 0.0 (물리 구동, 예약 아님) — 수렴.
- connected_components: 3 케이스 전부 eps 0.0 — 수렴.
- impulse (측정 윈도 |tauA|+|tauB|): FDM/WRAP 0.0 (윈도 내 샤프트
  접촉 없음), PURGE eps 0.9672 — 수렴 판정 불가.
- boundary work: FDM 0.48 / PURGE 0.46 / WRAP 0.19 (tol 0.05) — 미수렴.

## 4. 근본 원인 (goal §24 — 수치 오류와 물리 민감도 구분)

- 증상: 파편이 첫 접촉 후 샤프트에서 튕겨 나감 → 측정 윈도에 지속적인
  샤프트 접촉 과정이 없음. work/impulse 적분은 단발 트랜지언트의
  dt-의존 잔여 접촉만 담음. 계측(관측)은 정상 — 미수렴은 픽스처가
  정상 상태(steady) 파쇄 과정을 만들지 않는 물리 민감도다.
- 임계값/시드/형상/마찰/측정 구간 무변경 (goal §23 준수).

## 5. 계측 인프라 (리뷰어 ACCEPT 항목) 상태

- per-physics-step contact stream: 구현·검증 (측정 윈도 접촉 7,999
  이벤트까지 캡처).
- contact body identity 분류: 구현·검증 (ground/fragment/ShaftA/B).
- signed shaft load: 구현·검증 (부호 유지, warmup에서
  tauA=-0.014/tauB=+0.029 등 역회전 부호 확인).
- boundary work: 구현·검증 (warmup 트랜지언트에서 0.06 J 측정).
- physics-driven bond event: 구현·검증 (v2 스모크에서 11 breaks,
  물리 구동).
- energy ledger ke_rot 버그: 수정·검증.

## 6. 미해결 (리뷰어 승인 필요)

1. 지속 접촉 픽스처 (geometry 변경 — 예: 회전 샤프트가 파편을 지속
   가동하도록 배치) — work/impulse 수렴 판정의 전제 조건.
   goal §7 "형상 변경 금지"와 충돌하므로 리뷰어 승인 필수.
2. UNCALIBRATED bond threshold (0.02 N·m·s)의 물리적 근거 — 현재
   synthetic 선언 상태 유지.
3. 12-run 전체 폐기물 사다리는 계속 미실행.

## 7. 실행자 결론 불가

- 부분 수렴의 수용, 픽스처 변경 승인, B/C/D 진입 여부.

REVIEWER DECISION REQUIRED.
