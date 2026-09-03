#!/usr/bin/env python3
"""v0.8 최종 벡터 도면, 전장 schedule, 매뉴얼과 시운전 문서를 생성한다."""

from __future__ import annotations

import csv
import re
import subprocess
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

WIRES = [
    ("W-PE-01", "AC inlet PE", "frame PE stud", "PE", "fault current; site dependent", "green/yellow; local code", "green/yellow", "ring lug", "PE-1", "upstream breaker", "short dedicated bond", "protective earth", "tooth washer + clamp"),
    ("W-PE-02", "frame PE stud", "hot shield", "PE", "fault current; site dependent", "green/yellow; local code", "green/yellow", "ring lug", "PE-2", "upstream breaker", "away from signal", "protective earth", "tooth washer + clamp"),
    ("W-24-00", "24 V 600 W PSU", "main fuse", "24 VDC", "25 A design maximum", ">=4 mm2; verify", "red", "ferrule", "F-MAIN", "F-MAIN 30 A candidate", "power duct", "0 V paired", "duct clamp"),
    ("W-24-01", "F-MAIN", "logic fuse", "24 VDC", "3 A design maximum", ">=0.75 mm2; verify", "red", "ferrule", "F-LOGIC", "F-LOGIC 3 A candidate", "signal duct", "0 V paired", "duct clamp"),
    ("W-SAFE-01", "logic branch", "E-stop/lid/service/thermal chain", "24 VDC", "1 A design maximum", ">=0.5 mm2; verify", "red", "locking terminal", "K-SAFE", "F-SAFE 1 A candidate", "dedicated safety route", "0 V paired", "both ends clamped"),
    ("W-SH-01", "safety contactor", "shredder driver", "24 VDC", "20 A branch limit", ">=2.5 mm2; verify", "red", "locking power", "DRV-SH", "F-SH 20 A", "power duct", "0 V paired", "both ends clamped"),
    ("W-EX-01", "safety contactor", "screw/feeder drivers", "24 VDC", "10 A design limit", ">=1.5 mm2; verify", "red", "locking power", "DRV-EX", "F-EX 10 A candidate", "power duct", "0 V paired", "both ends clamped"),
    ("W-HT-01", "safety contactor", "heater MOSFET branches", "24 VDC", "15 A installed heater total", ">=2.5 mm2; 300 C sleeve near hot zone", "red", "locking high-temp", "MOS-H1..H4", "4 x F-H 5 A candidate", "separate hot route", "grounded shield; no signal share", "hot-zone clamp"),
    ("W-FAN-01", "fan fuse", "cooling fan pair", "24 VDC", "3 A design limit", ">=0.75 mm2; verify donor", "blue", "service plug", "FAN-1/2", "F-FAN 3 A candidate", "forming-chain duct", "tach shield grounded one end", "service loop + clamp"),
    ("W-SENS-01", "thermocouples", "MAX6675/Mega", "mV/5 V logic", "signal only", "K-type extension; donor verify", "IEC K colours", "mini-K/locking", "T1..T5", "logic branch", "separate from heater/motor", "shield one end; isolated probe verify", "service loop"),
]

