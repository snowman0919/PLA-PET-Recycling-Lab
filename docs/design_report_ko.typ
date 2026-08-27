#set document(title: "모듈형 폐플라스틱 필라멘트 재생기 — 설계·검증 보고서", author: "filament-recycler project")
#set page(paper: "a4", margin: (x: 17mm, y: 16mm), numbering: "1 / 1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#set par(justify: true, leading: 0.72em)
#show heading.where(level: 1): it => { pagebreak(weak: true); set text(fill: rgb("174e68")); it; set text(fill: black) }
#let status(body) = block(width: 100%, fill: rgb("fff5df"), stroke: 1pt + rgb("cf8b22"), inset: 9pt, radius: 4pt, body)
#let good(body) = block(width: 100%, fill: rgb("eaf5f1"), stroke: 1pt + rgb("2f8069"), inset: 8pt, radius: 4pt, body)
#let metric(name, value, note) = [*#name:* #value #text(fill: gray, size: 8pt)[#note]]

#align(center)[
  #v(20mm)
  #text(size: 24pt, weight: "bold", fill: rgb("174e68"))[폐 PLA/PET → 1.75 mm 필라멘트]
  #v(4mm)
  #text(size: 17pt, weight: "bold")[시스템 설계·계산·검증 보고서]
  #v(10mm)
  #image("../renders/assembly/full_assembly_skeleton_isometric.png", width: 94%)
  #v(8mm)
  Revision 0.1.0-preflight · 2026-08-28
]

#status[
  *현재 판정: DESIGN PACKAGE GENERATED / PHYSICAL VALIDATION OPEN.* Parametric CAD, 계산, firmware/Pi core와 문서는 재현·자동시험됐지만 실제 기계의 안전·처리량·품질은 승인되지 않았다.
]

#pagebreak()
#outline(title: [목차], depth: 2)

= 요구사항과 아키텍처

목표는 순수 PLA 출력물과 전처리된 PET bottle/body를 material/color 분류, 3단 파쇄, 3-stream 선별, dual-profile 건조, 18 mm single-screw 압출, 공랭, dual-view gauge, puller 폐루프와 1 kg spooler로 처리하는 것이다.

#table(
  columns: (1.2fr, 1fr, 2.2fr), inset: 5pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*성능*], [*설계값*], [*현재 증거*],
  [안정 처리량], [≥200 g/h], [계산 목표; 물리 30 min 미실시],
  [직경], [1.75±0.05 mm], [Gauge/calibration software; optic U95 미실시],
  [개선/ovality], [±0.03 / ≤0.05 mm], [제어 simulation; production 미실시],
  [전원], [24 V 600 W 진술], [480 W provisional software cap; label 미확인],
  [크기], [2295×520×720 mm], [Full assembly keep-out CAD],
)

Mega가 위험 actuator 최종 권한을 가지고 Pi는 vision, recipe와 log를 담당한다. E-stop, guard chain, thermal fuse, pressure trip과 contactor는 firmware 밖에서 동작한다.

43개 시스템 요구사항은 `requirements/compliance_matrix.md`에서 one-to-one 추적한다. 현재 집계는 automated pass 3, design evidence 29, physical open 5, external-blocked 6이며 해석·host test를 물리 T/D 합격으로 바꾸지 않았다.

= 입력 분류와 저장

입력 proof는 320×220×220 mm 외피에 최대 Ø66×210 mm bottle, 110 mm 간격의 상·하 gate, 차광 camera/backlight 광로와 reject path를 둔다. 7-port head는 고정된 6개 색상과 Reject를 배치한다. 자동 geometry test에서 닫힌 gate와 reach probe의 공통체적은 1600 mm³, 열린 gate와 probe는 0 mm³이며 port count는 7이다.

#figure(
  grid(
    columns: (1fr, 1fr), gutter: 6pt,
    image("../renders/modules/input_classifier_proof_isometric.png", width: 100%),
    image("../renders/modules/classification_storage_proof_isometric.png", width: 100%),
  ),
  caption: [입력 classifier와 6색+Reject 저장 분배 proof]
)

이 결과는 simultaneous-open 방지 cam, positive-opening switch, fragment containment나 인식 정확도를 승인하지 않는다. 미확인 입력은 Reject이고, 정확도는 source-object-grouped dataset과 실제 조명 조건으로 측정한다.

= 파쇄 계산과 CAD

== Stage 1

#metric([Geometry], [Ø60×6 mm, 8-hook disc 10개, shaft center 50 mm], [phase sweep와 axial stack])
#metric([Drive gate], [40 N·m target / 60 N·m jam trip], [donor dyno 전 미승인])
#metric([Support], [20 mm keyed shafts, 6004 bearing 6개], [외부 timing support 포함])

#figure(image("../renders/modules/stage1_shredder_proof_isometric.png", width: 88%), caption: [Stage 1 rigid/kinematic proof])

