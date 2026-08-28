#set document(title: "Solid Manifold OpenModelica PLA/PET Recycler v0.4 설계 보고서")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let warn(body) = block(width: 100%, fill: rgb("fff0e6"), stroke: 1pt + rgb("c64e31"), inset: 8pt, body)
#let ok(body) = block(width: 100%, fill: rgb("eaf5ef"), stroke: 1pt + rgb("3b7d5a"), inset: 8pt, body)

#align(center)[
  #v(20mm)
  #text(size: 24pt, weight: "bold", fill: rgb("235a70"))[Compact Single-Path PLA/PET Recycler]
  #v(4mm)
  #text(size: 16pt)[설계 보고서]
  #v(8mm)
  #image("../renders/assembly/compact_full_assembly_isometric.png", width: 95%)
  #v(5mm)
  #text(size: 11pt)[Revision solid-manifold-openmodelica-v0.4 · 2026-08-29]
]

#warn[*계산·CAD release다.* 실제 cutter 성능, melt flow, 200 g/h, 직경 품질과 안전 인증은 물리 Gate 전 미검증이다. 구매·CNC·energization은 사용자 승인 전 금지한다.]

#pagebreak()
= 임무와 아키텍처

PLA와 PET는 하나의 hopper, hook cutter, screen/bin, sealed feed hopper, feeder, screw/barrel/die, cooling, X/Y gauge, puller, dancer/traverse spooler를 공유한다. Material profile은 setpoint만 변경하고 RUN 중 잠긴다.

#figure(image("../renders/assembly/compact_full_assembly_front.png", width: 92%), caption: [전면 — 금속 down-die 이후 285 mm vertical forming path])

장치 envelope는 470 x 700 x 930 mm다. Sliding lid, guard, motor/reducer, cable duct, PSU/panel, full 1 kg spool과 dancer/traverse motion keep-out이 포함된다. Screw 인출은 정비 시 전면 panel과 clamp를 제거하는 절차이며 정상 운전 envelope에는 service clearance를 포함하지 않는다.

= Layout trade

#table(columns: (1.5fr, 1.2fr, 1fr, 1fr), inset: 4pt,
  [*후보*], [*Envelope mm*], [*계획비용*], [*판정*],
  [Vertical down-die], [470 x 700 x 930], [179,954 KRW], [target PASS / donor·물리 Gate blocker],
  [Internal U-fold], [480 x 710 x 940], [196,000 KRW], [soft bend 기각],
  [Side spool column], [495 x 720 x 950], [204,000 KRW], [비용/목표 기각],
)

#figure(image("../renders/assembly/compact_full_assembly_top.png", width: 92%), caption: [정상 운전 부품이 frame footprint 안에 있음])

= Cutter와 입도

Candidate A는 repeated 58 x 6 mm seven-hook disc 12개, 20 mm keyed shaft 2개, 6004 bearing 4개, removable 5 mm screen과 수동 oversize recirculation을 사용한다. Candidate B는 두 번째 rotor/motor/bearing/guard를 요구해 CNC family 7개, 모터 2개, bearing 6개와 340 x 250 x 260 mm를 요구한다. Candidate A의 unique cutter CNC family 3개와 약 390 x 210 x 190 mm drive envelope를 채택했다.

Cutter의 각 pitch는 76% 긴 capture flank와 24% 짧은 nose/빠른 relief로 구성한다. Capture radius는 $s(u)=u-sin(2 pi u)/(2 pi)$ cycloid displacement로 root 18 mm에서 tip 29 mm까지 상승한다. 이는 cycloidal gear tooth를 복제한 것이 아니라 capture-buckle-shear용 radial cycloid displacement를 사용한 hook이다. `CUT-01` source, STEP과 DXF가 이 곡선을 직접 생성하며 6.2 mm internal keyway는 root 안에서 끝난다.

#figure(image("../renders/modules/CUT-01_cycloidal_hook_profile.png", width: 64%), caption: [CUT-01 asymmetric cycloidal-derived profile])

Actuator는 특정 MPN이 아니라 DRV-01 universal plate, donor별 DRV-Axx, motor-side DRV-F01, #35 12T:18T/24T/30T chain, cutter-side DRV-02 hub와 generic M3 Z16 face>=18 mm phase pair의 functional interface다. Project-lab wheelchair/conveyor, scooter/e-bike geared motor, 동급 donor 순으로 검사한다. 합격값은 18–30 V reversible, cutter 환산 14 N·m continuous, 20–40 rpm이다. 14/18/22/34/48 N·m 보호 계층은 모두 cutter-shaft equivalent이며, DRV-F01 실제 설정은 12:18/24/30 ratio에서 각각 17.25/12.94/10.35 N·m다. DRV-02는 sacrificial element가 아니다. Gate-1 전 torque 달성이나 donor 0원을 주장하지 않는다.

#figure(image("../renders/modules/interchangeable_drive_interface.png", width: 90%), caption: [DRV interface schematic LOD — donor geared-DC, motor-side DRV-F01, #35 chain, cutter-side DRV-02와 M3 Z16 phase pair. 주문 형상 아님])

