#!/usr/bin/env python3
"""v0.8 전장 벡터 도면과 재현 가능한 Arduino 릴리스를 생성·검사한다."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ELEC = ROOT / "exports/final/electrical"
FW = ROOT / "exports/final/firmware"
SOURCE = ROOT / "firmware/arduino_mega"
REV = "final-design-fabrication-closure-v0.8"
FQBN = "arduino:avr:mega"
DIAGRAMS = ("system_block_diagram", "power_distribution", "full_wiring_diagram", "safety_chain",
            "Arduino_Mega_pinmap", "grounding_bonding", "enclosure_layout", "cable_routing")
WIRE_FIELDS = ("wire_id", "from", "to", "voltage", "maximum_current", "wire_gauge", "colour",
               "connector", "terminal", "fuse", "routing", "shield_ground", "strain_relief")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def tool(name: str) -> str:
    candidates = [shutil.which(name), *sorted(Path("/nix/store").glob(f"*-{name}-*/bin/{name}"))]
    flag = "version" if name == "arduino-cli" else "--version"
    for candidate in candidates:
        if candidate and subprocess.run([str(candidate), flag], capture_output=True).returncode == 0:
            return str(candidate)
    raise SystemExit(f"required tool unavailable: {name}")


def row(wire_id: str, source: str, destination: str, voltage: str, current: str,
        gauge: str, colour: str, connector: str, terminal: str, fuse: str,
        routing: str, shield: str, strain: str) -> dict[str, str]:
    return dict(zip(WIRE_FIELDS, (wire_id, source, destination, voltage, current, gauge, colour,
                                  connector, terminal, fuse, routing, shield, strain), strict=True))


def power_wires() -> list[dict[str, str]]:
    u = "DONOR/SITE_VERIFICATION_REQUIRED"
    wires = [
        row("AC-L", "AC inlet L", "PSU L", "100–240 VAC", "8 A design maximum at 100 VAC", ">=1.5 mm2 Cu 90 C; local code may increase", "brown", "mains terminal", "TB-AC-L", "site OCPD <=16 A", "mains duct", "PE separate", "gland + clamp"),
        row("AC-N", "AC inlet N", "PSU N", "100–240 VAC", "8 A design maximum at 100 VAC", ">=1.5 mm2 Cu 90 C; local code may increase", "blue", "mains terminal", "TB-AC-N", "site OCPD <=16 A", "mains duct", "PE separate", "gland + clamp"),
        row("PE-01", "AC inlet PE", "frame PE stud", "PE", "site OCPD <=16 A fault path", ">=1.5 mm2 Cu green/yellow; local code may increase", "green/yellow", "ring lug", "PE-STUD", "site OCPD <=16 A", "short dedicated bond", "protective earth", "tooth washer + clamp"),
        row("PE-02", "frame PE stud", "enclosure backplate", "PE", "site OCPD <=16 A fault path", ">=1.5 mm2 Cu green/yellow; local code may increase", "green/yellow", "ring lug", "PE-ENC", "site OCPD <=16 A", "dedicated bond", "protective earth", "tooth washer + clamp"),
        row("PE-03", "frame PE stud", "metal hot shield", "PE", "site OCPD <=16 A fault path", ">=1.5 mm2 Cu green/yellow; 300 C sleeve", "green/yellow", "ring lug", "PE-HOT", "site OCPD <=16 A", "away from sensors", "protective earth", "tooth washer + hot clamp"),
        row("PE-04", "frame PE stud", "motor frames", "PE", "site OCPD <=16 A fault path", ">=1.5 mm2 Cu green/yellow; local code may increase", "green/yellow", "ring lug", "PE-MOTOR", "site OCPD <=16 A", "power route", "protective earth", "tooth washer + clamp"),
        row("24-MAIN+", "PSU +24 V", "F-MAIN", "24 VDC", "25 A PSU maximum", ">=6 mm2 Cu 90 C", "red", "locking DC terminal >=30 A 60 VDC", "TB24+", "F-MAIN 30 A DC", "high-current duct", "paired 0 V", "both ends clamped"),
        row("24-MAIN-", "PSU 0 V", "0 V star", "0 VDC", "25 A PSU maximum", ">=6 mm2 Cu 90 C", "black", "locking DC terminal >=30 A 60 VDC", "TB24-", "F-MAIN upstream", "high-current duct", "functional 0 V; not PE", "both ends clamped"),
    ]
    branches = (
        ("LOGIC", "F-MAIN", "Mega + sensors", "3 A design limit", ">=0.75 mm2 Cu", "F-LOGIC 3 A DC", "logic duct"),
        ("SAFE", "F-MAIN", "hardwired safety feed", "1 A design limit", ">=0.5 mm2 Cu", "F-SAFE 1 A DC", "safety duct"),
        ("SH", "K0 contactor", "shredder H-bridge", "20 A branch limit", ">=2.5 mm2 Cu", "F-SH 20 A DC", "motor duct"),
        ("SCREW", "K0 contactor", "screw driver", "10 A design envelope", ">=1.5 mm2 Cu", "F-SCREW 10 A DC", "motor duct"),
        ("FEED", "K0 contactor", "FD-MET auger/agitator driver", "5 A design envelope; donor must be <=5 A", ">=0.75 mm2 Cu", "F-FEED 5 A DC", "motor duct"),
        ("PULL", "K0 contactor", "puller driver", "5 A design envelope; donor must be <=5 A", ">=0.75 mm2 Cu", "F-PULL 5 A DC", "forming duct"),
        ("SPOOL", "K0 contactor", "spooler/traverse drivers", "5 A combined design envelope; donors must total <=5 A", ">=0.75 mm2 Cu", "F-SPOOL 5 A DC", "forming duct"),
        ("FAN", "K0 contactor", "cooling fan pair", "3 A design envelope", ">=0.75 mm2 Cu", "F-FAN 3 A DC", "forming duct"),
    )
    for tag, source, dest, current, gauge, fuse, route in branches:
        wires += [
            row(f"24-{tag}+", source, dest, "24 VDC", current, gauge, "red", f"J-{tag}", f"TB-{tag}+", fuse, route, "paired 0 V; shield separate", "locking plug + clamp"),
            row(f"24-{tag}-", dest, "0 V star", "0 VDC", current, gauge, "black", f"J-{tag}", f"TB-{tag}-", fuse, route, "functional 0 V; not PE", "locking plug + clamp"),
        ]
    for i, dest in enumerate(("heater Z1", "heater Z2", "heater Z3", "die heater"), 1):
        wires += [
            row(f"24-H{i}+", f"K0 via MOS-H{i}", dest, "24 VDC", "5 A design maximum", ">=0.75 mm2 Cu; 300 C sleeve", "red", f"J-H{i} locking high-temp >=5 A 60 VDC", f"TB-H{i}+", f"F-H{i} 5 A DC + thermal fuse", "separate hot route", "grounded metal shield", "metal P-clamp"),
            row(f"24-H{i}-", dest, "heater 0 V star", "0 VDC", "5 A design maximum", ">=0.75 mm2 Cu; 300 C sleeve", "black", f"J-H{i} locking high-temp >=5 A 60 VDC", f"TB-H{i}-", f"F-H{i} upstream", "separate hot route", "functional 0 V; shield PE-03", "metal P-clamp"),
        ]
    chain = (("F-SAFE", "S0 E-stop NC"), ("S0 E-stop NC", "S1 lid NC"),
             ("S1 lid NC", "S2 service NC"), ("S2 service NC", "TF independent thermal cutoff"),
             ("TF independent thermal cutoff", "K0 contactor A1"), ("K0 contactor A2", "0 V star"))
    for i, (source, dest) in enumerate(chain, 1):
        wires.append(row(f"SAFE-{i:02d}", source, dest, "24 VDC" if i < 6 else "0 VDC", "1 A design maximum", ">=0.5 mm2 Cu; hot-rated at TF", "red" if i < 6 else "black", "positive-opening/locking terminal >=1 A 60 VDC", f"SAFE-{i}", "F-SAFE", "dedicated safety duct", "paired return; not PE", "both ends clamped"))
    return wires


OUTPUTS = {"SHREDDER_DIR_PIN", "SHREDDER_REVERSE_PIN", "SHREDDER_ENABLE_PIN", "SCREW_DIR_PIN",
           "SCREW_ENABLE_PIN", "PULLER_DIR_PIN", "PULLER_ENABLE_PIN", "SPOOLER_DIR_PIN",
           "SPOOLER_ENABLE_PIN", "TRAVERSE_STEP_PIN", "TRAVERSE_DIR_PIN", "TRAVERSE_ENABLE_PIN",
           "FAN_TACH_MUX_SELECT_PIN", "FEEDER_DIR_PIN", "FEEDER_ENABLE_PIN", "FEEDER_PWM_PIN", "SHREDDER_PWM_PIN", "SCREW_PWM_PIN",
           "PULLER_PWM_PIN", "SPOOLER_PWM_PIN", "COOLING_PWM_PIN", "HOPPER_PTC_PIN",
           "THERMOCOUPLE_SCK_PIN"}


def pins() -> list[tuple[str, str]]:
    text = (SOURCE / "src/board_config.h").read_text(encoding="utf-8")
    result = re.findall(r"constexpr uint8_t ([A-Z0-9_]+_PIN) = ([A-Z][0-9]+|[0-9]+);", text)
    for name, values in re.findall(r"constexpr uint8_t (HEATER_PINS|THERMOCOUPLE_CS_PINS)\[\d+\] = \{([^}]+)\};", text):
        result += [(f"{name}_{i}", value.strip()) for i, value in enumerate(values.split(","), 1)]
    if len(result) < 45:
        raise SystemExit(f"pin parser incomplete: {len(result)}")
    return result


def signal_wires(pin_rows: list[tuple[str, str]]) -> list[dict[str, str]]:
    wires = []
    for name, pin in pin_rows:
        target = name.removesuffix("_PIN").replace("_", " ").title()
        output = name in OUTPUTS or name.startswith(("HEATER_PINS_", "THERMOCOUPLE_CS_PINS_", "THERMOCOUPLE_SCK"))
        source, dest = (f"Mega {pin}", target) if output else (target, f"Mega {pin}")
        shielded = any(key in name for key in ("TACH", "CURRENT", "GAUGE", "DANCER", "THERMOCOUPLE", "FAULT"))
        wires.append(row(f"SIG-{pin}", source, dest, "5 V logic/interface dependent", "0.1 A design maximum", ">=0.25 mm2 Cu; interface level verify", "white + ID", f"J-{pin}", pin, "F-LOGIC upstream", "sensor duct; separated from PWM/motor" if shielded else "logic/control duct", "shield at enclosure end only" if shielded else "logic 0 V; not PE", "service loop + clamp"))
    return wires


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def svg(title: str, subtitle: str, nodes: list[tuple[int, int, int, int, str, str]],
        edges: list[tuple[int, int, int, int, str, str]], notes: list[str]) -> str:
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1050" viewBox="0 0 1600 1050">',
           '<defs><marker id="a" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8z" fill="#263f50"/></marker></defs>',
           '<rect width="1600" height="1050" fill="white"/><style>text{font-family:"Noto Sans CJK KR",sans-serif;fill:#15242d}.t{font-size:31px;font-weight:700}.s{font-size:17px}.n{font-size:15px;font-weight:600}.e{font-size:13px;font-weight:600}.edge{fill:none;stroke-width:3;marker-end:url(#a)}</style>',
           f'<text x="50" y="52" class="t">{html.escape(title)}</text>', f'<text x="50" y="82" class="s">{html.escape(subtitle)}</text>']
    for x, y, w, h, label, fill in nodes:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#294c60" stroke-width="2"/>')
        lines = label.split("|")
        start = y + h / 2 - (len(lines) - 1) * 11
        out += [f'<text x="{x+w/2}" y="{start+i*22}" class="n" text-anchor="middle">{html.escape(line)}</text>' for i, line in enumerate(lines)]
    for x1, y1, x2, y2, label, colour in edges:
        out += [f'<path class="edge" stroke="{colour}" d="M{x1},{y1} L{x2},{y2}"/>',
                f'<rect x="{(x1+x2)//2-72}" y="{(y1+y2)//2-15}" width="144" height="21" fill="white" opacity=".92"/>',
                f'<text x="{(x1+x2)//2}" y="{(y1+y2)//2+1}" class="e" text-anchor="middle">{html.escape(label)}</text>']
    out.append('<rect x="45" y="890" width="1510" height="125" rx="7" fill="#fff4e8" stroke="#bb5d20" stroke-width="2"/>')
    out += [f'<text x="65" y="{920+i*28}" class="s">• {html.escape(note)}</text>' for i, note in enumerate(notes)]
    out.append('</svg>')
    return "\n".join(out) + "\n"


def diagram_data(pin_count: int) -> dict[str, tuple[str, list, list, list[str]]]:
    b, g, o, x, r = "#e2f1f8", "#e4f3e7", "#fff0d7", "#edf0f2", "#ffe1dc"
    safety = "Hardware safety is independent of firmware; physical validation NOT_RUN."
    unknown = "Exact donor ratings, conductor sizing and local-code compliance are USER_VERIFICATION_REQUIRED."
    return {
      "system_block_diagram": ("energy, safety, control and process blocks",
       [(50,150,190,80,"AC inlet|SITE MAINS",x),(290,150,210,80,"24 V / 600 W PSU|25 A max",o),(555,130,220,120,"F-MAIN|branch protection",o),(830,115,260,150,"HARDWIRED K0 CHAIN|E-stop · lid · service|independent thermal cutoff",r),(1150,120,390,140,"HAZARDOUS LOADS|shredder · feeder · screw|4 heater MOSFETs · forming",o),(555,400,220,100,"Arduino Mega|protected logic",b),(50,400,400,100,"SENSORS|thermocouples · gauge · tach|current · dancer · faults",g),(830,400,260,100,"command interfaces|PWM · DIR · ENABLE",b),(1150,400,390,100,"drivers / MOSFETs / fans|ratings USER APPROVAL REQUIRED",o),(290,680,210,80,"PE STUD",g),(555,680,220,80,"frame + enclosure",g),(830,680,260,80,"motor frames",g),(1150,680,390,80,"metal hot shield",g)],
       [(240,190,290,190,"AC-L/N","#334d5f"),(500,190,555,190,"24-MAIN±","#c24c36"),(775,190,830,190,"24-SAFE+","#c24c36"),(1090,190,1150,190,"protected 24 V","#c24c36"),(450,450,555,450,"SIG inputs","#31734f"),(775,450,830,450,"SIG outputs","#315a84"),(1090,450,1150,450,"logic only","#315a84"),(500,720,555,720,"PE-02","#31734f"),(775,720,830,720,"PE-04","#31734f"),(1090,720,1150,720,"PE-03","#31734f")],[safety,unknown]),
      "power_distribution": ("24 VDC single-line; all branch IDs appear in wire_schedule.csv",
       [(45,135,205,80,"PSU 24 V / 600 W|25 A max",o),(300,135,180,80,"F-MAIN|30 A DC",r)] + [(550,105+i*92,190,62,label,r) for i,label in enumerate(("F-LOGIC 3 A","F-SAFE 1 A","F-SH 20 A","F-SCREW 10 A","F-FEED 5 A","F-PULL/SPOOL 5 A each","F-FAN 3 A","F-H1..H4 5 A"))] + [(900,105+i*92,300,62,label,o if i>1 else b) for i,label in enumerate(("Mega + sensors","K0 safety coil","shredder driver","screw driver","FD-MET auger driver","forming drivers","fan pair","MOS-H1..H4 + TF"))] + [(1300,340,240,120,"0 V STAR|functional return|NOT PE",x)],
       [(250,175,300,175,"24-MAIN+","#c24c36")] + [(480,175,550,136+i*92,f"24-{tag}+","#c24c36") for i,tag in enumerate(("LOGIC","SAFE","SH","SCREW","FEED","PULL/SPOOL","FAN","H1..4"))] + [(740,136+i*92,900,136+i*92,f"F-{tag}","#c24c36") for i,tag in enumerate(("LOGIC","SAFE","SH","SCREW","FEED","PULL/SPOOL","FAN","H1..4"))],["500 W software heater cap does not replace branch fuses or independent thermal cutoff.",unknown]),
      "safety_chain": ("normally-closed hard cut; de-energize-to-trip",
       [(45+i*245,230,190,85,label,r if i else o) for i,label in enumerate(("F-SAFE","S0 E-STOP NC","S1 LID NC","S2 SERVICE NC","TF THERMAL CUTOFF","K0 COIL"))] + [(1080,500,240,85,"K0 feedback|force-guided",g),(650,500,240,85,"Mega D24|diagnostic only",b),(220,500,240,85,"K0 power contacts|hazardous branches",o)],
       [(235+i*245,272,290+i*245,272,f"SAFE-{i+1:02d}","#c24c36") for i in range(5)] + [(1320,542,890,542,"SIG-24","#315a84")],["Any open S0/S1/S2/TF removes K0 coil energy with firmware halted.","Reset needs cause removal, physical lockout confirmation and explicit restart permission."]),
      "full_wiring_diagram": ("terminal topology; paired schedules contain every conductor field",
       [(45,135,210,105,"TB-AC|AC-L · AC-N · PE-01",x),(305,135,210,105,"PSU|24 V / 600 W",o),(565,135,210,105,"TB24 + FUSES|MAIN · LOGIC · SAFE",o),(825,115,225,145,"K0 SAFETY|SAFE-01..06",r),(1100,115,215,145,"POWER LOADS|SH · SCREW · FEED|PULL · SPOOL · FAN",o),(1365,115,180,145,"HEATERS|24-H1..H4",o),(565,420,210,125,"ARDUINO MEGA|SIG-<PIN>|D2..D52 / A0..A15",b),(45,420,410,125,"SENSOR TERMINALS|TC1..5 · tach · current · gauge|dancer · limits · driver faults",g),(825,420,225,125,"CONTROL TERMINALS|PWM · DIR · ENABLE|STEP · mux · heater gate",b),(1100,420,445,125,"DRIVER / MOSFET INTERFACES|logic isolation as required|exact levels USER_VERIFY",o),(305,700,210,90,"0 V STAR|all 24-*- returns",x),(565,700,210,90,"PE STUD|PE-01..04",g),(825,700,225,90,"SHIELD BAR|one-end only",g),(1100,700,445,90,"FIELD DEVICES|strain relief + service loops|no sharp-edge or solid crossing",x)],
       [(255,187,305,187,"AC-L/N","#334d5f"),(515,187,565,187,"24-MAIN±","#c24c36"),(775,187,825,187,"24-SAFE+","#c24c36"),(1050,187,1100,187,"branches","#c24c36"),(1315,187,1365,187,"24-H1..4","#c24c36"),(455,482,565,482,"SIG inputs","#31734f"),(775,482,825,482,"SIG outputs","#315a84"),(1050,482,1100,482,"J-<PIN>","#315a84"),(515,745,565,745,"PE-02","#31734f"),(775,745,825,745,"shields","#315a84"),(1050,745,1100,745,"field routes","#31734f")],["This diagram plus wire, connector and fuse schedules is the terminal wiring definition.","FD-MET feeder: D44 PWM / D42 DIR / D46 EN / D47 FAULT / A7 TACH; 5 A branch envelope."]),
      "Arduino_Mega_pinmap": (f"{pin_count} assignments parsed from released board_config.h",
       [(45,130,330,190,"SAFETY INPUTS|D20 E-stop · D21 lid|D22 service · D23 thermal|D24 K0 feedback",r),(45,365,330,205,"MOTION FEEDBACK|D2 shredder · D3 puller|A13 screw · A15 spooler|A14 fan mux · A5/A6 limits",g),(45,620,330,180,"ANALOG / FAULTS|A0 current · A1 dancer · A2/A3 gauge|A4 cooling · A7 feeder tach|A8..A12 faults/valid",g),(600,300,400,260,"ARDUINO MEGA 2560|board_config.h authoritative|all SIG-<PIN> scheduled",b),(1225,130,330,210,"MOTOR COMMANDS|D5..D9 PWM · D30..D38 DIR/EN|D39..D41 traverse|D44/D42/D46 feeder",o),(1225,390,330,180,"HEATER / FAN|D10..D13 heater · D4 hopper PTC|D49 mux select",o),(1225,620,330,180,"TC / UI|CS D14..D17,D48 · D50 SO · D52 SCK|D18/D19 encoder · D25..D29 buttons",g)],
       [(375,225,600,365,"SIG-D20..24","#315a84"),(375,467,600,430,"tach/limits","#315a84"),(375,710,600,500,"analog/faults","#315a84"),(1000,365,1225,235,"motor SIG","#315a84"),(1000,430,1225,480,"heater SIG","#315a84"),(1000,500,1225,710,"TC/UI SIG","#315a84")],["pinmap.md and pin_schedule.csv list every assignment and source fingerprint.",safety]),
      "grounding_bonding": ("protective earth and functional shield/reference are separate",
       [(45,190,200,90,"AC INLET PE",g),(320,180,250,110,"DEDICATED PE STUD|bare metal + tooth washer",g),(690,120,270,80,"enclosure backplate|PE-02",g),(690,245,270,80,"motor frames|PE-04",g),(690,370,270,80,"metal hot shield|PE-03",g),(1080,180,250,100,"SHIELD BAR|functional / one-end",b),(1400,180,150,100,"sensor cable|shields",b),(1080,430,250,100,"0 V STAR|NOT PE",x),(1400,430,150,100,"Mega / sensor|reference",x)],
       [(245,235,320,235,"PE-01","#31734f"),(570,235,690,160,"PE-02","#31734f"),(570,235,690,285,"PE-04","#31734f"),(570,235,690,410,"PE-03","#31734f"),(1330,230,1400,230,"one end","#315a84"),(1330,480,1400,480,"0 V","#202020")],["Measure each PE bond; paint, anodizing and loose hardware are not valid bond paths.","Never use a shield or logic 0 V as PE; size and test per local code."]),
      "enclosure_layout": ("segregation and access plan; final holes wait for accepted component envelopes",
       [(45,125,1510,680,"ENCLOSURE BOUNDARY|donor dimensions USER APPROVAL REQUIRED",x),(75,185,270,245,"MAINS ZONE|inlet · disconnect|PSU · TB-AC · cover",r),(390,185,300,245,"DC HIGH CURRENT|fuses · K0 · TB24|0 V star",o),(735,185,360,245,"DRIVER / HEATER|H-bridge · drivers|MOS-H1..H4 · heat sinks",o),(1140,185,375,245,"LOGIC / SENSOR|Mega · interfaces|MAX6675 · shield bar",b),(75,520,270,155,"PE STUD|short bonds",g),(390,520,300,155,"LOW GLANDS|AC / motor power",x),(735,520,360,155,"LOW GLANDS|heater / fan",x),(1140,520,375,155,"HIGH GLANDS|sensor / UI",x)],
       [(345,305,390,305,"barrier","#c24c36"),(690,305,735,305,"barrier","#c24c36"),(1095,305,1140,305,"barrier","#c24c36"),(345,597,390,597,"PE-02","#31734f"),(690,597,735,597,"duct split","#334d5f"),(1095,597,1140,597,"duct split","#334d5f")],["Maintain finger-safe covers, fuse access, heat-sink clearance, bend radius and duct fill.","Placement contract only: exact drilling waits for accepted donor envelopes and local mains review."]),
      "cable_routing": ("machine route zones, separation, service loops and strain relief",
       [(45,150,280,125,"ENCLOSURE|power glands low|signal glands high",b),(430,120,270,105,"SHREDDER|motor + 6 PPR tach",o),(430,280,270,105,"FD-MET FEEDER|PWM/DIR/EN + fault/tach",o),(810,120,280,265,"HOT ZONE|4 heater pairs|5 thermocouples|PE-bonded shield",r),(1200,120,350,105,"COOLING|fan power/current/tach",o),(1200,280,350,105,"GAUGE + PULLER|shielded signal / motor power",g),(810,520,280,110,"FRAME TRUNK|separate power/sensor ducts",x),(1200,520,350,110,"SPOOLER / TRAVERSE|service loop + limits",o)],
       [(325,212,430,172,"24-SH± / SIG-D2","#c24c36"),(325,212,430,332,"24-FEED± / D44,D42,D46,D47,A7","#c24c36"),(325,212,810,250,"24-H1..4 / TC SIG","#c24c36"),(1090,250,1200,172,"24-FAN± / A4,A14","#c24c36"),(1090,250,1200,332,"24-PULL± / D3","#c24c36"),(950,385,950,520,"split routes","#31734f"),(1090,575,1200,575,"24-SPOOL± / limits","#c24c36")],["No cable may cross cutter, chain, hot surface, sharp edge or solid; verify full motion/service envelope.","Sensor routes are separate from PWM/motor/heater conductors; cross at 90 degrees only."])
    }


def electrical_release(commit: str) -> tuple[int, int]:
    ELEC.mkdir(parents=True, exist_ok=True)
    pin_rows = pins()
    wires = power_wires() + signal_wires(pin_rows)
    if len({item["wire_id"] for item in wires}) != len(wires):
        raise SystemExit("duplicate wire_id")
    write_csv(ELEC / "wire_schedule.csv", WIRE_FIELDS, wires)
    connectors = [{"connector_id": item["connector"], "wire_id": item["wire_id"], "from": item["from"], "to": item["to"], "terminal": item["terminal"], "retention": "locking/strain-relieved as scheduled", "rating": f'>= scheduled {item["maximum_current"]}; >= scheduled {item["voltage"]}; exact MPN USER_APPROVAL_REQUIRED'} for item in wires]
    write_csv(ELEC / "connector_schedule.csv", tuple(connectors[0]), connectors)
    fuses = [
      {"fuse_id":"F-MAIN","branch":"24 V main","rating":"30 A DC","maximum_current":"25 A PSU maximum","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"protect 6 mm2 main conductors"},
      {"fuse_id":"F-LOGIC","branch":"Mega/sensors","rating":"3 A DC","maximum_current":"3 A design maximum","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"protected logic branch"},
      {"fuse_id":"F-SAFE","branch":"hardwired safety","rating":"1 A DC","maximum_current":"1 A design maximum","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"firmware-independent"},
      {"fuse_id":"F-SH","branch":"shredder","rating":"20 A DC","maximum_current":"20 A","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"donor must remain inside design envelope"},
      {"fuse_id":"F-SCREW","branch":"screw","rating":"10 A DC","maximum_current":"10 A envelope","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"donor must remain inside design envelope"},
      *[{"fuse_id":name,"branch":branch,"rating":"5 A DC","maximum_current":"5 A design envelope","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"received donor(s) must remain within envelope; otherwise redesign"} for name,branch in (("F-FEED","FD-MET auger/agitator"),("F-PULL","puller"),("F-SPOOL","spooler/traverse combined"))],
      {"fuse_id":"F-FAN","branch":"fans","rating":"3 A DC","maximum_current":"3 A envelope","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"start/stall must remain inside envelope"},
      *[{"fuse_id":f"F-H{i}","branch":f"heater {i}","rating":"5 A DC","maximum_current":"5 A design maximum","dc_interrupt_rating":">=1 kA at >=32 VDC","basis":"thermal fuse remains series"} for i in range(1,5)]
    ]
    write_csv(ELEC / "fuse_schedule.csv", tuple(fuses[0]), fuses)
    pin_records = [{"symbol": name, "mega_pin": pin, "wire_id": f"SIG-{pin}", "source":"firmware/arduino_mega/src/board_config.h", "revision":commit} for name,pin in pin_rows]
    write_csv(ELEC / "pin_schedule.csv", tuple(pin_records[0]), pin_records)
    for name, (subtitle, nodes, edges, notes) in diagram_data(len(pin_rows)).items():
        write(ELEC / f"{name}.svg", svg(name.replace("_", " "), subtitle, nodes, edges, notes))
        write(ELEC / f"{name}.typ", f'#set page(paper: "a3", flipped: true, margin: 10mm)\n#image("{name}.svg", width: 100%, height: 100%, fit: "contain")')
        env = dict(os.environ, SOURCE_DATE_EPOCH="946684800")
        subprocess.run([tool("typst"), "compile", str(ELEC/f"{name}.typ"), str(ELEC/f"{name}.pdf"), "--root", str(ROOT)], check=True, env=env)
    return len(wires), len(pin_rows)


def tracked_sources() -> list[Path]:
    names = subprocess.check_output(["git", "ls-files", "firmware/arduino_mega"], cwd=ROOT, text=True).splitlines()
    files = sorted(ROOT/name for name in names if "/__pycache__/" not in name and "/build/" not in name)
    if not any(path.name == "arduino_mega.ino" for path in files):
        raise SystemExit("firmware source incomplete")
    return files


def compile_hex(cli: str, sketch: Path, output: Path) -> tuple[Path, str]:
    result = subprocess.run([cli, "compile", "--fqbn", FQBN, "--output-dir", str(output), str(sketch)], cwd=ROOT, text=True, capture_output=True)
    text = (result.stdout + result.stderr).strip()
    hexes = list(output.glob("*.ino.hex"))
    if result.returncode or len(hexes) != 1 or "Sketch uses" not in text:
        raise SystemExit(text)
    return hexes[0], text


def rebuild_script() -> str:
    return '''#!/usr/bin/env python3
"""Released source clean-build and HEX identity check."""
import hashlib, json, shutil, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cli():
    for p in [shutil.which("arduino-cli"), *sorted(Path("/nix/store").glob("*-arduino-cli-*/bin/arduino-cli"))]:
        if p and subprocess.run([str(p), "version"], capture_output=True).returncode == 0: return str(p)
    raise SystemExit("arduino-cli unavailable")
manifest = json.loads((ROOT / "build_manifest.json").read_text())
with tempfile.TemporaryDirectory(prefix="ppr-release-rebuild-") as out:
    result = subprocess.run([cli(), "compile", "--fqbn", "arduino:avr:mega", "--output-dir", out, str(ROOT/"source/arduino_mega")], text=True, capture_output=True)
    hexes = list(Path(out).glob("*.ino.hex"))
    if result.returncode or len(hexes) != 1: raise SystemExit(result.stdout + result.stderr)
    actual = sha(hexes[0])
expected = sha(ROOT / "binaries/filament_recycler_atmega2560.hex")
assert actual == expected == manifest["binary"]["sha256"], (actual, expected)
print(f"RELEASED_HEX_REPRODUCIBLE_OK sha256={actual}")
'''


def firmware_docs(pin_rows: list[tuple[str,str]], generator_commit: str, source_commit: str) -> None:
    table = "\n".join(f"| `{name}` | `{pin}` | `SIG-{pin}` |" for name,pin in pin_rows)
    write(FW/"pinmap.md", f"""# Arduino Mega 2560 pin map — v0.8

