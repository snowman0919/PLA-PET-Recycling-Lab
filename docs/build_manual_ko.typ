#set document(title: "Compact Single-Path PLA/PET Recycler v0.3 제작 매뉴얼")
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
  #text(size: 11pt)[Revision compact-single-path-v0.3 · 2026-08-28]
]

#danger[*물리 운전 승인 문서가 아니다.* Cutter, screw, heater, mains/high-current는 사용자 승인, exact component 확인, guard와 물리 Gate 전 energize하지 않는다.]

#pagebreak()
= 작업 전 확인

`bom/reuse_inventory.csv`의 UNVERIFIED 항목은 label, 수량, 상태, shaft, voltage/current와 telemetry를 기록한다. 사용할 수 없는 donor는 `cash_budget.csv` allowance 범위에서 대체하되 주문은 승인 후 진행한다.

#danger[현재 exact shredder motor/driver/current sensor/phase gear 포함 cash rollup은 309,900 KRW로 상한을 109,900 KRW 초과한다. 예산 blocker를 해소하기 전 이 문서를 구매 목록으로 사용하지 않는다.]

PLA/PET 원료는 batch별로 분리한다. PET는 cap, neck ring, label, adhesive와 오염을 제거하고 PLA에는 metal insert가 없어야 한다. 미확인 plastic은 투입하지 않는다.

#gate[Lockout: main disconnect OFF, 0 V 확인, cutter/screw shaft mechanical block, thermal cooldown 확인 뒤 service한다. E-stop만으로 jam을 제거하지 않는다.]

= Frame과 module 배치

470 x 700 x 930 mm profile frame을 평면 table에 고정한다. 네 column과 top/bottom rail을 사각/대각 측정하고 metal module plate를 profile에 직접 체결한다.

#figure(image("../renders/assembly/compact_full_assembly_front.png", width: 92%), caption: [전면 조립 기준])

조립 순서: frame -> control/PSU와 PE -> extruder thrust/barrel -> vertical forming -> spooler -> sealed hopper/feeder -> shredder plates/shaft -> screen/bin -> anti-reach/hopper/lid -> guard/cable duct다. Printed housing에 cutter/extruder load를 전달하지 않는다.

= Hopper와 cutter

PPR-C01 sliding lid와 PPR-C02 baffle을 metal hopper에 M4 captured nut로 조립한다. Lid를 열어도 높이는 930 mm를 넘지 않는다. Reach probe가 cutter에 닿으면 사용하지 않는다.

#figure(image("../renders/modules/PPR-C02_individual.png", width: 75%), caption: [PPR-C02 anti-reach baffle])

20 mm shaft, bearing 6004, metal plates를 dry-fit하고 hand rotation을 확인한다. 각 side plate 바깥에서 `CUT-08` 2 mm steel figure-eight retainer를 M4 6개로 체결해 bearing outer ring을 축방향 고정한다. Retainer의 Ø34 relief가 inner ring/seal에 닿지 않아야 한다. Hook disc clearance는 ground metal shim으로 맞춘다. PPR-C04 handle은 removable metal screen에만 연결하며 구조 screen을 출력하지 않는다.

`CUT-01`은 76% cycloidal capture flank가 회전 중심 쪽 root에서 tip으로 진행하고, 24% 빠른 relief가 hook back을 만들도록 좌우 shaft에 같은 disc를 끼운다. 오른쪽 shaft만 180/7 degree phase offset한다. Ø20.2 bore의 6.2 mm blind internal keyway가 root section 안에서 끝나고 tooth 외곽까지 열리지 않았는지 검사한다. 각 disc 사이에는 `CUT-02` 7 mm spacer와 금속 shim을 사용한다. Disc가 plate 또는 반대 shaft disc와 접촉하면 motor를 연결하지 않는다.

`MY1016Z-24V-250W-75RPM` motor를 `CUT-07` slot plate에 장착하고 KTR ROTEX19 98ShA bore17/20 coupling을 right cutter shaft에 맞춘다. 두 cutter shaft 후단에는 KHK `SS3-16H` M3 Z16 hardened gear를 설치하고 bore를 20 mm shaft에 맞춰 후가공한다. Gear center는 shaft center와 같은 48 mm다. 한 gear에는 6 x 6 x 4 mm annealed brass key와 대응 6 mm keyway를 사용하고 coupon에서 20–24 N·m 범위에 전단되는지 확인한다. Hand rotation 20회에서 tooth/coupling/disc 접촉이 없어야 guard를 닫을 수 있다.

