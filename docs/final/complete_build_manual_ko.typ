#set document(title: "v0.8 실행용 조립 매뉴얼")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= v0.8 실행용 조립 매뉴얼
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
전체 배치: `GGM-FULL-ASM` / 구동계: `GGM R2`. 기본 조립 투상도는 통합 전 참조이며 최신 전체 배치가 아니다.
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

이 문서와 `assembly_steps.csv`, 부품별 제조도면, 전기 schedule을 함께 사용한다. 전체 기계의 최신 배치는 `exports/final/drive_ggm_v08/GGM-FULL-ASM.step` 및 FCStd이며 구동계는 R2 GGM 도면이 우선한다. `assembly_drawing_set.pdf`의 기본 조립 투상도는 GGM 통합 전의 부품 관계 참조다. GGM-R2와 충돌하는 전체 배치·좌표·구동부는 복사하지 않는다. 구버전 매뉴얼은 적용하지 않는다.

각 단계의 실측값·작업자·검토자·증거 경로를 기록한다. 계산·CAD PASS는 물리 합격이 아니다. 구매·가공·통전·가열 전에는 해당 사용자 승인 gate를 통과해야 한다.

부품 수량은 `release/active_part_set.json`의 출고/검사 단위이며 assembly ID는 중복 구매하지 않는 참조다. 공정 witness, qualification coupon과 교체용 gasket은 해당 단계의 설치품과 구분한다. `SYS-*` 체결값은 `release/build_bom_release.py::fasteners`, `PR-*` 값은 `exports/print/print_manifest.csv`에서 BOM과 함께 생성한다. 금속 조인트 기본 토크를 출력물에 적용하지 않는다. 표에 없는 donor/구매품 체결은 수령품 제조사 값과 실측 승인 전 HOLD다.

== 단계 1: EX-CPN-BAR ×1; EX-CPN-SCR ×1; PPR-FULL-ASM ×1; BOM/revision traveler ×1

- 공구: document viewer; caliper
- 체결품 / 토크: N/A / N/A—document gate
- 방향: v0.8 identifiers visible; EX-CPN-BAR/EX-CPN-SCR are process witnesses, not installed parts
- 공차·간극: all files same revision
- 도면: GA-001
- 검사: hash and revision cross-check
- 합격: all required files present
- 다음 선행조건: parts kitting

== 단계 2: PPR-FRAME-ASM ×1; FR profiles ×28; corner brackets ×28

- 공구: square; long steel tape/rule; 3/5 mm hex
- 체결품 / 토크: SYS-01: M5x12 SHCS + washer + prevailing T-nut; 56 kits paired across 28 two-fastener corner brackets ×56 / SYS-01: 5.0 N·m
- 방향: 470×700 base square
- 공차·간극: base X470±0.8 mm; Y700±0.8 mm; rail squareness≤0.50/700 mm; all numeric limits include U95
- 도면: FR-001
- 검사: 56 witness marks; independent X/Y and two-diagonal measurements with evidence hash; rocking check
- 합격: |diagonal A-B|+U95_A+U95_B≤1.0 mm; no rocking
- 다음 선행조건: table anchors

== 단계 3: FR-ANCHOR-01 ×4

- 공구: 8 mm socket; torque wrench
- 체결품 / 토크: M8 anchors ×4 / M8 20 N·m provisional
- 방향: load path into table
- 공차·간극: no gap; frame level ≤0.5°
- 도면: FR-001
- 검사: witness mark and level
- 합격: four anchors engaged
- 다음 선행조건: shredder frame

== 단계 4: CUT-03 ×2; CUT-08 ×2; CUT-09 ×4; PPR-SHREDDER-ASM ×1