Source commit `{source_commit}`; `board_config.h` SHA-256 `{sha(SOURCE/'src/board_config.h')}`.

| Symbol | Mega pin | wire ID |
|---|---:|---|
{table}

`board_config.h` is authoritative. The active feeder is the single coaxial FD-MET positive-displacement auger/agitator on D44 PWM, D42 direction, D46 enable, D47 fault and A7 low-speed tach. A received donor exceeding the 5 A branch envelope is rejected or triggers an electrical redesign; it is never silently substituted. Hardwired E-stop, lid/service, thermal cutoff and branch fuses are firmware-independent.
""")
    cal = re.findall(r"^\s*(CAL_[A-Z0-9_]+)(?:\s*=\s*\d+)?,?\s*$", (SOURCE/"src/calibration_record.h").read_text(), re.M)
    write(FW/"EEPROM_schema.md", f"""# EEPROM schema v4

Magic `0x50505236`; version `4`; {len(cal)} domains: {', '.join(f'`{x}`' for x in cal)}.

Binary order and CRC boundaries are defined by `source/arduino_mega/src/calibration_record.h` (SHA-256 `{sha(SOURCE/'src/calibration_record.h')}`). Each domain carries id, units, source, verified, revision, value, valid range and FNV-1a CRC; the aggregate carries readiness mask and whole-record CRC. Raw offsets are compiler-layout dependent, so raw editing is forbidden.

