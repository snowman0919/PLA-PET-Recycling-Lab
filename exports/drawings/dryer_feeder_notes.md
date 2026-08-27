# 이중 프로파일 건조기·정량공급기 proof 도면 주기

## 기준 형상과 재질 경계

- hopper: 내경 140 mm, 원통 유효 높이 320 mm, 벽 2 mm, cone 높이 90 mm, outlet Ø36 mm
- 유효 체적: 4.926 L, 설계 재고 1.2 kg(벌크밀도 250 kg/m³ 기준), 200 g/h에서 6 h 체류량
- 단열재: 원통부 40 mm, 외부 ventilated metal shield와 명목 air gap 6 mm
- base: 320×270×6 mm, 3점 load-cell envelope와 metal support frame
- agitator: shaft Ø10 mm, paddle 반경 55 mm, 명목 벽 간극 15 mm, 20 rpm
- metering auger: 외경 Ø30 mm, shaft Ø10 mm, pitch 24 mm, 길이 168 mm, housing 내경 Ø34 mm
- double gate: Ø36 open-bore plate 2장, 축방향 12 mm 간격의 개념 형상

160 °C PET 모드에서 호퍼, cone, lid, gate, agitator, auger, housing, 공정 공기 덕트와 heater 접촉 경로는 모두 금속 또는 해당 온도·전압에 정격된 무기 절연물이어야 한다. PLA 인쇄물은 뜨거운 공기 경로·구조 하중·heater guard로 사용할 수 없다. 단열재 외부에는 6 mm 환기 간극과 접지된 금속 손접촉 방호판을 둔다.

## 열 프로파일과 독립 안전계통

- PLA: 45 °C × 6 h, 24 V 60 W branch, 독립 trip 60 °C, one-shot fuse 72 °C
- bottle PET: 140 °C × 2 h preheat 후 160 °C × 4 h dry, 24 V 240 W branch, 독립 trip 170 °C, one-shot fuse 184 °C
- PET 건조공기 기준: dew point −40 °C 이하, outlet moisture 목표 50 ppm
- PLA/PET heater branch는 소프트웨어 선택만 공유하지 않고 접촉기·커넥터 또는 keying으로 물리적 상호배제한다.
- heater control sensor, 독립 over-temperature sensor, outlet material sensor를 분리하고 thermal fuse는 소프트웨어로 reset할 수 없게 한다.

PET profile은 bottle-grade PET 설계값이며 PETG의 저온 건조값으로 대체하지 않는다. 외부 교정 dew-point meter와 수분 측정으로 기준을 충족하기 전에는 PET 압출을 허용하지 않는다. PET heater와 extruder peak heat-up은 전력 budget상 동시에 시작하지 않는다.

## 공급·하중 경로

CAD의 3점 frame은 base→load cell→post/rail→auger housing/hopper의 명목 하중 경로만 보여준다. 실제 제작 전 cell 정격, 편심 하중, 측력 방지 flexure, 운송 stop, 볼트·용접부와 frame 처짐을 계산한다. hopper와 dry-air hose에는 load-cell 측정을 우회하는 강성 연결을 두지 않는다.

CAD의 auger flight는 pitch/2 간격의 얇은 ring envelope다. 연속 helix, root fillet, flight 두께, 용접 순서, balance와 끝단 bearing/seal을 정의하지 않으므로 이 STEP/STL로 오거를 제작하지 않는다. 실제 helix는 2–6 rpm에서 200 g/h gravimetric calibration과 stall test 후 별도 drawing revision으로 승인한다.

Double gate는 두 open-bore plate의 공간 검토 형상이다. actuator, blade overlap, interlock sequence, powder leakage와 bridging을 입증하지 않는다. 압력·건조공기 손실 시험에서 실패하면 commercial rotary airlock으로 교체한다.

## 조립·서비스 여유

- lid/agitator 상부 인출: 최소 100 mm와 motor cable service loop
- auger 축방향 인출: drive 반대편 최소 210 mm(오거 길이 168 mm + seal/공구 여유)
- gate/airlock 하부 분리: 최소 60 mm
- insulation/shield 점검: shield 둘레 60 mm 이상 손·공구 접근 공간
- heater, blower, desiccant cartridge와 모든 hot wiring은 shield 외부에서 개별 분리 가능하게 한다.

Base DXF는 320×270×6 mm 외곽 proof만 포함한다. load-cell, frame, guard, cable gland hole pattern은 공급품 선정 후 추가해야 하며 현재 DXF는 제작 승인본이 아니다.
