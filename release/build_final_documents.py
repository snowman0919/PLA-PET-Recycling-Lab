#!/usr/bin/env python3
"""v0.8 최종 벡터 도면, 전장 schedule, 매뉴얼과 시운전 문서를 생성한다."""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/final"
DRAW = ROOT / "docs/drawings"
ELEC = ROOT / "exports/final/electrical"
REV = "final-design-fabrication-closure-v0.8"

DRAWINGS = [
    ("GA-001", "general arrangement", "GA-001_general_arrangement.svg"),
    ("ASM-001", "full assembly", "ASM-001_full_assembly.svg"),
    ("ASM-002", "module arrangement", "ASM-002_module_arrangement.svg"),
    ("FR-001", "frame", "FR-001_frame.svg"),
    ("SH-001", "shredder assembly", "SH-001_shredder_assembly.svg"),
    ("SH-002", "cutter stack", "SH-002_cutter_stack.svg"),
    ("SH-003", "shaft and bearing assembly", "SH-003_shaft_bearing.svg"),
    ("SH-004", "chain and phase gear", "SH-004_chain_phase_gear.svg"),
    ("FD-001", "hopper", "FD-001_hopper.svg"),
    ("FD-002", "recirculation/screen", "FD-002_recirculation_screen.svg"),
    ("FD-003", "positive feeder", "FD-003_positive_feeder.svg"),
    ("EX-001", "extruder assembly", "EX-001_extruder_assembly.svg"),
    ("EX-002", "screw/barrel/die", "EX-002_screw_barrel_die.svg"),
    ("EX-003", "heater/thermocouple layout", "EX-003_heater_thermocouple.svg"),
    ("FM-001", "cooling and strand path", "FM-001_cooling_strand_path.svg"),
    ("FM-002", "gauge/puller", "FM-002_gauge_puller.svg"),
    ("SP-001", "spooler/traverse", "SP-001_spooler_traverse.svg"),
    ("GD-001", "guards and panels", "GD-001_guards_panels.svg"),
    ("EL-001", "electrical enclosure", "EL-001_electrical_enclosure.svg"),
    ("SV-001", "service envelopes", "SV-001_service_envelopes.svg"),
]

DRAWING_META = {
    "GA-001": ("mixed assembly; see BOM.csv", "470 × 700 × 930 mm envelope; service aisle ≥600 mm"),
    "ASM-001": ("mixed assembly; see BOM.csv", "high-load path cutter/screw → metal bearing plate → profile → table"),
    "ASM-002": ("mixed assembly; see BOM.csv", "module datum transfer ≤0.50 mm; service modules removable without hot-path disturbance"),
    "FR-001": ("2020/2040 aluminum profile", "base 470 × 700 mm; anchor M8 ×4; rail squareness ≤0.50/700"),
    "SH-001": ("steel cutter module", "shaft centres 48.00 ±0.03 mm; rotating-to-static clearance ≥1.90 mm"),
    "SH-002": ("D2 cutters / steel spacers", "CUT-01 t6 and CUT-02 t7; axial gap 0.25–0.50 mm by metal shim"),
    "SH-003": ("S45C shafts / 6004-2RS", "Ø20 h6 seats; shaft TIR ≤0.05 mm; centre parallelism ≤0.10/150"),
    "SH-004": ("S45C keyed hubs/gears / #35 chain", "12T:30T; chain alignment ≤0.50 mm; midspan slack 2–3%"),
    "FD-001": ("5052-H32 hopper", "feed opening 150 × 150 mm; all reachable edges R/C ≥0.5 mm"),
    "FD-002": ("304 screen / sheet chute", "screen aperture Ø5 on 9 pitch; cutter/static clearance ≥1.90 mm"),
    "FD-003": ("304 auger/housing/common agitator shaft", "auger OD24.60; housing ID25.00 +0.05/0; radial clearance 0.20–0.25 mm; pitch18"),
    "EX-001": ("SCM440 screw/barrel / steel supports", "rear axial datum fixed; front guide axial travel ≥1.30 mm"),
    "EX-002": ("nitrided SCM440 / 17-4PH die insert", "cold diametral clearance 0.28–0.32 mm; coaxiality ≤0.05 mm"),
    "EX-003": ("mica/NiCr heater and MI thermocouple", "probe insertion ≥12 mm; heater-to-polymer path metal-only; shield clearance ≥12 mm"),
    "FM-001": ("5052 duct / donor fans", "strand centreline offset ≤0.50 mm; hot-shield clearance ≥12 mm"),
    "FM-002": ("6061 plates / POM-C rollers", "roller axes parallel ≤0.05/80; gauge datum alignment ≤0.10 mm"),
    "SP-001": ("6061 plates / stainless shafts", "spool shaft Ø12 h6; traverse rod parallelism ≤0.10/160"),
    "GD-001": ("polycarbonate and bonded metal panels", "hazard opening ≤6 mm; no reach path to moving/hot parts"),
    "EL-001": ("2 mm 5052 enclosure", "PE bond target 0.10 ohm 이하; signal/power duct separation ≥18 mm"),
    "SV-001": ("service-envelope reference geometry", "front/rear access ≥600 mm; hot-zone removal envelope kept clear"),
}

