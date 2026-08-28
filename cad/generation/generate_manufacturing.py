#!/usr/bin/env python3
"""Generate VE drive, Gate-1 jig and screw/barrel RFQ artifacts."""

from __future__ import annotations

import csv
import json
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
    generic_phase_gear_lamination,
    universal_motor_plate,
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
            f"- revision: `solid-manifold-openmodelica-v0.4`\n"
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
<text x="55" y="620">OD Ø34.00 ±0.05 · bore Ø16.20 +0.02/0 after final hone · radial clearance 0.14–0.16</text>
<text x="55" y="655">feed port 18 axial ×20, near edge 12.0 from rear Datum B · break edge R0.5</text>
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
<text x="55" y="600">breaker seat Ø16.20 +0.05/0 ×3; insert seat Ø12.00 +0.03/0 ×14; heater Ø6.20 H9 thru;</text>
<text x="55" y="630">sensor Ø3.20 +0.05/0 blind12; 2×M4-6H depth8 retainer holes at X8/32; all melt edges R0.3.</text>
<text x="55" y="665">BREAKER 304: Ø15.90 -0.05/0 ×2; 7×Ø2.00 +0.05/0 (six PCD10). INSERT 17-4PH H900:</text>
<text x="55" y="695">Ø11.90 -0.02/0 ×14; Ø3.00 +0.02/0 ×10 land, Ra≤0.4; 4 mm 60° included transition; TIR≤0.02.</text>
<text x="55" y="730">RELIEF 304 t1.5: 32×20; two 10×2.5 webs; 2×Ø4.5 @24; Ø4 bypass. Hot coupon 3–6 MPa.</text>
<text x="55" y="760">GASKET C110 annealed t0.50: OD34 / ID16.20 / 4×Ø4.5 PCD26. Use 4×M4×45 class10.9, 3.0 N·m.</text>
<text x="55" y="795">Leak/relief hot test behind grounded shield only. Analytical relief estimate is screening, not release evidence. FULL PART HOLD.</text>
</svg>\n""",encoding="utf-8")


def write_drive_package():
    base=ROOT/"exports/drive_interface"; base.mkdir(parents=True,exist_ok=True)
    specs=[
        dict(id="DRV-01",name="Universal donor motor plate",shape=universal_motor_plate(),qty=1,material="6 mm SS400 steel",process="laser cut + standard metal angles",critical="180 x140 x6; frame holes 4xØ6.6; slots nominal per DXF; flatness <=0.5; motor-specific adapter carries motor load"),
        dict(id="DRV-02",name="Bolt-on cutter sprocket hub",shape=bolt_on_sprocket_hub(),qty=1,material="S45C",process="turn + keyway + PCD drilling",critical="bore Ø20.2 +0.03/0 after received CUT-05 measurement; 6.2 keyway; 4xØ6.6 PCD36; sprocket register TIR <=0.10"),
        dict(id="DRV-03",name="M3 Z16 phase gear lamination",shape=generic_phase_gear_lamination(),qty=6,material="6 mm S45C",process="waterjet/laser rough + stack dowel/finish",critical="M3 Z16 20 degree; bore Ø20.2 +0.05/0; 2xM4 clearance Ø4.5 + 1xØ3 H7 dowel on PCD30 at 0/120/240 degree; three laminations per gear; stack face >=18"),
    ]
    rows=export_shape_set(specs,base/"parts")
    with (base/"manifest.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["part_id","name","quantity","material","process","x_mm","y_mm","z_mm","release_state"])
        for r in rows:w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"{r['x']:.2f}",f"{r['y']:.2f}",f"{r['z']:.2f}","HOLD_DONOR_AND_GATE1"])
    (base/"interface_contract_ko.md").write_text("""# Interchangeable shredder drive interface — solid-manifold-openmodelica-v0.4

공정 경로와 dual-shaft cutter는 변경하지 않는다. 특정 MY1016Z, KTR coupling, KHK gear의 part number는 요구조건이 아니다.

## 합격 가능한 donor motor

- 18–30 V brushed DC gearmotor, reversible
- cutter 환산 continuous torque >=14 N·m, 3 s peak >=24 N·m
- interface ratio 선택 후 cutter 20–40 rpm continuous, no-load <=80 rpm
- shaft 10–20 mm이며 key, D-flat 또는 clamping hub 사용 가능
- 20 A branch 안에서 실제 current/torque calibration 가능
- S2 60 min 이상 또는 30분 coupon에서 winding/gearcase <=80 °C
- label, 수량 1, 정상 회전, backlash, shaft 치수, 무부하 전류가 기록된 project-lab/donor만 현금 0원 인정

우선순위는 (1) project-lab wheelchair/conveyor geared DC motor, (2) 검증된 24 V scooter/e-bike geared motor, (3) 기존 MY1016Z급 donor다. NEMA17은 full shredder actuator로 합격하지 않는다.

## 기계 interface

`DRV-01` plate에는 motor-specific standard angle/saddle과 `DRV-Axx` donor adapter만 추가한다. Motor torque는 `DRV-F01` replaceable motor-side shear element와 #35 chain의 12T input, 교환 가능한 18T/24T/30T output sprocket을 거쳐 right CUT-05 shaft로 전달한다. `DRV-02`는 cutter-side Ø20 shaft와 PCD36 sprocket blank를 분리하는 output hub이며 sacrificial element가 아니다. Shaft가 다른 donor에는 `DRV-Axx`만 바꾼다. 두 cutter shaft의 counter-rotation/phase는 특정 공급사 대신 M3 Z16, 20°, face>=18 mm steel gear functional specification으로 조달하거나 `DRV-03` 3-lamination/gear를 사용한다. DRV-03 각 lamination은 PCD30의 2x M4 clamp hole과 1x Ø3 H7 dowel hole로 위상을 재현하며, 치면 맞물림만으로 정렬하지 않는다.

Chain efficiency 0.85 screening에서 12T:18T, 12T:24T, 12T:30T의 motor output continuous/3 s capability는 각각 최소 11.0/18.8, 8.3/14.2, 6.6/11.3 N·m여야 한다. Motor speed 30–60/40–80/50–100 rpm이 cutter 20–40 rpm을 만든다. 24 V label power는 150 W 이상을 screening 시작점으로 쓰되 합격은 label watt가 아니라 Gate-1 torque/current/RPM/temperature 결과로 정한다. 후보별 기록표는 `bom/donor_drive_acceptance.csv`와 `donor_measurement_form.csv`다.

