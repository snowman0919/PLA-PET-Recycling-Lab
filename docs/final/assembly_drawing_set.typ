#set document(title: "v0.8 치수·검사 조립 도면 세트")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= v0.8 치수·검사 조립 도면 세트
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

= GA-001 — general arrangement
#image("../drawings/v0.8/GA-001_general_arrangement.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mixed assembly; see BOM.csv  *핵심 치수/공차:* 470 × 700 × 930 mm envelope; service aisle ≥600 mm  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= ASM-001 — full assembly
#image("../drawings/v0.8/ASM-001_full_assembly.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mixed assembly; see BOM.csv  *핵심 치수/공차:* high-load path cutter/screw → metal bearing plate → profile → table  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= ASM-002 — module arrangement
#image("../drawings/v0.8/ASM-002_module_arrangement.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mixed assembly; see BOM.csv  *핵심 치수/공차:* module datum transfer ≤0.50 mm; service modules removable without hot-path disturbance  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= FR-001 — frame
#image("../drawings/v0.8/FR-001_frame.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 2020/2040 aluminum profile  *핵심 치수/공차:* base 470 × 700 mm; anchor M8 ×4; rail squareness ≤0.50/700  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= SH-001 — shredder assembly
#image("../drawings/v0.8/SH-001_shredder_assembly.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* steel cutter module  *핵심 치수/공차:* shaft centres 48.00 ±0.03 mm; rotating-to-static clearance ≥1.90 mm; CUT-08 retainer M4×12 = 3 N·m; CUT-03 pair tied by 4× CUT-09 OD10/ID6.6/L128 matched steel sleeves and M6×170 class10.9 at7 N·m; plates mount through G1J-10 feet  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= SH-002 — cutter stack
#image("../drawings/v0.8/SH-002_cutter_stack.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* D2 cutters / numbered match-ground steel spacers  *핵심 치수/공차:* CUT-01 t6 and CUT-02 nominal t7; do not interchange spacers; every one of 11 axial gaps 0.25–0.50 mm over one full hand rotation by metal shim  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= SH-003 — shaft and bearing assembly
#image("../drawings/v0.8/SH-003_shaft_bearing.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* S45C QT shafts / SKF 61905-2RS1  *핵심 치수/공차:* Ø25 h6 seats; CUT-05R key clock25.714±0.02°; shaft TIR ≤0.05 mm; centre parallelism ≤0.10/150  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= SH-004 — chain and phase gear
#image("../drawings/v0.8/SH-004_chain_phase_gear.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* direct-keyed steel #35 sprockets / S45C phase gears / #35 chain  *핵심 치수/공차:* GGM_SH_12T direct-keyed to 12 h6 jackshaft with 4x4 key; GGM_SH_30T direct-keyed to CUT-05R 25 h6 with 6x6 key; keys carry torque; received maker retention hardware is axial-only and torque remains HOLD until receipt; sprocket radial TIR ≤0.10 mm; total axial shift+U95 ≤0.20 mm; chain alignment ≤0.20/150 mm; midspan slack 2–3%; DRV-02 superseded; phase stack M4×4 = 3 N·m  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= FD-001 — hopper
#image("../drawings/v0.8/FD-001_hopper.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 5052-H32 hopper  *핵심 치수/공차:* feed opening 150 × 150 mm; all reachable edges R/C ≥0.5 mm  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= FD-002 — recirculation/screen
#image("../drawings/v0.8/FD-002_recirculation_screen.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 304 screen / sheet chute  *핵심 치수/공차:* screen aperture Ø5 on 9 pitch; cutter/static clearance ≥1.90 mm  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= FD-003 — positive feeder
#image("../drawings/v0.8/FD-003_positive_feeder.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 304 auger/housing/common agitator shaft  *핵심 치수/공차:* auger OD24.60; housing ID25.00 +0.05/0; radial clearance 0.20–0.25 mm; shaft/bore diametral clearance0.200–0.322; SYS-15 Ø3x12 spring pin; pitch18  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= EX-001 — extruder assembly
#image("../drawings/v0.8/EX-001_extruder_assembly.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* SCM440 screw/barrel / steel supports  *핵심 치수/공차:* integral barrel shoulder + rear retainer; 2× M4×25 class8.8 at 2.9 N·m; cold endplay 0.12–0.28 mm; front guide axial travel ≥1.50 mm; mount M5×4 = 2.5 N·m  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= EX-002 — screw/barrel/die
#image("../drawings/v0.8/EX-002_screw_barrel_die.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* nitrided SCM440 / NSK 51102 / 17-4PH die insert  *핵심 치수/공차:* cold screw/barrel diametral clearance 0.28–0.32 mm; 51102 pocket clearance0.30–0.35 mm; shaft abutment≥23 mm; housing abutment≤20 mm; shim-set loaded-direction endplay0.05–0.15 mm; coaxiality ≤0.05 mm; thrust M6×8 = 9 N·m; die SYS-04 M4×45×4 stock screws cut/deburred to42.5±0.1 give engagement6.82–7.40/thread-bottom clearance0.60–1.18; digital torque1.50 N·m, physical receipt/leak/first thermal cycle NOT_RUN; retainer M4×2 = 1.2 N·m  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= EX-003 — heater/thermocouple layout
#image("../drawings/v0.8/EX-003_heater_thermocouple.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mica/NiCr heater and thermocouple candidates; TH-INS-01 secondary shield-exterior barrier after S4 qualification  *핵심 치수/공차:* Band free-state ID34.10–34.20 and usable closure≥1.00 leave worst-case closure reserve0.277 mm; after cold tightening, 0.05 mm feeler penetration≤5 mm at 8 sectors excluding split±10° is physical NOT_RUN. HOLD T1–T3: probe unselected; OD tolerance and insertion stop unqualified. Barrel flat-bottom bore5.40±0.05 preserves conservative ligament3.345≥3.32, but does not qualify probe insertion; do not deepen or force probe to bottom. T4 insertion10/blind12 and T5 insertion4 are nominal candidates. Qualify retention, insulation and thermal response before assembly. TH-INS-01 is allowed only on the outside face of the grounded metal hot shield and must not cover heaters, barrel/die, cutoffs, probes, terminals or vents; S4 coupon smoke and P9 interface-temperature margin remain physical gates. SYS-04 die joint digital load-path PASS at1.50 N·m; physical receipt/leak/first thermal cycle NOT_RUN; shield clearance requires service verification.  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= FM-001 — cooling and strand path
#image("../drawings/v0.8/FM-001_cooling_strand_path.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 5052 duct / donor fans  *핵심 치수/공차:* strand centreline offset ≤0.50 mm; hot-shield clearance ≥12 mm  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= FM-002 — gauge/puller
#image("../drawings/v0.8/FM-002_gauge_puller.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 6061 plates / silicone rollers / S45C eccentric bushes  *핵심 치수/공차:* adjusted unloaded roller gap 1.60–1.90 mm over full rotation; bush index pair≤0.5°; roller axes parallel≤0.05/80; gauge datum alignment≤0.10 mm  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= SP-001 — spooler/traverse
#image("../drawings/v0.8/SP-001_spooler_traverse.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 6061 plates / stainless shafts  *핵심 치수/공차:* spool shaft Ø12 h6; traverse rod parallelism ≤0.10/160  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= GD-001 — guards and panels
#image("../drawings/v0.8/GD-001_guards_panels.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* polycarbonate and bonded metal panels  *핵심 치수/공차:* hazard opening ≤6 mm; no reach path to moving/hot parts  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= EL-001 — electrical enclosure
#image("../drawings/v0.8/EL-001_electrical_enclosure.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 2 mm 5052 enclosure  *핵심 치수/공차:* PE bond target 0.10 ohm 이하; signal/power duct separation ≥18 mm  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`

#pagebreak()

= SV-001 — service envelopes
#image("../drawings/v0.8/SV-001_service_envelopes.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* service-envelope reference geometry  *핵심 치수/공차:* front/rear access ≥600 mm; hot-zone removal envelope kept clear  *단위:* mm · 제3각법 · NTS · source `c707bac2084a1e84c4018975cbe1ad37fc0c8a37`