Uninitialized, old-version, out-of-range or CRC-failed data is zeroed/unverified; boot material is `NONE` and production outputs remain inhibited. Only commissioning measurement or factory certificate may be verified. Hardware safety does not depend on EEPROM or firmware.
""")
    write(FW/"flashing_guide_ko.md", f"""# ATmega2560 flashing guide

Target `{FQBN}`; source `{source_commit}`; generation base `{generator_commit}`. 먼저 `python3 reproducible_build/build_and_verify.py`로 clean build/HEX 일치를 확인한다.

1. Main 24 V, heater와 motor branch를 물리 lockout하고 USB만 연결한다.
2. 보드/포트를 확인하고 `arduino-cli upload -p <PORT> --fqbn {FQBN} source/arduino_mega`로 기록한다.
3. verify/read-back 후 boot material `NONE`과 모든 actuator safe-state를 확인한다.
4. Branch power는 별도 사용자 승인과 pre-power 검사 전 연결하지 않는다.

Flash는 safety chain이 아니다. E-stop, lid/service, thermal cutoff, K0와 fuse는 firmware 독립이다.
""")
    write(FW/"calibration_guide_ko.md", """# v0.8 calibration guide

모든 값은 donor label, 계측기 ID, 날짜, 단위, 범위, revision, 원시 증거와 함께 EEPROM v4 CRC로 기록한다. Reference/simulation은 verified가 아니다.

