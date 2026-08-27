# 18 mm 단축 압출기 proof 도면 주기

## 기준 형상

- screw: 외경 Ø18.000 mm, 24 L/D = 432 mm flight length, pitch 18 mm, 24회전
- feed/transition/metering: 144/144/144 mm, channel depth 2.8125→1.125 mm, compression ratio 2.5:1
- flight width: 1.8 mm, CAD proof 분할 10°(회전당 36 facet), 최대 chord 오차 0.0343 mm
- barrel: bore Ø18.200 mm, OD Ø38 mm, hot length 438 mm, 명목 radial clearance 0.100 mm
- breaker: 두께 6 mm, Ø1.5 mm 구멍 7개; screen pack 후보 40–125 mesh
- die: Ø3.0 mm × 12 mm land, screw nose–breaker 2.0 mm, breaker–die 면접촉
- drive: 20–45 rpm, 연속 20 N·m 목표, 30 N·m latched torque trip
- base: −90…760 mm, 850×220×6 mm; 모터 cradle, 감속기 pedestal, 4040 rail과 금속 지지판

현재 helical STEP은 공간·간극·가공경로 proof다. 연속 곡면 CNC 형상은 이 표의 OD, pitch, channel depth와 transition을 보존해 재생성하고, root fillet/flight flank/entry blend를 제조도에서 정의한다. STL로 screw, barrel, breaker, die, thrust plate 또는 압력부를 제작하지 않는다.

## 공차와 표면 요구

Ø18.000/Ø18.200은 명목치이며 열팽창, 축 처짐, flight 마모와 polymer wedging을 포함하지 않는다. 제작 승인 전 screw OD·barrel bore의 재질별 열팽창으로 280 °C worst case를 다시 계산하고 다음을 치수검사한다.

- screw OD, barrel bore와 전체 길이의 25/50/75% 위치
- screw 축 기준 flight OD 및 bearing journal의 total indicated runout
- barrel bore 직진도·동축도, feed throat와 die register 동축도
- flight flank, root와 bore의 표면조도, edge break와 질화/경화 후 치수

Cold metrology에서 모든 위치의 실제 radial clearance가 승인 범위 안에 있고, hot-growth 분석과 회전 coupon이 통과하기 전 조립하지 않는다. 0.100 mm proof 값은 제조 허용차가 아니다.

## 압력 경계와 하중 경로

- clean target 3 MPa, warning 5 MPa, 자동 감속 6.5 MPa, latched stop 8 MPa
- 기계식 relief 후보 10 MPa, 구조 proof 계산값 20 MPa
- 8 MPa 추력 2.036 kN, 20 MPa proof feature 추력 5.089 kN
- 51102 후보 정격: static 16.8 kN, proof-feature 안전율 3.30

하중 경로는 die/barrel→barrel clamp plates→rail/base와 screw shoulder→51102 thrust bearing→12 mm thrust plate→rail/base다. CAD의 압력센서와 파열장치는 keep-out/열린 port proof만 제공한다. 실제 transducer diaphragm, thread engagement, seal, rupture-disc holder, 배출 방향, catch volume과 공급자 온도·압력 정격은 별도 승인한다. Relief discharge는 사람, 배선, 가연물과 정면으로 마주보지 않으며 접지된 금속 catch 안으로 유도한다.

20 MPa는 구조 계산용 proof feature이지 무자격 작업자의 시험 지시가 아니다. 완성 pressure boundary의 proof, relief calibration과 법규 적합성은 자격 있는 압력시험 담당자가 승인한 절차·차폐 설비로 수행한다.

## 열·전기 경계

- heater zones: 80/80/80/60 W, 합계 300 W
- PLA setpoints: 180/190/200/190 °C; independent high limit 230 °C
- bottle PET setpoints: 250/270/280/275 °C; independent high limit 295 °C
- thermal fuse 후보 300 °C, hot-zone design maximum 310 °C
- insulation 40 mm, grounded ventilated shield air gap 8 mm, 접근 표면 목표 50 °C 이하
- thrust bearing–hot barrel axial heat break: 73 mm; bearing plate 목표 70 °C 이하

각 zone은 heater control sensor와 독립 high-limit sensor를 분리한다. SSR welded-on, sensor open/short, MCU hang에서도 독립 접촉기와 one-shot thermal fuse가 heater branch를 차단해야 한다. Feed throat cooling은 PLA 공급원 지침에 따라 항상 proof하고, 냉각 유량 상실 시 feed와 screw를 정지한다. PET/PLA profile 변경에는 material purge와 수동 승인 절차를 둔다.

## 재질·서비스·금지사항

Screw 후보는 열처리 가능한 4140, barrel은 tool steel 또는 stainless-lined pressure tube, die/breaker는 경화·내식 금속이다. 실제 재질 인증, 열처리, 식품접촉 요구, 갈바닉/부식과 마모 입자는 미검증이다. PVC, 미확인 난연재, PETG 혼입물, 라벨·접착제·금속 오염물은 투입하지 않는다.

Screw를 drive 쪽으로 인출하려면 축방향 최소 600 mm 서비스 공간과 lift/support가 필요하다. Die/breaker/screen pack은 압력 0, heater 격리, lockout/tagout, 안전온도 확인 후만 분리한다. Guard를 제거한 상태에서는 motor energize가 불가능해야 한다. 현재 DXF는 12 mm thrust plate 외곽과 shaft/frame hole proof이며 bearing seat, fastener, gusset와 용접 상세를 포함한 제작 승인본이 아니다.