- 공구: square; 3/5 mm hex; 10 mm socket/spanner; torque wrench
- 체결품 / 토크: SYS-06: M4x12 class 8.8 SHCS ×12 / SYS-06: 3 N·m
- 방향: bearing datums inward; four CUT-09 steel sleeves span the128 mm inner-face gap; four chamber ties pass through both CUT-03 plates and sleeves; upper two also pass through PPR-C02 clearance holes without clamping the polymer; each plate mounts to two G1J-10 steel feet and the feet mount to G1J-01/profile
- 공차·간극: shaft centres48.00±0.03 mm; inside plate gap128.00±0.06 mm; four-sleeve matched length spread≤0.03 mm; plate perpendicularity≤0.20/125
- 도면: SH-001/SH-003
- 검사: CMM/caliper centre distance and inside gap at four tie positions; verify every sleeve is metal-to-metal seated; 12 retainer +4 tie +16 foot-joint witness marks
- 합격: pair parallel; retainer clears seal/inner ring; no printed part lies in chamber or plate-to-profile compression path
- 다음 선행조건: bearings/shafts dry-fit

== 단계 5: CUT-05 ×1; CUT-05R ×1; CUT-10 ×4; SKF 61905-2RS1 ×4

- 공구: arbor press; micrometer; optical index
- 체결품 / 토크: Ø25 metal collars / collar screw per maker
- 방향: left key datum0°; right all-key datum25.714°
- 공차·간극: Ø25 h6; key clock±0.02°; TIR≤0.05 mm
- 도면: SH-003
- 검사: micrometer, optical comparator and dial indicator
- 합격: free rotation without preload; CUT-10 contacts outer ring only
- 다음 선행조건: cutter stack

== 단계 6: CUT-01 ×12; CUT-02 ×10; CUT-06 ×2

- 공구: shim set; feeler gauge
- 체결품 / 토크: keys and 0.05/0.10/0.25 mm metal shims / collars per drawing
- 방향: install each spacer at its engraved shaft/position; hooks counter-rotate; phase offset
- 공차·간극: all 11 axial gaps 0.25–0.50 mm over one full rotation
- 도면: SH-002
- 검사: feeler sweep every gap, then hand rotate 20 revolutions; record position map
- 합격: all gaps accepted; no disc/static contact
- 다음 선행조건: phase drive

== 단계 7: DRV-03 ×1; DRV-03R ×1; GGM_JackInnerSpacer_front ×1; GGM_JackInnerSpacer_pinionfront ×1; GGM_JackInnerSpacer_pinionrear ×1; GGM_JackInnerSpacer_rear ×1; GGM_SH_12T ×1; GGM_SH_30T ×1; GGM_SH_Angle201 ×1; GGM_SH_Angle83 ×1; GGM_SH_Base ×1; GGM_SH_BearingCap271 ×1; GGM_SH_BearingCap283 ×1; GGM_SH_BearingCap301 ×1; GGM_SH_BearingCap313 ×1; GGM_SH_BearingPlate273 ×1; GGM_SH_BearingPlate303 ×1; GGM_SH_CutterKey ×1; GGM_SH_FuseInput ×1; GGM_SH_FuseOutput ×1; GGM_SH_FusePinBlank ×1; GGM_SH_JackInputKey ×1; GGM_SH_JackSprocketKey ×1; GGM_SH_Jackshaft ×1; GGM_SH_MotorKey ×1; GGM_SH_Mount ×1; GGM_SH_Spacer_220_100 ×1; GGM_SH_Spacer_220_280 ×1; GGM_SH_Spacer_90_100 ×1; GGM_SH_Spacer_90_280 ×1

- 공구: straightedge; dial indicator; optical index; torque wrench; receipt packet
- 체결품 / 토크: SYS-08: M4x22 class 10.9 SHCS ×4; SYS-09: received sprocket maker axial-retention hardware; 4x4/6x6 keys carry torque ×2 / SYS-08: 3 N·m; SYS-09: HOLD N·m
- 방향: K9DG60N2+K9G75C → keyed GGM protection coupling → 6201-supported jackshaft → direct-keyed GGM_SH_12T:#35:GGM_SH_30T → CUT-05R; 4x4/6x6 keys carry sprocket torque; DRV-03/DRV-03R retain cutter phase; DRV-02 is superseded
- 공차·간극: GGM mount as-drawn compatibility required; pair backlash0.120–0.140 mm; combined digital phase≤1.0°; sprocket radial TIR≤0.10 mm; sprocket total axial shift+U95≤0.20 mm; chain alignment≤0.20/150 mm; midspan slack2–3%; no tight spot in20 hand turns
- 도면: SH-004 + GGM drive contract/component register
- 검사: authenticated GGM receipt/mount result; received sprocket bore/key/retention identity; blue-check key flank contact; axial-shift and radial-TIR dial checks; optical clocking; hand rotation; P3 current/torque/protection evidence; SYS-09: blue-check key flank; no friction-only/set-screw-only torque path; each sprocket radial TIR <=0.10 mm; total axial shift+U95 <=0.20 mm; chain alignment <=0.20/150 mm
- 합격: HOLD: 미검증 체결품이 있어 조립 합격 불가; HOLD: GGM receipt/mount, keyed sprocket axial retention and P3 physical bench remain NOT_RUN; friction-only/set-screw-only torque path prohibited
- 다음 선행조건: 진행 금지: 체결 규격·토크 검증 및 승인 후 다음 단계

