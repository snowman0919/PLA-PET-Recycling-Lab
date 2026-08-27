# Stage 1 shredder 초기 proof design

- 상태: 해석 기반 후보, 물리 시험 미검증
- 목적: PLA printed shell과 세척·건조된 500 mL PET 병을 15~30 mm 조각으로 전처리
- 목표 안정 처리량: 200 g/h 이상

## 설계점

| 항목 | 초기값 | 근거/제한 |
|---|---:|---|
| 형식 | 저속 dual shaft, 비대칭 hook | capture → buckle/tension → fracture 유도 |
| cutter OD / root OD | 60 / 38 mm | 50 mm 축간거리에서 tip-root nominal 1 mm envelope |
| 축간거리 | 50 mm | tip overlap 10 mm; 정확한 phase/collision은 CAD 검사 필요 |
| cutter 두께 | 6 mm | 저가 plate stock 후보; 최종 axial clearance는 shim 시험 |
| hook 수 | 8/disc 후보 | tip pitch 약 23.6 mm로 15~30 mm 목표와 부합 |
| active width | 60~72 mm | 200 mm 폭을 동시에 전단하지 않고 throat에서 접힘·순차 포획 |
| bearing span | 80 mm 목표 | active stack와 seal을 좁게 유지; reducer overhang load는 별도 계산 |
| shaft | 17 mm keyed steel 후보 | 6203 계열 표준 bore 후보; 재질·key는 확정 전 |
| output speed | 15~30 rpm 탐색 | throughput보다 안전한 capture와 peak torque 우선 |
| continuous torque target | 15~25 N·m | feed-limited normal envelope; coupon에서 갱신 |
| overload trip target | 약 40~50 N·m | reverse 전에 current/speed 기반 차단, 실제 drive에 맞춰 낮출 수 있음 |
| structural proof load | 60 N·m | 50 N·m trip보다 높은 단기 해석점, 반복 fatigue 허용값 아님 |

## torque 시나리오

첫 screening은 다음 보수적 full-shear 식을 사용한다.

\[
F = \tau_s b t n_p n_e, \qquad T = F r K
\]

여기서 `b`는 한 tooth의 유효 접촉폭, `t`는 국부 유효 두께, `n_p`는 shear plane, `n_e`는 동시 engagement, `K`는 불확실성 계수다. 실제 PET는 먼저 좌굴·notch tear가 일어나 full shear보다 낮을 수 있고, PLA 출력물은 layer와 infill 때문에 solid block과 다르다. 따라서 이 식은 motor 확정값이 아니라 test envelope를 정하는 용도다.

`stage1_proof_design.py`의 현재 결과:

| 시나리오 | 계산 torque |
|---|---:|
| PET 0.35 mm 단일 국부 tear | 6.3 N·m |
| PET 0.7 mm 국부 접힘, 2 tooth engagement | 36.8 N·m |
| PLA 2.0 mm printed shell | 27.0 N·m |
| PLA 3.0 mm thick shell overload | 54.0 N·m |

두 번째와 네 번째는 정상 연속 운전이 아니라 feed limit/overload/reverse 판단을 보호한다. bottle neck과 solid PLA block은 이 계산으로 처리 보장하지 않는다.

## shaft screening

output torque 60 N·m, 유효반경 25 mm, bearing span 80 mm, simply-supported 중앙 집중하중, steel `E=200 GPa`, 보수적 yield `305 MPa`로 계산했다. keyed section 응력집중과 fatigue는 아직 포함하지 않았으므로 추가 margin이 필요하다.

| shaft d | von Mises | 정적 SF | 중앙 처짐 |
|---:|---:|---:|---:|
| 12 mm | 417.0 MPa | 0.73 | 0.126 mm |
| 15 mm | 213.5 MPa | 1.43 | 0.052 mm |
| 17 mm | 146.7 MPa | 2.08 | 0.031 mm |
| 20 mm | 90.1 MPa | 3.39 | 0.016 mm |

현재 baseline은 17 mm이나, gear overhang과 keyway를 포함한 해석에서 SF 2 미만이거나 처짐이 최종 radial clearance의 1/3을 넘으면 20 mm 또는 span 축소로 변경한다.

## drive 비교

| 후보 | 판단 | 채택 조건 |
|---|---|---|
| donor NEMA17 + 고감속 | Stage 1 기본안으로 부적합 가능성이 큼 | 실제 speed-torque curve에서 15~30 rpm, 15 N·m 이상 연속과 40 N·m trip을 열 한도 내 달성 |
| 복수 NEMA17 | 복잡도 대비 torque 증가가 제한됨 | 이미 보유한 동일 motor/driver를 동기화하고 combined bench test 통과 |
| 24 V DC worm/gearmotor | 우선 비교 후보 | output 15~30 rpm, rated continuous 15~25 N·m, bounded 40~50 N·m overload, reverse duty와 shaft load 명시 |
| geared motor + chain final stage | 추천 가능한 조정 수단 | guard 포함, 3:1~6:1 final reduction, sprocket/shaft/key와 bearing overhang 검증 |
| printed cycloidal reducer | proof rig 후보 | metal pins/bearings/output plate, torque fixture에서 60 N·m proof와 thermal endurance 통과 |

단순 reduction ratio만 크게 하면 stepper가 고속 저토크 영역으로 가므로 해결되지 않는다. 실제 motor torque-speed curve와 효율을 사용해

\[
G \ge \frac{T_{out}}{\eta T_{motor}},\quad n_{motor}=G n_{out}
\]

두 조건을 동시에 만족해야 한다.

## 다음 Gate

1. donor motor label, shaft, phase resistance, driver IC 확인
2. torque-limited manual coupon rig로 PET body, PET folded seam, PLA 1.2/2.0/3.0 mm shell 측정
3. 17 mm shaft + 60 mm cutter CAD collision/phase sweep
4. gearmotor 구매 후보는 price/label/datasheet 검증 후 사용자 승인
5. CNC cutter 전에 low-cost replaceable tooth coupon으로 geometry 검증
