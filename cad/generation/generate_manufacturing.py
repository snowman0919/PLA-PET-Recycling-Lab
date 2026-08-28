#!/usr/bin/env python3
"""Generate VE drive, Gate-1 jig and screw/barrel RFQ artifacts."""

from __future__ import annotations

import csv
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
<text x="55" y="675">OD 15.92 -0.02/0 · pitch 16.00 ±0.03 · land 1.60 ±0.05 · single start RH</text>
<text x="55" y="710">root Ø10.88 feed → linear Ø14.08 compression → Ø14.08 meter</text>
<text x="55" y="745">Datum A: drive journal axis · flight OD TIR ≤0.05/256 · flight OD Ra≤0.8 µm</text>
<text x="55" y="780">SCM440 QT 28–32 HRC → gas nitride 0.30–0.50 mm, surface 900–1100 HV</text>
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
<text x="55" y="690">4x M5×0.8 depth10 on PCD28 at 45° · bore straightness ≤0.05/256 · face ⟂ axis 0.03</text>
<text x="55" y="725">bore Ra≤0.4–0.8 µm; SCM440 QT 28–32 HRC → gas nitride 0.30–0.50 mm, ≥900 HV</text>
<text x="55" y="760">Final hone after nitriding. No weld or plating on bore. Supplier to report bore at 20/140/260 mm.</text>
</svg>\n""",encoding="utf-8")


def write_drive_package():
    base=ROOT/"exports/drive_interface"; base.mkdir(parents=True,exist_ok=True)
    specs=[
        dict(id="DRV-01",name="Universal donor motor plate",shape=universal_motor_plate(),qty=1,material="6 mm steel",process="laser cut + standard metal angles"),
        dict(id="DRV-02",name="Bolt-on cutter sprocket hub",shape=bolt_on_sprocket_hub(),qty=1,material="S45C",process="turn + keyway + PCD drilling"),
        dict(id="DRV-03",name="M3 Z16 phase gear lamination",shape=generic_phase_gear_lamination(),qty=6,material="6 mm S45C",process="laser/waterjet + stack dowel/finish"),
    ]
    rows=export_shape_set(specs,base/"parts")
    with (base/"manifest.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["part_id","name","quantity","material","process","x_mm","y_mm","z_mm","release_state"])
        for r in rows:w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"{r['x']:.2f}",f"{r['y']:.2f}",f"{r['z']:.2f}","HOLD_DONOR_AND_GATE1"])
    (base/"interface_contract_ko.md").write_text("""# Interchangeable shredder drive interface — compact-single-path-v0.3

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

`DRV-01` plate에는 motor-specific standard angle/saddle만 추가한다. Motor torque는 #35 chain의 교환 가능한 12T input과 18T/24T output sprocket을 거쳐 right CUT-05 shaft로 전달한다. `DRV-02`는 Ø20 key shaft와 PCD36 four-bolt sprocket blank를 분리하므로 shaft diameter가 다른 donor에는 motor-side hub만 교체한다. 두 cutter shaft의 counter-rotation/phase는 특정 공급사 대신 M3 Z16, 20°, face>=18 mm steel gear functional specification으로 조달하거나 `DRV-03` 3-lamination/gear를 사용한다.

Chain efficiency 0.85 screening에서 12T:18T는 motor output continuous/3 s peak가 최소 11.0/18.8 N·m, 12T:24T는 최소 8.3/14.2 N·m여야 한다. 각각 motor speed 30–60/40–80 rpm이 cutter 20–40 rpm을 만든다. 24 V label power는 150 W 이상을 screening 시작점으로 쓰되 합격은 label watt가 아니라 Gate-1 torque/current/RPM/temperature 결과로 정한다. 후보별 기록표는 `bom/donor_drive_acceptance.csv`다.

