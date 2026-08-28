#set document(title: "Compact Single-Path PLA/PET Recycler v0.3 설계 보고서")
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
  #text(size: 11pt)[Revision compact-single-path-v0.3 · 2026-08-28]
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
  [Vertical down-die], [470 x 700 x 930], [309,900 KRW], [기구 채택/예산 blocker],
  [Internal U-fold], [480 x 710 x 940], [196,000 KRW], [soft bend 기각],
  [Side spool column], [495 x 720 x 950], [204,000 KRW], [비용/목표 기각],
)

#figure(image("../renders/assembly/compact_full_assembly_top.png", width: 92%), caption: [정상 운전 부품이 frame footprint 안에 있음])

= Cutter와 입도

Candidate A는 repeated 58 x 6 mm seven-hook disc 12개, 20 mm keyed shaft 2개, 6004 bearing 4개, removable 5 mm screen과 수동 oversize recirculation을 사용한다. Candidate B는 두 번째 rotor/motor/bearing/guard를 요구해 CNC family 7개, 모터 2개, bearing 6개와 340 x 250 x 260 mm를 요구한다. Candidate A의 unique cutter CNC family 3개와 약 390 x 210 x 190 mm drive envelope를 채택했다.

Cutter의 각 pitch는 76% 긴 capture flank와 24% 짧은 nose/빠른 relief로 구성한다. Capture radius는 $s(u)=u-sin(2 pi u)/(2 pi)$ cycloid displacement로 root 18 mm에서 tip 29 mm까지 상승한다. 이는 cycloidal gear tooth를 복제한 것이 아니라 capture-buckle-shear용 radial cycloid displacement를 사용한 hook이다. `CUT-01` source, STEP과 DXF가 이 곡선을 직접 생성하며 6.2 mm internal keyway는 root 안에서 끝난다.

#figure(image("../renders/modules/CUT-01_cycloidal_hook_profile.png", width: 64%), caption: [CUT-01 asymmetric cycloidal-derived profile])

Actuator는 `MY1016Z-24V-250W-75RPM` geared brushed-DC motor다. KTR ROTEX19 98ShA bore17/20 coupling으로 right shaft를 직접 구동하고, KHK `SS3-16H` M3 Z16 hardened pair가 두 shaft를 반대 방향으로 동기화한다. Catalog raw torque 0.98 N·m, integrated ratio 23.2, gearbox efficiency 0.65를 적용한 보수적 cutter torque는 14.8 N·m다. ROTEX19 nominal/max는 17/34 N·m다. Gear hardened surface limit 28.0 N·m보다 낮은 20–24 N·m에서 6 x 6 x 4 mm brass phase-gear key가 전단되도록 coupon으로 조정한다. 이 값은 실측 보증이 아니며 Gate 1 calibration 전 14 N·m continuous를 달성했다고 주장하지 않는다.

#figure(image("../renders/modules/shredder_drive_guard_removed.png", width: 90%), caption: [Guard 제거 render — direct motor, ROTEX19 coupling과 hardened phase gear pair])

#figure(image("../renders/modules/shared_shredder_module.png", width: 90%), caption: [공용 input/cutter/screen/bin — metal shaft/bearing plate load path])

24 N·m에서 20 mm solid shaft torsional shear screening은 simulation JSON에 기록한다. Impact, keyway notch, bearing plate bending과 실제 PET seam capture는 Gate 1 대상이다. 3–6 mm fraction은 55–85% 가정뿐이며 Gate 2 실패 전 별도 stage를 추가하지 않는다.

= Dryer와 extrusion

Integrated dryer 대신 외부 pre-dry + sealed 4.5 L maintenance hopper를 채택했다. 장치 heater는 PLA 45 °C/PET 60 °C 유지용이며 건조 완료를 대신하지 않는다.

12/14/16/18 mm screw를 12–20 L/D 범위에서 비교해 16 mm x 16 L/D, active 256 mm를 선택했다. Pressure-only torque 식은

$ T = 1.5 (Delta p pi D^3) / 16 $

이고 6 MPa에서 약 7.24 N·m다. 선정 drive 목표 15 N·m continuous/22 N·m trip은 계산 여유가 있지만 friction, cold slug, screen blockage는 포함하지 않는다. Screening commissioning window는 120–220 g/h이며 200 g/h는 stretch target이다.

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

정확 shredder motor/driver/current sensor/hardened phase gear를 포함한 신규 현금 계획은 총 309,900 KRW로 hard cap을 109,900 KRW 초과한다. 현재 상태는 release blocker다. 고토크 donor motor/gear의 label·shaft·current를 확인하거나 CNC RFQ를 value-engineering해 총액이 200,000 KRW 이하가 되기 전 main 승격과 구매를 금지한다. Shredder 금속 package는 bearing retainer를 포함해 CUT-01부터 CUT-08까지 8개 unique family다. Full cutter와 screw를 동시에 주문하지 않고 Gate 1 coupon부터 진행한다.

#figure(image("../renders/review/print_orientation.png", width: 92%), caption: [12개 출력 part family orientation overview])

출력 질량과 개별 bounding box는 CAD solid volume에서 자동 계산된다. 고하중·hot path는 출력품을 사용하지 않는다.

= 검증 경계

#ok[자동검증은 revision, envelope, 비용, print limit, profile lock, 계산 산출물, package 존재와 stale source를 검사한다.]

물리 Gate는 cutter coupon, flake/feed, cold extruder, hot PLA/PET, diameter/full spool 순서다. Physical 결과를 simulation 결과와 혼용하지 않는다.