1. Tach: shredder 6 PPR, screw 12 PPR, puller/spooler 20 PPR 후보를 실회전/pulse로 각각 확인한다.
2. Drive/current: no-load를 빼고 torque arm 5/10/15/18/22 N·m에서 shredder torque/A, ratio, efficiency를 교정한다. Screw/puller/spooler는 별도 방향·RPM·stall/tach-loss 시험을 한다.
3. Fan: 0/25/50/100%의 A4 current와 fan1/2 tach, open/stall/one-fan-only를 시험한다. Tach는 airflow 증거가 아니다.
4. Gauge/dancer: traceable pin으로 X/Y/U95/ovality를, 전각도 sweep으로 0.32 rad warning, 0.36 rad stop, 0.4363 rad hard-stop을 확인한다.
5. Traverse: 좌우 limit, steps/mm, 2 mm backoff, 68 mm usable width를 확인한다. Explicit HOME 전 이동 금지다.
6. Purge: waste path, 최소 120 s, verified screw tach 32 revolutions, temperature band, 육안 확인이 모두 필요하다. 80/120 g은 estimate다.
7. Fault clear: 원인 제거, energy isolation, guard close, physical lockout key와 operator confirmation 후 수행하며 자동 재시작하지 않는다.

교정 전 production enable 금지. Hardwired safety 시험은 별도 수행한다.
""")
    write(FW/"runtime_state_machine_ko.md", """# Runtime state machine — v0.8