Chain guard, 20 A fuse, E-stop/lid/service hard inhibit, current+RPM jam detection과 20–24 N·m sacrificial brass key는 유지한다. Donor 확인과 Gate-1 전 full quantity 발주 금지다.
""",encoding="utf-8")


def write_gate1_package():
    base=ROOT/"exports/jigs/gate1"; (base/"parts").mkdir(parents=True,exist_ok=True)
    rows=export_shape_set(gate1_parts(),base/"parts")
    envelope=export_assembly(gate1_assembly(),base,"gate1_assembly")
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
        f"# Gate-1 jig 출력물 집계\n\n총 예상 PLA 질량은 `{total_print:.1f} g`이며 final machine의 1100.5 g과 분리한 시험 jig 집계다. "
        f"18,000 KRW/kg 기준 재료비는 약 `{total_print*18:.0f} KRW`다. 모든 부품은 각 축 210 mm 이하다.\n",encoding="utf-8")
    with (base/"bom.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["item","qty","source","cash_krw","status","reuse_after_test","notes"])
        data=[
            ("CUT-01 coupon disc",2,"exports/cnc/CUT-01",4000,"COUPON_RFQ","yes","D2/SKD11 candidate; no remaining 10 discs"),
            ("CUT-03 side plate",2,"exports/cnc/CUT-03",8000,"RFQ_HOLD","yes","42 H7 seats match-machined"),
            ("CUT-05 shaft",2,"exports/cnc/CUT-05",12000,"RFQ_HOLD","yes","final machine shaft"),
            ("CUT-04 5 mm screen coupon",1,"exports/cnc/CUT-04",0,"BUDGET_LINE_CNC04","yes","5 mm holes; 3 mm 304; top clearance >=1.9 mm"),
            ("6004-2RS",4,"project-lab/donor",0,"VERIFY_INVENTORY","yes","designation/play/corrosion"),
            ("DRV-03 phase lamination",6,"exports/drive_interface",6000,"COUPON_RFQ","yes","3 laminations per gear"),
            ("G1J-01 base",1,"donor metal plate",0,"VERIFY_INVENTORY","jig","flatness <=0.3 mm"),
            ("G1J-02 torque arm",1,"exports/jigs/gate1/parts",2000,"RFQ_HOLD","jig","250.0 mm force radius"),
            ("0-200 N force gauge or 100 kg load cell/HX711",1,"project-lab or buy allowance",7500,"CALIBRATION_HOLD","jig","accuracy <=2% after calibration"),
            ("3 mm polycarbonate guard sheet",1,"project-lab/donor",0,"VERIFY_INVENTORY","jig","no acrylic in fragment plane"),
            ("printed chute/tray/corners",1,"exports/jigs/gate1/parts",4500,"PRINT_HOLD","jig","약 0.25 kg; cold low-load only"),
            ("M6/M8 fastener shim collars",1,"hardware allowance",1500,"BUY_HOLD","yes","metal shim controls cutter clearance"),
        ]
        w.writerows(data)
    (base/"assembly_ko.md").write_text(f"""# Gate-1 cutter coupon jig 조립도

- revision: `compact-single-path-v0.3`
- nominal assembly envelope: `{envelope[0]} x {envelope[1]} x {envelope[2]} mm`
- 목적: CUT-01 두 장만 사용해 PLA/PET peak torque, jam recovery와 chip-size fraction을 측정한다.

## 조립 순서

