#set document(title: "Coupled Digital Validation PLA/PET Recycler v0.5 제작 매뉴얼")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 8pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 8pt, body)

#align(center)[
  #v(20mm)
  #text(size: 23pt, weight: "bold", fill: rgb("235a70"))[Compact PLA/PET Recycler]
  #v(3mm)
  #text(size: 16pt)[제작·조립·시운전 매뉴얼]
  #v(8mm)
  #image("../renders/assembly/compact_full_assembly_isometric.png", width: 95%)
  #v(5mm)
  #text(size: 11pt)[Revision implementation-crosssolver-v0.6 · 2026-08-30]
]

#danger[*물리 운전 승인 문서가 아니다.* Cutter, screw, heater, mains/high-current는 사용자 승인, exact component 확인, guard와 commissioning gate 전 energize하지 않는다.]

Release: `IMPLEMENTATION_BASELINE` / `VIRTUAL_PHYSICS_VALIDATED` / `EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN`.

#pagebreak()
= 작업 전 확인

`bom/reuse_inventory.csv`의 UNVERIFIED 항목은 label, 수량, 상태, shaft, voltage/current와 telemetry를 기록한다. 사용할 수 없는 donor는 `cash_budget.csv` allowance 범위에서 대체하되 주문은 승인 후 진행한다.

#danger[조건부 target은 173,729 KRW, contingency 포함 absolute plan은 193,729 KRW지만 donor motor와 RFQ는 UNVERIFIED다. Optional Gate-1 미수행은 main을 차단하지 않지만, donor 0원 확정·full cutter/screw/barrel 발주·통전에는 이 문서를 승인서로 사용할 수 없다.]

PLA/PET 원료는 batch별로 분리한다. PET는 cap, neck ring, label, adhesive와 오염을 제거하고 PLA에는 metal insert가 없어야 한다. 미확인 plastic은 투입하지 않는다.

#gate[Lockout: main disconnect OFF, 0 V 확인, cutter/screw shaft mechanical block, thermal cooldown 확인 뒤 service한다. E-stop만으로 jam을 제거하지 않는다.]

= Frame과 module 배치

470 x 700 x 930 mm profile frame을 평면 table에 고정한다. 2020은 890×4, 430×10, 660×6, 300×2, 318×1, 280×2, 50×1이고 shredder tier에는 2040 660×2를 40 mm 축이 수직이 되게 쓴다. 총 profile은 14.668 m다. Virtual relative bearing displacement는 0.351 mm다.

#figure(image("../renders/assembly/compact_full_assembly_front.png", width: 92%), caption: [전면 조립 기준])

조립 순서: frame -> control/PSU와 PE -> extruder thrust/barrel -> vertical forming -> spooler -> sealed hopper/feeder -> shredder plates/shaft -> screen/bin -> anti-reach/hopper/lid -> guard/cable duct다. 본체 금속 제작품 24 family의 FCStd/STEP/STL/DXF와 controlling note는 `exports/fabrication/parts`에 있으며 `machine_manifest.csv`와 `assembly_interface_schedule.csv`가 수량·접속·검사 Gate를 지배한다. Printed housing에 cutter/extruder load를 전달하지 않는다.

== 조립·체결 schedule

