#set document(title: "Implementation Cross-solver PLA/PET Recycler v0.6 설계 보고서")
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
  #text(size: 11pt)[Revision implementation-crosssolver-v0.6 · 2026-08-30]
]

#warn[*계산·CAD release다.* 실제 cutter 성능, melt flow, 200 g/h, 직경 품질과 안전 인증은 물리 Gate 전 미검증이다. 구매·CNC·energization은 사용자 승인 전 금지한다.]

#pagebreak()
= 임무와 아키텍처

PLA와 PET는 하나의 hopper, hook cutter, screen/bin, sealed feed hopper, feeder, screw/barrel/die, cooling, X/Y gauge, puller, dancer/traverse spooler를 공유한다. Material profile은 setpoint만 변경하고 RUN 중 잠긴다.

#figure(image("../renders/assembly/compact_full_assembly_front.png", width: 92%), caption: [전면 — 금속 down-die 이후 323 mm straight vertical forming path])

장치 envelope는 470 x 700 x 930 mm다. Sliding lid, guard, motor/reducer, cable duct, PSU/panel, full 1 kg spool과 dancer/traverse motion keep-out이 포함된다. Screw 인출은 정비 시 전면 panel과 clamp를 제거하는 절차이며 정상 운전 envelope에는 service clearance를 포함하지 않는다.

= Layout trade

#table(columns: (1.5fr, 1.2fr, 1fr, 1fr), inset: 4pt,
  [*후보*], [*Envelope mm*], [*계획비용*], [*판정*],
  [Vertical down-die], [470 x 700 x 930], [173,729 KRW], [target PASS / donor·물리 Gate blocker],
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

이고 6 MPa에서 약 7.24 N·m다. Reduced-order Modelica는 actual screw inertia, pressure-flow resistance, torque/current/speed feedback과 hot blockage trip을 닫는다. Default coupled point는 PLA 16 rpm/99.4 g/h, PET 18 rpm/97.5 g/h, fan 100%다. 200 g/h는 cooling/forming 기준을 통과하지 않는 `DIGITAL_STRETCH_TARGET`이다.

Barrel front interface는 기존 M5/PCD28에서 M4-6H/PCD26으로 수정했다. Ø34 body와 Ø16.20 bore 사이에서 M4 major envelope 기준 outer/bore-side ligament를 각각 2.0/2.9 mm 이상 확보하고 OD 또는 bore breakthrough를 RFQ 불합격으로 규정했다. Assembly feeder centre도 rear Datum B에서 12–30 mm인 실제 feed-port 구간의 중심에 맞췄다.

EX-DIE-01…05는 40×40×48 SCM440 body의 실제 교차 Ø8 유로, Ø15.9×2 seven-hole 304 breaker, Ø11.9×14 17-4PH H900 insert, C110 gasket와 304 t1.5 sacrificial retainer다. Body와 barrel은 4×M4×45로 접속되고 outlet centreline X=74.5 mm가 두 cooling duct, 직렬·직교 X/Y gauge와 puller nip에 정렬된다. Retainer의 두 10×2.5 mm web은 265 °C 보수 first-yield 식에서 4.32 MPa지만 고온 physical coupon 3개가 3–6 MPa 개방창을 확인하기 전 합격이 아니다. Upper ABS duct는 hot shield에서 10 mm, die body에서 28 mm 이상 떨어지고 기존 관통은 제거했다.

#figure(image("../renders/review/compact_section.png", width: 92%), caption: [Section — hopper/cutter와 horizontal hot zone, vertical forming])

= 열·전력·제어

Barrel 3×100 W band와 die 60 W cartridge로 열 path가 구성되고, `T1`~`T5` 온도 센서를 포함한다. 인터록으로 shredder와 고온 구간의 상호배제 하에서 실제 열 요구는 총 360 W가 된다.
채널별 one-shot 차단을 포함해 `channel fuse`와 독립 thermal cutoff이 동작한다. 설계 기준은 3개의 상태를 분리한다: 1) `SHREDDER_ACTIVE`에서는 barrel/die heater는 OFF, 2) `EXTRUSION_ACTIVE`에서는 shredder drive는 hard-disable, 3) 비활성 안전 상태는 2차 방열만 유지.

