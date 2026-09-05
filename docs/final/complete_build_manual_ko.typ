#set document(title: "v0.8 실행용 조립 매뉴얼")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= v0.8 실행용 조립 매뉴얼
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `final-design-fabrication-closure-v0.8` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

이 문서와 `assembly_steps.csv`, `assembly_drawing_set.pdf`, `exports/final/manufacturing/`, `exports/final/electrical/`이 v0.8 조립의 단일 실행 기준이다. 구버전 매뉴얼은 적용하지 않는다.

각 단계의 실측값·작업자·검토자·증거 경로를 기록한다. 계산·CAD PASS는 물리 합격이 아니다. 구매·가공·통전·가열 전에는 해당 사용자 승인 gate를 통과해야 한다.

== 단계 1: BOM/revision traveler ×1

- 공구: document viewer; caliper
- 체결품 / 토크: N/A / N/A—document gate
- 방향: v0.8 identifiers visible
- 공차·간극: all files same revision
- 도면: GA-001
- 검사: hash and revision cross-check
- 합격: all required files present
- 다음 선행조건: parts kitting

== 단계 2: FR profiles ×28; corner brackets ×28

- 공구: square; 3/5 mm hex
- 체결품 / 토크: M5x12/washer/T-nut joint kits ×56 / M5 5 N·m
- 방향: 470×700 base square
- 공차·간극: squareness ≤0.50/700 mm
- 도면: FR-001
- 검사: 56 witness marks; diagonal and rocking measurement
- 합격: both diagonals within 1 mm
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

== 단계 4: CUT-03/CUT-08 plates ×2 each

- 공구: square; 5 mm hex
- 체결품 / 토크: M6 class 8.8 / M6 9 N·m
- 방향: bearing datums inward
- 공차·간극: shaft centres 48.00±0.03 mm
- 도면: SH-001
- 검사: CMM/caliper centre distance
- 합격: pair parallel and rigid
- 다음 선행조건: bearings/shafts

== 단계 5: CUT-05 ×2; 6004-2RS ×4

- 공구: arbor press; micrometer
- 체결품 / 토크: metal collars / collar screw per maker
- 방향: drive ends aligned
- 공차·간극: Ø20 h6; TIR≤0.05 mm
- 도면: SH-003
- 검사: micrometer and dial indicator
- 합격: free rotation without preload
- 다음 선행조건: cutter stack

== 단계 6: CUT-01 ×12; CUT-02 ×10

- 공구: shim set; feeler gauge
- 체결품 / 토크: keys and metal shims / collars per drawing
- 방향: hooks counter-rotate; phase offset
- 공차·간극: axial gap 0.25–0.50 mm
- 도면: SH-002
- 검사: hand rotate 20 revolutions
- 합격: no disc/static contact
- 다음 선행조건: phase drive

== 단계 7: DRV-01/A60/F01/02/03 ×1 set

- 공구: straightedge; dial; torque wrench
- 체결품 / 토크: M4/M6 keyed hardware / M4 3 N·m; M6 9 N·m
- 방향: 12T:30T guarded chain
- 공차·간극: alignment≤0.50 mm; slack 2–3%
- 도면: SH-004
- 검사: blue check and hand rotation
- 합격: keyed path; no friction-only joint
- 다음 선행조건: shredder guard

== 단계 8: DRV-GD-01 and interlock ×1

- 공구: 2.5/3 mm hex; gap probe
- 체결품 / 토크: M4 guarded fasteners / M4 3 N·m
- 방향: cover removable only under lockout
- 공차·간극: hazard opening≤6 mm
- 도면: GD-001
- 검사: reach probe and switch actuation
- 합격: no reach path; forced-open works
- 다음 선행조건: feed path

== 단계 9: IN-HOP-01/CUT-04/FD-HOP-01 ×1 set

- 공구: riveter; 3 mm hex
- 체결품 / 토크: M4/rivets / M4 3 N·m
- 방향: flow down into screen
- 공차·간극: cutter/static clearance≥1.90 mm
- 도면: FD-001/FD-002
- 검사: feeler gauge and burr check
- 합격: no sharp edge or cutter contact
- 다음 선행조건: flake bin

== 단계 10: FD-BIN-01/FD-MET-01..03 ×1 set

- 공구: caliper; bore gauge; 2.5 mm hex
- 체결품 / 토크: M3/M4 service hardware / M3 1.2; M4 3 N·m
- 방향: vertical auger removable; paddles above hopper cone
- 공차·간극: auger radial running clearance 0.20–0.25 mm; pitch 18 mm
- 도면: FD-003
- 검사: hand turn through 10 revolutions and cleanout check
- 합격: no rub, dead pocket or inaccessible retained flake
- 다음 선행조건: extruder support

