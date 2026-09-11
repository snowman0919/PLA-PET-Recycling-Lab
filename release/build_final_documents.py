#!/usr/bin/env python3
"""v0.8 최종 벡터 도면, 조립 매뉴얼과 시운전 문서를 생성한다.

Electrical/firmware release는 `release/build_electrical_firmware_release.py`만 생성한다.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path

from build_bom_release import assembly_step_number, fastener_step_number, fasteners

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/final"
DRAW = ROOT / "docs/drawings"
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
    "SH-001": ("steel cutter module", "shaft centres 48.00 ±0.03 mm; rotating-to-static clearance ≥1.90 mm; CUT-08 retainer M4×12 = 3 N·m; CUT-03 pair tied by 4× CUT-09 OD10/ID6.6/L128 matched steel sleeves and M6×170 class10.9 at7 N·m; plates mount through G1J-10 feet"),
    "SH-002": ("D2 cutters / numbered match-ground steel spacers", "CUT-01 t6 and CUT-02 nominal t7; do not interchange spacers; every one of 11 axial gaps 0.25–0.50 mm over one full hand rotation by metal shim"),
    "SH-003": ("S45C QT shafts / SKF 61905-2RS1", "Ø25 h6 seats; CUT-05R key clock25.714±0.02°; shaft TIR ≤0.05 mm; centre parallelism ≤0.10/150"),
    "SH-004": ("direct-keyed steel #35 sprockets / S45C phase gears / #35 chain", "GGM_SH_12T direct-keyed to 12 h6 jackshaft with 4x4 key; GGM_SH_30T direct-keyed to CUT-05R 25 h6 with 6x6 key; keys carry torque; received maker retention hardware is axial-only and torque remains HOLD until receipt; sprocket radial TIR ≤0.10 mm; total axial shift+U95 ≤0.20 mm; chain alignment ≤0.20/150 mm; midspan slack 2–3%; DRV-02 superseded; phase stack M4×4 = 3 N·m"),
    "FD-001": ("5052-H32 hopper", "feed opening 150 × 150 mm; all reachable edges R/C ≥0.5 mm"),
    "FD-002": ("304 screen / sheet chute", "screen aperture Ø5 on 9 pitch; cutter/static clearance ≥1.90 mm"),
    "FD-003": ("304 auger/housing/common agitator shaft", "auger OD24.60; housing ID25.00 +0.05/0; radial clearance 0.20–0.25 mm; shaft/bore diametral clearance0.200–0.322; SYS-15 Ø3x12 spring pin; pitch18"),
    "EX-001": ("SCM440 screw/barrel / steel supports", "integral barrel shoulder + rear retainer; 2× M4×25 class8.8 at 2.9 N·m; cold endplay 0.12–0.28 mm; front guide axial travel ≥1.50 mm; mount M5×4 = 2.5 N·m"),
    "EX-002": ("nitrided SCM440 / NSK 51102 / 17-4PH die insert", "cold screw/barrel diametral clearance 0.28–0.32 mm; 51102 pocket clearance0.30–0.35 mm; shaft abutment≥23 mm; housing abutment≤20 mm; shim-set loaded-direction endplay0.05–0.15 mm; coaxiality ≤0.05 mm; thrust M6×8 = 9 N·m; die SYS-04 M4×45×4 stock screws cut/deburred to42.5±0.1 give engagement6.82–7.40/thread-bottom clearance0.60–1.18; digital torque1.50 N·m, physical receipt/leak/first thermal cycle NOT_RUN; retainer M4×2 = 1.2 N·m"),
    "EX-003": ("mica/NiCr heater and thermocouple candidates; TH-INS-01 secondary shield-exterior barrier after S4 qualification", "Band free-state ID34.10–34.20 and usable closure≥1.00 leave worst-case closure reserve0.277 mm; after cold tightening, 0.05 mm feeler penetration≤5 mm at 8 sectors excluding split±10° is physical NOT_RUN. HOLD T1–T3: probe unselected; OD tolerance and insertion stop unqualified. Barrel flat-bottom bore5.40±0.05 preserves conservative ligament3.345≥3.32, but does not qualify probe insertion; do not deepen or force probe to bottom. T4 insertion10/blind12 and T5 insertion4 are nominal candidates. Qualify retention, insulation and thermal response before assembly. TH-INS-01 is allowed only on the outside face of the grounded metal hot shield and must not cover heaters, barrel/die, cutoffs, probes, terminals or vents; S4 coupon smoke and P9 interface-temperature margin remain physical gates. SYS-04 die joint digital load-path PASS at1.50 N·m; physical receipt/leak/first thermal cycle NOT_RUN; shield clearance requires service verification."),
    "FM-001": ("5052 duct / donor fans", "strand centreline offset ≤0.50 mm; hot-shield clearance ≥12 mm"),
    "FM-002": ("6061 plates / silicone rollers / S45C eccentric bushes", "adjusted unloaded roller gap 1.60–1.90 mm over full rotation; bush index pair≤0.5°; roller axes parallel≤0.05/80; gauge datum alignment≤0.10 mm"),
    "SP-001": ("6061 plates / stainless shafts", "spool shaft Ø12 h6; traverse rod parallelism ≤0.10/160"),
    "GD-001": ("polycarbonate and bonded metal panels", "hazard opening ≤6 mm; no reach path to moving/hot parts"),
    "EL-001": ("2 mm 5052 enclosure", "PE bond target 0.10 ohm 이하; signal/power duct separation ≥18 mm"),
    "SV-001": ("service-envelope reference geometry", "front/rear access ≥600 mm; hot-zone removal envelope kept clear"),
}

ASSEMBLY_FIELDS = ("step_number", "part_ids_quantity", "required_tools", "fasteners", "torque", "orientation", "clearance_tolerance", "drawing", "inspection_method", "pass_fail", "next_prerequisite")
ASSEMBLY_STEPS = [
    (1, "BOM/revision traveler ×1", "document viewer; caliper", "N/A", "N/A—document gate", "v0.8 identifiers visible", "all files same revision", "GA-001", "hash and revision cross-check", "all required files present", "parts kitting"),
    (2, "FR profiles ×28; corner brackets ×28", "square; long steel tape/rule; 3/5 mm hex", "M5x12/washer/T-nut joint kits ×56", "M5 5 N·m", "470×700 base square", "base X470±0.8 mm; Y700±0.8 mm; rail squareness≤0.50/700 mm; all numeric limits include U95", "FR-001", "56 witness marks; independent X/Y and two-diagonal measurements with evidence hash; rocking check", "|diagonal A-B|+U95_A+U95_B≤1.0 mm; no rocking", "table anchors"),
    (3, "FR-ANCHOR-01 ×4", "8 mm socket; torque wrench", "M8 anchors ×4", "M8 20 N·m provisional", "load path into table", "no gap; frame level ≤0.5°", "FR-001", "witness mark and level", "four anchors engaged", "shredder frame"),
    (4, "CUT-03/CUT-08 plates ×2 each; CUT-09 sleeves ×4; G1J-10 feet ×4", "square; 3/5 mm hex; 10 mm socket/spanner; torque wrench", "bearing retainer M4 ×12; FST-21 M6×170 class10.9 ×4; FST-02/FST-03 M6×20 class8.8 ×16", "retainer M4 3 N·m; chamber tie M6 7 N·m; foot joints M6 9 N·m", "bearing datums inward; four CUT-09 steel sleeves span the128 mm inner-face gap; four chamber ties pass through both CUT-03 plates and sleeves; upper two also pass through PPR-C02 clearance holes without clamping the polymer; each plate mounts to two G1J-10 steel feet and the feet mount to G1J-01/profile", "shaft centres48.00±0.03 mm; inside plate gap128.00±0.06 mm; four-sleeve matched length spread≤0.03 mm; plate perpendicularity≤0.20/125", "SH-001/SH-003", "CMM/caliper centre distance and inside gap at four tie positions; verify every sleeve is metal-to-metal seated; 12 retainer +4 tie +16 foot-joint witness marks", "pair parallel; retainer clears seal/inner ring; no printed part lies in chamber or plate-to-profile compression path", "bearings/shafts dry-fit"),
    (5, "CUT-05 ×1; CUT-05R ×1; SKF 61905-2RS1 ×4; CUT-10 ×4", "arbor press; micrometer; optical index", "Ø25 metal collars", "collar screw per maker", "left key datum0°; right all-key datum25.714°", "Ø25 h6; key clock±0.02°; TIR≤0.05 mm", "SH-003", "micrometer, optical comparator and dial indicator", "free rotation without preload; CUT-10 contacts outer ring only", "cutter stack"),
    (6, "CUT-01 ×12; numbered CUT-02 ×10", "shim set; feeler gauge", "keys and 0.05/0.10/0.25 mm metal shims", "collars per drawing", "install each spacer at its engraved shaft/position; hooks counter-rotate; phase offset", "all 11 axial gaps 0.25–0.50 mm over one full rotation", "SH-002", "feeler sweep every gap, then hand rotate 20 revolutions; record position map", "all gaps accepted; no disc/static contact", "phase drive"),
    (7, "GGM shredder drive set; direct-keyed GGM_SH_12T/GGM_SH_30T; DRV-03/DRV-03R", "straightedge; dial indicator; optical index; torque wrench; receipt packet", "phase gear M4 ×4; received 12T/30T axial-retention hardware", "phase M4 3 N·m; sprocket retention torque HOLD until receipt/maker value", "K9DG60N2+K9G75C → keyed GGM protection coupling → 6201-supported jackshaft → direct-keyed GGM_SH_12T:#35:GGM_SH_30T → CUT-05R; 4x4/6x6 keys carry sprocket torque; DRV-03/DRV-03R retain cutter phase; DRV-02 is superseded", "GGM mount as-drawn compatibility required; pair backlash0.120–0.140 mm; combined digital phase≤1.0°; sprocket radial TIR≤0.10 mm; sprocket total axial shift+U95≤0.20 mm; chain alignment≤0.20/150 mm; midspan slack2–3%; no tight spot in20 hand turns", "SH-004 + GGM drive contract/component register", "authenticated GGM receipt/mount result; received sprocket bore/key/retention identity; blue-check key flank contact; axial-shift and radial-TIR dial checks; optical clocking; hand rotation; P3 current/torque/protection evidence", "HOLD: GGM receipt/mount, keyed sprocket axial retention and P3 physical bench remain NOT_RUN; friction-only/set-screw-only torque path prohibited", "shredder guard"),
    (8, "DRV-GD-01 and interlock ×1", "2.5/3 mm hex; gap probe", "M4 guarded fasteners", "M4 3 N·m", "cover removable only under lockout", "hazard opening≤6 mm", "GD-001", "reach probe and switch actuation", "no reach path; forced-open works", "feed path"),
    (9, "IN-HOP-01/CUT-04/FD-HOP-01 ×1 set", "riveter; 3 mm hex", "M4/rivets", "M4 3 N·m", "flow down into screen", "cutter/static clearance≥1.90 mm", "FD-001/FD-002", "feeler gauge and burr check", "no sharp edge or cutter contact", "flake bin"),
    (10, "FD-BIN-01/FD-MET-01..03/FD-DA-01/FD-CP-01 ×1 set", "caliper; bore gauge; 3 mm pin punch; dial indicator", "SYS-15 Ø3x12 lower + Ø3x18 upper spring pins; M4/M6 mount hardware", "SYS-15 N/A; mount torque receipt-gated", "key EG17-G10 into FD-CP-01; install both matched pins; bolt FD-DA-01 only to metal frame", "auger radial clearance0.20–0.25; coupling diametral clearance0.050–0.102; gearbox axis≤0.10 mm", "FD-003", "pin gauge/micrometer; coupling TIR; 10 hand turns; 2.2 N.m torque-arm and 24 PPR tach test", "digital reference defined; purchase/receipt and physical tests remain HOLD", "extruder support"),
    (11, "rear datum/front guide/rail/collar/retainer ×1; matched spacer ×2", "dial indicator; 3/4 mm hex; torque wrench", "M5 hot-mount hardware ×4; M4×25 class8.8 ×2", "M5 2.5 N·m; dry M4 2.9 N·m candidate", "integral shoulder captured by rear retainer through 4.20 mm matched spacers; front radial sliding", "axis≤0.20/390; cold axial free travel≥1.50 mm; cold endplay 0.12–0.28 mm; first thermal cycle hard-stop contact 0", "EX-001", "dial sweep, feeler/endplay and travel gauge; record material certificate and torque witness; first authorized thermal cycle records axial motion/hard-stop clearance", "digital geometry/strength PASS; physical endplay, preload retention and thermal-cycle inspection NOT_RUN", "physical inspection approval before screw/barrel"),
    (12, "EX-THR-01/EX-SCR-01/EX-BAR-01/NSK 51102 + GGM extruder drive ×1 set", "micrometer; bore/depth gauge; dial indicator; torque wrench; receipt packet", "M6×20 class 8.8 thrust-plate fasteners ×8; 0.05–0.30 mm ground steel shim selection", "M6 9 N·m", "51102 shaft washer against integral Ø23 shoulder; housing washer in marked-face pocket; K9DG60N2+K9G150C direct keyed protection coupling with 6201 rear radial support; gearbox carries no extrusion thrust", "screw/barrel diametral0.28–0.32 mm; pocket diametral0.30–0.35 mm; loaded-direction endplay0.05–0.15 mm; GGM mount as-drawn compatibility required", "EX-002 + GGM manufacturing r2", "bearing marking/height, seat/pocket/abutment limits, blue-check washer ribs, three-station bore/OD, dial endplay/free rotation, authenticated GGM receipt/mount result and P3 drive evidence", "HOLD: digital dimensions PASS; GGM receipt/mount/P3 drive evidence, physical endplay and hot rotation remain NOT_RUN", "die/hot zone"),
    (13, "EX-DIE-01..05; heater/TC ×1 set", "insulation meter; torque wrench; depth gauge; 0.05 mm feeler; 20 N pull gauge", "M4x45 class 10.9 SHCS cut/deburred to 42.5 +/-0.1 ×4; M4 retainer screws ×2; SYS-17 M3×8 ×8", "SYS-04 1.50 N·m dry design torque; SYS-17 0.5 N·m", "band free-state ID34.10–34.20; usable closure≥1.00; EX-DIE-05 issued2; TH-TC-01 Tempco MTA1 T1–T4 with supplier-welded stops", "band closure reserve≥0.25 mm; T1–T3 probe Ø3.00±0.03 in bore3.20–3.25, stop5.20±0.05, tip gap0.10–0.30; T4 stop10.00±0.05 in depth11.95–12.05; TH-TCR-01 bridge captures collar; never clamp MI sheath", "EX-002/EX-003", "verify band contact; vendor drawing; probe dimensions and ≥100 MΩ at100 VDC; 20 N pull motion≤0.10 cold/hot; coupon bias≤2°C and t90≤30s; SYS-04 physical receipt/leak/first thermal cycle remains NOT_RUN", "HOLD: supplier drawing, receipt/thermal tests and band contact; SYS-04 digital load-path PASS but physical receipt/leak/first thermal cycle NOT_RUN", "센서 수령시험 및 체결 HOLD 해소 전 다음 단계 진행 금지"),
    (14, "CO-01/CO-02 ×1 set", "calibrated anemometer; 3 mm hex", "M4 clamps", "M4 3 N·m", "airflow across strand away from hot zone", "strand centreline≤0.50 mm", "FM-001", "route and service removal check", "no hot contact; feedback wired", "gauge"),
    (15, "gauge mechanism ×1", "gauge block; caliper", "M3 hardware", "M3 1.2 N·m", "U95 axes normal to strand", "datum alignment≤0.10 mm", "FM-002", "gauge block repeatability check", "mechanical repeatability recorded", "puller"),
    (16, "FM-PL/RL/AX/EB/GR/GA ×1 set", "feeler gauge; dial indicator; 2.5/3 mm hex", "M3 eccentric-bush clamps plus M4 guard and metal collars", "M3 1.2 N·m; M4 3 N·m", "FM-EB-01 pair at equal index; fixed and adjustable roller axes parallel", "unloaded full-rotation gap1.60–1.90 mm; bush index pair≤0.5°; parallel≤0.05/80; TIR≤0.05 mm", "FM-002", "feeler sweep over one full rotation, index and hand-feed check", "gap remains in range; no pinch bypass, bush slip or bind", "spooler"),
    (17, "SP-DA/AX/RL/SH/BP/MM/TR/DS ×1 set", "square; dial; 3 mm hex", "M4 plus collars", "M4 3 N·m", "traverse parallel to spool", "rod parallel≤0.10/160 mm", "SP-001", "full-stroke hand traverse", "no collision in service envelope", "all guards"),
    (18, "GD panels/interlocks ×1 set; TH-INS-01 qualified shield-exterior cut set ×1", "gap probe; 3 mm hex; scissors/roller for qualified tape", "captive M4 hardware; tape has no structural/safety fastener role", "M4 3 N·m; tape N/A", "labels outward; service panels keyed; TH-INS-01 only on outside face of grounded metal hot shield after S4 coupon PASS; no heater/barrel/die/cutoff/probe/terminal/vent coverage", "openings≤6 mm at hazards; tape adhesive-interface peak+U95+30 C≤documented continuous rating; cooldown edge lift+U95≤2.0 mm", "GD-001/SV-001 + control/thermal_barrier_tape_contract.json", "reach/access/removal test; S4 coupon evidence; P9 interface/outer-surface temperature and cooldown edge-lift record", "all hazards covered; no smoke/char/melt/adhesive flow; tape does not obstruct sensing, cutoff, terminals or ventilation", "enclosure/PE"),
    (19, "CT-ENC-01 ×1; PE-01..04 bonds ×4", "DMM; torque wrench", "M4x10/two tooth washers/all-metal nut ×4 sets", "M4 3 N·m", "PE first; ducts segregated", "bond target 0.10 ohm 이하; separation≥18 mm", "EL-001", "four-wire continuity where available", "all four bonds and witness marks recorded", "power wiring"),
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
#danger[*물리 검증·안전 인증·통전 승인이 아니다.* E-stop, lid/service interlock, branch fuse, 독립 thermal fuse를 정상 firmware와 독립 구현하고 exact received component 정격·배선·보호소자를 실측 확인하기 전 통전하지 않는다.]
Revision: `{REV}` · 상태: `DIGITAL_DOCUMENT / PHYSICAL_NOT_RUN / USER_APPROVAL_REQUIRED`

{body}
'''


def typst_binary() -> str:
    candidates = [shutil.which("typst"), *sorted(Path("/nix/store").glob("*-typst-*/bin/typst"))]
    for candidate in candidates:
        if candidate and subprocess.run([str(candidate), "--version"], capture_output=True).returncode == 0:
            return str(candidate)
    raise SystemExit("required tool unavailable: typst")


def compile_typ(path: Path, output: Path | None = None) -> None:
    env = os.environ.copy(); env["SOURCE_DATE_EPOCH"] = "946684800"
    subprocess.run([typst_binary(), "compile", str(path), str(output or path.with_suffix(".pdf")), "--root", str(ROOT)], check=True, cwd=ROOT, env=env)


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
            "drawing_number": number, "part_assembly_id": number, "revision": "final-design-fabrication-closure-v0.8", "units": "mm",
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


def assembly_rows() -> list[dict[str, str]]:
    rows = {int(row[0]): dict(zip(ASSEMBLY_FIELDS, map(str, row))) for row in ASSEMBLY_STEPS}
    active = json.loads((ROOT / "release/active_part_set.json").read_text(encoding="utf-8"))["parts"]
    assert len({item["part_id"] for item in active}) == len(active), "duplicate active part"
    parts: dict[int, list[str]] = {}
    for item in active:
        step = assembly_step_number(item["part_id"])
        assert step in rows, f"unknown assembly step: {item['part_id']}"
        parts.setdefault(step, []).append(f"{item['part_id']} ×{item['quantity']}")
    supplements = {1: "BOM/revision traveler ×1", 2: "FR profiles ×28; corner brackets ×28",
                   5: "SKF 61905-2RS1 ×4", 19: "PE-01..04 bonds ×4"}
    for step, entries in parts.items():
        rows[step]["part_ids_quantity"] = "; ".join(sorted(entries) + ([supplements[step]] if step in supplements else []))
    joints: dict[int, list[dict[str, object]]] = {}
    for joint in fasteners():
        joints.setdefault(fastener_step_number(joint), []).append(joint)
    for step, entries in joints.items():
        # Metal-only defaults must never be used on the lower-torque printed interfaces.
        system = any(str(joint["joint_id"]).startswith("SYS-") for joint in entries)
        for field, values in (
            ("fasteners", [f"{joint['joint_id']}: {joint['specification']} ×{joint['quantity']}" for joint in entries]),
            ("torque", [f"{joint['joint_id']}: {joint['torque_Nm']} N·m" for joint in entries]),
        ):
            if not system:
                values.insert(0, "non-printed interfaces only: " + rows[step][field])
            rows[step][field] = "; ".join(values)
        held = [joint for joint in entries if str(joint["verification_state"]).startswith("HOLD")]
        if held:
            rows[step]["inspection_method"] += "; " + "; ".join(f"{j['joint_id']}: {j['inspection']}" for j in held)
            rows[step]["pass_fail"] = "HOLD: 미검증 체결품이 있어 조립 합격 불가; " + rows[step]["pass_fail"]
            rows[step]["next_prerequisite"] = "진행 금지: 체결 규격·토크 검증 및 승인 후 다음 단계"
    rows[1]["orientation"] += "; EX-CPN-BAR/EX-CPN-SCR are process witnesses, not installed parts"
    return list(rows.values())


def manuals() -> None:
    steps = assembly_rows()
    with (FINAL / "assembly_steps.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ASSEMBLY_FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(steps)
    step_text = []
    for data in steps:
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

부품 수량은 `release/active_part_set.json`의 출고/검사 단위이며 assembly ID는 중복 구매하지 않는 참조다. 공정 witness, qualification coupon과 교체용 gasket은 해당 단계의 설치품과 구분한다. `SYS-*` 체결값은 `release/build_bom_release.py::fasteners`, `PR-*` 값은 `exports/print/print_manifest.csv`에서 BOM과 함께 생성한다. 금속 조인트 기본 토크를 출력물에 적용하지 않는다. 표에 없는 donor/구매품 체결은 수령품 제조사 값과 실측 승인 전 HOLD다.

'''
    write(complete, typ("v0.8 실행용 조립 매뉴얼", intro + "\n".join(step_text)))
    compile_typ(complete)
    with (ROOT / "exports/final/interface_catalog.csv").open(encoding="utf-8", newline="") as fh:
        interfaces = list(csv.DictReader(fh))
    interface_summary = f"Source-pinned unified catalog {len(interfaces)}행(alias reconciliation 포함): {sum(row['status'] == 'PASS' for row in interfaces)} PASS / {sum(row['status'] == 'HOLD' for row in interfaces)} HOLD. Exhaustive mating coverage는 HOLD다."
    bodies = {
        "exploded_views_ko": "== 조립 순서\n\nFrame → shredder frame → bearing/shaft → cutter stack → phase gear/chain/motor/shear fuse → screen/recirculation/hopper → flake bin → feeder → extruder/thrust → heater/sensor/die → hot shield → cooling → gauge → puller → spooler/traverse → guards → enclosure → wiring → firmware → calibration → dry checks.\n\n각 단계의 형상은 `assembly_drawing_set.pdf` 해당 도면 번호를 사용한다. 고하중 경로는 metal part → bearing/plate → aluminum profile → table이다.",
        "tolerance_and_fit_guide_ko": "== 기준\n\n" + interface_summary + "\n\n`exports/final/interface_catalog.csv`가 critical interface별 nominal/tolerance/검사법과 source HOLD를 지배한다. HOLD 또는 NOT_EVALUATED 행은 조립·가공 승인 기준이 아니다. Cutter/blade clearance는 출력 공차가 아닌 ground metal shim으로 조절한다. Bearing seat, die insert, screw/barrel cold/hot clearance, rear datum/front sliding travel을 조립 전 측정한다.\n\n#gate[측정기 ID·교정상태·온도·실측값을 기록하고 허용범위를 벗어나면 임의 rework 대신 source parameter와 도면 revision을 갱신한다.]",
        "electrical_assembly_ko": "== 순서\n\nPE bond → PSU 미통전 설치 → branch fuse → hardwired safety chain → drivers/MOSFET → logic → sensors → cable clamp 순이다. `exports/final/electrical`의 세 CSV와 8개 벡터 PDF를 작업표로 사용한다.\n\n#gate[전원 분리 상태에서 PE continuity, insulation, polarity, fuse/terminal ID, forced-open safety contact를 독립 검사한다.]",
        "firmware_and_calibration_ko": "== Firmware\n\nReleased HEX는 `exports/final/firmware/binaries/filament_recycler_atmega2560.hex`; build evidence는 `validation/results/arduino_mega_compile.json`이다. Source/HEX hash 일치를 검증하고 Mega 2560 target/fuse setting을 확인한다.\n\n== Calibration\n\nReceived GGM label/serial을 receipt packet과 대조한 뒤 A0 shredder current, A9 extruder current, shredder/screw tach, puller/spooler tach, traverse limits, X/Y gauge U95, dancer, cooling current와 fan tach를 각각 교정한다. EEPROM CRC/revision/unit/range가 유효하지 않으면 production ready를 금지한다.",
        "maintenance_manual_ko": """== Lockout

