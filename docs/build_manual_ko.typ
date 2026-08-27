#set document(title: "모듈형 폐플라스틱 필라멘트 재생기 — 제작·조립 매뉴얼", author: "filament-recycler project")
#set page(paper: "a4", margin: (x: 17mm, y: 16mm), numbering: "1 / 1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#set par(justify: true, leading: 0.72em)
#show heading.where(level: 1): it => { pagebreak(weak: true); set text(fill: rgb("174e68")); it; set text(fill: black) }
#let warning(body) = block(width: 100%, fill: rgb("fff0e8"), stroke: 1pt + rgb("d64b2a"), inset: 9pt, radius: 4pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf5f7"), stroke: 1pt + rgb("267184"), inset: 8pt, radius: 4pt, body)
#let module_figure(path, caption) = figure(image(path, width: 92%), caption: caption)

#align(center)[
  #v(22mm)
  #text(size: 25pt, weight: "bold", fill: rgb("174e68"))[모듈형 자동 폐플라스틱\ 필라멘트 재생기]
  #v(5mm)
  #text(size: 17pt, weight: "bold")[제작·조립·시운전 매뉴얼]
  #v(12mm)
  #image("../renders/assembly/full_assembly_skeleton_isometric.png", width: 92%)
  #v(8mm)
  #text(size: 11pt)[Revision 0.1.0-preflight · 2026-08-28]
]

#warning[
  *물리 운전 승인 문서가 아니다.* 본 설계는 계산·CAD·software 검증 단계다. Cutter, heater, pressure boundary와 high-current bus는 donor inspection, 가공도 승인, E-stop/interlock/thermal/pressure fault test와 사용자 안전 승인 전 energize하지 않는다.
]

#pagebreak()
#outline(title: [목차], depth: 2)

= 문서 사용법과 책임

이 매뉴얼은 source commit, BOM Part ID, CAD artifact와 coupon 계획을 조립 순서에 연결한다. 고전류/heater 배선과 pressure proof는 자격 있는 감독이 수행하며, 사용자는 실제 donor label·치수·사진, 가공/구매 승인과 물리 시험을 담당한다.

#table(
  columns: (1.2fr, 2.8fr),
  inset: 5pt,
  stroke: 0.5pt + rgb("c6d4d8"),
  [*구분*], [*Source / Gate*],
  [요구사항], [`requirements/system_requirements.md`, `requirements/compliance_matrix.md`],
  [3D source], [`cad/freecad/**/generate.py`, `cad/parameters/baseline.json`],
  [BOM], [`bom/bom.csv`, 두 design CSV, `cost_rollup.csv`],
  [가공견적], [`exports/cnc_quote_packages` — RFQ precheck only],
  [배선], [`electronics/schematics/safety_power_control.md`, H01–H18],
  [교정], [`docs/calibration.md`, module coupon plans],
  [승인], [`validation/release_checklist.md`],
)

== 허용·금지 원료

허용 입력은 순수 PLA 출력 폐기물과 cap·neck ring·label·adhesive를 제거하고 세척한 PET body다. 한 batch에는 한 재질만 사용한다.

#warning[
  PVC, PETG, TPU, ABS/nylon/PC, 난연·도장·복합재, 미확인 플라스틱, 금속 insert/screw/bearing/magnet, 음식·세정제 잔류물은 금지한다. UNKNOWN/낮은 confidence는 Reject가 기본이다.
]

= 준비와 입고검사

== 공구·계측기

- Metric hex/torque tools, caliper·micrometer·dial indicator, pin gauge
- Insulation/continuity/PE meter와 전류 제한 bench setup
- Traceable temperature reference, thermocouple logger, airflow meter
- Qualified pressure calibrator/remote shielded proof equipment
- Tachometer/encoder length reference, force gauge, dead weights
- 보안경·face shield·cut/heat-resistant PPE와 lockout hardware

== Donor gate

Zortrax M200, 24 V PSU, NEMA17/driver, fan, TFT를 분해하기 전에 `bom/donor_inventory_checklist.md`대로 label·connector·cold resistance·shaft·driver IC를 기록한다. `NEEDS_INSPECTION/NEEDS_DYNO`는 AVAILABLE이 아니다.

== FDM coupon