FUSES = [
    ("F-MAIN", "24 V distribution", "30 A candidate", "25 A PSU output", "DC interrupt rating >= source; exact MPN verify"),
    ("F-LOGIC", "Mega/gauge", "3 A candidate", "logic load measurement required", "protect branch conductor"),
    ("F-SAFE", "hardwired permission chain", "1 A candidate", "coil/current measurement required", "firmware cannot bypass"),
    ("F-SH", "shredder driver", "20 A", "donor label + calibrated current", "18 N m jam trip is calibrated, not fuse rating"),
    ("F-EX", "screw/feeder", "10 A candidate", "donor label/current required", "recalculate after donor selection"),
    ("F-H1..H4", "heater MOSFET channels", "5 A each candidate", "360 W installed aggregate", "one-shot thermal fuse remains series independent"),
    ("F-FAN", "cooling fans", "3 A candidate", "donor start/stall current required", "A4 current and A14 tach are diagnostics only"),
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
    for page, (number, name, svg) in enumerate(DRAWINGS, 1):
        rows.append({
            "drawing_number": number, "part_assembly_id": number, "revision": "v0.8", "units": "mm",
            "scale": "NTS; dimensions from CAD", "projection": "third-angle orthographic/isometric",
            "material": "assembly-specific; BOM/manufacturing note governs", "finish": "part-specific; manufacturing note governs",
            "general_tolerance": "ISO 2768-m unless critical value overrides",
            "critical_tolerance": "interface_catalog.csv and manufacturing drawing govern",
            "notes": f"{name}; vector projection; do not scale drawing", "source_commit": commit,
            "pdf": "docs/final/assembly_drawing_set.pdf", "page": page, "status": "PASS",
        })
    DRAW.mkdir(parents=True, exist_ok=True)
    with (DRAW / "drawing_register.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    pages = []
    for i, (number, name, svg) in enumerate(DRAWINGS):
        if i: pages.append("#pagebreak()")
        pages.append(f'''= {number} — {name}
#image("../drawings/v0.8/{svg}", width: 100%, height: 205mm, fit: "contain")
Drawing `{number}` · Rev v0.8 · mm · third-angle · NTS · source `{commit}`

General tolerance ISO 2768-m. Critical interfaces are controlled by `exports/final/interface_catalog.csv`; do not scale this drawing.''')
    src = FINAL / "assembly_drawing_set.typ"
    write(src, typ("v0.8 벡터 조립 도면 세트", "\n\n".join(pages)))
    compile_typ(src)


def electrical() -> None:
    ELEC.mkdir(parents=True, exist_ok=True)
    with (ELEC / "wire_schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(("wire_id", "from", "to", "voltage", "maximum_current", "wire_gauge", "colour", "connector", "terminal", "fuse", "routing", "shield_ground", "strain_relief")); w.writerows(WIRES)
    connectors = sorted({(r[7], r[8], r[1], r[2], "exact MPN and mating retention USER_VERIFICATION_REQUIRED") for r in WIRES})
    with (ELEC / "connector_schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(("connector_id", "terminal", "from", "to", "verification")); w.writerows(connectors)
    with (ELEC / "fuse_schedule.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(("fuse_id", "branch", "rating", "basis", "verification")); w.writerows(FUSES)

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
        "Arduino_Mega_pinmap": common + "\n== `board_config.h` exact pin map\n\n" + pin_rows + "\n\nArray pin groups와 analog pins는 source header가 최종 기준이다. Adapter가 미승인인 feeder 추가 I/O는 배정하지 않는다.",
        "grounding_bonding": common + "\n== PE와 shield\n\nAC inlet PE → dedicated frame stud → enclosure, motor frames, metal hot shield. Paint를 제거하고 tooth washer를 사용하며 각 bond를 개별 continuity 측정한다. Signal shield는 지정된 한쪽 끝만 접지하고 PE conductor로 사용하지 않는다.",
        "enclosure_layout": common + "\n== 물리 구획\n\nAC/PSU와 DC high-current, heater MOSFET/driver, safety contactor, logic/sensor 영역을 분리한다. Fuse는 접근 가능한 표찰 위치, PE stud는 독립 위치, duct fill과 bend radius는 exact wire 선정 후 확인한다.",
        "cable_routing": common + "\n== route\n\nHot-zone cable은 300 °C급 sleeve 후보와 metal clamp를 사용하고 moving cable은 full service envelope에서 strain relief를 확인한다. Thermocouple/tach/gauge는 heater PWM·motor와 분리하며 solid·sharp edge 관통을 금지한다.",
    }
    for name, body in docs.items():
        path = ELEC / f"{name}.typ"; write(path, typ(name.replace("_", " "), body)); compile_typ(path)


def manuals() -> None:
    complete = FINAL / "complete_build_manual_ko.typ"
    write(complete, '''#include "../build_manual_ko.typ"
#pagebreak()
= v0.8 closure 부록
본 문서의 기존 v0.6.2.1 조립 sequence는 v0.8 final geometry에도 적용하며, rear fixed axial datum/front radial sliding guide와 `docs/final/assembly_drawing_set.pdf`가 우선한다. 모든 단계는 part ID·수량, 공구, fastener, torque, 방향, clearance, 도면, 검사법, pass/fail, 다음 gate를 기록한 traveler와 함께 수행한다. 계산·CAD PASS는 물리 합격이 아니다.
''')
    compile_typ(complete)
    bodies = {
        "exploded_views_ko": "== 조립 순서\n\nFrame → shredder frame → bearing/shaft → cutter stack → phase gear/chain/motor/shear fuse → screen/recirculation/hopper → flake bin → feeder → extruder/thrust → heater/sensor/die → hot shield → cooling → gauge → puller → spooler/traverse → guards → enclosure → wiring → firmware → calibration → dry checks.\n\n각 단계의 형상은 `assembly_drawing_set.pdf` 해당 도면 번호를 사용한다. 고하중 경로는 metal part → bearing/plate → aluminum profile → table이다.",
        "tolerance_and_fit_guide_ko": "== 기준\n\n`exports/final/interface_catalog.csv`가 14개 critical interface의 nominal/tolerance/검사법을 지배한다. Cutter/blade clearance는 출력 공차가 아닌 ground metal shim으로 조절한다. Bearing seat, die insert, screw/barrel cold clearance, rear datum/front sliding travel을 조립 전 측정한다.\n\n#gate[측정기 ID·교정상태·온도·실측값을 기록하고 허용범위를 벗어나면 임의 rework 대신 source parameter와 도면 revision을 갱신한다.]",
        "electrical_assembly_ko": "== 순서\n\nPE bond → PSU 미통전 설치 → branch fuse → hardwired safety chain → drivers/MOSFET → logic → sensors → cable clamp 순이다. `exports/final/electrical`의 세 CSV와 8개 벡터 PDF를 작업표로 사용한다.\n\n#gate[전원 분리 상태에서 PE continuity, insulation, polarity, fuse/terminal ID, forced-open safety contact를 독립 검사한다.]",
        "firmware_and_calibration_ko": "== Firmware\n\nReleased HEX는 `exports/final/firmware/binaries/filament_recycler_atmega2560.hex`; build evidence는 `validation/results/arduino_mega_compile.json`이다. Source/HEX hash 일치를 검증하고 Mega 2560 target/fuse setting을 확인한다.\n\n== Calibration\n\nDonor label 확인 후 shredder current/RPM, screw tach, puller/spooler tach, traverse limits, X/Y gauge U95, dancer, cooling current와 fan tach를 각각 교정한다. EEPROM CRC/revision/unit/range가 유효하지 않으면 production ready를 금지한다.",
        "maintenance_manual_ko": "== Lockout\n\nMain disconnect OFF, 0 V, cutter/screw mechanical block, hot zone 60 °C 미만 확인 뒤 작업한다. E-stop만으로 jam을 제거하지 않는다.\n\n== 주기 점검\n\n매 사용 전 guard/interlock/PE/cable/누설; 매 lot cutter clearance·screen·die; 정기적으로 chain tension, bearing play, witness mark, fuse/thermal cutoff, calibration drift를 기록한다. Cutter·gasket·shear fuse replacement 기준은 제조도면과 실측 이력으로 관리한다.",
    }
    for name, body in bodies.items():
        p = FINAL / f"{name}.typ"; write(p, typ(name.replace("_ko", "").replace("_", " "), body)); compile_typ(p)


def commissioning() -> None:
    transition = """== 상태 전이\n\n`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 앞 단계의 서명·측정 증거와 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다.\n"""
    items = {
        "pre_power_checklist_ko": "도면/BOM revision, fastener witness mark, cutter/screw hand rotation, guard, PE, insulation, polarity, fuse, connector, strain relief를 확인한다. 모든 donor label과 미확정 설계값을 닫기 전 FAIL.",
        "first_power_on_ko": "Branch fuse를 제거한 logic-only 상태에서 current-limited 24 V를 인가하고 rail, Mega boot, input safe-state, E-stop/lid/service/thermal feedback을 확인한다. Hardware contactor가 각 forced-open에서 drop하지 않으면 즉시 차단.",
        "dry_run_ko": "Heater와 원료 없이 fan → puller/spooler/traverse → screw → guarded shredder를 별도 승인으로 한 branch씩 시험한다. 방향, no-motion, tach, driver fault, E-stop stop time과 자동재기동 금지를 기록한다.",
        "heater_commissioning_ko": "Motor disable/empty barrel/grounded shield 상태에서 thermal fuse·thermocouple open fault를 먼저 시험한다. 저출력 step부터 overshoot와 channel mapping을 확인하며 원격 stop·barrier를 사용한다.",
        "shredder_commissioning_ko": "Guard와 coupon fixture, calibrated torque/current/RPM 계측으로 no-load 후 Gate-1 coupon만 시험한다. 14 N m continuous, 18 N m jam trip과 shear element 분리를 물리 실측하며 full cutter stack 승인이 아니다.",
        "PLA_process_startup_ko": "확인된 PLA lot과 외부 건조 coupon, clean path, PLA profile, cooling proof 후 low feed로 시작한다. Melt, diameter, ovality, U95와 measured output을 기록하고 200 g/h를 release 합격으로 요구하지 않는다.",
        "PET_process_startup_ko": "PET 오염·수분 coupon, metal hot path, 300 °C급 thermal cutoff 후보의 실제 정격 확인 후 guarded low-feed first-hot-test를 수행한다. PET 조건은 PLA 결과로 대체하지 않는다.",
        "material_change_purge_ko": "Waste path를 확인하고 이전 material profile로 purge한다. 실제 screw revolutions, stable temperature, visual confirmation과 measured purge mass를 기록한다. 완료 후 모든 hot points가 60 °C 미만일 때까지 cooling을 유지한다.",
        "physical_validation_plan_ko": "Gate 1 cutter coupon → Gate 2 safety/drive → Gate 3 hot-zone leak/relief → Gate 4 gauge/forming → Gate 5 full spool 순으로 독립 evidence와 pass/fail을 남긴다. Simulation 결과는 시험 결과 칸에 복사하지 않는다.",
    }
    for name, body in items.items():
        checklist = "\n\n== Checklist\n\n- [ ] 작업자·검토자·날짜·장비 ID\n- [ ] 입력 조건·측정값·원시 증거 경로\n- [ ] Pass/fail 기준과 결과\n- [ ] 다음 단계 승인 또는 lockout 복귀"
        p = FINAL / f"{name}.typ"; write(p, typ(name.replace("_ko", "").replace("_", " "), transition + "\n== 절차\n\n" + body + checklist)); compile_typ(p)


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    FINAL.mkdir(parents=True, exist_ok=True)
    drawing_set(commit); electrical(); manuals(); commissioning()
    print(f"V08_FINAL_DOCUMENTS_OK drawings={len(DRAWINGS)} wires={len(WIRES)} pdf=24")


if __name__ == "__main__":
    main()
