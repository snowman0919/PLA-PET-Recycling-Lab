# Vibratory sorter proof 도면 주기

## 기준 형상

- base plate: 380×180×4 mm, isolator M6 위치 `(55,38)`, `(55,142)`, `(315,38)`, `(315,142)`
- tray: 320×140 mm envelope, 8° 하향
- screen cassette: 304×128 mm, active 280×110 mm
- top screen: square aperture 6.0 mm, pitch 8.0 mm, nominal wire 2.0 mm
- bottom screen: square aperture 3.0 mm, pitch 5.0 mm, nominal wire 2.0 mm
- deck pitch: normal 32 mm, screen 사이 normal clear 30.5 mm
- service clamp: 28×18×8 mm, M5 clearance Ø5.5 mm, 4개 proof

screen 격자는 개구·pitch·탈착 envelope 검토 형상이며 woven mesh 제조도면이 아니다. 공급품은 aperture 공차, wire 지름, 재질, 평탄도와 edge frame 용접을 새 drawing revision으로 반영한다. base DXF는 isolator 위치 proof이며 motor/guard/frame 최종 hole pattern이 없어 견적 외 제작 승인에 사용할 수 없다.

## 동적 장착

- moving mass 목표: 1.5 kg
- donor motor baseline: 1800 rpm
- eccentric: 40 g at 12 mm, 480 g·mm
- rubber isolator: 4개, 합성 natural frequency 8 Hz 후보
- 계산 운전점: 0.343 mm peak, 1.24 g peak
- rigid-part nominal motion allowance: ±0.4 mm의 두 배 + 2 mm = 2.8 mm

eccentric는 keyed/flat shaft, metal hub, locking fastener와 이중 이탈 방지 guard가 필요하다. 접착제만으로 고정하지 않는다. motor bracket은 금속이며 FDM으로 대체하지 않는다. isolator CAD의 상부 stud/frame 겹침은 threaded engagement envelope다.

## 배출·서비스

- top retained: guarded flexible boot를 통해 Stage 3 recirculation
- bottom retained: dryer 또는 재질/색상 storage
- bottom pass: sealed fines bin
- screen cassette는 네 M5 clamp를 푼 뒤 수직 인출하며 최소 60 mm service clearance 필요

세 경로 사이에는 conductive/antistatic 여부를 재료·분진 시험으로 정하고, 최소한 탈착 가능한 flexible seal을 둔다. screen removal door는 motor power를 물리적으로 차단하는 interlock을 가진다. snap fit만으로 screen·bin을 고정하지 않는다.
