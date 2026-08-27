# 가정과 미확정값

가정은 설계를 진행하기 위한 임시값이며 donor 실측이나 물리 시험이 들어오면 변경한다.

| ID | 현재 가정 | 영향 | 해제 증거 | 상태 |
|---|---|---|---|---|
| ASM-001 | 입력 PET는 cap, neck ring, label, adhesive, 잔류물 없이 세척·건조됨 | 오염·분류·압출 품질 | 사용자 준비 절차 확인 | Open |
| ASM-002 | PLA는 순수 비보강 재질이며 금속 insert/나사가 제거됨 | cutter 파손과 재질 혼입 | 샘플 검사 | Open |
| ASM-003 | 보유 24 V PSU는 label상 600 W지만 실제 정격·단자·보호기능은 미확정 | 전체 power budget | 전면/후면 label 사진과 무부하 전압 | Open |
| ASM-004 | donor NEMA17과 driver는 재사용 후보일 뿐 torque solution으로 확정하지 않음 | shredder/extruder reducer | motor/driver label, phase resistance, bench test | Open |
| ASM-005 | Stage 1 proof geometry는 60 mm급 cutter와 저속 dual shaft에서 시작 | torque, plate, shaft, hopper | coupon 파쇄와 jam torque log | Provisional |
| ASM-006 | Stage 1 정상 output speed 탐색범위는 15~30 rpm | capture와 처리량 | 고속영상/질량 처리량 시험 | Provisional |
| ASM-007 | Stage 1 설계 jam torque는 정상 연속 torque보다 최소 2배 크게 둠 | reducer/shaft/overload setting | instrumented jam test | Provisional |
| ASM-008 | barrel/screw 직경은 12~18 mm trade study 전 미확정 | CNC 비용, torque, flow | calculation sweep와 quote | Open |
| ASM-009 | 기본 spool은 단일 치수를 표준으로 단정하지 않고 adapter를 사용 | holder 호환성 | 상용 spool 표본 측정 | Locked approach |
| ASM-010 | 물리 배치는 수직 적층을 우선하되 무게중심·정비성 실패 시 계단식으로 변경 | frame size와 진동 | full assembly analysis | Provisional |
| ASM-011 | 분류기는 실제 dataset 전 rule/fusion scaffold만 제공 | 정확도와 reject rate | 교정 dataset과 confusion matrix | Open |
| ASM-012 | 가격이 없는 BOM 행은 구매 가격 0이 아니라 `TBD estimate`로 취급 | budget feasibility | vendor quote/date | Open |

## 변경 규칙

가정이 해제되면 관련 요구사항, ADR, 계산, CAD parameter, BOM과 검증 계획을 함께 갱신한다. 안전에 영향을 주는 가정은 물리 시험 전 임의로 `Confirmed`로 바꾸지 않는다.