== 단계 8: DRV-GD-01 ×1; GGM_ChainGuard ×1; GGM_SH_CouplingGuard ×1

- 공구: 2.5/3 mm hex; gap probe
- 체결품 / 토크: M4 guarded fasteners / M4 3 N·m
- 방향: cover removable only under lockout
- 공차·간극: hazard opening≤6 mm
- 도면: GD-001
- 검사: reach probe and switch actuation
- 합격: no reach path; forced-open works
- 다음 선행조건: feed path

== 단계 9: CUT-04 ×2; FD-HOP-01 ×1; IN-HOP-01 ×1; PPR-C01 ×1; PPR-C02 ×1; PPR-C04 ×1

- 공구: riveter; 3 mm hex
- 체결품 / 토크: non-printed interfaces only: M4/rivets; PR-PPR-C01-1: M4x10 latch flag screw ×1; PR-PPR-C02-1: M4x12 + washer ×4; PR-PPR-C02-2: chamber M6 tie bolts through clearance holes ×2; PR-PPR-C04-1: M5x16 + large washer + nyloc ×2 / non-printed interfaces only: M4 3 N·m; PR-PPR-C01-1: 1.2 N·m; PR-PPR-C02-1: 1.2 N·m; PR-PPR-C02-2: 6 N·m; PR-PPR-C04-1: 2.0 N·m
- 방향: flow down into screen
- 공차·간극: cutter/static clearance≥1.90 mm
- 도면: FD-001/FD-002
- 검사: feeler gauge and burr check
- 합격: no sharp edge or cutter contact
- 다음 선행조건: flake bin

== 단계 10: FD-BIN-01 ×1; FD-CP-01 ×1; FD-DA-01 ×1; FD-GSK-01 ×2; FD-MET-01 ×1; FD-MET-02 ×1; FD-MET-03 ×1; PPR-C03 ×4; PPR-FEEDER-ASM ×1

- 공구: caliper; bore gauge; 3 mm pin punch; dial indicator
- 체결품 / 토크: PR-PPR-C03-1: M3x8 + washer + nyloc ×8; SYS-12: M4x16 A2-70 SHCS + washer + all-metal prevailing nut ×4; SYS-15: 420 stainless slotted spring pins: Ø3x12 lower + Ø3x18 upper ×2 / PR-PPR-C03-1: 0.5 N·m; SYS-12: HOLD N·m; SYS-15: N/A N·m
- 방향: key EG17-G10 into FD-CP-01; install both matched pins; bolt FD-DA-01 only to metal frame
- 공차·간극: auger radial clearance0.20–0.25; coupling diametral clearance0.050–0.102; gearbox axis≤0.10 mm
- 도면: FD-003
- 검사: pin gauge/micrometer; coupling TIR; 10 hand turns; 2.2 N.m torque-arm and 24 PPR tach test; SYS-12: register clearance0.10-0.16; tighten crosswise only until gasket thickness0.35-0.40; dry-flake leak/retention test required
- 합격: HOLD: 미검증 체결품이 있어 조립 합격 불가; digital reference defined; purchase/receipt and physical tests remain HOLD
- 다음 선행조건: 진행 금지: 체결 규격·토크 검증 및 승인 후 다음 단계