`tolerance_coupon.stl`을 먼저 출력해 locating 0.10, slide 0.25, flake slide 0.40 mm baseline을 printer/material별로 바꾼다. Bearing/insert fit과 cutter shim은 별도이며 FDM coupon으로 금속 clearance를 승인하지 않는다.

#module_figure("../renders/modules/tolerance_coupon_isometric.png", [FDM tolerance coupon — 실제 측정 전 모든 print fit은 provisional])

= Frame과 전체 배치

전체 keep-out은 2,295 × 520 × 720 mm다. 4040은 shredder tower, 2040/4040은 extruder load path, 2020/2040은 forming rail에 우선한다. Tower, dryer와 spooler는 독립적으로 작업대에 고정하고 tip/anchor 시험을 수행한다.

#module_figure("../renders/assembly/full_assembly_skeleton_isometric.png", [11개 모듈 keep-out. Solid box는 제작 부품이 아니다.])

#gate[
  Frame 합격: 바닥 네 점 rocking 없음, profile 절단면/fastener 손상 없음, 각 metal plate가 profile/T-nut에 직접 하중 전달, service corridor와 screw 인출공간 ≥600 mm, PE bonding stud 확보.
]

= 입력 분류·7-port 저장

최대 Ø66×210 mm 병 envelope, 상부 닫힘/하부 열림의 이중 gate와 110 mm 분리, 차광 camera/backlight, reject flap을 먼저 dry-fit한다. Gate hinge·cam·positive-opening switch는 금속 load path에 두고 두 gate의 simultaneous-open을 기계적으로 막는다.

#module_figure("../renders/modules/input_classifier_proof_isometric.png", [500 mL 기준 병과 double-gate classifier proof])
#module_figure("../renders/modules/classification_storage_proof_isometric.png", [6색 고정 bin + Reject의 seven-port 분배 proof])

#gate[
  입력 승인: 닫힌 gate reach-probe 통과 0, simultaneous-open 0/1000 cycle, interlock 단선·stall에서 safe stop, 미확인 재질은 항상 Reject, 7개 port 오배출 0/100 cycle. 재질 정확도 목표는 source-object-grouped dataset을 고정한 뒤 승인한다.
]

= 3단 파쇄 tower

== Stage 1

20 mm keyed shaft 2개, 6004 bearing 6개와 외부 timing support plate를 먼저 금속 frame에 dry-fit한다. 60×6 mm hook disc 10개와 6.4 mm spacer stack은 timing gear와 분리하며 명목 axial clearance 0.2 mm는 ground shim으로 맞춘다.

#module_figure("../renders/modules/stage1_shredder_proof_isometric.png", [Stage 1 proof — hopper/chamber containment와 실제 gear tooth는 별도 상세 필요])

Bearing seat/runout, retainer preload, shaft hand rotation과 guard tool access를 검사한다. Printed hopper는 anti-reach와 fragment containment coupon 전 사용하지 않는다.

== Stage 2

50 mm single rotor, fixed 8×20×64 mm bed knife와 carrier를 양쪽 metal plate 사이에 조립한다. Blade clearance 0.2 mm는 metal shim으로 조정한다. Fused proof rotor를 그대로 가공하지 말고 replaceable blade pocket, shoulder/dowel, bolt와 balance drawing을 승인한다.

#module_figure("../renders/modules/stage2_shredder_proof_isometric.png", [Stage 2 rotor/bed-knife kinematic proof])

== Stage 3

17 mm shaft/6203 supports, 40 mm rotor와 stator를 조립하고 4/5/6 mm flat screen coupon으로 입도를 고른다. Full containment에는 선택된 curved screen/support와 oversize return, dust seal을 추가한다.

#module_figure("../renders/modules/stage3_granulator_proof_isometric.png", [Stage 3 proof — flat screen은 opening coupon이지 containment가 아니다])

#warning[
  Cutter chamber는 회전 중 열지 않는다. Jam 제거는 E-stop, main disconnect, 0 V, shaft mechanical block와 전용 도구 후에만 수행한다.
]

= 진동 선별·저장

8° 2-deck cassette에 top 6 mm, bottom 3 mm screen을 M5 captive clamp로 고정한다. 네 isolator와 guarded eccentric를 metal bracket에 장착하고 flexible boot를 oversize/acceptable/fines path에 연결한다.

