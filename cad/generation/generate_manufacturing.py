#!/usr/bin/env python3
"""Generate VE drive, Gate-1 jig and screw/barrel RFQ artifacts."""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

import FreeCAD as App
import Mesh
import Part
import importDXF

ROOT=Path(__file__).resolve().parents[2]
COMPACT=ROOT/"cad/freecad/compact"
sys.path.insert(0,str(COMPACT))
from generate import feature, normalize_dxf, normalize_step, normalize_zip_container  # noqa: E402
from manufacturing import (  # noqa: E402
    bolt_on_sprocket_hub,
    extruder_rfq_parts,
    gate1_assembly,
    gate1_parts,
    solid_phase_gear,
    motor_side_fuse_inner_hub,
    motor_side_fuse_outer_hub,
    motor_side_fuse_pin,
    universal_motor_plate,
)
from geometry import (  # noqa: E402
    die_cartridge_heater_shape,
    k_type_probe_shape,
    machine_fabrication_parts,
    mica_band_heater_shape,
    motor_adapter_42gp775_shape,
    motor_adapter_gmp60_shape,
    thermocouple_retainer_shape,
)


def export_shape_set(specs, base):
    rows=[]
    for spec in specs:
        folder=base/spec["id"]; folder.mkdir(parents=True,exist_ok=True)
        doc=App.newDocument(spec["id"].replace("-","_"))
        obj=feature(doc,"Part",spec["shape"],spec["name"],spec["id"],spec["material"])
        doc.recompute()
        fcstd=folder/f"{spec['id']}.FCStd"; fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd,True)
        step=folder/f"{spec['id']}.step"; Part.export([obj],str(step)); normalize_step(step)
        stl=folder/f"{spec['id']}.stl"; Mesh.export([obj],str(stl))
        dxf=folder/f"{spec['id']}.dxf"; importDXF.export([obj],str(dxf)); normalize_dxf(dxf)
        (folder/"drawing_notes.md").write_text(
            f"# {spec['id']} — {spec['name']}\n\n"
            f"- revision: `safety-orchestration-closure-v0.6.1`\n"
            f"- quantity: `{spec['qty']}`\n"
            f"- material: `{spec['material']}`\n"
            f"- process: `{spec['process']}`\n"
            f"- controlling requirements: `{spec.get('critical', '3D geometry controls nominal dimensions; supplier shall report deviations')}`\n"
            "- file precedence: 본 note/치수 요구사항 > STEP > DXF/STL. DXF/STL은 견적·CAM reference이며 자동 공차를 부여하지 않는다.\n"
            "- edge/inspection: 별도 표기가 없으면 burr 제거, sharp edge C0.3–0.5, 가공 후 유해한 균열·뒤틀림 없음.\n"
            "- release: `HOLD`; 해당 물리 gate와 사용자 승인 전 양산/전체수량 발주 금지.\n",
            encoding="utf-8",
        )
        bb=spec["shape"].BoundBox
        rows.append({**spec,"x":bb.XLength,"y":bb.YLength,"z":bb.ZLength})
        App.closeDocument(doc.Name)
    return rows


def export_assembly(items, base, stem):
    doc=App.newDocument(stem)
    objects=[]
    for index,item in enumerate(items):
        objects.append(feature(doc,f"Part{index:03d}",item["shape"],item["name"],material=item["material"]))
    doc.recompute()
    fcstd=base/f"{stem}.FCStd"; fcstd.unlink(missing_ok=True); doc.saveAs(str(fcstd)); normalize_zip_container(fcstd,True)
    step=base/f"{stem}.step"; Part.export(objects,str(step)); normalize_step(step)
    stl=base/f"{stem}.stl"; Mesh.export(objects,str(stl))
    compound=Part.makeCompound([o.Shape for o in objects]); bb=compound.BoundBox
    App.closeDocument(doc.Name)
    return [round(bb.XLength,2),round(bb.YLength,2),round(bb.ZLength,2)]


