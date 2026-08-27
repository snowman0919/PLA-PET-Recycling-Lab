# Stage 1 reducer interface envelope

- 상태: proof baseline interface, donor motor/dyno 미확정
- 출력축 속도: 15~30 rpm
- 정상 연속 torque 목표: 15~25 N·m
- 제어 trip 후보: 40~50 N·m
- 단기 구조 proof 해석점: 60 N·m

## 기계 interface

입력은 shaft A의 20 mm keyed 축 연장부에 coaxial flexible coupling으로 연결하는 구성을 우선한다. coupling CAD는 현재 `OD 30 × 25 mm` keep-out envelope이며 실제 bore, key, clamp와 제조사 허용 misalignment는 선택 부품에 맞춰 갱신한다. reducer housing은 shredder plate에 직접 매달지 않고 4040 계열 frame crossmember에 독립 지지한다.

두 cutter shaft의 동기화 기어는 nominal pitch-envelope `Ø49 × 10 mm`, 중심거리 50 mm다. 실제 module, tooth count, pressure angle, backlash, material과 guard는 미정이다. Engineering Recommended 구성은 main right bearing과 제3 support bearing 사이에 기어를 둔다. chain/sprocket처럼 추가 radial load를 만드는 전달 방식은 별도 shaft/bearing 계산 없이 대체할 수 없다.

## 변형 비교

| 항목 | Target Budget | Engineering Recommended |
|---|---|---|
| timing 지지 | 제3 plate/bearing 생략 가능 후보 | 제3 plate + 6004 두 개 포함 |
| 허용 조건 | 실제 coupon torque, 50 N·m 이하 trip, overhung shaft 검증 | 60 N·m proof baseline 유지 |
| reducer 연결 | coaxial coupling 우선 | coaxial coupling 우선 |
| chain/sprocket | 별도 overhung load 검증 필수 | 별도 support 없이 불허 |

## donor 검증 Gate

1. motor/reducer label, 정격 전압·전류·출력 rpm·duty를 기록한다.
2. 실제 15/20/30 rpm에서 torque-speed와 winding/housing 온도를 측정한다.
3. 15~25 N·m 연속 구간과 40~50 N·m current/speed trip의 반복성을 확인한다.
4. 정회전-정지-역회전 jam cycle에서 coupling, key, gear timing과 frame 변위를 점검한다.
5. 결과 전까지 특정 donor나 감속비가 요구 성능을 달성한다고 주장하지 않는다.