#module_figure("../renders/modules/vibratory_sorter_proof_isometric.png", [세 흐름 vibratory sorter proof])

#gate[
  5–40 Hz sweep, frame acceleration ≤0.35 g 목표, resonance dwell 금지, fastener 이동 0, fines leak 0, cassette를 주변 module 분해 없이 인출할 수 있어야 한다.
]

= Dryer·정량 feeder

ID140×320 mm metal hopper/cone, three-point metal support와 40 mm insulation을 조립한다. PLA 60 W branch와 PET 240 W branch는 hardware selector, 서로 다른 independent trip/fuse와 metal hot path를 가진다. Agitator, double gate와 30 mm auger의 load path를 출력물에 두지 않는다.

#module_figure("../renders/modules/dryer_feeder_proof_isometric.png", [Dual-profile dryer/feeder proof])

PET baseline은 140 °C 2 h+160 °C 4 h, PLA는 45 °C 6 h다. Dew point ≤−40 °C와 PET outlet moisture ≤50 ppm은 물리 coupon 전 미검증이다.

= 18 mm extruder

24 L/D screw, ID18.2/OD38 barrel, breaker/screen, Ø3×12 mm die를 승인된 metal 재질·열처리·표면/공차 drawing으로 제작한다. Screw→51102 thrust bearing→12 mm plate→profile과 die/barrel→clamp→profile 하중경로를 유지한다.

#module_figure("../renders/modules/extruder_proof_isometric.png", [18 mm pressure-limited extruder proof])
#module_figure("../renders/modules/extruder_screw_isometric.png", [24회전 faceted helical proof — smooth CNC toolpath가 아니다])

Heater 네 branch, control/high-limit sensor, branch fuse, one-shot fuse, pressure transducer, mechanical relief와 guarded catch를 설치한다. Heater envelope 밖에는 실두께 50 mm insulation과 8 mm air gap의 grounded metal shield를 둔다. PLA/ABS 부품은 shield 직접 복사 시야에 두지 않고 metal baffle의 유효 view factor를 0.60 이하로 제한한다. 정상 shield ≤50 °C와 인접 polymer ≤45 °C를 seam/clamp/slot/penetration 열전대로 확인한다. 구조 계산 20 MPa와 열저항 모델은 임의 pressure/thermal proof 지시가 아니다.

= Cooling·gauge·puller

146.667 mm 덕트 3개를 총 440 mm로 조립하고 80 mm fan 3개를 각각 service connector에 연결한다. 첫 hot strand 덕트는 metal/temperature-qualified material이다. Gauge 중심은 die에서 470 mm다.

#module_figure("../renders/modules/forming_line_proof_isometric.png", [Cooling, gauge, puller assembly])
#module_figure("../renders/modules/diameter_gauge_optical_proof_isometric.png", [Enclosure를 제거한 direct/mirror dual-view ray proof])

Ø40×16 mm roller를 1.50 mm nominal gap으로 맞추고 3–15 N nip을 coupon으로 정한다. Ø30 mm odometer는 저하중 tangent contact하며 drive encoder와 slip을 비교한다. Mirror/window는 교체·세정 가능해야 한다.

= Dancer·traverse spooler

12 mm shaft와 6001 bearing을 두 metal plate에 설치하고 printed taper adapter에는 별도 metal clamp/retainer를 둔다. Ø200×73 mm maximum spool, cage radial 5 mm와 dancer sweep clearance 6.445 mm를 확인한다.

#module_figure("../renders/modules/spooler_proof_isometric.png", [1 kg급 maximum-envelope spooler proof])

Dancer 120 mm ±30°, target 0.5 N, clutch 0.25 N·m, traverse 70 mm/1.8 mm pitch를 교정한다. Full 1 kg winding, tip, flange spill, end-stop와 8 h endurance 전 production 승인하지 않는다.

= 전기·제어 조립

#warning[
  Mains/24 V high-current wiring은 selected MPN, fuse coordination, wire/connector rating과 자격 있는 감독 없이는 수행하지 않는다. 아래는 topology이며 현장 배선 승인도가 아니다.
]