14/18/22/34/48 N·m hierarchy는 모두 **cutter-shaft equivalent torque**다. 따라서 `DRV-F01`의 실제 motor-side mechanical setting은 efficiency 0.85에서 12:18=17.25, 12:24=12.94, 12:30=10.35 N·m다. DRV-F01이 작동해도 DRV-02, chain, phase pair의 위상 경로는 유지되어야 한다. Chain guard, 20 A fuse, E-stop/lid/service hard inhibit와 calibrated torque+RPM jam detection을 유지한다. Shear 재료·직경·groove는 Gate-1 quasi-static calibration으로 확정한다. Donor 확인과 Gate-1 전 full quantity 발주 금지다.

## 치수 근거가 있는 reference variant

Parvalux `781096-735901` BRx70-60 24 V + GB12 30:1 PMDC gearmotor를 구매 의존성이 없는 envelope reference로만 둔다. 공식 공개값은 100 rpm, 9.8 N·m S1, 17.2 N·m intermittent, 270 x 81 x 138 mm다. 12T:30T에서 cutter 40 rpm이며 계산상 capability는 충분하지만 가격이 예산을 크게 넘으므로 선정품/BOM/0원 donor가 아니다. Assembly의 red box는 이 공식 overall envelope이며 proprietary body 형상을 가장하지 않는다. Source URL과 확인일은 `reference_variant.json`에 고정한다.
""",encoding="utf-8")
    reference={
        "revision":"solid-manifold-openmodelica-v0.4","manufacturer":"Parvalux","part_number":"781096-735901",
        "model":"BRx70-60 24V 3000RPM - GB12 30:1 Bronze","motor_type":"PMDC right-angle geared motor",
        "published":{"voltage_v":24,"power_w":157,"output_speed_rpm":100,"continuous_torque_nm":9.8,"intermittent_torque_nm":17.2,"overall_envelope_mm":[270,81,138],"gear_ratio":30},
        "machine_interface":{"chain_ratio":"12T:30T","screening_efficiency":0.85,"cutter_speed_rpm":40,"cutter_equivalent_continuous_capability_nm":20.83,"cutter_equivalent_intermittent_capability_nm":36.55,"motor_side_relief_setting_nm":10.35},
        "source_url":"https://www.parvalux.com/product/brx70-60-24v-3000rpm-gb12-301-bronze/",
        "source_checked_date":"2026-08-29","selection_state":"REFERENCE_ONLY_NOT_SELECTED_NOT_IN_BUDGET","purchase_allowed":False,
    }
    (base/"reference_variant.json").write_text(json.dumps(reference,indent=2,ensure_ascii=False)+"\n")
    with (base/"ratio_and_fuse_settings.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["input_teeth","output_teeth","ratio","efficiency","motor_rpm_for_cutter_20_40","minimum_motor_continuous_nm_for_14_cutter_nm","minimum_motor_peak_nm_for_24_cutter_nm","motor_side_electrical_trip_nm_for_18_cutter_nm","motor_side_mechanical_relief_nm_for_22_cutter_nm","status"])
        for output,ratio in ((18,1.5),(24,2.0),(30,2.5)):
            gain=ratio*0.85; w.writerow([12,output,ratio,0.85,f"{20*ratio:.0f}-{40*ratio:.0f}",f"{14/gain:.2f}",f"{24/gain:.2f}",f"{18/gain:.2f}",f"{22/gain:.2f}","GATE1_CALIBRATION_REQUIRED"])
    with (base/"donor_measurement_form.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["candidate_id","manufacturer","model","serial","quantity","condition","label_voltage_v","label_power_w","output_no_load_rpm","shaft_diameter_mm","shaft_form","shaft_length_mm","mount_pattern_mm","shaft_height_mm","overall_l_w_h_mm","no_load_current_a","continuous_current_a","stall_or_peak_current_a","backlash_deg","case_temp_after_30min_c","selected_chain_ratio","motor_side_relief_setting_nm","gate1_result","photo_hash","operator","status"]); w.writerow(["DONOR-","","","",1,"","","","","","key/D-flat/clamp","","","","","","","","","","","","NOT_RUN","","","UNVERIFIED"])


def svg_gate1_hardcut(path):
    """Human-readable hardwired motor-energy cut schematic for Gate-1."""
    path.write_text("""<svg xmlns="http://www.w3.org/2000/svg" width="1189" height="841" viewBox="0 0 1189 841">