1. G1J-01을 고정 table에 M8 네 점으로 체결하고 0.3 mm 이내 평면을 확인한다.
2. 최종기용 CUT-03 두 장과 6004 bearing 네 개를 조립한다. Bearing은 outer ring만 눌러 삽입한다.
3. CUT-05 두 축을 넣고 CUT-01 coupon을 축당 한 장만 6.5 mm offset으로 장착한다. 0.25–0.50 mm metal shim으로 axial gap을 맞춘다.
4. CUT-04 5 mm screen coupon을 cutter tip 아래 nominal 3.0 mm 위치에 금속 rail/shim으로 고정하고 실제 최소 clearance가 1.9 mm 이상인지 확인한다.
5. DRV-03 lamination을 축당 세 장 정렬·dowel 체결하고 hand rotation 20회에서 간섭이 없어야 한다.
6. G1J-02 torque arm 중심에서 force hole까지 `250.0 ±0.5 mm`를 실측한다.
7. Chip tray, feed chute, 3 mm polycarbonate 네 panel과 G1J-P03 corner를 설치한다. Torque arm은 right panel의 좁은 slot만 통과하고 외측 offset baffle이 fragment 직선경로를 막는다. Guard가 열린 동안 motor enable은 hard-open이어야 한다.
8. Manual torque test 뒤에만 donor drive를 DRV-01/#35 chain interface로 연결한다.

고하중 경로는 cutter → metal shaft → 6004 → CUT-03 → G1J-01 → table이다. 출력 chute/tray/corner는 하중경로가 아니다.
""",encoding="utf-8")
    (base/"test_procedure_ko.md").write_text("""# Gate-1 CUT-01 coupon 시험 절차와 합격기준

## 시험 전 부품과 계측

- CUT-01 coupon 2개와 CUT-04 5 mm screen coupon 1개만 사용한다. Full 12-disc stack과 screw/barrel 발주는 금지한다.
- PLA wall 1.2/2.0/3.0 mm: 25 x 80 mm, 각 5개.
- PET body single layer와 four-layer folded seam: 25 x 80 mm, 각 5개. Cap/neck/label/adhesive 제거.
- 0–200 N force gauge 또는 calibrated load cell, arm radius 250.0 mm, driven-shaft Hall RPM, 50 A current sensor, 3/6/20 mm sieve, 0.1 g scale, video.
- Force gauge는 0/49.05/98.10/147.15 N에서 오차 <=2%, arm radius 오차 <=0.5 mm여야 한다.

## A. Lockout와 dry mechanical

1. Main disconnect OFF/0 V, shaft block, guard open 상태에서 fastener torque와 shim을 기록한다.
2. Hand rotation 20회: cutter/plate/gear/screen 접촉 0, shaft TIR <=0.10 mm, phase error <=1.0°.
3. Polycarbonate guard, lid/service switch와 E-stop이 motor energy를 실제 제거하는지 각각 continuity test한다.

## B. Quasi-static 절단토크

1. Coupon을 push stick으로 capture point에 놓고 guard를 닫는다.
2. Torque arm을 3–5 rpm 상당으로 당겨 peak force `F_peak`를 기록한다. `T_peak=F_peak x r`, `r=0.2500 m`다.
3. 각 specimen 5회 후 median, maximum, failure mode(capture/buckle/shear/slip)를 기록한다.
4. PLA 세 두께와 PET body의 max <=14 N·m, folded seam max <=24 N·m이어야 한다. 24 N·m 전에 shaft/gear/plate 영구변형, tooth crack 또는 key damage가 있으면 FAIL이다.

## C. Motor/current와 jam recovery

1. 합격한 donor motor만 연결하고 PLA 32 rpm/PET 24 rpm에서 no-load current/RPM을 기록한다.
2. Controlled folded seam jam을 각 재질 3회 만든다. PLA 16 A/650 ms, PET 18 A/850 ms 또는 command 대비 RPM 35% drop/500 ms에서 reverse가 시작돼야 한다.
3. Reverse는 PLA 800 ms/PET 1100 ms, 최대 3회다. 세 번째 실패 뒤 enable=0과 latched fault가 유지돼야 한다.
4. Guard를 열고 lockout/jam 제거 확인 없이는 reset되면 FAIL이다.

## D. Chip-size