== 단계 11: ExtruderFixedCollar ×1; ExtruderFrontSlidingGuide ×1; ExtruderRearFixedDatum ×1; ExtruderRearRetainer ×1; ExtruderRearRetainerSpacer318 ×2; ExtruderSupportRailRear ×1; PPR-EXTRUDER-ASM ×1

- 공구: dial indicator; 3/4 mm hex; torque wrench
- 체결품 / 토크: SYS-07: M5 profile fastener ×4; SYS-10: M4x25 class 8.8 SHCS ×2 / SYS-07: 2.5 N·m; SYS-10: 2.9 N·m
- 방향: integral shoulder captured by rear retainer through 4.20 mm matched spacers; front radial sliding
- 공차·간극: axis≤0.20/390; cold axial free travel≥1.50 mm; cold endplay 0.12–0.28 mm; first thermal cycle hard-stop contact 0
- 도면: EX-001
- 검사: dial sweep, feeler/endplay and travel gauge; record material certificate and torque witness; first authorized thermal cycle records axial motion/hard-stop clearance
- 합격: digital geometry/strength PASS; physical endplay, preload retention and thermal-cycle inspection NOT_RUN
- 다음 선행조건: physical inspection approval before screw/barrel

== 단계 12: EX-BAR-01 ×1; EX-SCR-01 ×1; EX-THR-01 ×1; GGM_EX_CouplingGuard ×1; GGM_EX_FuseInput ×1; GGM_EX_FuseOutput ×1; GGM_EX_FusePinBlank ×1; GGM_EX_MotorKey ×1; GGM_EX_Mount ×1; GGM_EX_RadialCap ×1; GGM_EX_RadialHolder ×1; GGM_EX_ScrewKey ×1

- 공구: micrometer; bore/depth gauge; dial indicator; torque wrench; receipt packet
- 체결품 / 토크: SYS-03: M6x20 class 8.8 ×8 / SYS-03: 9 N·m
- 방향: 51102 shaft washer against integral Ø23 shoulder; housing washer in marked-face pocket; K9DG60N2+K9G150C direct keyed protection coupling with 6201 rear radial support; gearbox carries no extrusion thrust
- 공차·간극: screw/barrel diametral0.28–0.32 mm; pocket diametral0.30–0.35 mm; loaded-direction endplay0.05–0.15 mm; GGM mount as-drawn compatibility required
- 도면: EX-002 + GGM manufacturing r2
- 검사: bearing marking/height, seat/pocket/abutment limits, blue-check washer ribs, three-station bore/OD, dial endplay/free rotation, authenticated GGM receipt/mount result and P3 drive evidence
- 합격: HOLD: digital dimensions PASS; GGM receipt/mount/P3 drive evidence, physical endplay and hot rotation remain NOT_RUN
- 다음 선행조건: die/hot zone

== 단계 13: EX-DIE-01 ×1; EX-DIE-02 ×1; EX-DIE-03 ×1; EX-DIE-04 ×1; EX-DIE-05 ×2; EX-SH-01 ×1; TH-BH-01 ×3

- 공구: insulation meter; torque wrench; depth gauge; 0.05 mm feeler; 20 N pull gauge
- 체결품 / 토크: SYS-04: M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1 ×4; SYS-05: M4 retainer screw ×2; SYS-16: 2x M3x8 A4-80 SHCS + Schnorr washer ×2; SYS-17: M3x8 A4-80 SHCS + Schnorr washer ×8 / SYS-04: 1.5 N·m; SYS-05: 1.2 N·m; SYS-16: 1.0 N·m; SYS-17: 0.5 N·m
- 방향: band free-state ID34.10–34.20; usable closure≥1.00; EX-DIE-05 issued2; TH-TC-01 Tempco MTA1 T1–T4 with supplier-welded stops
- 공차·간극: band closure reserve≥0.25 mm; T1–T3 probe Ø3.00±0.03 in bore3.20–3.25, stop5.20±0.05, tip gap0.10–0.30; T4 stop10.00±0.05 in depth11.95–12.05; TH-TCR-01 bridge captures collar; never clamp MI sheath
- 도면: EX-002/EX-003
- 검사: verify band contact; vendor drawing; probe dimensions and ≥100 MΩ at100 VDC; 20 N pull motion≤0.10 cold/hot; coupon bias≤2°C and t90≤30s; SYS-04 physical receipt/leak/first thermal cycle remains NOT_RUN
- 합격: HOLD: supplier drawing, receipt/thermal tests and band contact; SYS-04 digital load-path PASS but physical receipt/leak/first thermal cycle NOT_RUN
- 다음 선행조건: 센서 수령시험 및 체결 HOLD 해소 전 다음 단계 진행 금지