H01–H18 harness schedule대로 AC disconnect→PSU→dual-channel E-stop relay→contactor→fused switched bus를 배선한다. Pi/Mega는 protected always-on branch다. Heater driver/Mega가 stuck-high여도 safety relay, contactor와 thermal fuse가 독립 차단해야 한다.

#module_figure("../renders/modules/control_enclosure_proof_isometric.png", [Grounded shell, metal partition, split door와 조작부의 공간 proof])

#figure(
  block(width: 92%, fill: rgb("f5f8f9"), stroke: 1pt + rgb("8ba2aa"), inset: 10pt)[
    *AC/PE* → main disconnect/fuse → 24 V PSU\
    ├ always-on fuse → 5 V buck/Pi + protected Mega\
    └ dual-channel E-stop relay → monitored contactor → branch fuses\
    #h(12pt)├ shredder/sorter/extruder/forming drives\
    #h(12pt)└ six heater fuse → thermal fuse → default-off driver
  ],
  caption: [Firmware가 우회할 수 없는 전력 차단 topology]
)

Mega pin은 `mega_pinout.csv`, FRP1은 `frp1.md`를 따른다. Sensor front-end와 shredder motion feedback이 미선정인 현재 firmware qualification flag 5개는 false라 self-test가 의도적으로 arm되지 않는다.

= 제작 검토용 CAD 변형 뷰

표준 7-view 외에 section·x-ray·exploded·tool/cable·slicing 검토 뷰를 제공한다. 아래 overlay는 assembly 검토를 돕지만 최종 단면도·fastener별 공구 reach·harness 길이·G-code 승인을 대신하지 않는다.

#figure(
  grid(columns: (1fr, 1fr), gutter: 5pt,
    image("../renders/review/input_classifier_proof_section.png", width: 100%),
    image("../renders/review/stage1_shredder_proof_section.png", width: 100%),
  ), caption: [입력 double-gate와 Stage 1 cutaway review]
)

#figure(
  grid(columns: (1fr, 1fr), gutter: 5pt,
    image("../renders/review/dryer_feeder_proof_transparent.png", width: 100%),
    image("../renders/review/extruder_proof_transparent.png", width: 100%),
  ), caption: [Dryer와 extruder hidden-line x-ray review]
)

#figure(
  grid(columns: (1fr, 1fr), gutter: 5pt,
    image("../renders/review/full_assembly_skeleton_exploded.png", width: 100%),
    image("../renders/review/extruder_proof_tool_access.png", width: 100%),
  ), caption: [전체 모듈 exploded와 extruder service sweep prompt]
)

#figure(
  grid(columns: (1fr, 1fr), gutter: 5pt,
    image("../renders/review/full_assembly_skeleton_cable_routing.png", width: 100%),
    image("../renders/review/tolerance_coupon_slicing_preview.png", width: 100%),
  ), caption: [Cable topology overlay와 height-band slicing orientation preview]
)

= 시운전과 인수

무부하 순서는 PE/continuity→E-stop/contact mirror→guard wire-open→sensor open/short→driver default-off→encoder direction→개별 저속 motor→무수지 heater→airflow→pressure signal이다. 각 단계 실패 시 다음 에너지 단계로 가지 않는다.

#gate[
  설계 자동검증 통과는 물리 승인과 다르다. 최종 인수에는 donor inventory, tolerance coupon, 모든 cutter/material coupon, dryer moisture, pressure/relief, 30 min PLA/PET ≥200 g/h, 1.75±0.05 mm/ovality≤0.05 mm, 1 kg winding과 사용자 서명이 필요하다.
]

= 조립 후 필수 기록

- Commit/artifact manifest, 모든 part/harness ID와 as-built 사진
- Donor labels, MPN/datasheet, serial과 calibrated instrument IDs
- Shaft/bore/runout/shim/torque/PE/insulation 결과
- Fault-injection raw log와 reset sequence
- PLA/PET batch, moisture, temperature/pressure/current, diameter raw log
- 변경품, 원인, 재검증 범위와 승인자

= 제작자료·주문·출력 Appendix

== 항목 1–4 — 개요·안전·원료·공구

항목 1 시스템 개요, 항목 2 안전 경고, 항목 3 허용 투입물, 항목 4 필요한 공구는 본문 1–2장과 `docs/safety.md`를 따른다. 표지의 미승인 경고와 금지 원료를 작업 시작 전 작업자 전원이 확인한다.