#figure(image("../renders/modules/shared_shredder_module.png", width: 90%), caption: [공용 input/cutter/screen/bin — metal shaft/bearing plate load path])

OpenModelica scenario에서 cutter-equivalent relief가 22 N·m로 전달토크를 제한했고 bearing과 chain의 동적 envelope를 만들었다. 이 JSON을 구조 screening과 CalculiX가 직접 읽는다. MSL Rotational/Translational/MultiBody 요소가 cutter/screw/puller, filament span, dancer/frame mass-property 경로에 사용된다. Impact, keyway notch, bearing plate bending과 실제 PET seam capture는 Gate 1 대상이다. 3–6 mm fraction은 물리시험 전 claim하지 않으며 Gate 2 실패 전 별도 stage를 추가하지 않는다.

= Dryer와 extrusion

Integrated dryer 대신 외부 pre-dry + sealed 4.5 L maintenance hopper를 채택했다. 장치 heater는 PLA 45 °C/PET 60 °C 유지용이며 건조 완료를 대신하지 않는다. 외부 dryer의 qualified temperature/time은 아직 없으므로 PLA/PET 모두 `UNQUALIFIED_EXTERNAL_PROCESS`다.

12/14/16/18 mm screw를 12–20 L/D 범위에서 비교해 16 mm x 16 L/D, active 256 mm를 선택했다. Pressure-only torque 식은

$ T = 1.5 (Delta p pi D^3) / 16 $

이고 6 MPa에서 약 7.24 N·m다. 선정 drive 목표 15 N·m continuous/22 N·m trip은 계산 여유가 있지만 friction, cold slug, screen blockage는 포함하지 않는다. Fill, conveying efficiency, backflow와 tip leakage를 포함한 nominal model은 PLA 18 rpm 111.8 g/h, PET 20 rpm 108.4 g/h다. 14–28 rpm 안에서 nominal 200 g/h를 지지하지 않으며, 200 g/h는 32–36 rpm 또는 높은 fill을 물리 검증해야 하는 stretch target이다.

#figure(image("../renders/review/compact_section.png", width: 92%), caption: [Section — hopper/cutter와 horizontal hot zone, vertical forming])

= 열·전력·제어

Heater 300 W, shredder software peak 432 W, screw 85 W, motion/fan/logic 45 W의 단순 합은 862 W로 PSU를 초과한다. 따라서 shredder enable과 barrel heater/screw enable을 hardware-enable과 state machine 양쪽에서 상호 배제한다. 허용 state peak는 500 W, 600 W PSU margin은 100 W다.

300 °C hot path, 25 mm insulation, 10 mm air gap와 grounded sheet shield의 1D screening은 shield 52 °C, adjacent polymer 42 °C다. Seam/slot/radiation view를 포함하지 않으므로 Gate 4 thermocouple 기준은 shield 55 °C, polymer 45 °C다.

200 g/h line speed는 PLA/PET 약 1.12/1.00 m/min이고 die-gauge transport delay는 약 12.6/14.1 s다. Diameter simulation은 first-order/transport model뿐이며 calibration·melt dynamics를 증명하지 않는다.

= Gauge와 spooler

두 직교 LED/photodiode shadow channel을 채택한다. `d_mean=(d_x+d_y)/2`, ovality는 두 축 차이의 절댓값이다. U95 <=0.05 mm initial, <=0.03 mm improvement를 traceable pin/wire로 검증한다.

#figure(image("../renders/review/forming_spool_motion.png", width: 92%), caption: [Puller 이후 solid guide, dancer sweep, traverse와 full spool])

Puller가 직경을 결정하며 spooler는 dancer를 추종한다. Maximum spool Ø200 x 73 mm와 dancer/traverse full motion이 assembly bounding box에 포함된다.

= 비용과 제조

Specific motor/coupling/gear 종속 제거, donor flat stock과 coupon 선행, 실제 slicing을 반영한 조건부 target은 179,954 KRW다. 20,000 KRW contingency 포함 absolute plan은 199,954 KRW이며 계획 여유는 46 KRW다. Motor 0원은 exact evidence 전 확정이 아니며, CUT-01은 Gate-1용 2장만, screw/barrel은 EX-CPN-SCR/EX-CPN-BAR coupon만 먼저 허용한다. Gate-1 PASS 없이는 current-source가 모두 일치해도 main 승격하지 않는다.

#figure(image("../renders/review/print_orientation.png", width: 92%), caption: [12개 출력 part family orientation overview])

PrusaSlicer 2.9.6 toolpath 질량은 989.76 g, 실패 reserve 12% 포함 procurement mass는 1,108.53 g, 총 시간은 87.5 h다. CAD nominal mass와 slicer mass는 별도 기록한다. 고하중·hot path는 출력품을 사용하지 않는다.

= 검증 경계

#ok[Digital baseline은 closed B-Rep, manifold mesh, actual slicing, OpenModelica 18 scenario/6 sweep, CalculiX와 firmware sync를 검사한다. 물리 상태는 PHYSICAL_NOT_RUN이다.]

물리 Gate는 cutter coupon, flake/feed, cold extruder, hot PLA/PET, diameter/full spool 순서다. Physical 결과를 simulation 결과와 혼용하지 않는다.