Main disconnect OFF, 0 V 확인과 재투입 방지, cutter/screw mechanical block 및 사용자 확인 뒤 작업한다. E-stop만으로 jam을 제거하지 않는다. 잔류 압력과 저장 에너지를 해제하고 충분히 냉각한다. 기존 60 °C 기준만으로 접촉 안전을 보증하지 않으며, 온도 표시값만으로 내부 냉각 완료를 판단하지 않는다.

== 주기 점검

매 사용 전 guard/interlock/PE/cable/누설; 매 lot cutter clearance·screen·die; 정기적으로 chain tension, bearing play, witness mark, fuse/thermal cutoff, calibration drift를 기록한다. Cutter·gasket·shear fuse replacement 기준은 제조도면과 실측 이력으로 관리한다.

== Hot-zone 유지판 접근 — 절차 미승인 / HOLD

현재 정식 CAD의 차열판을 단순히 위로 들어내지 않는다. FreeCAD 기준 조립 검사에서 상향 5 mm 위치에 T1–T4 프로브, 히터 리드 및 주변 부품 간섭이 있다. 배선을 당기거나 프로브를 지렛대로 사용하지 않는다. 전기적 분리만으로 금속 sheath가 차열판에서 빠지는 것은 아니다.

유지판 후보의 긴 직선 드라이버 접근은 간섭한다. 차열판이 없는 상태의 짧은 L형 공구 회전 공간 검사는 부분 증거일 뿐, 차열판 탈거·공구 삽입·손 공간을 승인하지 않는다.

