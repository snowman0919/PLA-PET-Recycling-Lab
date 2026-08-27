# Stage 2 중간 파쇄기 proof design

- 상태: 해석·CAD 후보, 물리 시험 미검증
- 입력 목표: Stage 1의 15–30 mm 조각
- 출력 목표: 6–12 mm
- 우선 구조: single-shaft rotor + fixed bed knife

## baseline

| 항목 | 값 | 제한 |
|---|---:|---|
| rotor OD / core OD | 50 / 38 mm | fused proof envelope; 실제 blade pocket 미설계 |
| blade | 3열, 축방향 8×8 mm segment, 총 14° stagger | 순차 전단 proof; pocket/fastener 미정 |
| active width | 64 mm | 한 번에 전체 폭을 solid shear하지 않도록 feed 제한 |
| shaft | 20 mm keyed steel 후보 | bearing center span 84.4 mm |
| bearing | 6004-2RS 후보 2개 | Stage 1과 부품 공통화 후보 |
| bed knife | 8×20×64 mm, M6 계열 4-hole proof | bolt class, thread engagement, dowel 미정 |
| blade clearance | nominal 0.2 mm | ground shim과 worst-case runout로 확정 |
| speed | 60–120 rpm | 3–6 blade pass/s |
| continuous torque | 10–18 N·m | coupon에서 갱신 |
| trip torque | 35–45 N·m | current + speed-drop 기반 후보 |
| structural proof | 60 N·m | fatigue 허용값 아님 |

## 전단·축 screening

Stage 1과 같은 full-shear 상한식을 국부 engagement에 적용했다.

| 시나리오 | force | torque |
|---|---:|---:|
| PET 0.7 mm folded wall, 8 mm segment | 392 N | 14.7 N·m |
| PLA 2 mm shell, 8 mm segment | 960 N | 36.0 N·m |
| PLA 두 segment 동시 engagement | 1,920 N | 72.0 N·m |

두 engagement는 정상 연속 조건이 아니라 jam/trip 경계다. CAD bearing 중심에서 유도한 84.4 mm simply-supported span, 20 mm shaft, 60 N·m, 25 mm 반경에서 nominal von Mises는 `92.4 MPa`, `SF/Kt1.6=2.06`, 중앙 처짐은 약 `0.019 mm`다. blade edge, shaft shoulder와 keyway의 상세 FEA는 포함하지 않았다.

## 속도와 동력

3-blade rotor는 60/90/120 rpm에서 3/4.5/6 Hz blade-pass를 만든다. 18 N·m에서 기계 출력은 각각 약 113/170/226 W다. 실제 reducer 효율, acceleration, jam reverse와 열 duty를 포함하지 않으므로 600 W PSU 적합성이나 donor motor 적합성을 이 수치만으로 결론 내리지 않는다.

Stage 1 drive와의 기계적 공유는 순차 운전 + clutch/belt change 또는 검증된 two-speed transmission일 때만 후보로 남긴다. Stage 1은 15–30 rpm, Stage 2는 60–120 rpm이므로 고정 감속비를 단순 공유하면 한쪽 운전점이 어긋난다. 동시 구동은 합산 torque transient와 jam 역회전이 결합되어 baseline에서 제외한다.

초기 straight 64 mm blade는 국부 engagement 계산과 모순되어 폐기했다. 현재 8 mm segment를 2°씩 stagger한 staircase proof는 동시에 물리는 폭을 줄이지만, 실제 material bridging으로 인접 segment가 함께 물릴 수 있으므로 72 N·m 두-segment 경우를 jam 경계로 유지한다.

## 출력 입도 Gate

blade-pass frequency와 nominal clearance만으로 6–12 mm를 보장할 수 없다. PLA/PET 조각의 방향, 재포획과 긴 PET strip이 지배할 수 있다. coupon에서 다음을 측정한다.

1. 입력 15/20/30 mm, PLA shell 1.2/2.0/3.0 mm와 PET body/folded seam
2. 60/90/120 rpm, 제한 feed rate별 torque/current/speed-drop
3. 3, 6, 12, 15 mm sieve를 이용한 질량분율과 긴 strip 최대길이
4. 12 mm 초과율 또는 긴 strip이 높으면 removable grate, recirculation 또는 staggered tooth를 비교
5. dust 증가와 열/edge wear를 함께 기록