== 항목 5 — 전체 BOM

Master는 `bom/bom.csv` 81행/19열이며 아래 표는 조달·조립 식별에 필요한 열을 PDF에 전부 싣는다. 가격은 `cost_rollup.csv`, 상세 substitute·evidence·notes는 master CSV를 사용한다. `TBD`를 0원이나 주문 승인으로 해석하지 않는다.

#let bom_rows = csv("../bom/bom.csv", row-type: dictionary)
#block[
  #set text(size: 6.3pt)
  #table(
    columns: (0.9fr, 0.8fr, 2.3fr, 0.35fr, 0.6fr, 0.65fr, 0.8fr),
    inset: 2.2pt,
    stroke: 0.35pt + rgb("c8d5d9"),
    table.header([*Part ID*], [*Module*], [*Description*], [*Qty*], [*Source*], [*Critical*], [*Status*]),
    ..bom_rows.map(row => (
      row.at("Part ID"), row.at("Module"), row.at("Description"), row.at("Quantity"),
      row.at("Source type"), row.at("Criticality"), row.at("Status")
    )).flatten()
  )
]

== 항목 6 — donor 부품 회수 방법

1. 전원을 분리하고 capacitor discharge를 확인한 뒤 Zortrax·PSU·motor/driver·fan·TFT를 분해 전 촬영한다.
2. `donor_inventory.csv`에 label, connector, wire color, cold resistance, shaft 치수와 손상을 먼저 기록한다.
3. Harness를 자르지 말고 양쪽 connector를 보존·표찰한다. 출처가 불명확한 heater/sensor/safety 부품은 재사용하지 않는다.
4. Motor는 current-limited bench에서 direction→no-load current→tach→temperature 순으로 검사하고 `NEEDS_DYNO`를 임의 해제하지 않는다.

== 항목 7–8 — 출력 설정·방향·support

아래 출력 설정과 출력 방향과 support 값은 0.4 mm nozzle 기준 시작점이며 tolerance coupon 실측이 우선한다.

#table(
  columns: (1.2fr, 1fr, 1fr, 2fr), inset: 4pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*대상*], [*Layer/wall*], [*Infill*], [*방향·support*],
  [Coupon/fit], [0.20 mm / 4], [35%], [Gap과 hole 축을 XY; support 없음],
  [Cold guard/duct/bin], [0.20 mm / 4–5], [35–50%], [넓은 base를 bed; overhang >50°만 최소 support],
  [Clamp/adapter], [0.16–0.20 / 6], [60%], [하중층이 벌어지지 않게 축을 bed와 평행; metal clamp 필수],
  [Hot/impact/shaft part], [출력 금지], [—], [금속 제작 또는 온도·충격 자격 재료만 허용],
)

Slicer preview는 height band일 뿐 seam·infill·support·G-code가 아니다. 실제 slicer에서 orientation, support 접촉면, 최소 wall, 예상 질량/시간을 저장하고 first article을 측정한다.

== 항목 9 — CNC 주문 방법

1. `exports/cnc_quote_packages` 34행을 업체에 *DFM/RFQ precheck*로 보내 공정·누락공차·재료·열처리·검사·단가·lead time을 받는다.
2. Donor 실측과 coupon 결과를 반영하고 datum/GD&T/fit/roughness/heat-treatment가 있는 최종 도면을 별도 승인한다.
3. Cutter/pressure/hot-zone은 material certificate와 검사 성적서를 요구한다. STEP만으로 주문하지 않는다.
4. 견적 유효기간·세금·배송·후처리를 분리해 100,000 KRW CNC 목표와 비교하고 사용자 서면 승인 전 발주하지 않는다.

== 항목 10–11 — 부품별 치수도·조립 전 검사

`exports/drawings/*_notes.md`, STEP와 DXF의 Part ID가 BOM과 일치하는지 확인한다. 모든 bearing bore/shaft/key/shim/plate thickness, print fit, frame squareness, fastener grade, hot-zone material, guard reach와 tool clearance를 기록한다. CAD nominal만으로 press/slip fit를 승인하지 않는다.

= 모듈 조립 색인 Appendix

