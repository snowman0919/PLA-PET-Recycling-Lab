# Dancer·traverse 스풀러 proof 도면 주기

## 기준 형상과 하중경로

- 허용 spool envelope: 최대 Ø200×73 mm, 최소 지원 core Ø80 mm
- 최대 loaded mass 1.35 kg, 4 g proof 중앙하중 52.96 N
- shaft: Ø12 mm steel, bearing span 105 mm
- bearing: 6001-2RS 2개, 구조용 금속 bearing plate
- 계산 bending stress 8.19 MPa, 250 MPa yield 기준 SF 30.5, 중앙처짐 0.0063 mm
- base: `X=−15…340 mm`, 355×240 mm; 전체 설계 envelope 높이 320 mm

하중경로는 spool→금속 clamp가 포함된 taper adapter→steel shaft→6001 bearings→metal plates/profile/base다. Printed taper adapter는 중심 맞춤과 교체 인터페이스이며 torque 전달 또는 축방향 보유의 유일한 하중경로로 사용하지 않는다. Bearing seat, shaft shoulder, clamp, retaining ring와 fastener는 실제 공급품 공차에 맞춘 제작도에서 확정한다.

## Dancer와 장력

Dancer arm 길이는 120 mm, 작동범위는 ±30°, roller OD는 24 mm다. 이 범위는 총 240 mm, PLA 명목선속에서 약 12.9 s의 line buffer를 준다. 목표 장력은 0.5 N이다. End-angle reference와 Ø200 spool 사이 CAD 최소 clearance는 6.445 mm이며 guard·실제 fastener·cable loop를 포함한 coupon에서 다시 확인한다.

Angle sensor는 full range를 최소 5점 dead-weight로 교정하고 spring law, hysteresis와 friction을 기록한다. Dancer high/low limit는 각각 spool speed correction 한계와 feed/extrusion pause에 연결한다. Arm과 roller는 entanglement guard 안에 두되 filament threading을 위한 captive service position을 제공한다.

## Drive, torque limit와 traverse

PLA 명목 spool speed는 Ø80 core에서 4.45 rpm, Ø200 full에서 1.78 rpm이다. 허용 command 범위는 1–6 rpm이다. 0.5 N 장력의 full-radius torque는 0.05 N·m이고 clutch limit 0.25 N·m는 최대 반경에서 2.5 N 장력에 해당한다. Torque limiter는 공급품 정격을 사용하고 locked-spool 시험으로 실제 breakaway를 교정한다.

Traverse travel은 70 mm, layer pitch는 spool 1회전당 1.80 mm, lead screw lead는 8 mm다. 계산 carriage 속도는 core에서 8.00 mm/min, full spool에서 3.20 mm/min이다. Home/end switch 2중 경계, software travel limit와 mechanical end stop을 모두 둔다. Filament fleet angle, flange 간섭과 layer packing은 실제 1 kg winding coupon으로 승인한다.

## Guard·서비스·금지사항

Spool cage는 Ø200 reference에 radial 5 mm minimum clearance를 둔 proof envelope다. 회전 spool, shaft end, coupling, clutch와 lead screw는 손가락·머리카락·옷이 닿지 않는 impact-rated guard 안에 둔다. Guard open, shaft overspeed, dancer end limit 또는 traverse end-limit mismatch 때 drive는 latched stop되고 자동 재시작하지 않는다.

Spool 교체 전 drive 격리, dancer 무장력, shaft 정지를 확인한다. 1.35 kg spool을 한 손으로 유지한 채 clamp를 풀지 않도록 support cradle과 captive axial retainer를 둔다. DXF는 17 mm 금속 plate outline, Ø28 mm 6001 envelope와 M8 후보 hole의 proof이며 bearing press fit, gusset, weld, edge break와 최종 fastener pattern은 포함하지 않는다.