#table(
  columns: (7%, 17%, 17%, 13%, 12%, 34%),
  inset: 2.5pt,
  table.header([순서], [부품/수량], [체결품], [공구], [체결 torque], [방향·순서·critical clearance]),
  [1], [20×20 frame rail/column], [M5 T-nut·washer], [4 mm hex, square, tape], [4.0 N·m], [바닥→column→상부; 대각차 ≤1.0, table M8 anchor는 최종 수평 후 체결],
  [2], [Control/PSU/PE], [M4×10 + tooth washer], [3 mm hex, DMM], [1.2 N·m], [PE를 먼저, 신호선을 나중; hot shield·motor cable과 분리, 0 V continuity 기록],
  [3], [Thrust/barrel/EX-DIE-01…05], [M6×20 8.8; die 4×M4×45 10.9 + C110 gasket; retainer 2×M4], [3/5 mm hex, dial indicator], [M4 die 3.0 / retainer 1.2 / M6 9 N·m], [Thrust→barrel→breaker→gasket→die body→insert→retainer; screw hand TIR ≤0.10, shield air gap ≥10],
  [4], [Cooling/gauge/puller], [PPR-C05 M4×12, C06 M3×12, C07 M4 captive], [2.5/3 mm hex], [M3 0.5 / M4 1.2 N·m], [die→duct→X/Y gauge→puller 직선; soft filament 굴곡 금지],
  [5], [Guide/dancer/spool], [PPR-C08 M5, C09 M6 clamp, C10 M4], [4/5/3 mm hex], [M4 1.2 / M5 2.5 / M6 4 N·m], [metal spindle가 축하중 부담; dancer -25…+25°, traverse 0…80 전 범위 확인],
  [6], [CUT-03/05/6004/CUT-08], [M6 plate + M4 retainer], [press sleeve, 4/5 mm hex], [M4 1.2 / M6 9 N·m], [Bearing outer ring만 압입; shaft→bearing→plate→profile 금속 하중경로],
  [7], [CUT-01/02 stack], [6 mm key + ground shim], [feeler gauge, torque wrench], [shaft nut 업체도면값], [축별 disc 순서를 기록; axial gap 0.25–0.50, screen 최소 1.9],
  [8], [DRV-01/Axx/F01/02/03], [M6 mount, M4 gear laminate+dowel], [straightedge, dial, 3/5 mm hex], [M4 1.2 / M6 9 N·m], [Motor→F01→12T chain→18/24/30T→DRV-02→phase pair; chain alignment ≤0.5],
  [9], [Hopper/bin/screen], [PPR-C01/02 M4, C03 M3, C04 M5], [2.5/3/4 mm hex], [M3 0.5 / M4 1.2 / M5 2.5], [Screen이 service 방향으로 완전히 빠져야 함; baffle 직선 손 접근 차단],
  [10], [Guard/interlocks/cable], [M4 captive + tooth washer], [3 mm hex, DMM], [1.2 N·m], [Guard를 마지막 체결; S0/S1 개방 시 K1=0, power restore 무자동재기동],
)

각 체결부는 torque 기록 후 witness mark한다. Nyloc은 손으로 thread 2산 이상 돌린 뒤 조이고, heat-set insert는 `PPR-TC01` 합격 온도/보정값으로만 삽입한다. Hole을 억지로 키워 조립하지 말고 해당 part source parameter를 수정해 재생성한다.

= Hopper와 cutter

PPR-C01 sliding lid와 PPR-C02 baffle을 metal hopper에 M4 captured nut로 조립한다. Lid를 열어도 높이는 930 mm를 넘지 않는다. Reach probe가 cutter에 닿으면 사용하지 않는다.

#figure(image("../renders/modules/PPR-C02_individual.png", width: 75%), caption: [PPR-C02 anti-reach baffle])

20 mm shaft, bearing 6004, metal plates를 dry-fit하고 hand rotation을 확인한다. 각 side plate 바깥에서 `CUT-08` 2 mm steel figure-eight retainer를 M4 6개로 체결해 bearing outer ring을 축방향 고정한다. Retainer의 Ø34 relief가 inner ring/seal에 닿지 않아야 한다. Hook disc clearance는 ground metal shim으로 맞춘다. PPR-C04 handle은 removable metal screen에만 연결하며 구조 screen을 출력하지 않는다.

`CUT-01`은 76% cycloidal capture flank가 회전 중심 쪽 root에서 tip으로 진행하고, 24% 빠른 relief가 hook back을 만들도록 좌우 shaft에 같은 disc를 끼운다. 오른쪽 shaft만 180/7 degree phase offset한다. Ø20.2 bore의 6.2 mm blind internal keyway가 root section 안에서 끝나고 tooth 외곽까지 열리지 않았는지 검사한다. 각 disc 사이에는 `CUT-02` 7 mm spacer와 금속 shim을 사용한다. Disc가 plate 또는 반대 shaft disc와 접촉하면 motor를 연결하지 않는다.