== 항목 12–20 — 기계 모듈

#table(
  columns: (0.35fr, 1.1fr, 2.5fr), inset: 4pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*No*], [*조립*], [*순서와 완료 gate*],
  [12], [Stage 1 조립], [Plate/bearing dry-fit→shaft/key→shim/cutter stack→timing support→retainer; hand rotation과 0.20 mm nominal gap 측정],
  [13], [Stage 2 조립], [Side plate/bearing→rotor→carrier/bed knife→metal shim; full phase sweep와 fastener retention],
  [14], [Stage 3 조립], [Plate/bearing→rotor/stator→4/5/6 mm screen cassette; rotor-screen gap·containment 확인],
  [15], [vibratory sorter 조립], [Base/isolator→two decks→6/3 mm cassette→guarded eccentric; empty sweep 후 세 stream leak test],
  [16], [dryer feeder 조립], [3-point load-cell base→metal vessel/cone→agitator→dual gate/auger→insulation/shield→air loop; leak·airflow·temperature mapping],
  [17], [extruder 조립], [Thrust/radial support→screw/barrel→feed throat→breaker/screen→die→heater/sensor/shield; cold alignment과 remote pressure proof],
  [18], [cooling gauge puller 조립], [Three ducts/fans→dual-view optical enclosure→odometer→nip puller; occupied velocity map과 gauge calibration],
  [19], [spooler 조립], [Metal plates/bearings/shaft→clamped adapter→dancer→traverse/endstop→guard; full-radius collision and 1 kg winding],
  [20], [profile frame 조립], [Heavy tower→extruder rail→forming rail→module anchor→PE studs; square/rocking/tip/service corridor 확인],
)

== 항목 21 — 제어 패널 조립

Grounded enclosure에 metal backplate와 partition을 설치한다. Mains/24 V high-current duct와 logic/sensor duct를 분리하고 DIN rail, PE stud, gland, touch-safe terminal, fuse holder와 service loop를 selected MPN 치수로 다시 배치한다. Door 조작부가 HV conductor를 노출하지 않아야 한다.

= 전기·최초전원 Appendix

== 항목 22 — 전원 배선

H01–H18 schedule과 `safety_power_control.md`를 따른다. AC inlet→disconnect/fuse→PE/PSU→always-on logic와 safety-relay-switched high-current bus 순이다. 24 V field signal을 Mega pin에 직접 연결하지 않는다.

== 항목 23 — Arduino Mega 핀맵

Source of truth는 `electronics/pinout/mega_pinout.csv`다. D22–D29 안전 aux는 NC/open=fault, D30 contactor request는 safety relay 허가 중 하나, D4–D9 heater PWM은 default-off driver 입력이다. D14 tach, D15 hopper gate, A15 vibration을 사용하며 pin collision test가 이를 고정한다.

== 항목 24 — Raspberry Pi 연결

Qualified 24→5 V buck와 fuse로 Pi를 공급하고 Mega USB serial `115200 8N1`만 사용한다. 250 ms heartbeat, 750 ms timeout, CRC/sequence를 유지한다. Pi는 recipe/vision/log를 담당하지만 contactor나 heater를 직접 허가하지 못한다.

== 항목 25–26 — heater wiring·fuse와 E-stop

각 4개 extruder zone과 PLA/PET dryer branch는 개별 fuse→one-shot thermal fuse→default-off driver→heater, 독립 sensor 경로를 갖는다. PLA/PET dryer는 hardware selector로 상호배제한다. Dual-channel latching E-stop과 monitored contactor는 MCU stuck-high에서도 위험 에너지를 제거해야 한다.

== 항목 27–28 — 최초 전원 인가·무부하 시험

1. High-current branch를 분리한 채 PE continuity, polarity, insulation과 logic supply를 확인한다.
2. Safety relay/contact mirror, E-stop/lid/service wire-open, watchdog/USB dropout을 무에너지 상태에서 주입한다.
3. Sensor open/short와 ADC rail을 확인하고 5개 qualification lock은 signed calibration 전 false로 둔다.
4. Current-limited 상태에서 driver default-off→개별 motor 저속→direction/encoder→fan/airflow 순으로 시험한다.
5. 무수지 heater는 저전력 rise/no-rise/high-limit 시험 후에만 진행하며 pressure boundary는 remote shielded proof 절차를 따른다.

