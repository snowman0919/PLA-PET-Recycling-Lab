#!/usr/bin/env python3
"""Run the pinned PrusaSlicer CLI and replace planning values with slicer evidence."""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
import zipfile
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/"exports/print/slicer_profiles/PPR_PrusaSlicer_2.9.6.ini"


def normalize_3mf_zip(path):
    """Rewrite a slicer 3MF with stable member order and ZIP metadata."""
    temporary=path.with_suffix(path.suffix+".normalized")
    with zipfile.ZipFile(path,"r") as source, zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED) as target:
        target.comment=source.comment
        for member in sorted(source.infolist(),key=lambda item:item.filename):
            info=zipfile.ZipInfo(member.filename,(2000,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=member.external_attr
            info.create_system=member.create_system
            target.writestr(info,source.read(member.filename))
    temporary.replace(path)


def parse_time(value):
    seconds=0
    for amount,unit in re.findall(r"(\d+)\s*([dhms])",value):
        seconds+=int(amount)*{"d":86400,"h":3600,"m":60,"s":1}[unit]
    return seconds


def gcode_metrics(path):
    text=path.read_text(errors="replace")
    mass_match=re.search(r"^; filament used \[g\] = ([0-9.]+)",text,re.M)
    time_match=re.search(r"^; estimated printing time \(normal mode\) = (.+)$",text,re.M)
    if not mass_match or not time_match: raise SystemExit(f"SLICER_METADATA_MISSING {path.name}")
    return float(mass_match.group(1)),parse_time(time_match.group(1))


def support_volume_cm3(path):
    """Integrate positive filament-E moves tagged as support material."""
    absolute=True; current_e=0.0; role=""; support_length_mm=0.0
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith(";TYPE:"):
            role=line.split(":",1)[1].strip().lower()
        elif line.startswith("M82"):
            absolute=True
        elif line.startswith("M83"):
            absolute=False
        elif line.startswith("G92"):
            match=re.search(r"(?:^|\s)E(-?[0-9.]+)",line)
            if match: current_e=float(match.group(1))
        elif line.startswith(("G0 ","G1 ")):
            match=re.search(r"(?:^|\s)E(-?[0-9.]+)",line)
            if not match: continue
            value=float(match.group(1)); delta=value-current_e if absolute else value
            if absolute: current_e=value
            if delta>0 and "support" in role: support_length_mm+=delta
    return support_length_mm*math.pi*(1.75/2)**2/1000


def first_layer_preview_svg(gcode_path, output_path, title):
    """Render the first extrusion layer as a lightweight, reviewable bed SVG."""
    absolute_xy=True; absolute_e=True
    x=y=0.0; current_e=0.0; role="unclassified"; layer_count=0; layer_z=None
    segments=[]
    colors={
        "skirt/brim":"#78909c", "perimeter":"#2563a6", "external perimeter":"#123f73",
        "solid infill":"#e58b2a", "infill":"#e58b2a", "support material":"#c8443a",
        "support material interface":"#8f2f29",
    }
    for raw in gcode_path.read_text(errors="replace").splitlines():
        line=raw.strip()
        if line == ";LAYER_CHANGE":
            layer_count+=1
            if layer_count>1: break
            continue
        if layer_count!=1: continue
        if line.startswith(";Z:"):
            try: layer_z=float(line.split(":",1)[1])
            except ValueError: pass
            continue
        if line.startswith(";TYPE:"):
            role=line.split(":",1)[1].strip().lower()
            continue
        if line.startswith("G90"): absolute_xy=True; continue
        if line.startswith("G91"): absolute_xy=False; continue
        if line.startswith("M82"): absolute_e=True; continue
        if line.startswith("M83"): absolute_e=False; continue
        if line.startswith("G92"):
            match=re.search(r"(?:^|\s)E(-?[0-9.]+)",line)
            if match: current_e=float(match.group(1))
            continue
        if not line.startswith(("G0 ","G1 ")): continue
        values={key:float(value) for key,value in re.findall(r"(?:^|\s)([XYE])(-?[0-9.]+)",line)}
        nx=(values.get("X",x) if absolute_xy else x+values.get("X",0.0))
        ny=(values.get("Y",y) if absolute_xy else y+values.get("Y",0.0))
        delta_e=0.0
        if "E" in values:
            delta_e=values["E"]-current_e if absolute_e else values["E"]
            if absolute_e: current_e=values["E"]
        if delta_e>0 and (abs(nx-x)>1e-6 or abs(ny-y)>1e-6):
            segments.append((x,y,nx,ny,colors.get(role,"#58636b"),role))
        x,y=nx,ny
    if len(segments)<3: raise SystemExit(f"SLICER_PREVIEW_EMPTY {gcode_path.name}")
    output_path.parent.mkdir(parents=True,exist_ok=True)
    lines=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="765" viewBox="0 0 240 255">',
        '<rect width="240" height="255" fill="#f6f8f9"/>',
        f'<text x="10" y="9" font-family="sans-serif" font-size="4.2" fill="#19313d">{escape(title)}</text>',
        f'<text x="10" y="15" font-family="sans-serif" font-size="3.2" fill="#526873">first extrusion layer Z={layer_z if layer_z is not None else "unknown"} mm · {len(segments)} segments</text>',
        '<rect x="10" y="20" width="220" height="220" rx="1" fill="#ffffff" stroke="#364b55" stroke-width="0.6"/>',
        '<g stroke-linecap="round" fill="none">',
    ]
    for x0,y0,x1,y1,color,_ in segments:
        lines.append(f'<line x1="{10+x0:.3f}" y1="{240-y0:.3f}" x2="{10+x1:.3f}" y2="{240-y1:.3f}" stroke="{color}" stroke-width="0.38"/>')
    lines.extend([
        '</g>',
        '<g font-family="sans-serif" font-size="3.1" fill="#334851">',
        '<rect x="10" y="244" width="4" height="2" fill="#123f73"/><text x="15" y="246">perimeter</text>',
        '<rect x="42" y="244" width="4" height="2" fill="#e58b2a"/><text x="47" y="246">solid/infill</text>',
        '<rect x="78" y="244" width="4" height="2" fill="#c8443a"/><text x="83" y="246">support</text>',
        '<rect x="108" y="244" width="4" height="2" fill="#78909c"/><text x="113" y="246">skirt/brim</text>',
        '</g></svg>',
    ])
    output_path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return len(segments),layer_z


def update_print_note(pid,mass_g,time_s,support_cm3):
    path=ROOT/f"exports/print/{pid}/print_notes.md"; text=path.read_text()
    begin="<!-- SLICER_EVIDENCE_BEGIN -->"; end="<!-- SLICER_EVIDENCE_END -->"
    block=f"{begin}\n- PrusaSlicer package mass: **{mass_g:.2f} g** for released quantity\n- PrusaSlicer package time: **{time_s/3600:.2f} h**\n- support extrusion volume: **{support_cm3:.3f} cm³** (G-code role integration; included in package mass)\n{end}"
    if begin in text:
        text=re.sub(re.escape(begin)+r".*?"+re.escape(end),block,text,flags=re.S)
    else:
        text=text.rstrip()+"\n\n"+block+"\n"
    path.write_text(text)


def main():
    slicer=shutil.which("prusa-slicer")
    if not slicer: raise SystemExit("PrusaSlicer not found; run through nix develop")
    manifest=ROOT/"exports/print/print_manifest.csv"
    with manifest.open(newline="") as f: rows=list(csv.DictReader(f))
    out_dir=ROOT/"exports/print/plate_layouts"; out_dir.mkdir(parents=True,exist_ok=True)
    preview_dir=ROOT/"exports/print/slicing_previews"; preview_dir.mkdir(parents=True,exist_ok=True)
    results=[]
    for index,row in enumerate(rows,1):
        pid=row["part_id"]; stl=ROOT/f"exports/print/{pid}/{pid}.stl"
        plate=out_dir/f"plate-{index:02d}-{pid}.3mf"; gcode=preview_dir/f"plate-{index:02d}-{pid}.gcode"
        support_enabled=row["support"].strip().lower()!="no"
        support_args=["--support-material","--support-material-auto","--support-material-threshold","45"] if support_enabled else []
        common=[slicer,"--threads","1","--load",str(PROFILE),"--duplicate",row["quantity"],"--center","110,110","--ensure-on-bed",*support_args,str(stl)]
        for action,target in (("--export-3mf",plate),("--export-gcode",gcode)):
            completed=subprocess.run(common[:-1]+[action,"--output",str(target),common[-1]],cwd=ROOT,text=True,capture_output=True)
            if completed.returncode:
                raise SystemExit(f"SLICER_FAIL {pid}: {completed.stdout}{completed.stderr}")
            if action=="--export-3mf": normalize_3mf_zip(target)
        mass_g,time_s=gcode_metrics(gcode); support_cm3=support_volume_cm3(gcode)
        preview=preview_dir/f"plate-{index:02d}-{pid}-first-layer.svg"
        preview_segments,preview_z=first_layer_preview_svg(gcode,preview,f"{pid} x{row['quantity']} / PrusaSlicer 2.9.6")
        row["slicer_mass_total_g"]=f"{mass_g:.2f}"; row["slicer_time_s"]=str(time_s)
        row["slicer_status"]="PASS"
        results.append({"part_id":pid,"quantity":int(row["quantity"]),"mass_g":mass_g,"time_s":time_s,"support_generation_enabled":support_enabled,"support_volume_cm3":round(support_cm3,4),"plate":str(plate.relative_to(ROOT)),"gcode":str(gcode.relative_to(ROOT)),"preview":str(preview.relative_to(ROOT)),"preview_first_layer_z_mm":preview_z,"preview_segment_count":preview_segments,"status":"PASS"})
        update_print_note(pid,mass_g,time_s,support_cm3)

    coupon_id="PPR-TC01"; coupon_dir=ROOT/"exports/print/coupons"/coupon_id
    coupon_stl=coupon_dir/f"{coupon_id}.stl"; coupon_plate=coupon_dir/f"{coupon_id}_plate.3mf"; coupon_gcode=preview_dir/f"coupon-{coupon_id}.gcode"
    coupon_common=[slicer,"--threads","1","--load",str(PROFILE),"--center","110,110","--ensure-on-bed",str(coupon_stl)]
    for action,target in (("--export-3mf",coupon_plate),("--export-gcode",coupon_gcode)):
        completed=subprocess.run(coupon_common[:-1]+[action,"--output",str(target),coupon_common[-1]],cwd=ROOT,text=True,capture_output=True)
        if completed.returncode: raise SystemExit(f"SLICER_FAIL {coupon_id}: {completed.stdout}{completed.stderr}")
        if action=="--export-3mf": normalize_3mf_zip(target)
    coupon_mass,coupon_time=gcode_metrics(coupon_gcode)
    coupon_preview=preview_dir/f"coupon-{coupon_id}-first-layer.svg"
    coupon_segments,coupon_z=first_layer_preview_svg(coupon_gcode,coupon_preview,f"{coupon_id} tolerance coupon / PrusaSlicer 2.9.6")
    coupon_result={"part_id":coupon_id,"mass_g":coupon_mass,"time_s":coupon_time,"plate":str(coupon_plate.relative_to(ROOT)),"gcode":str(coupon_gcode.relative_to(ROOT)),"preview":str(coupon_preview.relative_to(ROOT)),"preview_first_layer_z_mm":coupon_z,"preview_segment_count":coupon_segments,"status":"PASS","included_in_machine_mass":False}
    with manifest.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(rows)
    total_mass=sum(r["mass_g"] for r in results); total_time=sum(r["time_s"] for r in results); total_support=sum(r["support_volume_cm3"] for r in results)
    reserve=0.12*total_mass; cad_difference=total_mass-sum(float(r["cad_net_mass_total_g"]) for r in rows)
    (ROOT/"exports/print/total_material_report.md").write_text(
        "# 출력물 총 재료 보고 — 실제 slicing\n\n"
        "- revision: `virtual-physics-closure-v0.5.1`\n"
        "- slicer: `PrusaSlicer 2.9.6`, profile `PPR_PrusaSlicer_2.9.6.ini`\n"
        f"- slicer filament: **{total_mass:.1f} g**\n- slicer minus solid-CAD nominal: **{cad_difference:.1f} g**\n"
        f"- failed-print reserve 12%: **{reserve:.1f} g**\n- procurement planning mass: **{total_mass+reserve:.1f} g**\n"
        f"- total print time: **{total_time/3600:.1f} h**\n- 1.5 kg target: **{'PASS' if total_mass+reserve<=1500 else 'FAIL'}**\n"
        f"- G-code support extrusion volume: **{total_support:.2f} cm³** (nominal mass에 포함)\n"
        f"- PPR-TC01 tolerance coupon (machine total excluded): **{coupon_mass:.1f} g / {coupon_time/3600:.1f} h**\n",
        encoding="utf-8")
    result={"revision":"virtual-physics-closure-v0.5.1","slicer":"PrusaSlicer 2.9.6","profile":str(PROFILE.relative_to(ROOT)),"total_mass_g":round(total_mass,3),"failed_print_reserve_g":round(reserve,3),"planning_mass_g":round(total_mass+reserve,3),"total_time_s":total_time,"parts":results,"tolerance_coupon":coupon_result,"status":"PASS" if total_mass+reserve<=2000 else "FAIL"}
    out=ROOT/"validation/results"; out.mkdir(parents=True,exist_ok=True); (out/"slicer_results.json").write_text(json.dumps(result,indent=2)+"\n")
    with (ROOT/"bom/printed_material_cost.csv").open("w",newline="") as f:
        fields=["part_id","quantity","material","slicer_mass_total_g","cost_krw_per_kg","estimated_cost_krw","status"]
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); writer.writeheader()
        material={row["part_id"]:row["material"] for row in rows}
        for item in results:
            writer.writerow({"part_id":item["part_id"],"quantity":item["quantity"],"material":material[item["part_id"]],"slicer_mass_total_g":f"{item['mass_g']:.2f}","cost_krw_per_kg":18000,"estimated_cost_krw":round(item["mass_g"]*18),"status":"PRUSASLICER_ESTIMATE"})
        writer.writerow({"part_id":"TOTAL_NOMINAL","quantity":sum(item["quantity"] for item in results),"material":"MIXED","slicer_mass_total_g":f"{total_mass:.2f}","cost_krw_per_kg":18000,"estimated_cost_krw":round(total_mass*18),"status":"PRUSASLICER_ESTIMATE"})
        writer.writerow({"part_id":"FAILED_PRINT_RESERVE_12_PERCENT","quantity":0,"material":"MIXED","slicer_mass_total_g":f"{reserve:.2f}","cost_krw_per_kg":18000,"estimated_cost_krw":round(reserve*18),"status":"PLANNING_RESERVE"})
        writer.writerow({"part_id":"TOTAL_PLANNING","quantity":sum(item["quantity"] for item in results),"material":"MIXED","slicer_mass_total_g":f"{total_mass+reserve:.2f}","cost_krw_per_kg":18000,"estimated_cost_krw":round((total_mass+reserve)*18),"status":"CONDITIONAL_BUDGET_INPUT"})
    if result["status"]!="PASS": raise SystemExit("PRINT_MASS_AND_TIME_FAIL")
    print(f"SLICER_SUCCESS_OK parts={len(results)} mass_g={total_mass:.1f} time_h={total_time/3600:.1f}")


if __name__=="__main__": main()
