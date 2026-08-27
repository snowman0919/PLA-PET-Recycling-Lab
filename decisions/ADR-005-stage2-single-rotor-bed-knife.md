# ADR-005: Stage 2 single rotor + shimmed bed knife

- 상태: Accepted for proof baseline
- 날짜: 2026-08-28

## 결정

Stage 2는 50 mm OD, 3열 rotor와 fixed bed knife를 우선 proof한다. 각 blade 열은 8개의 8 mm axial segment를 총 14° stagger하여 64 mm straight edge의 동시 engagement를 피한다. shaft와 bearing은 Stage 1의 20 mm/6004 계열을 공통화 후보로 사용한다. blade clearance는 nominal 0.2 mm로 모델링하되 출력물 공차에 의존하지 않고 ground shim, dial-indicator runout과 feeler gauge로 설정한다.

구동은 60–120 rpm, 10–18 N·m 연속, 35–45 N·m trip 후보로 분리하고 60 N·m 구조 proof를 사용한다. Stage 1 drive 공유는 두 단계의 속도 차이와 jam reverse를 실제 transmission/dyno로 검증하기 전 채택하지 않는다.

## 제외·미해결

- fused rotor CAD를 최종 제작 rotor로 승인하지 않는다.
- replaceable blade pocket, bolt/dowel, dynamic balance, lower chamber와 grate는 상세 설계 전이다.
- 6–12 mm 출력은 physical sieve distribution을 통과해야 한다.
- PLA/PET 실제 edge wear와 heat treatment를 확인하기 전 CNC/재료 주문을 승인하지 않는다.

## 후속 Gate

- 0.5° rotor sweep에서 bed knife solid collision 없음과 nominal 최소 간극 확인
- shaft/plate/bed-knife carrier 정적 FEA
- blade retention proof와 120 rpm balance test
- guarded low-energy coupon에서 입도·torque spectrum 수집