1. CUT-04 5 mm screen과 동일 5 s screen dwell, oversize 재투입 1회 이하로 재질별 최소 30 g을 시험하고 chip을 20/6/3 mm sieve로 분류한다.
2. `3–6 mm`, `6–20 mm`, `>20 mm long strip`, `<3 mm fines` 질량과 총 회수율을 기록한다.
3. 초기 합격: 3–6 mm >=55%, >20 mm PET strip <=10%, fines <=15%, 회수율 >=95%. 미달이면 CUT-01 전체 수량을 발주하지 않고 hook/screen coupon만 수정한다.

## 기록과 release

CSV 필수 열은 material, specimen, thickness/fold, trial, peak_N, radius_m, peak_Nm, current_A, rpm_min, reverse_ms, retry, chip_bin_g, observation이다. Gate-1 PASS는 실제 서명된 raw CSV와 사진/영상 경로가 있어야 하며 simulation 값으로 대체할 수 없다.
""",encoding="utf-8")


def write_extruder_package():
    base=ROOT/"exports/cnc/extruder"; (base/"parts").mkdir(parents=True,exist_ok=True)
    rows=export_shape_set(extruder_rfq_parts(),base/"parts")
    with (base/"rfq_manifest.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["part_id","name","qty","material","process","step","drawing","release"])
        for r in rows:
            drawing=f"{r['id']}_drawing.svg" if r["id"] in ("EX-SCR-01","EX-BAR-01") else "manufacturing_audit_ko.md"
            release="COUPON_RFQ_ALLOWED" if r["id"].startswith("EX-CPN-") else "HOLD_PROCESS_COUPON_AND_GATE3"
            w.writerow([r["id"],r["name"],r["qty"],r["material"],r["process"],f"parts/{r['id']}/{r['id']}.step",drawing,release])
    svg_screw_drawing(base/"EX-SCR-01_drawing.svg"); svg_barrel_drawing(base/"EX-BAR-01_drawing.svg")
    with (base/"screw_profile.csv").open("w",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["zone","z_start_mm","z_end_mm","length_D","root_diameter_mm","pitch_mm","land_mm"])
        w.writerows([("feed",0,128,8,10.88,16,1.60),("compression",128,192,4,"10.88_to_14.08",16,1.60),("meter",192,256,4,14.08,16,1.60)])
    (base/"manufacturing_audit_ko.md").write_text("""# 16 mm x 16 L/D screw/barrel 제조성 audit — RFQ 기준

## Controlling geometry

STEP은 3D 견적/간섭 기준, SVG와 본 문서는 치수·GD&T 기준이다. STL/DXF는 CAM reference이며 공차를 대체하지 않는다. 공급사는 임의로 clearance나 heat treatment를 변경하지 않는다.

## EX-SCR-01 screw

- SCM440, normalized blank → rough turn → QT 28–32 HRC → centres 유지.
- Total 316.0 ±0.10; active 256.0; single-start RH; pitch 16.00 ±0.03; flight land 1.60 ±0.05.
- Zone 8D/4D/4D. Root Ø10.88 feed, linear compression, Ø14.08 meter. Flight OD Ø15.92 -0.02/0.
- Drive Ø12 h6 x35 with KS/DIN 4 x4 key, shaft keyseat 4 P9 wide x2.5 +0.10/0 deep; thrust journal Ø15 h6 x20; shoulder face perpendicularity 0.03 to Datum A axis. Flight start angle is 0° ±5° from key centre plane at active-section start.
- 4-axis flight mill leaving 0.15 mm grind/polish allowance. Root/flank Ra≤1.6 µm, flight OD Ra≤0.8 µm.
- Gas nitride 0.30–0.50 mm effective case, surface 900–1100 HV; mask drive/thrust journals. Final flight-OD grind between centres.
- Flight OD TIR ≤0.05 over active 256; drive-to-flight concentricity ≤0.03; straightness ≤0.05/256. No weld repair.

## EX-BAR-01 barrel