검증된 18–30 V donor geared-DC motor를 `CUT-07/DRV-01` universal plate의 standard metal angle과 donor별 `DRV-Axx`에 장착한다. #35 12T motor sprocket과 18T/24T/30T cutter sprocket을 cutter-side `DRV-02` four-bolt hub로 분리하고 chain alignment를 0.5 mm 이내로 맞춘다. 두 cutter shaft에는 generic M3 Z16, 20 degree, face>=18 mm steel pair 또는 DRV-03 lamination 3장/gear를 설치한다. Motor-side `DRV-F01` replaceable shear element는 22 N·m cutter-equivalent가 되도록 12:18/24/30 ratio에서 각각 17.25/12.94/10.35 N·m로 calibration한다. DRV-02는 sacrificial element가 아니며 34 N·m phase pair와 48 N·m shaft/cutter보다 DRV-F01이 먼저 분리되어야 한다. Hand rotation 20회에서 tooth/chain/disc 접촉이 없어야 interlocked guard를 닫는다.

#figure(image("../renders/modules/interchangeable_drive_interface.png", width: 92%), caption: [Interchangeable drive interface schematic LOD — donor 실측 전 adapter는 HOLD, 정상 운전은 guard 장착])

#figure(image("../renders/review/shredder_fastener_tool_access.png", width: 92%), caption: [Bearing plate/shaft/tool access review])

#danger[Gate-1 전 CUT-01은 정확히 2장 coupon만 허용한다. `exports/jigs/gate1`의 G1J-01–12/P01–P03, powered/manual assembly, metal guard upright/screen rail, closed roof, fastener schedule, S0/S1→K0→K1 hard-cut 배선과 분리된 preflight/force/drive/torque/jam/chip/evidence CSV로 donor label/shaft/current/RPM, PET body/folded seam과 PLA 1.2/2.0/3.0 mm의 torque/jam/chip size를 측정한 뒤 full stack을 판단한다.]

= Dry feed와 extruder

원료는 외부 dryer에서 준비한 뒤 밀폐 용기로 옮겨 sealed hopper에 넣는다. 현재 PLA/PET dryer recipe는 `UNQUALIFIED_EXTERNAL_PROCESS`이므로 물리 moisture coupon과 사용자 확인 없이 건조 완료로 표시하지 않는다. Maintenance heater branch에 fuse, independent high-limit와 one-shot fuse를 직렬 설치한다.

16 mm screw/barrel은 `exports/cnc/extruder`의 SCM440 QT/nitride drawing을 따른다. Barrel T1–T3은 Ø3.20 blind6이고 nominal melt-bore ligament는 2.9 mm다. Ø3 ungrounded mineral-insulated K probe를 MAX6675 T- common electronics reference에 연결하며 sheath-to-junction insulation을 수령 검사한다. Die cartridge는 Ø6.00 -0.02/-0.06, bore는 Ø6.05 H7 reamed이고 허용 직경 간극은 0.070–0.122 mm다. Thrust bearing -> metal plate -> profile 순서로 조립하고 cooldown/0 V 뒤 screw를 축방향 인출한다.

EX-DIE-02 seven-hole breaker를 EX-DIE-01의 barrel-side Ø16.20×3 seat에 넣고 새 EX-DIE-05 C110 annealed gasket를 barrel과 body 사이에 둔다. 4×M4×45 class 10.9를 3.0 N·m로 대각 체결한다. EX-DIE-03 Ø11.90×14 insert를 아래에서 넣고 EX-DIE-04 304 t1.5 retainer를 2×M4, 1.2 N·m로 고정한다. Ø8 수평/수직 channel은 borescope로 burr/step이 없는지 확인한다. 265 °C 계산값 4.32 MPa는 합격 근거가 아니며 동일 lot 3개가 shielded 265 °C hydraulic fixture에서 3–6 MPa에 insert를 포획한 채 우회 개방해야 한다. 누설·relief first-hot-test는 grounded shield, 원격 E-stop과 물리 barrier 뒤에서만 수행한다.