def write_machine_fabrication_package():
    """Export every non-shredder stock/fabricated machine family."""
    base = ROOT / "exports/fabrication"
    (base / "parts").mkdir(parents=True, exist_ok=True)
    rows = export_shape_set(machine_fabrication_parts(), base / "parts")
    with (base / "machine_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["part_id", "name", "quantity", "material", "process", "x_mm", "y_mm", "z_mm", "files", "release_state"])
        for row in rows:
            w.writerow([row["id"], row["name"], row["qty"], row["material"], row["process"], f"{row['x']:.2f}", f"{row['y']:.2f}", f"{row['z']:.2f}", "FCStd|STEP|STL|DXF|drawing_notes", "DESIGN_RELEASED_PROCUREMENT_USER_APPROVAL_REQUIRED"])
    with (base / "frame_cut_list.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["part_id", "stock", "cut_length_mm", "quantity", "end_condition", "length_tolerance_mm", "source", "release_state"])
        w.writerows([
            ("FR-01", "20x20 aluminum profile", "890.0", 4, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-02", "20x20 aluminum profile", "430.0", 10, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-03", "20x20 aluminum profile", "660.0", 6, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-04", "20x20 aluminum profile", "300.0", 2, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-05", "20x20 aluminum profile", "318.0", 1, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-06", "20x20 aluminum profile", "280.0", 2, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-07", "20x20 aluminum profile", "50.0", 1, "square/square; deburr", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
            ("FR-08", "20x40 aluminum profile", "660.0", 2, "square/square; deburr; 40 mm axis vertical", "+/-0.5", "project-lab inventory first", "VERIFY_INVENTORY_OR_QUOTE"),
        ])
    with (base / "assembly_interface_schedule.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["interface", "part_a", "part_b", "hardware", "fit_or_clearance", "inspection", "status"])
        w.writerows([
            ("feeder_to_barrel", "FD-MET-01", "EX-BAR-01", "metal saddle/clamp + high-temp gasket", "face contact; no bore intrusion", "dry-fit light/feeler check", "GATE2_AND_GATE3"),
            ("hopper_feeder_registered_flange", "FD-HOP-01/FD-GSK-01", "FD-MET-01", "4xM4 through bolts + all-metal locknuts", "register diametral clearance0.10–0.16; flow-path expansion0–0.15; gasket compressed0.35–0.40", "bore gauge, depth gauge, feeler, dry-flake leak/retention check", "GATE2"),
            ("feeder_reference_drive", "FD-MET-03/FD-CP-01", "EG17-G10/FD-DA-01", "3 mm key + Ø3x18 spring pin + 4xM4 gearbox screws + 2xM6 frame bolts", "coupling bore clearance0.05–0.102; axis position≤0.10; gearbox continuous rating5 N.m", "micrometer/pin gauge; hand turn; no-load tach; torque-arm test", "DIGITAL_REFERENCE_PURCHASE_AND_PHYSICAL_TEST_HOLD"),
            ("screw_to_barrel", "EX-SCR-01", "EX-BAR-01", "matched supplier pair", "0.14-0.16 mm radial at 20+/-2 C", "three-station report", "HOLD_PROCESS_COUPON_AND_GATE3"),
            ("puller_axes", "FM-AX-01", "FM-PL-01/FM-RL-01", "metal collars", "0.10 mm radial in Ø8.2 bores", "free rotation/TIR/slip", "GATE5"),
            ("guide_axis", "FM-GA-01", "625-2RS/FM-GR-01/PPR-C08", "two 625 bearings + metal collars", "Ø5 h6 axle; Ø16 H7 roller seats; Ø5.2 bracket clearance", "free rotation/no bearing preload", "GATE5"),
            ("spool_axis", "SP-SH-01", "PPR-C09/6001 bearings", "metal collars", "bearing fit per received lot", "full-spool runout", "GATE5"),
        ])
    (base / "README_ko.md").write_text(
        "# Machine fabrication package — safety-orchestration-closure-v0.6.1\n\n"
        "이 디렉터리는 shredder CUT, drive DRV, Gate-1 jig, extruder RFQ와 중복되지 않는 본체 제작품을 담는다. "
        "각 part 폴더의 note가 공차를 지배하고 STEP은 3D 형상, DXF/STL은 견적 reference다. "
        "Frame은 겹치는 profile solid가 아니라 `frame_cut_list.csv`의 butt-joint cut length로 조립한다. "
        "모든 주문은 사용자 승인 전 HOLD이며, donor 치수와 Gate-1/2/3/5 상태는 대체할 수 없다.\n",
        encoding="utf-8",
    )
    return rows


def svg_screw_drawing(path):
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1189" height="841" viewBox="0 0 1189 841">
<style>text{font-family:'Noto Sans CJK KR',sans-serif;font-size:18px}.t{font-size:28px;font-weight:bold}.d{stroke:#17465a;stroke-width:2;fill:none}.p{stroke:#111;stroke-width:3;fill:#d7e2e8}.c{stroke:#c43d32;stroke-width:2;stroke-dasharray:8 5}</style>
<text x="55" y="55" class="t">EX-SCR-01 — 16 mm × 16D single screw RFQ drawing</text>
<path class="p" d="M90 330 L180 330 L180 315 L230 315 L230 300 L870 300 L870 420 L230 420 L230 405 L180 405 L180 390 L90 390 Z"/>
<path class="c" d="M80 360 H890"/>
<path class="d" d="M230 270 V450 M550 270 V450 M710 270 V450 M870 270 V450"/>
<text x="335" y="265">FEED 128 (8D)</text><text x="545" y="265">COMPRESSION 64 (4D)</text><text x="765" y="265">METER 64 (4D)</text>
<path class="d" d="M90 475 V520 M870 475 V520 M90 505 H870"/><text x="440" y="535">TOTAL 316.0 ±0.10</text>
<path class="d" d="M230 550 V590 M870 550 V590 M230 575 H870"/><text x="465" y="610">ACTIVE 256.0 (L/D 16)</text>
<text x="55" y="650">Rear: Ø12 h6 x35, keyseat 4 P9 x2.5 deep · thrust journal Ø15 h6 x20 · neck 5</text>
<text x="55" y="685">OD 15.92 -0.02/0 · pitch 16.00 ±0.03 · land 1.60 ±0.05 · single start RH</text>
<text x="55" y="720">root Ø10.88 feed → linear Ø14.08 compression → Ø14.08 meter · end faces ⟂ A 0.03</text>
<text x="55" y="755">Datum A: common journal axis · flight OD TIR ≤0.05/256 · drive-to-flight concentricity ≤0.03 · OD Ra≤0.8 µm</text>
<text x="55" y="790">SCM440 QT 28–32 HRC → gas nitride 0.30–0.50 mm, surface 900–1100 HV · full part HOLD</text>
</svg>\n""",encoding="utf-8")


def svg_barrel_drawing(path):
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1189" height="841" viewBox="0 0 1189 841">
<style>text{font-family:'Noto Sans CJK KR',sans-serif;font-size:18px}.t{font-size:28px;font-weight:bold}.d{stroke:#17465a;stroke-width:2;fill:none}.p{stroke:#111;stroke-width:3;fill:#d7e2e8}.b{fill:#fff;stroke:#111;stroke-width:2}.c{stroke:#c43d32;stroke-width:2;stroke-dasharray:8 5}</style>
<text x="55" y="55" class="t">EX-BAR-01 — Ø34 / ID16.20 barrel RFQ drawing</text>
<rect x="120" y="300" width="700" height="150" class="p"/><rect x="120" y="345" width="700" height="60" class="b"/>
<rect x="150" y="260" width="50" height="85" class="b"/><path class="c" d="M90 375 H850"/>
<path class="d" d="M120 480 V525 M820 480 V525 M120 510 H820"/><text x="415" y="550">LENGTH 280.0 ±0.05</text>
<text x="55" y="620">OD Ø34.00 -0.03/0 · bore Ø16.20 +0.02/0 after final hone · radial clearance 0.14–0.16</text>
<text x="55" y="655">feed port 18 axial ×20, near edge B+12 · 3× sensor Ø3.20 +0.05/0 flat-bottom blind5.40±0.05 at B+95/170/245</text>
<text x="55" y="690">4x M4×0.7-6H full depth8/tap drill11, PCD26 at 45° · outer/inner ligament ≥2.0/2.9 · faces B/C ⟂ D 0.03</text>
<text x="55" y="725">bore Ra 0.4–0.8 µm; SCM440 QT 28–32 HRC → gas nitride 0.30–0.50 mm, ≥900 HV</text>
<text x="55" y="760">Assembly: B aligns screw active start; screw tip is 24.0 behind C. Final hone after nitride; report ID at B+20/140/260.</text>
<text x="55" y="795">No weld/plating on bore · feed-port centre plane is angular datum · full part HOLD</text>
</svg>\n""",encoding="utf-8")


def svg_process_coupon_drawing(path):
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1189" height="841" viewBox="0 0 1189 841">
<style>text{font-family:'Noto Sans CJK KR',sans-serif;font-size:18px}.t{font-size:28px;font-weight:bold}.d{stroke:#17465a;stroke-width:2;fill:none}.p{stroke:#111;stroke-width:3;fill:#d7e2e8}.b{fill:#fff;stroke:#111;stroke-width:2}</style>
<text x="50" y="52" class="t">EX-CPN-SCR / EX-CPN-BAR — matched process coupon RFQ drawing</text>
<rect x="100" y="175" width="480" height="105" class="p"/><path class="d" d="M100 150V310M580 150V310M100 135H580"/><text x="285" y="125">L48.00 ±0.05</text>
<text x="100" y="335">EX-CPN-SCR: 3 full RH pitches, pitch 16.00 ±0.03, land 1.60 ±0.05</text>
<text x="100" y="370">OD Ø15.92 -0.02/0; root Ø10.88 ±0.03; OD Ra≤0.8, root/flank Ra≤1.6 µm</text>
<text x="100" y="405">Ends ⟂ axis 0.03; no journal. Same SCM440 heat/QT/nitride/finish route as EX-SCR-01.</text>
<rect x="100" y="505" width="600" height="130" class="p"/><rect x="100" y="545" width="600" height="50" class="b"/>
<path class="d" d="M100 480V670M700 480V670M100 465H700"/><text x="335" y="453">L60.00 ±0.05</text>
<text x="100" y="705">EX-CPN-BAR: OD Ø34.00 ±0.05; final ID Ø16.20 +0.02/0; bore Ra 0.4–0.8 µm</text>
<text x="100" y="740">Ends ⟂ bore axis 0.03; same SCM440 heat/QT/nitride/final-hone route as EX-BAR-01.</text>
<text x="100" y="780">Matched actual diametral clearance 0.28–0.32 at 20 ±2 °C. Coupon RFQ allowed; full parts remain HOLD.</text>
</svg>\n""",encoding="utf-8")


def svg_die_drawing(path):
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1189" height="841" viewBox="0 0 1189 841">
<style>text{font-family:'Noto Sans CJK KR',sans-serif;font-size:17px}.t{font-size:27px;font-weight:bold}.d{stroke:#17465a;stroke-width:2;fill:none}.p{stroke:#111;stroke-width:3;fill:#d7e2e8}.b{fill:#fff;stroke:#111;stroke-width:2}.c{stroke:#c43d32;stroke-width:2;stroke-dasharray:8 5}</style>
<text x="50" y="50" class="t">EX-DIE-01…05 — connected 90° open-die assembly RFQ drawing</text>
<rect x="120" y="150" width="320" height="320" class="p"/><circle cx="280" cy="310" r="64" class="b"/><path class="c" d="M280 130V490M100 310H460"/>
<circle cx="354" cy="236" r="18" class="b"/><circle cx="206" cy="236" r="18" class="b"/><circle cx="206" cy="384" r="18" class="b"/><circle cx="354" cy="384" r="18" class="b"/>
<text x="120" y="505">BARREL FACE: 40 × 40; 4× Ø4.5 THRU + Ø8×5 head recess, PCD26 at 45°</text>
<path class="p" d="M600 165H920V485H600Z"/><rect x="600" y="270" width="320" height="80" class="b"/><rect x="720" y="350" width="80" height="135" class="b"/>
<path class="c" d="M560 310H950M760 140V520"/><text x="585" y="135">SECTION — barrel is to the right, outlet is downward</text>
<text x="610" y="260">Ø8 horizontal channel</text><text x="805" y="405">Ø8 vertical</text>
<text x="55" y="570">BODY SCM440 QT 28–32 HRC + gas nitride: 40×40×48; face flatness 0.03; channels Ø8 H9;</text>
<text x="55" y="600">breaker seat Ø16.20 +0.05/0 ×3; insert seat Ø12.00 +0.03/0 ×14; heater Ø6.55 H7 reamed thru;</text>
<text x="55" y="630">sensor Ø3.20 +0.05/0 blind12; 2×M4-6H depth8 retainer holes at X8/32; all melt edges R0.3.</text>
<text x="55" y="665">BREAKER 304: Ø15.90 -0.05/0 ×2; 7×Ø2.00 +0.05/0 (six PCD10). INSERT 17-4PH H900:</text>
<text x="55" y="695">Ø11.90 -0.02/0 ×14; Ø3.00 +0.02/0 ×10 land, Ra≤0.4; 4 mm 60° included transition; TIR≤0.02.</text>
<text x="55" y="730">RELIEF 304 t1.5: 32×20; two 10×2.5 webs; 2×Ø4.5 @24; Ø4 bypass. Hot coupon 3–6 MPa.</text>
<text x="55" y="760">GASKET C110 annealed t0.50: OD34 / ID16.20 / 4×Ø4.5 PCD26. SYS-04 M4×45 stock cut to 42.5±0.1; 1.50 N·m digital design torque.</text>
<text x="55" y="795">Leak/relief hot test behind grounded shield only. Analytical relief estimate is screening, not release evidence. FULL PART HOLD.</text>
</svg>\n""",encoding="utf-8")


def write_drive_package():
    base=ROOT/"exports/drive_interface"; base.mkdir(parents=True,exist_ok=True)
    specs=[
        dict(id="DRV-01",name="Universal donor motor plate",shape=universal_motor_plate(),qty=1,material="6 mm SS400 steel",process="laser cut + standard metal angles",critical="180 x140 x6; frame holes 4xØ6.6; DRV-A60 tension slots 6.6x18 act along chain centres, giving C=81-99 about nominal90; flatness <=0.5; motor-specific adapter carries motor load"),
        dict(id="DRV-02",name="Bolt-on cutter sprocket hub",shape=bolt_on_sprocket_hub(),qty=1,material="S45C",process="turn + keyway + PCD drilling",critical="bore Ø25.01 +0.02/0 after received CUT-05R measurement; matched keyway6.005-6.010; 4xØ6.6 PCD36.00±0.05; match-drill a standard #35 30T blank, face>=6, to the hub; assembled tooth-root radial TIR <=0.10"),
        dict(id="DRV-03",name="M3 Z16 solid phase gear left",shape=solid_phase_gear(),qty=1,material="18 mm S45C",process="wire-EDM profile/bore/keyway + finish",critical="M3 Z16 20 degree; face18; assembled pair tangential backlash 0.120-0.140 over one full mesh rotation at 20 +/-2 C; bore Ø25.01 +0.01/0; matched 8.005-8.010 keyway at datum0 deg; root fillet R1 minimum; 2xM4 clearance + 1xØ3 H7 inspection/clocking holes; full34 N.m CalculiX screen"),
        dict(id="DRV-03R",name="M3 Z16 solid phase gear right",shape=solid_phase_gear(180/7-180/16),qty=1,material="18 mm S45C",process="wire-EDM profile/bore/keyway + finish",critical="same tooth form and full-rotation pair backlash acceptance as DRV-03; matched 8.005-8.010 keyway clocked14.464 +/-0.02 deg from tooth datum so installed tooth phase11.25 deg matches CUT-05R key datum25.714 deg"),
        dict(id="DRV-A42",name="42GP-775 reference adapter plate",shape=motor_adapter_42gp775_shape(),qty=1,material="6 mm SS400 steel",process="laser + drill/ream",critical="70 x70 x6; centre Ø26; 4xØ4.5 PCD35; two 6.6x16 universal slots; adapter is retained although 42GP rated torque fails full-machine target"),
        dict(id="DRV-A60",name="GMP60-60127 released reference adapter plate",shape=motor_adapter_gmp60_shape(),qty=1,material="6 mm SS400 steel",process="laser + drill/ream",critical="80 x80 x6; pilot bore Ø32.05–32.10; 4xØ5.50–5.60 PCD45.00±0.05; two 6.6x18 universal slots; accept reference motor pilot Ø31.95–32.00 and PCD44.90–45.10 only"),
        dict(id="DRV-F01A",name="Motor-side fuse inner hub",shape=motor_side_fuse_inner_hub(),qty=1,material="S45C",process="turn + wire-EDM/broach D-bore + radial drill",critical="D-bore circle Ø12.02–12.05 and across-flat10.92–10.95 x13; final3 mm round relief; accept motor shaft Ø11.95–12.00/across-flat10.85–10.90; OD20 x16; radial Ø3.2; no set-screw-only torque path"),
        dict(id="DRV-F01B",name="Motor-side fuse sprocket carrier",shape=motor_side_fuse_outer_hub(),qty=1,material="S45C",process="turn + PCD drill + radial drill",critical="OD36/ID20.4 x10; radial Ø3.2; 4xØ4.5 PCD28 to 12T sprocket; rotates free after pin fracture"),
        dict(id="DRV-F01P",name="Replaceable waisted shear pin coupon",shape=motor_side_fuse_pin(),qty=6,material="C360/CuZn39Pb3 brass",process="turn waist to released digital baseline; optional coupon correlation may refine later",critical="Ø3 x36 blank; starting waist Ø1.8 x4; target 10.35 N.m motor-side; one-shot BROKEN state; optional empirical calibration is not a design-release gate"),
    ]
    rows=export_shape_set(specs,base/"parts")
    with (base/"manifest.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["part_id","name","quantity","material","process","x_mm","y_mm","z_mm","release_state"])
        release={
            "DRV-03":"ACTIVE_GGM_PHASE_GEAR_GATE1_QTY_1_USER_APPROVAL_REQUIRED",
            "DRV-03R":"ACTIVE_GGM_PHASE_GEAR_GATE1_QTY_1_USER_APPROVAL_REQUIRED",
            "DRV-01":"LEGACY_GENERIC_DRIVE_SUPERSEDED_BY_GGM_V08",
            "DRV-A42":"LEGACY_GENERIC_DRIVE_SUPERSEDED_BY_GGM_V08",
            "DRV-A60":"LEGACY_GENERIC_DRIVE_SUPERSEDED_BY_GGM_V08",
            "DRV-02":"LEGACY_SUPERSEDED_BY_DIRECT_KEYED_GGM_SH_30T",
            "DRV-F01A":"LEGACY_GENERIC_DRIVE_SUPERSEDED_BY_GGM_V08",
            "DRV-F01B":"LEGACY_GENERIC_DRIVE_SUPERSEDED_BY_GGM_V08",
            "DRV-F01P":"LEGACY_GENERIC_DRIVE_SUPERSEDED_BY_GGM_V08",
        }
        for r in rows:
            state=release[r["id"]]
            w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"{r['x']:.2f}",f"{r['y']:.2f}",f"{r['z']:.2f}",state])
            note=base/"parts"/r["id"]/"drawing_notes.md"
            text=note.read_text(encoding="utf-8")
            text=text.replace("revision: `safety-orchestration-closure-v0.6.1`", "revision: `final-design-fabrication-closure-v0.8`")
            replacement=("- release: `"+state+"`; DRV-03/DRV-03R만 current GGM phase path에서 사용한다. "
                         "LEGACY 상태 부품은 STEP/DXF가 존재해도 GGM v0.8 제작에 사용하지 않는다.\n")
            text=text.replace("- release: `HOLD`; 해당 물리 gate와 사용자 승인 전 양산/전체수량 발주 금지.\n",replacement)
            note.write_text(text,encoding="utf-8")
    (base/"interface_contract_ko.md").write_text("""# GGM v0.8 분쇄기 구동 인터페이스

Revision: `final-design-fabrication-closure-v0.8`

현재 powered 기준은 `GGM K9DG60N2 + K9G75C -> GGM 보호 커플링 -> 2x6201 지지 jackshaft -> direct-keyed #35 12T:30T -> CUT-05R`이다. 12T는 jackshaft의 4x4 key, 30T는 CUT-05R의 6x6x20 key가 토크를 전달한다. Key가 아닌 set screw/clamp 마찰만으로 토크를 전달하지 않는다.

두 sprocket의 exact MPN은 아직 승인되지 않았다. 수령품은 key/bore가 해당 shaft와 맞고 maker의 독립 axial-retention feature가 있어야 한다. Retention hardware는 축방향 위치만 유지하며 체결 토크는 수령품 maker 값 확인 전 `HOLD`다. 조립 후 각 sprocket tooth/root radial TIR <=0.10 mm, total axial shift + U95 <=0.20 mm, chain plane alignment <=0.20/150 mm, midspan slack 2-3%를 확인한다. 이 조건을 만족하지 못하면 adapter revision을 새로 발행하며 구형 `DRV-02`를 임의 재사용하지 않는다.

`DRV-03/DRV-03R` phase gear pair는 계속 active이며 matched 8 mm key가 shaft torque/phase를 전달한다. `DRV-01`, `DRV-02`, `DRV-A42`, `DRV-A60`, `DRV-F01A/B/P`는 generic donor-drive compatibility archive이며 현재 GGM fabrication baseline에서는 superseded다. 이 디렉터리의 해당 STEP/DXF가 존재하더라도 제작 승인으로 해석하지 않는다.

현재 보호 기준은 gearbox software limit 8.0 N.m, mechanical protection coupon 8.8-9.3 N.m, motor-lead current calibrated range 0-6 A다. 과거 14/18/22 N.m donor-drive hierarchy와 50 A current calibration은 GGM v0.8 물리 합격기준이 아니다.

Controlling sources: `control/ggm_drive_contract.json`, `analysis/drive_acceptance_v08/drive_component_register.csv`, `validation/physical_v08/P3_GGM_BENCH_KO.md`, `validation/physical_v08/P4_SHREDDER_COUPON_KO.md`.
""",encoding="utf-8")
    reference={
        "revision":"safety-orchestration-closure-v0.6.1","manufacturer":"TT Motor","part_number":"GMP60-60127-2460",
        "model":"GMP60-60127 24 V ratio 47","motor_type":"brushed PMDC planetary gearmotor",
        "published":{"voltage_v":24,"motor_power_w":138,"output_no_load_rpm":95,"output_rated_rpm":70,"continuous_torque_kg_cm":100,"continuous_torque_nm":9.80665,"no_load_current_a":0.75,"rated_current_a":8.2,"stall_current_a":31,"overall_axial_length_including_shaft_mm":211.8,"motor_diameter_mm":60.5,"motor_length_mm":127,"gearbox_diameter_mm":60,"gearbox_length_mm":59,"front_boss_diameter_mm":32,"front_boss_length_mm":4.85,"shaft_diameter_mm":12,"shaft_length_mm":25.8,"shaft_flat_length_mm":13,"shaft_flat_across_mm":10.9,"mounting":"4xM5 PCD45","gearbox_face_step_mm":2,"gear_ratio":47},
        "machine_interface":{"chain_ratio":"12T:30T","screening_efficiency":0.85,"cutter_rated_speed_rpm":28,"cutter_equivalent_continuous_capability_nm":20.84,"motor_side_relief_setting_nm":10.35,"adapter":"DRV-A60"},
        "rejected_requested_reference":{"part_number":"GMP42-775PM ratio 51","rated_speed_rpm":90,"rated_torque_kg_cm":26,"rated_torque_nm":2.5497,"cutter_equivalent_torque_12T_30T_efficiency_0_85_nm":5.42,"status":"REJECTED_CONTINUOUS_TORQUE","adapter_retained":"DRV-A42"},
        "source_url":"https://www.ttmotor.com/uploads/GMP60-609760127.pdf",
        "rejected_reference_source_url":"https://www.ttmotor.com/uploads/GMP42-775PM.pdf",
        "source_checked_date":"2026-09-09","selection_state":"LEGACY_GENERIC_REFERENCE_SUPERSEDED_BY_GGM_V08","purchase_allowed":False,
    }
    (base/"reference_variant.json").write_text(json.dumps(reference,indent=2,ensure_ascii=False)+"\n")
    with (base/"ratio_and_fuse_settings.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["input_teeth","output_teeth","ratio","efficiency","motor_rpm_for_cutter_20_40","minimum_motor_continuous_nm_for_14_cutter_nm","minimum_motor_peak_nm_for_24_cutter_nm","motor_side_electrical_trip_nm_for_18_cutter_nm","motor_side_mechanical_relief_nm_for_22_cutter_nm","status"])
        for output,ratio in ((18,1.5),(24,2.0),(30,2.5)):
            gain=ratio*0.85; w.writerow([12,output,ratio,0.85,f"{20*ratio:.0f}-{40*ratio:.0f}",f"{14/gain:.2f}",f"{24/gain:.2f}",f"{18/gain:.2f}",f"{22/gain:.2f}","LEGACY_GENERIC_DRIVE_NOT_GGM_ACCEPTANCE"])
    with (base/"donor_measurement_form.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["candidate_id","manufacturer","model","serial","quantity","condition","label_voltage_v","label_power_w","output_no_load_rpm","shaft_diameter_mm","shaft_form","shaft_length_mm","mount_pattern_mm","shaft_height_mm","overall_l_w_h_mm","no_load_current_a","continuous_current_a","stall_or_peak_current_a","backlash_deg","case_temp_after_30min_c","selected_chain_ratio","motor_side_relief_setting_nm","gate1_result","photo_hash","operator","status"]); w.writerow(["DONOR-","","","",1,"","","","","","key/D-flat/clamp","","","","","","","","","","","","NOT_RUN","","","UNVERIFIED"])
    return rows


def svg_gate1_hardcut(path):
    """Human-readable hardwired motor-energy cut schematic for Gate-1."""
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1189" height="841" viewBox="0 0 1189 841">
<style>text{font-family:'Noto Sans CJK KR',sans-serif;font-size:18px}.t{font-size:27px;font-weight:bold}.w{stroke:#17465a;stroke-width:4;fill:none}.c{fill:#eef4f6;stroke:#111;stroke-width:2}.n{font-size:15px}.danger{fill:#a12c2c}</style>
<text x="45" y="48" class="t">Optional Gate-1 24 V hardwired motor-energy cut — safety-orchestration-closure-v0.6.1</text>
<text x="45" y="83" class="danger">Mega output alone cannot energize K1. S0/S1 opening drops K0 and requires manual START reset.</text>
<rect x="55" y="145" width="120" height="70" class="c"/><text x="76" y="185">24 V PSU</text>
<path d="M175 170H235" class="w"/><rect x="235" y="145" width="95" height="50" class="c"/><text x="260" y="178">F1 20 A</text>
<path d="M330 170H390" class="w"/><rect x="390" y="135" width="130" height="70" class="c"/><text x="420" y="175">K1 NO</text><text x="410" y="195" class="n">DC >=30 V/25 A</text>
<path d="M520 170H580" class="w"/><rect x="580" y="135" width="145" height="70" class="c"/><text x="604" y="166">BTS7960</text><text x="596" y="193" class="n">reversing driver</text>
<path d="M725 170H785" class="w"/><rect x="785" y="135" width="145" height="70" class="c"/><text x="803" y="165">M1 GGM SH</text><text x="795" y="193" class="n">K9DG60N2+K9G75C</text>
<path d="M55 360H125" class="w"/><rect x="125" y="335" width="95" height="50" class="c"/><text x="151" y="368">F2 2 A</text>
<path d="M220 360H275" class="w"/><rect x="275" y="330" width="125" height="60" class="c"/><text x="295" y="356">S0 E-STOP</text><text x="307" y="380" class="n">NC, latching</text>
<path d="M400 360H455" class="w"/><rect x="455" y="330" width="145" height="60" class="c"/><text x="475" y="356">S1 GUARD</text><text x="468" y="380" class="n">positive-opening NC</text>
<path d="M600 360H655" class="w"/><rect x="655" y="330" width="125" height="60" class="c"/><text x="680" y="356">S2 START</text><text x="700" y="380" class="n">NO</text>
<path d="M780 360H835" class="w"/><rect x="835" y="320" width="115" height="80" class="c"/><text x="865" y="352">K0 coil</text><text x="844" y="378" class="n">manual-reset relay</text>
<path d="M950 360H1040V455H835" class="w"/><rect x="835" y="425" width="115" height="60" class="c"/><text x="860" y="452">K0 AUX</text><text x="869" y="475" class="n">seal-in NO</text>
<path d="M892 400V530H745" class="w"/><rect x="605" y="505" width="140" height="55" class="c"/><text x="627" y="538">K1 coil 24 V</text>
<path d="M55 360V215" class="w"/><text x="47" y="315" class="n">+24 V control</text>
<text x="55" y="635">Required point-to-point checks: S0 open -> K1=0; S1 open -> K1=0; power restore -> K1 remains 0 until S2;</text>
<text x="55" y="668">welded K1 main contact is detected only by motor-bus voltage/RPM check and requires lockout. K1 is not a safety relay.</text>
<text x="55" y="701">Mega monitors K0 auxiliary, K1 auxiliary/motor-bus voltage, current and RPM. It may request stop by opening an optional series output,</text>
<text x="55" y="734">but no Mega state may bridge S0 or S1. PE bonds PSU/chassis/metal guard; 0 V is not PE.</text>
<text x="55" y="795" class="n">Controlling connection list: wiring_bom.csv + fastener_schedule.csv + test_procedure_ko.md. Verify received-device terminal markings before wiring.</text>
</svg>
""",encoding="utf-8")


def write_gate1_package():
    base=ROOT/"exports/jigs/gate1"; (base/"parts").mkdir(parents=True,exist_ok=True)
    rows=export_shape_set(gate1_parts(),base/"parts")
    envelope=export_assembly(gate1_assembly(mode="manual"),base,"gate1_assembly")
    powered_envelope=export_assembly(gate1_assembly(mode="powered"),base,"gate1_powered_assembly")
    with (base/"jig_manifest.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["part_id","name","quantity","material","process","x_mm","y_mm","z_mm","critical","release_state"])
        for r in rows:
            w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"{r['x']:.2f}",f"{r['y']:.2f}",f"{r['z']:.2f}",r["critical"],"HOLD_USER_APPROVAL"])
    print_rows=[]
    for r in rows:
        if r["class_"]!="print": continue
        mass=r["shape"].Volume*1.24/1000*r["qty"]
        print_rows.append((r["id"],r["qty"],r["material"],"0.24 mm",3,"20%", "upright/end-face", "no; bridge only",f"{mass:.1f}"))
    with (base/"print_manifest.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["part_id","qty","material","layer_height","walls","infill","orientation","support","estimated_mass_g"])
        w.writerows(print_rows)
    total_print=sum(float(r[-1]) for r in print_rows)
    (base/"total_material_report.md").write_text(
        f"# Gate-1 jig 출력물 집계\n\n총 예상 PLA 질량은 `{total_print:.1f} g`이며 final-machine 출력 package와 분리한 시험 jig 집계다. "
        f"18,000 KRW/kg 기준 재료비는 약 `{total_print*18:.0f} KRW`다. 모든 부품은 각 축 210 mm 이하다.\n",encoding="utf-8")
    with (base/"bom.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["item_id","item","qty","source","planning_cash_krw","budget_bucket","status","reuse_after_test","notes"])
        data=[
            ("CUT-01","CUT-01 coupon disc",2,"exports/cnc/CUT-01",4000,"CNC-01","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","maximum Gate-1 release 2; remaining 10-disc full stack HOLD"),
            ("CUT-03","CUT-03 side plate",2,"exports/cnc/CUT-03",3000,"CNC-02","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","both plates are required by Gate-1 and reused; 42 H7 seats match-machined"),
            ("CUT-05","CUT-05 left shaft",1,"exports/cnc/CUT-05",3500,"CNC-03","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","left shaft; received inspection required"),
            ("CUT-05R","CUT-05R right clocked shaft",1,"exports/cnc/CUT-05R",3500,"CNC-03","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","right shaft key clock25.714 deg; received optical inspection required"),
            ("CUT-04","CUT-04 5 mm screen coupon",1,"exports/cnc/CUT-04",4000,"CNC-04","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","maximum Gate-1 release 1; second screen HOLD; actual clearance >=1.9 mm"),
            ("CUT-08","61905 bearing retainer",2,"exports/cnc/CUT-08",0,"CNC-02","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","positive bearing outer-ring retention; nested in CNC-02 allowance"),
            ("CUT-09","shredder chamber distance sleeve",4,"exports/cnc/CUT-09",0,"CNC-02","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","four matched steel sleeves isolate printed chute from chamber clamp load; nested in CNC-02 allowance"),
            ("CUT-10","61905 outer-ring seat ring",4,"exports/cnc/CUT-10",0,"CNC-02","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","OD42 g6; outer ring only; nested in CNC-02 allowance"),
            ("BRG-61905","SKF 61905-2RS1 bearing",4,"approved stock/buy",0,"HW-ALLOW","VERIFY_INVENTORY","yes","verify etched designation, 25x42x9, seal drag and corrosion; no order placed"),
            ("DRV-03","M3 Z16 solid phase gear left",1,"exports/drive_interface/parts/DRV-03",1500,"SH-INTERFACE","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","18 mm S45C; 8 mm matched key at datum0 deg"),
            ("DRV-03R","M3 Z16 solid phase gear right",1,"exports/drive_interface/parts/DRV-03R",1500,"SH-INTERFACE","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","yes","18 mm S45C; local key14.464 deg; installed tooth phase11.25 deg"),
            ("DRV-01/Axx","LEGACY universal motor adapter — DO NOT USE WITH GGM",1,"exports/drive_interface",0,"CNC-02","LEGACY_NOT_FOR_GGM_DO_NOT_FABRICATE","no","historical v0.6 powered fixture only; current P4 uses final GGM shredder drive"),
            ("GGM-SH-PATH","Current direct-keyed GGM protection/jackshaft + #35 12T:30T drive path",1,"control/ggm_drive_contract.json + analysis/drive_acceptance_v08/drive_component_register.csv",0,"SH-INTERFACE","P3_GGM_BENCH_PASS_REQUIRED_BEFORE_P4","yes","K9DG60N2+K9G75C; 4x4 key at 12T and 6x6 key at 30T carry torque; received maker axial retention required; DRV-02 superseded"),
            ("G1J-01","Reusable base plate",1,"donor plate; drawing supplied",0,"HW-ALLOW","VERIFY_INVENTORY","jig","380x280x8, flatness <=0.30; no zero-cash claim until verified"),
            ("G1J-02","250 mm torque arm",1,"exports/jigs/gate1/parts",0,"CNC-02","GATE1_RFQ_ALLOWED_USER_APPROVAL_REQUIRED","jig","manual configuration only; remove before powered configuration"),
            ("G1J-03","Front/rear polycarbonate panels",2,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","3 mm PC, never acrylic; bucket includes all G1J-03..06 sheet"),
            ("G1J-04","Left polycarbonate panel",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","3 mm PC"),
            ("G1J-05","Right slotted polycarbonate panel",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","open edge slot and baffle required"),
            ("G1J-06","Torque-slot offset baffle",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","blocks fragment line of sight"),
            ("G1J-07","20x20x2 metal guard upright L220",4,"standard angle stock",0,"HW-ALLOW","BUY_HOLD","jig","primary fragment-retention load path"),
            ("G1J-08","20x20x2 steel screen rail L150",2,"standard angle stock",0,"HW-ALLOW","BUY_HOLD","jig","shimmed/removable"),
            ("G1J-09","Interlock metal bracket",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","switch model-specific overtravel set at assembly"),
            ("G1J-10","40x40x4 CUT-03 foot L50",4,"standard angle stock",0,"HW-ALLOW","BUY_HOLD","jig","metal plate-to-base load path"),
            ("G1J-11","LEGACY DRV-01 foot L50",2,"same stock as G1J-10",0,"HW-ALLOW","LEGACY_NOT_FOR_GGM_DO_NOT_FABRICATE","no","historical powered fixture only; current GGM support uses final drive drawings"),
            ("G1J-12","Top polycarbonate panel with chute opening",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","3 mm PC closes fragment path; included in guard allowance"),
            ("MET-01","0-200 N force gauge or 100 kg load cell/HX711",1,"project-lab or buy allowance",7500,"GATE1-METROLOGY","CALIBRATION_HOLD","jig","accuracy <=2%; M8 clevis and independent safety tether"),
            ("G1J-P01..03","Printed chute/tray/edge trim",1,"exports/jigs/gate1/parts",4400,"GATE1-PRINT","PRINT_HOLD","jig","generated mass/cost must remain inside GATE1-PRINT bucket; cold low-load only"),
            ("COLLAR/KEY/SHIM","Ø25 split collars 8, 6x6 cutter keys, 8x7 gear keys, 0.25/0.50 metal shims",1,"standard hardware",0,"HW-ALLOW","BUY_HOLD","yes","coupon and shaft axial retention; no printed shim or set-screw-only torque path"),
            ("SAFE-K0/K1","Manual-reset control relay and 24 V motor power relay",1,"project-lab or SAFE-ALLOW",0,"SAFE-ALLOW","VERIFY_RATING","yes","K1 DC breaking rating >=30 V/25 A; K0 has seal-in auxiliary contact"),
            ("SAFE-S0/S1","Latching E-stop NC + positive-opening guard switch NC",1,"project-lab or SAFE-ALLOW",0,"SAFE-ALLOW","VERIFY_RATING","yes","series hard inhibit; Mega cannot bypass"),
            ("SAFE-F1/F2","20 A motor branch fuse + 2 A control fuse",1,"project-lab or fuse allowance",0,"FUSE-ALLOW","VERIFY_RATING","yes","close to 24 V source"),
            ("HW-SET","Fastener, shim, collar and clevis set",1,"fastener_schedule.csv",0,"HW-ALLOW","BUY_HOLD","yes","all quantities and torques in schedule; bucket cap retained"),
        ]
        w.writerows(data)
    with (base/"fastener_schedule.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["joint_id","mating_parts","fastener","qty","washer_nut","nominal_torque_Nm","locking","access_tool","inspection"])
        w.writerows([
            ("FST-01","G1J-01 to test table","M8 x25 class 8.8 hex",4,"M8 flat washer + fixture T-nut","18","mechanical prevailing nut/T-slot","13 mm socket","base flatness <=0.30 mm after torque"),
            ("FST-02","G1J-10 to G1J-01","M6 x20 class 8.8 hex",8,"M6 washer + nyloc","9","nyloc","10 mm socket","no foot rocking; witness mark"),
            ("FST-03","CUT-03 to four G1J-10","M6 x20 class 8.8 hex",8,"M6 washer + nyloc","9","nyloc","10 mm socket","plate perpendicularity <=0.20/125"),
            ("FST-04","G1J-08 screen rails to CUT-03/feet","M5 x16 class 8.8 hex",4,"M5 washer + nyloc","5","nyloc","8 mm socket","screen minimum cutter clearance >=1.9 mm"),
            ("FST-05","CUT-04 to G1J-08 rails","M5 x12 thumb screw",4,"M5 large washer + captive nut","3","captive nut","hand/8 mm","screen cannot lift; tool removal only after lockout"),
            ("FST-06","DRV-03/DRV-03R solid gear retention","M4 x22 class 10.9 SHCS",4,"M4 washer + all-metal locknut","3","all-metal locknut","3 mm hex + 7 mm spanner","2 bolts/gear; matched 8 mm key blue-checked"),
            ("FST-07","DRV-03/DRV-03R inspection registration","3 x18 hardened dowel h6",2,"press/slip fit per drawing","N/A","3 H7 inspection hole","arbor press","one dowel/gear; verify clock datum, not torque path"),
            ("FST-08","G1J-07 upright to G1J-01","M4 x16 class 8.8 hex",8,"M4 washer + nyloc","3","nyloc","7 mm socket","upright verticality <=0.5/180"),
            ("FST-09","G1J-03/04/05 PC panel to G1J-07","M4 x16 pan-head",24,"M4 nylon washer + nyloc","1.2","nyloc; no threadlocker on PC","PH2 + 7 mm","panel retained, no crazing; 0.5 mm compliant washer compression"),
            ("FST-10","G1J-06 baffle to G1J-05/upright","M4 x20 pan-head + 10 mm spacer",4,"nylon washer + nyloc","1.2","nyloc","PH2 + 7 mm",">=10 mm offset and no line-of-sight to cutter"),
            ("FST-11","G1J-09 switch bracket to upright","M4 x16 class 8.8",2,"washer + nyloc","3","nyloc","3 mm hex","positive opening and specified overtravel"),
            ("FST-12","received guard switch to G1J-09","M4 x20 pan-head",2,"washer + nyloc","1.2","nyloc","PH2 + 7 mm","terminal/actuator not preloaded beyond rating"),
            ("FST-13","G1J-P01 feed chute to guard","M4 x16 pan-head",4,"large washer + nyloc","1.2","nyloc","PH2 + 7 mm","anti-reach baffle intact; push-stick-only path"),
            ("FST-14","G1J-02 force gauge clevis","M8 shoulder bolt or clevis pin",1,"two retainers + independent tether","hand snug","double retention","pliers/13 mm","line of pull <=2 degree; tether slack under normal load"),
            ("FST-15","CUT-08 retainers to CUT-03","M4 x12 class 8.8 SHCS",12,"M4 washer + all-metal locknut","3","all-metal locknut","3 mm hex + 7 mm spanner","outer rings retained; seal untouched; free rotation"),
            ("FST-16","CUT-01 coupons and shafts","6x6 keys + eight Ø25 split collars",1,"0.25/0.50 metal shim set","collar maker rating","split clamp; no set-screw-only retention","hex key + feeler gauge","6.5 mm offset; axial working gap 0.25-0.50"),
            ("FST-17","DRV-01 to G1J-11/base","M6 x20 class 8.8 hex",8,"M6 washer + nyloc","9","nyloc","10 mm socket","plate verticality <=0.5/140; no rocking"),
            ("FST-18","DRV-Axx to DRV-01 and motor","received adapter drawing hardware",1,"hardened washers + prevailing nuts","supplier/drawing","prevailing hardware","torque wrench","pilot seated; sprocket TIR <=0.20; donor envelope clear"),
            ("FST-19","GGM_SH_12T/GGM_SH_30T axial retention","received sprocket maker axial-retention hardware",2,"maker-specified locking/retention feature","HOLD","maker specification; key carries torque","tool per received hardware","blue-check 4x4/6x6 keys; radial TIR <=0.10; axial shift+U95 <=0.20; chain alignment <=0.20/150; no friction-only torque path"),
            ("FST-20","G1J-12 roof and G1J-P01 chute","M4 x16 pan-head",12,"M4 nylon washer + nyloc","1.2","nyloc; no threadlocker on PC","PH2 + 7 mm","roof retained; chute gap <=1 mm; no unguarded opening >6 mm"),
            ("FST-21","CUT-03 pair through four CUT-09 sleeves","M6 x170 class 10.9 hex",4,"M6 hardened washer both ends + all-metal locknut","7","all-metal locknut; no threadlocker near polymer","10 mm socket + spanner","sleeves fully seated; plate inside gap128.00 +/-0.06; matched sleeve spread <=0.03; printed chute carries no clamp load"),
        ])
    with (base/"wiring_bom.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["ref","qty","functional_specification","source_priority","budget_bucket","received_inspection","release"])
        w.writerows([
            ("F1",1,"20 A DC branch fuse + holder, >=32 VDC interrupt rating","project-lab then low-cost buy","FUSE-ALLOW","continuity and holder heating at coupon current","HOLD"),
            ("F2",1,"2 A DC control fuse + holder, >=32 VDC","project-lab then low-cost buy","FUSE-ALLOW","continuity and polarity","HOLD"),
            ("S0",1,"latching mushroom E-stop, 1 NC positive-opening contact, >=24 VDC/1 A control","project-lab then low-cost buy","SAFE-ALLOW","terminal identity and forced-opening continuity","HOLD"),
            ("S1",1,"guard switch, positive-opening NC, metal actuator preferred","project-lab then low-cost buy","SAFE-ALLOW","travel/overtravel and forced-opening continuity","HOLD"),
            ("S2",1,"momentary START pushbutton, 1 NO, >=24 VDC/1 A","project-lab then low-cost buy","SAFE-ALLOW","contact continuity","HOLD"),
            ("K0",1,"24 VDC manual-reset control relay, >=2 NO auxiliary contacts, coil suppression","project-lab then low-cost buy","SAFE-ALLOW","coil voltage, seal-in drop on S0/S1","HOLD"),
            ("K1",1,"24 VDC motor-power relay/contactor, NO main contact >=30 VDC/25 A plus aux","project-lab then low-cost buy","SAFE-ALLOW","DC breaking rating; contact drop/temp under coupon load","HOLD"),
            ("DRV",1,"reversible 24 V motor driver, >=30 A peak with heatsink","existing BTS7960-class candidate","SH-DRIVE","load test and heatsink temperature","HOLD"),
            ("CS1",1,"bidirectional Hall motor-lead current sensor, 5 V analog, useful calibrated range 0-6 A","project-lab sensor or buy to current GGM contract","SH-DRIVE","A0 polarity/zero/span against independent reference; residual+U95 <=0.10 A","HOLD"),
            ("TB1",1,"touch-safe terminal block >=32 VDC/30 A","project-lab then low-cost buy","HW-ALLOW","rating and screw retention","HOLD"),
            ("WIRE-P",1,"red/black >=2.5 mm2 copper motor harness, 105 C","project-lab then low-cost buy","HW-ALLOW","crimp pull test and voltage drop","HOLD"),
            ("WIRE-C",1,"0.5-0.75 mm2 control wire, ferrules, labels","project-lab then low-cost buy","HW-ALLOW","point-to-point continuity","HOLD"),
            ("PE",1,"green/yellow >=2.5 mm2 chassis/guard bond with star washers","project-lab then low-cost buy","HW-ALLOW","<0.1 ohm bond at accessible metal","HOLD"),
        ])
    svg_gate1_hardcut(base/"wiring_24v_hardcut.svg")
    with (base/"specimen_schedule.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["material","specimen_type","nominal_thickness_or_fold","width_mm","length_mm","replicates","conditioning","id_pattern"])
        w.writerows([
            ("PLA","printed wall","1.2 mm",25,80,5,"23+/-2 C, dry surface","PLA12-01..05"),
            ("PLA","printed wall","2.0 mm",25,80,5,"23+/-2 C, dry surface","PLA20-01..05"),
            ("PLA","printed wall","3.0 mm",25,80,5,"23+/-2 C, dry surface","PLA30-01..05"),
            ("PET","bottle body single layer","measured actual",25,80,5,"label/cap/adhesive removed, dry surface","PET-B-01..05"),
            ("PET","four-layer folded seam","4 layers; measured total",25,80,5,"label/cap/adhesive removed, dry surface","PET-F-01..05"),
        ])
    with (base/"calibration_log_template.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["date_time","instrument_id","serial","reference_mass_kg","reference_force_N","indicated_force_N","error_percent","ambient_C","operator","pass_fail","evidence_path"])
        for mass,force in ((0,0),(5,49.05),(10,98.10),(15,147.15)):
            w.writerow(["","","",mass,f"{force:.2f}","","","","","",""])
    with (base/"preflight_inspection_template.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["item_id","inspection","method","acceptance","measured","unit","evidence_path","operator","reviewer","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        rows=(
            ("PF-01","base flatness","straightedge/feeler or indicator","<=0.30","mm"),
            ("PF-02","plate perpendicularity","square + feeler","<=0.20/125","mm/mm"),
            ("PF-03","both shaft TIR","dial indicator","<=0.10","mm"),
            ("PF-04","phase error","index marks/encoder","<=1.0","deg"),
            ("PF-05","minimum cutter-screen clearance","feeler gauge",">=1.90","mm"),
            ("PF-06","hand rotation 20 turns contact count","manual locked-out rotation","=0","count"),
            ("PF-07","PE bond worst point","four-wire/zero-compensated ohmmeter","<0.10","ohm"),
            ("PF-08","S0 opens K0/K1 and motor bus","continuity + bus voltage","K1=0 and bus=0","boolean/V"),
            ("PF-09","S1 opens K0/K1 and motor bus","continuity + bus voltage","K1=0 and bus=0","boolean/V"),
            ("PF-10","power restore automatic restart","power-cycle observation","must not restart","boolean"),
            ("PF-11","guard panel crack/line of sight","visual + reach probe","0 crack; no cutter reach","count/boolean"),
            ("PF-12","CUT-08/collar positive retention","visual + axial push/pull","no bearing/coupon axial release","boolean"),
            ("PF-13","DRV-03/DRV-03R key engagement and phase clock","blue check + optical index","full key engagement; installed tooth phase11.25 +/-1.0 deg; no relative slip","boolean"),
            ("PF-14","powered drive/outer guard clearance","feeler + hand rotation","moving drive clearance >=3; outer guard closed","mm/boolean"),
        )
        for item_id,inspection,method,acceptance,unit in rows:
            w.writerow({"item_id":item_id,"inspection":inspection,"method":method,"acceptance":acceptance,"unit":unit})
    with (base/"gate1_results_template.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["date_time","operator","reviewer","material","specimen_id","actual_thickness_or_fold_mm","trial","peak_N","radius_m","calculated_peak_Nm","force_angle_deg","failure_mode","permanent_damage","observation","photo_video_path","raw_log_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        groups=(("PLA","PLA12",5),("PLA","PLA20",5),("PLA","PLA30",5),("PET","PET-B",5),("PET","PET-F",5))
        for material,prefix,count in groups:
            for trial in range(1,count+1):
                w.writerow({"material":material,"specimen_id":f"{prefix}-{trial:02d}","trial":trial,"radius_m":"0.2500"})
    with (base/"drive_calibration_template.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["date_time","operator","reviewer","donor_id","calibration_type","point","input_teeth","output_teeth","motor_rpm","cutter_rpm","motor_current_A","no_load_current_A","force_N","arm_radius_m","cutter_torque_Nm","current_above_no_load_A","cutter_torque_per_amp_Nm_A","derived_efficiency","motor_case_C","relief_released","permanent_phase_damage","evidence_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        w.writerow({"calibration_type":"NO_LOAD","point":1,"input_teeth":12,"arm_radius_m":"0.2500"})
        for point,target in enumerate((2,4,6,7.5,8.0),1):
            w.writerow({"calibration_type":"GGM_GEARBOX_TORQUE_CURRENT_REFERENCE","point":point,"input_teeth":12,"arm_radius_m":"0.2500","cutter_torque_Nm":"","evidence_path":f"gearbox reference target {target} N.m; actual current/torque recorded in physical_v08 GGM inspection packet"})
        for point in range(1,4):
            w.writerow({"calibration_type":"GGM_MECH_PROTECTION_REFERENCE","point":point,"input_teeth":12,"arm_radius_m":"0.2500","cutter_torque_Nm":"","evidence_path":"gearbox-side target 8.8-9.3 N.m; physical_v08 GGM inspection packet governs"})
    with (base/"jam_recovery_results_template.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["date_time","operator","reviewer","material","trial","command_rpm","pre_jam_rpm","trip_cutter_torque_Nm","overload_duration_ms","rpm_drop_percent","rpm_drop_duration_ms","reverse_start_ms","reverse_duration_ms","retry_count","jam_cleared","latched_fault_after_third_failure","guard_lockout_required_for_reset","motor_case_C","permanent_damage","photo_video_path","raw_log_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for material,command_rpm in (("PLA",16),("PET",16)):
            for trial in range(1,4):
                w.writerow({"material":material,"trial":trial,"command_rpm":command_rpm,"trip_cutter_torque_Nm":""})
    with (base/"chip_size_results_template.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["date_time","operator","reviewer","material","batch_id","screen_hole_mm","screen_dwell_s","oversize_recirc_count","input_mass_g","mass_3_6_g","mass_6_20_g","mass_gt20_g","fines_lt3_g","recovered_total_g","fraction_3_6_percent","fraction_6_20_percent","fraction_gt20_percent","fines_percent","recovery_percent","longest_strip_mm","photo_path","scale_log_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for material in ("PLA","PET"):
            w.writerow({"material":material,"batch_id":f"{material}-CHIP-01","screen_hole_mm":5,"screen_dwell_s":5,"oversize_recirc_count":1})
    with (base/"evidence_manifest_template.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["evidence_id","evidence_type","relative_path","sha256","captured_at","operator","reviewer","notes"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for evidence_id,evidence_type in (
            ("EV-01","preflight_signed_csv"),("EV-02","force_calibration_signed_csv"),
            ("EV-03","drive_calibration_signed_csv"),("EV-04","torque_results_signed_csv"),
            ("EV-05","jam_results_signed_csv"),("EV-06","chip_size_signed_csv"),
            ("EV-07","photo_video_directory_manifest"),("EV-08","material_received_inspection"),
        ):
            w.writerow({"evidence_id":evidence_id,"evidence_type":evidence_type})
    (base/"gate1_release_record_ko.md").write_text("""# Gate-1 release record — 물리시험 후 작성

- revision: `safety-orchestration-closure-v0.6.1`
- 현재 상태: `NOT_RUN`
- preflight CSV SHA-256:
- force calibration CSV SHA-256:
- drive calibration CSV SHA-256:
- torque CSV SHA-256:
- jam CSV SHA-256:
- chip-size CSV SHA-256:
- evidence manifest SHA-256:
- photo/video evidence directory:
- CUT-01/CUT-04 material certificate 또는 received inspection:
- donor motor exact model/label/shaft/no-load current/30 min temperature:
- PLA max/median torque:
- PET body max/median torque:
- PET folded seam max/median torque:
- jam/reverse 3회 결과:
- chip-size mass fractions/recovery:
- 손상/영구변형/guard 결함:
- 결론: `NOT_RUN | FAIL | PASS`
- 시험자/날짜/서명:
- 검토자/날짜/서명:

`PASS`는 `test_procedure_ko.md`의 모든 기준, traceable calibration과 원시 증거가 동시에 충족될 때만 별도 empirical record에 기록한다. 이 template의 존재는 시험 결과가 아니다. 미수행은 `main`을 차단하지 않지만 full cutter/screw-barrel 발주는 별도 사용자 승인 전 금지한다.
""",encoding="utf-8")
    (base/"assembly_ko.md").write_text(f"""# Gate-1 cutter coupon jig 조립도 — v0.8 GGM 호환

- manual coupon geometry lineage: `safety-orchestration-closure-v0.6.1`
- current powered drive authority: `validation/physical_v08/physical_gate_contract.json`
- nominal manual assembly envelope: `{envelope[0]} x {envelope[1]} x {envelope[2]} mm`
- legacy powered STEP envelope: `{powered_envelope[0]} x {powered_envelope[1]} x {powered_envelope[2]} mm` — **reference only, do not energize as current configuration**

## Manual coupon 조립

1. G1J-01을 고정 table에 M8 네 점으로 체결하고 0.3 mm 이내 평면을 확인한다.
2. G1J-10 feet에 CUT-03 두 장, CUT-10 seat ring 네 개, 61905/6905 25x42x9 bearing 네 개와 CUT-08 retainer를 조립한다. Outer ring만 press한다.
3. CUT-05/CUT-05R에 CUT-01을 축당 한 장만 장착하고 metal collar/shim으로 axial working gap 0.25–0.50 mm를 맞춘다.
4. CUT-04 5 mm screen coupon은 cutter tip과 실제 최소 1.90 mm clearance를 유지한다.
5. DRV-03/DRV-03R phase gear를 설치하고 tooth phase 11.25±1.0°, hand rotation 20회 무간섭을 확인한다.
6. G1J-02 torque arm의 실제 radius를 250.0±0.5 mm로 측정하고 force gauge/load cell을 독립 tether와 연결한다.
7. 3 mm polycarbonate guard와 roof/baffle를 조립하고 unguarded opening≤6 mm를 확인한다.
8. S0 E-stop/S1 positive-opening interlock hard-cut을 검증한다. 자동 재가동은 허용하지 않는다.

## Powered coupon 변경

Manual torque test 뒤 torque arm을 제거한다. **legacy `gate1_powered_assembly.step`, DRV-01/Axx, DRV-F01 경로는 사용하지 않는다.** Powered coupon은 P3 GGM bench PASS 이후 final GGM shredder path `K9DG60N2+K9G75C → GGM protection coupling → 6201 jackshaft → #35 12T:30T → CUT-05R`를 사용한다. Manual arm과 powered drive는 동시에 장착하지 않는다. 12T/30T는 각각 4x4/6x6 key가 토크를 전달하고, 수령된 sprocket의 maker axial-retention feature가 별도로 축방향 위치를 유지해야 한다. `DRV-02`는 이 경로에서 사용하지 않는다.

고하중 구조경로는 cutter → metal shaft → 61905/CUT-10/CUT-08 → CUT-03 → G1J-10/GGM final support → frame/table이다. 출력 chute/tray/printed trim은 구조 하중경로가 아니다.
""",encoding="utf-8")
    (base/"test_procedure_ko.md").write_text("""# Gate-1 CUT-01 coupon 시험 절차 — GGM v0.8 적용본

현재 controlling 상위 계약은 `validation/physical_v08/physical_gate_contract.json`이다. 기존 `gate1_powered_assembly.step`, DRV-01/Axx/F01 powered 경로와 18/22/24 N·m 합격기준은 **legacy**이며 현 GGM 구동 시험에 사용하지 않는다. 이 문서의 manual coupon geometry와 계측 양식은 계속 사용한다.

## 시험 전 부품과 계측

- CUT-01 coupon은 축당 1개, 총 2개만 제작한다. 나머지 10개는 Gate-1 PASS 전 제작하지 않는다.
- CUT-04 5 mm screen coupon 1개, CUT-05/CUT-05R 각 1개, CUT-03 plate 2개, 61905/6905 25×42×9 bearing 4개와 해당 metal retainer/seat를 사용한다.
- Powered 시험은 최종 GGM shredder path `K9DG60N2 + K9G75C → GGM protection coupling → 6201-supported jackshaft → #35 12T:30T`를 사용한다.
- PLA wall 1.2/2.0/3.0 mm와 cleaned PET body를 specimen ID별로 준비한다. 실제 폐출력물/PET 형태를 사진으로 남긴다.
- 0–200 N verified force gauge/load cell, 250.0 mm arm, 독립 tach, calibrated motor-lead current sensor, 3/6/20 mm sieve, 0.1 g scale를 사용한다.

## A. Lockout와 cold mechanical

1. Main power 0 V 상태에서 shaft/plate/bearing/gear/screen의 실제 part ID와 revision을 기록한다.
2. Hand rotation 20회에서 cutter/plate/gear/screen 접촉 0, shaft TIR ≤0.10 mm, phase error ≤1.0°, bearing/retainer axial release 0을 확인한다.
3. rotating-to-static clearance는 최소 1.90 mm다. Guard와 positive-opening interlock이 닫히지 않으면 powered 단계로 가지 않는다.
4. Manual torque arm과 powered GGM coupling은 동시에 장착하지 않는다.

## B. Quasi-static cutter demand

1. Coupon을 정해진 capture point에 놓고 guard를 닫은 뒤 250.0 mm torque arm을 3–5 rpm 상당의 낮은 속도로 당긴다.
2. `T_peak = F_peak × 0.2500 m`로 specimen별 peak/median과 capture/buckle/shear/slip mode를 기록한다.
3. 이 시험은 실제 PLA/PET cutter demand를 측정하기 위한 것이며 과거 14/18/22/24 N·m 숫자를 강제 합격점으로 쓰지 않는다.
4. 어떤 specimen에서도 shaft/gear/plate의 영구변형, tooth/key 손상, bearing release가 있으면 FAIL이다.

## C. GGM drive와 controlled jam

1. P3 GGM bench gate가 먼저 PASS해야 한다. 즉 current calibration, output torque holdout, software limit 8.0 N·m, mechanical protection 8.8–9.3 N·m가 실제 기록으로 확인되어야 한다.
2. Powered coupon은 legacy `gate1_powered_assembly.step` 대신 final GGM drive manufacturing/assembly 자료를 사용한다. Shredder cutter speed 목표는 약 16 rpm이며 실제값을 기록한다.
3. 정상 PLA/PET body 투입에서 8.0 N·m gearbox software limit가 반복적으로 동작하면 처리량/투입법을 낮추고 원인을 기록한다. 정상 처리 합격을 위해 protection threshold를 올리지 않는다.
4. Controlled jam은 guard closed 상태에서 소수의 정해진 specimen으로 수행한다. Guarded stop/reverse sequence와 tach-loss behavior가 현 GGM firmware contract대로 bounded하게 끝나야 하며 세 번째 실패 이후 latched fault가 유지되어야 한다.
5. Jam 제거 전 자동 재시작이 발생하거나, mechanical protection 뒤 구동계/chain/phase gear에 영구변형이 생기면 FAIL이다.

## D. Chip-size / 재순환

1. 재질별 최소 30 g을 CUT-04 5 mm screen으로 처리하고 20/6/3 mm sieve로 분류한다.
2. 1차 결과와 oversize 1회 재순환 결과를 분리해서 기록한다.
3. 최종 합격은 재순환 1회 이하에서 `3–6 mm ≥70%`, `>20 mm PET strip ≤2%`, `<3 mm fines ≤15%`, 총 회수율 `≥95%`다.
4. 미달이면 남은 CUT-01 10개를 제작하지 않고 hook/screen/feed strategy만 수정한다.

## 기록

기존 `preflight_inspection_template.csv`, `calibration_log_template.csv`, `drive_calibration_template.csv`, `gate1_results_template.csv`, `jam_recovery_results_template.csv`, `chip_size_results_template.csv`, `evidence_manifest_template.csv`를 계속 사용하되 GGM field mapping은 `validation/physical_v08`와 `analysis/drive_acceptance_v08/manufacturing/inspection_packet_template.json`이 우선한다. Simulation 값을 실제 measurement 칸에 복사하지 않는다.
""",encoding="utf-8")


def write_extruder_package():
    base=ROOT/"exports/cnc/extruder"; (base/"parts").mkdir(parents=True,exist_ok=True)
    rows=export_shape_set(extruder_rfq_parts(),base/"parts")
    with (base/"rfq_manifest.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["part_id","name","qty","material","process","step","drawing","release"])
        for r in rows:
            if r["id"] in ("EX-SCR-01", "EX-BAR-01"):
                drawing=f"{r['id']}_drawing.svg"
            elif r["id"].startswith("EX-DIE-"):
                drawing="EX-DIE_drawing.svg"
            else:
                drawing="EX-CPN_drawing.svg"
            release="COUPON_RFQ_ALLOWED" if r["id"].startswith("EX-CPN-") else "HOLD_PROCESS_COUPON_AND_GATE3"
            w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"parts/{r['id']}/{r['id']}.step",drawing,release])
    svg_screw_drawing(base/"EX-SCR-01_drawing.svg"); svg_barrel_drawing(base/"EX-BAR-01_drawing.svg"); svg_process_coupon_drawing(base/"EX-CPN_drawing.svg"); svg_die_drawing(base/"EX-DIE_drawing.svg")
    with (base/"screw_profile.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["zone","z_start_mm","z_end_mm","length_D","root_diameter_mm","pitch_mm","land_mm"])
        w.writerows([("feed",0,128,8,10.88,16,1.60),("compression",128,192,4,"10.88_to_14.08",16,1.60),("meter",192,256,4,14.08,16,1.60)])
    with (base/"inspection_report_template.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["part_id","serial_or_lot","characteristic","station_mm","direction","lower_limit_mm","upper_limit_mm","measured","instrument_id","temperature_C","pass_fail","certificate_or_trace"])
        w.writerows([
            ("EX-CPN-SCR","","length","overall","axial",47.95,48.05,"","",20,"",""),
            ("EX-CPN-SCR","","flight_OD","8/24/40","micrometer",15.90,15.92,"","",20,"",""),
            ("EX-CPN-SCR","","root_OD","8/24/40","diameter",10.85,10.91,"","",20,"",""),
            ("EX-CPN-SCR","","pitch","three pitches","axial",15.97,16.03,"","",20,"",""),
            ("EX-CPN-SCR","","land","three flights","normal",1.55,1.65,"","",20,"",""),
            ("EX-CPN-SCR","","end_perpendicularity","both ends","to axis",0,0.03,"","",20,"",""),
            ("EX-CPN-BAR","","length","overall","axial",59.95,60.05,"","",20,"",""),
            ("EX-CPN-BAR","","OD","representative","diameter",33.95,34.05,"","",20,"",""),
            ("EX-CPN-BAR","","bore_ID","20/40","X/Y",16.20,16.22,"","",20,"",""),
            ("EX-CPN-BAR","","end_perpendicularity","both ends","to bore",0,0.03,"","",20,"",""),
            ("EX-CPN-SCR/BAR","","diametral_clearance","matched min/max including measurement uncertainty","derived",0.28,0.32,"","",20,"",""),
            ("EX-CPN-SCR","","qt_core_hardness","microsection","HRC",28,32,"","",20,"",""),
            ("EX-CPN-BAR","","qt_core_hardness","microsection","HRC",28,32,"","",20,"",""),
            ("EX-CPN-SCR","","surface_hardness","after final grind","HV0.3",900,1100,"","",20,"",""),
            ("EX-CPN-BAR","","surface_hardness","after final hone","HV0.3",900,"","","",20,"",""),
            ("EX-CPN-SCR","","effective_case_depth","after final grind","mm",0.30,0.50,"","",20,"",""),
            ("EX-CPN-BAR","","effective_case_depth","after final hone","mm",0.25,"","","",20,"",""),
            ("EX-CPN-BAR","","nitriding_case_process_target","before final hone / certificate","mm",0.30,0.50,"","",20,"",""),
            ("EX-CPN-SCR","","flight_OD_Ra","one trace","um",0,0.8,"","",20,"",""),
            ("EX-CPN-SCR","","root_flank_Ra","one trace","um",0,1.6,"","",20,"",""),
            ("EX-CPN-BAR","","bore_Ra","one trace","um",0.4,0.8,"","",20,"",""),
            ("EX-DIE-01","","barrel_face_flatness","entire face","mm",0,0.03,"","",20,"",""),
            ("EX-DIE-01","","melt_channel_ID","horizontal/vertical","X/Z",8.00,8.10,"","",20,"",""),
            ("EX-DIE-01","","insert_seat_ID","14 deep","Z",12.00,12.03,"","",20,"",""),
            ("EX-DIE-03","","orifice_ID","10 mm land","Z",3.00,3.02,"","",20,"",""),
            ("EX-DIE-03","","orifice_concentricity","to OD","TIR",0,0.02,"","",20,"",""),
            ("EX-DIE-04","","relief_open_pressure","three coupons","MPa",3.0,6.0,"","",20,"","physical coupon required"),
        ])
    with (base/"supplier_deviation_template.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["item","drawing_requirement","supplier_yes_no","proposed_deviation","price_effect_krw","lead_time_effect_days","customer_disposition"])
        for item in ("material/certificate","QT hardness","nitriding/case certificate","pitch-land-root-OD","TIR/concentricity","barrel final hone","matched clearance","die intersecting-channel deburr","die insert land/concentricity","relief coupon price/lead time","inspection reports","coupon price/lead time","full-part price/lead time"):
            w.writerow([item,"see controlling drawing/audit","","","","","HOLD"])
    (base/"manufacturing_audit_ko.md").write_text("""# 16 mm x 16 L/D screw/barrel 제조성 audit — RFQ 기준

## Controlling geometry

STEP은 3D 견적/간섭 기준, SVG와 본 문서는 치수·GD&T 기준이다. STL/DXF는 CAM reference이며 공차를 대체하지 않는다. 공급사는 임의로 clearance나 heat treatment를 변경하지 않는다.

- 모든 치수는 mm, 표면조도는 Ra µm, 별도 표기 없는 선형치수 공차는 ±0.10 mm, 각도는 ±0.5°다.
- 재료는 SCM440 KS D3867/JIS G4105 또는 동등 chemical/mechanical certificate를 제출한다. Supplier stock allowance는 임의이지만 추천 rough blank는 screw Ø22 x330, barrel solid/seamless Ø42 x295다.
- 임의 대체재·공정·공차 이탈은 deviation list에 써서 회신하며 무응답은 수락으로 간주하지 않는다.
- JLCCNC는 2026-09-08 회신에서 비목록 SCM440 조달, Q&T, 가스질화 및 coupon-first 생산 순서를 지원하지 않는다고 확인되어 현 사양 공급 후보에서 제외했다. 다른 전문 업체도 동등재 성적서만으로 대체 승인하지 않으며, 45# steel 등을 자동 선택하지 않는다. baseline SCM440/Q&T 경로는 적용 규격 판본·최종 QT/질화 상태를 제출한다. 245–270 °C 최종상태 물성은 제공 가능하면 수집하되 baseline P5의 단독 blocker로 두지 않는다. 재료·열처리 deviation은 해당 고온 물성 근거를 제출하고 설계 재해석 후 별도 승인한다.

## EX-SCR-01 screw

- SCM440, normalized blank → rough turn → QT 28–32 HRC → centres 유지.
- Total 316.0 ±0.10. Rear drive 0–35, thrust journal 35–55, neck 55–60, active 60–316. Active 256.0; single-start RH; pitch 16.00 ±0.03; flight land 1.60 ±0.05. Flight은 두 active-section end plane과 만나며 end burr R0.2 max, undercut·weld build-up은 금지한다.
- Zone 8D/4D/4D. Root Ø10.88 feed, linear compression, Ø14.08 meter. Flight OD Ø15.92 -0.02/0.
- Drive Ø12 h6 x35 with KS/DIN 4 x4 key, shaft keyseat 4 P9 wide x2.5 +0.10/0 deep; thrust journal Ø15 h6 x20; neck root Ø10.88 x5. Datum A는 Ø12/Ø15 journal의 common axis이며 shoulder/end face는 A에 직각도 0.03. Flight start angle은 active start에서 key centre plane 기준 0° ±5°.
- 4-axis flight mill leaving 0.15 mm grind/polish allowance. Root/flank Ra≤1.6 µm, flight OD Ra≤0.8 µm.
- Gas nitride 0.30–0.50 mm effective case, surface 900–1100 HV0.3; mask drive/thrust journals and keyseat. Final flight-OD grind between retained centres. Nitriding distortion 후 journal h6/TIR을 최종 확인한다.
- Flight OD TIR ≤0.05 over active 256; drive-to-flight concentricity ≤0.03; straightness ≤0.05/256. No weld repair.

## EX-BAR-01 barrel

- SCM440 solid/seamless blank, QT 28–32 HRC. OD Ø34.00 -0.03/0, length 280.00 ±0.05. Rear face=Datum B, front face=Datum C, final bore axis=Datum D. Assembly에서 B는 screw active start와 일치하고 screw tip은 C 뒤 24.0 ±0.2에 위치한다.
- Bore after final hone Ø16.20 +0.02/0, Ra≤0.4–0.8 µm. Bore straightness ≤0.05/256 and concentricity to OD/register ≤0.05.
- Feed opening은 축방향 18.00 ±0.10 x chord width 20.00 ±0.10, rear edge B+12.00 ±0.10. Port centre plane을 전면 bolt pattern의 0° 각도 기준으로 삼는다. Bore-intersection edge R0.5 ±0.2; screw flight 위 sharp edge 금지.
- T1/T2/T3 radial blind sensor bores는 B+95.00/170.00/245.00 ±0.10, Ø3.20 +0.05/0, flat-bottom depth5.40 ±0.05이다. 깊이는 OD 진입점에서 평바닥까지이며 drill cone을 추가하지 않는다. 다른 tool-tip 형상은 deviation으로 제출한다. Bore axis 위치는 Datum D 기준0.05 max, 직각도는0.10/5.5 이내다. 편심·기울기·치수 한계를 포함한 보수적 최소 ligament는3.345 mm로 요구값3.32 mm를 넘는다. 프로브 선정·삽입·고정·열응답은 별도 HOLD이며 plug/depth gauge 결과를 제출한다.
- Front die interface는 4x M4 x0.7-6H, full thread depth 8 minimum, tap-drill depth 11 minimum, PCD26.00 ±0.05 at 45/135/225/315° ±0.2° from feed-port centre plane이다. Ø3.3 tap drill 기준 nominal outer ligament 2.35 mm, bore-side ligament 3.25 mm이고 M4 major envelope 기준으로도 각각 2.0/2.9 mm 이상이다. 나사·counterbore가 OD 또는 bore로 breakthrough하면 FAIL이다. B/C faces은 D에 직각도 0.03; OD concentricity to D ≤0.05.
- Rough turn/deep drill → 600–650 °C stress relieve(재료 공급사 표준 cycle, certificate 기록) → datum-face/OD finish → semi-finish ream/hone leaving 0.05–0.08 mm on diameter → feed port/thread machine → gas nitride 0.30–0.50 mm, ≥900 HV0.3 → final hone. Effective case after final hone is ≥0.25 mm.
- Report bore at 20/140/260 mm and roundness ≤0.02 at each station. Front/rear face perpendicularity 0.03 to bore axis.

## Matched clearance and inspection

Specified drawing-limit diametral clearance is 0.28–0.32 mm and radial clearance is 0.14–0.16 mm. Supplier는 20 ±2 °C에서 screw OD를 active z=20/140/240, barrel ID를 B+20/140/260의 서로 직교하는 2개 방향으로 측정하고 최소/최대 clearance가 범위 안인 pair만 표식한다. Air/bore-gauge report, hardness/case-depth certificate, material certificate, Ra trace, pitch check과 TIR inspection sheet은 RFQ deliverable이다.

## DFM decision

SCM440 was selected over stainless for local availability, machinability and nitriding cost. PET-temperature metal compatibility is adequate for a research coupon, but corrosion/wear life is not certified. `EX-CPN-SCR` 3-pitch와 `EX-CPN-BAR` 60 mm process coupon만 먼저 견적·가공할 수 있다. Coupon의 치수·경도·case depth·Ra가 본 도면을 만족하고 공급사 DFM이 닫힌 뒤에도 Gate-3 cold proof 전 full screw/barrel 발주는 HOLD다. No physical result is claimed here.

Coupon controlling dimensions: EX-CPN-SCR L48.00 ±0.05, three RH pitches 16.00 ±0.03, OD/root/land와 열처리는 EX-SCR-01 feed zone과 동일하며 journal은 없다. EX-CPN-BAR L60.00 ±0.05, OD Ø34.00 ±0.05, final ID Ø16.20 +0.02/0, bore Ra/case는 EX-BAR-01과 동일하다. 두 coupon의 ends는 axis에 0.03 이내 수직이다. Coupon은 matched pair로 표식하고 실측 diametral clearance 0.28–0.32 mm여야 한다.

## EX-DIE connected open-die assembly

`EX-DIE-01`은 barrel 전면에 SYS-04 4×M4×45 class 10.9 SHCS를 42.5±0.1 mm로 절단·디버링해 `EX-DIE-05` annealed copper gasket와 체결하는 40×40×48 SCM440 body다. die grip34.95–35.05, 압축 gasket0.25–0.53, barrel full thread depth8.00에서 물림6.82–7.40 mm와 thread-bottom 여유0.60–1.18 mm를 확보한다. 디지털 6 MPa joint screen은 1.50 N·m dry design torque에서 PASS이며, 실제 수령 길이·누설·첫 thermal cycle witness check는 NOT_RUN이다. Ø8 수평 유로와 Ø8 수직 유로는 X20/Z0에서 실제로 교차하며, 공급사는 교차부를 borescope로 확인하고 burr·step을 R0.3 이하로 제거한다. Barrel-side에는 Ø15.90×2 `EX-DIE-02` seven-hole 304 breaker가 Ø16.20×3 seat에 갇힌다. Bottom에는 OD Ø11.90×14 `EX-DIE-03` 17-4PH H900 insert가 Ø12.00×14 seat에 들어가고 Ø3.00×10 land와 4 mm conical transition으로 open discharge한다. 직접 hot path에 polymer는 없다.

Body sealing face flatness는 0.03, melt channel Ø8 H9, insert seat Ø12.00 +0.03/0, breaker seat Ø16.20 +0.05/0이다. Heater bore Ø6.55 H7 reamed through와 lead-face 2×M3×0.5-6H depth6(14 mm pitch) flange thread, sensor bore Ø3.20 +0.05/0 blind12는 유로와 bolt를 관통하지 않는다. Body는 6-face datum machining → intersecting drill/ream → stress relieve → final seat/face → gas nitride → sealing face lap 순서다. Channel/seat에는 weld repair와 plating을 금지한다.

`EX-DIE-04`는 304 stainless t1.5의 교환식 sacrificial retainer다. 두 10 mm wide ×2.5 mm long web, 265 °C 보수 항복강도 150 MPa와 Ø11.9 insert에서 Ø3 orifice를 뺀 투영면적을 쓴 단순 탄성 항복 screening은 약 4.32 MPa이며 normal 3 MPa와 motor-trip equivalent 6 MPa 사이를 겨냥한다. 이는 release 값이 아니다. 동일 lot coupon 3개를 shielded heated hydraulic fixture에서 265 °C 조건으로 시험해 최초 영구변형/우회 개방이 3–6 MPa이고 fragment/ejection이 없을 때만 사용한다. Retainer는 insert를 포획한 채 우회 유로를 열어야 하며, grounded metal shield와 remote first-hot-test 없이는 가열하지 않는다. Full die assembly 역시 process coupon, relief coupon 및 Gate-3 전 `HOLD_PROCESS_COUPON_AND_GATE3`다.
""",encoding="utf-8")
    (base/"supplier_rfq_checklist_ko.md").write_text("""# 공급사 RFQ 응답 checklist

공급사는 가격만 답하지 말고 아래를 yes/no/deviation으로 회신한다.

1. SCM440 mill certificate와 QT 28–32 HRC 제공 가능 여부.
2. Screw 316/256 mm, pitch/land/root/OD와 Ø12 h6 keyseat, Ø15 h6 journal 가공 가능 여부.
3. Flight OD TIR 0.05/256, concentricity 0.03, Ra 0.8 검사 가능 여부.
4. Barrel Ø16.20 +0.02/0 final hone, three-station ID/roundness와 Ra report 가능 여부.
5. Front 4×M4-6H depth8/PCD26 가공 후 OD/bore breakthrough가 없고 major-envelope ligament outer 2.0 mm, bore-side 2.9 mm 이상인지 확인.
6. B+95/170/245의 3× Ø3.20 +0.05/0 flat-bottom blind5.40 ±0.05 thermocouple bore는 보수적 최소 ligament3.345 mm(요구≥3.32)를 적용한다. 각 보어 양쪽 axial pitch10에 TH-TCR-01용 2×M3-6H depth4를 가공한다. 평바닥 외 공구 형상은 deviation이며 Tempco MTA1 Ø3.00±0.03/stop5.20±0.05 승인도면과 독립 대조한다.
7. Gas nitride case/surface hardness certificate, screw final-grind 후 effective case 0.30–0.50 mm, barrel final-hone 후 effective case ≥0.25 mm 가능 여부. Barrel의 nitride 공정 목표 0.30–0.50 mm와 final-hone 제거량을 함께 기록한다.
8. Drawing-limit radial clearance 0.14–0.16 matched measurement 가능 여부.
9. EX-CPN-SCR/EX-CPN-BAR coupon 단가·납기와 full part 단가·납기를 분리 기재.
10. 모든 deviation과 대체재를 발주 전 명시. 무응답 항목은 수락으로 간주하지 않는다. Baseline SCM440의 245–270 °C 물성은 가능하면 제출하되, 재료/열처리 deviation 제안 시에는 재해석 입력으로 필수다.
11. EX-DIE-01 intersecting Ø8 channel borescope/deburr, face flatness와 seat ID report 가능 여부.
12. EX-DIE-03 Ø3×10 land Ra≤0.4 및 OD 기준 concentricity 0.02 검사 가능 여부.
13. EX-DIE-04 동일 lot relief coupon 3개와 shielded 265 °C, 3–6 MPa 개방압 시험은 full die와 분리 견적한다.

Full part order release는 `HOLD_PROCESS_COUPON_AND_GATE3`이며 본 checklist가 닫혀도 자동 승인되지 않는다.
""",encoding="utf-8")


def write_thermal_package():
    """가열기·센서의 실제 형상과 구매 전 RFQ 계약을 생성한다."""
    base=ROOT/"exports/thermal"; (base/"parts").mkdir(parents=True,exist_ok=True)
    cutoff=json.loads((ROOT/"control/thermal_cutoff_contract.json").read_text(encoding="utf-8"))
    inv=cutoff["inventory"]
    if inv["procurement_quantity"] != inv["installed_quantity"] + inv["spare_quantity"] or inv["installed_quantity"] != 2:
        raise RuntimeError("thermal cutoff inventory contract is inconsistent")
    fuse=Part.makeBox(20,6,8)
    specs=[
        dict(id="TH-BH-01",name="Custom barrel mica band heater",shape=mica_band_heater_shape(),qty=3,material="mica/NiCr/stainless sheath",process="custom heater RFQ",critical="24 VDC 100 W each; free-state ID34.10–34.20; usable split-closure travel >=1.00; width45 ±0.5; radial build2 nominal; cold resistance 5.76 Ω ±10%; 300 mm fiberglass leads; PE-bonded sheath; PET service 300 C design; no stock Ø35 substitution"),
        dict(id="TH-DIE-01",name="Die cartridge heater",shape=die_cartridge_heater_shape(),qty=1,material="Tempco custom Hi-Density; 321SS sheath; 304SS flange",process="custom RFQ + accepted drawing + receipt test NOT_RUN",critical="24 VDC 60 W; Ø6.500 ±0.013 Type CG; insertion39.50 ±0.20 Type OAL; lead-end cold≥9.5 and disc-end cold≥6.4; HTL550 C leads; custom MFR flange t1.5 20x12 with 2xØ3.4 at14 pitch; cold resistance9.12–10.56 Ω; fit EX-DIE-01 Ø6.55 H7=6.550–6.565; diametral clearance0.037–0.078; SYS-16 positive retention; vendor acceptance/received OD-camber-insulation required; HOLD purchase/energization"),
        dict(id="TH-TC-01",name="Tempco MTA1 custom ungrounded Type-K probes",shape=k_type_probe_shape(),qty=5,material="Alloy 600 MI sheath Ø3.00 ±0.03; 96% MgO; supplier-welded 304SS stop collar",process="custom Tempco RFQ; accepted drawing/receipt0 C insulation and thermal response receipt tests NOT_RUN",critical="MTA1 options K/2/M/A/Q, ungrounded U, sheath25.40 mm, fiberglass lead300 mm, high-temp ceramic potting; T1-T3 collar gives insertion5.20 ±0.05, T4 10.00 ±0.05, T5 4.00 ±0.05; flat closed tip; collar Ø6.0x0.8; bore Ø3.20 +0.05/0 gives diametral clearance0.17-0.28; no compression fitting; exact MPN assigned after quote; supplier drawing/insulation/calibration/thermal-response receipt evidence HOLD"),
        dict(id="TH-TCR-01",name="Thermocouple stop-collar retainer bridge",shape=thermocouple_retainer_shape(),qty=4,material="304 stainless t1.5",process="laser/waterjet + deburr",critical="12x16x1.5; centre Ø3.4; 2xØ3.4 at10 pitch; retain supplier-welded Ø6x0.8 collar with 2xM3x6 A4-80 at0.5 N.m; no clamp load on MI sheath; prove >=20 N axial pull cold and after thermal cycle"),
        dict(id="TH-FUSE-01",name="Independent one-shot thermal fuse envelope",shape=fuse,qty=inv["procurement_quantity"],material="300 C-class barrel/die protection",process="purchased + lot continuity/traceability",critical="two installed one-shot devices (TF-BARREL + TF-DIE) in series in the K0 coil safety chain plus one same-spec spare; H1-H4 use branch fuses only; exact body/lead crimp from selected datasheet; never solder within hot zone"),
    ]
    for obsolete in ("TH-PTC-EL", "TH-PTC-01", "TH-PTC-02"):
        shutil.rmtree(base / "parts" / obsolete, ignore_errors=True)
    rows=export_shape_set(specs,base/"parts")
    with (base/"manifest.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["part_id","name","quantity","material","x_mm","y_mm","z_mm","release_state"])
        for r in rows:w.writerow([r["id"],r["name"],r["qty"],r["material"],f"{r['x']:.2f}",f"{r['y']:.2f}",f"{r['z']:.2f}","USER_APPROVAL_AND_RECEIPT_TEST_HOLD"])
    (base/"thermal_cutoff_topology.json").write_text(json.dumps(cutoff,indent=2)+"\n",encoding="utf-8")
    (base/"heater_rfq_ko.md").write_text("""# v0.6 가열계 RFQ 및 수령검사 계약

## 고정 아키텍처

Barrel은 `TH-BH-01` 24 V/100 W/ID34/W45 mica band 3개, die는 `TH-DIE-01` Tempco custom 24 V/60 W/Ø6.50×39.50 Type CG cartridge 1개를 쓴다. 공정가열 정격합계는 360 W(15.0 A)다. TH-DIE-01은 HTL lead, OAL, MFR flange를 포함한 승인 도면이 필요하며 일반 3D-printer cartridge 대체를 금지한다. Ø35 stock band를 Ø34 barrel에 느슨하게 쓰거나 PTC를 barrel 주가열에 쓰는 대체는 금지한다.

Zone 중심은 barrel datum B에서 67.5/137.5/212.5 mm이며 band 범위는 B+45–90, 115–160, 190–235 mm다. Band free-state ID는34.10–34.20 mm, clamp의 usable split-closure travel은 최소1.00 mm다. Barrel OD33.97–34.00 mm에 필요한 최악 원주방향 closure는 π(34.20−33.97)=0.723 mm이고 잔여 travel은 최소0.277 mm다. 냉간 체결 뒤 split ±10°를 제외한 8개 등간격 sector에서 0.05 mm feeler가 5 mm 넘게 들어가지 않아야 한다. 이 검사는 수령 후 `NOT_RUN`이며 디지털 closure 계산만 PASS다. T1/T2/T3 bore는 B+95/170/245 mm, Ø3.20 +0.05/0, flat-bottom 깊이5.40 ±0.05이며 보수적 최소 ligament3.345 mm(요구≥3.32)를 유지한다. TH-TC-01은 Tempco MTA1 K/U/Q 맞춤품으로 Ø3.00±0.03, sheath25.40±0.25와 공급자 용접 stop collar를 쓴다. T1–T3 stop5.20±0.05, T4 stop10.00±0.05이며 TH-TCR-01 bridge와 2×M3로 고정한다. 직경 clearance는0.17–0.28 mm다. 승인도면·절연·인발·열응답 수령검사는 HOLD다.

각 100 W band cold resistance는 5.76 Ω ±10%, 60 W cartridge는 Tempco 공개 resistance tolerance -5/+10%를 적용한 9.12–10.56 Ω를 수령 시 20 ±2 °C에서 기록한다. Sheath-to-lead 절연, PE bond, lead strain relief, 실제 외형과 clamp closure를 검사한다. 24 V 저전압이라도 각 channel은 F-H1..F-H4 5 A branch fuse와 40–60 V VDS/10 A continuous thermal-capable MOSFET를 사용한다. 이 branch fuse는 과전류 보호이며 thermal cutoff가 아니다.

`TH-FUSE-01`은 총 3개를 조달한다. `TF-BARREL` 1개와 `TF-DIE` 1개를 저전류 K0 coil safety chain에 직렬로 설치하고, 동일 사양 1개는 교체용 spare로 보관한다. 어느 installed cutoff 하나라도 open되면 K0 coil energy가 제거되어 motor와 네 heater branch 전체가 함께 차단된다. Mega/MOSFET은 이 두 independent cutoff를 우회할 수 없으며 spare를 installed safety element로 계산하지 않는다.

모든 heater 구매와 energization은 사용자 승인 대상이다. 수령검사·절연검사·두 installed thermal cutoff continuity·K0 hard-cut 검증·무부하 단계가 끝나기 전 PSU에 연결하지 않는다.
""",encoding="utf-8")
    with (base/"channel_schedule.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["channel","load","nominal_w","nominal_a_24v","sensor","hard_cut","control","state"])
        w.writerows([
            ("HZ1","TH-BH-01 zone1",100,"4.17","T1 K-type","F-H1 branch fuse + K0 dual thermal-cutoff chain","MOSFET1 low-frequency","HOLD"),
            ("HZ2","TH-BH-01 zone2",100,"4.17","T2 K-type","F-H2 branch fuse + K0 dual thermal-cutoff chain","MOSFET2 low-frequency","HOLD"),
            ("HZ3","TH-BH-01 zone3",100,"4.17","T3 K-type","F-H3 branch fuse + K0 dual thermal-cutoff chain","MOSFET3 low-frequency","HOLD"),
            ("HDIE","TH-DIE-01",60,"2.50","T4 K-type","F-H4 branch fuse + K0 dual thermal-cutoff chain","MOSFET4 low-frequency","HOLD"),
        ])
    print(f"THERMAL_PACKAGE_OK parts={len(rows)} process_heater_w=360 sensors=5")


def main():
    machine_rows = write_machine_fabrication_package()
    drive_rows = write_drive_package(); write_gate1_package(); write_extruder_package(); write_thermal_package()
    print(f"MANUFACTURING_PACKAGE_OK machine_parts={len(machine_rows)} drive={len(drive_rows)} jig_parts={len(gate1_parts())} extruder_parts={len(extruder_rfq_parts())}")


if __name__=="__main__":main()
