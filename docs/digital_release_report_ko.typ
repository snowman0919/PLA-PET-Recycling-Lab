#set document(title: "PLA/PET Recycler v0.4 디지털 release 보고서")
#set page(paper: "a4", margin: 18mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let box(body) = block(width: 100%, fill: rgb("edf5f8"), stroke: 1pt + rgb("286783"), inset: 8pt, body)
#let warn(body) = block(width: 100%, fill: rgb("fff0e8"), stroke: 1pt + rgb("bd4b2d"), inset: 8pt, body)

#align(center)[
  #text(size: 22pt, weight: "bold")[PLA/PET Recycler v0.4]
  #text(size: 15pt)[디지털 fabrication baseline 보고서]
  #v(4mm)
  Revision `solid-manifold-openmodelica-v0.4` · 2026-08-29
]

#box[
Release state: *DIGITAL_FABRICATION_BASELINE* \
Physical state: *PHYSICAL_NOT_RUN / PHYSICAL_VALIDATION_PENDING*
]

#warn[본 보고서는 물리 파쇄 성능, melt flow, filament 품질 또는 안전 인증을 주장하지 않는다. Gate-1 결과 없이 full cutter/screw/barrel 발주와 `main` 승격은 금지한다.]

= Architecture와 envelope

PLA/PET는 470 × 700 × 930 mm cabinet 안에서 공용 hopper, cycloidal-inspired dual-shaft cutter, screen, sealed hopper, 16 mm×16D screw, die, cooling, X/Y gauge, puller와 spooler를 공유한다. Manufacturing object와 motion/service keep-out을 분리했다.

#image("../renders/assembly/compact_full_assembly_isometric.png", width: 96%)

= CAD와 slicing evidence

- Active CAD 135 objects: valid B-Rep/solid topology PASS.
- Print part 12종: 각 1 solid, STL watertight 2-manifold, zero-area/non-manifold 0.
- PrusaSlicer 2.9.6: support 포함 994.61 g, 87.9 h; 실패 reserve 포함 1,113.96 g.
- Keep-out 4개는 `REVIEW_ONLY_NOT_MANUFACTURED` package에 격리.

전체 재생성 뒤 `CLEAN_CLONE_REPRODUCIBILITY`가 manifest의 모든 산출물을 재검사한다. STEP timestamp/export sequence, FCStd의 비제조 topological history map, ZIP member timestamp만 정규화한다. FCStd Document와 B-Rep 및 3MF member content는 해시 범위에 유지한다. PrusaSlicer는 path ordering 재현성을 위해 1 thread로 고정한다.

= 기계 simulation과 구조 연계

OpenModelica 1.27.0과 Modelica Standard Library 4.0.0으로 18 scenario 및 6 sensitivity sweep를 실행했다. Torque hierarchy는 14 < 18 < 22 < 34 < 48 N·m다. Dynamic envelope는 cutter 전달 22.0 N·m, bearing 1.255 kN, chain 0.603 kN, table anchor 0.485 kN이다.

동일 JSON을 9개 closed-form 구조 screening과 CalculiX bearing plate/cutter shaft deck가 읽는다. CalculiX 결과는 plate 45.36 MPa/0.1840 mm, shaft 48.63 MPa/0.0136 mm다. Gate-1 실측 pulse를 얻으면 재실행한다.

= Throughput와 firmware

16 mm screw nominal model은 PLA 18 rpm 111.8 g/h, PET 20 rpm 108.4 g/h다. 200 g/h는 stretch target이다. Firmware profile은 baseline JSON에서 생성되며 donor torque calibration이 verified가 아니면 shredder start를 거부한다. PLA/PET external pre-dry는 모두 `UNQUALIFIED_EXTERNAL_PROCESS`다.

Barrel front die interface는 M4-6H/PCD26으로 RFQ를 정정해 Ø34 OD와 Ø16.20 bore에 대해 nominal thread-envelope ligament outer 2.0 mm, bore-side 2.9 mm를 확보했다. Feed assembly centre는 rear Datum B 기준 12–30 mm port와 일치한다.

= Budget와 release lock

- Conditional target: 179,951 KRW ≤180,000 KRW.
- Quote contingency: 20,000 KRW.
- Absolute plan: 199,951 KRW ≤200,000 KRW; 계획 여유 49 KRW.
- Donor 0원과 모든 RFQ는 미확정이며 구매 release는 BLOCKED.
- CUT-01 2장 Gate-1 coupon 외 full stack는 HOLD.
- EX-CPN-SCR/EX-CPN-BAR 외 full screw/barrel은 HOLD.

= 남은 물리 gate

Gate-1 cutter torque/jam/chip size, Gate-2 flake/feed, Gate-3 cold extruder, Gate-4 hot PLA/PET, Gate-5 diameter/spool을 순서대로 수행한다. 각 단계의 signed raw data와 evidence hash가 simulation 결과를 대체하지 않고 별도 physical record가 된다.