== 단계 14: PPR-C05 ×2; PPR-FORMING-ASM ×1

- 공구: calibrated anemometer; 3 mm hex
- 체결품 / 토크: non-printed interfaces only: M4 clamps; PR-PPR-C05-1: M4x12 + washer + nyloc ×16 / non-printed interfaces only: M4 3 N·m; PR-PPR-C05-1: 1.2 N·m
- 방향: airflow across strand away from hot zone
- 공차·간극: strand centreline≤0.50 mm
- 도면: FM-001
- 검사: route and service removal check
- 합격: no hot contact; feedback wired
- 다음 선행조건: gauge

== 단계 15: PPR-C06 ×2

- 공구: gauge block; caliper
- 체결품 / 토크: non-printed interfaces only: M3 hardware; PR-PPR-C06-1: M3x12 ×8 / non-printed interfaces only: M3 1.2 N·m; PR-PPR-C06-1: 0.5 N·m
- 방향: U95 axes normal to strand
- 공차·간극: datum alignment≤0.10 mm
- 도면: FM-002
- 검사: gauge block repeatability check
- 합격: mechanical repeatability recorded
- 다음 선행조건: puller

== 단계 16: FM-AX-01 ×2; FM-EB-01 ×2; FM-PL-01 ×2; FM-RL-01 ×2; PPR-C07 ×1

- 공구: feeler gauge; dial indicator; 2.5/3 mm hex
- 체결품 / 토크: PR-PPR-C07-1: M4 captive screws ×4; SYS-11: M3x10 class 8.8 SHCS ×4 / PR-PPR-C07-1: 1.2 N·m; SYS-11: 1.2 N·m
- 방향: FM-EB-01 pair at equal index; fixed and adjustable roller axes parallel
- 공차·간극: unloaded full-rotation gap1.60–1.90 mm; bush index pair≤0.5°; parallel≤0.05/80; TIR≤0.05 mm
- 도면: FM-002
- 검사: feeler sweep over one full rotation, index and hand-feed check
- 합격: gap remains in range; no pinch bypass, bush slip or bind
- 다음 선행조건: spooler

== 단계 17: FM-GA-01 ×1; FM-GC-01 ×2; FM-GR-01 ×1; PPR-C08 ×2; PPR-C09 ×2; PPR-C10 ×1; SP-AX-01 ×2; SP-BP-01 ×2; SP-BR-01 ×2; SP-DA-01 ×1; SP-DS-01 ×1; SP-MM-01 ×1; SP-RL-01 ×1; SP-SH-01 ×1; SP-TR-01 ×2

- 공구: square; dial; 3 mm hex
- 체결품 / 토크: PR-PPR-C08-1: M5x16 + washer + T-nut ×4; PR-PPR-C09-1: M6x30 through clamp + washer + nyloc ×2; PR-PPR-C10-1: M4x16 belt-clamp screws ×2; SYS-13: M5x20 A2-70 SHCS + washer + all-metal prevailing nut ×8; SYS-14: M3x25 A2-70 SHCS + washers + all-metal prevailing nuts ×3 / PR-PPR-C08-1: 2.0 N·m; PR-PPR-C09-1: 2.5 N·m; PR-PPR-C10-1: 1.2 N·m; SYS-13: 2.5 N·m; SYS-14: 0.35 N·m
- 방향: traverse parallel to spool
- 공차·간극: rod parallel≤0.10/160 mm
- 도면: SP-001
- 검사: full-stroke hand traverse
- 합격: no collision in service envelope
- 다음 선행조건: all guards

== 단계 18: GD panels/interlocks ×1 set; TH-INS-01 qualified shield-exterior cut set ×1

