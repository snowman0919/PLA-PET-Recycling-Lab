#set document(title: "PLA/PET Recycler v0.6 구현·교차 solver release 보고서")
#set page(paper: "a4", margin: 18mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let box(body) = block(width: 100%, fill: rgb("edf5f8"), stroke: 1pt + rgb("286783"), inset: 8pt, body)
#let warn(body) = block(width: 100%, fill: rgb("fff0e8"), stroke: 1pt + rgb("bd4b2d"), inset: 8pt, body)

#align(center)[
  #text(size: 22pt, weight: "bold")[PLA/PET Recycler v0.6]
  #text(size: 15pt)[Implementation + cross-solver baseline 보고서]
  #v(4mm)
  Revision `implementation-crosssolver-v0.6` · 2026-08-30
]

#box[
Release state: *IMPLEMENTATION_BASELINE* \
Virtual physics: *VIRTUAL_PHYSICS_VALIDATED* \
Empirical state: *EMPIRICAL_VALIDATION_OPTIONAL_NOT_RUN*
Cross-solver state: *CROSS_SOLVER_VALIDATION_PENDING*
]

#warn[본 보고서는 실제 파쇄 성능, 실제 melt flow, 실제 filament 품질 또는 안전 인증을 주장하지 않는다. Optional empirical Gate-1 미수행은 `main`을 차단하지 않지만 구매·가공·heater 통전·commissioning은 별도 사용자 승인 전 금지한다.]

= Architecture와 envelope

PLA/PET는 470 × 700 × 930 mm cabinet 안에서 공용 hopper, cycloidal-inspired dual-shaft cutter, screen, sealed hopper, 16 mm×16D screw, die, cooling, X/Y gauge, puller와 spooler를 공유한다. Manufacturing object와 motion/service keep-out을 분리했다.

#image("../renders/assembly/compact_full_assembly_isometric.png", width: 96%)

= CAD와 slicing evidence

- Active CAD 163 objects: valid B-Rep/solid topology PASS.
- Print part 12종: 각 1 solid, STL watertight 2-manifold, zero-area/non-manifold 0.
- PrusaSlicer 2.9.6: support 포함 904.20 g, 81.6 h; 실패 reserve 포함 1,012.70 g.
- Keep-out 4개는 `REVIEW_ONLY_NOT_MANUFACTURED` package에 격리.

전체 재생성 뒤 `CLEAN_CLONE_REPRODUCIBILITY`가 manifest의 모든 산출물을 재검사한다. STEP timestamp/export sequence, FCStd의 비제조 topological history map, ZIP member timestamp만 정규화한다. FCStd Document와 B-Rep 및 3MF member content는 해시 범위에 유지한다. PrusaSlicer는 path ordering 재현성을 위해 1 thread로 고정한다.

= 기계 simulation과 구조 연계

OpenModelica 1.27.0과 Modelica Standard Library 4.0.0으로 explicit process arbitration, motor·gearbox·chain/backlash·ideal broken shear fuse·cutter, screw pressure-flow feedback, cooling/forming, explicit spool length balance를 결합한 mandatory 74 scenario를 실행했다. Torque hierarchy는 14 < 18 < 22 < 34 < 48 N·m다.

동일 JSON을 10개 closed-form 구조 screening과 CalculiX bearing plate/cutter shaft deck가 읽는다. Bearing plate medium→fine 전역변위 변화 1.1644%, shaft 0.3119%로 5% mesh 기준을 통과했다. FreeCAD source에서 Fusion STEP 9개와 LC01–LC10을 생성해 source/STEP/load hash를 결박했지만 실제 Fusion solve는 `PENDING_EXTERNAL_EXECUTION`이다. Ø3.2 blind5.5 thermocouple bore는 3.4 mm ligament로 기존 blind6 SF 2.00보다 여유를 높였다.

= Throughput와 firmware

16 mm screw default virtual point는 PLA 16 rpm/99.4 g/h, PET 18 rpm/97.5 g/h, fan 100%다. 200 g/h는 `DIGITAL_STRETCH_TARGET`이다. Arduino Mega는 실제 pin map, MAX6675 5채널, motor/heater/gauge backend, EEPROM CRC calibration, ordered material change와 controlled pause를 compile/host test했다. 실물 board 시험은 미수행이다. Firmware/Modelica configuration은 controller contract와 baseline JSON에서 함께 생성된다.

Barrel front die interface는 M4-6H/PCD26으로 RFQ를 정정해 Ø34 OD와 Ø16.20 bore에 대해 nominal thread-envelope ligament outer 2.0 mm, bore-side 2.9 mm를 확보했다. Feed assembly centre는 rear Datum B 기준 12–30 mm port와 일치한다.

EX-DIE-01…05는 barrel과 C110 gasket로 직접 연결되는 Ø8 교차 유로, 7-hole breaker, Ø3×10 land insert와 304 t1.5 sacrificial retainer다. Assembly centreline은 X=74.5 mm로 cooling/gauge/puller와 일치하며 ABS duct는 shield 10 mm, die body 28 mm 이상 이격된다. Relief 4.32 MPa는 265 °C 보수 digital beam screening일 뿐이며 동일 lot 고온 물리 coupon 3개는 `NOT_RUN`이다.

= Budget와 release lock

- Conditional target: 173,729 KRW ≤180,000 KRW.
- Quote contingency: 20,000 KRW.
- Absolute plan: 193,729 KRW ≤200,000 KRW; 계획 여유 6,271 KRW.
- Donor 0원과 모든 RFQ는 미확정이며 구매 release는 BLOCKED.
- CUT-01 2장 Gate-1 coupon 외 full stack는 HOLD.
- EX-CPN-SCR/EX-CPN-BAR 외 full screw/barrel은 HOLD.

= 선택적 경험 검증과 별도 승인 gate

Gate-1 cutter torque/jam/chip size부터 Gate-5 diameter/spool까지는 `OPTIONAL_EMPIRICAL_VALIDATION`으로 유지한다. 각 결과는 simulation을 대체하지 않는 별도 correlation record다. `DESIGN_RELEASE_GATE=PASS`와 무관하게 `PROCUREMENT_APPROVAL_GATE`와 `COMMISSIONING_GATE`는 `USER_APPROVAL_REQUIRED`다.
