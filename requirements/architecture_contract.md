# 2‑tower 수치 아키텍처 계약

상태: **ARCHITECTURE CONTRACT / VIRTUAL EVIDENCE / PHYSICAL REVIEW OPEN**

이 문서는 학부생 1인이 제작 가능한 범위로 축소한 두 rack의 치수·기능·안전 경계를 고정한다. 자동 분류와 중간 파쇄기는 MVP 범위에서 제외한다.

## 범위 결정

- Release 구성은 **1차 twin-shaft + 2차 5 mm screen granulator**의 2단 파쇄다.
- 재질·색상은 사용자가 batch 전에 수동 확인한다. 카메라 분류기, 색상 diverter, 진동 선별기, Raspberry Pi는 MVP에 포함하지 않는다.
- Tower 간 이송은 자동 docking 대신 밀폐 수동 batch bin을 사용한다.

## 고정 envelope

| 항목 | Tower A | Tower B |
|---|---:|---:|
| 역할 | 수동 투입·2단 파쇄·batch | 건조·압출·성형·권취·제어 |
| Rack | 500×500×1100 mm | 850×500×1000 mm |
| 추가 rail | 없음 | die 이후 700 mm |
| 운전 envelope | 500×500×1100 mm | 1550×500×1000 mm |
| 추정 운전 질량 | 34.50 kg | 67.35 kg |
| 추정 수직 CG | 498.4 mm | 420.9 mm |
| 무고정 tip 가속도 | 0.502 g | 0.594 g |
| 계산 anchor pair tension | 67.6 N | 0.0 N |

Tower A는 0.25 g 파쇄 진동과 60 N cutter 반력을 1.5배 한 rigid-body screen으로 검토한다. 계산상 anchor가 필요하며 각 점 1 kN 후보는 실제 substrate, edge distance와 fastener 시험으로 확정한다. Tower B도 공통 설치정책상 4점 고정한다.

## Batch·공정 interface

- Bin: gross 3.0 L, usable 2.0 L, 250 kg/m³에서 0.5 kg, 취급상한 0.7 kg.
- 비대칭 key + captive M5 clamp 2개 + sealed metal throat를 사용한다.
- Gate를 닫기 전 undock 금지, redock 전 가시 청결검사, batch ID/material/color/lot 추적을 요구한다.
- Tower B는 cooling 440 mm, die→gauge 470 mm, puller 시작 600 mm를 유지하되 rail 끝을 700 mm로 제한한다. Hot strand를 꺾어 footprint를 줄이지 않는다.

## 안전 경계

- 공통 latching E-stop chain은 두 tower의 위험에너지를 모두 제거한다.
- NC 래칭 E-stop 버튼은 공통 24 V 액추에이터 접촉기 1개의 coil을 직접 끊는다. Arduino는 보조접점을 감시할 뿐 차단을 단독 수행하지 않는다.
- 공통 접지 제어함 1개를 Tower B 하부 뒤쪽에 둔다.
- Batch/data connector로 다른 tower의 위험에너지가 따라 켜지지 않는다.
- 작업실 보유 안전장비는 model/rating/channel/fault test가 inventory된 뒤에만 credit한다.

## 미완료 gate

질량·CG 실측, anchor pullout, operator reach, profile joint/선반, 진동, chute cleaning, guard/service path와 접촉기 DC 정격은 물리 검증 전 열려 있다. 상세 수치와 가정은 `simulation/architecture/two_tower_contract.json`에 있다.