연산치 열 계산에서 `extrusion active` peak는 490 W로 관리되고, 24 V 600 W PSU 대비 연속 target는 500 W, 허용 reserve는 100 W다.

300 °C hot path, 25 mm insulation, 10 mm air gap와 grounded sheet shield의 1D screening은 shield 52 °C, adjacent polymer 42 °C다. Seam/slot/radiation view를 포함하지 않으므로 Gate 4 thermocouple 기준은 shield 55 °C, polymer 45 °C다.

200 g/h line speed는 PLA/PET 약 1.12/1.00 m/min이고 첫 gauge까지 248 mm transport delay는 약 13.3/14.9 s다. Diameter simulation은 first-order/transport model뿐이며 calibration·melt dynamics를 증명하지 않는다.

= Gauge와 spooler

두 직교 LED/photodiode shadow channel을 채택한다. `d_mean=(d_x+d_y)/2`, ovality는 두 축 차이의 절댓값이다. U95 <=0.05 mm initial, <=0.03 mm improvement를 traceable pin/wire로 검증한다.

#figure(image("../renders/review/forming_spool_motion.png", width: 92%), caption: [Puller 이후 solid guide, dancer sweep, traverse와 full spool])

Puller가 직경을 결정하며 spooler는 dancer를 추종한다. Maximum spool Ø200 x 73 mm와 dancer/traverse full motion이 assembly bounding box에 포함된다.

= 비용과 제조

Specific motor/coupling/gear 종속 제거, donor flat stock과 coupon 선행, 360 W heater계와 실제 slicing을 반영한 조건부 target은 173,729 KRW다. 20,000 KRW contingency 포함 absolute plan은 193,729 KRW이며 계획 여유는 6,271 KRW다. Motor 0원은 exact evidence 전 확정이 아니고 구매·가공은 별도 사용자 승인 대상이다. Optional Gate-1 미수행은 `main` 승격을 막지 않는다.

#figure(image("../renders/review/print_orientation.png", width: 92%), caption: [12개 출력 part family orientation overview])

PrusaSlicer 2.9.6 toolpath 질량은 필요한 part의 support를 포함해 904.20 g, 실패 reserve 12% 반영 기준 procurement mass는 1,012.70 g, 총 시간은 81.6 h다. 12개 plate와 PPR-TC01의 첫 extrusion layer SVG를 `exports/print/slicing_previews`에 생성해 bed 배치와 perimeter/infill/support role을 사람이 검토할 수 있게 했다. CAD nominal mass와 slicer mass는 별도 기록한다. 고하중·hot path는 출력품을 사용하지 않는다.

= 검증 경계

#ok[Implementation baseline은 closed B-Rep, manifold mesh, actual slicing, Arduino Mega compile/host test, OpenModelica mandatory 74 scenario, CalculiX 3단계 mesh/analytical structure, controller-contract/firmware sync와 Fusion 중립 package hash binding을 검사한다. 상태는 IMPLEMENTATION_BASELINE / VIRTUAL_PHYSICS_VALIDATED / CROSS_SOLVER_VALIDATION_PENDING / EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN이다.]

Fusion용 STEP 9개와 LC01–LC10, static/modal/thermal/thermal-stress/nonlinear/event/buckling study 계약은 준비됐으나 Autodesk Fusion 실행 결과는 없다. 따라서 solver correlation은 PENDING이며 OpenModelica/CalculiX PASS를 Fusion PASS로 표시하지 않는다.

Gate-1…5는 optional empirical commissioning/model-correlation 절차다. 수행 결과와 simulation 결과를 혼용하지 않는다.
