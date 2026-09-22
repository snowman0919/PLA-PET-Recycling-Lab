# C2.3-A-R3 리뷰 핸드오프 (판정 요청)

> 실행자: Muse Spark 1.3 / OMP Vibe (Goal mode). 판정 권한 없음.
> 최종값 IMPLEMENTED / BLOCKED / FAILED만.

## 1. R3 결과 요약

- **T1 (contact-only): 5% GATE_MET (수치 기록, 단계 승인 아님)** — 지속 접촉 픽스처에서 contact
  integrator 수렴 확립. 주 쌍 (0.0025 vs 0.00125)에서
  tau epsilon 1.85% / W epsilon 1.85% (기준 5% 이내).
- **T2 (nonbreaking bonded): BLOCKED** — 지속 접촉 + joint 병렬
  구성이 이 PhysX 빌드에서 3가지 변형 모두 실패 (아래 상세).
- **T3 (load-driven break): BLOCKED** — T2 위에 구축되므로 T2와
  함께 보류.

## 2. T1 상세 (5% GATE_MET)

픽스처: rigid specimen (0.08 box, 0.02 kg)을 회전 kinematic
샤프트(40 rpm, Y축) crown에 2mm 접촉 깊이로 전체 위치 pin. Pin은
문서화된 진단 제약 (이상적 슬라이더와 동등). 4dt 전부 RUN_OK,
관측 2.4 s, 질량오차 0.

| dt | tau (N·m·s) | W (J) |
|---|---|---|
| 0.01 | 0.00365302 | 0.01530174 |
| 0.005 | 0.00264899 | 0.01109606 |
| 0.0025 | 0.00280889 | 0.01176584 |
| 0.00125 | 0.00275683 | 0.01154779 |

주 쌍 epsilon: tau 0.0185, W 0.0185 — 모두 5% 이내. 시드/형상/
마찰/측정 구간/임계값 무변경.

## 3. T2 BLOCKED 상세 (픽스처 반복 이력)

리뷰어 승인 fixture 변경 안에서 3가지 변형을 구현·실행:

1. **v1 (x-offset pin + joints)**: 외곽 specimen이 crown 밖에
   배치되어 impulse stream 오염. eps 53% FAIL.
2. **v2 (Y축 0.08박스 배치)**: 0.12m 샤프트에 0.08박스 3개가
   들어가지 않아 외곽 박스 반쯤 off-crown. eps 60% FAIL.
3. **v5 (no pin, gravity + preload)**: 샤프트 마찰이 warmup 0.3s
   안에 체인을 튕겨 냄 (r3p28: 최종 위치 x=-0.68, z=0.024 —
   바닥에 떨어짐). 측정 윈도 접촉 0건.
4. **v9/v10 (guide walls)**: 벽 z-위치 버그 수정 후에도 체인이
   볼록한 crown에서 굴러 이탈 (free box chain은 구조적으로
   불안정).
5. **v11 (plate specimen)**: crown을 가로지르는 판형 — 여전히
   이탈.
6. **prismatic slider (r3p30)**: joint frame snap이 초기 2mm
   겹침을 해소하여 접촉 상실 (2행만 기록).
7. **v12/v13 (full pin + 0.04박스 Y배치 + joints)**: 접촉은
   유지되나 (713→5169 rows) pin-vs-joint 충돌이 dt-스케일 impulse를
   주입 — impulse/W가 dt에 정비례 증가 (eps 84% FAIL).

결론: 이 PhysX 빌드(6.1.0-rc.26)에서 지속 접촉 + joint 병렬
안정화는 추가 픽스처 엔지니어링 (예: 실제 관절 토크 판독 또는
PhysX joint break API 사용)이 필요. 현재 도구로는 T2 수렴 판정
불가.

## 4. 리뷰어 지시 반영 상태

- fixture 변경 승인: 사용함 (T1 픽스처 확립).
- R·sum|F| 금지: 준수 (전 경로 typed impulse).
- 0.2초 예약 파단 금지: 준수 (T3 코드는 load-driven이나 T2 BLOCKED로
  미실행).
- energy ledger ke_t1→ke_r1 버그: R2에서 수정됨 (R3 코드에 반영).
- T1 먼저, 실패 시 중단 원칙: T1은 5% 게이트 충족 — 그러나 T2가 BLOCKED이므로
  T3로 진입하지 않음.

## 5. 미해결 (리뷰어 승인 필요)

1. T2/T3 지속 접촉 + joint 병렬 안정화 방법 (옵션: (a) joint local
   frame 명시적 설정, (b) PhysX joint break API 사용, (c) D6 joint
   limiter 기반 파단).
2. 12-run 전체 폐기물 사다리는 계속 미실행.

## 6. 실행자 결론 불가

- T1 수렴의 수용, T2/T3 BLOCKED의 처리 방향, B 진입 여부.

REVIEWER DECISION REQUIRED.