Machine: `IDLE → SHREDDING | PREHEATING → EXTRUSION → COOLDOWN → IDLE`. Forming 이상은 `FORMING_CHAIN_RUNDOWN (10 s bounded) → THERMAL_HOLD → REQUALIFYING → READY_TO_RETHREAD` 뒤 explicit confirmation으로만 복귀한다. 모든 상태는 `FAULT/ESTOP`으로 전이하며 자동 재시작하지 않는다.

Material change: `PURGE_PREHEAT_REQUIRED → PURGE_READY_CONFIRM_REQUIRED → PURGE_RUNNING → SCREEN_CLEAN_REQUIRED → HOPPER_CLEAN_REQUIRED → TEMPERATURE_TRANSITION_REQUIRED → FINAL_CONFIRM_REQUIRED`. 중단/E-stop/fault clear는 시작 단계로 복귀한다.

Invalid EEPROM은 material NONE/calibration unverified/output inhibit다. Any safety input false면 command는 zero이며 K0가 독립적으로 energy를 제거한다. Shredder와 heater/screw enable은 상호 배제한다. Cooling command는 proof가 아니며 A4 current와 두 fan tach가 필요하다. Serial clear는 physical lockout을 우회하지 못한다. Exact predicates는 released `process_state.cpp`와 `machine_supervisor.cpp`가 지배한다. Physical validation은 NOT_RUN이다.
""")


def firmware_release(generator_commit: str) -> tuple[str,int,int]:
    cli = tool("arduino-cli")
    source_commit = subprocess.check_output(["git","log","-1","--format=%H","--","firmware/arduino_mega"], cwd=ROOT, text=True).strip()
    for target in (FW/"source", FW/"reproducible_build"):
        if target.exists(): shutil.rmtree(target)
    release_source = FW/"source/arduino_mega"
    files = tracked_sources()
    for original in files:
        dest = release_source/original.relative_to(SOURCE)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, dest)
    (FW/"binaries").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ppr-original-") as a, tempfile.TemporaryDirectory(prefix="ppr-released-") as b:
        original_hex, output = compile_hex(cli, SOURCE, Path(a))
        released_hex, _ = compile_hex(cli, release_source, Path(b))
        if sha(original_hex) != sha(released_hex): raise SystemExit("released source HEX mismatch")
        shutil.copyfile(released_hex, FW/"binaries/filament_recycler_atmega2560.hex")
        digest = sha(released_hex)
    usage = re.search(r"Sketch uses (\d+) bytes \((\d+)%\).*?Global variables use (\d+) bytes \((\d+)%\).*?leaving (\d+) bytes", output, re.S)
    if not usage: raise SystemExit("memory usage parse failed")
    cores = json.loads(subprocess.check_output([cli,"core","list","--format","json"], text=True))
    core = next(x for x in cores["platforms"] if x["id"] == "arduino:avr")
    props = subprocess.check_output([cli,"compile","--fqbn",FQBN,"--show-properties",str(SOURCE)], text=True)
    compiler_path = re.search(r"^runtime\.tools\.avr-gcc\.path=(.+)$", props, re.M).group(1)
    compiler = subprocess.check_output([str(Path(compiler_path)/"bin/avr-g++"),"--version"], text=True).splitlines()[0]
    manifest = {"schema_version":1,"status":"PASS","release_revision":REV,"source_git_sha":source_commit,"generation_base_git_sha":generator_commit,
      "board_target":FQBN,"arduino_cli_version":subprocess.check_output([cli,"version"],text=True).strip(),
      "arduino_core":{"id":"arduino:avr","version":core["installed_version"]},"compiler_version":compiler,
      "libraries":[],"exact_build_command":"arduino-cli compile --fqbn arduino:avr:mega --output-dir <clean-dir> source/arduino_mega",
      "flash":{"used_bytes":int(usage.group(1)),"maximum_bytes":253952,"percent_reported":int(usage.group(2))},
      "sram":{"global_bytes":int(usage.group(3)),"maximum_bytes":8192,"percent_reported":int(usage.group(4)),"local_stack_heap_headroom_bytes":int(usage.group(5))},
      "binary_sha256":digest,"binary":{"path":"binaries/filament_recycler_atmega2560.hex","sha256":digest},
      "source_files":{str(path.relative_to(SOURCE)):sha(path) for path in files},
      "clean_rebuild":{"status":"PASS","original_source_hex_sha256":digest,"released_source_hex_sha256":digest},
      "safety_note":"E-stop, lid/service interlocks, independent thermal cutoff and branch fuses are firmware-independent."}
    write(FW/"build_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    write(FW/"library_lock.json", json.dumps({"schema_version":1,"fqbn":FQBN,"platforms":[{"id":"arduino:avr","version":core["installed_version"]}],"libraries":[],"note":"No external Arduino libraries; core APIs only."}, indent=2, sort_keys=True))
    script = FW/"reproducible_build/build_and_verify.py"
    write(script, rebuild_script()); script.chmod(0o755)
    firmware_docs(pins(), generator_commit, source_commit)
    return digest, int(usage.group(1)), int(usage.group(3))


def self_check(wire_count: int, pin_count: int) -> None:
    wires = list(csv.DictReader((ELEC/"wire_schedule.csv").open(encoding="utf-8")))
    assert tuple(wires[0]) == WIRE_FIELDS and len(wires) == wire_count
    assert all(all(item[field].strip() for field in WIRE_FIELDS) for item in wires)
    assert {f"SIG-{pin}" for _,pin in pins()} <= {item["wire_id"] for item in wires}
    assert len(list(csv.DictReader((ELEC/"pin_schedule.csv").open(encoding="utf-8")))) == pin_count
    for name in DIAGRAMS:
        assert (ELEC/f"{name}.svg").stat().st_size > 2000
        assert (ELEC/f"{name}.pdf").stat().st_size > 10000
    manifest = json.loads((FW/"build_manifest.json").read_text())
    assert manifest["clean_rebuild"]["status"] == "PASS"
    assert sha(FW/manifest["binary"]["path"]) == manifest["binary"]["sha256"]
    check = subprocess.run(["python3", str(FW/"reproducible_build/build_and_verify.py")], text=True, capture_output=True)
    if check.returncode or "RELEASED_HEX_REPRODUCIBLE_OK" not in check.stdout:
        raise SystemExit(check.stdout + check.stderr)


def main() -> None:
    commit = subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
    wire_count, pin_count = electrical_release(commit)
    digest, flash, sram = firmware_release(commit)
    self_check(wire_count, pin_count)
    print(f"V08_ELECTRICAL_FIRMWARE_RELEASE_OK wires={wire_count} pins={pin_count} flash={flash} sram={sram} hex={digest}")


if __name__ == "__main__": main()
