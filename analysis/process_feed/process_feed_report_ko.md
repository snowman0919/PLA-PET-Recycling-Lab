# P0-H 공정 공급 virtual closure 보고서

## 판정

`PROCESS_FEED_VIRTUAL_VALIDATION = PASS`이다. 이 판정은 결정적 reduced-order surrogate와 FreeCAD nominal geometry에 한정되며 실제 flake, donor motor, 전류 센서 또는 질량 유량 시험 결과가 아니다. 물리 검증 상태는 `NOT_RUN`이다.

중력만 사용하지 않고 68° 밀폐 hopper, 14 rpm 정상/20 rpm 해소용 저속 agitator, Ø24 mm × 18 mm pitch positive metering auger, 0–55 g inventory state, auger tach 및 motor-current 상태를 채택했다. 정상 목표는 100 g/h이고 제어 출력은 90–110 g/h로 제한한다.

## 검증 범위와 결과

- 재료 형상: PLA support/spaghetti/thin-wall/dense flake 및 PET flat/folded/long-aspect/low-bulk-density의 8종
- 독립 입력: bulk density, aspect ratio, wall/inter-particle friction, agitator RPM, auger RPM, throat fill, screen discharge variability
- 정적 sweep: 3-level OAT + 32-point balanced corner, 총 392 case
- 시간영역 정상 envelope: 재료당 5개, 총 40 case, 0.25 s step, 120 s
- 평균 공급량 범위: 95.86–100.24 g/h
- 최대 연속 starvation: 1.00 s (기준 ≤2 s)
- 최대 bridge 해소: 2 cycle (기준 ≤3)
- 최대 정상 torque/current: 1.413 N·m / 2.768 A (기준 2.2 N·m / 4.2 A 미만)
- inventory 범위: 19.971–20.146 g (0–55 g 경계 안)
- uncontrolled overfeed: 0 sample
- 열화 case: PET 극한 마찰/형상은 75 g/h derate, tach loss·jam·screen discharge loss는 bounded controlled pause

`feed_validation.json`, `nominal_dynamic_summary.csv`, `nominal_state_trace.csv`, `parameter_sweep.csv`가 판정과 상태 증적이다.

## 모델 가정과 남은 실물 검증

모델은 DEM 자체가 아니라 결정 가능한 particle/rigid-body surrogate이다. 체적 효율 0.18, bridge index, torque-current 선형 관계는 설계 가정이다. 따라서 100 g/h 실물 능력을 확정하지 않는다. 8개 재료 coupon으로 mass/rev, bridge 해소 cycle, tach/current threshold, gasket 누설을 계측해 보정해야 한다. 실제 cutter/screw/heater는 lockout과 사용자 확인 전 작동하지 않는다.

PF-04/PF-05의 2.2 N·m feeder attachment는 기존 Fusion LC01–LC10에 없으므로 `LC11_FEEDER_ATTACHMENT = PENDING_EXTERNAL_FUSION_EXECUTION`으로 분류했다.
