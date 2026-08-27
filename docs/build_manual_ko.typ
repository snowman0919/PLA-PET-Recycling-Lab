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
  [요구사항], [`requirements/system_requirements.md`],
  [3D source], [`cad/freecad/**/generate.py`, `cad/parameters/baseline.json`],
  [BOM], [`bom/bom.csv`, 두 design CSV],
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

Heater 네 branch, control/high-limit sensor, branch fuse, one-shot fuse, pressure transducer, mechanical relief와 guarded catch를 설치한다. 구조 계산 20 MPa는 임의 hydro/pneumatic proof 지시가 아니다.

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

Mega pin은 `mega_pinout.csv`, FRP1은 `frp1.md`를 따른다. Sensor front-end가 미선정인 현재 firmware qualification flag 4개는 false라 self-test가 의도적으로 arm되지 않는다.

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

#v(5mm)
#align(center)[#text(size: 8pt, fill: gray)[끝 — Release 상태는 `validation/release_checklist.md`가 결정한다.]]