Stage 1은 PET bottle buckle/capture와 PLA infill fracture를 대상으로 하며 solid PLA 무제한 처리를 주장하지 않는다. Cutter material, heat treatment, actual bite force와 containment coupon이 남아 있다.

== Stage 2·3

#table(
  columns: (1.2fr, 1.1fr, 1.1fr, 1.8fr), inset: 4pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*항목*], [*Stage 2*], [*Stage 3*], [*Gate*],
  [입출력], [15–30→6–12 mm], [6–12→3–6 mm], [실제 sieve distribution],
  [Rotor], [Ø50 single], [Ø40 staggered], [Replaceable pocket/balance],
  [Clearance], [0.20 mm], [0.15 mm], [Metal shim],
  [Screen], [선택적 grate], [4/5/6 mm], [Curved containment coupon],
)

#figure(
  grid(
    columns: (1fr, 1fr), gutter: 6pt,
    image("../renders/modules/stage2_shredder_proof_isometric.png", width: 100%),
    image("../renders/modules/stage3_granulator_proof_isometric.png", width: 100%),
  ),
  caption: [Stage 2/3 proof assemblies]
)

= 진동 선별기

Tray 3.5 kg, eccentric 40 g×12 mm, 30 Hz에서 force 17.1 N, free acceleration 0.499 g 계산점이다. Isolator 4개 각 약 947 N/m 후보에서 amplitude 1.38 mm, frame 전달 목표 0.35 g다. 5–40 Hz sweep와 fatigue coupon이 선정값을 확정한다.

#figure(image("../renders/modules/vibratory_sorter_proof_isometric.png", width: 88%), caption: [8° two-deck, oversize/acceptable/fines proof])

= 건조·정량공급

Metal hopper ID140×320 mm, 40 mm insulation과 closed dry-air path를 선택했다. PLA 45 °C 6 h는 60 W branch, PET 140 °C 2 h+160 °C 4 h는 240 W branch이며 hardware 상호배제한다. 200 g/h auger 계산속도는 3.54 rpm이다.

#table(
  columns: (1fr, 1fr, 1fr, 1.5fr), inset: 4pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*Profile*], [*Heat-up*], [*Steady*], [*미검증 Gate*],
  [PLA], [60 W], [약 12 W], [실제 resin dryness],
  [PET], [240 W], [약 46 W], [−40 °C dew point / ≤50 ppm],
)

#figure(image("../renders/modules/dryer_feeder_proof_isometric.png", width: 82%), caption: [Dual-profile dryer/feeder proof])

= Extruder 선정

12–18 mm 설계공간에서 18 mm×24 L/D를 선택했다. 432 mm flight, pitch 18 mm, feed/transition/metering 각 144 mm, channel 2.8125→1.125 mm, compression 2.5:1이다. CAD는 회전당 36 facet, 24회전의 닫힌 B-rep proof다.

#table(
  columns: (1.6fr, 1fr, 2fr), inset: 4pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*항목*], [*값*], [*의미*],
  [Screw/barrel], [Ø18.0 / bore 18.2], [Nominal radial clearance 0.100 mm],
  [Length], [24 L/D / barrel 438 mm], [200 g/h compact candidate],
  [Die], [Ø3×12 mm], [Draw-down/puller required],
  [Pressure], [3 target / 8 trip MPa], [20 MPa structural proof feature],
  [Thrust], [2.036 kN at 8 MPa], [51102 candidate; proof SF 3.30],
  [Drive], [20 N·m continuous at 45 rpm], [126 W nominal target; dyno required],
)

#figure(image("../renders/modules/extruder_proof_isometric.png", width: 88%), caption: [Pressure-limited extruder with metal load path])

Heater profile은 PLA 180/190/200/190 °C, PET 250/270/280/275 °C다. 각 branch는 별도 sensor/fuse이며 PLA/PET independent limit 후보는 230/295 °C다.

= Cooling·dual-view gauge·puller

Ø1.75 mm, 200 g/h 선속은 PLA 1.118 m/min, PET 0.997 m/min이다. 440 mm cross-flow tunnel은 2.5 m/s 명목에서 PLA 필요길이 365.0 mm, PET 211.6 mm이며 250 g/h/4 m/s PLA worst margin은 54.5 mm다.

#figure(image("../renders/modules/forming_line_proof_isometric.png", width: 88%), caption: [440 mm cooling + 470 mm gauge + puller])

Camera Module 3 native는 약 62 px/1.75 mm이고 32 mm macro field 목표는 약 252 px다. 두 view는 radial distortion/homography를 독립 교정하며 `U95≤0.020 mm`를 release gate로 둔다.

Die–gauge 470 mm의 PLA 지연은 25.23 s다. 900 s model에서 mass-flow feed-forward+bounded Smith PI는 RMS 0.0093 mm, max 0.0146 mm, ±0.05 밖 0 s였지만 실제 melt/tyre/camera dynamics는 미포함이다.