ASSEMBLY_FIELDS = ("step_number", "part_ids_quantity", "required_tools", "fasteners", "torque", "orientation", "clearance_tolerance", "drawing", "inspection_method", "pass_fail", "next_prerequisite")
ASSEMBLY_STEPS = [
    (1, "BOM/revision traveler ×1", "document viewer; caliper", "N/A", "N/A—document gate", "v0.8 identifiers visible", "all files same revision", "GA-001", "hash and revision cross-check", "all required files present", "parts kitting"),
    (2, "FR profiles and brackets ×1 set", "square; 3/5 mm hex", "M5 profile joints", "M5 5 N·m", "470×700 base square", "squareness ≤0.50/700 mm", "FR-001", "diagonal and rocking measurement", "both diagonals within 1 mm", "table anchors"),
    (3, "FR-ANCHOR-01 ×4", "8 mm socket; torque wrench", "M8 anchors ×4", "M8 20 N·m provisional", "load path into table", "no gap; frame level ≤0.5°", "FR-001", "witness mark and level", "four anchors engaged", "shredder frame"),
    (4, "CUT-03/CUT-08 plates ×2 each", "square; 5 mm hex", "M6 class 8.8", "M6 9 N·m", "bearing datums inward", "shaft centres 48.00±0.03 mm", "SH-001", "CMM/caliper centre distance", "pair parallel and rigid", "bearings/shafts"),
    (5, "CUT-05 ×2; 6004-2RS ×4", "arbor press; micrometer", "metal collars", "collar screw per maker", "drive ends aligned", "Ø20 h6; TIR≤0.05 mm", "SH-003", "micrometer and dial indicator", "free rotation without preload", "cutter stack"),
    (6, "CUT-01 ×12; CUT-02 ×10", "shim set; feeler gauge", "keys and metal shims", "collars per drawing", "hooks counter-rotate; phase offset", "axial gap 0.25–0.50 mm", "SH-002", "hand rotate 20 revolutions", "no disc/static contact", "phase drive"),
    (7, "DRV-01/A60/F01/02/03 ×1 set", "straightedge; dial; torque wrench", "M4/M6 keyed hardware", "M4 3 N·m; M6 9 N·m", "12T:30T guarded chain", "alignment≤0.50 mm; slack 2–3%", "SH-004", "blue check and hand rotation", "keyed path; no friction-only joint", "shredder guard"),
    (8, "DRV-GD-01 and interlock ×1", "2.5/3 mm hex; gap probe", "M4 guarded fasteners", "M4 3 N·m", "cover removable only under lockout", "hazard opening≤6 mm", "GD-001", "reach probe and switch actuation", "no reach path; forced-open works", "feed path"),
    (9, "IN-HOP-01/CUT-04/FD-HOP-01 ×1 set", "riveter; 3 mm hex", "M4/rivets", "M4 3 N·m", "flow down into screen", "cutter/static clearance≥1.90 mm", "FD-001/FD-002", "feeler gauge and burr check", "no sharp edge or cutter contact", "flake bin"),
    (10, "FD-BIN-01/FD-MET-01..03 ×1 set", "caliper; bore gauge; 2.5 mm hex", "M3/M4 service hardware", "M3 1.2; M4 3 N·m", "vertical auger removable; paddles above hopper cone", "auger radial running clearance 0.20–0.25 mm; pitch 18 mm", "FD-003", "hand turn through 10 revolutions and cleanout check", "no rub, dead pocket or inaccessible retained flake", "extruder support"),
    (11, "rear datum/front guide/rail/collar ×1 set", "dial indicator; 4 mm hex", "M5 hot-mount hardware", "M5 5 N·m", "rear axial fixed; front radial sliding", "axis≤0.20/390; travel≥1.30 mm", "EX-001", "dial sweep and travel gauge", "travel and alignment pass", "screw/barrel"),
    (12, "EX-SCR-01/EX-BAR-01 ×1", "bore gauge; feeler gauge", "thrust/coupling hardware", "drawing-specific", "feed end to die end", "cold diametral clearance 0.28–0.32 mm", "EX-002", "three-station bore/OD report", "rotation free; coaxiality≤0.05 mm", "die/hot zone"),
    (13, "EX-DIE-01..05; heater/TC ×1 set", "insulation meter; torque wrench", "die fasteners", "cross-tighten per drawing", "TC tips in metal hot path", "probe insertion≥12 mm; shield gap≥12 mm", "EX-002/EX-003", "cold leak-path and continuity inspection", "all channels identified; physical hot test pending", "cooling path"),
    (14, "CO-01/CO-02 ×1 set", "calibrated anemometer; 3 mm hex", "M4 clamps", "M4 3 N·m", "airflow across strand away from hot zone", "strand centreline≤0.50 mm", "FM-001", "route and service removal check", "no hot contact; feedback wired", "gauge"),
    (15, "gauge mechanism ×1", "gauge block; caliper", "M3 hardware", "M3 1.2 N·m", "U95 axes normal to strand", "datum alignment≤0.10 mm", "FM-002", "gauge block repeatability check", "mechanical repeatability recorded", "puller"),
    (16, "FM-PL/RL/AX/GR/GA ×1 set", "dial indicator; 3 mm hex", "M4 plus metal collars", "M4 3 N·m", "roller axes parallel", "parallel≤0.05/80; TIR≤0.05 mm", "FM-002", "hand feed dummy strand", "no pinch bypass or bind", "spooler"),
    (17, "SP-DA/AX/RL/SH/BP/MM/TR/DS ×1 set", "square; dial; 3 mm hex", "M4 plus collars", "M4 3 N·m", "traverse parallel to spool", "rod parallel≤0.10/160 mm", "SP-001", "full-stroke hand traverse", "no collision in service envelope", "all guards"),
    (18, "GD panels/interlocks ×1 set", "gap probe; 3 mm hex", "captive M4 hardware", "M4 3 N·m", "labels outward; service panels keyed", "openings≤6 mm at hazards", "GD-001/SV-001", "reach/access and removal test", "all hazards covered", "enclosure/PE"),
    (19, "CT-ENC-01; PE bonds ×1 set", "DMM; torque wrench", "M4 PE stud/tooth washer", "M4 3 N·m", "PE first; ducts segregated", "bond target 0.10 ohm 이하; separation≥18 mm", "EL-001", "four-wire continuity where available", "bond and witness mark recorded", "power wiring"),
    (20, "wire/fuse schedules ×1 set", "crimper; pull tester; DMM", "listed terminals/ferrules", "terminal maker value", "power and signal in separate ducts", "gauge/temperature/routing per schedule", "electrical PDFs", "100% point-to-point and pull test", "all IDs and polarities pass", "hard safety chain"),
    (21, "E-stop/lid/service/thermal chain ×1", "DMM; insulated probe", "locking safety terminals", "terminal maker value", "normally-safe series chain", "each open removes coil energy", "safety_chain.pdf", "de-energized forced-open continuity", "firmware cannot bypass", "logic wiring"),
    (22, "Mega/sensors/drivers ×1 set", "DMM; logic current limiter", "locking low-voltage terminals", "terminal maker value", "outputs safe at reset", "pin schedule exact match", "Arduino_Mega_pinmap.pdf", "source-to-pin point check", "no hazardous enable asserted", "firmware flash"),
    (23, "released HEX/source ×1", "USB programmer; hash tool", "N/A", "N/A—software gate", "Mega 2560 target", "binary SHA equals build manifest", "firmware_and_calibration_ko.pdf", "clean build and readback hash", "reproducible build PASS", "calibration"),
    (24, "sensor/actuator calibration records ×1 set", "reference loads/gauges", "N/A", "N/A—calibration gate", "one subsystem at a time", "range/unit/CRC/revision valid", "firmware_and_calibration_ko.pdf", "bounded calibration routine", "invalid data forces safe state", "pre-power signoff"),
    (25, "complete assembly traveler ×1", "checklist; camera; DMM", "all witness marks", "verify recorded values", "machine locked out", "all prior tolerances PASS", "pre_power_checklist_ko.pdf", "independent review and photo record", "physical state remains NOT_RUN", "explicit user commissioning approval"),
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def typ(title: str, body: str) -> str:
    return f'''#set document(title: "{title}")
#set page(paper: "a4", margin: 17mm, numbering: "1")
#set text(font: "Noto Sans CJK KR", size: 9pt, lang: "ko")
#set heading(numbering: "1.1")
#let danger(body) = block(width: 100%, fill: rgb("ffece5"), stroke: 1pt + rgb("c5482e"), inset: 7pt, body)
#let gate(body) = block(width: 100%, fill: rgb("eaf3f7"), stroke: 1pt + rgb("33738b"), inset: 7pt, body)
= {title}
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact donor 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `{REV}` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

{body}
'''


def compile_typ(path: Path, output: Path | None = None) -> None:
    subprocess.run(["typst", "compile", str(path), str(output or path.with_suffix(".pdf")), "--root", str(ROOT)], check=True, cwd=ROOT)


def drawing_set(commit: str) -> None:
    rows = []
    pages = []
    for number, name, svg in DRAWINGS:
        material, critical = DRAWING_META[number]
        source = DRAW / "v0.8" / svg
        pdf = DRAW / "v0.8" / f"{number}_{name.replace(' ', '_').replace('/', '_')}.pdf"
        sheet = FINAL / f".{number}.typ"
        write(sheet, typ(f"{number} — {name}", f'''#image("../drawings/v0.8/{svg}", width: 100%, height: 170mm, fit: "contain")

== 제작·검사 기준

- 단위: mm · 제3각법 · 축척: NTS(기입 치수 우선)
- 재료/구성: {material}
- 핵심 치수/공차: {critical}
- 일반공차: ISO 2768-m. 개별 부품은 `exports/final/manufacturing` 도면과 `interface_catalog.csv`를 함께 검사한다.
- Source: `{commit}` · 물리 검증: `NOT_RUN`
'''))
        compile_typ(sheet, pdf); sheet.unlink()
        rows.append({
            "drawing_number": number, "part_assembly_id": number, "revision": "v0.8", "units": "mm",
            "scale": "NTS; written dimensions control", "projection": "third-angle orthographic/isometric",
            "material": material, "finish": "deburr; part-specific surface finish in manufacturing package",
            "general_tolerance": "ISO 2768-m unless critical value overrides",
            "critical_tolerance": critical,
            "notes": f"{name}; vector projection; do not scale drawing", "source_commit": commit,
            "pdf": str(pdf.relative_to(ROOT)), "page": 1, "status": "PASS",
        })
        pages += [f'''= {number} — {name}
#image("../drawings/v0.8/{svg}", width: 100%, height: 170mm, fit: "contain")

*재료/구성:* {material}  \
*핵심 치수/공차:* {critical}  \
*단위:* mm · 제3각법 · NTS · source `{commit}`''', "#pagebreak()"]
    DRAW.mkdir(parents=True, exist_ok=True)
    with (DRAW / "drawing_register.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    src = FINAL / "assembly_drawing_set.typ"
    write(src, typ("v0.8 치수·검사 조립 도면 세트", "\n\n".join(pages[:-1])))
    compile_typ(src)


def electrical() -> None:
    ELEC.mkdir(parents=True, exist_ok=True)
    with (ELEC / "wire_schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(("wire_id", "from", "to", "voltage", "maximum_current", "wire_gauge", "colour", "connector", "terminal", "fuse", "routing", "shield_ground", "strain_relief")); w.writerows(WIRES)
    connectors = sorted({(r[7], r[8], r[1], r[2], "exact MPN and mating retention USER_VERIFICATION_REQUIRED") for r in WIRES})
    with (ELEC / "connector_schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(("connector_id", "terminal", "from", "to", "verification")); w.writerows(connectors)
    with (ELEC / "fuse_schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(("fuse_id", "branch", "rating", "basis", "verification")); w.writerows(FUSES)

    pin_text = (ROOT / "firmware/arduino_mega/src/board_config.h").read_text()
    pins = re.findall(r"constexpr uint8_t ([A-Z0-9_]+) = ([A-Z0-9]+);", pin_text)
    pin_rows = "\n".join(f"- `{name}` → `{pin}`" for name, pin in pins)
    common = '''
== 설계 기준

`24 V / 600 W PSU (25 A)` → main fuse → 분기 보호. Hazardous motion/heater permission은 `E-stop → lid → service guard → independent thermal cutoff → safety contactor`의 hardwired normally-safe chain이다. Mega는 feedback만 읽으며 chain을 우회하지 않는다. Protective earth는 frame과 metal hot shield에 전용 bond한다.

== 통전 전 gate

- exact PSU/driver/MOSFET/fuse/connector 정격과 DC 차단능력 확인
- 각 conductor ampacity·온도·길이·전압강하를 현지 규정과 donor stall current로 재계산
- PE continuity, insulation, polarity, branch isolation, forced-open interlock 시험 기록
- logic-only → motor → heater 순으로 별도 사용자 승인; power restore 자동 재기동 금지
'''
    docs = {
        "system_block_diagram": common + "\n== 블록\n\n`AC inlet/main switch → verified PSU → main fuse → logic / hardwired safety chain → motor, heater, fan branches`\n\nSensors → protected interfaces → Arduino Mega; commands → drivers only while hardware permission is present.",
        "power_distribution": common + "\n== 분배\n\nMain 24 V bus에서 logic, shredder, screw/feeder, heater 4채널, puller/spooler, fan을 각각 fuse로 분리한다. Software aggregate heater cap 500 W와 reserve 100 W는 물리 fuse를 대체하지 않는다.",
        "full_wiring_diagram": common + "\n== 배선 기준\n\n모든 active conductor는 `wire_schedule.csv`, connector는 `connector_schedule.csv`, 보호소자는 `fuse_schedule.csv`와 일치해야 한다. Heater/motor와 thermocouple/gauge/tach route를 분리한다.",
        "safety_chain": common + "\n== 안전 chain truth table\n\nE-stop, lid, service guard, thermal chain 중 하나라도 open이면 safety contactor가 de-energize되어 heater와 hazardous motion enable을 물리 제거한다. Welded contact/command-feedback mismatch는 latch하며 physical lockout key 없이 clear하지 않는다.",
        "Arduino_Mega_pinmap": common + "\n== `board_config.h` exact pin map\n\n" + pin_rows + "\n\nArray pin groups와 analog pins는 source header가 최종 기준이다. 활성 FD-MET 동축 auger/agitator는 D44 PWM, D42 direction, D46 enable, D47 fault, A7 tach를 사용한다.",
        "grounding_bonding": common + "\n== PE와 shield\n\nAC inlet PE → dedicated frame stud → enclosure, motor frames, metal hot shield. Paint를 제거하고 tooth washer를 사용하며 각 bond를 개별 continuity 측정한다. Signal shield는 지정된 한쪽 끝만 접지하고 PE conductor로 사용하지 않는다.",
        "enclosure_layout": common + "\n== 물리 구획\n\nAC/PSU와 DC high-current, heater MOSFET/driver, safety contactor, logic/sensor 영역을 분리한다. Fuse는 접근 가능한 표찰 위치, PE stud는 독립 위치, duct fill과 bend radius는 exact wire 선정 후 확인한다.",
        "cable_routing": common + "\n== route\n\nHot-zone cable은 300 °C급 sleeve 후보와 metal clamp를 사용하고 moving cable은 full service envelope에서 strain relief를 확인한다. Thermocouple/tach/gauge는 heater PWM·motor와 분리하며 solid·sharp edge 관통을 금지한다.",
    }
    for name, body in docs.items():
        path = ELEC / f"{name}.typ"; write(path, typ(name.replace("_", " "), body)); compile_typ(path)


def manuals() -> None:
    with (FINAL / "assembly_steps.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n"); writer.writerow(ASSEMBLY_FIELDS); writer.writerows(ASSEMBLY_STEPS)
    step_text = []
    for row in ASSEMBLY_STEPS:
        data = dict(zip(ASSEMBLY_FIELDS, map(str, row)))
        step_text.append(f'''== 단계 {data["step_number"]}: {data["part_ids_quantity"]}

- 공구: {data["required_tools"]}
- 체결품 / 토크: {data["fasteners"]} / {data["torque"]}
- 방향: {data["orientation"]}
- 공차·간극: {data["clearance_tolerance"]}
- 도면: {data["drawing"]}
- 검사: {data["inspection_method"]}
- 합격: {data["pass_fail"]}
- 다음 선행조건: {data["next_prerequisite"]}
''')
    complete = FINAL / "complete_build_manual_ko.typ"
    intro = '''이 문서와 `assembly_steps.csv`, `assembly_drawing_set.pdf`, `exports/final/manufacturing/`, `exports/final/electrical/`이 v0.8 조립의 단일 실행 기준이다. 구버전 매뉴얼은 적용하지 않는다.

각 단계의 실측값·작업자·검토자·증거 경로를 기록한다. 계산·CAD PASS는 물리 합격이 아니다. 구매·가공·통전·가열 전에는 해당 사용자 승인 gate를 통과해야 한다.

'''
    write(complete, typ("v0.8 실행용 조립 매뉴얼", intro + "\n".join(step_text)))
    compile_typ(complete)
    bodies = {
        "exploded_views_ko": "== 조립 순서\n\nFrame → shredder frame → bearing/shaft → cutter stack → phase gear/chain/motor/shear fuse → screen/recirculation/hopper → flake bin → feeder → extruder/thrust → heater/sensor/die → hot shield → cooling → gauge → puller → spooler/traverse → guards → enclosure → wiring → firmware → calibration → dry checks.\n\n각 단계의 형상은 `assembly_drawing_set.pdf` 해당 도면 번호를 사용한다. 고하중 경로는 metal part → bearing/plate → aluminum profile → table이다.",
        "tolerance_and_fit_guide_ko": "== 기준\n\n`exports/final/interface_catalog.csv`가 16개 critical interface의 nominal/tolerance/검사법을 지배한다. Cutter/blade clearance는 출력 공차가 아닌 ground metal shim으로 조절한다. Bearing seat, die insert, screw/barrel cold/hot clearance, rear datum/front sliding travel을 조립 전 측정한다.\n\n#gate[측정기 ID·교정상태·온도·실측값을 기록하고 허용범위를 벗어나면 임의 rework 대신 source parameter와 도면 revision을 갱신한다.]",
        "electrical_assembly_ko": "== 순서\n\nPE bond → PSU 미통전 설치 → branch fuse → hardwired safety chain → drivers/MOSFET → logic → sensors → cable clamp 순이다. `exports/final/electrical`의 세 CSV와 8개 벡터 PDF를 작업표로 사용한다.\n\n#gate[전원 분리 상태에서 PE continuity, insulation, polarity, fuse/terminal ID, forced-open safety contact를 독립 검사한다.]",
        "firmware_and_calibration_ko": "== Firmware\n\nReleased HEX는 `exports/final/firmware/binaries/filament_recycler_atmega2560.hex`; build evidence는 `validation/results/arduino_mega_compile.json`이다. Source/HEX hash 일치를 검증하고 Mega 2560 target/fuse setting을 확인한다.\n\n== Calibration\n\nDonor label 확인 후 shredder current/RPM, screw tach, puller/spooler tach, traverse limits, X/Y gauge U95, dancer, cooling current와 fan tach를 각각 교정한다. EEPROM CRC/revision/unit/range가 유효하지 않으면 production ready를 금지한다.",
        "maintenance_manual_ko": "== Lockout\n\nMain disconnect OFF, 0 V, cutter/screw mechanical block, hot zone 60 °C 미만 확인 뒤 작업한다. E-stop만으로 jam을 제거하지 않는다.\n\n== 주기 점검\n\n매 사용 전 guard/interlock/PE/cable/누설; 매 lot cutter clearance·screen·die; 정기적으로 chain tension, bearing play, witness mark, fuse/thermal cutoff, calibration drift를 기록한다. Cutter·gasket·shear fuse replacement 기준은 제조도면과 실측 이력으로 관리한다.",
    }
    for name, body in bodies.items():
        p = FINAL / f"{name}.typ"; write(p, typ(name.replace("_ko", "").replace("_", " "), body)); compile_typ(p)


def commissioning() -> None:
    transition = """== 상태 전이\n\n`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.\n"""
    def procedure(inputs: str, method: str, evidence: str, acceptance: str) -> str:
        return f"== 입력\n\n{inputs}\n\n== 방법\n\n{method}\n\n== 증거\n\n{evidence}\n\n== 수치 합격기준\n\n{acceptance}"

    items = {
        "pre_power_checklist_ko": procedure(
            "Released BOM/도면, 교정 유효 DMM·절연계·토크렌치, exact donor label, 미통전·lockout 상태.",
            "25개 assembly traveler와 witness mark를 대조하고 cutter/screw를 손으로 20회 회전한다. PE, 극성, fuse ID, connector, strain relief를 point-to-point 검사한다.",
            "서명 traveler, donor-label 사진, torque/치수표, PE·절연·극성 원시 측정 CSV.",
            "PE bond 각 경로 ≤0.10 Ω; 전자장치 분리 후 500 VDC 절연 ≥1 MΩ; shaft centre 48.00±0.03 mm; feeder radial clearance 0.20–0.25 mm; screw TIR ≤0.10 mm; 미확정 donor 0건."),
        "first_power_on_ko": procedure(
            "Motor/heater branch fuse 제거, 24 V current-limited supply, DMM·oscilloscope, hardwired K0 chain.",
            "Logic branch만 0.5 A limit로 올린 뒤 reset 출력을 확인한다. E-stop/lid/service/thermal contact를 하나씩 forced-open하고 K0 feedback과 물리 contact를 측정한다.",
            "Rail voltage/current trace, boot log, 4개 forced-open 사진·K0 voltage trace, 복전 후 상태 log.",
            "24 V rail 22.8–25.2 V; 초기 logic current ≤0.5 A; reset 시 hazardous enable 0개; 각 contact open 시 K0 coil 0 V; 복전 후 자동 motor/heater command 0개."),
        "dry_run_ko": procedure(
            "원료 없음, heater fuse 제거, guard 장착, tach/current 계측, branch별 별도 승인.",
            "Fan→puller/spooler/traverse→FD-MET feeder→screw→guarded shredder 순으로 한 branch씩 구동한다. 방향·fault pin·tach-loss·limit·E-stop을 강제한다.",
            "명령/실측 RPM·전류·방향 표, fault/limit/E-stop timestamp log, 복전·재기동 video.",
            "명령 반대 회전 0건; feeder 5 A, puller/spooler 각 5 A design envelope 이내; tach-loss 또는 driver fault 뒤 다음 supervisor cycle에서 command 0; traverse usable width 68 mm와 2 mm home backoff; 자동재기동 0건."),
        "heater_commissioning_ko": procedure(
            "빈 metal hot path, 모든 motor disable, grounded shield, T1–T5 reference probe, 독립 thermal cutoff, 원격 stop.",
            "TC open과 permission-open을 먼저 시험하고 zone별 저출력 step으로 channel mapping/온도 상승을 확인한다. PLA 목표 180/195/205/200 °C, PET 245/260/270/265 °C는 별도 ramp로 수행한다.",
            "Zone별 command/온도 250 ms log, reference-probe 비교, cutoff 개방 trace, hot-zone travel 측정.",
            "TC mapping 오류 0건; valid range -20–300 °C; 120 s 가열 명령에서 최소 +4 °C 아니면 fault; command-off 60 s 동안 +8 °C면 fault; software overtemperature 285 °C 이전 차단; cold axial travel ≥1.30 mm."),
        "shredder_commissioning_ko": procedure(
            "Gate-1의 정확히 2장 cutter coupon, closed guard, calibrated torque/current/RPM, PLA 1.2/2.0/3.0 mm와 PET body/folded-seam coupon.",
            "No-load 뒤 재료별 14 N·m 연속, 18 N·m jam trip, 22 N·m cutter-equivalent shear element를 단계적으로 시험한다. Full stack은 이 gate에서 조립하지 않는다.",
            "Torque/current/RPM CSV, jam-stop timestamp, chip-size 사진, shear coupon 파단 사진과 serial.",
            "PLA 32 rpm/PET 24 rpm 목표의 ±10%; 14 N·m 연속 안정; 18 N·m에서 250 ms 이내 stop; 22 N·m 이하에서 replaceable shear element가 34 N·m phase pair보다 먼저 분리; guard 이탈 0건."),
        "PLA_process_startup_ko": procedure(
            "확인된 단일 PLA lot, 외부 건조 coupon, clean path, calibrated T1–T5/gauge/tach/cooling.",
            "180/195/205 °C barrel과 200 °C die가 ±5 °C band에 든 뒤 low feed로 시작하고 10 s 안정 구간 20개 sample을 기록한다.",
            "Lot/moisture 기록, 온도·screw/puller/spool RPM, X/Y diameter·ovality·U95, 실제 질량/시간.",
            "Mean diameter error ≤0.05 mm; ovality ≤0.05 mm; U95 ≤0.03 mm; 20개 연속 valid; cooling current 0.2–2.0 A와 fan 2채널 tach valid. 200 g/h는 목표일 뿐 필수 release 기준이 아니다."),
        "PET_process_startup_ko": procedure(
            "확인된 단일 PET lot과 오염·수분 coupon, all-metal hot path, 실제 정격 확인된 300 °C급 wiring/cutoff, calibrated sensors.",
            "245/260/270 °C barrel과 265 °C die가 ±5 °C band에 든 뒤 guarded low-feed first-hot-test를 수행한다. PLA 결과를 재사용하지 않는다.",
            "Lot/moisture·오염 기록, 온도/압력 징후, relief/leak 영상, X/Y diameter·ovality·U95, 실제 질량/시간.",
            "Mean diameter error ≤0.05 mm; ovality ≤0.05 mm; U95 ≤0.03 mm; 20개 연속 valid; hot-zone travel ≥1.30 mm; 누설 0건; 3–6 MPa relief coupon 3개 모두 insert 포획 상태로 우회 개방."),
        "material_change_purge_ko": procedure(
            "이전/다음 material ID, verified screw tach, waste path, T1–T5, clean screen/hopper 도구.",
            "이전 material profile에서 waste path로 purge하고 시간·실제 screw 회전을 동시에 적산한다. Screen/hopper 청소와 다음 profile 전이를 각각 확인한다.",
            "Material-session log, screw RPM/revolution trace, purge 영상·폐기물 사진/실측 질량, 청소 signoff.",
            "Purge ≥120 s AND actual screw ≥32 rev; 모든 zone target ±5 °C; visual contamination 0; screen/hopper signoff 완료; 종료 후 모든 hot point 60 °C 미만."),
        "physical_validation_plan_ko": procedure(
            "승인된 coupon/fixture, calibrated instruments, 각 gate 작업자·독립 검토자, lockout/원격 E-stop.",
            "Gate 1 cutter coupon → Gate 2 safety/drive → Gate 3 hot-zone leak/relief → Gate 4 gauge/forming → Gate 5 full spool 순서로 수행하며 FAIL 시 즉시 lockout하고 다음 gate를 금지한다.",
            "Gate별 입력·방법·원시 CSV/사진/video·판정·서명. Simulation 값은 시험 결과 칸에 복사하지 않는다.",
            "G1: 18 N·m trip/22 N·m shear; G2: PE≤0.10 Ω·절연≥1 MΩ·자동재기동 0; G3: relief 3/3 PASS·누설 0; G4: diameter/ovality≤0.05 mm·U95≤0.03 mm; G5: 1 kg nominal spool, 68 mm traverse, dancer stop 0.36 rad 이전, hard-stop 0.4363 rad 비접촉."),
    }
    gate_rows = [
        ("assembly incomplete", "assembly complete", "all 25 assembly_steps rows signed; dimensions and guards inspected", "independent mechanical reviewer + user", "NOT_RUN"),
        ("assembly complete", "electrical inspection complete", "PE continuity, insulation, polarity, fuse IDs and point-to-point wiring PASS", "qualified electrical reviewer + user", "NOT_RUN"),
        ("electrical inspection complete", "safe for low-voltage logic", "current-limited logic rail; hardwired chain forced-open; outputs safe at reset", "electrical reviewer + user", "NOT_RUN"),
        ("safe for low-voltage logic", "safe for motors", "donor labels/ratings confirmed; direction, current, tach and stop tests one branch at a time", "mechanical/electrical reviewers + user", "NOT_RUN"),
        ("safe for motors", "safe for heaters", "empty guarded hot path; independent thermal cutoff; TC mapping; low-power ramp", "thermal/electrical reviewers + user", "NOT_RUN"),
        ("safe for heaters", "safe to process plastic", "Gate 1–4 evidence PASS; leak/relief/strand control verified; material lot and purge path ready", "final safety review + explicit user approval", "NOT_RUN"),
    ]
    with (FINAL / "commissioning_gates.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n"); writer.writerow(("from_state", "to_state", "checklist", "approval", "status")); writer.writerows(gate_rows)
    for name, body in items.items():
        checklist = "\n\n== Checklist\n\n- [ ] 작업자·검토자·날짜·장비 ID\n- [ ] 입력 조건·측정값·원시 증거 경로\n- [ ] Pass/fail 기준과 결과\n- [ ] 다음 단계 승인 또는 lockout 복귀"
        p = FINAL / f"{name}.typ"; write(p, typ(name.replace("_ko", "").replace("_", " "), transition + "\n== 절차\n\n" + body + checklist)); compile_typ(p)


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    FINAL.mkdir(parents=True, exist_ok=True)
    drawing_set(commit)
    manuals(); commissioning()
    print(f"V08_FINAL_DOCUMENTS_OK drawings={len(DRAWINGS)} assembly_steps={len(ASSEMBLY_STEPS)}")


if __name__ == "__main__":
    main()
