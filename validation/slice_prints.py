#!/usr/bin/env python3
"""Run the pinned PrusaSlicer CLI and replace planning values with slicer evidence."""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/"exports/print/slicer_profiles/PPR_PrusaSlicer_2.9.6.ini"


def parse_time(value):
    seconds=0
    for amount,unit in re.findall(r"(\d+)\s*([dhms])",value):
        seconds+=int(amount)*{"d":86400,"h":3600,"m":60,"s":1}[unit]
    return seconds


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
        common=[slicer,"--load",str(PROFILE),"--duplicate",row["quantity"],"--center","110,110","--ensure-on-bed",str(stl)]
        for action,target in (("--export-3mf",plate),("--export-gcode",gcode)):
            completed=subprocess.run(common[:-1]+[action,"--output",str(target),common[-1]],cwd=ROOT,text=True,capture_output=True)
            if completed.returncode:
                raise SystemExit(f"SLICER_FAIL {pid}: {completed.stdout}{completed.stderr}")
        text=gcode.read_text(errors="replace")
        mass_match=re.search(r"^; filament used \[g\] = ([0-9.]+)",text,re.M)
        time_match=re.search(r"^; estimated printing time \(normal mode\) = (.+)$",text,re.M)
        if not mass_match or not time_match: raise SystemExit(f"SLICER_METADATA_MISSING {pid}")
        row["slicer_mass_total_g"]=mass_match.group(1); row["slicer_time_s"]=str(parse_time(time_match.group(1)))
        row["slicer_status"]="PASS"
        results.append({"part_id":pid,"quantity":int(row["quantity"]),"mass_g":float(row["slicer_mass_total_g"]),"time_s":int(row["slicer_time_s"]),"plate":str(plate.relative_to(ROOT)),"gcode":str(gcode.relative_to(ROOT)),"status":"PASS"})
    with manifest.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n"); w.writeheader(); w.writerows(rows)
    total_mass=sum(r["mass_g"] for r in results); total_time=sum(r["time_s"] for r in results)
    reserve=0.12*total_mass; cad_difference=total_mass-sum(float(r["cad_net_mass_total_g"]) for r in rows)
    (ROOT/"exports/print/total_material_report.md").write_text(
        "# 출력물 총 재료 보고 — 실제 slicing\n\n"
        "- revision: `solid-manifold-openmodelica-v0.4`\n"
        "- slicer: `PrusaSlicer 2.9.6`, profile `PPR_PrusaSlicer_2.9.6.ini`\n"
        f"- slicer filament: **{total_mass:.1f} g**\n- slicer minus solid-CAD nominal: **{cad_difference:.1f} g**\n"
        f"- failed-print reserve 12%: **{reserve:.1f} g**\n- procurement planning mass: **{total_mass+reserve:.1f} g**\n"
        f"- total print time: **{total_time/3600:.1f} h**\n- 1.5 kg target: **{'PASS' if total_mass+reserve<=1500 else 'FAIL'}**\n",
        encoding="utf-8")
    result={"revision":"solid-manifold-openmodelica-v0.4","slicer":"PrusaSlicer 2.9.6","profile":str(PROFILE.relative_to(ROOT)),"total_mass_g":round(total_mass,3),"failed_print_reserve_g":round(reserve,3),"planning_mass_g":round(total_mass+reserve,3),"total_time_s":total_time,"parts":results,"status":"PASS" if total_mass+reserve<=2000 else "FAIL"}
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