#figure(image("../renders/review/compact_section.png", width: 92%), caption: [Hot path와 straight vertical forming section])

Metal down-die 이후 puller까지 filament를 꺾지 않는다. 25 mm insulation, 10 mm air gap와 grounded shield를 두고 direct hot path에 polymer를 쓰지 않는다.

= Cooling, gauge, puller

PPR-C05 ABS 100 mm duct 2개와 fan을 service connector로 조립한다. Upper duct와 hot shield 사이 10 mm, die body까지 28 mm 이상을 유지한다. Die 가까운 금속 shield가 먼저 복사를 차단한다. PPR-C06 두 module은 높이 방향으로 연속 배치하고 하나를 Z축 90° 회전해 X/Y LED, slit, photodiode를 직교시킨다.

PPR-C07 guard 아래 metal puller plate와 roller를 조립한다. Manual strand insertion은 heater/roller 상태를 UI가 안내하고 guard를 닫은 뒤에만 RUN을 허용한다.

#gate[Traceable pin/wire calibration에서 X/Y U95 <=0.05 mm가 아니면 quality release를 금지한다. 물리 calibration 전 1.75 mm 정확도 달성 표시는 금지한다.]

= Guide, dancer, traverse, spool

Puller 아래에서 충분히 굳은 strand만 PPR-C08 guide roller로 방향 전환한다. 12 mm metal spindle에 PPR-C09 adapter를 끼우되 축하중은 metal clamp가 받는다. Donor rod/belt 위에 PPR-C10 traverse를 장착한다.

#figure(image("../renders/review/forming_spool_motion.png", width: 92%), caption: [Solid guide와 full motion spooler])

Empty/full dummy spool로 dancer 50° sweep, traverse 80 mm와 cable clearance를 확인한다. Spooler torque는 dancer 추종에만 사용하고 puller보다 빠르게 filament를 잡아당기지 않는다.

= Control과 UI

첫 화면 PLA/PET/Maintenance/Calibration을 확인한다. START 후 material 변경이 거부되는지 host test와 실제 panel에서 확인한다. 전환 wizard는 purge 최소량, screen clean, hopper clean, temperature transition, final confirmation을 모두 요구한다.

표시 항목은 material/state, screw speed, shredder load, heater temperature, feeder, X/Y/mean/ovality/U95, spool progress와 fault다.

= 선택적 경험 검증과 합격 기록

Gate 1 cutter coupon부터 Gate 5 diameter/full spool까지는 `OPTIONAL_EMPIRICAL_VALIDATION`이다. 정확한 부품, 절차, 측정과 pass/fail은 `validation/test_plans/physical_gates.md`에 있으며 미수행은 design release나 main을 차단하지 않는다. 실행은 별도 사용자 승인 대상이다.

#danger[계산 PASS나 CAD 간섭 PASS를 실제 파쇄, melt flow, filament 품질 또는 안전 인증으로 옮겨 적지 않는다.]

= Print package

각 `exports/print/PPR-Cxx` 폴더에는 FreeCAD Python, FCStd, STEP, STL, 3MF, print notes와 dimension sheet가 있다. `plate_layouts`의 3MF는 PrusaSlicer 2.9.6이 생성한 실제 plate이며 필요한 part의 support를 포함해 nominal 904.20 g/81.6 h, reserve 포함 1,012.70 g이다. `slicing_previews/*-first-layer.svg`에서 220×220 mm bed상의 실제 첫 extrusion layer를 확인한다. 대용량 raw G-code는 같은 source/profile로 재생성한다. 모든 part는 각 축 210 mm 이하를 자동 검사한다. `PPR-TC01` tolerance coupon을 먼저 출력해 hole/insert/slide 보정을 기록한다.

#figure(image("../renders/review/support_contact.png", width: 92%), caption: [아래보기 facet support-contact review — red])
