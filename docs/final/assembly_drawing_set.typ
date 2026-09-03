#set document(title: "v0.8 벡터 조립 도면 세트")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= v0.8 벡터 조립 도면 세트
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

= GA-001 — general arrangement
#image("../drawings/v0.8/GA-001_general_arrangement.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `GA-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= ASM-001 — full assembly
#image("../drawings/v0.8/ASM-001_full_assembly.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `ASM-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= ASM-002 — module arrangement
#image("../drawings/v0.8/ASM-002_module_arrangement.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `ASM-002` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= FR-001 — frame
#image("../drawings/v0.8/FR-001_frame.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `FR-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= SH-001 — shredder assembly
#image("../drawings/v0.8/SH-001_shredder_assembly.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `SH-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= SH-002 — cutter stack
#image("../drawings/v0.8/SH-002_cutter_stack.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `SH-002` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= SH-003 — shaft and bearing assembly
#image("../drawings/v0.8/SH-003_shaft_bearing.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `SH-003` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= SH-004 — chain and phase gear
#image("../drawings/v0.8/SH-004_chain_phase_gear.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `SH-004` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= FD-001 — hopper
#image("../drawings/v0.8/FD-001_hopper.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `FD-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= FD-002 — recirculation/screen
#image("../drawings/v0.8/FD-002_recirculation_screen.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `FD-002` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= FD-003 — positive feeder
#image("../drawings/v0.8/FD-003_positive_feeder.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `FD-003` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= EX-001 — extruder assembly
#image("../drawings/v0.8/EX-001_extruder_assembly.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `EX-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= EX-002 — screw/barrel/die
#image("../drawings/v0.8/EX-002_screw_barrel_die.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `EX-002` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= EX-003 — heater/thermocouple layout
#image("../drawings/v0.8/EX-003_heater_thermocouple.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `EX-003` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= FM-001 — cooling and strand path
#image("../drawings/v0.8/FM-001_cooling_strand_path.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `FM-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= FM-002 — gauge/puller
#image("../drawings/v0.8/FM-002_gauge_puller.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `FM-002` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= SP-001 — spooler/traverse
#image("../drawings/v0.8/SP-001_spooler_traverse.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `SP-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= GD-001 — guards and panels
#image("../drawings/v0.8/GD-001_guards_panels.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `GD-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= EL-001 — electrical enclosure
#image("../drawings/v0.8/EL-001_electrical_enclosure.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `EL-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.

#pagebreak()

= SV-001 — service envelopes
#image("../drawings/v0.8/SV-001_service_envelopes.svg", width: 100%, height: 205mm, fit: "contain")
Drawing `SV-001` · Rev v0.8 · mm · third-angle · NTS · source `65f758c4b46b520eafd86cf3667ed249af2fb5f2`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.