= 교정·생산 Appendix

== 항목 29 — PLA calibration

45 °C dryer stage, PLA zone 180/190/200/die 190 °C에서 낮은 feed로 시작한다. 온도 overshoot, pressure, motor load와 strand 상태를 기록하며 coupon으로 실제 setpoint를 조정한다. 30분 ≥200 g/h와 직경 합격 전 recipe를 release하지 않는다.

== 항목 30 — PET calibration

140 °C preheat 2 h→160 °C dry 4 h 후보를 사용하되 -40 °C 이하 dew point와 outlet moisture ≤50 ppm을 외부 계측으로 확인한다. PET agglomeration/degradation, 250/270/280/die 275 °C zone과 purge를 단계적으로 검증한다.

== 항목 31 — 색상 calibration

고정 6색+Reject target, matte background와 fixed lighting에서 white/black reference를 촬영한다. Source object별 group split로 confusion matrix를 만들고 threshold 변경 후 seven-port mapping과 reject rate를 재시험한다.

== 항목 32 — diameter gauge calibration

Traceable 1.70/1.75/1.80 mm pin 또는 wire를 X/Y 광로에 각각 놓고 distortion·mirror pose·threshold를 교정한다. 먼지·투명/검정 strand·vibration dropout을 포함해 U95≤0.020 mm 전에는 ±0.05 mm 생산 판정을 승인하지 않는다.

== 항목 33 — 첫 filament 생산

허용 원료 한 batch를 투입하고 각 단계 질량, moisture, temperature, pressure, current/load, d_x/d_y/mean/ovality, puller command와 spool mass를 원시 log로 남긴다. 30분 안정구간과 시작/끝 waste를 분리해 처리량을 계산한다.

== 항목 34 — 재질 변경과 purge

Feed를 차단하고 남은 flake를 회수한 뒤 현 recipe의 safe purge material로 최소 7 residence volume을 배출한다. Hopper/auger/screw/die/guide/bins를 lot 단위로 청소하고 색·재질 crossover가 없어야 다음 batch ID를 연다.

= 정비·기록 Appendix

== 항목 35 — 유지보수

`docs/maintenance.md`의 lockout, wear measurement와 lubrication 제한을 따른다. Guard를 제거한 상태로 jog하지 않고 변경된 safety part는 전체 fault matrix를 재실행한다.

== 항목 36 — cutter 청소

완전 정지·전원격리·축 고정 후 전용 도구로 잔편을 제거한다. 손으로 chamber에 들어가지 않는다. Edge chip, crack, spacer/shim, bearing play와 fastener witness mark를 기록하고 이상 시 cutter set 전체를 격리한다.

== 항목 37 — screw 청소

압력 0과 safe handling temperature를 확인한 후 승인된 pull/withdraw 절차를 사용한다. Hot polymer와 rupture path를 shield하고 screw flight/root, barrel bore, breaker/die를 긁는 강철 도구를 사용하지 않는다.

== 항목 38 — 문제 해결

`docs/troubleshooting.md`의 증상→안전정지→원인격리→재검증 순서를 따른다. Fault latch를 반복 reset해 우회하지 않으며 jam·heater·pressure·gauge fault의 원시 log를 보존한다.

== 항목 39 — 정기 점검 주기

매 batch 전 guard/interlock/PE/누설·청결, 8 h마다 cutter/shaft/bearing temperature와 harness abrasion, 40 h마다 fastener torque witness·shim·belt/coupling·filter, 200 h마다 full safety fault matrix·sensor calibration·frame anchor를 점검한다. 실제 wear rate가 더 짧은 주기를 요구하면 즉시 낮춘다.

== 항목 40 — revision 및 변경 이력

As-built 변경은 Part ID, 원인, 사진/측정, 영향 요구사항, 재실행 gate와 승인자를 commit에 남긴다. `CHANGELOG.md`, artifact manifest와 두 PDF revision을 함께 갱신하고 물리 release tag는 모든 critical checklist 서명 전 만들지 않는다.

#v(5mm)
#align(center)[#text(size: 8pt, fill: gray)[끝 — Release 상태는 `validation/release_checklist.md`가 결정한다.]]