== 단계 11: rear datum/front guide/rail/collar ×1 set

- 공구: dial indicator; 4 mm hex
- 체결품 / 토크: M5 hot-mount hardware / M5 5 N·m
- 방향: rear axial fixed; front radial sliding
- 공차·간극: axis≤0.20/390; travel≥1.30 mm
- 도면: EX-001
- 검사: dial sweep and travel gauge
- 합격: travel and alignment pass
- 다음 선행조건: screw/barrel

== 단계 12: EX-SCR-01/EX-BAR-01 ×1

- 공구: bore gauge; feeler gauge
- 체결품 / 토크: thrust/coupling hardware / drawing-specific
- 방향: feed end to die end
- 공차·간극: cold diametral clearance 0.28–0.32 mm
- 도면: EX-002
- 검사: three-station bore/OD report
- 합격: rotation free; coaxiality≤0.05 mm
- 다음 선행조건: die/hot zone

== 단계 13: EX-DIE-01..05; heater/TC ×1 set

- 공구: insulation meter; torque wrench
- 체결품 / 토크: die fasteners / cross-tighten per drawing
- 방향: TC tips in metal hot path
- 공차·간극: probe insertion≥12 mm; shield gap≥12 mm
- 도면: EX-002/EX-003
- 검사: cold leak-path and continuity inspection
- 합격: all channels identified; physical hot test pending
- 다음 선행조건: cooling path

== 단계 14: CO-01/CO-02 ×1 set

- 공구: calibrated anemometer; 3 mm hex
- 체결품 / 토크: M4 clamps / M4 3 N·m
- 방향: airflow across strand away from hot zone
- 공차·간극: strand centreline≤0.50 mm
- 도면: FM-001
- 검사: route and service removal check
- 합격: no hot contact; feedback wired
- 다음 선행조건: gauge

== 단계 15: gauge mechanism ×1

- 공구: gauge block; caliper
- 체결품 / 토크: M3 hardware / M3 1.2 N·m
- 방향: U95 axes normal to strand
- 공차·간극: datum alignment≤0.10 mm
- 도면: FM-002
- 검사: gauge block repeatability check
- 합격: mechanical repeatability recorded
- 다음 선행조건: puller

== 단계 16: FM-PL/RL/AX/GR/GA ×1 set

- 공구: dial indicator; 3 mm hex
- 체결품 / 토크: M4 plus metal collars / M4 3 N·m
- 방향: roller axes parallel
- 공차·간극: parallel≤0.05/80; TIR≤0.05 mm
- 도면: FM-002
- 검사: hand feed dummy strand
- 합격: no pinch bypass or bind
- 다음 선행조건: spooler

== 단계 17: SP-DA/AX/RL/SH/BP/MM/TR/DS ×1 set

- 공구: square; dial; 3 mm hex
- 체결품 / 토크: M4 plus collars / M4 3 N·m
- 방향: traverse parallel to spool
- 공차·간극: rod parallel≤0.10/160 mm
- 도면: SP-001
- 검사: full-stroke hand traverse
- 합격: no collision in service envelope
- 다음 선행조건: all guards

== 단계 18: GD panels/interlocks ×1 set

- 공구: gap probe; 3 mm hex
- 체결품 / 토크: captive M4 hardware / M4 3 N·m
- 방향: labels outward; service panels keyed
- 공차·간극: openings≤6 mm at hazards
- 도면: GD-001/SV-001
- 검사: reach/access and removal test
- 합격: all hazards covered
- 다음 선행조건: enclosure/PE

== 단계 19: CT-ENC-01 ×1; PE-01..04 bonds ×4

- 공구: DMM; torque wrench
- 체결품 / 토크: M4x10/two tooth washers/all-metal nut ×4 sets / M4 3 N·m
- 방향: PE first; ducts segregated
- 공차·간극: bond target 0.10 ohm 이하; separation≥18 mm
- 도면: EL-001
- 검사: four-wire continuity where available
- 합격: all four bonds and witness marks recorded
- 다음 선행조건: power wiring

== 단계 20: wire/fuse schedules ×1 set

- 공구: crimper; pull tester; DMM
- 체결품 / 토크: listed terminals/ferrules / terminal maker value
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

== 단계 22: Mega/sensors/drivers ×1 set

- 공구: DMM; logic current limiter
- 체결품 / 토크: locking low-voltage terminals / terminal maker value
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
