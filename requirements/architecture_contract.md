# 2‑tower 수치 아키텍처 계약

상태: **ARCHITECTURE CONTRACT / VIRTUAL EVIDENCE / PHYSICAL REVIEW OPEN**

이 문서는 기존 2,295×520×720 mm 직선 proof를 다음 revision의 제작 승인본으로 사용하지 않고, 두 rack의 치수·기능·안전 경계를 고정한다. 원문 최종 합격기준과 최신 최소화 방향이 충돌하는 부분은 최종 기능을 삭제하지 않는 쪽으로 해결했다.

## 범위 결정

- Release 구성은 **3단 파쇄**, PLA/PET/UNKNOWN, 고정 6색+Reject를 유지한다.
- Stage 3 bypass와 material+Reject routing은 coupon/dataset commissioning 비교 모드일 뿐이다. Hardware/BOM을 삭제하거나 최종 요구사항을 닫는 근거로 쓰지 않는다.
- Tower 간 이송은 자동 docking 대신 밀폐 수동 batch bin을 사용한다.

## 고정 envelope

| 항목 | Tower A | Tower B |
|---|---:|---:|
| 역할 | 분류·3단 파쇄·선별·batch | 건조·압출·성형·권취·제어 |
| Rack | 600×600×1350 mm | 900×600×1150 mm |
| 추가 rail | 없음 | die 이후 760 mm |
| 운전 envelope | 600×600×1350 mm | 1660×600×1150 mm |
| 추정 운전 질량 | 57.50 kg | 75.35 kg |
| 추정 수직 CG | 675.4 mm | 480.0 mm |
| 무고정 tip 가속도 | 0.444 g | 0.625 g |
| 계산 anchor pair tension | 222.3 N | 0.0 N |

Tower A는 0.35 g sorter 전달목표와 60 N cutter 반력을 1.5배 한 rigid-body screen에서 중력 복원모멘트를 넘으므로 **4점 anchor가 필수**다. 각 점 1 kN pullout 후보는 실제 substrate, edge distance와 fastener 시험으로 확정한다. Tower B도 공통 설치정책상 4점 고정한다.

## Batch·공정 interface

- Bin: gross 8.0 L, usable 6.0 L, 250 kg/m³에서 1.5 kg, 취급상한 2.0 kg.
- 비대칭 key + captive M5 clamp 2개 + sealed metal throat를 사용한다.
- Gate를 닫기 전 undock 금지, redock 전 가시 청결검사, batch ID/material/color/lot 추적을 요구한다.
- Tower B는 cooling 440 mm, die→gauge 470 mm, puller 시작 600 mm를 유지한다. Hot strand를 꺾어 footprint를 줄이지 않는다.

## 안전 경계

- 공통 latching E-stop chain은 두 tower의 위험에너지를 모두 제거한다.
- Tower A motion과 Tower B drive/heater는 별도 monitored contactor/branch로 분리한다.
- 공통 접지 제어함 1개를 Tower B 하부 뒤쪽에 둔다.
- Batch/data connector로 다른 tower의 위험에너지가 따라 켜지지 않는다.
- 작업실 보유 안전장비는 model/rating/channel/fault test가 inventory된 뒤에만 credit한다.

## 미완료 gate

질량·CG 실측, anchor pullout, operator reach, profile joint/선반, modal/진동, chute cleaning, guard/service path는 물리 검증 전 열려 있다. 상세 수치와 가정은 `simulation/architecture/two_tower_contract.json`에 있다.