#figure(image("../renders/modules/shredder_drive_guard_removed.png", width: 92%), caption: [Direct geared-DC motor/coupling/phase gear 조립 — 정상 운전은 guard 장착])

#figure(image("../renders/review/shredder_fastener_tool_access.png", width: 92%), caption: [Bearing plate/shaft/tool access review])

#danger[Gate 1 전 full cutter stack을 발주하지 않는다. Motor label, Ø17 x 44 mm shaft, 20/73.5 mm mount, 75 rpm, no-load current를 입고검사하고 coupon에서 PET seam과 PLA 1.2/2.0/3.0 mm를 측정한 뒤 shaft/hub를 확정한다.]

= Dry feed와 extruder

원료는 외부 dryer에서 준비한 뒤 밀폐 용기로 옮겨 sealed hopper에 넣는다. Maintenance heater branch에 fuse, independent high-limit와 one-shot fuse를 직렬 설치한다.

16 mm screw/barrel을 thrust bearing -> metal plate -> profile 순서로 조립한다. Hand rotation, TIR <=0.10 mm와 30 min heater-off load를 통과하기 전 heater를 연결하지 않는다. Breaker/screen과 open die는 guard를 해체하지 않고 인출 가능해야 한다. Screw service는 hot zone cooldown/0 V 뒤 front 방향으로 extruder cassette 전체를 profile clamp에서 빼낸 다음 cabinet 밖 작업대에서 screw를 축방향 인출한다. Frame column 사이로 screw만 억지로 빼지 않는다.

#figure(image("../renders/review/compact_section.png", width: 92%), caption: [Hot path와 straight vertical forming section])

Metal down-die 이후 puller까지 filament를 꺾지 않는다. 25 mm insulation, 10 mm air gap와 grounded shield를 두고 direct hot path에 polymer를 쓰지 않는다.

= Cooling, gauge, puller

PPR-C05 ABS duct 2개와 fan을 service connector로 조립한다. Die 가까운 금속 shield가 먼저 복사를 차단한다. PPR-C06 gauge halves 안에 X/Y LED, slit, photodiode를 직교 배치한다.

PPR-C07 guard 아래 metal puller plate와 roller를 조립한다. Manual strand insertion은 heater/roller 상태를 UI가 안내하고 guard를 닫은 뒤에만 RUN을 허용한다.

#gate[Traceable pin/wire calibration에서 X/Y U95 <=0.05 mm가 아니면 quality release를 금지한다. 물리 calibration 전 1.75 mm 정확도 달성 표시는 금지한다.]

= Guide, dancer, traverse, spool

Puller 아래에서 충분히 굳은 strand만 PPR-C08 guide roller로 방향 전환한다. 12 mm metal spindle에 PPR-C09 adapter를 끼우되 축하중은 metal clamp가 받는다. Donor rod/belt 위에 PPR-C10 traverse를 장착한다.

#figure(image("../renders/review/forming_spool_motion.png", width: 92%), caption: [Solid guide와 full motion spooler])

Empty/full dummy spool로 dancer 50° sweep, traverse 80 mm와 cable clearance를 확인한다. Spooler torque는 dancer 추종에만 사용하고 puller보다 빠르게 filament를 잡아당기지 않는다.

= Control과 UI

첫 화면 PLA/PET/Maintenance/Calibration을 확인한다. START 후 material 변경이 거부되는지 host test와 실제 panel에서 확인한다. 전환 wizard는 purge 최소량, screen clean, hopper clean, temperature transition, final confirmation을 모두 요구한다.

표시 항목은 material/state, screw speed, shredder load, heater temperature, feeder, X/Y/mean/ovality/U95, spool progress와 fault다.

= 물리 Gate와 합격 기록

Gate 1 cutter coupon -> Gate 2 flake/feed -> Gate 3 cold mechanical -> Gate 4 hot PLA then dry PET -> Gate 5 diameter/full spool 순서다. 정확한 부품, 절차, 측정과 pass/fail은 `validation/test_plans/physical_gates.md`에 있다.

#danger[계산 PASS나 CAD 간섭 PASS를 실제 파쇄, melt flow, filament 품질 또는 안전 인증으로 옮겨 적지 않는다.]

= Print package

각 `exports/print/PPR-Cxx` 폴더에는 FCStd, STEP, STL, 3MF와 print notes가 있다. Plate는 `plate_layouts`, 전체 질량은 `total_material_report.md`를 참조한다. 모든 part는 각 축 210 mm 이하를 자동 검사한다.

#figure(image("../renders/review/support_contact.png", width: 92%), caption: [아래보기 facet support-contact review — red])