- 공구: gap probe; 3 mm hex; scissors/roller for qualified tape
- 체결품 / 토크: captive M4 hardware; tape has no structural/safety fastener role / M4 3 N·m; tape N/A
- 방향: labels outward; service panels keyed; TH-INS-01 only on outside face of grounded metal hot shield after S4 coupon PASS; no heater/barrel/die/cutoff/probe/terminal/vent coverage
- 공차·간극: openings≤6 mm at hazards; tape adhesive-interface peak+U95+30 C≤documented continuous rating; cooldown edge lift+U95≤2.0 mm
- 도면: GD-001/SV-001 + control/thermal_barrier_tape_contract.json
- 검사: reach/access/removal test; S4 coupon evidence; P9 interface/outer-surface temperature and cooldown edge-lift record
- 합격: all hazards covered; no smoke/char/melt/adhesive flow; tape does not obstruct sensing, cutoff, terminals or ventilation
- 다음 선행조건: enclosure/PE

== 단계 19: CT-ENC-01 ×1; PE-01..04 bonds ×4

- 공구: DMM; torque wrench
- 체결품 / 토크: SYS-02: M4x10 + two tooth washers + all-metal nut per bond ×4 / SYS-02: 3.0 N·m
- 방향: PE first; ducts segregated
- 공차·간극: bond target 0.10 ohm 이하; separation≥18 mm
- 도면: EL-001
- 검사: four-wire continuity where available
- 합격: all four bonds and witness marks recorded
- 다음 선행조건: power wiring

== 단계 20: PPR-C12 ×8

- 공구: crimper; pull tester; DMM
- 체결품 / 토크: non-printed interfaces only: listed terminals/ferrules; PR-PPR-C12-1: M4x10 + profile T-nut ×8 / non-printed interfaces only: terminal maker value; PR-PPR-C12-1: 1.0 N·m
- 방향: power and signal in separate ducts
- 공차·간극: gauge/temperature/routing per schedule
- 도면: electrical PDFs
- 검사: 100% point-to-point and pull test
- 합격: all IDs and polarities pass
- 다음 선행조건: hard safety chain

== 단계 21: E-stop/lid/service/thermal chain ×1

- 공구: DMM; insulated probe
- 체결품 / 토크: locking safety terminals / terminal maker value
- 방향: normally-safe series chain
- 공차·간극: each open removes coil energy
- 도면: safety_chain.pdf
- 검사: de-energized forced-open continuity
- 합격: firmware cannot bypass
- 다음 선행조건: logic wiring

== 단계 22: PPR-C11 ×1

- 공구: DMM; logic current limiter
- 체결품 / 토크: non-printed interfaces only: locking low-voltage terminals; PR-PPR-C11-1: M3x10 ×4 / non-printed interfaces only: terminal maker value; PR-PPR-C11-1: 0.5 N·m
- 방향: outputs safe at reset
- 공차·간극: pin schedule exact match
- 도면: Arduino_Mega_pinmap.pdf
- 검사: source-to-pin point check
- 합격: no hazardous enable asserted
- 다음 선행조건: firmware flash

== 단계 23: released HEX/source ×1

- 공구: USB programmer; hash tool
- 체결품 / 토크: N/A / N/A—software gate
- 방향: Mega 2560 target
- 공차·간극: binary SHA equals build manifest
- 도면: firmware_and_calibration_ko.pdf
- 검사: clean build and readback hash
- 합격: reproducible build PASS
- 다음 선행조건: calibration

== 단계 24: sensor/actuator calibration records ×1 set

- 공구: reference loads/gauges
- 체결품 / 토크: N/A / N/A—calibration gate
- 방향: one subsystem at a time
- 공차·간극: range/unit/CRC/revision valid
- 도면: firmware_and_calibration_ko.pdf
- 검사: bounded calibration routine
- 합격: invalid data forces safe state
- 다음 선행조건: pre-power signoff

== 단계 25: complete assembly traveler ×1

- 공구: checklist; camera; DMM
- 체결품 / 토크: all witness marks / verify recorded values
- 방향: machine locked out
- 공차·간극: all prior tolerances PASS
- 도면: pre_power_checklist_ko.pdf
- 검사: independent review and photo record
- 합격: physical state remains NOT_RUN
- 다음 선행조건: explicit user commissioning approval