<style>text{font-family:'Noto Sans CJK KR',sans-serif;font-size:18px}.t{font-size:27px;font-weight:bold}.w{stroke:#17465a;stroke-width:4;fill:none}.c{fill:#eef4f6;stroke:#111;stroke-width:2}.n{font-size:15px}.danger{fill:#a12c2c}</style>
<text x="45" y="48" class="t">Gate-1 24 V hardwired motor-energy cut — solid-manifold-openmodelica-v0.4</text>
<text x="45" y="83" class="danger">Mega output alone cannot energize K1. S0/S1 opening drops K0 and requires manual START reset.</text>
<rect x="55" y="145" width="120" height="70" class="c"/><text x="76" y="185">24 V PSU</text>
<path d="M175 170H235" class="w"/><rect x="235" y="145" width="95" height="50" class="c"/><text x="260" y="178">F1 20 A</text>
<path d="M330 170H390" class="w"/><rect x="390" y="135" width="130" height="70" class="c"/><text x="420" y="175">K1 NO</text><text x="410" y="195" class="n">DC >=30 V/25 A</text>
<path d="M520 170H580" class="w"/><rect x="580" y="135" width="145" height="70" class="c"/><text x="604" y="166">BTS7960</text><text x="596" y="193" class="n">reversing driver</text>
<path d="M725 170H785" class="w"/><rect x="785" y="135" width="145" height="70" class="c"/><text x="812" y="165">M1 donor</text><text x="801" y="193" class="n">24 V geared DC</text>
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
    envelope=export_assembly(gate1_assembly(),base,"gate1_assembly")
    with (base/"jig_manifest.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["part_id","name","quantity","material","process","x_mm","y_mm","z_mm","critical","release_state"])
        for r in rows:
            w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"{r['x']:.2f}",f"{r['y']:.2f}",f"{r['z']:.2f}",r["critical"],"HOLD_USER_APPROVAL"])
    print_rows=[]
    for r in rows:
        if r["class_"]!="print": continue
        mass=r["shape"].Volume*1.24/1000*r["qty"]
        print_rows.append((r["id"],r["qty"],r["material"],"0.24 mm",3,"20%", "upright/end-face", "no; bridge only",f"{mass:.1f}"))
    with (base/"print_manifest.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["part_id","qty","material","layer_height","walls","infill","orientation","support","estimated_mass_g"])
        w.writerows(print_rows)
    total_print=sum(float(r[-1]) for r in print_rows)
    (base/"total_material_report.md").write_text(
        f"# Gate-1 jig 출력물 집계\n\n총 예상 PLA 질량은 `{total_print:.1f} g`이며 final-machine 출력 package와 분리한 시험 jig 집계다. "
        f"18,000 KRW/kg 기준 재료비는 약 `{total_print*18:.0f} KRW`다. 모든 부품은 각 축 210 mm 이하다.\n",encoding="utf-8")
    with (base/"bom.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["item_id","item","qty","source","planning_cash_krw","budget_bucket","status","reuse_after_test","notes"])
        data=[
            ("CUT-01","CUT-01 coupon disc",2,"exports/cnc/CUT-01",4000,"CNC-01","COUPON_RFQ_ALLOWED","yes","D2/SKD11 candidate; remaining full stack is HOLD"),
            ("CUT-03","CUT-03 side plate",2,"exports/cnc/CUT-03",7000,"CNC-02","RFQ_HOLD","yes","42 H7 bearing seats match-machined"),
            ("CUT-05","CUT-05 shaft",2,"exports/cnc/CUT-05",11000,"CNC-03","RFQ_HOLD","yes","final-machine shaft; received inspection required"),
            ("CUT-04","CUT-04 5 mm screen coupon",1,"exports/cnc/CUT-04",5000,"CNC-04","COUPON_RFQ_ALLOWED","yes","3 mm 304; actual clearance >=1.9 mm"),
            ("BRG-6004","6004-2RS bearing",4,"project-lab/donor or HW-ALLOW",0,"HW-ALLOW","VERIFY_INVENTORY","yes","designation/play/corrosion; buy cost must remain inside bucket"),
            ("DRV-03","M3 Z16 phase gear lamination",6,"exports/drive_interface",6000,"SH-INTERFACE","COUPON_RFQ_ALLOWED","yes","3 laminations/gear; 2xM4 + 1x3H7 dowel PCD30"),
            ("G1J-01","Reusable base plate",1,"donor plate; drawing supplied",0,"HW-ALLOW","VERIFY_INVENTORY","jig","320x240x8, flatness <=0.30; no zero-cash claim until verified"),
            ("G1J-02","250 mm torque arm",1,"exports/jigs/gate1/parts",0,"CNC-02","RFQ_HOLD","jig","nest with CNC-02 flat pack; no separate budget addition"),
            ("G1J-03","Front/rear polycarbonate panels",2,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","3 mm PC, never acrylic; bucket includes all G1J-03..06 sheet"),
            ("G1J-04","Left polycarbonate panel",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","3 mm PC"),
            ("G1J-05","Right slotted polycarbonate panel",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","open edge slot and baffle required"),
            ("G1J-06","Torque-slot offset baffle",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","blocks fragment line of sight"),
            ("G1J-07","20x20x2 metal guard upright L180",4,"standard angle stock",0,"HW-ALLOW","BUY_HOLD","jig","primary fragment-retention load path"),
            ("G1J-08","20x20x2 steel screen rail L150",2,"standard angle stock",0,"HW-ALLOW","BUY_HOLD","jig","shimmed/removable"),
            ("G1J-09","Interlock metal bracket",1,"exports/jigs/gate1/parts",0,"SAFE-ALLOW","BUY_HOLD","jig","switch model-specific overtravel set at assembly"),
            ("G1J-10","40x40x4 CUT-03 foot L50",4,"standard angle stock",0,"HW-ALLOW","BUY_HOLD","jig","metal plate-to-base load path"),
            ("MET-01","0-200 N force gauge or 100 kg load cell/HX711",1,"project-lab or buy allowance",7500,"GATE1-METROLOGY","CALIBRATION_HOLD","jig","accuracy <=2%; M8 clevis and independent safety tether"),
            ("G1J-P01..03","Printed chute/tray/edge trim",1,"exports/jigs/gate1/parts",4500,"GATE1-PRINT","PRINT_HOLD","jig","234 g estimate; cold low-load only"),
            ("SAFE-K0/K1","Manual-reset control relay and 24 V motor power relay",1,"project-lab or SAFE-ALLOW",0,"SAFE-ALLOW","VERIFY_RATING","yes","K1 DC breaking rating >=30 V/25 A; K0 has seal-in auxiliary contact"),
            ("SAFE-S0/S1","Latching E-stop NC + positive-opening guard switch NC",1,"project-lab or SAFE-ALLOW",0,"SAFE-ALLOW","VERIFY_RATING","yes","series hard inhibit; Mega cannot bypass"),
            ("SAFE-F1/F2","20 A motor branch fuse + 2 A control fuse",1,"project-lab or fuse allowance",0,"FUSE-ALLOW","VERIFY_RATING","yes","close to 24 V source"),
            ("HW-SET","Fastener, shim, collar and clevis set",1,"fastener_schedule.csv",0,"HW-ALLOW","BUY_HOLD","yes","all quantities and torques in schedule; bucket cap retained"),
        ]
        w.writerows(data)
    with (base/"fastener_schedule.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["joint_id","mating_parts","fastener","qty","washer_nut","nominal_torque_Nm","locking","access_tool","inspection"])
        w.writerows([
            ("FST-01","G1J-01 to test table","M8 x25 class 8.8 hex",4,"M8 flat washer + fixture T-nut","18","mechanical prevailing nut/T-slot","13 mm socket","base flatness <=0.30 mm after torque"),
            ("FST-02","G1J-10 to G1J-01","M6 x20 class 8.8 hex",8,"M6 washer + nyloc","9","nyloc","10 mm socket","no foot rocking; witness mark"),
            ("FST-03","CUT-03 to four G1J-10","M6 x20 class 8.8 hex",8,"M6 washer + nyloc","9","nyloc","10 mm socket","plate perpendicularity <=0.20/125"),
            ("FST-04","G1J-08 screen rails to CUT-03/feet","M5 x16 class 8.8 hex",4,"M5 washer + nyloc","5","nyloc","8 mm socket","screen minimum cutter clearance >=1.9 mm"),
            ("FST-05","CUT-04 to G1J-08 rails","M5 x12 thumb screw",4,"M5 large washer + captive nut","3","captive nut","hand/8 mm","screen cannot lift; tool removal only after lockout"),
            ("FST-06","DRV-03 three-lamination stack per gear","M4 x22 class 10.9 SHCS",4,"M4 washer + all-metal locknut","3","all-metal locknut","3 mm hex + 7 mm spanner","2 bolts/gear; dowel seated; stack face 18 mm"),
            ("FST-07","DRV-03 registration per gear","3 x18 hardened dowel h6",2,"press/slip fit per drawing","N/A","3 H7 lamination holes","arbor press","one dowel/gear; no tooth-based registration"),
            ("FST-08","G1J-07 upright to G1J-01","M4 x16 class 8.8 hex",8,"M4 washer + nyloc","3","nyloc","7 mm socket","upright verticality <=0.5/180"),
            ("FST-09","G1J-03/04/05 PC panel to G1J-07","M4 x16 pan-head",24,"M4 nylon washer + nyloc","1.2","nyloc; no threadlocker on PC","PH2 + 7 mm","panel retained, no crazing; 0.5 mm compliant washer compression"),
            ("FST-10","G1J-06 baffle to G1J-05/upright","M4 x20 pan-head + 10 mm spacer",4,"nylon washer + nyloc","1.2","nyloc","PH2 + 7 mm",">=10 mm offset and no line-of-sight to cutter"),
            ("FST-11","G1J-09 switch bracket to upright","M4 x16 class 8.8",2,"washer + nyloc","3","nyloc","3 mm hex","positive opening and specified overtravel"),
            ("FST-12","received guard switch to G1J-09","M4 x20 pan-head",2,"washer + nyloc","1.2","nyloc","PH2 + 7 mm","terminal/actuator not preloaded beyond rating"),
            ("FST-13","G1J-P01 feed chute to guard","M4 x16 pan-head",4,"large washer + nyloc","1.2","nyloc","PH2 + 7 mm","anti-reach baffle intact; push-stick-only path"),
            ("FST-14","G1J-02 force gauge clevis","M8 shoulder bolt or clevis pin",1,"two retainers + independent tether","hand snug","double retention","pliers/13 mm","line of pull <=2 degree; tether slack under normal load"),
        ])
    with (base/"wiring_bom.csv").open("w",newline="") as f:
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
            ("CS1",1,"galvanically isolated 50 A current sensor","existing ACS758-class candidate","SH-DRIVE","zero/span calibration; never sole safety cut","HOLD"),
            ("TB1",1,"touch-safe terminal block >=32 VDC/30 A","project-lab then low-cost buy","HW-ALLOW","rating and screw retention","HOLD"),
            ("WIRE-P",1,"red/black >=2.5 mm2 copper motor harness, 105 C","project-lab then low-cost buy","HW-ALLOW","crimp pull test and voltage drop","HOLD"),
            ("WIRE-C",1,"0.5-0.75 mm2 control wire, ferrules, labels","project-lab then low-cost buy","HW-ALLOW","point-to-point continuity","HOLD"),
            ("PE",1,"green/yellow >=2.5 mm2 chassis/guard bond with star washers","project-lab then low-cost buy","HW-ALLOW","<0.1 ohm bond at accessible metal","HOLD"),
        ])
    svg_gate1_hardcut(base/"wiring_24v_hardcut.svg")
    with (base/"specimen_schedule.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["material","specimen_type","nominal_thickness_or_fold","width_mm","length_mm","replicates","conditioning","id_pattern"])
        w.writerows([
            ("PLA","printed wall","1.2 mm",25,80,5,"23+/-2 C, dry surface","PLA12-01..05"),
            ("PLA","printed wall","2.0 mm",25,80,5,"23+/-2 C, dry surface","PLA20-01..05"),
            ("PLA","printed wall","3.0 mm",25,80,5,"23+/-2 C, dry surface","PLA30-01..05"),
            ("PET","bottle body single layer","measured actual",25,80,5,"label/cap/adhesive removed, dry surface","PET-B-01..05"),
            ("PET","four-layer folded seam","4 layers; measured total",25,80,5,"label/cap/adhesive removed, dry surface","PET-F-01..05"),
        ])
    with (base/"calibration_log_template.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["date_time","instrument_id","serial","reference_mass_kg","reference_force_N","indicated_force_N","error_percent","ambient_C","operator","pass_fail","evidence_path"])
        for mass,force in ((0,0),(5,49.05),(10,98.10),(15,147.15)):
            w.writerow(["","","",mass,f"{force:.2f}","","","","","",""])
    with (base/"preflight_inspection_template.csv").open("w",newline="") as f:
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
        )
        for item_id,inspection,method,acceptance,unit in rows:
            w.writerow({"item_id":item_id,"inspection":inspection,"method":method,"acceptance":acceptance,"unit":unit})
    with (base/"gate1_results_template.csv").open("w",newline="") as f:
        fields=["date_time","operator","reviewer","material","specimen_id","actual_thickness_or_fold_mm","trial","peak_N","radius_m","calculated_peak_Nm","force_angle_deg","failure_mode","permanent_damage","observation","photo_video_path","raw_log_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        groups=(("PLA","PLA12",5),("PLA","PLA20",5),("PLA","PLA30",5),("PET","PET-B",5),("PET","PET-F",5))
        for material,prefix,count in groups:
            for trial in range(1,count+1):
                w.writerow({"material":material,"specimen_id":f"{prefix}-{trial:02d}","trial":trial,"radius_m":"0.2500"})
    with (base/"drive_calibration_template.csv").open("w",newline="") as f:
        fields=["date_time","operator","reviewer","donor_id","calibration_type","point","input_teeth","output_teeth","motor_rpm","cutter_rpm","motor_current_A","no_load_current_A","force_N","arm_radius_m","cutter_torque_Nm","current_above_no_load_A","cutter_torque_per_amp_Nm_A","derived_efficiency","motor_case_C","relief_released","permanent_phase_damage","evidence_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        w.writerow({"calibration_type":"NO_LOAD","point":1,"input_teeth":12,"arm_radius_m":"0.2500"})
        for point,target in enumerate((4,8,12,16,18),1):
            w.writerow({"calibration_type":"TORQUE_CURRENT","point":point,"input_teeth":12,"arm_radius_m":"0.2500","cutter_torque_Nm":target})
        for point in range(1,4):
            w.writerow({"calibration_type":"MECH_RELIEF","point":point,"input_teeth":12,"arm_radius_m":"0.2500","cutter_torque_Nm":22})
    with (base/"jam_recovery_results_template.csv").open("w",newline="") as f:
        fields=["date_time","operator","reviewer","material","trial","command_rpm","pre_jam_rpm","trip_cutter_torque_Nm","overload_duration_ms","rpm_drop_percent","rpm_drop_duration_ms","reverse_start_ms","reverse_duration_ms","retry_count","jam_cleared","latched_fault_after_third_failure","guard_lockout_required_for_reset","motor_case_C","permanent_damage","photo_video_path","raw_log_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for material,command_rpm in (("PLA",32),("PET",24)):
            for trial in range(1,4):
                w.writerow({"material":material,"trial":trial,"command_rpm":command_rpm,"trip_cutter_torque_Nm":18})
    with (base/"chip_size_results_template.csv").open("w",newline="") as f:
        fields=["date_time","operator","reviewer","material","batch_id","screen_hole_mm","screen_dwell_s","oversize_recirc_count","input_mass_g","mass_3_6_g","mass_6_20_g","mass_gt20_g","fines_lt3_g","recovered_total_g","fraction_3_6_percent","fraction_6_20_percent","fraction_gt20_percent","fines_percent","recovery_percent","longest_strip_mm","photo_path","scale_log_path","pass_fail"]
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader()
        for material in ("PLA","PET"):
            w.writerow({"material":material,"batch_id":f"{material}-CHIP-01","screen_hole_mm":5,"screen_dwell_s":5,"oversize_recirc_count":1})
    with (base/"evidence_manifest_template.csv").open("w",newline="") as f:
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

- revision: `solid-manifold-openmodelica-v0.4`
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

`PASS`는 `test_procedure_ko.md`의 모든 기준, traceable calibration과 원시 증거가 동시에 충족될 때만 parent Codex가 별도 commit에서 기록한다. 이 template의 존재는 release가 아니다. `PASS`가 아닌 상태에서는 full cutter stack, full screw/barrel 발주와 `main` 승격을 계속 금지한다.
""",encoding="utf-8")
    (base/"assembly_ko.md").write_text(f"""# Gate-1 cutter coupon jig 조립도

- revision: `solid-manifold-openmodelica-v0.4`
- nominal assembly envelope: `{envelope[0]} x {envelope[1]} x {envelope[2]} mm`
- 목적: CUT-01 두 장만 사용해 PLA/PET peak torque, jam recovery와 chip-size fraction을 측정한다.

## 조립 순서

1. G1J-01을 고정 table에 M8 네 점으로 체결하고 0.3 mm 이내 평면을 확인한다.
2. G1J-10 metal foot 네 개에 최종기용 CUT-03 두 장을 체결한 뒤 6004 bearing 네 개를 조립한다. Bearing은 outer ring만 눌러 삽입한다.
3. CUT-05 두 축을 넣고 CUT-01 coupon을 축당 한 장만 6.5 mm offset으로 장착한다. 0.25–0.50 mm metal shim으로 axial gap을 맞춘다.
4. G1J-08 steel angle rail 두 개에 CUT-04 5 mm screen coupon을 captive fastener로 고정하고, cutter tip 아래 nominal 3.0 mm/실제 최소 clearance 1.9 mm 이상을 shim으로 맞춘다.
5. DRV-03 lamination을 gear당 3장, 2x M4 clamp bolt과 1x Ø3 h6 dowel로 조립하고 hand rotation 20회에서 간섭이 없어야 한다.
6. G1J-02 torque arm 중심에서 force hole까지 `250.0 ±0.5 mm`를 실측한다. Calibrated handheld force gauge를 M8 clevis에 연결하고 독립 safety tether를 단다. 힘 방향과 arm 운동평면 편차는 2° 이하다.
7. G1J-07 metal upright 4개를 base에 체결한 뒤 G1J-03/04/05 3 mm polycarbonate panel을 nylon washer로 유지한다. G1J-06 offset baffle은 right-panel slot에서 10 mm 이상 떨어져 fragment 직선경로를 막아야 한다. G1J-P03은 edge trim일 뿐 panel 지지구가 아니다.
8. G1J-09에 positive-opening S1을 설치하고 `wiring_24v_hardcut.svg`대로 S0/S1→K0→K1 manual-reset hard cut을 배선한다. S0/S1 개방 후 START 없이 자동 재가동하면 FAIL이다.
9. `fastener_schedule.csv`의 torque/witness mark, PE bond <0.1 ohm, panel crack 0을 확인한다.
10. Manual torque test 뒤에만 합격 donor drive를 DRV-01/#35 chain interface로 연결한다.

고하중 경로는 cutter → metal shaft → 6004 → CUT-03 → G1J-01 → table이다. 출력 chute/tray/corner는 하중경로가 아니다.
""",encoding="utf-8")
    (base/"test_procedure_ko.md").write_text("""# Gate-1 CUT-01 coupon 시험 절차와 합격기준

## 시험 전 부품과 계측

- CUT-01 coupon 2개와 CUT-04 5 mm screen coupon 1개만 사용한다. Full 12-disc stack과 screw/barrel 발주는 금지한다.
- PLA wall 1.2/2.0/3.0 mm: 25 x 80 mm, 각 5개.
- PET body single layer와 four-layer folded seam: 25 x 80 mm, 각 5개. Cap/neck/label/adhesive 제거.
- 0–200 N calibrated handheld force gauge(또는 load cell), M8 clevis + 독립 safety tether, arm radius 250.0 mm, driven-shaft Hall RPM, 50 A current sensor, 3/6/20 mm sieve, 0.1 g scale, video.
- Force gauge는 0/49.05/98.10/147.15 N에서 오차 <=2%, arm radius 오차 <=0.5 mm여야 한다.

## A. Lockout와 dry mechanical

1. Main disconnect OFF/0 V, shaft block, guard open 상태에서 fastener torque와 shim을 기록한다.
2. Hand rotation 20회: cutter/plate/gear/screen 접촉 0, shaft TIR <=0.10 mm, phase error <=1.0°.
3. Polycarbonate guard, S0 E-stop과 S1 positive-opening switch가 K0/K1을 drop하여 motor bus energy를 실제 제거하는지 각각 continuity/voltage test한다. 전원 복귀 후 S2 START 없이 K1이 자동 재투입되면 FAIL이다.

## B. Quasi-static 절단토크

1. Coupon을 push stick으로 capture point에 놓고 guard를 닫는다.
2. Force gauge를 arm 운동평면에서 각도 편차 2° 이하로 유지하고 3–5 rpm 상당으로 당겨 peak force `F_peak`를 기록한다. `T_peak=F_peak x r`, `r=0.2500 m`다.
3. 각 specimen 5회 후 median, maximum, failure mode(capture/buckle/shear/slip)를 기록한다.
4. PLA 세 두께와 PET body의 max <=14 N·m, folded seam max <=24 N·m이어야 한다. 24 N·m 전에 shaft/gear/plate 영구변형, tooth crack 또는 key damage가 있으면 FAIL이다.

## C. Motor/current와 jam recovery

1. 합격한 donor motor만 연결하고 PLA 32 rpm/PET 24 rpm에서 no-load current/RPM, arm/load-cell torque 대비 current-to-torque slope, 실제 sprocket ratio와 효율을 기록한다. `verified` calibration record 없이는 powered cutter를 시작하지 않는다.
2. 14/18/22/34/48 N·m는 모두 cutter-shaft reference다. Motor-side `DRV-F01`을 구동모터 분리 상태에서 quasi-static calibration한다. 효율 0.85 기준 시작 setting은 12:18 = 17.25 N·m, 12:24 = 12.94 N·m, 12:30 = 10.35 N·m이며, 실제 ratio/효율/측정 불확도를 기록해 22 N·m cutter-equivalent에서 분리되도록 보정한다. DRV-02·chain·phase pair는 분리 또는 영구변형되면 FAIL이다.
3. Controlled jam을 각 재질 3회 만든다. Calibrated cutter torque 18 N·m에서 PLA 650 ms/PET 850 ms 또는 command 대비 RPM 35% drop/500 ms에서 reverse가 시작돼야 한다. 고정 A값은 donor 공통 torque 기준으로 사용하지 않는다.
4. Reverse는 PLA 800 ms/PET 1100 ms, 최대 3회다. 세 번째 실패 뒤 enable=0과 latched fault가 유지돼야 한다.
5. Guard를 열고 lockout/jam 제거 확인 없이는 reset되면 FAIL이다.

## D. Chip-size

1. CUT-04 5 mm screen과 동일 5 s screen dwell, oversize 재투입 1회 이하로 재질별 최소 30 g을 시험하고 chip을 20/6/3 mm sieve로 분류한다.
2. `3–6 mm`, `6–20 mm`, `>20 mm long strip`, `<3 mm fines` 질량과 총 회수율을 기록한다.
3. 초기 합격: 3–6 mm >=55%, >20 mm PET strip <=10%, fines <=15%, 회수율 >=95%. 미달이면 CUT-01 전체 수량을 발주하지 않고 hook/screen coupon만 수정한다.

## 기록과 release

`preflight_inspection_template.csv`, `calibration_log_template.csv`, `drive_calibration_template.csv`, `gate1_results_template.csv`, `jam_recovery_results_template.csv`, `chip_size_results_template.csv`, `evidence_manifest_template.csv`를 각각 작성한다. 하나의 specimen 행에 서로 다른 시험을 합쳐 쓰지 않는다. Gate-1 PASS는 실제 서명된 raw CSV, calibration, 사진/영상 경로와 `gate1_release_record_ko.md`의 hash가 있어야 하며 simulation 값으로 대체할 수 없다.
""",encoding="utf-8")


def write_extruder_package():
    base=ROOT/"exports/cnc/extruder"; (base/"parts").mkdir(parents=True,exist_ok=True)
    rows=export_shape_set(extruder_rfq_parts(),base/"parts")
    with (base/"rfq_manifest.csv").open("w",newline="") as f:
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
    with (base/"screw_profile.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["zone","z_start_mm","z_end_mm","length_D","root_diameter_mm","pitch_mm","land_mm"])
        w.writerows([("feed",0,128,8,10.88,16,1.60),("compression",128,192,4,"10.88_to_14.08",16,1.60),("meter",192,256,4,14.08,16,1.60)])
    with (base/"inspection_report_template.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["part_id","serial_or_lot","characteristic","station_mm","direction","lower_limit_mm","upper_limit_mm","measured","instrument_id","temperature_C","pass_fail","certificate_or_trace"])
        w.writerows([
            ("EX-CPN-SCR","","flight_OD",24,"X/Y",15.90,15.92,"","",20,"",""),
            ("EX-CPN-SCR","","pitch","0-48","axial",15.97,16.03,"","",20,"",""),
            ("EX-CPN-SCR","","land","three flights","normal",1.55,1.65,"","",20,"",""),
            ("EX-CPN-BAR","","bore_ID",20,"X/Y",16.20,16.22,"","",20,"",""),
            ("EX-CPN-BAR","","bore_ID",40,"X/Y",16.20,16.22,"","",20,"",""),
            ("EX-CPN-SCR/BAR","","diametral_clearance","matched min/max","derived",0.28,0.32,"","",20,"",""),
            ("EX-CPN-SCR/BAR","","surface_hardness","each coupon","HV0.3",900,1100,"","",20,"",""),
            ("EX-CPN-SCR/BAR","","effective_case_depth","each coupon","mm",0.30,0.50,"","",20,"",""),
            ("EX-CPN-SCR","","flight_OD_Ra","one trace","um",0,0.8,"","",20,"",""),
            ("EX-CPN-BAR","","bore_Ra","one trace","um",0.4,0.8,"","",20,"",""),
            ("EX-DIE-01","","barrel_face_flatness","entire face","mm",0,0.03,"","",20,"",""),
            ("EX-DIE-01","","melt_channel_ID","horizontal/vertical","X/Z",8.00,8.10,"","",20,"",""),
            ("EX-DIE-01","","insert_seat_ID","14 deep","Z",12.00,12.03,"","",20,"",""),
            ("EX-DIE-03","","orifice_ID","10 mm land","Z",3.00,3.02,"","",20,"",""),
            ("EX-DIE-03","","orifice_concentricity","to OD","TIR",0,0.02,"","",20,"",""),
            ("EX-DIE-04","","relief_open_pressure","three coupons","MPa",3.0,6.0,"","",20,"","physical coupon required"),
        ])
    with (base/"supplier_deviation_template.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["item","drawing_requirement","supplier_yes_no","proposed_deviation","price_effect_krw","lead_time_effect_days","customer_disposition"])
        for item in ("material/certificate","QT hardness","nitriding/case certificate","pitch-land-root-OD","TIR/concentricity","barrel final hone","matched clearance","die intersecting-channel deburr","die insert land/concentricity","relief coupon price/lead time","inspection reports","coupon price/lead time","full-part price/lead time"):
            w.writerow([item,"see controlling drawing/audit","","","","","HOLD"])
    (base/"manufacturing_audit_ko.md").write_text("""# 16 mm x 16 L/D screw/barrel 제조성 audit — RFQ 기준

## Controlling geometry

STEP은 3D 견적/간섭 기준, SVG와 본 문서는 치수·GD&T 기준이다. STL/DXF는 CAM reference이며 공차를 대체하지 않는다. 공급사는 임의로 clearance나 heat treatment를 변경하지 않는다.

- 모든 치수는 mm, 표면조도는 Ra µm, 별도 표기 없은 선형치수 공차는 ±0.10 mm, 각도는 ±0.5°다.
- 재료는 SCM440 KS D3867/JIS G4105 또는 동등 chemical/mechanical certificate를 제출한다. Supplier stock allowance는 임의이지만 추천 rough blank는 screw Ø22 x330, barrel solid/seamless Ø42 x295다.
- 임의 대체재·공정·공차 이탈은 deviation list에 써서 회신하며 무응답은 수락으로 간주하지 않는다.

## EX-SCR-01 screw

- SCM440, normalized blank → rough turn → QT 28–32 HRC → centres 유지.
- Total 316.0 ±0.10. Rear drive 0–35, thrust journal 35–55, neck 55–60, active 60–316. Active 256.0; single-start RH; pitch 16.00 ±0.03; flight land 1.60 ±0.05. Flight은 두 active-section end plane과 만나며 end burr R0.2 max, undercut·weld build-up은 금지한다.
- Zone 8D/4D/4D. Root Ø10.88 feed, linear compression, Ø14.08 meter. Flight OD Ø15.92 -0.02/0.
- Drive Ø12 h6 x35 with KS/DIN 4 x4 key, shaft keyseat 4 P9 wide x2.5 +0.10/0 deep; thrust journal Ø15 h6 x20; neck root Ø10.88 x5. Datum A는 Ø12/Ø15 journal의 common axis이며 shoulder/end face는 A에 직각도 0.03. Flight start angle은 active start에서 key centre plane 기준 0° ±5°.
- 4-axis flight mill leaving 0.15 mm grind/polish allowance. Root/flank Ra≤1.6 µm, flight OD Ra≤0.8 µm.
- Gas nitride 0.30–0.50 mm effective case, surface 900–1100 HV0.3; mask drive/thrust journals and keyseat. Final flight-OD grind between retained centres. Nitriding distortion 후 journal h6/TIR을 최종 확인한다.
- Flight OD TIR ≤0.05 over active 256; drive-to-flight concentricity ≤0.03; straightness ≤0.05/256. No weld repair.

## EX-BAR-01 barrel

- SCM440 solid/seamless blank, QT 28–32 HRC. OD Ø34.00 ±0.05, length 280.00 ±0.05. Rear face=Datum B, front face=Datum C, final bore axis=Datum D. Assembly에서 B는 screw active start와 일치하고 screw tip은 C 뒤 24.0 ±0.2에 위치한다.
- Bore after final hone Ø16.20 +0.02/0, Ra≤0.4–0.8 µm. Bore straightness ≤0.05/256 and concentricity to OD/register ≤0.05.
- Feed opening은 축방향 18.00 ±0.10 x chord width 20.00 ±0.10, rear edge B+12.00 ±0.10. Port centre plane을 전면 bolt pattern의 0° 각도 기준으로 삼는다. Bore-intersection edge R0.5 ±0.2; screw flight 위 sharp edge 금지.
- Front die interface는 4x M4 x0.7-6H, full thread depth 8 minimum, tap-drill depth 11 minimum, PCD26.00 ±0.05 at 45/135/225/315° ±0.2° from feed-port centre plane이다. Ø3.3 tap drill 기준 nominal outer ligament 2.35 mm, bore-side ligament 3.25 mm이고 M4 major envelope 기준으로도 각각 2.0/2.9 mm 이상이다. 나사·counterbore가 OD 또는 bore로 breakthrough하면 FAIL이다. B/C faces은 D에 직각도 0.03; OD concentricity to D ≤0.05.
- Rough turn/deep drill → 600–650 °C stress relieve(재료 공급사 표준 cycle, certificate 기록) → datum-face/OD finish → semi-finish ream/hone leaving 0.05–0.08 mm on diameter → feed port/thread machine → gas nitride 0.30–0.50 mm, ≥900 HV0.3 → final hone. Effective case after final hone is ≥0.25 mm.
- Report bore at 20/140/260 mm and roundness ≤0.02 at each station. Front/rear face perpendicularity 0.03 to bore axis.

## Matched clearance and inspection

Specified drawing-limit diametral clearance is 0.28–0.32 mm and radial clearance is 0.14–0.16 mm. Supplier는 20 ±2 °C에서 screw OD를 active z=20/140/240, barrel ID를 B+20/140/260의 서로 직교하는 2개 방향으로 측정하고 최소/최대 clearance가 범위 안인 pair만 표식한다. Air/bore-gauge report, hardness/case-depth certificate, material certificate, Ra trace, pitch check과 TIR inspection sheet은 RFQ deliverable이다.

## DFM decision

SCM440 was selected over stainless for local availability, machinability and nitriding cost. PET-temperature metal compatibility is adequate for a research coupon, but corrosion/wear life is not certified. `EX-CPN-SCR` 3-pitch와 `EX-CPN-BAR` 60 mm process coupon만 먼저 견적·가공할 수 있다. Coupon의 치수·경도·case depth·Ra가 본 도면을 만족하고 공급사 DFM이 닫힌 뒤에도 Gate-3 cold proof 전 full screw/barrel 발주는 HOLD다. No physical result is claimed here.

Coupon controlling dimensions: EX-CPN-SCR L48.00 ±0.05, three RH pitches 16.00 ±0.03, OD/root/land와 열처리는 EX-SCR-01 feed zone과 동일하며 journal은 없다. EX-CPN-BAR L60.00 ±0.05, OD Ø34.00 ±0.05, final ID Ø16.20 +0.02/0, bore Ra/case는 EX-BAR-01과 동일하다. 두 coupon의 ends는 axis에 0.03 이내 수직이다. Coupon은 matched pair로 표식하고 실측 diametral clearance 0.28–0.32 mm여야 한다.

## EX-DIE connected open-die assembly

`EX-DIE-01`은 barrel 전면에 4×M4×45 class 10.9 bolt와 `EX-DIE-05` annealed copper gasket로 체결되는 40×40×48 SCM440 body다. Ø8 수평 유로와 Ø8 수직 유로는 X20/Z0에서 실제로 교차하며, 공급사는 교차부를 borescope로 확인하고 burr·step을 R0.3 이하로 제거한다. Barrel-side에는 Ø15.90×2 `EX-DIE-02` seven-hole 304 breaker가 Ø16.20×3 seat에 갇힌다. Bottom에는 OD Ø11.90×14 `EX-DIE-03` 17-4PH H900 insert가 Ø12.00×14 seat에 들어가고 Ø3.00×10 land와 4 mm conical transition으로 open discharge한다. 직접 hot path에 polymer는 없다.

Body sealing face flatness는 0.03, melt channel Ø8 H9, insert seat Ø12.00 +0.03/0, breaker seat Ø16.20 +0.05/0이다. Heater bore Ø6.20 H9 through와 sensor bore Ø3.20 +0.05/0 blind12는 유로와 bolt를 관통하지 않는다. Body는 6-face datum machining → intersecting drill/ream → stress relieve → final seat/face → gas nitride → sealing face lap 순서다. Channel/seat에는 weld repair와 plating을 금지한다.

`EX-DIE-04`는 304 stainless t1.5의 교환식 sacrificial retainer다. 두 10 mm wide ×2.5 mm long web, 265 °C 보수 항복강도 150 MPa와 Ø11.9 insert에서 Ø3 orifice를 뺀 투영면적을 쓴 단순 탄성 항복 screening은 약 4.32 MPa이며 normal 3 MPa와 motor-trip equivalent 6 MPa 사이를 겨냥한다. 이는 release 값이 아니다. 동일 lot coupon 3개를 shielded heated hydraulic fixture에서 265 °C 조건으로 시험해 최초 영구변형/우회 개방이 3–6 MPa이고 fragment/ejection이 없을 때만 사용한다. Retainer는 insert를 포획한 채 우회 유로를 열어야 하며, grounded metal shield와 remote first-hot-test 없이는 가열하지 않는다. Full die assembly 역시 process coupon, relief coupon 및 Gate-3 전 `HOLD_PROCESS_COUPON_AND_GATE3`다.
""",encoding="utf-8")
    (base/"supplier_rfq_checklist_ko.md").write_text("""# 공급사 RFQ 응답 checklist

공급사는 가격만 답하지 말고 아래를 yes/no/deviation으로 회신한다.

1. SCM440 mill certificate와 QT 28–32 HRC 제공 가능 여부.
2. Screw 316/256 mm, pitch/land/root/OD와 Ø12 h6 keyseat, Ø15 h6 journal 가공 가능 여부.
3. Flight OD TIR 0.05/256, concentricity 0.03, Ra 0.8 검사 가능 여부.
4. Barrel Ø16.20 +0.02/0 final hone, three-station ID/roundness와 Ra report 가능 여부.
5. Front 4×M4-6H depth8/PCD26 가공 후 OD/bore breakthrough가 없고 major-envelope ligament outer 2.0 mm, bore-side 2.9 mm 이상인지 확인.
6. Gas nitride case/surface hardness certificate와 barrel final-hone 후 effective case ≥0.25 mm 가능 여부.
7. Drawing-limit radial clearance 0.14–0.16 matched measurement 가능 여부.
8. EX-CPN-SCR/EX-CPN-BAR coupon 단가·납기와 full part 단가·납기를 분리 기재.
9. 모든 deviation과 대체재를 발주 전 명시. 무응답 항목은 수락으로 간주하지 않는다.
10. EX-DIE-01 intersecting Ø8 channel borescope/deburr, face flatness와 seat ID report 가능 여부.
11. EX-DIE-03 Ø3×10 land Ra≤0.4 및 OD 기준 concentricity 0.02 검사 가능 여부.
12. EX-DIE-04 동일 lot relief coupon 3개와 shielded 265 °C, 3–6 MPa 개방압 시험은 full die와 분리 견적한다.

Full part order release는 `HOLD_PROCESS_COUPON_AND_GATE3`이며 본 checklist가 닫혀도 자동 승인되지 않는다.
""",encoding="utf-8")


def main():
    write_drive_package(); write_gate1_package(); write_extruder_package()
    print(f"MANUFACTURING_PACKAGE_OK drive=3 jig_parts={len(gate1_parts())} extruder_parts={len(extruder_rfq_parts())}")


if __name__=="__main__":main()