- SCM440 solid/seamless blank, QT 28–32 HRC. OD Ø34.00 ±0.05, length 280.00 ±0.05.
- Bore after final hone Ø16.20 +0.02/0, Ra≤0.4–0.8 µm. Bore straightness ≤0.05/256 and concentricity to OD/register ≤0.05.
- Feed opening 18 axial x20, rear edge 12.0 from Datum B. Port edges R0.5; no sharp edge over screw flight.
- Front 4x M5 x0.8, thread depth 10 minimum, PCD28 at 45/135/225/315° from feed-port centre plane. Front face is Datum C and is perpendicular 0.03 to bore axis.
- Rough deep drill → stress relieve → semi-finish ream/hone leaving 0.05–0.08 mm → feed port/flange machine → gas nitride 0.30–0.50 mm, ≥900 HV → final hone. Effective case after final hone is ≥0.25 mm.
- Report bore at 20/140/260 mm and roundness ≤0.02 at each station. Front/rear face perpendicularity 0.03 to bore axis.

## Matched clearance and inspection

Specified drawing-limit diametral clearance is 0.28–0.32 mm and radial clearance is 0.14–0.16 mm. Supplier records screw OD and barrel ID at three stations at 20 ±2 °C and pairs parts inside that interval. Blue/air-gauge report, hardness/case-depth certificate, Ra trace and TIR inspection sheet are RFQ deliverables.

## DFM decision

SCM440 was selected over stainless for local availability, machinability and nitriding cost. PET-temperature metal compatibility is adequate for a research coupon, but corrosion/wear life is not certified. `EX-CPN-SCR` 3-pitch와 `EX-CPN-BAR` 60 mm process coupon만 먼저 견적·가공할 수 있다. Coupon의 치수·경도·case depth·Ra가 본 도면을 만족하고 공급사 DFM이 닫힌 뒤에도 Gate-3 cold proof 전 full screw/barrel 발주는 HOLD다. No physical result is claimed here.

Coupon controlling dimensions: EX-CPN-SCR L48.00 ±0.05, three RH pitches 16.00 ±0.03, OD/root/land와 열처리는 EX-SCR-01 feed zone과 동일하며 journal은 없다. EX-CPN-BAR L60.00 ±0.05, OD Ø34.00 ±0.05, final ID Ø16.20 +0.02/0, bore Ra/case는 EX-BAR-01과 동일하다. 두 coupon의 ends는 axis에 0.03 이내 수직이다.
""",encoding="utf-8")
    (base/"supplier_rfq_checklist_ko.md").write_text("""# 공급사 RFQ 응답 checklist

공급사는 가격만 답하지 말고 아래를 yes/no/deviation으로 회신한다.

1. SCM440 mill certificate와 QT 28–32 HRC 제공 가능 여부.
2. Screw 316/256 mm, pitch/land/root/OD와 Ø12 h6 keyseat, Ø15 h6 journal 가공 가능 여부.
3. Flight OD TIR 0.05/256, concentricity 0.03, Ra 0.8 검사 가능 여부.
4. Barrel Ø16.20 +0.02/0 final hone, three-station ID/roundness와 Ra report 가능 여부.
5. Gas nitride case/surface hardness certificate와 barrel final-hone 후 effective case ≥0.25 mm 가능 여부.
6. Drawing-limit radial clearance 0.14–0.16 matched measurement 가능 여부.
7. EX-CPN-SCR/EX-CPN-BAR coupon 단가·납기와 full part 단가·납기를 분리 기재.
8. 모든 deviation과 대체재를 발주 전 명시. 무응답 항목은 수락으로 간주하지 않는다.

Full part order release는 `HOLD_PROCESS_COUPON_AND_GATE3`이며 본 checklist가 닫혀도 자동 승인되지 않는다.
""",encoding="utf-8")


def main():
    write_drive_package(); write_gate1_package(); write_extruder_package()
    print("MANUFACTURING_PACKAGE_OK drive=3 jig_parts=5 extruder_parts=4")


if __name__=="__main__":main()