12×52 mm 점검창과 28×68×2 mm 덮개는 미채택 후보다. 후보의 덮개 탈거20 mm 및 공구 회전 공간은 명목 CAD 검사에서 간섭이 없지만, 체결품·탈락 방지·PE 본딩·차열 성능은 미검증이다. 이 문서를 근거로 기존 차열판을 절단하거나 후보 부품을 설치하지 않는다.

정비 절차 해제 조건: 채택된 CAD/도면과 부품 목록 일치, 체결품 및 본딩 방식 확정, 실제 공구와 손의 접근·부품 탈거 경로 검증, 물리적 lockout 및 사용자 확인. 재조립 후 차열판/덮개 고정, PE 연속성, 배선 손상·장력, 센서 삽입/고정을 검사하고 해당 시운전 gate를 다시 수행한다. 기록 항목은 작업자·날짜·부품 revision·분리한 커넥터·검사값·미해결 사항·승인자다. 현재 실제 정비 시험은 NOT_RUN이다.
""",
    }
    for name, body in bodies.items():
        p = FINAL / f"{name}.typ"; write(p, typ(name.replace("_ko", "").replace("_", " "), body)); compile_typ(p)


def commissioning() -> None:
    transition = """== 상태 전이\n\n`assembly complete` → `electrical inspection complete` → `safe for low-voltage logic` → `safe for motors` → `safe for heaters` → `safe to process plastic`. 이 전이는 실제 장치의 물리 단계에 적용한다. 앞 단계의 서명·측정 증거와 해당 단계의 별도 사용자 승인이 없으면 다음 단계로 이동하지 않는다. 문서 작성·호스트 테스트·시뮬레이션의 진행이나 완료를 승인하는 절차는 아니다.\n"""
    def procedure(inputs: str, method: str, evidence: str, acceptance: str) -> str:
        return f"== 입력\n\n{inputs}\n\n== 방법\n\n{method}\n\n== 증거\n\n{evidence}\n\n== 수치 합격기준\n\n{acceptance}"

    items = {
        "pre_power_checklist_ko": procedure(
            "Released BOM/도면, 교정 유효 DMM·절연계·토크렌치, exact received component label/serial, 미통전·lockout 상태.",
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
            "TC mapping 오류 0건; valid range -20–300 °C; 120 s 가열 명령에서 최소 +4 °C 아니면 fault; command-off 60 s 동안 +8 °C면 fault; software overtemperature 285 °C 이전 차단; cold axial travel ≥1.50 mm."),
        "shredder_commissioning_ko": procedure(
            "P3 physical release PASS, 정확히 2장 CUT-01 P4 coupon, closed GGM guards, calibrated A0 current/torque/RPM, PLA 1.2/2.0/3.0 mm와 PET body/folded-seam coupon.",
            "No-load에서 약 16 rpm cutter speed를 기록한 뒤 P4 재료 coupon을 낮은 투입률로 시험한다. P3에서 보정한 software gearbox torque limit 8.0 N·m가 정상 처리 중 반복되면 feed를 낮추고 원인을 기록하며 보호값을 올리지 않는다. Controlled jam은 bounded reverse 최대 3회 후 미복구 시 latched fault로 끝내고 자동 재시작을 허용하지 않는다. 8.8–9.3 N·m mechanical protection은 P3에서 독립 quasi-static coupon으로 선행 검증한다. Full 12-disc stack은 P4 PASS 전 제작/조립하지 않는다.",
            "P3 release/evidence manifest, P4 torque-current-RPM CSV, jam recovery log, chip-size/회수율 기록, guard/interlock 및 손상 검사 사진.",
            "영구 구조·key·guard 손상 0건; jam retry≤3이고 미복구 3차 실패는 latched fault; 자동 재시작 0건; oversize recirculation≤1; 3–6 mm 질량분율≥70%, >20 mm PET strip≤2%, fines≤15%, 회수율≥95%. P3 mechanical protection은 U95 포함 8.8–9.3 N·m 및 파단 후 자유회전/허브·키 무손상."),
        "PLA_process_startup_ko": procedure(
            "확인된 단일 PLA lot, 외부 건조 coupon, clean path, calibrated T1–T5/gauge/tach/cooling.",
            "180/195/205 °C barrel과 200 °C die가 ±5 °C band에 든 뒤 low feed로 시작하고 10 s 안정 구간 20개 sample을 기록한다.",
            "Lot/moisture 기록, 온도·screw/puller/spool RPM, X/Y diameter·ovality·U95, 실제 질량/시간.",
            "Mean diameter error ≤0.05 mm; ovality ≤0.05 mm; U95 ≤0.03 mm; 20개 연속 valid; cooling current 0.2–2.0 A와 fan 2채널 tach valid. 200 g/h는 목표일 뿐 필수 release 기준이 아니다."),
        "PET_process_startup_ko": procedure(
            "확인된 단일 PET lot과 오염·수분 coupon, all-metal hot path, 실제 정격 확인된 300 °C급 wiring/cutoff, calibrated sensors.",
            "245/260/270 °C barrel과 265 °C die가 ±5 °C band에 든 뒤 guarded low-feed first-hot-test를 수행한다. PLA 결과를 재사용하지 않는다.",
            "Lot/moisture·오염 기록, 온도/압력 징후, relief/leak 영상, X/Y diameter·ovality·U95, 실제 질량/시간.",
            "Mean diameter error ≤0.05 mm; ovality ≤0.05 mm; U95 ≤0.03 mm; 20개 연속 valid; 가열 전 cold axial travel ≥1.50 mm이고 hot run 중 hard-stop 접촉 0; 누설 0건; relief coupon은 별도 승인된 절차의 실제 결과만 사용."),
        "material_change_purge_ko": procedure(
            "이전/다음 material ID, verified screw tach, waste path, T1–T5, clean screen/hopper 도구.",
            "이전 material profile에서 waste path로 purge하고 시간·실제 screw 회전을 동시에 적산한다. Screen/hopper 청소와 다음 profile 전이를 각각 확인한다.",
            "Material-session log, screw RPM/revolution trace, purge 영상·폐기물 사진/실측 질량, 청소 signoff.",
            "Purge ≥120 s AND actual screw ≥32 rev; 모든 zone target ±5 °C; visual contamination 0; screen/hopper signoff 완료; 종료 후 모든 hot point 60 °C 미만."),
        "physical_validation_plan_ko": procedure(
            "승인된 coupon/fixture, calibrated instruments, 각 gate 작업자·독립 검토자, lockout/원격 E-stop.",
            "P0 23-gate digital prerequisite → P1 inventory/receipt → P2 cold fit → P3 GGM bench → P4 two-cutter coupon → P5 process coupon → P6 cold extruder → P7 safety/logic → P8 motor dry-run → P9 empty hot-zone → P10 PLA → P11 PET → P12 forming/spool 순서로 진행한다. 각 물리 단계는 별도 사용자 승인 전 NOT_RUN이다.",
            "Gate별 입력·방법·원시 CSV/사진/video·판정·서명. Simulation 값은 시험 결과 칸에 복사하지 않는다.",
            "GGM: software gearbox torque limit 8.0 N·m, mechanical protection 8.8–9.3 N·m 실측; cutter는 CUT-01 2개 coupon 선행. Electrical: PE≤0.10 Ω·자동재기동 0. Hot-zone: cold axial travel≥1.50 mm, SYS-04 42.5±0.1 mm/1.50 N·m, 실제 누설은 first-hot-test에서 확인. Forming: diameter/ovality≤0.05 mm, U95≤0.03 mm target; spool: 68 mm traverse, dancer stop 0.36 rad 이전, hard-stop 0.4363 rad 비접촉."),
    }
    gate_rows = [
        ("assembly incomplete", "assembly complete", "all 25 assembly_steps rows signed; dimensions and guards inspected", "independent mechanical reviewer + user", "NOT_RUN"),
        ("assembly complete", "electrical inspection complete", "PE continuity, insulation, polarity, fuse IDs and point-to-point wiring PASS", "qualified electrical reviewer + user", "NOT_RUN"),
        ("electrical inspection complete", "safe for low-voltage logic", "current-limited logic rail; hardwired chain forced-open; outputs safe at reset", "electrical reviewer + user", "NOT_RUN"),
        ("safe for low-voltage logic", "safe for motors", "received GGM/driver labels and ratings confirmed; P3 current/torque protection evidence; direction, tach and stop tests one branch at a time", "mechanical/electrical reviewers + user", "NOT_RUN"),
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