= Spooler

Ø200×73 mm, 1.35 kg/4 g proof의 12 mm shaft는 bending stress 8.19 MPa, SF 30.5, deflection 0.0063 mm다. Core→full speed 4.45→1.78 rpm, 0.5 N tension에서 full-radius torque 0.05 N·m, clutch limit 0.25 N·m다.

#figure(image("../renders/modules/spooler_proof_isometric.png", width: 82%), caption: [Dancer/traverse maximum spool proof])

Dancer 120 mm ±30°는 240 mm/12.9 s buffer, traverse는 70 mm, 1.8 mm/rev, 8.00→3.20 mm/min이다.

= 전력·전자·control

FRP1은 `FRP1|TYPE|SEQ|PAYLOAD|CRC16`이고 Pi heartbeat 250 ms, Mega timeout 750 ms다. Loop를 포함한 safe-output worst software latency는 760 ms, AVR watchdog은 nominal 2 s다. Persistent jam은 3 reverse retry 후 7.372 s 이내 latch된다.

#good[
  Host tests: CRC/sequence 변조, heartbeat, E-stop, contactor feedback, airflow, sensor/rise fault, 480 W arbiter, jam retry와 Pi gauge/classifier/history/dropout/quality pause가 통과했다.
]

Sensor MPN·conversion과 shredder motion feedback이 미선정이라 firmware의 5개 commissioning lock은 false다. 이는 결함이 아니라 donor를 추측하지 않기 위한 intentional fail-safe다.

#figure(image("../renders/modules/control_enclosure_proof_isometric.png", width: 82%), caption: [300×220×180 mm grounded control-enclosure topology proof])

Metal partition 기준 좌우 keep-out gap은 30 mm이고 전원/히터와 logic/sensor에 별도 duct·gland를 둔다. 실제 MPN 기준의 PE, SCCR, 열상승, 연면거리, terminal access와 wire bend radius는 물리 패널 승인 항목이다.

= BOM과 예산

시스템 BOM은 81 line, CRITICAL 56 line이다. 공개 후보 Camera USD25와 2-channel safety relay USD143만 planning FX 1,400 KRW/USD로 235,200 KRW이며 cap을 35,200 KRW 넘는다. 배송·세금·contactor·pressure·heater·CNC는 빠져 있다.

`cost_rollup.csv`는 신규구매 28 line(미가격 26), CNC/fabrication 33, print filament 6, project-lab replacement 3, donor replacement 11을 분리한다. Baseline 81 line은 모두 required이고 optional로 숨긴 항목은 0이다.

`exports/cnc_quote_packages`의 34행은 STEP/DXF/도면 메모를 묶은 DFM/RFQ precheck다. Mixed-source thrust plate를 보조 포함했으며 최종 GD&T·재료·열처리 승인 전에는 fabrication release가 아니다.

#status[
  Target Budget는 safety relay와 camera를 포함한 검증된 project-lab stock이 있을 때만 조건부다. Engineering Recommended 총액은 donor inventory, MPN과 CNC quote 전 `TBD`이며 임의 가격으로 채우지 않았다.
]

= 검증 상태와 잔여 위험

#table(
  columns: (1.4fr, 1fr, 2.2fr), inset: 4pt, stroke: 0.5pt + rgb("c8d5d9"),
  [*영역*], [*상태*], [*남은 Gate*],
  [FreeCAD/exports], [자동 PASS], [Clean clone 재생성·physical fabrication review],
  [Kinematics/thermal/control], [계산 PASS], [Material/sensor rig cross-check],
  [Firmware/Pi], [Host PASS], [Board compile·front-end·fault rig],
  [Safety], [Architecture only], [E-stop/interlock/fuse/pressure physical test],
  [Throughput/diameter], [계산 only], [PLA/PET 30 min ≥200 g/h],
  [Cost], [Floor only], [Landed quote/CNC approval],
)

가장 큰 잔여 위험은 pressure-rated screw/barrel/relief 제작, cutter impact/containment, PET dryness/degradation, electrical safety relay/contactor coordination, gauge U95와 full production stability다.

= 재현 명령

```text
nix develop --command bash -lc "FreeCADCmd -c ...generate_all.py"
nix develop --command bash -lc "FreeCADCmd -c ...render_views.py"
make -C firmware/arduino_mega test
PYTHONPATH=software/raspberry_pi python3 -m unittest discover ...
python3 validation/run_all.py
```

Artifact SHA-256는 `artifacts/manifest.json`, 상세 test 상태는 `docs/validation_report_ko.md`에 있다. 설계 변경은 관련 generator, 계산, test, render, manual과 manifest를 함께 갱신한다.

#v(6mm)
#align(center)[#text(size: 8pt, fill: gray)[끝 — 물리 Release는 서명된 checklist 없이는 선언하지 않는다.]]
