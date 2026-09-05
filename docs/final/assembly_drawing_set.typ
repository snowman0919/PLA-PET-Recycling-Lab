#set document(title: "v0.8 치수·검사 조립 도면 세트")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= v0.8 치수·검사 조립 도면 세트
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

= GA-001 — general arrangement
#image("../drawings/v0.8/GA-001_general_arrangement.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mixed assembly; see BOM.csv  *핵심 치수/공차:* 470 × 700 × 930 mm envelope; service aisle ≥600 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= ASM-001 — full assembly
#image("../drawings/v0.8/ASM-001_full_assembly.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mixed assembly; see BOM.csv  *핵심 치수/공차:* high-load path cutter/screw → metal bearing plate → profile → table  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= ASM-002 — module arrangement
#image("../drawings/v0.8/ASM-002_module_arrangement.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mixed assembly; see BOM.csv  *핵심 치수/공차:* module datum transfer ≤0.50 mm; service modules removable without hot-path disturbance  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= FR-001 — frame
#image("../drawings/v0.8/FR-001_frame.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 2020/2040 aluminum profile  *핵심 치수/공차:* base 470 × 700 mm; anchor M8 ×4; rail squareness ≤0.50/700  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= SH-001 — shredder assembly
#image("../drawings/v0.8/SH-001_shredder_assembly.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* steel cutter module  *핵심 치수/공차:* shaft centres 48.00 ±0.03 mm; rotating-to-static clearance ≥1.90 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= SH-002 — cutter stack
#image("../drawings/v0.8/SH-002_cutter_stack.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* D2 cutters / steel spacers  *핵심 치수/공차:* CUT-01 t6 and CUT-02 t7; axial gap 0.25–0.50 mm by metal shim  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= SH-003 — shaft and bearing assembly
#image("../drawings/v0.8/SH-003_shaft_bearing.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* S45C shafts / 6004-2RS  *핵심 치수/공차:* Ø20 h6 seats; shaft TIR ≤0.05 mm; centre parallelism ≤0.10/150  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= SH-004 — chain and phase gear
#image("../drawings/v0.8/SH-004_chain_phase_gear.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* S45C keyed hubs/gears / #35 chain  *핵심 치수/공차:* 12T:30T; chain alignment ≤0.50 mm; midspan slack 2–3%  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= FD-001 — hopper
#image("../drawings/v0.8/FD-001_hopper.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 5052-H32 hopper  *핵심 치수/공차:* feed opening 150 × 150 mm; all reachable edges R/C ≥0.5 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= FD-002 — recirculation/screen
#image("../drawings/v0.8/FD-002_recirculation_screen.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 304 screen / sheet chute  *핵심 치수/공차:* screen aperture Ø5 on 9 pitch; cutter/static clearance ≥1.90 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= FD-003 — positive feeder
#image("../drawings/v0.8/FD-003_positive_feeder.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 304 auger/housing/common agitator shaft  *핵심 치수/공차:* auger OD24.60; housing ID25.00 +0.05/0; radial clearance 0.20–0.25 mm; pitch18  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= EX-001 — extruder assembly
#image("../drawings/v0.8/EX-001_extruder_assembly.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* SCM440 screw/barrel / steel supports  *핵심 치수/공차:* rear axial datum fixed; front guide axial travel ≥1.30 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= EX-002 — screw/barrel/die
#image("../drawings/v0.8/EX-002_screw_barrel_die.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* nitrided SCM440 / 17-4PH die insert  *핵심 치수/공차:* cold diametral clearance 0.28–0.32 mm; coaxiality ≤0.05 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= EX-003 — heater/thermocouple layout
#image("../drawings/v0.8/EX-003_heater_thermocouple.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* mica/NiCr heater and MI thermocouple  *핵심 치수/공차:* probe insertion ≥12 mm; heater-to-polymer path metal-only; shield clearance ≥12 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= FM-001 — cooling and strand path
#image("../drawings/v0.8/FM-001_cooling_strand_path.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 5052 duct / donor fans  *핵심 치수/공차:* strand centreline offset ≤0.50 mm; hot-shield clearance ≥12 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= FM-002 — gauge/puller
#image("../drawings/v0.8/FM-002_gauge_puller.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 6061 plates / POM-C rollers  *핵심 치수/공차:* roller axes parallel ≤0.05/80; gauge datum alignment ≤0.10 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= SP-001 — spooler/traverse
#image("../drawings/v0.8/SP-001_spooler_traverse.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 6061 plates / stainless shafts  *핵심 치수/공차:* spool shaft Ø12 h6; traverse rod parallelism ≤0.10/160  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= GD-001 — guards and panels
#image("../drawings/v0.8/GD-001_guards_panels.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* polycarbonate and bonded metal panels  *핵심 치수/공차:* hazard opening ≤6 mm; no reach path to moving/hot parts  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= EL-001 — electrical enclosure
#image("../drawings/v0.8/EL-001_electrical_enclosure.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* 2 mm 5052 enclosure  *핵심 치수/공차:* PE bond target 0.10 ohm 이하; signal/power duct separation ≥18 mm  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`

#pagebreak()

= SV-001 — service envelopes
#image("../drawings/v0.8/SV-001_service_envelopes.svg", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* service-envelope reference geometry  *핵심 치수/공차:* front/rear access ≥600 mm; hot-zone removal envelope kept clear  *단위:* mm · 제3각법 · NTS · source `adc8bec89d946f696c179d79b1af2c401189ab35`
