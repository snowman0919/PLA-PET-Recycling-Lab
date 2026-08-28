# OpenModelica 기계 검증 결과

- revision: `solid-manifold-openmodelica-v0.4`
- 판정: **PASS**
- 상태: `PHYSICAL_NOT_RUN` — 이 결과는 물리 성능이나 안전 인증을 대체하지 않는다.
- 시나리오: 18개 + sensitivity sweep 6개, solver `dassl`, tolerance `1e-06`

## 하중 envelope

- cutter 전달토크: 22.00 N·m
- phase gear 토크: 11.08 N·m
- bearing 합성하중: 1255 N
- chain 장력: 603 N
- table anchor 최대 인장: 495 N / 1200 N

## 시나리오 판정

|시나리오|판정|핵심 결과|
|---|---:|---|
|NoLoadStartStop|PASS|T=3.48 N·m, phase=0.0038 rad|
|PLANominal|PASS|T=10.18 N·m, phase=0.0052 rad|
|PETNominal|PASS|T=11.88 N·m, phase=0.0056 rad|
|SingleToothImpact|PASS|T=16.68 N·m, phase=0.0061 rad|
|MultiToothEngagement|PASS|T=16.68 N·m, phase=0.0067 rad|
|OneShaftJam|PASS|T=16.68 N·m, phase=0.0067 rad|
|MotorStall|PASS|T=16.68 N·m, phase=0.0068 rad|
|JamReverseRetry|PASS|T=16.68 N·m, phase=0.0067 rad|
|EmergencyStop|PASS|T=10.18 N·m, phase=0.0052 rad|
|InputFuseOperation|PASS|T=22.00 N·m, phase=0.0081 rad|
|ChainBacklashImpact|PASS|T=16.68 N·m, phase=0.0061 rad|
|ScrewPressureRamp|PASS|screw=7.87 N·m|
|ScrewJam|PASS|screw=29.47 N·m|
|EmptySpool|PASS|line=1.10 N|
|HalfSpool|PASS|line=1.10 N|
|FullSpool|PASS|line=1.10 N|
|GaugeDropout|PASS|line=1.10 N|
|FullMechanicalNominal|PASS||

## 해석 경계

Cutter load는 Gate-1 실측 전 surrogate이다. 14/18/22/34/48 N·m는 모두 cutter-shaft equivalent다. 물리 DRV-F01은 motor-side에 두며 22 N·m cutter-equivalent가 되도록 선택 ratio와 효율로 환산한다. Cutter-side DRV-02는 sacrificial element가 아니다. 이 보호 순서는 디지털 모델에서만 검증했다. M8 table anchor 체결은 운전 전 필수이며, 실제 토크·충격·입도·jam은 Gate-1에서 검증한다.
